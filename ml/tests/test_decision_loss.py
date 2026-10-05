import math

import pytest
import torch

from unstuk_ml.decision_loss import choice_loss, noul_loss

INF = math.inf


def test_one_correct_option_is_cross_entropy() -> None:
    loss = choice_loss(torch.tensor([[1.0, 2.0, 0.0]]), torch.tensor([[True, False, False]]))

    expected = math.log(math.exp(1) + math.exp(2) + math.exp(0)) - 1
    assert loss.item() == pytest.approx(expected, rel=1e-5)


def test_two_correct_options_share_the_probability() -> None:
    loss = choice_loss(torch.tensor([[1.0, 2.0, 0.0]]), torch.tensor([[True, True, False]]))

    expected = -math.log((math.exp(1) + math.exp(2)) / (math.exp(1) + math.exp(2) + 1))
    assert loss.item() == pytest.approx(expected, rel=1e-5)


def test_padded_options_and_rows_without_an_answer_add_nothing() -> None:
    logits = torch.tensor([[1.0, 2.0, -INF], [3.0, 0.0, 1.0]])
    answers = torch.tensor([[True, False, False], [False, False, False]])

    alone = choice_loss(logits[:1, :2], answers[:1, :2])

    assert choice_loss(logits, answers).item() == pytest.approx(alone.item(), rel=1e-5)


def test_rows_without_a_noul_target_add_nothing() -> None:
    logits = torch.tensor([2.0, -5.0])
    targets = torch.tensor([1.0, 0.0])

    loss = noul_loss(logits, targets, torch.tensor([True, False]))

    assert loss.item() == pytest.approx(math.log(1 + math.exp(-2)), rel=1e-5)


def test_a_batch_that_asks_nothing_costs_nothing() -> None:
    assert choice_loss(torch.zeros(2, 3), torch.zeros(2, 3, dtype=torch.bool)).item() == 0
    assert noul_loss(torch.zeros(2), torch.zeros(2), torch.zeros(2, dtype=torch.bool)).item() == 0


def test_gradients_stay_finite_beside_padded_options() -> None:
    logits = torch.tensor([[1.0, 2.0, 0.5], [3.0, 0.0, 1.0]], requires_grad=True)
    padded = logits.masked_fill(torch.tensor([[False, False, True], [False] * 3]), -INF)
    answers = torch.tensor([[True, False, False], [False, False, False]])

    (grad,) = torch.autograd.grad(choice_loss(padded, answers), logits)

    assert torch.isfinite(grad).all()
    assert grad[1].abs().sum() == 0
