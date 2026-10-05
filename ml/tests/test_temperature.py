import numpy as np

from unstuk_ml.temperature import fit_temperature, softmax


def test_softmax_rows_sum_to_one_and_temperature_keeps_the_top_pick() -> None:
    logits = np.array([[2.0, 1.0, -1.0], [0.0, 3.0, 2.5]])

    sharp, soft = softmax(logits, 0.5), softmax(logits, 4.0)

    assert np.allclose(sharp.sum(axis=1), 1.0)
    assert (sharp.argmax(axis=1) == soft.argmax(axis=1)).all()
    assert soft.max() < sharp.max()


def test_fitting_recovers_the_temperature_the_labels_were_drawn_with() -> None:
    rng = np.random.default_rng(19)
    logits = rng.normal(scale=4.0, size=(20_000, 5))
    truth = softmax(logits, 2.0)
    targets = np.array([rng.choice(5, p=row) for row in truth], dtype=np.int64)

    assert abs(fit_temperature(logits, targets) - 2.0) < 0.1


def test_narrow_bounds_reach_the_small_temperatures_cosines_need() -> None:
    rng = np.random.default_rng(19)
    cosines = rng.uniform(0.6, 0.8, size=(20_000, 5))
    truth = softmax(cosines, 0.02)
    targets = np.array([rng.choice(5, p=row) for row in truth], dtype=np.int64)

    assert abs(fit_temperature(cosines, targets, bounds=(0.001, 1.0)) - 0.02) < 0.002
