"""Choosing the decision model (M5 spec section 3): a dev grid under a zero-shot guard.

Every config trains on all the data and on three leave-intents-out folds. A config qualifies only
if, on the folds, it names intents it never trained on at least as well as the frozen zero-shot
rung does on the same lines; among those, the rung rule picks on dev. Nothing here reads the test.
"""

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel

from unstuk_ml import rung, zero_shot
from unstuk_ml.backbone import load_backbone
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel, Head
from unstuk_ml.decision_scoring import decision_logits, fit_temperatures
from unstuk_ml.decision_training import DecisionRun, RunConfig
from unstuk_ml.encoder import download, embed_cached
from unstuk_ml.evaluate import in_scope_accuracy
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.folds import FOLDS, folds, naming, trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.record import Record

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
CONFIGS = ROUND_1 + ROUND_2


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


def pick(results: Mapping[str, DecisionRun], line: float) -> tuple[list[GridRow], GridRow | None]:
    """Every config's row, and the best qualifying one by the rung rule, if any qualifies."""
    grid = [_row(config, results, line) for config in CONFIGS]
    qualified = [row for row in grid if row.qualifies]
    return grid, rung.best(qualified) if qualified else None


def choose(runs: Path = RUNS_DIR) -> tuple[list[GridRow], ZeroShotLine, Settings | None]:
    catalog = load_catalog()
    dev = rung.read_clean("dev")
    results = {
        run.name: DecisionRun.model_validate_json((runs / run.name / RESULT).read_text("utf-8"))
        for run in GRID
    }
    line = zero_shot_line(embed_cached, dev, catalog)
    grid, best = pick(results, line.mean)
    if best is None:
        return grid, line, None
    chosen = results[best.run]
    model = DecisionModel(load_backbone(), chosen.config.head)
    model.load_state_dict(load_weights(runs / best.run, chosen.checkpoint_sha256))
    intents = trained_intents(catalog)
    tokenizer = decision_tokenizer(download()[1])
    temperatures = fit_temperatures(
        decision_logits(model, dev, intents, catalog, tokenizer), dev, intents
    )
    settings = Settings(
        run=best.run,
        epoch=best.epoch,
        choice_temperature=temperatures.choice,
        noul_temperature=temperatures.noul,
        checkpoint_sha256=chosen.checkpoint_sha256,
        commit=chosen.commit,
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
            f"({mark})"
        )
    if settings is None:
        print("no config qualifies; nothing written")
        return
    SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"{settings.run}, epoch {settings.epoch}, T choice {settings.choice_temperature}, "
        f"T noul {settings.noul_temperature}"
    )
    print(f"written to {SETTINGS}; commit it before scoring the test")
