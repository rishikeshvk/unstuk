import math

import pytest
import torch

from unstuk_ml.decision_loss import choice_brier, choice_loss, noul_brier, noul_loss

INF = math.inf
ONE = torch.tensor([False])
TWO = torch.tensor([False, False])


def test_one_correct_option_is_cross_entropy() -> None:
    loss = choice_loss(torch.tensor([[1.0, 2.0, 0.0]]), torch.tensor([[True, False, False]]), ONE)

    expected = math.log(math.exp(1) + math.exp(2) + math.exp(0)) - 1
    assert loss.item() == pytest.approx(expected, rel=1e-5)


def test_two_correct_options_share_the_probability() -> None:
    loss = choice_loss(torch.tensor([[1.0, 2.0, 0.0]]), torch.tensor([[True, True, False]]), ONE)

    expected = -math.log((math.exp(1) + math.exp(2)) / (math.exp(1) + math.exp(2) + 1))
    assert loss.item() == pytest.approx(expected, rel=1e-5)


def test_padded_options_and_rows_without_an_answer_add_nothing() -> None:
    logits = torch.tensor([[1.0, 2.0, -INF], [3.0, 0.0, 1.0]])
    answers = torch.tensor([[True, False, False], [False, False, False]])

    alone = choice_loss(logits[:1, :2], answers[:1, :2], ONE)

    assert choice_loss(logits, answers, TWO).item() == pytest.approx(alone.item(), rel=1e-5)


def test_rows_without_a_noul_target_add_nothing() -> None:
    logits = torch.tensor([2.0, -5.0])
    targets = torch.tensor([1.0, 0.0])

    loss = noul_loss(logits, targets, torch.tensor([True, False]))

    assert loss.item() == pytest.approx(math.log(1 + math.exp(-2)), rel=1e-5)


def test_a_batch_that_asks_nothing_costs_nothing() -> None:
    assert choice_loss(torch.zeros(2, 3), torch.zeros(2, 3, dtype=torch.bool), TWO).item() == 0
    assert choice_brier(torch.zeros(2, 3), torch.zeros(2, 3, dtype=torch.bool), TWO).item() == 0
    assert noul_loss(torch.zeros(2), torch.zeros(2), torch.zeros(2, dtype=torch.bool)).item() == 0
    assert noul_brier(torch.zeros(2), torch.zeros(2), torch.zeros(2, dtype=torch.bool)).item() == 0


def test_gradients_stay_finite_beside_padded_options() -> None:
    logits = torch.tensor([[1.0, 2.0, 0.5], [3.0, 0.0, 1.0]], requires_grad=True)
    padded = logits.masked_fill(torch.tensor([[False, False, True], [False] * 3]), -INF)
    answers = torch.tensor([[True, False, False], [False, False, False]])

    spread = torch.tensor([True, False])
    loss = choice_loss(padded, answers, spread) + choice_brier(padded, answers, spread)

    (grad,) = torch.autograd.grad(loss, logits)

    assert torch.isfinite(grad).all()
    assert grad[1].abs().sum() == 0


def test_a_spread_row_is_cross_entropy_against_an_even_split() -> None:
    logits = torch.tensor([[1.0, 2.0, 0.0]])

    loss = choice_loss(logits, torch.tensor([[True, True, False]]), torch.tensor([True]))

    log_p = logits.log_softmax(dim=1)[0]
    assert loss.item() == pytest.approx(-(log_p[0] + log_p[1]).item() / 2, rel=1e-5)


def test_a_spread_row_costs_least_at_the_even_split() -> None:
    answers, spread = torch.tensor([[True, True, False]]), torch.tensor([True])
    even = torch.tensor([[5.0, 5.0, -5.0]])
    one_sided = torch.tensor([[8.0, 2.0, -5.0]])

    assert choice_loss(even, answers, spread) < choice_loss(one_sided, answers, spread)
    assert choice_brier(even, answers, spread) < choice_brier(one_sided, answers, spread)


def test_brier_is_the_squared_distance_from_the_answer() -> None:
    logits = torch.tensor([[0.0, 0.0, 0.0, 0.0]])

    loss = choice_brier(logits, torch.tensor([[True, False, False, False]]), ONE)

    assert loss.item() == pytest.approx(0.75**2 + 3 * 0.25**2, rel=1e-5)


def test_brier_vanishes_at_a_sure_right_answer() -> None:
    logits = torch.tensor([[30.0, -30.0, -INF]])

    assert choice_brier(logits, torch.tensor([[True, False, False]]), ONE).item() < 1e-12
    assert noul_brier(torch.tensor([30.0]), torch.tensor([1.0]), torch.tensor([True])) < 1e-12


def test_noul_brier_is_the_squared_error_of_the_probability() -> None:
    loss = noul_brier(
        torch.tensor([0.0, 9.0]), torch.tensor([1.0, 0.0]), torch.tensor([True, False])
    )

    assert loss.item() == pytest.approx(0.25, rel=1e-5)
