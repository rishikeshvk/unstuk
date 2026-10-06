"""Other wordings of each trained intent's option text (M5 spec section 3, round 3).

A wording teaches the Choice head what an option means, not one exact string. `import` copies an
agent's sheet into `catalog/option-wordings.json` as written; `check` then drops any wording that
the frozen encoder places nearer another intent's option than its own.
"""

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from unstuk_ml.catalog import CATALOG_DIR, WORDINGS_FILE, load_catalog
from unstuk_ml.encoder import embed_cached
from unstuk_ml.labels import HELD_OUT

Embed = Callable[[Sequence[str]], NDArray[np.float32]]
SHEET = CATALOG_DIR / "sheets" / "option-wordings-v1.txt"


def parse_sheet(text: str) -> dict[str, list[str]]:
    """`## <intent>` headers, each followed by one wording per line."""
    wordings: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in (raw.strip() for raw in text.splitlines()):
        if line.startswith("## "):
            current = wordings.setdefault(line[3:].strip(), [])
        elif line and line != "```":
            if current is None:
                raise ValueError(f"a wording comes before any intent header: {line!r}")
            current.append(line)
    return wordings


def misplaced(
    wordings: Mapping[str, Sequence[str]], options: Mapping[str, str], embed: Embed
) -> list[tuple[str, str, str]]:
    """Each wording nearer another intent's option than its own: (intent, wording, nearest)."""
    ids = list(options)
    option_vectors = embed([options[i] for i in ids])
    wrong = []
    for intent, texts in wordings.items():
        nearest = (embed(list(texts)) @ option_vectors.T).argmax(axis=1)
        wrong += [
            (intent, t, ids[n]) for t, n in zip(texts, nearest, strict=True) if ids[n] != intent
        ]
    return wrong


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("import", help=f"copy {SHEET.name} into {WORDINGS_FILE.name} as written")
    commands.add_parser(
        "check", help="drop wordings the frozen encoder places nearer another intent"
    )
    args = parser.parse_args()

    if args.command == "import":
        wordings = parse_sheet(SHEET.read_text(encoding="utf-8"))
        _write(WORDINGS_FILE, wordings)
        print({intent: len(texts) for intent, texts in wordings.items()})
        return
    catalog = load_catalog()
    wrong = misplaced(catalog.wordings, catalog.intents, embed_cached)
    for intent, text, nearest in wrong:
        print(f"dropped from {intent} (nearest {nearest}): {text}")
    dropped = {(intent, text) for intent, text, _ in wrong}
    kept = {i: [t for t in texts if (i, t) not in dropped] for i, texts in catalog.wordings.items()}
    _write(WORDINGS_FILE, kept)
    print({intent: len(texts) for intent, texts in kept.items()})


def _write(path: Path, wordings: Mapping[str, Sequence[str]]) -> None:
    held = set(wordings) & HELD_OUT
    if held:
        raise ValueError(f"held-out intents must have no wordings: {sorted(held)}")
    path.write_text(json.dumps(wordings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
