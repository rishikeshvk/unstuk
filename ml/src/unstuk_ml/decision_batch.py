"""Decision examples as tensors (M5 spec section 1): complaints, their state and their options.

Each distinct option text is encoded once per batch, and examples point at their options by
index, because the catalog's dozen option texts repeat in nearly every example.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
from tokenizers import Encoding, Tokenizer

from unstuk_ml.training_examples import Example

# Training lines reach 83 tokens; a state of two findings adds about 20.
MAX_TOKENS = 128


@dataclass(frozen=True)
class Encoded:
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    token_type_ids: torch.Tensor


@dataclass(frozen=True)
class DecisionBatch:
    queries: Encoded
    """One row per example: the complaint, with the state as segment B when there is one."""
    options: Encoded
    """One row per distinct option text in the batch."""
    option_index: torch.Tensor
    """[examples, options] rows of `options`; 0 where padded."""
    option_mask: torch.Tensor
    """[examples, options] True where the example has that option."""
    answers: torch.Tensor
    """[examples, options] True on the correct options."""
    out_of_scope: torch.Tensor
    """[examples] the Noul target, 0 where the example doesn't ask it."""
    asks_out_of_scope: torch.Tensor
    """[examples] True where the example has a Noul target."""


def decision_tokenizer(path: Path) -> Tokenizer:
    tokenizer = Tokenizer.from_file(str(path))
    tokenizer.enable_truncation(MAX_TOKENS)
    tokenizer.enable_padding()
    return tokenizer


def collate(examples: Sequence[Example], tokenizer: Tokenizer) -> DecisionBatch:
    texts = list(dict.fromkeys(o for e in examples for o in e.options))
    row = {text: n for n, text in enumerate(texts)}
    width = max(len(e.options) for e in examples)
    index = torch.zeros(len(examples), width, dtype=torch.long)
    mask = torch.zeros(len(examples), width, dtype=torch.bool)
    answers = torch.zeros(len(examples), width, dtype=torch.bool)
    for n, example in enumerate(examples):
        count = len(example.options)
        index[n, :count] = torch.tensor([row[o] for o in example.options])
        mask[n, :count] = True
        answers[n, list(example.answers)] = True
    return DecisionBatch(
        # Without a state the line is encoded alone, exactly as M4's encoder read it.
        queries=_encode(tokenizer, [(e.text, e.state) if e.state else e.text for e in examples]),
        options=_encode(tokenizer, texts),
        option_index=index,
        option_mask=mask,
        answers=answers,
        out_of_scope=torch.tensor([float(e.out_of_scope or False) for e in examples]),
        asks_out_of_scope=torch.tensor([e.out_of_scope is not None for e in examples]),
    )


def _encode(tokenizer: Tokenizer, inputs: Sequence[str | tuple[str, str]]) -> Encoded:
    encodings: list[Encoding] = tokenizer.encode_batch(list(inputs))
    return Encoded(
        input_ids=torch.tensor([e.ids for e in encodings]),
        attention_mask=torch.tensor([e.attention_mask for e in encodings]),
        token_type_ids=torch.tensor([e.type_ids for e in encodings]),
    )
