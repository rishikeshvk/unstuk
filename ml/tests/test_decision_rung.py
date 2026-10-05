from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from records import make

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_rung import CONFIGS, GRID, pick, runs_of, zero_shot_line
from unstuk_ml.decision_training import DecisionRun, EpochResult, RunConfig
from unstuk_ml.folds import trained_intents

CATALOG = load_catalog()
INTENTS = trained_intents(CATALOG)


def epoch(f1: float, loss: float, fold: float | None) -> EpochResult:
    return EpochResult(
        epoch=0,
        train_loss=0.1,
        dev_macro_f1=f1,
        dev_log_loss=loss,
        dev_in_scope_accuracy=f1,
        seconds=1.0,
        node_dev_accuracy=0.9,
        fold_accuracy=fold,
    )


def results(scores: dict[str, tuple[float, float, float]]) -> dict[str, DecisionRun]:
    """Each config's dev macro-F1, log-loss and fold accuracy, as if every run had come back."""
    out = {}
    for config in CONFIGS:
        f1, loss, fold = scores.get(config.name, (0.5, 1.0, 0.5))
        for run in runs_of(config):
            out[run.name] = DecisionRun(
                config=run,
                epochs=[epoch(f1, loss, None if run.fold is None else fold)],
                chosen_epoch=0,
                checkpoint_sha256="0" * 64,
                commit="abc",
                device="cpu",
            )
    return out


def test_every_config_runs_on_all_the_data_and_each_fold() -> None:
    assert len(CONFIGS) == 13
    assert len(GRID) == 52
    assert [r.name for r in runs_of(CONFIGS[0])] == [
        "cosine-lr2e-05-state",
        "cosine-lr2e-05-state-fold0",
        "cosine-lr2e-05-state-fold1",
        "cosine-lr2e-05-state-fold2",
    ]
    assert all(c.state for c in CONFIGS)


def test_only_configs_at_or_above_the_line_compete_on_dev() -> None:
    best_on_dev, guarded = CONFIGS[0].name, CONFIGS[1].name
    runs = results({best_on_dev: (0.99, 0.1, 0.60), guarded: (0.95, 0.2, 0.80)})

    grid, best = pick(runs, line=0.75)

    assert best is not None
    assert best.run == guarded
    assert [row.qualifies for row in grid].count(True) == 1


def test_ties_on_dev_go_to_the_lower_log_loss() -> None:
    a, b = CONFIGS[2].name, CONFIGS[3].name
    runs = results({a: (0.95, 0.3, 0.9), b: (0.95, 0.2, 0.9)})

    _, best = pick(runs, line=0.8)

    assert best is not None
    assert best.run == b


def test_when_no_config_reaches_the_line_nothing_is_picked() -> None:
    grid, best = pick(results({}), line=0.9)

    assert best is None
    assert len(grid) == 13


def fake_embed(texts: Sequence[str]) -> NDArray[np.float32]:
    """One axis per intent: its option text and every line about it point the same way."""
    vectors = np.zeros((len(texts), len(INTENTS) + 1), dtype=np.float32)
    for n, text in enumerate(texts):
        axis = next(
            (k for k, i in enumerate(INTENTS) if CATALOG.intents[i] == text or text.endswith(i)),
            len(INTENTS),
        )
        vectors[n, axis] = 1
    return vectors


def test_the_zero_shot_line_scores_each_folds_unseen_intents() -> None:
    dev = [make(f"d{n}", f"a line about {i}", i) for n, i in enumerate(INTENTS * 2)]

    line = zero_shot_line(fake_embed, dev, CATALOG)

    assert line.fold_accuracies == [1.0, 1.0, 1.0]
    assert line.mean == 1.0


def test_a_fold_config_differs_from_its_full_run_only_by_the_fold() -> None:
    full, *rest = runs_of(RunConfig(head="attention", learning_rate=5e-5, typos=True, state=True))

    assert [r.model_copy(update={"fold": None}) for r in rest] == [full] * 3


def test_round_two_moves_the_backbone_less() -> None:
    assert [c.name for c in CONFIGS[8:]] == [
        "cosine-lr1e-05-typos-state",
        "attention-lr1e-05-typos-state",
        "cosine-lr5e-06-typos-state",
        "attention-lr5e-06-typos-state",
        "attention-lr2e-05-typos-state-frozen8",
    ]
