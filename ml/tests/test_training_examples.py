import os
import subprocess
import sys
from collections.abc import Sequence

import pytest
from records import make

from unstuk_ml.catalog import load_catalog
from unstuk_ml.folds import trained_intents
from unstuk_ml.labels import HELD_OUT
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.record import Record
from unstuk_ml.state_slice import excluded_checks
from unstuk_ml.training_examples import (
    MAX_DISTRACTORS,
    OTHER_OPTIONS,
    Example,
    epoch,
)

CATALOG = load_catalog()
INTENTS = trained_intents(CATALOG)
OPTION_OF = {option: intent for intent, option in CATALOG.intents.items()}
WORDING_OF = {w: intent for intent, ws in CATALOG.wordings.items() for w in ws}
RECORDS = [
    make(f"line-{n}", f"complaint number {n} about the phone", label)
    for n, label in enumerate([*INTENTS, "out_of_scope"] * 10)
]
NODE = NodeQuestion(
    id="node-1",
    target="airplane_mode",
    question="Which item on the screen is the airplane mode switch?",
    options=["Dark theme", "Airplane mode", "Torch"],
    answer="Airplane mode",
    source="aosp:values",
    oem="aosp",
)


def draw(
    records: Sequence[Record] | None = None,
    number: int = 0,
    state: bool = False,
    typos: bool = False,
    intents: list[str] = INTENTS,
    wordings: bool = False,
    drop_gold: bool = False,
) -> list[Example]:
    return epoch(
        RECORDS if records is None else records,
        [],
        CATALOG,
        intents,
        seed=7,
        number=number,
        state=state,
        typos=typos,
        wordings=wordings,
        drop_gold=drop_gold,
    )


def test_the_gold_option_is_offered_once_among_three_to_eleven_others() -> None:
    for record, example in zip(RECORDS, draw(), strict=True):
        if example.out_of_scope:
            continue
        gold = [OPTION_OF[example.options[i]] for i in example.answers]

        assert gold == record.labels
        assert len(set(example.options)) == len(example.options)
        assert OTHER_OPTIONS[0] <= len(example.options) - 1 <= OTHER_OPTIONS[1]


def test_only_the_runs_intents_are_offered() -> None:
    offered = {OPTION_OF[o] for example in draw() for o in example.options}

    assert offered == set(INTENTS)
    assert not offered & HELD_OUT


def test_a_fold_offers_fewer_options_without_failing() -> None:
    kept = INTENTS[:4]
    records = [make("a", "no net", kept[0]), make("b", "book a cab", "out_of_scope")]

    for example in draw(records, intents=kept):
        assert {OPTION_OF[o] for o in example.options} <= set(kept)


def test_a_line_naming_an_intent_the_run_cant_offer_is_an_error() -> None:
    with pytest.raises(ValueError, match="line-0"):
        draw(RECORDS[:1], intents=INTENTS[1:])


def test_out_of_scope_lines_ask_the_noul_and_mask_the_choice() -> None:
    examples = draw([make("a", "book a cab", "out_of_scope"), make("b", "no net", "no_internet")])

    assert [e.out_of_scope for e in examples] == [True, False]
    assert examples[0].answers == frozenset()
    assert len(examples[1].answers) == 1


def test_a_line_with_two_problems_has_two_answers() -> None:
    (example,) = draw([make("a", "silent and no net", labels=["phone_not_ringing", "no_internet"])])

    assert {OPTION_OF[example.options[i]] for i in example.answers} == {
        "phone_not_ringing",
        "no_internet",
    }


def test_only_a_vague_line_spreads_its_target_over_its_readings() -> None:
    readings = ["phone_not_ringing", "notifications_missing"]
    vague, multi = draw(
        [
            make("a", "no sound", labels=readings, tags=["vague"]),
            make("b", "silent and no alerts", labels=readings),
        ]
    )

    assert vague.spread
    assert len(vague.answers) == 2
    assert not multi.spread


def test_options_are_drawn_again_each_epoch_and_repeat_for_the_same_epoch() -> None:
    assert draw(number=0) == draw(number=0)
    assert [e.options for e in draw(number=0)] != [e.options for e in draw(number=1)]


def test_state_and_typos_never_change_the_options_drawn() -> None:
    plain = [e.options for e in draw()]

    assert [e.options for e in draw(state=True, typos=True)] == plain


