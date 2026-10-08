"""The shipped int8 graph on real messages (m8-spec section 5): scored once, against the M4 bar.

Intervals resample lines within each participant. The model ships if it passes every bar row but
held-out intents, on all lines and with any one participant left out. The report holds aggregates
only, never a message's text, so it can be committed.
"""

import argparse
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from unstuk_ml.bar import BarRow, check
from unstuk_ml.baseline_report import REPORTS
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_scoring import Temperatures, scored
from unstuk_ml.decision_test import baselines, offered
from unstuk_ml.evaluate import (
    Metric,
    Scored,
    accuracy,
    bootstrap,
    confusions,
    expected_calibration_error,
    held_out_accuracy,
    in_scope_accuracy,
    out_of_scope_recall,
)
from unstuk_ml.field_cards import FREE, load_cards
from unstuk_ml.freeze import LOCK, frozen_changes
from unstuk_ml.labels import OUT_OF_SCOPE, VAGUE
from unstuk_ml.quantized_test import load_shipped
from unstuk_ml.real_labels import LABELS_FILE, read_labels
from unstuk_ml.real_messages import MESSAGES_FILE, REAL_DIR, read_messages
from unstuk_ml.record import Record

REPORT = REPORTS / "real.md"
MIN_CLEAR_LINES = 150
MIN_PARTICIPANTS = 4
# plan.md's MVP targets: (name, metric, target, higher is better).
TARGETS: tuple[tuple[str, Metric, float, bool], ...] = (
    ("Top-1 accuracy, in scope", in_scope_accuracy, 0.85, True),
    ("Out-of-scope recall", out_of_scope_recall, 0.90, True),
    ("Expected calibration error", expected_calibration_error, 0.05, False),
    ("Held-out intents", held_out_accuracy, 0.70, True),
)


@dataclass(frozen=True)
class RealSet:
    records: list[Record]
    """Kept lines: `generator` is the participant, `batch` the medium."""
    cards: dict[str, str]
    """Line id to its card's `about`."""
    dropped: int
    hashes: dict[str, str]


def load_real(real_dir: Path = REAL_DIR) -> RealSet:
    """Messages joined with their labels; refuses unless both still match the lock."""
    lock = real_dir / LOCK
    if not lock.exists():
        raise FileNotFoundError(f"{lock} is missing; freeze the labels before scoring")
    changes = frozen_changes(real_dir)
    if changes:
        raise ValueError("data/real differs from its lock: " + "; ".join(changes))
    messages = read_messages(real_dir / MESSAGES_FILE.name)
    labels = {label.id: label for label in read_labels(real_dir / LABELS_FILE.name)}
    unlabelled = [m.id for m in messages if m.id not in labels]
    if unlabelled or len(labels) != len(messages):
        raise ValueError(f"every message needs exactly one label; {len(unlabelled)} have none")
    about = {card.id: card.about for card in load_cards()}
    kept = [m for m in messages if not labels[m.id].dropped]
    records = [
        Record(
            id=m.id,
            text=m.text,
            labels=labels[m.id].labels,
            tags=labels[m.id].tags,
            source="real",
            generator=m.participant,
            batch=m.medium,
        )
        for m in kept
    ]
    return RealSet(
        records=records,
        cards={m.id: about[m.card] for m in kept},
        dropped=len(messages) - len(kept),
        hashes=json.loads(lock.read_text(encoding="utf-8")),
    )


def enough(records: Sequence[Record]) -> bool:
    clear = [r for r in records if VAGUE not in r.tags]
    return len(clear) >= MIN_CLEAR_LINES and len(participants(records)) >= MIN_PARTICIPANTS


def participants(records: Sequence[Record]) -> list[str]:
    return sorted({r.generator for r in records})


def bar_rows(items: Sequence[Scored], base: Mapping[str, Sequence[Scored]]) -> list[BarRow]:
    return check(items, base, strata=[s.record.generator for s in items])


def gated(rows: Sequence[BarRow]) -> list[BarRow]:
    """The rows the ship rule reads: held-out intents are reported, not gated."""
    return [row for row in rows if row.requirement.metric is not held_out_accuracy]


def leave_one_out(
    items: Sequence[Scored], base: Mapping[str, Sequence[Scored]]
) -> dict[str, list[BarRow]]:
    """Per participant left out, the gated rows that fail without them."""
    failing = {}
    for person in participants([s.record for s in items]):
        keep = [i for i, s in enumerate(items) if s.record.generator != person]
        rows = bar_rows(
            [items[i] for i in keep], {k: [v[i] for i in keep] for k, v in base.items()}
        )
        failing[person] = [row for row in gated(rows) if not row.passes]
    return failing


def ships(rows: Sequence[BarRow], without: Mapping[str, Sequence[BarRow]]) -> bool:
    return all(row.passes for row in gated(rows)) and not any(without.values())


def card_match(items: Sequence[Scored], cards: Mapping[str, str]) -> tuple[int, int]:
    """Card lines whose label is what the card's story was written for: (matching, total)."""
    on_cards = [s for s in items if cards[s.record.id] != FREE]
    matching = sum(
        VAGUE in s.record.tags
        if cards[s.record.id] == VAGUE
        else cards[s.record.id] in s.record.labels
        for s in on_cards
    )
    return matching, len(on_cards)


def render_report(
    real: RealSet,
    items: Sequence[Scored],
    base: Mapping[str, Sequence[Scored]],
    about: str,
) -> str:
    rows = bar_rows(items, base)
    without = leave_one_out(items, base)
    lines = [
        "# The int8 decision graph on real messages",
        "",
        "Written by `uv run unstuk-real-test`; do not edit by hand. Aggregates only: no message "
        f"is quoted. {about}.",
        "",
        *_counts(real),
        *_bar(rows, without),
        *_targets(items),
        *_outcomes(items),
        *_groups(items, real.cards),
        *_mistakes(items),
    ]
    return "\n".join(lines) + "\n"


