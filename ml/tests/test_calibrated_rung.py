import pytest

from unstuk_ml.calibrated_rung import GRID, WeightRow, pick


def row(weight: float, brier: float, log_loss: float, eligible: bool = True) -> WeightRow:
    return WeightRow(
        run=f"w{weight}",
        brier_weight=weight,
        epoch=4,
        dev_macro_f1=0.98,
        dev_log_loss=log_loss,
        dev_brier=brier,
        eligible=eligible,
    )


def test_picks_the_lowest_brier_among_eligible_weights_then_the_lower_log_loss() -> None:
    rows = [row(0, 0.05, 0.1), row(0.5, 0.04, 0.2, eligible=False), row(1, 0.05, 0.09)]

    assert pick(rows).brier_weight == 1


def test_refuses_when_no_weight_is_eligible() -> None:
    with pytest.raises(ValueError, match="macro-F1"):
        pick([row(0, 0.05, 0.1, eligible=False)])


def test_every_weight_trains_on_the_vague_slice_on_all_data_and_three_folds() -> None:
    assert len(GRID) == 12
    assert all(run.vague for run in GRID)
    assert sorted({run.fold for run in GRID}, key=str) == [0, 1, 2, None]
