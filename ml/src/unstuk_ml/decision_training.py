"""One training run of the decision model (M5 spec sections 2 and 3), checked on dev every epoch.

The epoch with the best dev macro-F1 (ties to the lower log-loss, as for every rung) is kept and
written with its metrics. Nothing here reads the test set.
"""

import argparse
import hashlib
import math
import random
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any

import torch
from pydantic import BaseModel, ConfigDict
from tokenizers import Tokenizer
from torch import nn

from unstuk_ml import rung
from unstuk_ml.backbone import load_backbone
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import collate, decision_tokenizer
from unstuk_ml.decision_loss import decision_loss
from unstuk_ml.decision_model import DecisionModel, Head
from unstuk_ml.decision_scoring import log_loss, node_accuracy, predict
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import in_scope_accuracy, macro_f1
from unstuk_ml.folds import folds, trained_intents, without
from unstuk_ml.node_labels import NodeQuestion, read_questions
from unstuk_ml.record import Record, read_records
from unstuk_ml.training_examples import Example, epoch
from unstuk_ml.validate import DEFAULT_DATA_DIR

REPO_ROOT = DEFAULT_DATA_DIR.parent
RUNS_DIR = REPO_ROOT / "ml" / "runs"
# Written into a Colab bundle, which carries no .git directory.
COMMIT_FILE = REPO_ROOT / "COMMIT"
# The heads start from scratch, so the backbone's fine-tuning rate would barely move them.
HEAD_LEARNING_RATE = 1e-3
WEIGHT_DECAY = 0.01
WARMUP_SHARE = 0.1
MAX_GRADIENT_NORM = 1.0


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    head: Head
    learning_rate: float
    typos: bool
    state: bool
    fold: int | None = None
    epochs: int = 6
    batch_size: int = 32
    seed: int = 7
    limit: int | None = None
    """Only the first lines and questions of each file, for a smoke run."""

    @property
    def name(self) -> str:
        parts = [self.head, f"lr{self.learning_rate:g}"]
        parts += ["typos"] * self.typos + ["state"] * self.state
        parts += [f"fold{self.fold}"] if self.fold is not None else []
        parts += [f"limit{self.limit}"] if self.limit is not None else []
        return "-".join(parts)


class EpochResult(BaseModel):
    epoch: int
    train_loss: float
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float
    node_dev_accuracy: float
    fold_accuracy: float | None
    """Accuracy on dev lines of the intents this fold never trained on."""
    seconds: float


class RunResult(BaseModel):
    config: RunConfig
    epochs: list[EpochResult]
    chosen_epoch: int
    checkpoint_sha256: str
    commit: str
    device: str


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


def parameter_groups(model: DecisionModel, learning_rate: float) -> list[dict[str, Any]]:
    backbone = {id(p) for p in model.backbone.parameters()}
    heads = [p for p in model.parameters() if id(p) not in backbone]
    return [
        {"params": list(model.backbone.parameters()), "lr": learning_rate},
        {"params": heads, "lr": HEAD_LEARNING_RATE},
    ]


def learning_rate_factor(step: int, steps: int) -> float:
    """A linear warm-up over the first tenth of training, then a linear decay to zero."""
    warmup = max(1, int(WARMUP_SHARE * steps))
    if step < warmup:
        return step / warmup
    return max(0.0, (steps - step) / (steps - warmup))


