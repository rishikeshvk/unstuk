"""Real messages from the M8 sittings (m8-spec section 3).

They live in `data/real/` only, which is gitignored. Tools that read them print counts, never text.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from unstuk_ml.validate import DEFAULT_DATA_DIR

REAL_DIR = DEFAULT_DATA_DIR / "real"
SITTINGS_DIR = REAL_DIR / "sittings"
MESSAGES_FILE = REAL_DIR / "messages.jsonl"

Medium = Literal["in_person", "chat"]


class RealMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    participant: str
    medium: Medium
    card: str
    text: str = Field(min_length=1)


def read_messages(path: Path = MESSAGES_FILE) -> list[RealMessage]:
    return [
        RealMessage.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_messages(messages: Sequence[RealMessage], path: Path = MESSAGES_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(m.model_dump(), ensure_ascii=False) + "\n" for m in messages),
        encoding="utf-8",
    )
