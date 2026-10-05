"""Train and dev, split by batch so near-twins from one batch never sit on both sides."""

import random
from collections import defaultdict
from collections.abc import Sequence

from unstuk_ml.grid import AXES
from unstuk_ml.record import Record

# How many batches of each kind go to dev; about 15% of the pool.
DEV_BATCHES = {"train": 6, "oos": 2, "contrast": 1}
ALWAYS_DEV = frozenset({"mobile-actions-eval"})
ATTEMPTS = 1000


def split(records: Sequence[Record], seed: int) -> tuple[list[Record], list[Record]]:
    dev_batches = _choose_dev_batches(records, seed)
    train = [r for r in records if r.batch not in dev_batches]
    dev = [r for r in records if r.batch in dev_batches]
    return train, dev


def _choose_dev_batches(records: Sequence[Record], seed: int) -> set[str]:
    """Draws dev batches until every grid value appears in dev, covering every kind of writer."""
    personas: dict[str, dict[str, str]] = {}
    by_kind: dict[str, list[str]] = defaultdict(list)
    for record in records:
        if record.persona is not None and record.batch not in personas:
            personas[record.batch] = record.persona
            by_kind[record.batch.rsplit("-", 1)[0]].append(record.batch)
    rng = random.Random(seed)
    for _ in range(ATTEMPTS):
        chosen = {
            b for kind, n in DEV_BATCHES.items() for b in rng.sample(sorted(by_kind[kind]), n)
        }
        if _covers_grid([personas[b] for b in chosen]):
            return chosen | ALWAYS_DEV
    raise ValueError(f"no dev split covering the grid in {ATTEMPTS} attempts")


def _covers_grid(cells: Sequence[dict[str, str]]) -> bool:
    return all({cell[axis] for cell in cells} == set(values) for axis, values in AXES.items())
