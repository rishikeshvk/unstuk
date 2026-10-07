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
NoulInput = Literal["complaint", "options", "fit"]
"""What decides out of scope: the complaint alone, the complaint against the options, or only how
well the options fit (round 7), which can't tell a familiar complaint from an unfamiliar one."""

# bge's cosines differ by hundredths, so a softmax over them needs a large scale to be decisive.
INITIAL_SCALE = 20.0


@dataclass(frozen=True)
class Decision:
    choice_logits: torch.Tensor
    """[examples, options], -inf where an example has no option."""
    out_of_scope_logit: torch.Tensor
    """[examples]"""


class DecisionModel(nn.Module):
    def __init__(self, backbone: BertModel, head: Head, noul: NoulInput = "complaint") -> None:
        super().__init__()
        width = backbone.config.hidden_size
        self.backbone = backbone
        self.noul_input = noul
        self.log_scale = nn.Parameter(torch.tensor(math.log(INITIAL_SCALE)))
        self.correction = (
            AttentionCorrection(width, backbone.config.num_attention_heads)
            if head == "attention"
            else None
        )
        # Against the options: the complaint, the Choice-weighted options, their product, the best.
        self.noul = nn.Linear({"complaint": width, "options": 3 * width + 1, "fit": 3}[noul], 1)

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
        choice = scores.masked_fill(~batch.option_mask, -math.inf)
        return Decision(
            choice_logits=choice,
            out_of_scope_logit=self.noul(self._noul_features(query, options, choice)).squeeze(-1),
        )

    def _noul_features(
        self, query: torch.Tensor, options: torch.Tensor, choice: torch.Tensor
    ) -> torch.Tensor:
        if self.noul_input == "complaint":
            return query
        if self.noul_input == "fit":
            return fit_features(choice)
        weighted = (choice.softmax(dim=1)[..., None] * options).sum(dim=1)
        best = choice.max(dim=1).values[:, None]
        return torch.cat([query, weighted, query * weighted, best], dim=-1)

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


def fit_features(choice: torch.Tensor) -> torch.Tensor:
    """How well the offered options fit: the best logit, its margin over the second, and the
    entropy as a share of its maximum, so 4 options and 12 read on the same scale."""
    best, second = choice.topk(2, dim=1).values.unbind(dim=1)
    offered = torch.isfinite(choice).sum(dim=1).float()
    entropy = torch.special.entr(choice.softmax(dim=1)).sum(dim=1) / offered.log()
    return torch.stack([best, best - second, entropy], dim=1)
