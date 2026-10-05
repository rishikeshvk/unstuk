"""One line of a data file (M3 spec section 7)."""

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unstuk_ml.labels import OUT_OF_SCOPE, SLICES, VAGUE

MAX_LABELS = 2
MAX_VAGUE_LABELS = 3


class Record(BaseModel):
    # A misspelt field must be an error, not a value silently dropped.
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    labels: list[str] = Field(min_length=1)
    tags: list[str] = []
    source: Literal["seed", "generated", "handwritten", "mobile_actions"]
    generator: str = Field(min_length=1)
    batch: str = Field(min_length=1)
    persona: dict[str, str] | None = None
    state: list[str] | None = None

    @model_validator(mode="after")
    def follows_the_label_contract(self) -> Self:
        if not self.text.strip():
            raise ValueError("text is blank")
        limit = MAX_VAGUE_LABELS if VAGUE in self.tags else MAX_LABELS
        if len(self.labels) > limit:
            raise ValueError(f"{len(self.labels)} labels, at most {limit} allowed")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("a label is repeated")
        if OUT_OF_SCOPE in self.labels and len(self.labels) > 1:
            raise ValueError(f"{OUT_OF_SCOPE} can't be combined with an intent")
        unknown_tags = set(self.tags) - SLICES - {VAGUE}
        if unknown_tags:
            raise ValueError(f"unknown tags: {', '.join(sorted(unknown_tags))}")
        return self


def read_records(path: Path) -> list[Record]:
    return [
        Record.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
