from tiny_model import tiny_model

from unstuk_ml.fine_tuning import (
    HEAD_LEARNING_RATE,
    chunks,
    learning_rate_factor,
    parameter_groups,
    shuffled,
)


def test_the_heads_learn_at_their_own_rate() -> None:
    model = tiny_model("attention")

    backbone, heads = parameter_groups(model, model.backbone, 5e-5)

    assert (backbone["lr"], heads["lr"]) == (5e-5, HEAD_LEARNING_RATE)
    ids = {id(p) for p in heads["params"]}
    assert {id(model.log_scale), id(model.noul.weight)} <= ids
    assert not ids & {id(p) for p in model.backbone.parameters()}


def test_the_rate_warms_up_over_a_tenth_then_decays_to_zero() -> None:
    factors = [learning_rate_factor(step, steps=100) for step in (0, 5, 10, 55, 100)]

    assert factors == [0.0, 0.5, 1.0, 0.5, 0.0]


def test_an_epochs_order_depends_on_the_seed_and_epoch_only() -> None:
    items = list(range(20))

    assert shuffled(items, 7, 0) == shuffled(items, 7, 0) != shuffled(items, 7, 1)
    assert sorted(shuffled(items, 7, 0)) == items


def test_chunks_keep_every_item_in_order() -> None:
    assert chunks([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
