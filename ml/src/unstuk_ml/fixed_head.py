"""The fixed-head rung's model (M5 spec section 3): fine-tuned bge-small read by one linear layer.

One output per trained label, as in M4's frozen probe, so it measures what fine-tuning adds on its
own. Unlike the decision model it can't name an intent it never trained on.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass, fields

import numpy as np
import torch
from numpy.typing import NDArray
from tokenizers import Tokenizer
from torch import nn
from transformers import BertModel

from unstuk_ml.catalog import Catalog
from unstuk_ml.decision_batch import Encoded, encode
from unstuk_ml.folds import trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.record import Record
from unstuk_ml.typos import noisy

BATCH_SIZE = 64


def fixed_labels(catalog: Catalog) -> list[str]:
    return [*trained_intents(catalog), OUT_OF_SCOPE]


@dataclass(frozen=True)
class Row:
    text: str
    label: int


def rows(
    records: Sequence[Record], labels: Sequence[str], *, seed: int, number: int, typos: bool
) -> list[Row]:
    """One row per label, so a line with two problems teaches both (as M4's rungs do)."""
    rng = random.Random(f"{seed}/{number}/typos")
    return [
        Row(noisy(r.text, rng) if typos else r.text, labels.index(label))
        for r in records
        for label in r.labels
    ]


@dataclass(frozen=True)
class FixedHeadBatch:
    texts: Encoded
    labels: torch.Tensor

    def to(self, device: torch.device) -> "FixedHeadBatch":
        return FixedHeadBatch(*(getattr(self, f.name).to(device) for f in fields(self)))


def collate_rows(batch: Sequence[Row], tokenizer: Tokenizer) -> FixedHeadBatch:
    return FixedHeadBatch(
        texts=encode(tokenizer, [row.text for row in batch]),
        labels=torch.tensor([row.label for row in batch]),
    )


class FixedHeadModel(nn.Module):
    def __init__(self, backbone: BertModel, labels: Sequence[str]) -> None:
        super().__init__()
        self.labels = list(labels)
        self.backbone = backbone
        self.head = nn.Linear(backbone.config.hidden_size, len(self.labels))

    def forward(self, texts: Encoded) -> torch.Tensor:
        hidden: torch.Tensor = self.backbone(
            input_ids=texts.input_ids,
            attention_mask=texts.attention_mask,
            token_type_ids=texts.token_type_ids,
        ).last_hidden_state
        logits: torch.Tensor = self.head(hidden[:, 0])
        return logits


def fixed_head_loss(model: FixedHeadModel, batch: FixedHeadBatch) -> torch.Tensor:
    return nn.functional.cross_entropy(model(batch.texts), batch.labels)


def fixed_head_logits(
    model: FixedHeadModel, records: Sequence[Record], tokenizer: Tokenizer
) -> NDArray[np.float64]:
    """One row of logits per line, in the model's label order."""
    training = model.training
    model.train(False)
    device = next(model.parameters()).device
    rows_out = []
    try:
        for start in range(0, len(records), BATCH_SIZE):
            texts = [r.text for r in records[start : start + BATCH_SIZE]]
            with torch.no_grad():
                rows_out.append(model(encode(tokenizer, texts).to(device)).float().cpu())
    finally:
        model.train(training)
    return torch.cat(rows_out).numpy().astype(np.float64)