def test_without_state_or_typos_the_line_is_unchanged() -> None:
    for record, example in zip(RECORDS, draw(), strict=True):
        assert (example.text, example.state) == (record.text, "")


def test_typos_change_about_a_quarter_of_the_lines() -> None:
    changed = sum(e.text != r.text for r, e in zip(RECORDS, draw(typos=True), strict=True))

    assert 0.1 < changed / len(RECORDS) < 0.4


def test_a_records_own_state_is_rendered() -> None:
    record = make("a", "silent", "phone_not_ringing", state=["ringer_not_normal", "dnd_on"])

    (example,) = draw([record], state=True)

    assert example.state == "The ringer is on silent or vibrate. Do Not Disturb is on."


def test_distractor_state_says_nothing_about_the_label() -> None:
    for record, example in zip(RECORDS, draw(state=True), strict=True):
        checks = [c for c in CATALOG.checks if CATALOG.findings[c] in example.state]
        causes = {c for label in record.labels for c in CATALOG.causes.get(label, ())}

        assert len(checks) <= MAX_DISTRACTORS
        assert not set(checks) & (causes | excluded_checks(CATALOG))


def test_a_node_question_keeps_its_options_and_skips_the_noul() -> None:
    (example,) = epoch(
        [],
        [NODE],
        CATALOG,
        INTENTS,
        seed=7,
        number=0,
        state=True,
        typos=True,
        wordings=True,
        drop_gold=True,
    )

    assert example == Example(
        text=NODE.question,
        state="",
        options=("Dark theme", "Airplane mode", "Torch"),
        answers=frozenset({1}),
        out_of_scope=None,
    )


def test_an_epoch_does_not_depend_on_string_hashing() -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "from unstuk_ml.catalog import load_catalog\n"
        "from unstuk_ml.folds import trained_intents\n"
        "from unstuk_ml.record import Record\n"
        "from unstuk_ml.training_examples import epoch\n"
        "c = load_catalog()\n"
        "r = [Record(id=f'r{n}', text='phone is silent', labels=[i], source='generated',\n"
        "            generator='g', batch='b') for n, i in enumerate(trained_intents(c))]\n"
        "print(epoch(r, [], c, trained_intents(c), seed=7, number=0, state=True, typos=True,\n"
        "            wordings=True, drop_gold=True))\n"
    )
    outputs = {
        subprocess.run(
            [sys.executable, "-c", script],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for seed in range(8)
    }

    assert len(outputs) == 1


def test_wordings_change_only_the_option_texts_and_keep_the_canonical_ones_often() -> None:
    plain, worded = draw(), draw(wordings=True)
    offered = [o for e in worded for o in e.options]

    for before, after in zip(plain, worded, strict=True):
        assert (after.text, after.state, after.answers) == (
            before.text,
            before.state,
            before.answers,
        )
        assert [OPTION_OF[o] for o in before.options] == [
            OPTION_OF.get(o) or WORDING_OF[o] for o in after.options
        ]
    assert 0.4 < sum(o in OPTION_OF for o in offered) / len(offered) < 0.6


def test_a_fold_never_offers_a_removed_intents_wordings() -> None:
    kept = INTENTS[:4]
    records = [make(f"r{n}", "no net", kept[n % 4]) for n in range(40)]

    offered = {o for e in draw(records, intents=kept, wordings=True) for o in e.options}

    assert {OPTION_OF.get(o) or WORDING_OF[o] for o in offered} <= set(kept)


def test_a_quarter_of_in_scope_lines_lose_their_correct_option_and_turn_out_of_scope() -> None:
    plain, dropped = draw(), draw(drop_gold=True)
    in_scope = [(p, d) for p, d in zip(plain, dropped, strict=True) if not p.out_of_scope]
    turned = [(p, d) for p, d in in_scope if d.out_of_scope]

    assert 0.15 < len(turned) / len(in_scope) < 0.35
    for before, after in turned:
        assert after.answers == frozenset()
        assert len(after.options) == len(before.options) - len(before.answers)
        assert len(after.options) >= 3
        assert set(after.options) < set(before.options)


def test_out_of_scope_lines_are_left_alone_and_off_changes_nothing() -> None:
    plain, dropped = draw(), draw(drop_gold=True)

    for before, after in zip(plain, dropped, strict=True):
        if before.out_of_scope or not after.out_of_scope:
            assert after == before
