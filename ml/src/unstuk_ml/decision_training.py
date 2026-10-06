"""One training run of the decision model (M5 spec sections 2 and 3), checked on dev every epoch.

Nothing here reads the test set.
"""

import argparse
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import torch
from pydantic import BaseModel, ConfigDict
from tokenizers import Tokenizer

from unstuk_ml import rung
from unstuk_ml.backbone import freeze_lower, load_backbone
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import DecisionBatch, collate, decision_tokenizer
from unstuk_ml.decision_loss import decision_loss
from unstuk_ml.decision_model import DecisionModel, Head
from unstuk_ml.decision_scoring import log_loss, node_accuracy, predict
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import in_scope_accuracy, macro_f1
from unstuk_ml.fine_tuning import (
    RUNS_DIR,
    EpochCheck,
    RunResult,
    Training,
    chunks,
    fine_tune,
    save_run,
    shuffled,
    steps_per_epoch,
    training_device,
)
from unstuk_ml.folds import folds, trained_intents, without
from unstuk_ml.node_labels import NodeQuestion, read_questions
from unstuk_ml.record import Record, read_records
from unstuk_ml.training_examples import epoch
from unstuk_ml.validate import DEFAULT_DATA_DIR


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    head: Head
    learning_rate: float
    typos: bool
    state: bool
    fold: int | None = None
    wordings: bool = False
    """Offer other wordings of the option texts in training (round 3)."""
    frozen_layers: int = 0
    """Backbone layers kept as pre-trained, from the bottom, with the embeddings when above 0."""
    epochs: int = 6
    batch_size: int = 32
    seed: int = 7
    limit: int | None = None
    """Only the first lines and questions of each file, for a smoke run."""

    @property
    def name(self) -> str:
        parts = [self.head, f"lr{self.learning_rate:g}"]
        parts += ["typos"] * self.typos + ["wordings"] * self.wordings + ["state"] * self.state
        parts += [f"frozen{self.frozen_layers}"] if self.frozen_layers else []
        parts += [f"fold{self.fold}"] if self.fold is not None else []
        parts += [f"limit{self.limit}"] if self.limit is not None else []
        return "-".join(parts)


class EpochResult(EpochCheck):
    node_dev_accuracy: float
    fold_accuracy: float | None
    """Accuracy on dev lines of the intents this fold never trained on."""


DecisionRun = RunResult[RunConfig, EpochResult]


@dataclass(frozen=True)
class Data:
    train: list[Record]
    nodes: list[NodeQuestion]
    dev: list[Record]
    node_dev: list[NodeQuestion]


def load_data(limit: int | None = None) -> Data:
    """Lines from `data/clean` and the state slice, and node questions; never `data/test`."""
    data = Data(
        train=rung.read_clean("train") + read_records(DEFAULT_DATA_DIR / "state" / "train.jsonl"),
        nodes=read_questions(DEFAULT_DATA_DIR / "nodes" / "train.jsonl"),
        dev=rung.read_clean("dev"),
        node_dev=read_questions(DEFAULT_DATA_DIR / "nodes" / "dev.jsonl"),
    )
    if limit is None:
        return data
    return Data(data.train[:limit], data.nodes[:limit], data.dev[:limit], data.node_dev[:limit])


def removed_intents(config: RunConfig, catalog: Catalog) -> frozenset[str]:
    if config.fold is None:
        return frozenset()
    return folds(trained_intents(catalog))[config.fold]


