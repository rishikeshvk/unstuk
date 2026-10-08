"""The figures' look, from the app's colour tokens (docs/design-spec.md), light theme."""

from pathlib import Path

import matplotlib as mpl
from matplotlib.figure import Figure

GROUND = "#F6F1EA"
INK = "#1F1B2E"
MUTED = "#4A4458"
HAIRLINE = "#E4DCD2"
OUTLINE = "#CFC6BC"
# A step darker than the app's Tangerine, so marks clear 3:1 on Ground.
SHIPS = "#D35A2E"
OTHERS = "#6F6779"
TINT = "#FCE3D3"

FIGURES_DIR = Path(__file__).resolve().parents[4] / "docs" / "figures"


def apply() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "axes.edgecolor": OUTLINE,
            "axes.linewidth": 0.8,
            "axes.facecolor": GROUND,
            "axes.titlesize": 10.5,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "grid.color": HAIRLINE,
            "grid.linewidth": 0.8,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "figure.facecolor": GROUND,
            "savefig.facecolor": GROUND,
            # Text stays text, so the SVGs are small, searchable and diff cleanly.
            "svg.fonttype": "none",
            "svg.hashsalt": "unstuk",
        }
    )


def save(figure: Figure, name: str, figures_dir: Path = FIGURES_DIR) -> Path:
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / name
    # No date in the metadata, so redrawing the same data gives the same bytes.
    figure.savefig(path, format="svg", bbox_inches="tight", metadata={"Date": None})
    return path
