import json
from pathlib import Path

import pytest
from records import make

from unstuk_ml.evaluate import GateLines, Scored
from unstuk_ml.failures import load_failures, mistakes
from unstuk_ml.figures.failure_causes import tally

GATE = GateLines(automatic_at=0.75, clarify_below=0.7, clarify_margin=0.0)
RIGHT = Scored(make("r", "no net"), {"no_internet": 0.9}, GATE)
WRONG_ALONE = Scored(make("a", "no net"), {"phone_not_ringing": 0.9}, GATE)
WRONG_ASKED = Scored(make("b", "no ring", "phone_not_ringing"), {"no_internet": 0.6}, GATE)
VAGUE = Scored(make("v", "phone is odd", tags=["vague"]), {"phone_not_ringing": 0.9}, GATE)
ITEMS = [RIGHT, WRONG_ALONE, WRONG_ASKED, VAGUE]


def write(path: Path, codes: dict[str, str]) -> Path:
    lines = [json.dumps({"id": i, "cause": c, "note": ""}) for i, c in codes.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_mistakes_are_the_wrong_clear_lines() -> None:
    assert [s.record.id for s in mistakes(ITEMS)] == ["a", "b"]


def test_every_mistake_comes_back_with_its_code(tmp_path: Path) -> None:
    path = write(tmp_path / "f.jsonl", {"a": "wording", "b": "lexical_pull"})

    coded = load_failures(ITEMS, path)

    assert [(s.record.id, f.cause) for s, f in coded] == [("a", "wording"), ("b", "lexical_pull")]


def test_an_uncoded_mistake_is_refused(tmp_path: Path) -> None:
    path = write(tmp_path / "f.jsonl", {"a": "wording"})

    with pytest.raises(ValueError, match=r"missing \['b'\]"):
        load_failures(ITEMS, path)


def test_a_cause_outside_the_spec_is_refused(tmp_path: Path) -> None:
    path = write(tmp_path / "f.jsonl", {"a": "bad luck", "b": "wording"})

    with pytest.raises(ValueError, match="cause"):
        load_failures(ITEMS, path)


def test_causes_are_split_by_whether_the_app_acted_alone(tmp_path: Path) -> None:
    path = write(tmp_path / "f.jsonl", {"a": "wording", "b": "wording"})

    assert tally(load_failures(ITEMS, path)) == {"wording": (1, 1)}
