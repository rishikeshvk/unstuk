"""The decision model's answers as the shared report reads them (M5 spec section 1).

Noul gives the probability that a line is out of scope; the intents share the rest in proportion
to Choice, so `evaluate`'s metrics and the gate read the model as they read every baseline.
"""

import math
from collections.abc import Iterator, Sequence

import torch
from tokenizers import Tokenizer

from unstuk_ml.catalog import Catalog
from unstuk_ml.decision_batch import collate
from unstuk_ml.decision_model import Decision, DecisionModel
from unstuk_ml.evaluate import Scored
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.record import Record
from unstuk_ml.training_examples import Example, render_state

BATCH_SIZE = 64
# A probability of exactly 0 would make one line's log-loss infinite.
FLOOR = 1e-12


def predict(
    model: DecisionModel,
    records: Sequence[Record],
    intents: Sequence[str],
    catalog: Catalog,
    tokenizer: Tokenizer,
) -> list[Scored]:
    """Each line scored against the given intents' options, with its state if it has one."""
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
    scored = []
    decisions = _decisions(model, examples, tokenizer)
    for record, (choice, out_of_scope) in zip(records, decisions, strict=True):
        probabilities = {i: (1 - out_of_scope) * p for i, p in zip(intents, choice, strict=True)}
        scored.append(Scored(record, probabilities | {OUT_OF_SCOPE: out_of_scope}))
    return scored


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
    """Choice probabilities over each example's options, and its out-of-scope probability."""
    training = model.training
    model.train(False)
    device = next(model.parameters()).device
    try:
        for start in range(0, len(examples), BATCH_SIZE):
            chunk = examples[start : start + BATCH_SIZE]
            with torch.no_grad():
                decision: Decision = model(collate(chunk, tokenizer).to(device))
            choices = decision.choice_logits.float().softmax(dim=1).cpu()
            out_of_scope = decision.out_of_scope_logit.float().sigmoid().cpu()
            for example, choice, p in zip(chunk, choices, out_of_scope, strict=True):
                yield choice[: len(example.options)].tolist(), float(p)
    finally:
        model.train(training)
