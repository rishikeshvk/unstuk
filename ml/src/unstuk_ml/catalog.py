"""The parts of the repository's `catalog/` that data refers to (AGENTS.md invariant 8)."""

import json
from dataclasses import dataclass
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parents[3] / "catalog"


@dataclass(frozen=True)
class Catalog:
    intents: dict[str, str]
    """Intent id to its option text, the text the model chooses between."""
    checks: frozenset[str]
    """Check ids named by the intents' causes, which a record's `state` may list."""
    causes: dict[str, tuple[str, ...]]
    """Intent id to the check ids of its causes, in diagnosis order."""


def load_catalog(directory: Path = CATALOG_DIR) -> Catalog:
    intents = json.loads((directory / "intents.json").read_text(encoding="utf-8"))
    return Catalog(
        intents={intent["id"]: intent["option"] for intent in intents},
        checks=frozenset(cause["check"] for intent in intents for cause in intent["causes"]),
        causes={i["id"]: tuple(c["check"] for c in i["causes"]) for i in intents},
    )
