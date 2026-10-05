from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from records import make
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer

from unstuk_ml.baseline_report import Decider
from unstuk_ml.record import Record
from unstuk_ml.rung import ClassWeight, Rung, Trial, best, examples, load, score, train, tune

# Features looked up from a table, so the protocol is tested without any real featuriser.
POINTS = {
    "net": (1.0, 0.0),
    "web": (0.9, 0.1),
    "dim": (0.0, 1.0),
    "dark": (0.1, 0.9),
    "rain": (-1.0, -1.0),
    "snow": (-0.9, -1.0),
}


def _features(texts: list[str]) -> NDArray[np.float64]:
    return np.array([POINTS[t] for t in texts])


def _build(c: float, class_weight: ClassWeight) -> Pipeline:
    return make_pipeline(
        FunctionTransformer(_features), LogisticRegression(C=c, class_weight=class_weight)
    )


def _rung(tmp_path: Path, extensions: tuple[float, ...] = ()) -> Rung:
    decider = Decider("Fake", "fake", "A lookup", "none", tmp_path / "fake.md")
    grid: list[tuple[float, ClassWeight]] = [(0.1, None), (1.0, None)]
    return Rung(decider, grid, _build, tmp_path / "fake.json", extensions)


TRAIN: list[Record] = [
    make("a", "net", "no_internet"),
    make("b", "dim", "screen_too_dim"),
    make("e", "rain", "out_of_scope"),
]
DEV: list[Record] = [
    make("c", "web", "no_internet"),
    make("d", "dark", "screen_too_dim"),
    make("f", "snow", "out_of_scope"),
]


def _trial(c: float, macro_f1: float, log_loss: float) -> Trial:
    return Trial(
        c=c,
        class_weight=None,
        dev_macro_f1=macro_f1,
        dev_log_loss=log_loss,
        dev_in_scope_accuracy=0.5,
    )


def test_a_line_with_two_problems_teaches_both() -> None:
    both = make("b", "no net and dark screen", labels=["no_internet", "screen_too_dim"])

    assert examples([both]) == (["no net and dark screen"] * 2, ["no_internet", "screen_too_dim"])


def test_the_best_trial_is_by_macro_f1_then_log_loss_then_grid_order() -> None:
    first, sharper, same = _trial(1, 0.8, 0.5), _trial(1, 0.8, 0.3), _trial(1, 0.8, 0.3)

    assert best([_trial(1, 0.7, 0.1), first]) is first
    assert best([first, sharper, same]) is sharper


def test_tuning_without_extensions_stays_on_the_grid(tmp_path: Path) -> None:
    settings = tune(_rung(tmp_path), TRAIN, DEV)

    # Both points get dev right; the less regularised one is surer, so its log-loss is lower.
    assert settings.c == 1.0
    assert [t.c for t in settings.grid] == [0.1, 1.0]
    assert settings.temperature > 0


def test_a_winner_at_the_grids_top_extends_it_until_it_is_inside(tmp_path: Path) -> None:
    settings = tune(_rung(tmp_path, extensions=(10.0, 100.0, 1000.0)), TRAIN, DEV)

    # Separable data: a larger C is always surer, so the top wins until the extensions run out.
    assert [t.c for t in settings.grid] == [0.1, 1.0, 10.0, 100.0, 1000.0]
    assert settings.c == 1000.0


def test_loading_refuses_before_tuning_and_then_retrains_the_same_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _rung(tmp_path)
    monkeypatch.setattr("unstuk_ml.rung.read_clean", lambda split: TRAIN)
    with pytest.raises(FileNotFoundError):
        load(fake)

    settings = tune(fake, TRAIN, DEV)
    fake.settings.write_text(settings.model_dump_json(), encoding="utf-8")
    _, model = load(fake)

    expected = train(fake, TRAIN, settings.c, settings.class_weight)
    assert score(model, 1.0, DEV) == score(expected, 1.0, DEV)
