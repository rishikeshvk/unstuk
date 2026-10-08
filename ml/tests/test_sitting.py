from pathlib import Path

import pytest

from unstuk_ml.field_cards import Card
from unstuk_ml.sitting import (
    blank_sitting,
    card_order,
    parse_sitting,
    read_sittings,
    to_messages,
)

CARDS = [
    Card(id="ring-1", about="phone_not_ringing", story="No sound when called."),
    Card(id="dim-1", about="screen_too_dim", story="The screen is hard to read."),
    Card(id="oos-pin", about="out_of_scope", story="You forgot the code."),
    Card(id="free-1", about="free", story="A problem you really had."),
]

SITTING = """\
participant: P01
medium: chat
consent: v1 2026-10-10

## dim-1
# The screen is hard to read.
cant see anything
its so dark

## ring-1
# No sound when called.

## free-1
phone not ringing when [name] calls
"""


def test_reads_answers_in_order_joining_lines_and_skipping_blank_cards() -> None:
    sitting = parse_sitting(SITTING)

    assert (sitting.participant, sitting.medium) == ("P01", "chat")
    assert sitting.consent == "v1 2026-10-10"
    assert sitting.answers == [
        ("dim-1", "cant see anything its so dark"),
        ("free-1", "phone not ringing when [name] calls"),
    ]
    assert sitting.unanswered == 1


def test_a_blank_sitting_parses_once_its_consent_date_is_written() -> None:
    blank = blank_sitting("P02", "in_person", CARDS)

    with pytest.raises(ValueError, match="consent"):
        parse_sitting(blank)
    sitting = parse_sitting(blank.replace("YYYY-MM-DD", "2026-10-10"))
    assert (sitting.answers, sitting.unanswered) == ([], len(CARDS))


def test_the_order_depends_on_the_participant_and_free_prompts_come_last() -> None:
    orders = {tuple(c.id for c in card_order(f"P{n:02d}", CARDS)) for n in range(1, 20)}

    assert len(orders) > 1
    assert all(order[-1] == "free-1" for order in orders)
    assert card_order("P01", CARDS) == card_order("P01", CARDS)


@pytest.mark.parametrize(
    ("change", "error"),
    [
        (("participant: P01", "participant: Asha"), "P01"),
        (("medium: chat", "medium: phone"), "medium"),
        (("consent: v1 2026-10-10\n", ""), "consent"),
        (("## free-1", "## dim-1"), "twice"),
    ],
)
def test_refuses_a_sitting_that_breaks_the_spec(change: tuple[str, str], error: str) -> None:
    with pytest.raises(ValueError, match=error):
        parse_sitting(SITTING.replace(*change))


def test_messages_carry_the_participant_and_card() -> None:
    messages = to_messages(parse_sitting(SITTING), CARDS)

    assert [(m.id, m.participant, m.medium, m.card) for m in messages] == [
        ("P01-dim-1", "P01", "chat", "dim-1"),
        ("P01-free-1", "P01", "chat", "free-1"),
    ]


def test_refuses_an_unknown_card() -> None:
    with pytest.raises(ValueError, match="unknown cards"):
        to_messages(parse_sitting(SITTING.replace("## dim-1", "## dim-9")), CARDS)


def test_a_file_must_hold_its_own_participant(tmp_path: Path) -> None:
    (tmp_path / "P02.txt").write_text(SITTING)

    with pytest.raises(ValueError, match="P01's sitting"):
        read_sittings(tmp_path)
