from pathlib import Path

import pytest
from records import make

from unstuk_ml.evaluate import GateLines, Scored
from unstuk_ml.writeup_scores import Published, load, mismatches, save

GATE = GateLines(automatic_at=0.75, clarify_below=0.7, clarify_margin=0.0)


def items() -> list[Scored]:
    right = [
        Scored(make(f"r{n}", "no net"), {"no_internet": 0.9, "out_of_scope": 0.1}, GATE)
        for n in range(9)
    ]
    wrong = Scored(make("w", "no ring"), {"phone_not_ringing": 0.9, "out_of_scope": 0.1}, GATE)
    return [*right, wrong]


def test_numbers_that_print_as_published_match() -> None:
    assert mismatches(items(), Published(0.9, 0.1, 0.0)) == []


def test_a_number_off_by_a_tenth_of_a_point_is_named() -> None:
    wrong = mismatches(items(), Published(0.901, 0.1, 0.0))

    assert wrong == ["in-scope accuracy 90.0%, published 90.1%"]


def test_scores_come_back_from_the_cache_as_they_went_in(tmp_path: Path) -> None:
    path = tmp_path / "decider.json"
    save(items(), path)

    assert load(path, [s.record for s in items()]) == items()


def test_a_cache_made_on_other_lines_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "decider.json"
    save(items(), path)

    with pytest.raises(ValueError, match="other lines"):
        load(path, [make("new", "no net")])


def test_one_decider_behind_two_gates_is_refused(tmp_path: Path) -> None:
    other = Scored(make("x", "no net"), {"no_internet": 0.9}, GateLines(0.8, 0.5, 0.0))

    with pytest.raises(ValueError, match="one gate"):
        save([*items(), other], tmp_path / "decider.json")
