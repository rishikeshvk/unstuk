"""The tokenizer parity fixture (M7 spec section 6): what bge's tokenizer makes of every text the
app could plausibly be given, so the Kotlin WordPiece can be held to the same ids.

Every train, dev, vague, state and node text, alone and with its rendered state, plus a typo'd copy
of each, the catalog's option texts and findings, and hand-written edge cases. The test splits and
`data/real/` are never read (AGENTS.md invariant 9).
"""

import argparse
import json
import random
from collections.abc import Iterator
from pathlib import Path

from tokenizers import Tokenizer

from unstuk_ml import rung
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.encoder import download
from unstuk_ml.node_labels import read_questions
from unstuk_ml.record import Record, read_records
from unstuk_ml.training_examples import render_state
from unstuk_ml.typos import add_typo
from unstuk_ml.validate import DEFAULT_DATA_DIR

FIXTURE = (
    DEFAULT_DATA_DIR.parent / "android" / "app" / "src" / "test" / "resources" / "wordpiece.jsonl"
)
SEED = 7
LONG = " ".join(["my phone keeps showing a weird notification about storage"] * 20)
# Text shapes the data may lack: accents, other scripts, emoji, odd spaces and control characters.
EDGE_CASES: tuple[str | tuple[str, str], ...] = (
    "",
    "   ",
    "Café résumé naïve façade",
    "WIFI!!! not working???",
    "can't  hear\tanything\nat all",
    "screen\u00a0too dark",
    "zero\u200bwidth",
    "bell\u0007 rings",
    "phone 📱 is 🔇 silent",
    "手机没有声音",
    "फ़ोन बज नहीं रहा",
    "ﬁne print ① ⅷ",
    "x" * 120,
    "self-driving e-mail co-op",
    "$5 @home #1 50% off (maybe) [ok] {no} ~yes~",
    LONG,
    (LONG, "Do Not Disturb is on."),
    ("no sound", LONG),
    (LONG, LONG),
)


def inputs(catalog: Catalog, data: Path = DEFAULT_DATA_DIR) -> Iterator[str | tuple[str, str]]:
    rng = random.Random(SEED)
    records = [
        *rung.read_clean("train"),
        *rung.read_clean("dev"),
        *read_records(data / "vague" / "train.jsonl"),
        *read_records(data / "vague" / "dev.jsonl"),
        *read_records(data / "state" / "train.jsonl"),
    ]
    for record in records:
        yield from _with_typo(_record_input(record, catalog), rng)
    for split in ("train", "dev"):
        for question in read_questions(data / "nodes" / f"{split}.jsonl"):
            yield from _with_typo(question.question, rng)
            yield from question.options
    yield from catalog.intents.values()
    yield from catalog.findings.values()
    yield from EDGE_CASES


def write(tokenizer: Tokenizer, catalog: Catalog, path: Path = FIXTURE) -> int:
    rows = list(dict.fromkeys(inputs(catalog)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        for item in rows:
            a, b = item if isinstance(item, tuple) else (item, None)
            encoding = tokenizer.encode(a, b) if b is not None else tokenizer.encode(a)
            row = {"a": a, "b": b, "ids": encoding.ids, "type_ids": encoding.type_ids}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def _record_input(record: Record, catalog: Catalog) -> str | tuple[str, str]:
    return (record.text, render_state(record.state, catalog)) if record.state else record.text


def _with_typo(item: str | tuple[str, str], rng: random.Random) -> Iterator[str | tuple[str, str]]:
    yield item
    yield (add_typo(item[0], rng), item[1]) if isinstance(item, tuple) else add_typo(item, rng)


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    tokenizer = decision_tokenizer(download()[1])
    tokenizer.no_padding()
    count = write(tokenizer, load_catalog())
    print(f"wrote {count} encodings to {FIXTURE} ({FIXTURE.stat().st_size / 1e6:.1f} MB)")
