"""A decider's report on the frozen proxy test set: the same tables for every rung (M4 spec 4)."""

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from unstuk_ml.evaluate import (
    Metric,
    Scored,
    accuracy,
    bootstrap,
    confident_and_wrong,
    confusions,
    expected_calibration_error,
    held_out_accuracy,
    in_scope_accuracy,
    macro_f1,
    out_of_scope_precision,
    out_of_scope_recall,
    vague_handled,
)
from unstuk_ml.freeze import LOCK, frozen_changes
from unstuk_ml.keyword_matcher import load_matcher
from unstuk_ml.record import Record
from unstuk_ml.validate import DEFAULT_DATA_DIR

REPORTS = DEFAULT_DATA_DIR.parent / "ml" / "reports"
TEST_DIR = DEFAULT_DATA_DIR / "test"
HEADLINE: list[tuple[str, Metric]] = [
    ("Top-1 accuracy, in scope", in_scope_accuracy),
    ("Top-1 accuracy, all clear lines", accuracy),
    ("Macro-F1", macro_f1),
    ("Out-of-scope recall", out_of_scope_recall),
    ("Out-of-scope precision", out_of_scope_precision),
    ("**Confident and wrong**", confident_and_wrong),
    ("Vague lines answered with a question or decline", vague_handled),
    ("Expected calibration error", expected_calibration_error),
]


@dataclass(frozen=True)
class Decider:
    title: str
    command: str
    about: str
    held_out_note: str
    """Why the held-out score is what it is: each rung reaches those intents differently."""
    report: Path


KEYWORDS = Decider(
    title="Keyword baseline",
    command="unstuk-evaluate-keywords",
    about="M2's keyword matcher, ported to Python",
    held_out_note="not zero-shot: the matcher has rules for them",
    report=REPORTS / "keyword-baseline.md",
)


def render(decider: Decider, items: Sequence[Scored]) -> str:
    lines = [f"# {decider.title} on the proxy test set", ""]
    lines += [
        f"Written by `uv run {decider.command}`; do not edit by hand. {decider.about}, "
        f"scored on all {len(items)} frozen test lines. Intervals are 95% bootstrap intervals.",
        "",
        "| Metric | Value | 95% interval |",
        "| --- | --- | --- |",
    ]
    headline = [*HEADLINE, (f"Held-out intents ({decider.held_out_note})", held_out_accuracy)]
    for name, metric in headline:
        low, high = bootstrap(items, metric)
        lines.append(f"| {name} | {_pct(metric(items))} | {_pct(low)} to {_pct(high)} |")
    lines += [
        "",
        "## What the gate would do",
        "",
        "| Lines | Automatic | Confirm | Clarify | Decline |",
    ]
    lines += ["| --- | --- | --- | --- | --- |"]
    for name, group in _groups(items):
        counts = Counter(s.outcome for s in group)
        cells = " | ".join(str(counts[o]) for o in ("automatic", "confirm", "clarify", "decline"))
        lines.append(f"| {name} ({len(group)}) | {cells} |")
    lines += ["", "## By slice and by writer", ""]
    lines += ["Vague lines are left out: they have no single right answer.", ""]
    lines += ["| Group | Clear lines | Accuracy | 95% interval |", "| --- | --- | --- | --- |"]
    for name, group in _by_tag(items) + _by_writer(items):
        clear = [s for s in group if not s.vague]
        if not clear:
            continue
        low, high = bootstrap(clear, accuracy)
        lines.append(
            f"| {name} | {len(clear)} | {_pct(accuracy(clear))} | {_pct(low)} to {_pct(high)} |"
        )
    lines += ["", "## Most common mistakes", ""]
    for given, said, wrong in confusions(items):
        examples = "; ".join(f"`{s.record.text}`" for s in wrong[:2])
        lines.append(f"- **{given} → {said}** ({len(wrong)}): {examples}")
    return "\n".join(lines) + "\n"


def _groups(items: Sequence[Scored]) -> list[tuple[str, list[Scored]]]:
    clear = [s for s in items if not s.vague]
    return [
        ("in scope", [s for s in clear if s.record.labels != ["out_of_scope"]]),
        ("out of scope", [s for s in clear if s.record.labels == ["out_of_scope"]]),
        ("vague", [s for s in items if s.vague]),
    ]


def _by_tag(items: Sequence[Scored]) -> list[tuple[str, list[Scored]]]:
    groups: dict[str, list[Scored]] = defaultdict(list)
    for s in items:
        for tag in s.record.tags:
            if tag != "vague":
                groups[f"slice: {tag}"].append(s)
    return sorted(groups.items())


def _by_writer(items: Sequence[Scored]) -> list[tuple[str, list[Scored]]]:
    groups: dict[str, list[Scored]] = defaultdict(list)
    for s in items:
        groups[f"writer: {s.record.generator}"].append(s)
    return sorted(groups.items())


def _pct(value: float) -> str:
    return "n/a" if value != value else f"{value:.1%}"


def load_test(test_dir: Path = TEST_DIR) -> list[Record]:
    """The frozen test lines; refuses to read them unless they still match the lock."""
    if not (test_dir / LOCK).exists():
        raise FileNotFoundError(f"{test_dir / LOCK} is missing; the test set isn't frozen")
    changes = frozen_changes(test_dir)
    if changes:
        raise ValueError("the test set differs from its lock: " + "; ".join(changes))
    return [
        Record.model_validate_json(line)
        for path in sorted(test_dir.glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write(decider: Decider, items: Sequence[Scored]) -> None:
    decider.report.parent.mkdir(parents=True, exist_ok=True)
    decider.report.write_text(render(decider, items), encoding="utf-8")
    print(f"scored {len(items)} test lines; see {decider.report}")


def main() -> None:
    matcher = load_matcher()
    write(KEYWORDS, [Scored(r, matcher.choose(r.text)) for r in load_test()])
