import json
from pathlib import Path

import pytest
from records import make

from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import Scored
from unstuk_ml.freeze import freeze
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.real_labels import RealLabel
from unstuk_ml.real_messages import RealMessage, write_messages
from unstuk_ml.real_test import (
    RealSet,
    bar_rows,
    card_match,
    enough,
    gated,
    leave_one_out,
    load_real,
    render_report,
    ships,
)
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.zero_shot import ZERO_SHOT

LABELS = ["no_internet", "phone_not_ringing", "screen_too_dim", OUT_OF_SCOPE]


def lines(people: int, each: int) -> list[Scored]:
    """The model right and sure on every line, for `people` participants."""
    items = []
    for p in range(1, people + 1):
        for n in range(each):
            label = LABELS[n % len(LABELS)]
            record = make(f"P0{p}-{n}", f"private words {p} {n}", label, generator=f"P0{p}")
            items.append(Scored(record, {label: 1.0}))
    return items


def baseline_wrong_on(items: list[Scored], wrong: set[str]) -> dict[str, list[Scored]]:
    scored = [
        Scored(s.record, {"colours_wrong": 1.0}) if s.record.id in wrong else s for s in items
    ]
    return {ZERO_SHOT.title: scored, ENCODER.decider.title: scored, TFIDF.decider.title: scored}


def test_ships_when_the_lead_holds_without_any_one_participant() -> None:
    items = lines(4, 12)
    base = baseline_wrong_on(items, {s.record.id for s in items if int(s.record.id[4:]) < 3})

    rows = bar_rows(items, base)
    without = leave_one_out(items, base)

    assert all(row.passes for row in gated(rows))
    assert not any(without.values())
    assert ships(rows, without)


def test_does_not_ship_when_one_participant_carries_the_lead() -> None:
    items = lines(4, 12)
    base = baseline_wrong_on(items, {s.record.id for s in items if s.record.generator == "P01"})

    rows = bar_rows(items, base)
    without = leave_one_out(items, base)

    assert all(row.passes for row in gated(rows))
    assert [row.requirement.name for row in without["P01"]] == [
        "Top-1 accuracy, in scope",
        "Macro-F1",
    ]
    assert not ships(rows, without)


def test_held_out_intents_are_not_gated() -> None:
    items = lines(4, 4)
    rows = bar_rows(items, baseline_wrong_on(items, set()))

    assert "Held-out intents" not in [row.requirement.name for row in gated(rows)]
    assert len(gated(rows)) == len(rows) - 1


def test_needs_150_clear_lines_and_4_participants() -> None:
    assert enough([s.record for s in lines(4, 38)])
    assert not enough([s.record for s in lines(4, 37)])
    assert not enough([s.record for s in lines(3, 60)])


def test_card_lines_match_when_labelled_as_their_story() -> None:
    items = lines(1, 3)
    cards = {"P01-0": "no_internet", "P01-1": "screen_too_dim", "P01-2": "free"}

    assert card_match(items, cards) == (1, 2)


def write_real(real_dir: Path, labels: list[RealLabel]) -> None:
    write_messages(
        [
            RealMessage(
                id="P01-ring-1", participant="P01", medium="chat", card="ring-1", text="no ring"
            ),
            RealMessage(
                id="P01-free-1", participant="P01", medium="chat", card="free-1", text="kuch nahi"
            ),
        ],
        real_dir / "messages.jsonl",
    )
    (real_dir / "labels.jsonl").write_text(
        "".join(json.dumps(label.model_dump()) + "\n" for label in labels)
    )


def test_joins_labels_and_leaves_dropped_lines_out(tmp_path: Path) -> None:
    write_real(
        tmp_path,
        [
            RealLabel(id="P01-ring-1", labels=["phone_not_ringing"]),
            RealLabel(id="P01-free-1", labels=[], dropped=True),
        ],
    )
    freeze(tmp_path)

    real = load_real(tmp_path)

    assert [(r.id, r.labels, r.generator, r.batch) for r in real.records] == [
        ("P01-ring-1", ["phone_not_ringing"], "P01", "chat")
    ]
    assert (real.cards, real.dropped) == ({"P01-ring-1": "phone_not_ringing"}, 1)


def test_refuses_unfrozen_or_unlabelled_lines(tmp_path: Path) -> None:
    write_real(tmp_path, [RealLabel(id="P01-ring-1", labels=["phone_not_ringing"])])
    with pytest.raises(FileNotFoundError, match="freeze"):
        load_real(tmp_path)

    freeze(tmp_path)
    with pytest.raises(ValueError, match="1 have none"):
        load_real(tmp_path)


def test_the_report_quotes_no_message() -> None:
    items = lines(4, 4)
    real = RealSet(
        records=[s.record for s in items],
        cards={s.record.id: "free" for s in items},
        dropped=0,
        hashes={"labels.jsonl": "ab" * 32},
    )

    report = render_report(real, items, baseline_wrong_on(items, set()), "test")

    assert "private words" not in report
    assert "16 lines from 4 participants" in report
