from pathlib import Path

import pytest
from pydantic import ValidationError
from records import make

from unstuk_ml.decisions import Decision, apply, load


def test_relabels_drops_and_keeps(tmp_path: Path) -> None:
    path = tmp_path / "decisions.jsonl"
    path.write_text(
        '{"id": "a", "action": "relabel", "labels": ["wifi_no_load"], "rule": "§5 connected"}\n'
        '{"id": "b", "action": "drop", "rule": "§1 unclear"}\n'
        '{"id": "c", "action": "keep", "rule": "§4"}\n'
    )
    records = [make("a", "connected, nothing loads"), make("b", "hmm"), make("c", "no net")]

    kept, dropped = apply(records, load(path))

    assert [(r.id, r.labels) for r in kept] == [("a", ["wifi_no_load"]), ("c", ["no_internet"])]
    assert [(d.record.id, d.reason) for d in dropped] == [("b", "review: §1 unclear")]


def test_no_file_means_no_decisions(tmp_path: Path) -> None:
    assert load(tmp_path / "missing.jsonl") == {}


def test_a_relabel_must_name_its_labels() -> None:
    with pytest.raises(ValidationError):
        Decision(id="a", action="relabel", rule="§5")