def train(
    config: RunConfig,
    data: Data,
    model: DecisionModel,
    tokenizer: Tokenizer,
    device: torch.device,
) -> tuple[list[EpochResult], dict[str, torch.Tensor]]:
    """Every epoch's dev check, and the weights of the best epoch."""
    torch.manual_seed(config.seed)
    catalog = load_catalog()
    removed = removed_intents(config, catalog)
    intents = [i for i in trained_intents(catalog) if i not in removed]
    records = without(data.train, removed)
    model.to(device)
    optimizer = torch.optim.AdamW(
        parameter_groups(model, config.learning_rate), weight_decay=WEIGHT_DECAY
    )
    steps = config.epochs * math.ceil((len(records) + len(data.nodes)) / config.batch_size)
    schedule = torch.optim.lr_scheduler.LambdaLR(
        optimizer, partial(learning_rate_factor, steps=steps)
    )
    # fp16 halves the T4's work; the scaler keeps small gradients from rounding to zero.
    cuda = device.type == "cuda"
    scaler = torch.amp.GradScaler(device.type, enabled=cuda)
    results: list[EpochResult] = []
    best: dict[str, torch.Tensor] = {}
    for number in range(config.epochs):
        start = time.perf_counter()
        examples = epoch(
            records,
            data.nodes,
            catalog,
            intents,
            seed=config.seed,
            number=number,
            state=config.state,
            typos=config.typos,
        )
        random.Random(f"{config.seed}/{number}/order").shuffle(examples)
        model.train(True)
        losses = []
        for chunk in _chunks(examples, config.batch_size):
            batch = collate(chunk, tokenizer).to(device)
            with torch.autocast(device.type, dtype=torch.float16, enabled=cuda):
                loss = decision_loss(model(batch), batch)
            optimizer.zero_grad(set_to_none=True)
            torch.autograd.backward(scaler.scale(loss))
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), MAX_GRADIENT_NORM)
            scaler.step(optimizer)
            scaler.update()
            schedule.step()
            losses.append(loss.item())
        result = _check(model, data, catalog, tokenizer, removed, number, losses, start)
        results.append(result)
        print(result.model_dump_json(), flush=True)
        if rung.best(results) is result:
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    return results, best


def run(config: RunConfig, out: Path) -> RunResult:
    """Trains, then writes `model.pt` and `result.json` under `out/<run name>/`."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DecisionModel(load_backbone(), config.head)
    tokenizer = decision_tokenizer(download()[1])
    epochs, weights = train(config, load_data(config.limit), model, tokenizer, device)
    directory = out / config.name
    directory.mkdir(parents=True, exist_ok=True)
    checkpoint = directory / "model.pt"
    torch.save(weights, checkpoint)
    result = RunResult(
        config=config,
        epochs=epochs,
        chosen_epoch=rung.best(epochs).epoch,
        checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        commit=source_commit(),
        device=torch.cuda.get_device_name() if device.type == "cuda" else "cpu",
    )
    (directory / "result.json").write_text(result.model_dump_json(indent=2) + "\n", "utf-8")
    return result


def source_commit() -> str:
    if COMMIT_FILE.exists():
        return COMMIT_FILE.read_text(encoding="utf-8").strip()
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _check(
    model: DecisionModel,
    data: Data,
    catalog: Catalog,
    tokenizer: Tokenizer,
    removed: frozenset[str],
    number: int,
    losses: Sequence[float],
    start: float,
) -> EpochResult:
    # Every trained intent is offered, so a fold's removed ones are scored zero-shot.
    scored = predict(model, data.dev, trained_intents(catalog), catalog, tokenizer)
    unseen = [s for s in scored if removed & set(s.record.labels)]
    return EpochResult(
        epoch=number,
        train_loss=sum(losses) / len(losses),
        dev_macro_f1=macro_f1(scored),
        dev_log_loss=log_loss(scored),
        dev_in_scope_accuracy=in_scope_accuracy(scored),
        node_dev_accuracy=node_accuracy(model, data.node_dev, tokenizer),
        fold_accuracy=in_scope_accuracy(unseen) if removed else None,
        seconds=round(time.perf_counter() - start, 1),
    )


def _chunks(examples: Sequence[Example], size: int) -> list[Sequence[Example]]:
    return [examples[start : start + size] for start in range(0, len(examples), size)]


def add_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--head", choices=["cosine", "attention"], required=True)
    parser.add_argument("--learning-rate", type=float, required=True)
    parser.add_argument("--typos", action="store_true")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--fold", type=int)
    parser.add_argument("--epochs", type=int, default=RunConfig.model_fields["epochs"].default)
    parser.add_argument("--limit", type=int, help="first N lines and questions, for a smoke run")


def config_from(args: argparse.Namespace) -> RunConfig:
    return RunConfig(
        head=args.head,
        learning_rate=args.learning_rate,
        typos=args.typos,
        state=args.state,
        fold=args.fold,
        epochs=args.epochs,
        limit=args.limit,
    )


def run_arguments(config: RunConfig) -> list[str]:
    """The command-line options that `config_from` turns back into this config."""
    arguments = ["--head", config.head, "--learning-rate", repr(config.learning_rate)]
    arguments += ["--typos"] * config.typos + ["--state"] * config.state
    arguments += ["--epochs", str(config.epochs)]
    arguments += ["--fold", str(config.fold)] if config.fold is not None else []
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
