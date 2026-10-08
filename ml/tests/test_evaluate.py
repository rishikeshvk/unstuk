import pytest
from records import make

from unstuk_ml.evaluate import (
    M2_GATE,
    GateLines,
    Scored,
    accuracy,
    beats,
    bootstrap,
    brier_score,
    calibration_bins,
    changed,
    confident_and_wrong,
    expected_calibration_error,
    in_scope_accuracy,
    load_gate,
    macro_f1,
    out_of_scope_precision,
    out_of_scope_recall,
    paired_bootstrap,
    vague_handled,
)

RIGHT = Scored(make("a", "no net"), {"no_internet": 1.0})
WRONG_SURE = Scored(make("b", "ring finger", "out_of_scope"), {"phone_not_ringing": 1.0})
DECLINED_OOS = Scored(make("c", "weather?", "out_of_scope"), {})
UNSURE = Scored(
    make("d", "dark grey", "colours_wrong"), {"screen_too_dim": 0.6, "colours_wrong": 0.4}
)
VAGUE_CLARIFIED = Scored(
    make("e", "no sound", tags=["vague"], labels=["phone_not_ringing", "notifications_missing"]),
    # Below the gate's 0.5 line: a two-way tie at exactly 0.5 would be confirmed, not clarified.
    {"phone_not_ringing": 0.4, "notifications_missing": 0.3, "cant_hear_call": 0.3},
)
VAGUE_SURE = Scored(
    make("f", "app broken", tags=["vague"], labels=["no_internet", "app_permission"]),
    {"no_internet": 1.0},
)
ALL = [RIGHT, WRONG_SURE, DECLINED_OOS, UNSURE, VAGUE_CLARIFIED, VAGUE_SURE]


def test_accuracy_ignores_vague_lines_and_counts_a_decline_as_out_of_scope() -> None:
    assert accuracy(ALL) == pytest.approx(2 / 4)
    assert in_scope_accuracy(ALL) == pytest.approx(1 / 2)


def test_out_of_scope_precision_and_recall() -> None:
    assert out_of_scope_recall(ALL) == pytest.approx(1 / 2)
    assert out_of_scope_precision(ALL) == pytest.approx(1.0)


def test_confident_and_wrong_counts_only_automatic_wrong_picks() -> None:
    assert confident_and_wrong(ALL) == pytest.approx(1 / 4)


def test_vague_lines_count_as_handled_when_clarified_or_declined() -> None:
    assert vague_handled(ALL) == pytest.approx(1 / 2)


def test_a_line_with_two_labels_is_right_when_either_is_picked() -> None:
    both = Scored(make("g", "x", labels=["no_internet", "screen_too_dim"]), {"screen_too_dim": 1.0})

    assert accuracy([both]) == 1.0
    assert macro_f1([both]) == 1.0


def test_perfectly_calibrated_confidence_has_zero_ece() -> None:
    lines = [Scored(make(f"r{n}", "x"), {"no_internet": 1.0}) for n in range(5)]

    assert expected_calibration_error(lines) == pytest.approx(0.0)
    assert expected_calibration_error([WRONG_SURE]) == pytest.approx(1.0)


def test_bootstrap_brackets_the_estimate_and_repeats() -> None:
    lines = [RIGHT] * 30 + [WRONG_SURE] * 10

    low, high = bootstrap(lines, accuracy)

    assert low <= accuracy(lines) <= high
    assert bootstrap(lines, accuracy) == (low, high)


def test_bootstrap_keeps_the_intervals_reported_before_m4() -> None:
    assert bootstrap([RIGHT] * 30 + [WRONG_SURE] * 10, accuracy) == (0.625, 0.875)


def test_bootstrap_has_no_interval_when_no_line_is_of_the_kind() -> None:
    low, high = bootstrap([RIGHT] * 5, out_of_scope_recall)

    assert low != low and high != high


def _decider(right: int, wrong_confidence: float, n: int = 200) -> list[Scored]:
    """Right on the first `right` lines, wrong on the rest with the given confidence."""
    return [
        Scored(make(f"r{i}", "x"), {"no_internet": 1.0})
        if i < right
        else Scored(make(f"r{i}", "x"), {"screen_too_dim": wrong_confidence})
        for i in range(n)
    ]


def test_a_decider_paired_with_itself_differs_by_exactly_zero() -> None:
    lines = _decider(right=120, wrong_confidence=1.0)

    assert paired_bootstrap(lines, lines, accuracy) == (0.0, 0.0)


