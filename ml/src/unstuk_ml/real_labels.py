"""Blind labels for real messages (m8-spec section 4), given by the developer one line at a time.

Only the text is shown: never the card, the participant or any model's answer. Every answer is
appended at once, so the loop can stop and resume. Answers are intent numbers from the table, or:

    o       out of scope
    v 1 5   vague, with up to three plausible intents
    x       drop: mostly not English (guide section 9)
    ?       show the table again
    q       stop for now
"""

import argparse
import json
import random
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from unstuk_ml.catalog import load_catalog
from unstuk_ml.freeze import LOCK
from unstuk_ml.labels import OUT_OF_SCOPE, VAGUE
from unstuk_ml.real_messages import MESSAGES_FILE, REAL_DIR, RealMessage, read_messages
from unstuk_ml.record import Record

LABELS_FILE = REAL_DIR / "labels.jsonl"
# The week-later relabelling, after the freeze; not .jsonl, which the lock covers.
AGAIN_FILE = REAL_DIR / "labels-again.ndjson"
AGAIN_SIZE = 40
SEED = 8


class RealLabel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    labels: list[str]
    tags: list[str] = []
    dropped: bool = False


class Stop(Exception):
    """The labeller asked to stop for now."""


def parse_answer(answer: str, message: RealMessage, intents: Sequence[str]) -> RealLabel:
    """The label an answer gives, checked against the label contract; ValueError if it's not one."""
    words = answer.replace(",", " ").split()
    if words == ["x"]:
        return RealLabel(id=message.id, labels=[], dropped=True)
    tags = [VAGUE] if words[:1] == ["v"] else []
    labels = [_label(word, intents) for word in words[len(tags) :]]
    if not labels:
        raise ValueError("give at least one label")
    try:
        Record(
            id=message.id,
            text=message.text,
            labels=labels,
            tags=tags,
            source="real",
            generator=message.participant,
            batch="real",
        )
    except ValidationError as error:
        raise ValueError(error.errors()[0]["msg"]) from error
    return RealLabel(id=message.id, labels=labels, tags=tags)


def pending(messages: Sequence[RealMessage], done: set[str]) -> list[RealMessage]:
    """Unlabelled messages in one fixed order, shuffled across participants and cards."""
    order = sorted(messages, key=lambda m: m.id)
    random.Random(SEED).shuffle(order)
    return [m for m in order if m.id not in done]


def again_sample(messages: Sequence[RealMessage], labels: Sequence[RealLabel]) -> list[RealMessage]:
    """The lines to label a second time: a random sample of the kept, not dropped, ones."""
    kept = {label.id for label in labels if not label.dropped}
    pool = sorted((m for m in messages if m.id in kept), key=lambda m: m.id)
    return random.Random(SEED).sample(pool, min(AGAIN_SIZE, len(pool)))


def label_loop(
    todo: Sequence[RealMessage],
    intents: Sequence[str],
    ask: Callable[[str], str],
    show: Callable[[str], None],
    save: Callable[[RealLabel], None],
) -> int:
    """Asks for each message's label until done or told to stop; returns how many were saved."""
    show(table(intents))
    saved = 0
    for number, message in enumerate(todo, start=1):
        show(f"\n[{number}/{len(todo)}] {message.text}")
        try:
            save(_ask_until_valid(message, intents, ask, show))
        except Stop:
            break
        saved += 1
    return saved


def table(intents: Sequence[str]) -> str:
    rows = [f"{n:>3}  {intent}" for n, intent in enumerate(intents, start=1)]
    return "\n".join([*rows, "  o  out_of_scope", "v …  vague", "  x  drop", "  q  stop"])


def read_labels(path: Path) -> list[RealLabel]:
    if not path.exists():
        return []
    return [
        RealLabel.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _ask_until_valid(
    message: RealMessage,
    intents: Sequence[str],
    ask: Callable[[str], str],
    show: Callable[[str], None],
) -> RealLabel:
    while True:
        answer = ask("label> ").strip()
        if answer == "q":
            raise Stop
        if answer == "?":
            show(table(intents))
            continue
        try:
            return parse_answer(answer, message, intents)
        except ValueError as error:
            show(f"  {error}")


def _label(word: str, intents: Sequence[str]) -> str:
    if word == "o":
        return OUT_OF_SCOPE
    if word.isdigit() and 1 <= int(word) <= len(intents):
        return intents[int(word) - 1]
    raise ValueError(f"{word!r} is not a number from the table, o, v or x")


def _appender(path: Path) -> Callable[[RealLabel], None]:
    def save(label: RealLabel) -> None:
        with path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(label.model_dump()) + "\n")

    return save


def main() -> None:
    parser = argparse.ArgumentParser(description="Label real messages blind, one at a time.")
    parser.add_argument(
        "--again", action="store_true", help="the week-later relabelling of a random sample"
    )
    args = parser.parse_args()
    messages = read_messages(MESSAGES_FILE)
    labels = read_labels(LABELS_FILE)
    frozen = (REAL_DIR / LOCK).exists()
    if args.again != frozen:
        raise SystemExit(
            "relabel only after freezing" if args.again else f"{REAL_DIR} is frozen already"
        )
    path, todo = (
        (AGAIN_FILE, again_sample(messages, labels)) if args.again else (LABELS_FILE, messages)
    )
    todo = pending(todo, {label.id for label in read_labels(path)})
    saved = label_loop(todo, list(load_catalog().intents), input, print, _appender(path))
    print(f"\n{saved} labelled; {len(todo) - saved} left in {path}")