def train(
    config: RunConfig,
    data: Data,
    model: DecisionModel,
    tokenizer: Tokenizer,
    device: torch.device,
) -> tuple[list[EpochResult], dict[str, torch.Tensor]]:
    """Every epoch's dev check, and the weights of the best epoch."""
    catalog = load_catalog()
    removed = removed_intents(config, catalog)
    intents = [i for i in trained_intents(catalog) if i not in removed]
    records = without(data.train, removed)

    def batches(number: int) -> Iterator[DecisionBatch]:
        examples = epoch(
            records,
            data.nodes,
            catalog,
            intents,
            seed=config.seed,
            number=number,
            state=config.state,
            typos=config.typos,
            wordings=config.wordings,
        )
        order = shuffled(examples, config.seed, number)
        return (collate(chunk, tokenizer) for chunk in chunks(order, config.batch_size))

    def check(number: int, train_loss: float, seconds: float) -> EpochResult:
        # Every trained intent is offered, so a fold's removed ones are scored zero-shot.
        scored = predict(model, data.dev, trained_intents(catalog), catalog, tokenizer)
        unseen = [s for s in scored if removed & set(s.record.labels)]
        return EpochResult(
            epoch=number,
            train_loss=train_loss,
            dev_macro_f1=macro_f1(scored),
            dev_log_loss=log_loss(scored),
            dev_in_scope_accuracy=in_scope_accuracy(scored),
            node_dev_accuracy=node_accuracy(model, data.node_dev, tokenizer),
            fold_accuracy=in_scope_accuracy(unseen) if removed else None,
            seconds=seconds,
        )

    training = Training(
        model=model,
        backbone=model.backbone,
        learning_rate=config.learning_rate,
        epochs=config.epochs,
        seed=config.seed,
        steps_per_epoch=steps_per_epoch(len(records) + len(data.nodes), config.batch_size),
        batches=batches,
        loss=lambda batch: decision_loss(model(batch), batch),
        check=check,
    )
    return fine_tune(training, device)


def run(config: RunConfig, out: Path) -> DecisionRun:
    """Trains, then writes `model.pt` and `result.json` under `out/<run name>/`."""
    device = training_device()
    backbone = load_backbone()
    freeze_lower(backbone, config.frozen_layers)
    model = DecisionModel(backbone, config.head)
    tokenizer = decision_tokenizer(download()[1])
    epochs, weights = train(config, load_data(config.limit), model, tokenizer, device)
    return save_run(out / config.name, config, epochs, weights, device)


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--head", choices=["cosine", "attention"], required=True)
    parser.add_argument("--learning-rate", type=float, required=True)
    parser.add_argument("--typos", action="store_true")
    parser.add_argument("--wordings", action="store_true")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--fold", type=int)
    parser.add_argument("--frozen-layers", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=RunConfig.model_fields["epochs"].default)
    parser.add_argument("--limit", type=int, help="first N lines and questions, for a smoke run")


def config_from(args: argparse.Namespace) -> RunConfig:
    return RunConfig(
        head=args.head,
        learning_rate=args.learning_rate,
        typos=args.typos,
        state=args.state,
        wordings=args.wordings,
        fold=args.fold,
        frozen_layers=args.frozen_layers,
        epochs=args.epochs,
        limit=args.limit,
    )


def run_arguments(config: RunConfig) -> list[str]:
    """The command-line options that `config_from` turns back into this config."""
    arguments = ["--head", config.head, "--learning-rate", repr(config.learning_rate)]
    arguments += ["--typos"] * config.typos + ["--state"] * config.state
    arguments += ["--wordings"] * config.wordings
    arguments += ["--epochs", str(config.epochs)]
    arguments += ["--fold", str(config.fold)] if config.fold is not None else []
    arguments += ["--frozen-layers", str(config.frozen_layers)] if config.frozen_layers else []
    arguments += ["--limit", str(config.limit)] if config.limit is not None else []
    return arguments


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_run_arguments(parser)
    parser.add_argument("--out", type=Path, default=RUNS_DIR)
    args = parser.parse_args()

    config = config_from(args)
    result = run(config, args.out)
    chosen = result.epochs[result.chosen_epoch]
    print(
        f"{config.name}: epoch {result.chosen_epoch}, dev macro-F1 {chosen.dev_macro_f1:.1%}, "
        f"written to {args.out / config.name}"
    )