def test_pairing_gives_a_tighter_interval_than_two_separate_ones() -> None:
    base, challenger = _decider(right=100, wrong_confidence=1.0), _decider(110, 1.0)

    low, high = paired_bootstrap(base, challenger, accuracy)
    base_low, base_high = bootstrap(base, accuracy)

    assert 0 < low <= accuracy(challenger) - accuracy(base) <= high
    # The two rungs disagree on only 10 lines, so the difference barely moves between resamples.
    assert high - low < (base_high - base_low) / 2
    assert paired_bootstrap(base, challenger, accuracy) == (low, high)


def test_pairing_refuses_lines_in_a_different_order() -> None:
    lines = _decider(right=100, wrong_confidence=1.0)

    with pytest.raises(ValueError, match="same lines"):
        paired_bootstrap(lines, lines[::-1], accuracy)


def test_a_rung_beats_the_one_below_only_if_it_is_not_less_safe() -> None:
    careful_base = _decider(right=100, wrong_confidence=0.6)

    assert beats(_decider(100, 1.0), _decider(130, 1.0))
    assert not beats(careful_base, _decider(130, 1.0))
    assert not beats(careful_base, careful_base)


def test_changed_lists_mistakes_fixed_and_introduced() -> None:
    base, challenger = _decider(right=100, wrong_confidence=1.0), _decider(110, 1.0)
    swapped = challenger[:5] + base[5:]  # wrong where base is right on the first five lines
    swapped[:5] = [Scored(s.record, {"screen_too_dim": 0.9}) for s in swapped[:5]]

    fixed, introduced = changed(base, challenger)
    assert [(g, s, len(lines)) for g, s, lines in fixed] == [("no_internet", "screen_too_dim", 10)]
    assert introduced == []

    _, introduced = changed(base, swapped)
    assert [(g, s, len(lines)) for g, s, lines in introduced] == [
        ("no_internet", "screen_too_dim", 5)
    ]


def test_a_close_runner_up_is_clarified_under_a_margin() -> None:
    split = {"phone_not_ringing": 0.55, "notifications_missing": 0.4, "out_of_scope": 0.05}
    line = make("f", "no sound", "phone_not_ringing")
    margin = GateLines(automatic_at=0.8, clarify_below=0.5, clarify_margin=0.2)

    assert Scored(line, split).outcome == "confirm"
    assert Scored(line, split, margin).outcome == "clarify"
    assert Scored(line, {"phone_not_ringing": 0.9, "out_of_scope": 0.1}, margin).outcome == (
        "automatic"
    )


def test_out_of_scope_is_never_the_runner_up() -> None:
    line = make("g", "no net")
    margin = GateLines(automatic_at=0.8, clarify_below=0.5, clarify_margin=0.2)

    assert Scored(line, {"no_internet": 0.55, "out_of_scope": 0.45}, margin).outcome == "confirm"


def test_the_catalogs_gate_loads_with_its_lines_in_order() -> None:
    gate = load_gate()

    assert 0 < gate.clarify_below <= gate.automatic_at <= 1
    assert gate.clarify_margin >= 0
    assert GateLines(automatic_at=0.8, clarify_below=0.5, clarify_margin=0.0) == M2_GATE


def test_brier_is_zero_when_sure_and_right_and_counts_a_decline_as_missing() -> None:
    assert brier_score([RIGHT]) == 0
    assert brier_score([WRONG_SURE]) == 2
    assert brier_score([DECLINED_OOS]) == 1
    assert brier_score([UNSURE]) == pytest.approx(0.6**2 + 0.6**2)


def test_strata_keep_each_group_s_count_in_every_resample() -> None:
    # One person always right, one always wrong: resampled within each, accuracy can't move.
    items = [Scored(make(f"r{n}", "no net"), {"no_internet": 1.0}) for n in range(5)]
    items += [Scored(make(f"w{n}", "no net"), {"colours_wrong": 1.0}) for n in range(5)]
    strata = ["P01"] * 5 + ["P02"] * 5

    assert bootstrap(items, accuracy, strata=strata) == (0.5, 0.5)
    low, high = bootstrap(items, accuracy)
    assert low < 0.5 < high


def test_strata_need_one_label_per_line() -> None:
    with pytest.raises(ValueError, match="one stratum per line"):
        bootstrap(ALL, accuracy, strata=["P01"])


def test_calibration_bins_group_lines_by_confidence() -> None:
    gate = GateLines(automatic_at=0.75, clarify_below=0.7, clarify_margin=0.0)
    items = [
        Scored(make("a", "no net"), {"no_internet": 0.95}, gate),
        Scored(make("b", "no net"), {"phone_not_ringing": 0.91}, gate),
        Scored(make("c", "no net"), {"no_internet": 0.55}, gate),
    ]

    found = calibration_bins(items)

    assert [(b.low, b.count, b.accuracy) for b in found] == [(0.5, 1, 1.0), (0.9, 2, 0.5)]
    assert expected_calibration_error(items) == pytest.approx((0.45 + 2 * 0.43) / 3)
