"""The bar for M5 (m4-results.md): per metric, the best M4 baseline, and what M5 must do against it.

"Better" means the paired 95% interval lies on the good side of 0; "not worse" means it doesn't
lie on the bad side. For confident and wrong and for calibration error, lower is better.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import (
    Metric,
    Scored,
    confident_and_wrong,
    expected_calibration_error,
    held_out_accuracy,
    in_scope_accuracy,
    macro_f1,
    out_of_scope_recall,
    paired_bootstrap,
)
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.zero_shot import ZERO_SHOT

Must = Literal["better", "not worse"]


@dataclass(frozen=True)
class Requirement:
    name: str
    metric: Metric
    rung: str
    """The title of the baseline that sets the bar."""
    must: Must
    higher_is_better: bool


BAR = (
    Requirement("Top-1 accuracy, in scope", in_scope_accuracy, ZERO_SHOT.title, "better", True),
    Requirement("Macro-F1", macro_f1, ENCODER.decider.title, "better", True),
    Requirement(
        "Confident and wrong", confident_and_wrong, TFIDF.decider.title, "not worse", False
    ),
    Requirement("Out-of-scope recall", out_of_scope_recall, TFIDF.decider.title, "not worse", True),
    Requirement("Held-out intents", held_out_accuracy, ZERO_SHOT.title, "not worse", True),
    Requirement(
        "Expected calibration error",
        expected_calibration_error,
        ZERO_SHOT.title,
        "not worse",
        False,
    ),
)


@dataclass(frozen=True)
class BarRow:
    requirement: Requirement
    bar: float
    value: float
    interval: tuple[float, float]
    """Paired 95% interval on the decider minus the baseline."""

    @property
    def passes(self) -> bool:
        low, high = self.interval
        if self.requirement.must == "better":
            return low > 0 if self.requirement.higher_is_better else high < 0
        return high >= 0 if self.requirement.higher_is_better else low <= 0


def check(decider: Sequence[Scored], baselines: Mapping[str, Sequence[Scored]]) -> list[BarRow]:
    """Every requirement, against the baseline that sets it, scored on the same lines."""
    rows = []
    for requirement in BAR:
        base = baselines[requirement.rung]
        rows.append(
            BarRow(
                requirement=requirement,
                bar=requirement.metric(base),
                value=requirement.metric(decider),
                interval=paired_bootstrap(base, decider, requirement.metric),
            )
        )
    return rows
