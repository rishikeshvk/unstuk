"""Scores a decider on the proxy test set with the metrics fixed in M3 spec section 10.

A prediction is a probability per label; empty means the decider declined. The risk gate's
lines turn it into what the app would do: the safety numbers count that.
"""

import json
import random
from collections import Counter
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from sklearn.metrics import f1_score

from unstuk_ml.catalog import CATALOG_DIR
from unstuk_ml.labels import HELD_OUT, OUT_OF_SCOPE, VAGUE
from unstuk_ml.record import Record

GATE_FILE = CATALOG_DIR / "gate.json"
BINS = 10
RESAMPLES = 1000
SEED = 19


@dataclass(frozen=True)
class GateLines:
    """The risk gate's lines on the top intent's probability, as the app reads them."""

    automatic_at: float
    clarify_below: float
    clarify_margin: float
    """Clarify when the top two intents are closer than this, however sure the top one is."""


# The placeholder lines M3 to M5 were scored with, kept so their reports reproduce.
M2_GATE = GateLines(automatic_at=0.8, clarify_below=0.5, clarify_margin=0.0)


def load_gate(path: Path = GATE_FILE) -> GateLines:
    return GateLines(**json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class Scored:
    record: Record
    probabilities: dict[str, float]
    gate: GateLines = M2_GATE

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
        if p < self.gate.clarify_below or p - self._runner_up < self.gate.clarify_margin:
            return "clarify"
        return "automatic" if p >= self.gate.automatic_at else "confirm"

    @property
    def _runner_up(self) -> float:
        """The second most likely intent's probability; out of scope is not an intent."""
        intents = sorted(
            (p for label, p in self.probabilities.items() if label != OUT_OF_SCOPE), reverse=True
        )
        return intents[1] if len(intents) > 1 else 0.0


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


@dataclass(frozen=True)
class CalibrationBin:
    low: float
    confidence: float
    """The mean probability of the top answer in the bin."""
    accuracy: float
    count: int


def calibration_bins(items: Sequence[Scored]) -> list[CalibrationBin]:
    """Answered clear lines by the top answer's probability, in `BINS` equal bins; empty ones left
    out."""
    answered = [s for s in items if not s.vague and s.probabilities]
    found = []
    for b in range(BINS):
        low, high = b / BINS, (b + 1) / BINS
        in_bin = [s for s in answered if low < s.top[1] <= high or (b == 0 and s.top[1] == 0)]
        if in_bin:
            confidence = sum(s.top[1] for s in in_bin) / len(in_bin)
            accuracy = _share(s.correct for s in in_bin)
            found.append(CalibrationBin(low, confidence, accuracy, len(in_bin)))
    return found


def expected_calibration_error(items: Sequence[Scored]) -> float:
    """Average gap between confidence and accuracy, weighted by how many lines fall in each bin."""
    found = calibration_bins(items)
    if not found:
        return float("nan")
    gap = 0.0
    for b in found:
        gap += b.count * abs(b.confidence - b.accuracy)
    return gap / sum(b.count for b in found)


def brier_score(items: Sequence[Scored]) -> float:
    """Mean squared distance between the probabilities and the first label, on clear lines; a
    decline puts nothing on any label."""
    clear = [s for s in items if not s.vague]
    total = 0.0
    for item in clear:
        gold = item.record.labels[0]
        total += sum((p - (label == gold)) ** 2 for label, p in item.probabilities.items())
        total += 0.0 if gold in item.probabilities else 1.0
    return total / len(clear)


def bootstrap(
    items: Sequence[Scored], metric: Metric, seed: int = SEED, strata: Sequence[str] | None = None
) -> tuple[float, float]:
    """A 95% interval: the metric on 1,000 resamples of the lines, with replacement.

    With strata, lines are resampled within each stratum, so every stratum keeps its count.
    """
    values = (metric([items[i] for i in drawn]) for drawn in _resamples(len(items), seed, strata))
    return _interval(values)


def share_interval(flags: Sequence[bool], seed: int = SEED) -> tuple[float, float]:
    """A 95% bootstrap interval for the share of true flags, for results that aren't `Scored`."""
    return _interval(_share(flags[i] for i in drawn) for drawn in _resamples(len(flags), seed))


def paired_bootstrap(
    base: Sequence[Scored],
    challenger: Sequence[Scored],
    metric: Metric,
    seed: int = SEED,
    strata: Sequence[str] | None = None,
) -> tuple[float, float]:
    """A 95% interval on challenger minus base, both scored on the same resampled lines."""
    _require_pairs(base, challenger)
    differences = (
        metric([challenger[i] for i in drawn]) - metric([base[i] for i in drawn])
        for drawn in _resamples(len(base), seed, strata)
    )
    return _interval(differences)


def beats(base: Sequence[Scored], challenger: Sequence[Scored]) -> bool:
    """M4 spec section 3: surely more accurate on both measures, and not surely less safe."""
    return (
        paired_bootstrap(base, challenger, in_scope_accuracy)[0] > 0
        and paired_bootstrap(base, challenger, macro_f1)[0] > 0
        and paired_bootstrap(base, challenger, confident_and_wrong)[0] <= 0
    )


def _resamples(n: int, seed: int, strata: Sequence[str] | None = None) -> Iterator[list[int]]:
    # Drawing indices uses the same random numbers as drawing the items themselves did.
    rng = random.Random(seed)
    if strata is None:
        for _ in range(RESAMPLES):
            yield rng.choices(range(n), k=n)
        return
    if len(strata) != n:
        raise ValueError("one stratum per line")
    groups = [[i for i in range(n) if strata[i] == s] for s in sorted(set(strata))]
    for _ in range(RESAMPLES):
        yield [i for group in groups for i in rng.choices(group, k=len(group))]


def _interval(values: Iterable[float]) -> tuple[float, float]:
    # Drops the NaN of a resample with no line of the kind.
    kept = sorted(v for v in values if v == v)
    if not kept:
        return float("nan"), float("nan")
    return kept[int(0.025 * len(kept))], kept[int(0.975 * len(kept)) - 1]


Confusions = list[tuple[str, str, list[Scored]]]


def confusions(items: Sequence[Scored], top: int = 10) -> Confusions:
    """The most common (given, predicted) mistakes among clear lines, with their lines."""
    return _grouped([s for s in items if not s.vague and not s.correct], top)


def changed(base: Sequence[Scored], challenger: Sequence[Scored]) -> tuple[Confusions, Confusions]:
    """Mistakes the challenger fixed, grouped as base made them, and mistakes it introduced."""
    _require_pairs(base, challenger)
    pairs = [(b, c) for b, c in zip(base, challenger, strict=True) if not b.vague]
    fixed = [b for b, c in pairs if not b.correct and c.correct]
    introduced = [c for b, c in pairs if b.correct and not c.correct]
    return _grouped(fixed, None), _grouped(introduced, None)


def _grouped(wrong: Sequence[Scored], top: int | None) -> Confusions:
    pairs = Counter((s.record.labels[0], s.top[0]) for s in wrong)
    return [
        (given, said, [s for s in wrong if (s.record.labels[0], s.top[0]) == (given, said)])
        for (given, said), _ in pairs.most_common(top)
    ]


def _require_pairs(base: Sequence[Scored], challenger: Sequence[Scored]) -> None:
    if [s.record.id for s in base] != [s.record.id for s in challenger]:
        raise ValueError("a paired comparison needs the same lines in the same order")


def _share(flags: Iterable[bool]) -> float:
    values = list(flags)
    return sum(values) / len(values) if values else float("nan")
