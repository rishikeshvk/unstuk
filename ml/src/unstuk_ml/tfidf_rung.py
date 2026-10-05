"""The TF-IDF rung (M4 spec section 2): word and character n-grams read by logistic regression.

`tune` picks the settings on dev and writes them down; `test` reads them back and scores the
frozen test set once. Committing the settings between the two shows they came first.
"""

import argparse
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline, make_pipeline

from unstuk_ml.baseline_report import KEYWORDS, REPORTS, Below, Decider, Table, load_test, write
from unstuk_ml.evaluate import Scored, in_scope_accuracy, macro_f1
from unstuk_ml.keyword_matcher import load_matcher
from unstuk_ml.record import Record
from unstuk_ml.temperature import fit_temperature, negative_log_likelihood, softmax
from unstuk_ml.validate import DEFAULT_DATA_DIR

ClassWeight = Literal["balanced"] | None
GRID: list[tuple[float, ClassWeight]] = [
    (c, weight) for c in (0.3, 1.0, 3.0, 10.0, 30.0, 100.0) for weight in (None, "balanced")
]
SETTINGS = DEFAULT_DATA_DIR.parent / "ml" / "settings" / "tfidf.json"
CLEAN_DIR = DEFAULT_DATA_DIR / "clean"
TFIDF = Decider(
    title="TF-IDF + logistic regression",
    command="unstuk-tfidf test",
    about="Word 1-2-grams and character 2-5-grams, read by logistic regression trained on "
    "`data/clean/train.jsonl`",
    held_out_note="no output for them; only a two-problem line whose other problem is trained can "
    "count as right",
    report=REPORTS / "tfidf.md",
)


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


def train(records: Sequence[Record], c: float, class_weight: ClassWeight) -> Pipeline:
    features = FeatureUnion(
        [
            ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2))),
            ("characters", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))),
        ]
    )
    model = make_pipeline(
        features, LogisticRegression(C=c, class_weight=class_weight, max_iter=5000)
    )
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


def tune(train_records: Sequence[Record], dev: Sequence[Record]) -> Settings:
    """Tries every grid point on dev, keeps the best and fits its temperature on dev."""
    trials = []
    for c, weight in GRID:
        model = train(train_records, c, weight)
        scored = score(model, 1.0, dev)
        trials.append(
            Trial(
                c=c,
                class_weight=weight,
                dev_macro_f1=macro_f1(scored),
                dev_log_loss=negative_log_likelihood(logits(model, dev), _targets(model, dev), 1.0),
                dev_in_scope_accuracy=in_scope_accuracy(scored),
            )
        )
    chosen = best(trials)
    model = train(train_records, chosen.c, chosen.class_weight)
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


def _read(path: Path) -> list[Record]:
    return [
        Record.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tune", help=f"choose settings on dev and write {SETTINGS.name}")
    commands.add_parser("test", help="score the frozen test set once with the written settings")
    args = parser.parse_args()

    train_records = _read(CLEAN_DIR / "train.jsonl")
    if args.command == "tune":
        settings = tune(train_records, _read(CLEAN_DIR / "dev.jsonl"))
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"C={settings.c}, class weight {settings.class_weight}, T={settings.temperature}")
        print(f"written to {SETTINGS}; commit it before running `test`")
        return

    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    model = train(train_records, settings.c, settings.class_weight)
    test = load_test()
    matcher = load_matcher()
    about = (
        f"{TFIDF.about}; C = {settings.c}, class weight {settings.class_weight or 'none'}, "
        f"temperature {settings.temperature} fitted on dev"
    )
    write(
        replace(TFIDF, about=about),
        score(model, settings.temperature, test),
        before_temperature=score(model, 1.0, test),
        below=Below(KEYWORDS, [Scored(r, matcher.choose(r.text)) for r in test]),
        tuning=_tuning_table(settings),
    )
