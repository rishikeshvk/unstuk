"""The fixed-head rung (M5 spec section 3): bge-small fine-tuned with a 13-way linear head.

`train` runs one grid point (on Colab). `choose` picks the best run on dev and fits its
temperature there, writing settings to commit. `test` then scores the frozen test set once, from
the checkpoint those settings name by its sha256.
"""

import argparse
from collections.abc import Iterator, Sequence
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from tokenizers import Tokenizer

from unstuk_ml import rung
from unstuk_ml.backbone import load_backbone
from unstuk_ml.baseline_report import REPORTS, Below, Decider, Table, load_test, write
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.encoder import download
from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import in_scope_accuracy, macro_f1
from unstuk_ml.fine_tuning import (
    RESULT,
    RUNS_DIR,
    EpochCheck,
    RunResult,
    Training,
    chunks,
    fine_tune,
    load_weights,
    save_run,
    shuffled,
    steps_per_epoch,
    training_device,
)
from unstuk_ml.fixed_head import (
    FixedHeadBatch,
    FixedHeadModel,
    collate_rows,
    fixed_head_logits,
    fixed_head_loss,
    fixed_labels,
    rows,
)
from unstuk_ml.record import Record
from unstuk_ml.temperature import fit_temperature, negative_log_likelihood
from unstuk_ml.zero_shot import score

SETTINGS = rung.SETTINGS_DIR / "fixed-head.json"
FIXED_HEAD = Decider(
    title="Fine-tuned bge-small + linear head",
    command="unstuk-fixed-head test",
    about="BAAI/bge-small-en-v1.5 fine-tuned on `data/clean/train.jsonl` with one output per "
    "trained intent and out of scope",
    held_out_note="no output for them; only a two-problem line whose other problem is trained "
    "can count as right",
    report=REPORTS / "fixed-head.md",
)


class FixedHeadConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    learning_rate: float
    typos: bool
    epochs: int = 6
    batch_size: int = 32
    seed: int = 7
    limit: int | None = None
    """Only the first train and dev lines, for a smoke run."""

    @property
    def name(self) -> str:
        parts = ["fixed-head", f"lr{self.learning_rate:g}"] + ["typos"] * self.typos
        parts += [f"limit{self.limit}"] if self.limit is not None else []
        return "-".join(parts)

    def arguments(self) -> list[str]:
        """The `train` options that give back this config."""
        arguments = ["--learning-rate", repr(self.learning_rate), "--epochs", str(self.epochs)]
        arguments += ["--typos"] * self.typos
        arguments += ["--limit", str(self.limit)] if self.limit is not None else []
        return arguments


FixedHeadRun = RunResult[FixedHeadConfig, EpochCheck]
GRID = [FixedHeadConfig(learning_rate=lr, typos=t) for lr in (2e-5, 5e-5) for t in (False, True)]


class GridRow(BaseModel):
    run: str
    epoch: int
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float


class Settings(BaseModel):
    run: str
    epoch: int
    temperature: float
    checkpoint_sha256: str
    commit: str
    grid: list[GridRow]


def train(
    config: FixedHeadConfig,
    records: Sequence[Record],
    dev: Sequence[Record],
    model: FixedHeadModel,
    tokenizer: Tokenizer,
    device: torch.device,
) -> tuple[list[EpochCheck], dict[str, torch.Tensor]]:
    labels = model.labels
    row_count = sum(len(r.labels) for r in records)

    def batches(number: int) -> Iterator[FixedHeadBatch]:
        epoch_rows = rows(records, labels, seed=config.seed, number=number, typos=config.typos)
        order = shuffled(epoch_rows, config.seed, number)
        return (collate_rows(chunk, tokenizer) for chunk in chunks(order, config.batch_size))

    def check(number: int, train_loss: float, seconds: float) -> EpochCheck:
        logits = fixed_head_logits(model, dev, tokenizer)
        scored = score(logits, labels, dev, 1.0)
        return EpochCheck(
            epoch=number,
            train_loss=train_loss,
            dev_macro_f1=macro_f1(scored),
            dev_log_loss=negative_log_likelihood(logits, targets(labels, dev), 1.0),
            dev_in_scope_accuracy=in_scope_accuracy(scored),
            seconds=seconds,
        )

    training = Training(
        model=model,
        backbone=model.backbone,
        learning_rate=config.learning_rate,
        epochs=config.epochs,
        seed=config.seed,
        steps_per_epoch=steps_per_epoch(row_count, config.batch_size),
        batches=batches,
        loss=lambda batch: fixed_head_loss(model, batch),
        check=check,
    )
    return fine_tune(training, device)


