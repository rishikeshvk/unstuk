"""The decision model's answers as the shared report reads them (M5 spec section 1).

Noul gives the probability that a line is out of scope; the intents share the rest in proportion
to Choice, so `evaluate`'s metrics and the gate read the model as they read every baseline. Each
head has its own temperature, fitted on dev (spec section 3).
"""

import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray
from tokenizers import Tokenizer

from unstuk_ml.catalog import Catalog
from unstuk_ml.decision_batch import collate
from unstuk_ml.decision_model import Decision, DecisionModel
from unstuk_ml.evaluate import Scored
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.record import Record
from unstuk_ml.temperature import fit_temperature, softmax
from unstuk_ml.training_examples import Example, render_state

BATCH_SIZE = 64
# A probability of exactly 0 would make one line's log-loss infinite.
FLOOR = 1e-12


@dataclass(frozen=True)
class Temperatures:
    choice: float
    noul: float


UNCALIBRATED = Temperatures(choice=1.0, noul=1.0)


@dataclass(frozen=True)
class Logits:
    choice: NDArray[np.float64]
    """[lines, options]"""
    out_of_scope: NDArray[np.float64]
    """[lines]"""


def decision_logits(
    model: DecisionModel,
    records: Sequence[Record],
    intents: Sequence[str],
    catalog: Catalog,
    tokenizer: Tokenizer,
) -> Logits:
    """Each line against the given intents' options, with its state if it has one."""
    options = tuple(catalog.intents[i] for i in intents)
    examples = [
        Example(
            text=r.text,
            state=render_state(r.state, catalog) if r.state else "",
            options=options,
            answers=frozenset(),
            out_of_scope=None,
        )
        for r in records
    ]
    choice, out_of_scope = zip(*_decisions(model, examples, tokenizer), strict=True)
    return Logits(np.array(choice, dtype=np.float64), np.array(out_of_scope, dtype=np.float64))


def scored(
    logits: Logits,
    records: Sequence[Record],
    intents: Sequence[str],
    temperatures: Temperatures = UNCALIBRATED,
) -> list[Scored]:
    choice = softmax(logits.choice, temperatures.choice)
    out_of_scope = 1 / (1 + np.exp(-logits.out_of_scope / temperatures.noul))
    items = []
    for record, row, p in zip(records, choice, out_of_scope, strict=True):
        probabilities = {i: float((1 - p) * q) for i, q in zip(intents, row, strict=True)}
        items.append(Scored(record, probabilities | {OUT_OF_SCOPE: float(p)}))
    return items


def predict(
    model: DecisionModel,
    records: Sequence[Record],
    intents: Sequence[str],
    catalog: Catalog,
    tokenizer: Tokenizer,
    temperatures: Temperatures = UNCALIBRATED,
) -> list[Scored]:
    logits = decision_logits(model, records, intents, catalog, tokenizer)
    return scored(logits, records, intents, temperatures)


def fit_temperatures(
    logits: Logits, records: Sequence[Record], intents: Sequence[str]
) -> Temperatures:
    """Choice on the in-scope lines, Noul on every line; each by log-loss."""
    in_scope = [n for n, r in enumerate(records) if r.labels[0] != OUT_OF_SCOPE]
    choice_targets = np.array([intents.index(records[n].labels[0]) for n in in_scope])
    # Two columns [0, z] make the softmax the sigmoid, so the same fit serves the yes/no head.
    noul = np.stack([np.zeros_like(logits.out_of_scope), logits.out_of_scope], axis=1)
    noul_targets = np.array([int(r.labels[0] == OUT_OF_SCOPE) for r in records])
    return Temperatures(
        choice=fit_temperature(logits.choice[in_scope], choice_targets),
        noul=fit_temperature(noul, noul_targets),
    )


def log_loss(scored: Sequence[Scored]) -> float:
    """Mean minus log probability of each line's first label."""
    losses = [-math.log(max(s.probabilities[s.record.labels[0]], FLOOR)) for s in scored]
    return sum(losses) / len(losses)


def node_accuracy(
    model: DecisionModel, questions: Sequence[NodeQuestion], tokenizer: Tokenizer
) -> float:
    examples = [Example(q.question, "", tuple(q.options), frozenset(), None) for q in questions]
    right = [
        q.options[max(range(len(choice)), key=choice.__getitem__)] == q.answer
        for q, (choice, _) in zip(questions, _decisions(model, examples, tokenizer), strict=True)
    ]
    return sum(right) / len(right)


def _decisions(
    model: DecisionModel, examples: Sequence[Example], tokenizer: Tokenizer
) -> Iterator[tuple[list[float], float]]:
    """Choice logits over each example's options, and its out-of-scope logit."""
    training = model.training
    model.train(False)
    device = next(model.parameters()).device
    try:
        for start in range(0, len(examples), BATCH_SIZE):
            chunk = examples[start : start + BATCH_SIZE]
            with torch.no_grad():
                decision: Decision = model(collate(chunk, tokenizer).to(device))
            choices = decision.choice_logits.float().cpu()
            out_of_scope = decision.out_of_scope_logit.float().cpu()
            for example, choice, z in zip(chunk, choices, out_of_scope, strict=True):
                yield choice[: len(example.options)].tolist(), float(z)
    finally:
        model.train(training)
