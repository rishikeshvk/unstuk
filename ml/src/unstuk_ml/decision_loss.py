"""The decision loss: cross-entropy for Choice, binary cross-entropy for Noul (M5 spec section 2),
each plus `brier_weight` times its Brier score (M6 spec section 2).

Each part averages only over the examples that ask its question: out-of-scope lines have no
correct option, and node questions don't ask whether they are out of scope.
"""

import torch
from torch import nn

from unstuk_ml.decision_batch import DecisionBatch
from unstuk_ml.decision_model import Decision


def decision_loss(decision: Decision, batch: DecisionBatch, brier_weight: float) -> torch.Tensor:
    choice, noul = decision.choice_logits, decision.out_of_scope_logit
    loss = choice_loss(choice, batch.answers, batch.spread) + noul_loss(
        noul, batch.out_of_scope, batch.asks_out_of_scope
    )
    if brier_weight:
        loss = loss + brier_weight * (
            choice_brier(choice, batch.answers, batch.spread)
            + noul_brier(noul, batch.out_of_scope, batch.asks_out_of_scope)
        )
    return loss


def choice_loss(logits: torch.Tensor, answers: torch.Tensor, spread: torch.Tensor) -> torch.Tensor:
    """Minus the log of the correct options' summed probability; for a spread row, cross-entropy
    against an even split over them, so putting everything on one reading costs more."""
    asked = answers.any(dim=1)
    if not asked.any():
        return logits.new_zeros(())
    logits, answers, spread = logits[asked], answers[asked], spread[asked]
    log_total = logits.logsumexp(dim=1)
    summed = log_total - logits.masked_fill(~answers, -torch.inf).logsumexp(dim=1)
    log_p = logits.masked_fill(~answers, 0) - log_total.unsqueeze(1)
    even = -(log_p * answers).sum(dim=1) / answers.sum(dim=1)
    return torch.where(spread, even, summed).mean()


def choice_brier(logits: torch.Tensor, answers: torch.Tensor, spread: torch.Tensor) -> torch.Tensor:
    """The squared distance from the target distribution. Without spread, the correct options count
    as one outcome, as in `choice_loss`, so a two-problem line may favour either."""
    asked = answers.any(dim=1)
    if not asked.any():
        return logits.new_zeros(())
    p = logits[asked].softmax(dim=1)
    answers, spread = answers[asked], spread[asked]
    wrong = (p * ~answers).pow(2).sum(dim=1)
    summed = (1 - (p * answers).sum(dim=1)).pow(2) + wrong
    target = answers / answers.sum(dim=1, keepdim=True)
    even = ((p - target) * answers).pow(2).sum(dim=1) + wrong
    return torch.where(spread, even, summed).mean()


def noul_loss(logits: torch.Tensor, targets: torch.Tensor, asked: torch.Tensor) -> torch.Tensor:
    if not asked.any():
        return logits.new_zeros(())
    return nn.functional.binary_cross_entropy_with_logits(logits[asked], targets[asked])


def noul_brier(logits: torch.Tensor, targets: torch.Tensor, asked: torch.Tensor) -> torch.Tensor:
    if not asked.any():
        return logits.new_zeros(())
    return (logits[asked].sigmoid() - targets[asked]).pow(2).mean()
