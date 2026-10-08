"""The gate's lines, tuned on dev by the rule fixed in the M6 spec (section 5) before any run.

`automatic_at` comes from clear dev lines alone: the lowest line at which automatic picks are wrong
at most 2% of the time. The clarify lines then catch as many vague dev lines as they can while
asking about few clear ones.
"""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from unstuk_ml.evaluate import GateLines, Scored, vague_handled
from unstuk_ml.labels import OUT_OF_SCOPE

AUTOMATIC_GRID = (*(round(0.5 + 0.05 * n, 2) for n in range(10)), 0.99)
CLARIFY_BELOW_GRID = (0.3, 0.4, 0.5, 0.6, 0.7)
CLARIFY_MARGIN_GRID = tuple(round(0.05 * n, 2) for n in range(9))
MAX_AUTOMATIC_WRONG = 0.02
MAX_CLEAR_CLARIFIED = 0.08


@dataclass(frozen=True)
class Tuning:
    lines: GateLines
    automatic_wrong: float
    """Of clear dev lines picked automatically, the share picked wrong."""
    clear_clarified: float
    """Of clear in-scope dev lines, the share asked about."""
    vague_handled: float
    """Of vague dev lines, the share asked about or declined."""


def tune(clear: Sequence[Scored], vague: Sequence[Scored]) -> Tuning:
    """`clear` is dev without vague lines; `vague` is the vague slice's dev."""
    automatic_at = _automatic_at(clear)
    in_scope = [s for s in clear if s.record.labels[0] != OUT_OF_SCOPE]
    candidates = [
        GateLines(automatic_at, below, margin)
        for below in CLARIFY_BELOW_GRID
        if below <= automatic_at
        for margin in CLARIFY_MARGIN_GRID
    ]
    allowed = [g for g in candidates if _clarified(in_scope, g) <= MAX_CLEAR_CLARIFIED]
    # Ties go to the smaller lines: ask no more than the vague lines need.
    best = max(
        allowed,
        key=lambda g: (vague_handled(_under(vague, g)), -g.clarify_below, -g.clarify_margin),
    )
    return Tuning(
        lines=best,
        automatic_wrong=_automatic_wrong(clear, automatic_at),
        clear_clarified=_clarified(in_scope, best),
        vague_handled=vague_handled(_under(vague, best)),
    )


def _automatic_at(clear: Sequence[Scored]) -> float:
    for line in AUTOMATIC_GRID:
        if _automatic_wrong(clear, line) <= MAX_AUTOMATIC_WRONG:
            return line
    raise ValueError(f"automatic picks are wrong over {MAX_AUTOMATIC_WRONG:.0%} at every line")


def _automatic_wrong(clear: Sequence[Scored], line: float) -> float:
    picked = [s for s in clear if s.top[0] != OUT_OF_SCOPE and s.top[1] >= line]
    return sum(not s.correct for s in picked) / len(picked) if picked else 0.0


def _clarified(items: Sequence[Scored], gate: GateLines) -> float:
    return sum(s.outcome == "clarify" for s in _under(items, gate)) / len(items)


def _under(items: Sequence[Scored], gate: GateLines) -> list[Scored]:
    return [replace(s, gate=gate) for s in items]
