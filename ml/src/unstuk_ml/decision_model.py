"""The decision model (M5 spec section 1): bge-small with a Choice head and a Noul head.

Choice scores whatever options it is given against the complaint; Noul says whether the complaint
is out of scope. The attention head adds a learned correction to the cosine score, starting at
zero, so before training both heads score exactly as the zero-shot rung does.
"""

import math
from dataclasses import dataclass
from typing import Literal

import torch
from torch import nn
from transformers import BertModel

from unstuk_ml.decision_batch import DecisionBatch, Encoded

Head = Literal["cosine", "attention"]
# bge's cosines differ by hundredths, so a softmax over them needs a large scale to be decisive.
INITIAL_SCALE = 20.0


@dataclass(frozen=True)
class Decision:
    choice_logits: torch.Tensor
    """[examples, options], -inf where an example has no option."""
    out_of_scope_logit: torch.Tensor
    """[examples]"""


class DecisionModel(nn.Module):
    def __init__(self, backbone: BertModel, head: Head) -> None:
        super().__init__()
        width = backbone.config.hidden_size
        self.backbone = backbone
        self.log_scale = nn.Parameter(torch.tensor(math.log(INITIAL_SCALE)))
        self.correction = (
            AttentionCorrection(width, backbone.config.num_attention_heads)
            if head == "attention"
            else None
        )
        self.noul = nn.Linear(width, 1)

    def forward(self, batch: DecisionBatch) -> Decision:
        tokens = self._hidden(batch.queries)
        query = tokens[:, 0]
        options = self._hidden(batch.options)[:, 0][batch.option_index]
        scores = self.log_scale.exp() * nn.functional.cosine_similarity(
            query[:, None], options, dim=-1
        )
        if self.correction is not None:
            scores = scores + self.correction(
                options, tokens, batch.queries.attention_mask.bool(), batch.option_mask
            )
        return Decision(
            choice_logits=scores.masked_fill(~batch.option_mask, -math.inf),
            out_of_scope_logit=self.noul(query).squeeze(-1),
        )

    def _hidden(self, encoded: Encoded) -> torch.Tensor:
        hidden: torch.Tensor = self.backbone(
            input_ids=encoded.input_ids,
            attention_mask=encoded.attention_mask,
            token_type_ids=encoded.token_type_ids,
        ).last_hidden_state
        return hidden


class AttentionCorrection(nn.Module):
    """Each option reads the complaint's tokens, then the example's other options; one number out.

    No positional encoding over options, so their order can't change a score.
    """

    def __init__(self, width: int, heads: int) -> None:
        super().__init__()
        self.cross_norm = nn.LayerNorm(width)
        self.cross = nn.MultiheadAttention(width, heads, batch_first=True)
        self.set_norm = nn.LayerNorm(width)
        self.set = nn.MultiheadAttention(width, heads, batch_first=True)
        self.out_norm = nn.LayerNorm(width)
        self.score = nn.Linear(width, 1)
        nn.init.zeros_(self.score.weight)
        nn.init.zeros_(self.score.bias)

    def forward(
        self,
        options: torch.Tensor,
        tokens: torch.Tensor,
        token_mask: torch.Tensor,
        option_mask: torch.Tensor,
    ) -> torch.Tensor:
        x = self.cross_norm(options)
        options = options + self.cross(x, tokens, tokens, key_padding_mask=~token_mask)[0]
        x = self.set_norm(options)
        options = options + self.set(x, x, x, key_padding_mask=~option_mask)[0]
        correction: torch.Tensor = self.score(self.out_norm(options)).squeeze(-1)
        return correction
