"""The shipped graph's test mistakes by cause, split by whether the app would have acted alone."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from unstuk_ml.evaluate import Scored
from unstuk_ml.failures import CAUSES, Cause, Failure
from unstuk_ml.figures.gate_outcomes import OUTCOMES
from unstuk_ml.figures.style import GROUND, MUTED

NAMES: dict[Cause, str] = {
    "lexical_pull": "Words point to another setting",
    "needs_state": "Only the phone's state can tell",
    "collision": "Not about the phone, or sounds like it isn't",
    "held_out": "Held-out intent",
    "two_problems": "Picked the other of two problems",
    "debatable_label": "Label is debatable",
    "wording": "Typos, dialect or odd phrasing",
    "other": "Other",
}
ALONE = OUTCOMES["automatic"]
ASKED = OUTCOMES["decline"]


def tally(coded: Sequence[tuple[Scored, Failure]]) -> dict[Cause, tuple[int, int]]:
    """Per cause, the mistakes the app would run by itself and the ones it would ask about or
    decline; causes with no mistakes left out, the largest first."""
    counts = {
        cause: (
            sum(f.cause == cause and s.outcome == "automatic" for s, f in coded),
            sum(f.cause == cause and s.outcome != "automatic" for s, f in coded),
        )
        for cause in CAUSES
    }
    found = {c: n for c, n in counts.items() if sum(n)}
    return dict(sorted(found.items(), key=lambda kv: -sum(kv[1])))


def draw(coded: Sequence[tuple[Scored, Failure]]) -> Figure:
    counts = tally(coded)
    figure, axes = plt.subplots(figsize=(7.2, 0.45 * len(counts) + 1.2))
    for row, (alone, asked) in enumerate(counts.values()):
        axes.barh(row, alone, height=0.55, color=ALONE, edgecolor=GROUND, linewidth=1)
        axes.barh(row, asked, left=alone, height=0.55, color=ASKED, edgecolor=GROUND, linewidth=1)
        axes.annotate(
            str(alone + asked),
            (alone + asked, row),
            xytext=(4, 0),
            textcoords="offset points",
            va="center",
            color=MUTED,
            fontsize=9,
        )
    axes.set_yticks(range(len(counts)), [NAMES[c] for c in counts])
    axes.set_ylim(len(counts) - 0.5, -0.5)
    axes.tick_params(axis="y", length=0)
    axes.spines["left"].set_visible(False)
    axes.set_xlabel("Test lines")
    axes.xaxis.set_major_locator(MaxNLocator(integer=True))
    axes.legend(
        ["Run by itself", "Asked, clarified or declined"],
        ncols=2,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0, 1.0),
        fontsize=8.5,
        handlelength=1,
        handleheight=1,
    )
    axes.set_title(f"Why the int8 graph got {len(coded)} clear test lines wrong", pad=24)
    return figure
