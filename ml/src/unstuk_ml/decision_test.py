"""The decision model on the frozen test (M5 spec section 5): scored once, against the M4 bar.

Every catalog intent is offered, the held-out ones included, as the zero-shot rung offers them; a
held-out intent can only be named zero-shot. The baselines are re-scored from their committed
settings, the same scorings M4 reported.
"""

import argparse
from collections.abc import Iterable, Sequence
from dataclasses import replace

from tokenizers import Tokenizer

from unstuk_ml import rung, zero_shot
from unstuk_ml.backbone import load_backbone
from unstuk_ml.bar import BarRow, check
from unstuk_ml.baseline_report import REPORTS, Below, Decider, load_test, render
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.decision_rung import SETTINGS, Settings
from unstuk_ml.decision_scoring import (
    UNCALIBRATED,
    Gate,
    Temperatures,
    decision_logits,
    node_accuracy,
    scored,
)
from unstuk_ml.decision_training import DecisionRun, noul_input
from unstuk_ml.encoder import download, embed_cached
from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import Scored
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.fixed_head import fixed_head_logits
from unstuk_ml.fixed_head_rung import FIXED_HEAD, load_checkpoint
from unstuk_ml.fixed_head_rung import SETTINGS as FIXED_HEAD_SETTINGS
from unstuk_ml.fixed_head_rung import Settings as FixedHeadSettings
from unstuk_ml.node_labels import read_questions
from unstuk_ml.node_similarity import NODES_DIR, known_labels, similarity_picker, string_picker
from unstuk_ml.record import Record
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.wise_ft import blend
from unstuk_ml.zero_shot import ZERO_SHOT

REPORT = REPORTS / "decision-model.md"
DECISION = Decider(
    title="Fine-tuned bge-small + Choice and Noul heads",
    command="unstuk-decision-test",
    about="BAAI/bge-small-en-v1.5 fine-tuned to choose among option texts, with every catalog "
    "intent offered",
    held_out_note="their options are offered; none was trained",
    report=REPORT,
)
SPEC = "../../docs/m5-spec.md"


def offered(catalog: Catalog) -> list[str]:
    """Every catalog intent, in catalog order: held-out ones are named only zero-shot."""
    return list(catalog.intents)


def guard_note(settings: Settings) -> list[str]:
    lines = ["", "## How this model was chosen", ""]
    if settings.guarded:
        return [*lines, f"On dev, under the zero-shot guard ([M5 spec]({SPEC}), section 3)."]
    return [
        *lines,
        f"**Without the zero-shot guard.** Seven rounds on dev ([M5 spec]({SPEC}), section 3) "
        "found no config that names never-trained intents as well as the frozen zero-shot rung "
        "once out of scope is decided: the Choice head names them about as well, but every "
        "out-of-scope check tried declines a fifth or more of their lines. By the pre-registered "
        "stop rule the guard was dropped and the rung rule alone picked this model, the most "
        "accurate on dev and the least able to name unseen intents on the folds. The held-out bar "
        "below is expected to fail for that reason.",
    ]


