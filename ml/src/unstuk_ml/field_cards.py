"""The M8 symptom cards (m8-spec section 2): short stories that never name the setting."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from unstuk_ml.validate import DEFAULT_DATA_DIR

CARDS_FILE = DEFAULT_DATA_DIR / "field" / "cards.json"
# Prompts for a problem the person really had; they come last in every sitting.
FREE = "free"


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    about: str
    """The intent the story was written for, `out_of_scope`, `vague` or `free`.

    A stimulus, not a label: a person may describe something else.
    """
    story: str


def load_cards(path: Path = CARDS_FILE) -> list[Card]:
    return TypeAdapter(list[Card]).validate_json(path.read_text(encoding="utf-8"))
