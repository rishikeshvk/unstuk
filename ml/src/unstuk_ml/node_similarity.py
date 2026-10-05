"""Node-label similarity (M4 spec decision 4): the label closest in meaning to the question.

Scored beside M3's string baseline on the same questions, with options as shown and cut at the
first ',' or '.' as the app's LabelMatch does, so a tile's state ("Wi-Fi, Off") can't blur it.
"""

import json
import re
from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from unstuk_ml.baseline_report import REPORTS
from unstuk_ml.encoder import embed_cached
from unstuk_ml.evaluate import share_interval
from unstuk_ml.node_labels import Label, NodeQuestion, match, selector_labels
from unstuk_ml.validate import DEFAULT_DATA_DIR

Embed = Callable[[Sequence[str]], NDArray[np.float32]]
Picker = Callable[[NodeQuestion], str | None]
NODES_DIR = DEFAULT_DATA_DIR / "nodes"
# The labels M3's baseline knew in advance; the Moto's own selector file is the test's answer key.
PIXEL = DEFAULT_DATA_DIR.parent / "android" / "app" / "src" / "main" / "assets" / "selectors"
REPORT = REPORTS / "node-similarity.md"


def cut(question: NodeQuestion) -> NodeQuestion:
    """Each option up to its first ',' or '.', as the app's LabelMatch reads it."""
    # model_copy skips validation: two options may cut to the same text, which is fine here.
    return question.model_copy(
        update={"options": [_lead(o) for o in question.options], "answer": _lead(question.answer)}
    )


def similarity_picker(embed: Embed, questions: Sequence[NodeQuestion]) -> Picker:
    texts = sorted({t for q in questions for t in (q.question, *q.options)})
    vectors = dict(zip(texts, embed(texts), strict=True))

    def pick(question: NodeQuestion) -> str:
        options = np.stack([vectors[o] for o in question.options])
        return question.options[int(np.argmax(options @ vectors[question.question]))]

    return pick


def string_picker(known: Sequence[Label]) -> Picker:
    by_target: dict[str, list[str]] = defaultdict(list)
    for label in known:
        by_target[label.item].append(label.text)
    return lambda question: match(question.options, by_target[question.target])


def known_labels() -> list[Label]:
    rows = json.loads((NODES_DIR / "aosp-labels.json").read_text(encoding="utf-8"))
    pixel = json.loads((PIXEL / "pixel.json").read_text(encoding="utf-8"))
    return [Label(**row) for row in rows] + selector_labels(pixel)


def render(dev: Sequence[NodeQuestion], test: Sequence[NodeQuestion], embed: Embed) -> str:
    known = known_labels()
    variants = [
        ("as shown", dev, test),
        ("cut at ',' or '.'", [cut(q) for q in dev], [cut(q) for q in test]),
    ]
    lines = [
        "# Node-label similarity",
        "",
        "Written by `uv run unstuk-node-similarity`; do not edit by hand. Frozen bge-small picks "
        "the option whose vector is closest to the question's; M3's string baseline matches labels "
        "known from AOSP and the Pixel. Dev is Xiaomi wording, the test is the Moto's screens. "
        "Dev intervals are 95% bootstrap intervals.",
        "",
        f"| Method | Options | Dev ({len(dev)}) | 95% interval | Test ({len(test)}) |",
        "| --- | --- | --- | --- | --- |",
    ]
    picks: dict[tuple[str, str], list[str | None]] = {}
    for variant, dev_q, test_q in variants:
        for method, picker in (
            ("String baseline", string_picker(known)),
            ("Similarity", similarity_picker(embed, [*dev_q, *test_q])),
        ):
            dev_right = [picker(q) == q.answer for q in dev_q]
            picks[(method, variant)] = [picker(q) for q in test_q]
            test_right = sum(
                p == q.answer for p, q in zip(picks[(method, variant)], test_q, strict=True)
            )
            low, high = share_interval(dev_right)
            lines.append(
                f"| {method} | {variant} | {sum(dev_right) / len(dev_right):.1%} | "
                f"{low:.1%} to {high:.1%} | {test_right}/{len(test_q)} |"
            )
    lines += ["", "## Each test question", ""]
    header = ["Question", "Answer", *(f"{m}, {v}" for m, v in picks)]
    lines += ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    for i, q in enumerate(test):
        marks = [_mark(chosen[i], _answer(q, variant)) for (_, variant), chosen in picks.items()]
        lines.append("| " + " | ".join([q.target, f"`{q.answer}`", *marks]) + " |")
    return "\n".join(lines) + "\n"


def _answer(question: NodeQuestion, variant: str) -> str:
    return question.answer if variant == "as shown" else _lead(question.answer)


def _mark(pick: str | None, answer: str) -> str:
    return "none" if pick is None else f"{'✓' if pick == answer else '✗'} `{pick}`"


def _lead(text: str) -> str:
    return re.split(r"[,.]", text, maxsplit=1)[0].strip()


def _read(path: Path) -> list[NodeQuestion]:
    return [
        NodeQuestion.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    text = render(_read(NODES_DIR / "dev.jsonl"), _read(NODES_DIR / "test.jsonl"), embed_cached)
    REPORT.write_text(text, encoding="utf-8")
    print(f"see {REPORT}")
