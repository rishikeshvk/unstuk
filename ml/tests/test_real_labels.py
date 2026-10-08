from collections.abc import Iterator

import pytest

from unstuk_ml.real_labels import (
    RealLabel,
    again_sample,
    label_loop,
    parse_answer,
    pending,
)
from unstuk_ml.real_messages import RealMessage

INTENTS = ["no_internet", "phone_not_ringing", "screen_too_dim"]
MESSAGE = RealMessage(
    id="P01-ring-1", participant="P01", medium="chat", card="ring-1", text="no ring"
)


def messages(n: int) -> list[RealMessage]:
    return [
        RealMessage(
            id=f"P0{i % 3 + 1}-c{i}",
            participant=f"P0{i % 3 + 1}",
            medium="chat",
            card=f"c{i}",
            text=f"line {i}",
        )
        for i in range(n)
    ]


@pytest.mark.parametrize(
    ("answer", "labels", "tags"),
    [
        ("2", ["phone_not_ringing"], []),
        ("1, 3", ["no_internet", "screen_too_dim"], []),
        ("o", ["out_of_scope"], []),
        ("v 1 2 3", ["no_internet", "phone_not_ringing", "screen_too_dim"], ["vague"]),
    ],
)
def test_reads_numbers_out_of_scope_and_vague(
    answer: str, labels: list[str], tags: list[str]
) -> None:
    assert parse_answer(answer, MESSAGE, INTENTS) == RealLabel(
        id=MESSAGE.id, labels=labels, tags=tags
    )


def test_x_drops_the_line() -> None:
    assert parse_answer("x", MESSAGE, INTENTS).dropped


@pytest.mark.parametrize("answer", ["", "4", "ring", "1 2 3", "o 1", "2 2", "v"])
def test_refuses_what_the_label_contract_forbids(answer: str) -> None:
    with pytest.raises(ValueError):
        parse_answer(answer, MESSAGE, INTENTS)


def test_the_order_mixes_participants_and_skips_what_is_done() -> None:
    lines = messages(12)
    order = pending(lines, set())

    assert [m.participant for m in order[:3]] != ["P01", "P01", "P01"]
    assert sorted(m.id for m in order) == sorted(m.id for m in lines)
    assert pending(lines, {order[0].id}) == order[1:]


def test_the_loop_asks_again_after_a_bad_answer_and_stops_on_q() -> None:
    answers: Iterator[str] = iter(["9", "1", "o", "q"])
    shown: list[str] = []
    saved: list[RealLabel] = []

    count = label_loop(messages(5), INTENTS, lambda _: next(answers), shown.append, saved.append)

    assert count == 2
    assert [label.labels for label in saved] == [["no_internet"], ["out_of_scope"]]
    assert any("not a number" in line for line in shown)


def test_the_loop_never_shows_the_card_or_participant() -> None:
    shown: list[str] = []
    label_loop([MESSAGE], INTENTS, lambda _: "2", shown.append, lambda _: None)

    assert not [line for line in shown if "ring-1" in line or "P01" in line]


def test_relabels_a_fixed_sample_of_kept_lines() -> None:
    lines = messages(60)
    labels = [RealLabel(id=m.id, labels=[], dropped=True) for m in lines[:10]]
    labels += [RealLabel(id=m.id, labels=["no_internet"]) for m in lines[10:]]

    sample = again_sample(lines, labels)

    assert len(sample) == 40
    assert not {m.id for m in sample} & {m.id for m in lines[:10]}
    assert sample == again_sample(lines, labels)
