import pytest
from records import make

from unstuk_ml.evaluate import (
    Scored,
    accuracy,
    bootstrap,
    confident_and_wrong,
    expected_calibration_error,
    in_scope_accuracy,
    macro_f1,
    out_of_scope_precision,
    out_of_scope_recall,
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
