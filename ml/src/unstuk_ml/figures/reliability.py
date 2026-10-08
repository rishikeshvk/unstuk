"""Reliability diagrams: how often each decider is right at each level of confidence."""

from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from unstuk_ml.evaluate import Scored, calibration_bins, expected_calibration_error
from unstuk_ml.figures.style import GROUND, HAIRLINE, MUTED, OTHERS, OUTLINE, SHIPS


@dataclass(frozen=True)
class Panel:
    title: str
    items: Sequence[Scored]
    ships: bool


def draw(panels: Sequence[Panel]) -> Figure:
    figure, grid = plt.subplots(
        2,
        len(panels),
        figsize=(3 * len(panels), 4.1),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.12, "wspace": 0.18},
    )
    tallest = max(b.count for p in panels for b in calibration_bins(p.items))
    for column, panel in enumerate(panels):
        color = SHIPS if panel.ships else OTHERS
        top, bottom = grid[0][column], grid[1][column]
        found = calibration_bins(panel.items)
        top.plot([0, 1], [0, 1], color=OUTLINE, linewidth=0.8, zorder=0)
        # Area follows the line count, so a bin of one line doesn't read like a bin of 400.
        top.scatter(
            [b.confidence for b in found],
            [b.accuracy for b in found],
            s=[12 + 160 * (b.count / tallest) ** 0.5 for b in found],
            color=color,
            edgecolors=GROUND,
            linewidths=1.5,
            zorder=3,
        )
        ece = expected_calibration_error(panel.items)
        top.set_title(f"{panel.title}\nECE {ece:.1%}", fontsize=9.5)
        top.set(xlim=(0, 1.04), ylim=(-0.04, 1.06))
        top.grid(True, color=HAIRLINE)
        bottom.bar(
            [b.low + 0.05 for b in found],
            [b.count for b in found],
            width=0.08,
            color=color,
        )
        bottom.set_ylim(0, tallest * 1.1)
        bottom.set_xlabel("Confidence in the top answer")
        if column == 0:
            top.set_ylabel("Share right")
            bottom.set_ylabel("Lines", color=MUTED)
        else:
            top.tick_params(labelleft=False)
            bottom.tick_params(labelleft=False)
    figure.suptitle(
        "On the diagonal, confidence means what it says; dot area is the number of lines",
        x=0.08,
        ha="left",
        fontweight="semibold",
        fontsize=10.5,
        y=1.04,
    )
    return figure
