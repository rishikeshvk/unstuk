"""Out of scope fitted out of fold (M6 spec section 4): one try, with a stop rule.

Every out-of-scope check in M5 was fitted on intents the model had trained on, so it learned that
an unfamiliar intent looks out of scope. A fold model never trained on its removed intents, so its
dev scores show what "in scope but unfamiliar" looks like, and a gate fitted on them can learn it.
"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression

from unstuk_ml import rung
from unstuk_ml.backbone import load_backbone
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.decision_rung import runs_of
from unstuk_ml.decision_scoring import (
    Logits,
    Temperatures,
    decision_logits,
    fit_temperatures,
    scored,
)
from unstuk_ml.decision_training import DecisionRun, RunConfig, noul_input
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import Scored, in_scope_accuracy, out_of_scope_recall
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.folds import folds, trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.record import Record

# The guard, fixed in the spec before any run.
MAX_UNSEEN_DECLINED = 0.10
MAX_RECALL_DROP = 0.02


@dataclass(frozen=True)
class FoldScores:
    """A fold model's logits on every dev line, and the intents it never trained on."""

    logits: Logits
    removed: frozenset[str]


@dataclass(frozen=True)
class TwoFeatureGate:
    """`p(out of scope) = sigmoid(a · best Choice logit + b · Noul logit + bias)`."""

    choice_weight: float
    noul_weight: float
    bias: float

    def apply(self, logits: Logits) -> Logits:
        z = (
            self.choice_weight * logits.choice.max(axis=1)
            + self.noul_weight * logits.out_of_scope
            + self.bias
        )
        return Logits(logits.choice, z)


def fit_out_of_fold(folds_scores: Sequence[FoldScores], dev: Sequence[Record]) -> TwoFeatureGate:
    """Logistic regression by log-loss over every fold's dev lines pooled; a removed intent's lines
    count as in scope, which is the point."""
    features = np.concatenate([_features(f.logits) for f in folds_scores])
    targets = np.concatenate([_targets(dev)] * len(folds_scores))
    regression = LogisticRegression(C=np.inf).fit(features, targets)
    (choice_weight, noul_weight), bias = regression.coef_[0], regression.intercept_[0]
    return TwoFeatureGate(float(choice_weight), float(noul_weight), float(bias))


def declined(items: Sequence[Scored]) -> float:
    """The share of lines whose top answer is out of scope."""
    return sum(s.top[0] == OUT_OF_SCOPE for s in items) / len(items)


@dataclass(frozen=True)
class Guard:
    unseen_declined: list[float]
    """Per fold: the share of its unseen intents' lines the gate calls out of scope."""
    unseen_accuracy: list[float]
    """Per fold: accuracy on those lines, comparable with M5's fold accuracy and its 78.7% line."""
    noul_recall: float
    gate_recall: float
    """Dev out-of-scope recall of the full model, with Noul and with the all-folds gate."""

    @property
    def mean_declined(self) -> float:
        return sum(self.unseen_declined) / len(self.unseen_declined)

    @property
    def passes(self) -> bool:
        return (
            self.mean_declined <= MAX_UNSEEN_DECLINED
            and self.gate_recall >= self.noul_recall - MAX_RECALL_DROP
        )


def guard(
    folds_scores: Sequence[FoldScores],
    full: Logits,
    dev: Sequence[Record],
    intents: Sequence[str],
) -> Guard:
    """Nested: each fold's unseen intents are scored by a gate fitted on the other folds only."""
    declines, accuracies = [], []
    for n, held in enumerate(folds_scores):
        gate = fit_out_of_fold([f for m, f in enumerate(folds_scores) if m != n], dev)
        lines = [i for i, r in enumerate(dev) if held.removed & set(r.labels)]
        logits = gate.apply(held.logits)
        unseen = scored(_rows(logits, lines), [dev[i] for i in lines], intents)
        declines.append(declined(unseen))
        accuracies.append(in_scope_accuracy(unseen))
    temperatures = fit_temperatures(full, dev, intents)
    gated = Temperatures(choice=temperatures.choice, noul=1.0)
    gate = fit_out_of_fold(folds_scores, dev)
    return Guard(
        unseen_declined=declines,
        unseen_accuracy=accuracies,
        noul_recall=out_of_scope_recall(scored(full, dev, intents, temperatures)),
        gate_recall=out_of_scope_recall(scored(gate.apply(full), dev, intents, gated)),
    )


def _features(logits: Logits) -> NDArray[np.float64]:
    return np.stack([logits.choice.max(axis=1), logits.out_of_scope], axis=1)


def _targets(dev: Sequence[Record]) -> NDArray[np.bool_]:
    return np.array([r.labels[0] == OUT_OF_SCOPE for r in dev])


def _rows(logits: Logits, rows: Sequence[int]) -> Logits:
    return Logits(logits.choice[rows], logits.out_of_scope[rows])


def run_guard(config: RunConfig, runs: Path = RUNS_DIR) -> tuple[Guard, TwoFeatureGate]:
    """Scores the config's full and fold checkpoints on dev, on CPU."""
    catalog = load_catalog()
    dev = rung.read_clean("dev")
    intents = trained_intents(catalog)
    tokenizer = decision_tokenizer(download()[1])

    def logits_of(run: RunConfig) -> Logits:
        result = DecisionRun.model_validate_json((runs / run.name / RESULT).read_text("utf-8"))
        model = DecisionModel(load_backbone(), run.head, noul_input(run))
        model.load_state_dict(load_weights(runs / run.name, result.checkpoint_sha256))
        return decision_logits(model, dev, intents, catalog, tokenizer)

    full, *fold_runs = runs_of(config)
    folds_scores = [
        FoldScores(logits_of(run), removed)
        for run, removed in zip(fold_runs, folds(intents), strict=True)
    ]
    full_logits = logits_of(full)
    return guard(folds_scores, full_logits, dev, intents), fit_out_of_fold(folds_scores, dev)


def report(config: RunConfig, result: Guard, gate: TwoFeatureGate) -> str:
    folds_line = ", ".join(
        f"{d:.1%} declined / {a:.1%} right"
        for d, a in zip(result.unseen_declined, result.unseen_accuracy, strict=True)
    )
    return "\n".join(
        [
            f"## `{config.name}`",
            "",
            f"- Unseen intents' lines, per fold: {folds_line}.",
            f"- Mean declined: **{result.mean_declined:.1%}** "
            f"(must be ≤ {MAX_UNSEEN_DECLINED:.0%}).",
            f"- Dev out-of-scope recall: Noul {result.noul_recall:.1%}, gate "
            f"{result.gate_recall:.1%} (may drop ≤ {MAX_RECALL_DROP:.0%}).",
            f"- Gate fitted on all folds: {json.dumps(asdict(gate))}.",
            f"- **{'Passes' if result.passes else 'Fails'}.**",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", help="full-run names whose fold runs are in ml/runs")
    args = parser.parse_args()
    for name in args.runs:
        result = DecisionRun.model_validate_json((RUNS_DIR / name / RESULT).read_text("utf-8"))
        guarded, gate = run_guard(result.config)
        print(report(result.config, guarded, gate), flush=True)
