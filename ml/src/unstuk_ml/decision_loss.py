"""The decision loss (M5 spec section 2): cross-entropy for Choice, binary cross-entropy for Noul.

Each part averages only over the examples that ask its question: out-of-scope lines have no
correct option, and node questions don't ask whether they are out of scope.
"""

import torch
from torch import nn

from unstuk_ml.decision_batch import DecisionBatch
from unstuk_ml.decision_model import Decision


def decision_loss(decision: Decision, batch: DecisionBatch) -> torch.Tensor:
    return choice_loss(decision.choice_logits, batch.answers) + noul_loss(
        decision.out_of_scope_logit, batch.out_of_scope, batch.asks_out_of_scope
    )


def choice_loss(logits: torch.Tensor, answers: torch.Tensor) -> torch.Tensor:
    """Minus the log of the summed probability of the correct options."""
    asked = answers.any(dim=1)
    if not asked.any():
        return logits.new_zeros(())
    logits, answers = logits[asked], answers[asked]
    gold = logits.masked_fill(~answers, -torch.inf).logsumexp(dim=1)
    return (logits.logsumexp(dim=1) - gold).mean()


def noul_loss(logits: torch.Tensor, targets: torch.Tensor, asked: torch.Tensor) -> torch.Tensor:
    if not asked.any():
        return logits.new_zeros(())
    return nn.functional.binary_cross_entropy_with_logits(logits[asked], targets[asked])
