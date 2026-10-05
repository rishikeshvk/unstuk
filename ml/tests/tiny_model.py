"""Small random models, so tests run in seconds without bge-small's weights."""

import torch
from transformers import BertConfig, BertModel

from unstuk_ml.decision_model import DecisionModel, Head


def tiny_backbone() -> BertModel:
    torch.manual_seed(0)
    config = BertConfig(
        hidden_size=32, num_hidden_layers=1, num_attention_heads=4, intermediate_size=64
    )
    # transformers leaves BertModel's constructor unannotated.
    return BertModel(config, add_pooling_layer=False)  # type: ignore[no-untyped-call]


def tiny_model(head: Head) -> DecisionModel:
    model = DecisionModel(tiny_backbone(), head)
    model.train(False)
    return model
