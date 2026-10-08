"""The int8 graph on the frozen test (M7 spec section 4): scored once, against M6's float model.

Both run through ONNX Runtime, as the app will, with every catalog intent offered. M6's float
model keeps its own temperatures and lines; the int8 graph has its refitted temperatures and the
lines re-tuned on it, which `catalog/gate.json` now holds.
"""

import argparse
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from unstuk_ml.bar import BarRow, Requirement
from unstuk_ml.baseline_report import REPORTS, Decider, load_test, render
from unstuk_ml.calibrated_rung import SETTINGS as M6_SETTINGS
from unstuk_ml.calibrated_rung import Settings as M6Settings
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import FLOAT_GRAPH
from unstuk_ml.decision_scoring import UNCALIBRATED, Temperatures, scored
from unstuk_ml.decision_test import offered
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import (
    GateLines,
    Scored,
    confident_and_wrong,
    expected_calibration_error,
    held_out_accuracy,
    in_scope_accuracy,
    load_gate,
    macro_f1,
    out_of_scope_recall,
    paired_bootstrap,
    vague_handled,
)
from unstuk_ml.fine_tuning import RUNS_DIR, sha256
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.quantized_rung import SETTINGS, Settings

REPORT = REPORTS / "quantized.md"
QUANTIZED = Decider(
    title="int8 decision graph",
    command="unstuk-quantized-test",
    about="M6's calibrated model as the int8 ONNX graph the app runs, behind gate lines "
    "re-tuned on it",
    held_out_note="their options are offered; none was trained",
    report=REPORT,
)
FLOAT = "M6 float model"
# Pre-registered in the M7 spec, section 4.
AGAINST_FLOAT = (
    Requirement("Top-1 accuracy, in scope", in_scope_accuracy, FLOAT, "not worse", True),
    Requirement("Confident and wrong", confident_and_wrong, FLOAT, "not worse", False),
    Requirement(
        "Expected calibration error", expected_calibration_error, FLOAT, "not worse", False
    ),
    Requirement("Out-of-scope recall", out_of_scope_recall, FLOAT, "not worse", True),
)
REPORTED = (
    ("Vague lines asked about or declined", vague_handled),
    ("Macro-F1", macro_f1),
    ("Held-out intents", held_out_accuracy),
)


def against_float(items: Sequence[Scored], base: Sequence[Scored]) -> list[BarRow]:
    return [
        BarRow(r, r.metric(base), r.metric(items), paired_bootstrap(base, items, r.metric))
        for r in AGAINST_FLOAT
    ]


def float_section(
    rows: Sequence[BarRow], items: Sequence[Scored], base: Sequence[Scored]
) -> list[str]:
    lines = [
        "",
        "## Against M6's float model",
        "",
        "Pre-registered in the M7 spec, section 4. Each model is under its own temperatures and "
        "lines; differences are int8 minus float, with paired 95% intervals.",
        "",
        "| Metric | Float | int8 | Difference | Must | Passes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        low, high = row.interval
        lines.append(
            f"| {row.requirement.name} | {row.bar:.1%} | {row.value:.1%} | "
            f"{low:+.1%} to {high:+.1%} | {row.requirement.must} | "
            f"{'yes' if row.passes else '**no**'} |"
        )
    for name, metric in REPORTED:
        low, high = paired_bootstrap(base, items, metric)
        lines.append(
            f"| {name} | {metric(base):.1%} | {metric(items):.1%} | {low:+.1%} to {high:+.1%} | "
            "reported | |"
        )
    same = all(row.passes for row in rows)
    return [*lines, "", f"**Not worse than float by the spec's rule: {'yes' if same else 'no'}.**"]


def sizes_section(settings: Settings, float_graph: Path) -> list[str]:
    rows = [f"| `{FLOAT_GRAPH}` | none | {float_graph.stat().st_size / 1e6:.1f} MB | M6's model |"]
    rows += [
        f"| `{t.graph}` | {', '.join(t.ops)} | {t.megabytes:.1f} MB | "
        f"{'passed the dev check' if t.passes else 'failed the dev check'}"
        f"{', **ships**' if t.graph == settings.graph else ''} |"
        for t in settings.tries
    ]
    return [
        "",
        "## Graph sizes",
        "",
        "| Graph | int8 ops | Size | Note |",
        "| --- | --- | --- | --- |",
        *rows,
    ]


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    m6 = M6Settings.model_validate_json(M6_SETTINGS.read_text(encoding="utf-8"))
    gate = load_gate()
    if GateLines(**settings.lines) != gate:
        raise ValueError("catalog/gate.json differs from the chosen settings; run the chooser")
    directory = RUNS_DIR / settings.run
    float_graph, graph = directory / FLOAT_GRAPH, directory / settings.graph
    if (sha256(float_graph), sha256(graph)) != (settings.float_sha256, settings.graph_sha256):
        raise ValueError("a graph differs from the one the settings name; run the export again")
    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    lines = load_test()
    intents = offered(catalog)

    logits = GraphDecider(graph, tokenizer, settings.scale).logits(lines, intents, catalog)
    temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature)
    items = [replace(s, gate=gate) for s in scored(logits, lines, intents, temperatures)]
    raw = [replace(s, gate=gate) for s in scored(logits, lines, intents, UNCALIBRATED)]

    float_logits = GraphDecider(float_graph, tokenizer, settings.scale).logits(
        lines, intents, catalog
    )
    float_temperatures = Temperatures(m6.choice_temperature, m6.noul_temperature or 1.0)
    base = [
        replace(s, gate=GateLines(**m6.lines))
        for s in scored(float_logits, lines, intents, float_temperatures)
    ]

    about = (
        f"{QUANTIZED.about}; `{settings.graph}` (sha256 `{settings.graph_sha256[:12]}…`) from "
        f"run `{settings.run}`, commit `{settings.commit[:7]}`, gate lines {settings.lines}"
    )
    text = render(replace(QUANTIZED, about=about), items, before_temperature=raw)
    sections = float_section(against_float(items, base), items, base)
    sections += sizes_section(settings, float_graph)
    REPORT.write_text(text + "\n".join(sections) + "\n", encoding="utf-8")
    print(f"scored {len(items)} test lines; see {REPORT}")
