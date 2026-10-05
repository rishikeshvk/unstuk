"""Signs a label can be told apart by something other than meaning (shortcut learning)."""

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from unstuk_ml.record import Record

_WORD = re.compile(r"[a-z']+")
MIN_COUNT = 15
TOP = 5


@dataclass(frozen=True)
class LabelProfile:
    label: str
    count: int
    mean_words: float
    top_first_words: list[tuple[str, float]]
    """The most common first words and the share of the label's lines that start with each."""


@dataclass(frozen=True)
class Giveaway:
    token: str
    label: str
    share: float
    """Share of the token's lines that carry this label."""
    count: int


def profiles(records: Sequence[Record]) -> list[LabelProfile]:
    by_label: dict[str, list[list[str]]] = defaultdict(list)
    for record in records:
        by_label[record.labels[0]].append(_words(record.text))
    result = []
    for label, texts in sorted(by_label.items()):
        firsts = Counter(words[0] for words in texts if words)
        result.append(
            LabelProfile(
                label,
                len(texts),
                sum(len(w) for w in texts) / len(texts),
                [(word, n / len(texts)) for word, n in firsts.most_common(TOP)],
            )
        )
    return result


def giveaways(records: Sequence[Record], min_share: float = 0.9) -> list[Giveaway]:
    """Common tokens found almost only under one label. Many are honest cues ("talking"); the report
    lets a person tell those from generator habits ("hey", "kindly")."""
    token_labels: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        for token in set(_words(record.text)):
            token_labels[token][record.labels[0]] += 1
    found = []
    for token, labels in token_labels.items():
        total = sum(labels.values())
        label, n = labels.most_common(1)[0]
        if total >= MIN_COUNT and n / total >= min_share:
            found.append(Giveaway(token, label, n / total, total))
    return sorted(found, key=lambda g: (g.label, -g.count))


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())
