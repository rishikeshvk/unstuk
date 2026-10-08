"""The graph that ships (M7 spec section 1): the encoder and Noul, without the Choice head.

M6's model scores options by cosine, so an option's vector doesn't depend on the complaint. One
graph turns any text into a unit vector and a Noul logit; Choice is a scaled dot product of
vectors, done outside the graph, so the same weights encode complaints and options alike.
"""

from pathlib import Path

import torch
from torch import nn

from unstuk_ml.decision_model import DecisionModel

INPUTS = ("input_ids", "attention_mask", "token_type_ids")
OUTPUTS = ("vector", "noul_logit")
OPSET = 18


class DecisionGraph(nn.Module):
    def __init__(self, model: DecisionModel) -> None:
        super().__init__()
        if model.correction is not None or model.noul_input != "complaint":
            raise ValueError("only a cosine head with Noul on the complaint splits into one graph")
        self.backbone = model.backbone
        self.noul = model.noul

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor, token_type_ids: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        cls = self.backbone(
            input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids
        ).last_hidden_state[:, 0]
        # The same eps as torch's cosine_similarity, which the trained head used.
        vector = cls / cls.norm(dim=-1, keepdim=True).clamp_min(1e-8)
        return vector, self.noul(cls).squeeze(-1)


def scale(model: DecisionModel) -> float:
    """The learned factor on cosine, which turns it into a Choice logit."""
    return float(model.log_scale.detach().exp())


def export(model: DecisionModel, path: Path) -> None:
    """The float graph, with batch and sequence lengths left free."""
    graph = DecisionGraph(model).eval()
    example = tuple(torch.ones(2, 8, dtype=torch.long) for _ in INPUTS)
    batch, tokens = torch.export.Dim("batch"), torch.export.Dim("tokens")
    torch.onnx.export(
        graph,
        example,
        str(path),
        input_names=list(INPUTS),
        output_names=list(OUTPUTS),
        dynamic_shapes={name: {0: batch, 1: tokens} for name in INPUTS},
        opset_version=OPSET,
        dynamo=True,
        external_data=False,
    )
