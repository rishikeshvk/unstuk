"""Every decider on the bar's metrics, with 95% bootstrap intervals."""

from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter

from unstuk_ml.bar import BAR
from unstuk_ml.evaluate import Scored, bootstrap
from unstuk_ml.figures.style import GROUND, HAIRLINE, MUTED, OTHERS, OUTLINE, SHIPS


def draw(
    deciders: Mapping[str, Sequence[Scored]], bar_setters: Mapping[str, str], ships: str
) -> Figure:
    """One panel per bar row; `bar_setters` maps a baseline's report title to its row title here."""
    names = list(deciders)
    figure, grid = plt.subplots(2, 3, figsize=(9.6, 5.4), sharey=True)
    for axes, requirement in zip(grid.flat, BAR, strict=True):
        for row, name in enumerate(names):
            items = deciders[name]
            value = requirement.metric(items)
            low, high = bootstrap(items, requirement.metric)
            color = SHIPS if name == ships else OTHERS
            axes.plot([low, high], [row, row], color=color, linewidth=2, solid_capstyle="round")
            axes.plot(
                value,
                row,
                "o",
                color=color,
                markersize=7,
                markeredgecolor=GROUND,
                markeredgewidth=1.5,
            )
        bar = requirement.metric(deciders[bar_setters[requirement.rung]])
        axes.axvline(bar, color=OUTLINE, linewidth=0.8, zorder=0)
        better = "higher" if requirement.higher_is_better else "lower"
        axes.set_title(f"{requirement.name}\n{better} is better", fontsize=9.5)
        axes.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=None))
        axes.grid(True, axis="x", color=HAIRLINE)
        axes.tick_params(axis="y", length=0)
        axes.annotate(
            "bar",
            (bar, -0.5),
            xytext=(3, 0),
            textcoords="offset points",
            color=MUTED,
            fontsize=8,
            va="center",
        )
    grid[0][0].set_yticks(range(len(names)), names)
    grid[0][0].set_ylim(len(names) - 0.4, -0.6)
    figure.suptitle(
        "The int8 graph clears every bar but held-out intents",
        x=0.02,
        ha="left",
        fontweight="semibold",
        fontsize=10.5,
    )
    figure.tight_layout()
    return figure
