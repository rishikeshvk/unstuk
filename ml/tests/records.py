"""Builds records for tests."""

from typing import Any

from unstuk_ml.record import Record


def make(record_id: str, text: str, label: str = "no_internet", **changes: Any) -> Record:
    fields: dict[str, Any] = {
        "id": record_id,
        "text": text,
        "labels": [label],
        "source": "generated",
        "generator": "claude-fresh",
        "batch": "train-01",
    }
    return Record.model_validate(fields | changes)
