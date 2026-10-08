"""Sitting files (m8-spec section 2): one participant's answers to the cards, pasted as typed.

A sitting file is a header, then one section per card:

    participant: P01
    medium: chat
    consent: v1 2026-10-10

    ## ring-1
    # Your daughter says she called you three times...
    phone not ringing when daughter calls

Lines starting with `#` (but not `##`) are the card's story and are ignored. An answer on several
lines is joined with spaces; a card left blank was not answered.
"""

import argparse
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast, get_args

from unstuk_ml.field_cards import FREE, Card, load_cards
from unstuk_ml.freeze import LOCK
from unstuk_ml.real_messages import (
    MESSAGES_FILE,
    REAL_DIR,
    SITTINGS_DIR,
    Medium,
    RealMessage,
    write_messages,
)

PARTICIPANT = re.compile(r"P\d{2}")
CONSENT = re.compile(r"v1 \d{4}-\d{2}-\d{2}")
CARD_HEADER = "## "
COMMENT = "#"
HEADER_KEYS = ("participant", "medium", "consent")


@dataclass(frozen=True)
class Sitting:
    participant: str
    medium: Medium
    consent: str
    answers: list[tuple[str, str]]
    """(card id, text) for every answered card, in the file's order."""
    unanswered: int


def card_order(participant: str, cards: Sequence[Card]) -> list[Card]:
    """Shuffled by the participant's code, so no card is always first; free prompts last."""
    stories = [c for c in cards if c.about != FREE]
    random.Random(participant).shuffle(stories)
    return stories + [c for c in cards if c.about == FREE]


def blank_sitting(participant: str, medium: Medium, cards: Sequence[Card]) -> str:
    _check_participant(participant)
    lines = [
        "# M8 sitting. Read the consent text in docs/m8-spec.md, section 3; on a yes,",
        "# write its date below. Read the prompt in section 2 once, then give the cards",
        "# in this order. Paste each answer under its card as typed; only names and",
        "# numbers become [name] and [number].",
        f"participant: {participant}",
        f"medium: {medium}",
        "consent: v1 YYYY-MM-DD",
    ]
    for card in card_order(participant, cards):
        lines += ["", f"{CARD_HEADER}{card.id}", f"{COMMENT} {card.story}", ""]
    return "\n".join(lines) + "\n"


def parse_sitting(text: str) -> Sitting:
    header: dict[str, str] = {}
    sections: list[tuple[str, list[str]]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith(CARD_HEADER):
            sections.append((line.removeprefix(CARD_HEADER).strip(), []))
        elif not line or line.startswith(COMMENT):
            continue
        elif sections:
            sections[-1][1].append(line)
        else:
            key, _, value = line.partition(":")
            if key not in HEADER_KEYS or key in header:
                raise ValueError(f"line {number}: expected one each of {', '.join(HEADER_KEYS)}")
            header[key] = value.strip()
    missing = [key for key in HEADER_KEYS if key not in header]
    if missing:
        raise ValueError(f"the header lacks {', '.join(missing)}")
    _check_participant(header["participant"])
    if header["medium"] not in get_args(Medium):
        raise ValueError(f"medium must be one of {', '.join(get_args(Medium))}")
    if not CONSENT.fullmatch(header["consent"]):
        raise ValueError("consent must be 'v1' and the date of the participant's yes")
    cards = [card for card, _ in sections]
    repeated = sorted({card for card in cards if cards.count(card) > 1})
    if repeated:
        raise ValueError(f"cards answered twice: {', '.join(repeated)}")
    return Sitting(
        participant=header["participant"],
        medium=cast(Medium, header["medium"]),
        consent=header["consent"],
        answers=[(card, " ".join(lines)) for card, lines in sections if lines],
        unanswered=sum(1 for _, lines in sections if not lines),
    )


def to_messages(sitting: Sitting, cards: Sequence[Card]) -> list[RealMessage]:
    known = {c.id for c in cards}
    unknown = sorted({card for card, _ in sitting.answers} - known)
    if unknown:
        raise ValueError(f"{sitting.participant}: unknown cards {', '.join(unknown)}")
    return [
        RealMessage(
            id=f"{sitting.participant}-{card}",
            participant=sitting.participant,
            medium=sitting.medium,
            card=card,
            text=text,
        )
        for card, text in sitting.answers
    ]


def read_sittings(sittings_dir: Path) -> list[Sitting]:
    sittings = []
    for path in sorted(sittings_dir.glob("*.txt")):
        try:
            sitting = parse_sitting(path.read_text(encoding="utf-8"))
        except ValueError as error:
            raise ValueError(f"{path.name}: {error}") from error
        if sitting.participant != path.stem:
            raise ValueError(f"{path.name} holds {sitting.participant}'s sitting")
        sittings.append(sitting)
    return sittings


def _check_participant(code: str) -> None:
    if not PARTICIPANT.fullmatch(code):
        raise ValueError(f"participant codes look like P01, not {code!r}")


def main_sheet() -> None:
    parser = argparse.ArgumentParser(description="Write a blank sitting file for one participant.")
    parser.add_argument("participant", help="a code like P01; never a name")
    parser.add_argument("--medium", choices=get_args(Medium), required=True)
    args = parser.parse_args()
    path = SITTINGS_DIR / f"{args.participant}.txt"
    if path.exists():
        raise SystemExit(f"{path} exists; a participant sits once")
    text = blank_sitting(args.participant, args.medium, load_cards())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")


def main_import() -> None:
    argparse.ArgumentParser(description="Turn the sitting files into messages.jsonl.").parse_args()
    if (REAL_DIR / LOCK).exists():
        raise SystemExit(f"{REAL_DIR} is frozen; its messages can't change")
    cards = load_cards()
    sittings = read_sittings(SITTINGS_DIR)
    messages = [m for sitting in sittings for m in to_messages(sitting, cards)]
    write_messages(messages)
    unanswered = sum(s.unanswered for s in sittings)
    print(
        f"{len(messages)} messages from {len(sittings)} participants "
        f"({unanswered} cards unanswered) written to {MESSAGES_FILE}"
    )