def _counts(real: RealSet) -> list[str]:
    records = real.records
    vague = sum(VAGUE in r.tags for r in records)
    oos = sum(r.labels == [OUT_OF_SCOPE] and VAGUE not in r.tags for r in records)
    by_medium = Counter(r.batch for r in records)
    hashes = ", ".join(f"`{name}` `{digest[:12]}…`" for name, digest in sorted(real.hashes.items()))
    return [
        "## The set",
        "",
        f"{len(records)} lines from {len(participants(records))} participants "
        f"({', '.join(f'{n} {m}' for m, n in sorted(by_medium.items()))}): "
        f"{len(records) - vague - oos} in scope, {oos} out of scope, {vague} vague; "
        f"{real.dropped} dropped as not English. Frozen: {hashes}.",
    ]


def _bar(rows: Sequence[BarRow], without: Mapping[str, Sequence[BarRow]]) -> list[str]:
    lines = [
        "",
        "## Against the M4 bar",
        "",
        "Differences are this model minus the baseline, with paired 95% intervals resampled within "
        "each participant. Held-out intents are reported, not gated (m8-spec section 5).",
        "",
        "| Metric | Bar | Set by | Must | This model | Difference | Passes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        low, high = row.interval
        verdict = "yes" if row.passes else "**no**"
        if row not in gated(rows):
            verdict += " (reported)"
        lines.append(
            f"| {row.requirement.name} | {row.bar:.1%} | {row.requirement.rung} | "
            f"{row.requirement.must} | {row.value:.1%} | {low:+.1%} to {high:+.1%} | {verdict} |"
        )
    lines += ["", "| Left out | Gated rows that fail |", "| --- | --- |"]
    for person, failing in without.items():
        names = ", ".join(row.requirement.name for row in failing) or "none"
        lines.append(f"| {person} | {names} |")
    verdict = "yes" if ships(rows, without) else "no"
    return [*lines, "", f"**Ships: {verdict}.**"]


def _targets(items: Sequence[Scored]) -> list[str]:
    strata = [s.record.generator for s in items]
    lines = ["", "## Against plan.md's MVP targets", ""]
    lines += ["| Metric | Target | Value | 95% interval |", "| --- | --- | --- | --- |"]
    for name, metric, target, higher in TARGETS:
        low, high = bootstrap(items, metric, strata=strata)
        sign = "≥" if higher else "≤"
        value = _pct(metric(items))
        lines.append(f"| {name} | {sign} {target:.0%} | {value} | {_pct(low)} to {_pct(high)} |")
    return lines


def _outcomes(items: Sequence[Scored]) -> list[str]:
    clear = [s for s in items if not s.vague]
    groups = [
        ("in scope", [s for s in clear if s.record.labels != [OUT_OF_SCOPE]]),
        ("out of scope", [s for s in clear if s.record.labels == [OUT_OF_SCOPE]]),
        ("vague", [s for s in items if s.vague]),
    ]
    lines = ["", "## What the gate would do", ""]
    lines += [
        "| Lines | Automatic | Confirm | Clarify | Decline |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, group in groups:
        counts = Counter(s.outcome for s in group)
        cells = " | ".join(str(counts[o]) for o in ("automatic", "confirm", "clarify", "decline"))
        lines.append(f"| {name} ({len(group)}) | {cells} |")
    return lines


def _groups(items: Sequence[Scored], cards: Mapping[str, str]) -> list[str]:
    def kind(s: Scored) -> str:
        return "free lines" if cards[s.record.id] == FREE else "card lines"

    groups: dict[str, list[Scored]] = {}
    for s in items:
        if not s.vague:
            for name in (s.record.generator, f"medium: {s.record.batch}", kind(s)):
                groups.setdefault(name, []).append(s)
    lines = ["", "## By participant, medium and source", ""]
    lines += ["| Group | Clear lines | Accuracy | 95% interval |", "| --- | --- | --- | --- |"]
    for name, group in sorted(groups.items()):
        low, high = bootstrap(group, accuracy)
        lines.append(
            f"| {name} | {len(group)} | {_pct(accuracy(group))} | {_pct(low)} to {_pct(high)} |"
        )
    matching, total = card_match(items, cards)
    return [*lines, "", f"Card lines labelled as their story was written: {matching} of {total}."]


def _mistakes(items: Sequence[Scored]) -> list[str]:
    lines = [
        "",
        "## Most common mistakes",
        "",
        "Label pairs only; the lines stay in `data/real/`.",
        "",
    ]
    lines += [f"- {given} → {said}: {len(wrong)}" for given, said, wrong in confusions(items)]
    return lines


def _pct(value: float) -> str:
    return "n/a" if value != value else f"{value:.1%}"


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    real = load_real()
    if not enough(real.records):
        raise SystemExit(
            f"need {MIN_CLEAR_LINES} clear lines from {MIN_PARTICIPANTS} participants; "
            "run more sittings before scoring"
        )
    settings, gate, decider = load_shipped()
    catalog = load_catalog()
    intents = offered(catalog)
    logits = decider.logits(real.records, intents, catalog)
    temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature)
    items = [replace(s, gate=gate) for s in scored(logits, real.records, intents, temperatures)]
    about = (
        f"`{settings.graph}` (sha256 `{settings.graph_sha256[:12]}…`) from run `{settings.run}`, "
        f"every catalog intent offered, gate lines {settings.lines}"
    )
    REPORT.write_text(render_report(real, items, baselines(real.records), about), encoding="utf-8")
    print(f"scored {len(items)} real lines; see {REPORT}")
