from pathlib import Path

import pytest
import torch
from records import make
from tiny_model import tiny_backbone

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.fine_tuning import EpochCheck
from unstuk_ml.fixed_head import FixedHeadModel, fixed_labels
from unstuk_ml.fixed_head_rung import (
    GRID,
    FixedHeadConfig,
    FixedHeadRun,
    load_checkpoint,
    pick,
    train,
)


def epoch_check(epoch: int, f1: float, loss: float) -> EpochCheck:
    return EpochCheck(
        epoch=epoch,
        train_loss=0.1,
        dev_macro_f1=f1,
        dev_log_loss=loss,
        dev_in_scope_accuracy=f1,
        seconds=1.0,
    )


def result(config: FixedHeadConfig, chosen: int, checks: list[EpochCheck]) -> FixedHeadRun:
    return FixedHeadRun(
        config=config,
        epochs=checks,
        chosen_epoch=chosen,
        checkpoint_sha256="0" * 64,
        commit="abc",
        device="cpu",
    )


def test_the_grid_is_two_rates_with_and_without_typos() -> None:
    assert [c.name for c in GRID] == [
        "fixed-head-lr2e-05",
        "fixed-head-lr2e-05-typos",
        "fixed-head-lr5e-05",
        "fixed-head-lr5e-05-typos",
    ]


def test_a_configs_arguments_say_what_it_trains() -> None:
    config = FixedHeadConfig(learning_rate=5e-5, typos=True, epochs=3, limit=64)

    assert config.arguments() == [
        "--learning-rate",
        "5e-05",
        "--epochs",
        "3",
        "--typos",
        "--limit",
        "64",
    ]


def test_each_runs_kept_epoch_competes_and_ties_go_to_the_lower_log_loss() -> None:
    results = [
        result(GRID[0], 1, [epoch_check(0, 0.90, 0.3), epoch_check(1, 0.95, 0.2)]),
        result(GRID[1], 0, [epoch_check(0, 0.95, 0.1)]),
        result(GRID[2], 0, [epoch_check(0, 0.93, 0.1)]),
    ]

    grid, best = pick(results)

    assert [(g.run, g.epoch) for g in grid] == [
        ("fixed-head-lr2e-05", 1),
        ("fixed-head-lr2e-05-typos", 0),
        ("fixed-head-lr5e-05", 0),
    ]
    assert best.run == "fixed-head-lr2e-05-typos"


def test_a_checkpoint_with_other_bytes_is_refused(tmp_path: Path) -> None:
    (tmp_path / "model.pt").write_bytes(b"not the weights")

    with pytest.raises(ValueError, match="not the checkpoint"):
        load_checkpoint(tmp_path, "0" * 64)


@pytest.mark.skipif(not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub")
def test_training_checks_dev_each_epoch() -> None:
    labels = fixed_labels(load_catalog())
    model = FixedHeadModel(tiny_backbone(), labels)
    records = [
        make(f"t{n}", f"complaint {n} about {label}", label) for n, label in enumerate(labels)
    ]
    config = FixedHeadConfig(learning_rate=5e-5, typos=True, epochs=2, batch_size=4)

    checks, weights = train(
        config,
        records,
        records,
        model,
        decision_tokenizer(download()[1]),
        torch.device("cpu"),
    )

    assert [c.epoch for c in checks] == [0, 1]
    assert set(weights) == set(model.state_dict())
