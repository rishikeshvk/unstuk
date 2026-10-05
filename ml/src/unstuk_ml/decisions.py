"""Review decisions: keep, relabel or drop a training line, each tied to a labelling-guide rule."""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unstuk_ml.duplicates import Drop
from unstuk_ml.record import Record


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    action: Literal["keep", "relabel", "drop"]
    labels: list[str] | None = None
    rule: str = Field(min_length=1)
    """The guide section that decides it, such as "§5 connected"."""

    @model_validator(mode="after")
    def relabel_names_labels(self) -> Self:
        if (self.action == "relabel") != bool(self.labels):
            raise ValueError("labels are given exactly when the action is relabel")
        return self


def load(path: Path) -> dict[str, Decision]:
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8").splitlines()
    decisions = [Decision.model_validate_json(line) for line in lines if line.strip()]
    return {d.id: d for d in decisions}


def apply(
    records: Sequence[Record], decisions: dict[str, Decision]
) -> tuple[list[Record], list[Drop]]:
    kept: list[Record] = []
    dropped: list[Drop] = []
    for record in records:
        decision = decisions.get(record.id)
        if decision is None or decision.action == "keep":
            kept.append(record)
        elif decision.action == "drop":
            dropped.append(Drop(record, f"review: {decision.rule}"))
        else:
            kept.append(record.model_copy(update={"labels": decision.labels}))
    return kept, dropped