def bar_section(rows: Sequence[BarRow]) -> list[str]:
    lines = [
        "",
        "## Against the M4 bar",
        "",
        "From `m4-results.md`: better than the best baseline on accuracy and macro-F1, not worse "
        "on each guard rail. Differences are this model minus the baseline, paired 95% intervals.",
        "",
        "| Metric | Bar | Set by | Must | This model | Difference | Passes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        low, high = row.interval
        lines.append(
            f"| {row.requirement.name} | {row.bar:.1%} | {row.requirement.rung} | "
            f"{row.requirement.must} | {row.value:.1%} | {low:+.1%} to {high:+.1%} | "
            f"{'yes' if row.passes else '**no**'} |"
        )
    cleared = all(row.passes for row in rows)
    lines += ["", f"**Clears the bar: {'yes' if cleared else 'no'}.**"]
    return lines


def node_section(model: DecisionModel, tokenizer: Tokenizer) -> list[str]:
    dev = read_questions(NODES_DIR / "dev.jsonl")
    test = read_questions(NODES_DIR / "test.jsonl")
    pickers = {
        "String baseline": string_picker(known_labels()),
        "Similarity (frozen)": similarity_picker(embed_cached, [*dev, *test]),
    }
    lines = [
        "",
        "## Node labels",
        "",
        "Which item on the screen is the switch: dev is Xiaomi wording, the test is the Moto's "
        "screens. The decision model answers with its Choice head; the others are M4's.",
        "",
        f"| Method | Dev ({len(dev)}) | Moto test ({len(test)}) |",
        "| --- | --- | --- |",
    ]
    for name, pick in pickers.items():
        lines.append(
            f"| {name} | {_share(pick(q) == q.answer for q in dev):.1%} | "
            f"{sum(pick(q) == q.answer for q in test)}/{len(test)} |"
        )
    model_test = round(node_accuracy(model, test, tokenizer) * len(test))
    lines.append(
        f"| Decision model | {node_accuracy(model, dev, tokenizer):.1%} | "
        f"{model_test}/{len(test)} |"
    )
    return lines


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    model = _model(settings)
    lines = load_test()
    intents = offered(catalog)
    logits = decision_logits(model, lines, intents, catalog, tokenizer)
    if settings.out_of_scope == "gate":
        logits = Gate(_given(settings.gate_weight), _given(settings.gate_bias)).apply(logits)
    temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature or 1.0)
    items = scored(logits, lines, intents, temperatures)
    about = (
        f"{DECISION.about}; run `{settings.run}`, epoch {settings.epoch}, checkpoint sha256 "
        f"`{settings.checkpoint_sha256[:12]}…` from commit `{settings.commit[:7]}`, out of scope "
        f"by {settings.out_of_scope}, temperatures {settings.choice_temperature} (Choice) and "
        f"{settings.noul_temperature} (Noul) fitted on dev"
    )
    text = render(
        replace(DECISION, about=about),
        items,
        before_temperature=scored(logits, lines, intents, UNCALIBRATED),
        below=Below(FIXED_HEAD, _fixed_head(lines)),
    )
    sections = guard_note(settings) + bar_section(check(items, _baselines(lines)))
    sections += node_section(model, tokenizer)
    REPORT.write_text(text + "\n".join(sections) + "\n", encoding="utf-8")
    print(f"scored {len(items)} test lines; see {REPORT}")


def _model(settings: Settings) -> DecisionModel:
    """The settings' checkpoint, refused unless its bytes match, blended if the settings say so."""
    result = DecisionRun.model_validate_json(
        (RUNS_DIR / settings.run / RESULT).read_text(encoding="utf-8")
    )
    model = DecisionModel(load_backbone(), result.config.head, noul_input(result.config))
    model.load_state_dict(load_weights(RUNS_DIR / settings.run, settings.checkpoint_sha256))
    if settings.blend is not None:
        blend(model.backbone, load_backbone().state_dict(), settings.blend)
    return model


def _baselines(lines: Sequence[Record]) -> dict[str, list[Scored]]:
    tfidf_settings, tfidf = rung.load(TFIDF)
    encoder_settings, encoder = rung.load(ENCODER)
    zero = zero_shot.Settings.model_validate_json(zero_shot.SETTINGS.read_text("utf-8"))
    labels, texts = zero_shot.options(zero.out_of_scope_option)
    cosines = zero_shot.cosines(embed_cached, lines, texts, zero.instruction)
    return {
        TFIDF.decider.title: rung.score(tfidf, tfidf_settings.temperature, lines),
        ENCODER.decider.title: rung.score(encoder, encoder_settings.temperature, lines),
        ZERO_SHOT.title: zero_shot.score(cosines, labels, lines, zero.temperature),
    }


def _fixed_head(lines: Sequence[Record]) -> list[Scored]:
    settings = FixedHeadSettings.model_validate_json(FIXED_HEAD_SETTINGS.read_text("utf-8"))
    model = load_checkpoint(RUNS_DIR / settings.run, settings.checkpoint_sha256)
    logits = fixed_head_logits(model, lines, decision_tokenizer(download()[1]))
    return zero_shot.score(logits, model.labels, lines, settings.temperature)


def _given(value: float | None) -> float:
    if value is None:
        raise ValueError("a gated model's settings must give the gate's weight and bias")
    return value


def _share(flags: Iterable[bool]) -> float:
    values = list(flags)
    return sum(values) / len(values)
