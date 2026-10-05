from pathlib import Path

import pytest

from unstuk_ml.freeze import freeze, frozen_changes


def test_nothing_to_report_before_freezing(tmp_path: Path) -> None:
    (tmp_path / "a.jsonl").write_text("{}\n")

    assert frozen_changes(tmp_path) == []


def test_reports_every_change_after_freezing(tmp_path: Path) -> None:
    (tmp_path / "a.jsonl").write_text("{}\n")
    (tmp_path / "b.jsonl").write_text("{}\n")
    freeze(tmp_path)

    (tmp_path / "a.jsonl").write_text('{"edited": true}\n')
    (tmp_path / "b.jsonl").unlink()
    (tmp_path / "c.jsonl").write_text("{}\n")

    assert frozen_changes(tmp_path) == [
        "a.jsonl changed after freezing",
        "b.jsonl removed after freezing",
        "c.jsonl added after freezing",
    ]


def test_an_unchanged_set_passes(tmp_path: Path) -> None:
    (tmp_path / "a.jsonl").write_text("{}\n")
    freeze(tmp_path)

    assert frozen_changes(tmp_path) == []


def test_refuses_to_freeze_twice(tmp_path: Path) -> None:
    freeze(tmp_path)

    with pytest.raises(FileExistsError):
        freeze(tmp_path)
