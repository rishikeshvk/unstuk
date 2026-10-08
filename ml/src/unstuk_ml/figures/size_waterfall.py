"""Where the APK's bytes go: from the float graph, through int8, to the release APK."""

import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from unstuk_ml.figures.style import INK, MUTED, OUTLINE, SHIPS, TINT

MODEL_ENTRY = "assets/model/decision.onnx"
RUNTIME_ENTRY = "lib/arm64-v8a/libonnxruntime.so"
DEX_PREFIX = "classes"
TARGET_MB = 60
BUDGET_MB = 100
MB = 1e6


@dataclass(frozen=True)
class ApkParts:
    model: int
    runtime: int
    dex: int
    total: int

    @property
    def rest(self) -> int:
        """Resources, vocabulary, option vectors, catalog, JNI glue and the zip's own overhead."""
        return self.total - self.model - self.runtime - self.dex


@dataclass(frozen=True)
class Step:
    name: str
    start: float
    end: float
    """In MB; a total starts at 0, a change starts where the last bar ended."""

    @property
    def is_total(self) -> bool:
        return self.start == 0


def apk_parts(apk: Path) -> ApkParts:
    """The release APK's largest parts, as stored in the zip."""
    with zipfile.ZipFile(apk) as archive:
        stored = {i.filename: i.compress_size for i in archive.infolist()}
    dex = sum(size for name, size in stored.items() if name.startswith(DEX_PREFIX))
    return ApkParts(stored[MODEL_ENTRY], stored[RUNTIME_ENTRY], dex, apk.stat().st_size)


def steps(float_graph: int, parts: ApkParts) -> list[Step]:
    model, runtime = parts.model / MB, parts.runtime / MB
    dex, rest = parts.dex / MB, parts.rest / MB
    return [
        Step("Float\ngraph", 0, float_graph / MB),
        Step("int8\nweights", float_graph / MB, model),
        Step("Model,\nint8", 0, model),
        Step("ONNX\nRuntime", model, model + runtime),
        Step("Dex", model + runtime, model + runtime + dex),
        Step("Everything\nelse", model + runtime + dex, model + runtime + dex + rest),
        Step("Release\nAPK", 0, parts.total / MB),
    ]


def draw(chart: Sequence[Step]) -> Figure:
    figure, axes = plt.subplots(figsize=(7.2, 3.6))
    for x, step in enumerate(chart):
        low, high = sorted((step.start, step.end))
        shrinks = step.end < step.start
        color = INK if step.is_total else TINT if shrinks else SHIPS
        axes.bar(x, high - low, bottom=low, width=0.56, color=color, edgecolor="none")
        change = step.end if step.is_total else step.end - step.start
        label = f"{change:.1f}" if step.is_total else f"{change:+.1f}".replace("-", "\u2212")
        axes.annotate(
            label,
            (x, high),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=INK if step.is_total else MUTED,
            fontsize=9,
        )
    for value, name in ((TARGET_MB, "60 MB target"), (BUDGET_MB, "100 MB budget")):
        axes.axhline(value, color=OUTLINE, linewidth=0.8, zorder=0)
        axes.annotate(
            name,
            (len(chart) - 0.55, value),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            annotation_clip=False,
            color=MUTED,
            fontsize=8.5,
        )
    axes.set_xticks(range(len(chart)), [s.name for s in chart], fontsize=8.5)
    axes.tick_params(axis="x", length=0)
    axes.set_ylabel("MB")
    axes.set_ylim(0, max(s.end for s in chart) * 1.12)
    axes.set_title("int8 cut the model by three quarters; the runtime now weighs as much")
    return figure
