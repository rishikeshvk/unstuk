import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from unstuk_ml.catalog import CATALOG_DIR, load_catalog
from unstuk_ml.labels import HELD_OUT
from unstuk_ml.option_wordings import misplaced, parse_sheet


def test_a_sheet_gives_each_intent_its_wordings() -> None:
    sheet = "```\n## no_internet\nNo web at all\n\nNothing goes online\n"
    sheet += "## talkback_on\nIt speaks\n```\n"

    assert parse_sheet(sheet) == {
        "no_internet": ["No web at all", "Nothing goes online"],
        "talkback_on": ["It speaks"],
    }


def test_a_wording_before_any_header_is_an_error() -> None:
    with pytest.raises(ValueError, match="before any intent header"):
        parse_sheet("No web at all\n## no_internet\n")


def test_the_catalogs_wordings_are_for_trained_intents_only() -> None:
    wordings = load_catalog().wordings

    assert wordings
    assert not set(wordings) & HELD_OUT


def test_a_wording_for_a_held_out_intent_is_refused(tmp_path: Path) -> None:
    for name in ("intents.json", "fixes.json"):
        (tmp_path / name).write_text((CATALOG_DIR / name).read_text())
    (tmp_path / "option-wordings.json").write_text(json.dumps({"wrong_time": ["The clock is off"]}))

    with pytest.raises(ValueError, match="wrong_time"):
        load_catalog(tmp_path)


def test_a_wording_nearer_another_intents_option_is_flagged() -> None:
    options = {"a": "alpha", "b": "beta"}
    axis = {"alpha": 0, "beta": 1, "like alpha": 0, "like beta": 1}

    def embed(texts: Sequence[str]) -> NDArray[np.float32]:
        return np.eye(2, dtype=np.float32)[[axis[t] for t in texts]]

    wrong = misplaced({"a": ["like alpha", "like beta"]}, options, embed)

    assert wrong == [("a", "like beta", "b")]
