"""Exact and near duplicates, inside the pool and against the frozen test set."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from unstuk_ml.normalize import normalize
from unstuk_ml.record import Record

# Rows compared at once; bounds memory to CHUNK x len(other) floats.
CHUNK = 512


@dataclass(frozen=True)
class Drop:
    record: Record
    reason: str


def exact_duplicates(records: Sequence[Record]) -> tuple[list[Record], list[Drop]]:
    """Keeps the first of each repeated text; one with differing labels is dropped entirely."""
    groups: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        groups[_key(record.text)].append(record)
    kept: list[Record] = []
    dropped: list[Drop] = []
    for group in groups.values():
        first, *rest = group
        if len({tuple(r.labels) for r in group}) > 1:
            dropped += [Drop(r, "same text, different labels") for r in group]
            continue
        kept.append(first)
        dropped += [Drop(r, f"exact duplicate of {first.id}") for r in rest]
    return kept, dropped


def similarity(texts: Sequence[str], others: Sequence[str]) -> np.ndarray:
    """Each text's highest cosine similarity to any of `others`, and its index (char 3-5-grams)."""
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
    vectorizer.fit([*texts, *others])
    left, right = vectorizer.transform(texts), vectorizer.transform(others)
    best = np.zeros((len(texts), 2))
    for start in range(0, len(texts), CHUNK):
        scores = (left[start : start + CHUNK] @ right.T).toarray()
        best[start : start + CHUNK, 0] = scores.max(axis=1)
        best[start : start + CHUNK, 1] = scores.argmax(axis=1)
    return best


def near_duplicates(records: Sequence[Record], threshold: float) -> tuple[list[Record], list[Drop]]:
    """Drops a record too close to an earlier kept one of the same label; pairs survive."""
    kept: list[Record] = []
    dropped: list[Drop] = []
    by_label: dict[tuple[str, ...], list[Record]] = defaultdict(list)
    for record in records:
        by_label[tuple(record.labels)].append(record)
    for group in by_label.values():
        texts = [r.text for r in group]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
        matrix = vectorizer.fit_transform(texts)
        scores = (matrix @ matrix.T).toarray()
        survivors: list[int] = []
        for i, record in enumerate(group):
            close = [j for j in survivors if scores[i, j] >= threshold]
            if close:
                dropped.append(Drop(record, f"near duplicate of {group[close[0]].id}"))
            else:
                survivors.append(i)
        kept += [group[i] for i in survivors]
    order = {r.id: n for n, r in enumerate(records)}
    return sorted(kept, key=lambda r: order[r.id]), dropped


def leaking(records: Sequence[Record], test: Sequence[Record], threshold: float) -> list[Drop]:
    """Training records at least `threshold` similar to a test record; the test is never touched."""
    best = similarity([r.text for r in records], [t.text for t in test])
    return [
        Drop(record, f"close to test {test[int(index)].id} ({score:.2f})")
        for record, (score, index) in zip(records, best, strict=True)
        if score >= threshold
    ]


def _key(text: str) -> str:
    return normalize(text).lower()
