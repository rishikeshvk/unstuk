import pytest
import torch
from tiny_model import tiny_model

from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.wise_ft import blend


def fine_tuned() -> tuple[DecisionModel, dict[str, torch.Tensor]]:
    """A tiny model whose backbone has moved by +1 everywhere from the returned frozen weights."""
    model = tiny_model("attention")
    frozen = {k: v.clone() for k, v in model.backbone.state_dict().items()}
    with torch.no_grad():
        for parameter in model.backbone.parameters():
            parameter.add_(1.0)
    return model, frozen


def backbone_weight(model: DecisionModel) -> torch.Tensor:
    return model.backbone.embeddings.word_embeddings.weight


def test_alpha_one_keeps_the_fine_tuned_weights() -> None:
    model, frozen = fine_tuned()
    before = backbone_weight(model).clone()

    blend(model.backbone, frozen, 1.0)

    assert torch.equal(backbone_weight(model), before)


def test_alpha_zero_restores_the_frozen_backbone_and_keeps_the_heads() -> None:
    model, frozen = fine_tuned()
    heads = {k: v.clone() for k, v in model.state_dict().items() if not k.startswith("backbone.")}

    blend(model.backbone, frozen, 0.0)

    assert torch.equal(backbone_weight(model), frozen["embeddings.word_embeddings.weight"])
    for name, tensor in heads.items():
        assert torch.equal(model.state_dict()[name], tensor)


def test_alpha_half_is_the_midpoint() -> None:
    model, frozen = fine_tuned()

    blend(model.backbone, frozen, 0.5)

    expected = frozen["embeddings.word_embeddings.weight"] + 0.5
    assert torch.allclose(backbone_weight(model), expected)


def test_weights_from_another_model_are_refused() -> None:
    model, frozen = fine_tuned()
    frozen.pop("embeddings.word_embeddings.weight")

    with pytest.raises(ValueError, match="don't match"):
        blend(model.backbone, frozen, 0.5)
