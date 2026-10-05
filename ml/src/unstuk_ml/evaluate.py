"""Scores a decider on the proxy test set with the metrics fixed in M3 spec section 10.

A prediction is a probability per label; empty means the decider declined. The risk gate's
thresholds (`decide/RiskGate.kt`) turn it into what the app would do: the safety numbers count that.
"""

import random
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from sklearn.metrics import f1_score

from unstuk_ml.labels import HELD_OUT, OUT_OF_SCOPE, VAGUE
from unstuk_ml.record import Record

CLARIFY_BELOW = 0.5
AUTOMATIC_AT = 0.8
BINS = 10
RESAMPLES = 1000
SEED = 19


@dataclass(frozen=True)
class Scored:
    record: Record
    probabilities: dict[str, float]

    @property
    def top(self) -> tuple[str, float]:
        """The predicted label and its probability; a decline is out of scope with no confidence."""
        if not self.probabilities:
            return OUT_OF_SCOPE, 0.0
        label = max(self.probabilities, key=lambda k: (self.probabilities[k], k))
        return label, self.probabilities[label]

    @property
    def correct(self) -> bool:
        return self.top[0] in self.record.labels

    @property
    def vague(self) -> bool:
        return VAGUE in self.record.tags

    @property
    def outcome(self) -> str:
        """What the gate would do, before diagnosis picks a fix and its risk tier."""
        label, p = self.top
        if not self.probabilities or label == OUT_OF_SCOPE:
            return "decline"
        if p < CLARIFY_BELOW:
            return "clarify"
        return "automatic" if p >= AUTOMATIC_AT else "confirm"


Metric = Callable[[Sequence[Scored]], float]


def accuracy(items: Sequence[Scored]) -> float:
    clear = [s for s in items if not s.vague]
    return _share(s.correct for s in clear)


def in_scope_accuracy(items: Sequence[Scored]) -> float:
    return accuracy([s for s in items if s.record.labels != [OUT_OF_SCOPE]])


def macro_f1(items: Sequence[Scored]) -> float:
    clear = [s for s in items if not s.vague]
    if not clear:
        return float("nan")
    truth = [s.record.labels[0] for s in clear]
    # A line with two problems counts as right when the pick is either of them.
    predicted = [s.record.labels[0] if s.correct else s.top[0] for s in clear]
    return float(
        f1_score(truth, predicted, labels=sorted(set(truth)), average="macro", zero_division=0)
    )


def out_of_scope_recall(items: Sequence[Scored]) -> float:
    actual = [s for s in items if not s.vague and s.record.labels == [OUT_OF_SCOPE]]
    return _share(s.top[0] == OUT_OF_SCOPE for s in actual)


def out_of_scope_precision(items: Sequence[Scored]) -> float:
    called = [s for s in items if not s.vague and s.top[0] == OUT_OF_SCOPE]
    return _share(s.record.labels == [OUT_OF_SCOPE] for s in called)


def confident_and_wrong(items: Sequence[Scored]) -> float:
    """Lines where the gate would run a fix by itself, for the wrong problem."""
    clear = [s for s in items if not s.vague]
    return _share(s.outcome == "automatic" and not s.correct for s in clear)


def vague_handled(items: Sequence[Scored]) -> float:
    """Unclear lines answered with a question or a decline, not a confident pick."""
    return _share(s.outcome in ("clarify", "decline") for s in items if s.vague)


def held_out_accuracy(items: Sequence[Scored]) -> float:
    return accuracy([s for s in items if s.record.labels[0] in HELD_OUT])


def expected_calibration_error(items: Sequence[Scored]) -> float:
    """Average gap between confidence and accuracy, weighted by how many lines fall in each bin."""
    answered = [s for s in items if not s.vague and s.probabilities]
    if not answered:
        return float("nan")
    gap = 0.0
    for b in range(BINS):
        low, high = b / BINS, (b + 1) / BINS
        in_bin = [s for s in answered if low < s.top[1] <= high or (b == 0 and s.top[1] == 0)]
        if in_bin:
            confidence = sum(s.top[1] for s in in_bin) / len(in_bin)
            gap += len(in_bin) * abs(confidence - _share(s.correct for s in in_bin))
    return gap / len(answered)


def bootstrap(items: Sequence[Scored], metric: Metric, seed: int = SEED) -> tuple[float, float]:
    """A 95% interval: the metric on 1,000 resamples of the lines, with replacement."""
    rng = random.Random(seed)
    values = sorted(
        v
        for v in (metric(rng.choices(items, k=len(items))) for _ in range(RESAMPLES))
        if v == v  # drops the NaN of a resample with no line of the kind
    )
    return values[int(0.025 * len(values))], values[int(0.975 * len(values)) - 1]


def confusions(items: Sequence[Scored], top: int = 10) -> list[tuple[str, str, list[Scored]]]:
    """The most common (given, predicted) mistakes among clear lines, with their lines."""
    wrong = [s for s in items if not s.vague and not s.correct]
    pairs = Counter((s.record.labels[0], s.top[0]) for s in wrong)
    return [
        (given, said, [s for s in wrong if (s.record.labels[0], s.top[0]) == (given, said)])
        for (given, said), _ in pairs.most_common(top)
    ]


def _share(flags: Iterable[bool]) -> float:
    values = list(flags)
    return sum(values) / len(values) if values else float("nan")
