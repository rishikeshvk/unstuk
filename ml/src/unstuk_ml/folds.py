"""Leave-intents-out folds (M5 spec section 3): a zero-shot check without the held-out intents.

Each fold removes some trained intents, their lines and their option texts from training, then
scores those intents' dev lines, as the test does for the held-out intents.
"""

import random
from collections.abc import Sequence

from unstuk_ml.catalog import Catalog
from unstuk_ml.labels import HELD_OUT
from unstuk_ml.record import Record

FOLDS = 3
SEED = 5


def trained_intents(catalog: Catalog) -> list[str]:
    return sorted(set(catalog.intents) - HELD_OUT)


def folds(intents: Sequence[str], seed: int = SEED) -> list[frozenset[str]]:
    """Disjoint groups of intents to remove, one per fold."""
    shuffled = sorted(intents)
    random.Random(seed).shuffle(shuffled)
    return [frozenset(shuffled[n::FOLDS]) for n in range(FOLDS)]


def without(records: Sequence[Record], removed: frozenset[str]) -> list[Record]:
    """The lines a fold trains on: none names a removed intent."""
    return [r for r in records if not removed & set(r.labels)]


def naming(records: Sequence[Record], removed: frozenset[str]) -> list[Record]:
    """The dev lines a fold scores: each names a removed intent."""
    return [r for r in records if removed & set(r.labels)]
