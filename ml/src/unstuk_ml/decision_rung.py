"""Choosing the decision model (M5 spec section 3): a dev grid under a zero-shot guard.

Every config trains on all the data and on three leave-intents-out folds. A config qualifies only
if, on the folds, it names intents it never trained on at least as well as the frozen zero-shot
rung does on the same lines; among those, the rung rule picks on dev. Nothing here reads the test.
"""

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
from pydantic import BaseModel
from tokenizers import Tokenizer

from unstuk_ml import rung, zero_shot
from unstuk_ml.backbone import load_backbone
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel, Head
from unstuk_ml.decision_scoring import (
    decision_logits,
    fit_temperatures,
    log_loss,
    node_accuracy,
    predict,
)
from unstuk_ml.decision_training import DecisionRun, RunConfig
from unstuk_ml.encoder import download, embed_cached
from unstuk_ml.evaluate import in_scope_accuracy, macro_f1
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.folds import FOLDS, folds, naming, trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion, read_questions
from unstuk_ml.record import Record
from unstuk_ml.validate import DEFAULT_DATA_DIR
from unstuk_ml.wise_ft import blend

SETTINGS = rung.SETTINGS_DIR / "decision.json"
HEADS: tuple[Head, ...] = ("cosine", "attention")
ROUND_1 = [
    RunConfig(head=head, learning_rate=lr, typos=typos, state=True)
    for lr in (2e-5, 5e-5)
    for typos in (False, True)
    for head in HEADS
]
# Round 1 forgot zero-shot naming from the first epoch (spec section 3), so round 2 moves less.
ROUND_2 = [
    *(
        RunConfig(head=head, learning_rate=lr, typos=True, state=True)
        for lr in (1e-5, 5e-6)
        for head in HEADS
    ),
    RunConfig(head="attention", learning_rate=2e-5, typos=True, state=True, frozen_layers=8),
]
# Round 2 failed too, so round 3 removes the 12 fixed option strings the model could memorise.
ROUND_3 = [
    RunConfig(head=head, learning_rate=lr, typos=True, state=True, wordings=True)
    for lr in (5e-6, 1e-5, 2e-5)
    for head in HEADS
]
CONFIGS = ROUND_1 + ROUND_2 + ROUND_3
# Round 3 failed too; round 4 blends the best checkpoints back toward the frozen encoder (WiSE-FT).
ALPHAS = (0.25, 0.5, 0.75)
BLENDED = [ROUND_3[1], ROUND_3[2], ROUND_2[3], ROUND_1[6]]
BLENDS = [(config, alpha) for config in BLENDED for alpha in ALPHAS]


def blend_name(config: RunConfig, alpha: float) -> str:
    return f"{config.name}-wise{alpha:g}"


def runs_of(config: RunConfig) -> list[RunConfig]:
    """The config on all the data, then on each fold."""
    return [config] + [config.model_copy(update={"fold": f}) for f in range(FOLDS)]


GRID = [run for config in CONFIGS for run in runs_of(config)]


class ZeroShotLine(BaseModel):
    fold_accuracies: list[float]
    mean: float


class GridRow(BaseModel):
    run: str
    epoch: int
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float
    node_dev_accuracy: float
    fold_accuracies: list[float]
    mean_fold_accuracy: float
    qualifies: bool


class Settings(BaseModel):
    run: str
    """The full run whose checkpoint the model starts from."""
    blend: float | None
    """WiSE-FT's alpha toward that checkpoint from the frozen backbone; None when unblended."""
    epoch: int
    choice_temperature: float
    noul_temperature: float
    checkpoint_sha256: str
    commit: str
    zero_shot: ZeroShotLine
    grid: list[GridRow]


def zero_shot_line(embed: zero_shot.Embed, dev: Sequence[Record], catalog: Catalog) -> ZeroShotLine:
    """The frozen zero-shot rung on each fold's lines, offered the decision model's options."""
    settings = zero_shot.Settings.model_validate_json(zero_shot.SETTINGS.read_text("utf-8"))
    intents = trained_intents(catalog)
    labels = [*intents, OUT_OF_SCOPE]
    texts = [*(catalog.intents[i] for i in intents), settings.out_of_scope_option]
    accuracies = []
    for removed in folds(intents):
        lines = naming(dev, removed)
        logits = zero_shot.cosines(embed, lines, texts, settings.instruction)
        scored = zero_shot.score(logits, labels, lines, settings.temperature)
        accuracies.append(in_scope_accuracy(scored))
    return ZeroShotLine(fold_accuracies=accuracies, mean=sum(accuracies) / len(accuracies))


def pick(grid: Sequence[GridRow]) -> GridRow | None:
    """The best qualifying row by the rung rule, if any qualifies."""
    qualified = [row for row in grid if row.qualifies]
    return rung.best(qualified) if qualified else None


def config_rows(results: Mapping[str, DecisionRun], line: float) -> list[GridRow]:
    return [_row(config, results, line) for config in CONFIGS]


@dataclass(frozen=True)
class _Scoring:
    """What scoring a checkpoint on dev needs, loaded once."""

    runs: Path
    results: Mapping[str, DecisionRun]
    catalog: Catalog
    dev: list[Record]
    node_dev: list[NodeQuestion]
    tokenizer: Tokenizer
    frozen: dict[str, torch.Tensor]

    def model(self, run: str, alpha: float | None) -> DecisionModel:
        result = self.results[run]
        model = DecisionModel(load_backbone(), result.config.head)
        model.load_state_dict(load_weights(self.runs / run, result.checkpoint_sha256))
        if alpha is not None:
            blend(model.backbone, self.frozen, alpha)
        return model


