"""The vague slice (M6 spec section 1): complaints that could mean several problems.

Fresh agents wrote them; a blind labeller then labels the same texts without the writers' labels,
and only the readings both leave open are kept, so a line is vague by two independent judgements.
"""

import argparse
import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from unstuk_ml import duplicates
from unstuk_ml.catalog import load_catalog
from unstuk_ml.clean import LEAKAGE
from unstuk_ml.grid import Cell, check_cell
from unstuk_ml.labels import HELD_OUT, VAGUE
from unstuk_ml.normalize import normalize
from unstuk_ml.record import Record, read_records
from unstuk_ml.sheet import parse_sheet

DEV_BATCHES = frozenset({"vague-06", "vague-07", "vague-13", "vague-14"})
MIN_READINGS = 2
SEED = 17


@dataclass(frozen=True)
class Slice:
    train: list[Record]
    dev: list[Record]
    dropped: list[duplicates.Drop]


def read_batches(sheets: Path, plan: Mapping[str, Cell]) -> list[Record]:
    records: list[Record] = []
    for batch, cell in plan.items():
        check_cell(cell)
        lines = parse_sheet((sheets / f"{batch}.txt").read_text(encoding="utf-8"))
        records += [
            Record(
                id=f"{batch}-{n:03d}",
                text=normalize(line.text),
                labels=line.labels,
                tags=[VAGUE],
                source="generated",
                generator="claude-fresh",
                batch=batch,
                persona=dict(cell),
            )
            for n, line in enumerate(lines, 1)
        ]
    return records


def blind_keys(records: Sequence[Record], seed: int = SEED) -> dict[str, Record]:
    """Shuffled before numbering, so neither a key nor a line's neighbours hint at its batch."""
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    return {f"v{n:03d}": r for n, r in enumerate(shuffled, 1)}


def agreed(record: Record, blind: Sequence[str]) -> Record | None:
    """The record with only the readings both labellers gave, or None if fewer than two remain."""
    shared = [label for label in record.labels if label in blind]
    if len(shared) < MIN_READINGS:
        return None
    return record.model_copy(update={"labels": shared})


def build(
    records: Sequence[Record], blind: Mapping[str, Sequence[str]], test: Sequence[Record]
) -> Slice:
    """`blind` maps record ids to the blind labeller's labels."""
    trained = set(load_catalog().intents) - HELD_OUT
    dropped: list[duplicates.Drop] = []
    kept: list[Record] = []
    for record in records:
        if not set(record.labels) <= trained:
            dropped.append(duplicates.Drop(record, "a label that isn't a trained intent"))
            continue
        both = agreed(record, blind[record.id])
        if both is None:
            dropped.append(duplicates.Drop(record, "the blind labeller settled it"))
            continue
        kept.append(both)
    kept, more = duplicates.exact_duplicates(kept)
    dropped += more
    leaked = duplicates.leaking(kept, test, LEAKAGE)
    dropped += leaked
    leaked_ids = {d.record.id for d in leaked}
    kept = [r for r in kept if r.id not in leaked_ids]
    return Slice(
        train=[r for r in kept if r.batch not in DEV_BATCHES],
        dev=[r for r in kept if r.batch in DEV_BATCHES],
        dropped=dropped,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the vague slice.")
    parser.add_argument("folder", type=Path, help="data/vague: plan.json, sheets/, blind-labels")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("blind", help="write key<TAB>text for a blind labeller")
    commands.add_parser("build", help="keep the lines both labellers leave open")
    args = parser.parse_args()

    folder: Path = args.folder
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    keys = blind_keys(read_batches(folder / "sheets", plan))
    if args.command == "blind":
        out = folder / "blind.tsv"
        out.write_text("".join(f"{k}\t{r.text}\n" for k, r in keys.items()), encoding="utf-8")
        print(f"{len(keys)} texts in {out}")
        return
    rows = (folder / "blind-labels.ndjson").read_text(encoding="utf-8").splitlines()
    blind = {keys[row["key"]].id: row["labels"] for row in map(json.loads, rows)}
    test_files = sorted((folder.parent / "test").glob("*.jsonl"))
    test = [r for path in test_files for r in read_records(path)]
    result = build(list(keys.values()), blind, test)
    for name, records in (("train", result.train), ("dev", result.dev)):
        lines = (json.dumps(r.model_dump(exclude_none=True), ensure_ascii=False) for r in records)
        text = "".join(f"{line}\n" for line in lines)
        (folder / f"{name}.jsonl").write_text(text, encoding="utf-8")
    reasons: dict[str, int] = {}
    for drop in result.dropped:
        reason = drop.reason.split(" of ")[0]
        reasons[reason] = reasons.get(reason, 0) + 1
    print(f"{len(result.train)} train, {len(result.dev)} dev; dropped {reasons}")
