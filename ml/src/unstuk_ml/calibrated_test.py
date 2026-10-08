"""The calibrated model on the frozen test (M6 spec section 6): scored once, against M5's model.

Every catalog intent is offered, as in M5. The M5 model is re-scored from its committed settings,
under M2's placeholder lines as it was reported; the pre-registered comparison is against that.
It is also shown under M6's tuned lines, to separate what the model changed from what the lines did.
"""

import argparse
from collections.abc import Sequence
from dataclasses import replace

from unstuk_ml.backbone import load_backbone
from unstuk_ml.bar import BarRow, Requirement, check
from unstuk_ml.baseline_report import REPORTS, Below, Decider, load_test, render
from unstuk_ml.calibrated_rung import SETTINGS, Settings
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.decision_rung import SETTINGS as M5_SETTINGS
from unstuk_ml.decision_rung import Settings as M5Settings
from unstuk_ml.decision_scoring import UNCALIBRATED, Temperatures, decision_logits, scored
from unstuk_ml.decision_test import DECISION, bar_section, baselines, load_model, offered
from unstuk_ml.decision_training import DecisionRun, noul_input
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import (
    BINS,
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
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.oof_gate import TwoFeatureGate

REPORT = REPORTS / "calibrated.md"
CALIBRATED = Decider(
    title="Calibrated decision model",
    command="unstuk-calibrated-test",
    about="M5's decision model trained on the vague slice too, with a Brier term, behind gate "
    "lines tuned on dev",
    held_out_note="their options are offered; none was trained",
    report=REPORT,
)
M5 = "M5 decision model"
# Pre-registered in the M6 spec, section 6: must be better, must not be worse, or only reported.
AGAINST_M5 = (
    Requirement(
        "Vague lines answered with a question or decline", vague_handled, M5, "better", True
    ),
    Requirement("Confident and wrong", confident_and_wrong, M5, "not worse", False),
    Requirement("Expected calibration error", expected_calibration_error, M5, "not worse", False),
    Requirement("Out-of-scope recall", out_of_scope_recall, M5, "not worse", True),
)
REPORTED = (
    ("Top-1 accuracy, in scope", in_scope_accuracy),
    ("Macro-F1", macro_f1),
    ("Held-out intents", held_out_accuracy),
)


def against_m5(items: Sequence[Scored], m5: Sequence[Scored]) -> list[BarRow]:
    return [
        BarRow(r, r.metric(m5), r.metric(items), paired_bootstrap(m5, items, r.metric))
        for r in AGAINST_M5
    ]


def m5_section(rows: Sequence[BarRow], items: Sequence[Scored], m5: Sequence[Scored]) -> list[str]:
    lines = [
        "",
        "## Against the M5 decision model",
        "",
        "Pre-registered in the M6 spec, section 6. M5 is scored under M2's placeholder lines, as "
        "it was reported; differences are this model minus M5, with paired 95% intervals.",
        "",
        "| Metric | M5 | This model | Difference | Must | Passes |",
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
        low, high = paired_bootstrap(m5, items, metric)
        lines.append(
            f"| {name} | {metric(m5):.1%} | {metric(items):.1%} | {low:+.1%} to {high:+.1%} | "
            "reported | |"
        )
    safer = all(row.passes for row in rows)
    return [*lines, "", f"**Safer than M5 by the spec's rule: {'yes' if safer else 'no'}.**"]


def lines_section(m5: Sequence[Scored], gate: GateLines) -> list[str]:
    """M5's model under M6's lines: what the lines alone would have done."""
    retuned = [replace(s, gate=gate) for s in m5]
    return [
        "",
        "## M5's model under the tuned lines",
        "",
        f"Lines: automatic at {gate.automatic_at}, clarify below {gate.clarify_below}, clarify "
        f"margin {gate.clarify_margin}.",
        "",
        "| Metric | M5, placeholder lines | M5, tuned lines |",
        "| --- | --- | --- |",
        *(
            f"| {r.name} | {r.metric(m5):.1%} | {r.metric(retuned):.1%} |"
            for r in AGAINST_M5
            if r.metric is not out_of_scope_recall
        ),
    ]


def reliability_section(items: Sequence[Scored], m5: Sequence[Scored]) -> list[str]:
    lines = [
        "",
        "## Reliability",
        "",
        "Clear lines by the top answer's probability: how many, and how often right.",
        "",
        "| Confidence | M5 lines | M5 right | This model's lines | This model right |",
        "| --- | --- | --- | --- | --- |",
    ]
    for b in range(BINS):
        low, high = b / BINS, (b + 1) / BINS
        cells = []
        for group in (m5, items):
            in_bin = [s for s in group if not s.vague and low < s.top[1] <= high]
            right = sum(s.correct for s in in_bin) / len(in_bin) if in_bin else None
            cells += [str(len(in_bin)), "-" if right is None else f"{right:.0%}"]
        lines.append(f"| {low:.1f} to {high:.1f} | {' | '.join(cells)} |")
    return lines


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    gate = load_gate()
    if GateLines(**settings.lines) != gate:
        raise ValueError("catalog/gate.json differs from the chosen settings; run the chooser")
    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    lines = load_test()
    intents = offered(catalog)

    model = calibrated_model(settings)
    logits = decision_logits(model, lines, intents, catalog, tokenizer)
    if settings.gate is not None:
        logits = TwoFeatureGate(**settings.gate).apply(logits)
    temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature or 1.0)
    items = [replace(s, gate=gate) for s in scored(logits, lines, intents, temperatures)]
    raw = [replace(s, gate=gate) for s in scored(logits, lines, intents, UNCALIBRATED)]

    m5_settings = M5Settings.model_validate_json(M5_SETTINGS.read_text(encoding="utf-8"))
    m5_logits = decision_logits(load_model(m5_settings), lines, intents, catalog, tokenizer)
    m5_temperatures = Temperatures(
        m5_settings.choice_temperature, m5_settings.noul_temperature or 1.0
    )
    m5 = scored(m5_logits, lines, intents, m5_temperatures)

    about = (
        f"{CALIBRATED.about}; run `{settings.run}`, epoch {settings.epoch}, checkpoint sha256 "
        f"`{settings.checkpoint_sha256[:12]}…` from commit `{settings.commit[:7]}`, out of scope "
        f"by {settings.out_of_scope}, gate lines {settings.lines}"
    )
    text = render(
        replace(CALIBRATED, about=about),
        items,
        before_temperature=raw,
        below=Below(DECISION, m5),
    )
    sections = m5_section(against_m5(items, m5), items, m5)
    sections += lines_section(m5, gate) + reliability_section(items, m5)
    sections += bar_section(check(items, baselines(lines)))
    REPORT.write_text(text + "\n".join(sections) + "\n", encoding="utf-8")
    print(f"scored {len(items)} test lines; see {REPORT}")


def calibrated_model(settings: Settings) -> DecisionModel:
    """The settings' checkpoint, refused unless its bytes match."""
    result = DecisionRun.model_validate_json(
        (RUNS_DIR / settings.run / RESULT).read_text(encoding="utf-8")
    )
    model = DecisionModel(load_backbone(), result.config.head, noul_input(result.config))
    model.load_state_dict(load_weights(RUNS_DIR / settings.run, settings.checkpoint_sha256))
    return model
