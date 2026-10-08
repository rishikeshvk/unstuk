"""Where the shipped model's test lines land at the risk gate."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from unstuk_ml.evaluate import Scored
from unstuk_ml.figures.style import GROUND, INK
from unstuk_ml.labels import OUT_OF_SCOPE

# From most to least the app does by itself; one hue, validated as an ordinal ramp on Ground.
OUTCOMES = {
    "automatic": "#6E260B",
    "confirm": "#9E3B19",
    "clarify": "#C9532A",
    "decline": "#EB8256",
}


def groups(items: Sequence[Scored]) -> dict[str, list[Scored]]:
    """In scope, out of scope and vague, as the results docs split them."""
    clear = [s for s in items if not s.vague]
    return {
        "In scope": [s for s in clear if s.record.labels != [OUT_OF_SCOPE]],
        "Out of scope": [s for s in clear if s.record.labels == [OUT_OF_SCOPE]],
        "Vague": [s for s in items if s.vague],
    }


def counts(items: Sequence[Scored]) -> dict[str, int]:
    return {o: sum(s.outcome == o for s in items) for o in OUTCOMES}


def draw(items: Sequence[Scored]) -> Figure:
    figure, axes = plt.subplots(figsize=(7.2, 2.6))
    split = groups(items)
    for row, group in enumerate(split.values()):
        left = 0.0
        for outcome, n in counts(group).items():
            share = n / len(group)
            axes.barh(
                row,
                share,
                left=left,
                height=0.5,
                color=OUTCOMES[outcome],
                edgecolor=GROUND,
                linewidth=1,
            )
            if share >= 0.07:
                text_color = GROUND if outcome != "decline" else INK
                axes.text(
                    left + share / 2,
                    row,
                    str(n),
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=8.5,
                )
            left += share
    axes.set_yticks(range(len(split)), [f"{k} ({len(v)})" for k, v in split.items()])
    axes.set_ylim(len(split) - 0.5, -0.5)
    axes.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    axes.set_xlim(0, 1)
    axes.tick_params(axis="y", length=0)
    axes.spines["left"].set_visible(False)
    handles = [Rectangle((0, 0), 1, 1, color=c) for c in OUTCOMES.values()]
    axes.legend(
        handles,
        list(OUTCOMES),
        ncols=4,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0, 1.0),
        fontsize=8.5,
        handlelength=1,
        handleheight=1,
    )
    axes.set_title("What the gate does with the test lines", pad=24)
    return figure
