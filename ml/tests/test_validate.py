import json
from pathlib import Path
from typing import Any

import pytest

from unstuk_ml.catalog import load_catalog
from unstuk_ml.freeze import freeze
from unstuk_ml.validate import validate

CATALOG = load_catalog()


def record(**changes: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "r1",
        "text": "my phone doesn't ring",
        "labels": ["phone_not_ringing"],
        "source": "seed",
        "generator": "claude",
        "batch": "seed-01",
    }
    return base | changes


def write(path: Path, *lines: dict[str, Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = [line if isinstance(line, str) else json.dumps(line) for line in lines]
    path.write_text("\n".join(text) + "\n", encoding="utf-8")


def messages(data_dir: Path) -> list[str]:
    return [problem.message for problem in validate(data_dir, CATALOG)]


def test_a_valid_file_has_no_problems(tmp_path: Path) -> None:
    write(
        tmp_path / "seed" / "a.jsonl",
        record(),
        record(id="r2", labels=["out_of_scope"], tags=["collision"]),
        record(id="r3", labels=["no_internet", "screen_too_dim"], tags=["multi"]),
        record(id="r4", labels=["no_internet"], state=["airplane_on"], persona={"age": "70+"}),
    )

    assert messages(tmp_path) == []


def test_reports_lines_that_are_not_json(tmp_path: Path) -> None:
    write(tmp_path / "seed" / "a.jsonl", "{not json")

    [message] = messages(tmp_path)

    assert "JSON" in message


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"lables": ["no_internet"]}, "lables"),
        ({"text": "   "}, "text is blank"),
        ({"source": "scraped"}, "source"),
        ({"labels": ["no_internet", "screen_too_dim", "text_too_small"]}, "at most 2"),
        ({"labels": ["out_of_scope", "no_internet"]}, "can't be combined"),
        ({"tags": ["sarcasm"]}, "unknown tags: sarcasm"),
    ],
)
def test_reports_records_that_break_the_format(
    tmp_path: Path, changes: dict[str, Any], expected: str
) -> None:
    write(tmp_path / "seed" / "a.jsonl", record(**changes))

    assert any(expected in message for message in messages(tmp_path))


def test_vague_complaints_may_carry_three_labels(tmp_path: Path) -> None:
    labels = ["no_internet", "notifications_missing", "phone_not_ringing"]
    write(tmp_path / "seed" / "a.jsonl", record(labels=labels, tags=["vague"]))

    assert messages(tmp_path) == []


def test_reports_labels_and_checks_missing_from_the_catalog(tmp_path: Path) -> None:
    write(tmp_path / "seed" / "a.jsonl", record(labels=["phone_on_fire"], state=["moon_full"]))

    assert messages(tmp_path) == ["unknown label phone_on_fire", "unknown check moon_full in state"]


def test_reports_an_id_used_twice_across_files(tmp_path: Path) -> None:
    write(tmp_path / "seed" / "a.jsonl", record())
    write(tmp_path / "raw" / "b.jsonl", record())

    [message] = messages(tmp_path)

    assert message.startswith("duplicate id r1, first at")


def test_held_out_intents_are_allowed_only_in_the_test_set(tmp_path: Path) -> None:
    write(tmp_path / "seed" / "a.jsonl", record(labels=["wrong_time"]))
    write(tmp_path / "test" / "b.jsonl", record(id="r2", labels=["wrong_time"]))

    problems = validate(tmp_path, CATALOG)

    assert [(p.place.path.parent.name, p.message) for p in problems] == [
        ("seed", "held-out intent wrong_time outside test/")
    ]


@pytest.mark.parametrize("folder", ["real", "clean"])
def test_skips_real_messages_and_derived_clean_data(tmp_path: Path, folder: str) -> None:
    write(tmp_path / folder / "a.jsonl", "anything at all")

    assert messages(tmp_path) == []


def test_reports_a_test_file_changed_after_freezing(tmp_path: Path) -> None:
    write(tmp_path / "test" / "a.jsonl", record())
    freeze(tmp_path / "test")
    write(tmp_path / "test" / "a.jsonl", record(text="edited later"))

    assert messages(tmp_path) == ["a.jsonl changed after freezing"]
