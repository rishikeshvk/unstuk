import json
from pathlib import Path

import pytest

from unstuk_ml.catalog import CATALOG_DIR, load_catalog
from unstuk_ml.keyword_matcher import KeywordMatcher, load_matcher

FIXTURE = Path(__file__).parent / "keyword-parity.json"


def test_matches_the_shared_parity_fixture() -> None:
    matcher = load_matcher()

    for case in json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]:
        got = matcher.choose(case["complaint"])
        assert got.keys() == case["probabilities"].keys(), case["complaint"]
        for intent, p in case["probabilities"].items():
            assert got[intent] == pytest.approx(p)


def test_matches_whole_words_and_shares_probability_by_hits() -> None:
    matcher = KeywordMatcher({"a": ["ring"], "b": ["dark", "too dark"]})

    assert matcher.choose("bring tea") == {}
    assert matcher.choose("Ring? too dark") == pytest.approx({"a": 1 / 3, "b": 2 / 3})


def test_rules_cover_exactly_the_catalogs_intents() -> None:
    rules = json.loads((CATALOG_DIR / "keywords.json").read_text(encoding="utf-8"))

    assert set(rules) == set(load_catalog().intents)
