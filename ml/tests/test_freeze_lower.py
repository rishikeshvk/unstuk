from tiny_model import tiny_backbone
from torch import nn
from transformers import BertConfig, BertModel

from unstuk_ml.backbone import freeze_lower


def learning(module: nn.Module) -> list[bool]:
    return [p.requires_grad for p in module.parameters()]


def test_the_embeddings_and_lowest_layers_stop_learning() -> None:
    config = BertConfig(
        hidden_size=32, num_hidden_layers=3, num_attention_heads=4, intermediate_size=64
    )
    # transformers leaves BertModel's constructor unannotated.
    backbone = BertModel(config, add_pooling_layer=False)  # type: ignore[no-untyped-call]

    freeze_lower(backbone, 2)

    assert not any(learning(backbone.embeddings))
    assert not any(learning(backbone.encoder.layer[0]) + learning(backbone.encoder.layer[1]))
    assert all(learning(backbone.encoder.layer[2]))


def test_freezing_no_layers_leaves_everything_learning() -> None:
    backbone = tiny_backbone()

    freeze_lower(backbone, 0)

    assert all(learning(backbone))
