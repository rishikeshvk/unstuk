from unstuk_ml.catalog import load_catalog
from unstuk_ml.state_slice import (
    PAIRS,
    ambiguous,
    build,
    deciding_checks,
    distractors,
    excluded_checks,
    split_by_text,
)

CATALOG = load_catalog()


def texts(per_pair: int = 9) -> dict[tuple[str, str], list[str]]:
    return {pair: [f"{pair[0]} or {pair[1]} text {n}" for n in range(per_pair)] for pair in PAIRS}


def test_deciding_checks_leave_out_shared_and_held_out_checks() -> None:
    a, b = deciding_checks(CATALOG, ("phone_not_ringing", "notifications_missing"))

    assert "dnd_on" not in a + b
    assert a == ["ring_volume_zero", "ringer_not_normal"]
    assert b == ["data_saver_on"]
    assert "auto_time_off" not in deciding_checks(CATALOG, ("no_internet", "wifi_no_load"))[1]
    assert "auto_time_off" in excluded_checks(CATALOG)


def test_every_label_is_the_side_whose_cause_holds() -> None:
    for record in build(texts(), CATALOG):
        pair = next(p for n, p in enumerate(PAIRS, 1) if record.batch == f"state-p{n}")
        a, b = deciding_checks(CATALOG, pair)
        state = set(record.state or [])
        if state & set(a):
            assert record.labels == [pair[0]]
        elif state & set(b):
            assert record.labels == [pair[1]]
        else:
            assert record.labels == list(pair)
            assert record.tags == ["vague"]


def test_distractors_belong_to_neither_side() -> None:
    for pair in PAIRS:
        involved = set(CATALOG.causes[pair[0]]) | set(CATALOG.causes[pair[1]])
        assert involved.isdisjoint(distractors(CATALOG, pair))


def test_a_text_never_sits_on_both_sides_of_the_split() -> None:
    train, test = split_by_text(build(texts(), CATALOG))

    assert {r.text for r in train}.isdisjoint({r.text for r in test})
    assert len(test) > 0


def test_keeps_only_texts_the_blind_labeller_left_open() -> None:
    pair = ("screen_too_dim", "colours_wrong")
    given = {pair: ["looks strange", "too dark"]}
    blind = {"looks strange": ["screen_too_dim", "colours_wrong"], "too dark": ["screen_too_dim"]}

    assert ambiguous(given, blind) == {pair: ["looks strange"]}


def test_the_build_is_the_same_every_run() -> None:
    assert build(texts(), CATALOG) == build(texts(), CATALOG)