def blend_row(config: RunConfig, alpha: float, scoring: _Scoring, line: float) -> GridRow:
    """A blend scored as its config was: dev from the full run, the folds from the fold runs."""
    intents = trained_intents(scoring.catalog)
    model = scoring.model(config.name, alpha)
    scored = predict(model, scoring.dev, intents, scoring.catalog, scoring.tokenizer)
    fold_accuracies = []
    for removed, fold in zip(folds(intents), runs_of(config)[1:], strict=True):
        lines = naming(scoring.dev, removed)
        fold_model = scoring.model(fold.name, alpha)
        unseen = predict(fold_model, lines, intents, scoring.catalog, scoring.tokenizer)
        fold_accuracies.append(in_scope_accuracy(unseen))
    full = scoring.results[config.name]
    mean = sum(fold_accuracies) / len(fold_accuracies)
    return GridRow(
        run=blend_name(config, alpha),
        epoch=full.chosen_epoch,
        dev_macro_f1=macro_f1(scored),
        dev_log_loss=log_loss(scored),
        dev_in_scope_accuracy=in_scope_accuracy(scored),
        node_dev_accuracy=node_accuracy(model, scoring.node_dev, scoring.tokenizer),
        fold_accuracies=fold_accuracies,
        mean_fold_accuracy=mean,
        qualifies=mean >= line,
    )


def choose(runs: Path = RUNS_DIR) -> tuple[list[GridRow], ZeroShotLine, Settings | None]:
    catalog = load_catalog()
    dev = rung.read_clean("dev")
    results = {
        run.name: DecisionRun.model_validate_json((runs / run.name / RESULT).read_text("utf-8"))
        for run in GRID
    }
    line = zero_shot_line(embed_cached, dev, catalog)
    scoring = _Scoring(
        runs=runs,
        results=results,
        catalog=catalog,
        dev=dev,
        node_dev=read_questions(DEFAULT_DATA_DIR / "nodes" / "dev.jsonl"),
        tokenizer=decision_tokenizer(download()[1]),
        frozen=load_backbone().state_dict(),
    )
    sources = {config.name: (config.name, None) for config in CONFIGS} | {
        blend_name(config, alpha): (config.name, alpha) for config, alpha in BLENDS
    }
    grid = config_rows(results, line.mean)
    grid += [blend_row(config, alpha, scoring, line.mean) for config, alpha in BLENDS]
    best = pick(grid)
    if best is None:
        return grid, line, None
    run, alpha = sources[best.run]
    model = scoring.model(run, alpha)
    intents = trained_intents(catalog)
    temperatures = fit_temperatures(
        decision_logits(model, dev, intents, catalog, scoring.tokenizer), dev, intents
    )
    settings = Settings(
        run=run,
        blend=alpha,
        epoch=best.epoch,
        choice_temperature=temperatures.choice,
        noul_temperature=temperatures.noul,
        checkpoint_sha256=results[run].checkpoint_sha256,
        commit=results[run].commit,
        zero_shot=line,
        grid=grid,
    )
    return grid, line, settings


def _row(config: RunConfig, results: Mapping[str, DecisionRun], line: float) -> GridRow:
    full = results[config.name]
    kept = full.epochs[full.chosen_epoch]
    fold_accuracies = []
    for fold in runs_of(config)[1:]:
        result = results[fold.name]
        accuracy = result.epochs[result.chosen_epoch].fold_accuracy
        if accuracy is None:
            raise ValueError(f"{fold.name} has no fold accuracy")
        fold_accuracies.append(accuracy)
    mean = sum(fold_accuracies) / len(fold_accuracies)
    return GridRow(
        run=config.name,
        epoch=kept.epoch,
        dev_macro_f1=kept.dev_macro_f1,
        dev_log_loss=kept.dev_log_loss,
        dev_in_scope_accuracy=kept.dev_in_scope_accuracy,
        node_dev_accuracy=kept.node_dev_accuracy,
        fold_accuracies=fold_accuracies,
        mean_fold_accuracy=mean,
        qualifies=mean >= line,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "choose", help=f"pick the config on dev under the guard; write {SETTINGS.name}"
    )
    parser.parse_args()

    grid, line, settings = choose()
    print(
        f"zero-shot line on the folds: {line.mean:.1%} {[f'{a:.1%}' for a in line.fold_accuracies]}"
    )
    for row in grid:
        mark = "qualifies" if row.qualifies else "below the line"
        print(
            f"{row.run}: dev macro-F1 {row.dev_macro_f1:.1%}, folds {row.mean_fold_accuracy:.1%} "
            f"{[f'{a:.1%}' for a in row.fold_accuracies]} ({mark})"
        )
    if settings is None:
        print("no config qualifies; nothing written")
        return
    SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"{settings.run}, blend {settings.blend}, epoch {settings.epoch}, "
        f"T choice {settings.choice_temperature}, "
        f"T noul {settings.noul_temperature}"
    )
    print(f"written to {SETTINGS}; commit it before scoring the test")
