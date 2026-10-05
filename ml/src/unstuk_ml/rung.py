"""The protocol every learned rung follows (M4 spec section 2): features, then logistic regression.

`tune` tries the grid on dev and writes the chosen settings down; `test` reads them back and
scores the frozen test set once. Committing the settings between the two shows they came first.
"""

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel
from sklearn.pipeline import Pipeline

from unstuk_ml.baseline_report import Below, Decider, Table, load_test, write
from unstuk_ml.evaluate import Scored, in_scope_accuracy, macro_f1
from unstuk_ml.record import Record
from unstuk_ml.temperature import fit_temperature, negative_log_likelihood, softmax
from unstuk_ml.validate import DEFAULT_DATA_DIR

ClassWeight = Literal["balanced"] | None
SETTINGS_DIR = DEFAULT_DATA_DIR.parent / "ml" / "settings"
CLEAN_DIR = DEFAULT_DATA_DIR / "clean"


@dataclass(frozen=True)
class Rung:
    decider: Decider
    grid: list[tuple[float, ClassWeight]]
    build: Callable[[float, ClassWeight], Pipeline]
    """An untrained pipeline for one grid point."""
    settings: Path
    extensions: tuple[float, ...] = ()
    """Larger C values tried in turn while dev's winner sits at the top of the grid."""


class Trial(BaseModel):
    c: float
    class_weight: ClassWeight
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float


class Settings(BaseModel):
    c: float
    class_weight: ClassWeight
    temperature: float
    grid: list[Trial]


def examples(records: Sequence[Record]) -> tuple[list[str], list[str]]:
    """One row per label, so a line with two problems teaches both (M4 spec section 2)."""
    rows = [(r.text, label) for r in records for label in r.labels]
    return [text for text, _ in rows], [label for _, label in rows]


def train(rung: Rung, records: Sequence[Record], c: float, class_weight: ClassWeight) -> Pipeline:
    model = rung.build(c, class_weight)
    texts, labels = examples(records)
    model.fit(texts, labels)
    return model


def logits(model: Pipeline, records: Sequence[Record]) -> NDArray[np.float64]:
    return np.asarray(model.decision_function([r.text for r in records]), dtype=np.float64)


def score(model: Pipeline, temperature: float, records: Sequence[Record]) -> list[Scored]:
    classes = [str(c) for c in model.classes_]
    probabilities = softmax(logits(model, records), temperature)
    return [
        Scored(r, dict(zip(classes, map(float, row), strict=True)))
        for r, row in zip(records, probabilities, strict=True)
    ]


def tune(rung: Rung, train_records: Sequence[Record], dev: Sequence[Record]) -> Settings:
    """Tries every grid point on dev, keeps the best and fits its temperature on dev."""
    trials = [_trial(rung, train_records, dev, c, w) for c, w in rung.grid]
    weights = list(dict.fromkeys(w for _, w in rung.grid))
    extensions = list(rung.extensions)
    while extensions and best(trials).c == max(t.c for t in trials):
        c = extensions.pop(0)
        trials += [_trial(rung, train_records, dev, c, w) for w in weights]
    chosen = best(trials)
    model = train(rung, train_records, chosen.c, chosen.class_weight)
    return Settings(
        c=chosen.c,
        class_weight=chosen.class_weight,
        temperature=fit_temperature(logits(model, dev), _targets(model, dev)),
        grid=trials,
    )


def best(trials: Sequence[Trial]) -> Trial:
    """Highest dev macro-F1; ties go to the lower log-loss, then to the earlier grid point."""
    return trials[
        min(range(len(trials)), key=lambda i: (-trials[i].dev_macro_f1, trials[i].dev_log_loss, i))
    ]


def load(rung: Rung) -> tuple[Settings, Pipeline]:
    """The frozen settings and the model they train; refuses before `tune` has written them."""
    settings = Settings.model_validate_json(rung.settings.read_text(encoding="utf-8"))
    return settings, train(rung, read_clean("train"), settings.c, settings.class_weight)


def test(rung: Rung, below: Callable[[list[Record]], Below]) -> None:
    settings, model = load(rung)
    lines = load_test()
    about = (
        f"{rung.decider.about}; C = {settings.c}, class weight "
        f"{settings.class_weight or 'none'}, temperature {settings.temperature} fitted on dev"
    )
    write(
        replace(rung.decider, about=about),
        score(model, settings.temperature, lines),
        before_temperature=score(model, 1.0, lines),
        below=below(lines),
        tuning=_tuning_table(settings),
    )


def read_clean(split: str) -> list[Record]:
    return [
        Record.model_validate_json(line)
        for line in (CLEAN_DIR / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main(rung: Rung, below: Callable[[list[Record]], Below]) -> None:
    parser = argparse.ArgumentParser(description=f"{rung.decider.title}: {__doc__}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tune", help=f"choose settings on dev and write {rung.settings.name}")
    commands.add_parser("test", help="score the frozen test set once with the written settings")
    args = parser.parse_args()

    if args.command == "test":
        test(rung, below)
        return
    settings = tune(rung, read_clean("train"), read_clean("dev"))
    rung.settings.parent.mkdir(parents=True, exist_ok=True)
    rung.settings.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"C={settings.c}, class weight {settings.class_weight}, T={settings.temperature}")
    print(f"written to {rung.settings}; commit it before running `test`")


def _trial(
    rung: Rung,
    train_records: Sequence[Record],
    dev: Sequence[Record],
    c: float,
    class_weight: ClassWeight,
) -> Trial:
    model = train(rung, train_records, c, class_weight)
    scored = score(model, 1.0, dev)
    return Trial(
        c=c,
        class_weight=class_weight,
        dev_macro_f1=macro_f1(scored),
        dev_log_loss=negative_log_likelihood(logits(model, dev), _targets(model, dev), 1.0),
        dev_in_scope_accuracy=in_scope_accuracy(scored),
    )


def _targets(model: Pipeline, records: Sequence[Record]) -> NDArray[np.int64]:
    classes = [str(c) for c in model.classes_]
    return np.array([classes.index(r.labels[0]) for r in records], dtype=np.int64)


def _tuning_table(settings: Settings) -> Table:
    rows = [
        [
            str(t.c),
            t.class_weight or "none",
            f"{t.dev_macro_f1:.1%}",
            f"{t.dev_log_loss:.3f}",
            f"{t.dev_in_scope_accuracy:.1%}",
            "**chosen**" if (t.c, t.class_weight) == (settings.c, settings.class_weight) else "",
        ]
        for t in settings.grid
    ]
    header = ["C", "Class weight", "Macro-F1", "Log-loss", "In-scope accuracy", ""]
    return Table(header, rows)
