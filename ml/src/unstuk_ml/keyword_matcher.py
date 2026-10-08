"""M2's keyword matcher, ported line for line from the app's `KeywordMatcher.kt` to score it here.

The app decided with it until M7. Its parity fixture (`tests/keyword-parity.json`) was checked by
both test suites while both existed, and still pins this port's behaviour.
"""

import json
import re
from pathlib import Path

from unstuk_ml.catalog import CATALOG_DIR

_NON_WORD = re.compile(r"[^a-z0-9]+")


class KeywordMatcher:
    def __init__(self, rules: dict[str, list[str]]) -> None:
        self._phrases = {
            intent: [_normalize(p) for p in phrases] for intent, phrases in rules.items()
        }

    def choose(self, complaint: str) -> dict[str, float]:
        """A probability per intent: its share of all phrase hits. Empty when nothing matched."""
        text = _normalize(complaint)
        hits = {i: sum(p in text for p in phrases) for i, phrases in self._phrases.items()}
        hits = {i: n for i, n in hits.items() if n > 0}
        total = sum(hits.values())
        return {i: n / total for i, n in hits.items()}


def load_matcher(catalog_dir: Path = CATALOG_DIR) -> KeywordMatcher:
    return KeywordMatcher(json.loads((catalog_dir / "keywords.json").read_text(encoding="utf-8")))


# Padded with spaces so a phrase only matches whole words ("ring" must not match "bring").
def _normalize(text: str) -> str:
    return " " + _NON_WORD.sub(" ", text.lower()).strip() + " "