def run(config: FixedHeadConfig, out: Path) -> FixedHeadRun:
    device = training_device()
    model = FixedHeadModel(load_backbone(), fixed_labels(load_catalog()))
    tokenizer = decision_tokenizer(download()[1])
    records, dev = rung.read_clean("train"), rung.read_clean("dev")
    if config.limit is not None:
        records, dev = records[: config.limit], dev[: config.limit]
    epochs, weights = train(config, records, dev, model, tokenizer, device)
    return save_run(out / config.name, config, epochs, weights, device)


def pick(results: Sequence[FixedHeadRun]) -> tuple[list[GridRow], GridRow]:
    """Each run's kept epoch, and the best of them by the rung rule."""
    grid = [
        GridRow(run=r.config.name, **r.epochs[r.chosen_epoch].model_dump(include=_GRID_FIELDS))
        for r in results
    ]
    return grid, rung.best(grid)


def choose(runs: Path = RUNS_DIR) -> Settings:
    """The best grid run, with its temperature fitted on dev; nothing here reads the test."""
    results = [
        FixedHeadRun.model_validate_json((runs / c.name / RESULT).read_text(encoding="utf-8"))
        for c in GRID
    ]
    grid, best = pick(results)
    chosen = next(r for r in results if r.config.name == best.run)
    model = load_checkpoint(runs / best.run, chosen.checkpoint_sha256)
    dev = rung.read_clean("dev")
    logits = fixed_head_logits(model, dev, decision_tokenizer(download()[1]))
    return Settings(
        run=best.run,
        epoch=best.epoch,
        temperature=fit_temperature(logits, targets(model.labels, dev)),
        checkpoint_sha256=chosen.checkpoint_sha256,
        commit=chosen.commit,
        grid=grid,
    )


def load_checkpoint(directory: Path, expected_sha256: str) -> FixedHeadModel:
    weights = load_weights(directory, expected_sha256)
    model = FixedHeadModel(load_backbone(), fixed_labels(load_catalog()))
    model.load_state_dict(weights)
    return model


def test() -> None:
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    model = load_checkpoint(RUNS_DIR / settings.run, settings.checkpoint_sha256)
    lines = load_test()
    logits = fixed_head_logits(model, lines, decision_tokenizer(download()[1]))
    about = (
        f"{FIXED_HEAD.about}; run `{settings.run}`, epoch {settings.epoch}, checkpoint sha256 "
        f"`{settings.checkpoint_sha256[:12]}…` from commit `{settings.commit[:7]}`, temperature "
        f"{settings.temperature} fitted on dev"
    )
    encoder_settings, encoder = rung.load(ENCODER)
    write(
        replace(FIXED_HEAD, about=about),
        score(logits, model.labels, lines, settings.temperature),
        before_temperature=score(logits, model.labels, lines, 1.0),
        below=Below(ENCODER.decider, rung.score(encoder, encoder_settings.temperature, lines)),
        tuning=_tuning_table(settings),
    )


def targets(labels: Sequence[str], records: Sequence[Record]) -> NDArray[np.int64]:
    return np.array([labels.index(r.labels[0]) for r in records], dtype=np.int64)


_GRID_FIELDS = {"epoch", "dev_macro_f1", "dev_log_loss", "dev_in_scope_accuracy"}


def _tuning_table(settings: Settings) -> Table:
    rows_out = [
        [
            f"`{g.run}`",
            str(g.epoch),
            f"{g.dev_macro_f1:.1%}",
            f"{g.dev_log_loss:.3f}",
            f"{g.dev_in_scope_accuracy:.1%}",
            "**chosen**" if g.run == settings.run else "",
        ]
        for g in settings.grid
    ]
    header = ["Run", "Kept epoch", "Macro-F1", "Log-loss", "In-scope accuracy", ""]
    return Table(header, rows_out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("train", help="train one grid point")
    one.add_argument("--learning-rate", type=float, required=True)
    one.add_argument("--typos", action="store_true")
    one.add_argument("--epochs", type=int, default=FixedHeadConfig.model_fields["epochs"].default)
    one.add_argument("--limit", type=int, help="first N train and dev lines, for a smoke run")
    one.add_argument("--out", type=Path, default=RUNS_DIR)
    commands.add_parser("choose", help=f"pick the best grid run on dev; write {SETTINGS.name}")
    commands.add_parser("test", help="score the frozen test set once with the written settings")
    args = parser.parse_args()

    if args.command == "train":
        config = FixedHeadConfig(
            learning_rate=args.learning_rate, typos=args.typos, epochs=args.epochs, limit=args.limit
        )
        result = run(config, args.out)
        print(f"{config.name}: epoch {result.chosen_epoch}, written to {args.out / config.name}")
    elif args.command == "choose":
        settings = choose()
        SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"{settings.run}, epoch {settings.epoch}, T={settings.temperature}")
        print(f"written to {SETTINGS}; commit it before running `test`")
    else:
        test()
