from collections import Counter

import pytest

from unstuk_ml.grid import AXES, check_cell, plan_batches


def test_the_same_seed_gives_the_same_plan() -> None:
    assert plan_batches(40, seed=6) == plan_batches(40, seed=6)
    assert plan_batches(40, seed=6) != plan_batches(40, seed=7)


@pytest.mark.parametrize("axis", list(AXES))
def test_every_value_appears_equally_often_give_or_take_one(axis: str) -> None:
    counts = Counter(cell[axis] for cell in plan_batches(40, seed=6))

    assert set(counts) == set(AXES[axis])
    assert max(counts.values()) - min(counts.values()) <= 1


def test_rejects_cells_outside_the_grid() -> None:
    with pytest.raises(ValueError, match="unknown axis mood"):
        check_cell({"mood": "happy"})
    with pytest.raises(ValueError, match="unknown age value toddler"):
        check_cell({"age": "toddler"})
