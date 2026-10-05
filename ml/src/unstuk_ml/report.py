"""The cleaning report: one page with the state of the data and every reason a line was dropped."""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from unstuk_ml.duplicates import Drop
from unstuk_ml.label_issues import Flag
from unstuk_ml.record import Record
from unstuk_ml.shortcuts import Giveaway, LabelProfile


@dataclass(frozen=True)
class Leakage:
    counts: dict[float, int]
    """Training lines at or above each similarity threshold to some test line."""
    examples: list[tuple[str, str, float]]


@dataclass(frozen=True)
class Cleaning:
    stages: list[tuple[str, int]]
    dropped: list[Drop]
    leakage: Leakage
    flags: list[Flag]
    profiles: list[LabelProfile]
    giveaways: list[Giveaway]
    train: list[Record]
    dev: list[Record]


def render(c: Cleaning) -> str:
    lines = ["# Cleaning report", "", "Written by `uv run unstuk-clean`; do not edit by hand.", ""]
    lines += ["## Stages", "", "| Stage | Lines left |", "| --- | --- |"]
    lines += [f"| {name} | {n} |" for name, n in c.stages]
    lines += ["", "## Dropped, by reason", "", "| Reason | Lines |", "| --- | --- |"]
    reasons = Counter(_reason_kind(d.reason) for d in c.dropped)
    lines += [f"| {reason} | {n} |" for reason, n in reasons.most_common()]
    lines += ["", "## Closeness to the test set", ""]
    lines += [
        "Training lines at or above each character-n-gram cosine similarity to some test line:",
        "",
    ]
    lines += ["| Threshold | Lines |", "| --- | --- |"]
    lines += [f"| {t} | {n} |" for t, n in sorted(c.leakage.counts.items())]
    lines += ["", "Closest pairs (training line, test line, similarity):", ""]
    lines += [f"- `{a}` / `{b}` ({s:.2f})" for a, b, s in c.leakage.examples]
    lines += [
        "",
        "## Flagged labels",
        "",
        f"{len(c.flags)} lines go to `data/clean/review.jsonl`.",
        "",
    ]
    lines += ["| Given | Model says | Lines |", "| --- | --- | --- |"]
    pairs = Counter((f.record.labels[0], f.predicted) for f in c.flags)
    lines += [f"| {g} | {p} | {n} |" for (g, p), n in pairs.most_common()]
    lines += [
        "",
        "## Shortcut check",
        "",
        "| Label | Lines | Mean words | Most common first words |",
    ]
    lines += ["| --- | --- | --- | --- |"]
    for p in c.profiles:
        firsts = ", ".join(f"{w} {s:.0%}" for w, s in p.top_first_words)
        lines.append(f"| {p.label} | {p.count} | {p.mean_words:.1f} | {firsts} |")
    lines += ["", "Tokens in 15+ lines with 90%+ of them under one label:", ""]
    lines += ["| Label | Tokens |", "| --- | --- |"]
    by_label: dict[str, list[str]] = {}
    for g in c.giveaways:
        by_label.setdefault(g.label, []).append(f"{g.token} ({g.count})")
    lines += [f"| {label} | {', '.join(tokens)} |" for label, tokens in by_label.items()]
    lines += ["", "## Splits", "", "| Label | Train | Dev |", "| --- | --- | --- |"]
    train, dev = _label_counts(c.train), _label_counts(c.dev)
    lines += [f"| {label} | {train[label]} | {dev[label]} |" for label in sorted(train | dev)]
    lines += [f"| **total** | {len(c.train)} | {len(c.dev)} |", ""]
    lines += ["| Source | Train | Dev |", "| --- | --- | --- |"]
    train_s, dev_s = Counter(r.source for r in c.train), Counter(r.source for r in c.dev)
    lines += [f"| {s} | {train_s[s]} | {dev_s[s]} |" for s in sorted(train_s | dev_s)]
    return "\n".join(lines) + "\n"


def _reason_kind(reason: str) -> str:
    if reason.startswith("close to test"):
        return "close to the test set"
    return reason.split(" of ")[0].split(":")[0]


def _label_counts(records: Sequence[Record]) -> Counter[str]:
    return Counter(r.labels[0] for r in records)
