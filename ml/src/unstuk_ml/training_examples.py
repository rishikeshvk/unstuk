"""Training examples for the decision model (M5 spec section 2): a complaint, a state and options.

Options are drawn again each epoch, so the Choice head learns to choose among whatever it is
given rather than one fixed list. Options, state and typos each draw from their own stream, so
turning state or typos on can't change which options a line is offered.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass

from unstuk_ml.catalog import Catalog
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.record import Record
from unstuk_ml.state_slice import excluded_checks
from unstuk_ml.typos import noisy

OTHER_OPTIONS = (3, 11)
MAX_DISTRACTORS = 2


@dataclass(frozen=True)
class Example:
    text: str
    state: str
    """The device state as the model reads it; empty when there is none."""
    options: tuple[str, ...]
    answers: frozenset[int]
    """Indices of the correct options; empty out of scope, where the Choice loss is masked."""
    out_of_scope: bool | None
    """The Noul target; None for node questions, which don't ask it."""


def render_state(checks: Sequence[str], catalog: Catalog) -> str:
    """The checks as the app words them, so the encoder reads plain sentences, not IDs."""
    return " ".join(catalog.findings[check] for check in checks)


def epoch(
    records: Sequence[Record],
    nodes: Sequence[NodeQuestion],
    catalog: Catalog,
    intents: Sequence[str],
    *,
    seed: int,
    number: int,
    state: bool,
    typos: bool,
) -> list[Example]:
    """One epoch's examples: every line with freshly drawn options, then every node question."""
    streams = _Streams(
        options=random.Random(f"{seed}/{number}/options"),
        state=random.Random(f"{seed}/{number}/state"),
        typos=random.Random(f"{seed}/{number}/typos"),
    )
    lines = [_line_example(r, catalog, intents, streams, state, typos) for r in records]
    return lines + [_node_example(q) for q in nodes]


@dataclass(frozen=True)
class _Streams:
    options: random.Random
    state: random.Random
    typos: random.Random


def _line_example(
    record: Record,
    catalog: Catalog,
    intents: Sequence[str],
    streams: _Streams,
    state: bool,
    typos: bool,
) -> Example:
    chosen = _options(record, intents, streams.options)
    return Example(
        text=noisy(record.text, streams.typos) if typos else record.text,
        state=_state(record, catalog, streams.state) if state else "",
        options=tuple(catalog.intents[i] for i in chosen),
        answers=frozenset(n for n, i in enumerate(chosen) if i in record.labels),
        out_of_scope=OUT_OF_SCOPE in record.labels,
    )


def _options(record: Record, intents: Sequence[str], rng: random.Random) -> list[str]:
    """The intents offered: the gold ones and a random subset of the others, shuffled."""
    gold = [label for label in record.labels if label != OUT_OF_SCOPE]
    unknown = set(gold) - set(intents)
    if unknown:
        raise ValueError(f"{record.id} names intents this run can't offer: {sorted(unknown)}")
    others = [i for i in intents if i not in gold]
    low, high = (min(n, len(others)) for n in OTHER_OPTIONS)
    chosen = gold + rng.sample(others, rng.randint(low, high))
    rng.shuffle(chosen)
    return chosen


def _state(record: Record, catalog: Catalog, rng: random.Random) -> str:
    """The record's own state, or distractor checks that say nothing about its label."""
    if record.state is not None:
        return render_state(record.state, catalog)
    causes = {c for label in record.labels for c in catalog.causes.get(label, ())}
    pool = sorted(catalog.checks - causes - excluded_checks(catalog))
    return render_state(rng.sample(pool, rng.randint(0, MAX_DISTRACTORS)), catalog)


def _node_example(question: NodeQuestion) -> Example:
    return Example(
        text=question.question,
        state="",
        options=tuple(question.options),
        answers=frozenset({question.options.index(question.answer)}),
        out_of_scope=None,
    )
