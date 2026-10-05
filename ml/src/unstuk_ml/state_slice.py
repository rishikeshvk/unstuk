"""The state slice (M3 spec section 8): complaints the words can't settle, with states that do.

The label is the intent whose cause holds in the state, so it is computed from the catalog, not
guessed. M5 trains with and without state and compares on this slice.
"""

import argparse
import json
import random
from collections.abc import Sequence
from pathlib import Path

from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.labels import HELD_OUT, VAGUE
from unstuk_ml.record import Record
from unstuk_ml.sheet import parse_sheet

Pair = tuple[str, str]

# Pairs whose complaints are often ambiguous from the words and whose causes differ.
PAIRS: tuple[Pair, ...] = (
    ("no_internet", "wifi_no_load"),
    ("phone_not_ringing", "notifications_missing"),
    ("no_internet", "notifications_missing"),
    ("screen_too_dim", "colours_wrong"),
    ("talkback_on", "colours_wrong"),
)
# Not a phone state: decided by the gate, not by diagnosis.
NOT_STATE = frozenset({"always"})
TRAIN_SHARE = 0.7
SEED = 13


def excluded_checks(catalog: Catalog) -> frozenset[str]:
    """Checks of held-out intents (invariant 9) and pseudo-checks that aren't phone state."""
    return frozenset(c for i in HELD_OUT for c in catalog.causes[i]) | NOT_STATE


def deciding_checks(catalog: Catalog, pair: Pair) -> tuple[list[str], list[str]]:
    """Each side's causes that are not causes of the other side and not excluded."""
    a, b = (set(catalog.causes[i]) - excluded_checks(catalog) for i in pair)
    return sorted(a - b), sorted(b - a)


def distractors(catalog: Catalog, pair: Pair) -> list[str]:
    """Checks that say nothing about either side, so "any check means label A" can't be learned."""
    involved = {c for i in pair for c in catalog.causes[i]}
    return sorted(catalog.checks - involved - excluded_checks(catalog))


def build(texts: dict[Pair, list[str]], catalog: Catalog, seed: int = SEED) -> list[Record]:
    rng = random.Random(seed)
    records: list[Record] = []
    for number, pair in enumerate(PAIRS, 1):
        a_checks, b_checks = deciding_checks(catalog, pair)
        if not a_checks or not b_checks:
            continue
        noise = distractors(catalog, pair)
        batch = f"state-p{number}"
        for n, text in enumerate(texts.get(pair, []), 1):
            states = [
                (rng.choice(a_checks), [pair[0]], "a"),
                (rng.choice(b_checks), [pair[1]], "b"),
            ]
            if n % 3 == 0:
                states.append((None, list(pair), "none"))
            for check, labels, side in states:
                state = [check] if check else []
                if rng.random() < 0.5:
                    state.append(rng.choice(noise))
                records.append(
                    Record(
                        id=f"{batch}-{n:02d}-{side}",
                        text=text,
                        labels=labels,
                        tags=[VAGUE] if side == "none" else [],
                        source="generated",
                        generator="claude-fresh",
                        batch=batch,
                        state=sorted(state),
                    )
                )
    return records


def split_by_text(records: Sequence[Record], seed: int = SEED) -> tuple[list[Record], list[Record]]:
    """A text and all its states land on the same side."""
    rng = random.Random(seed)
    test_texts: set[str] = set()
    for batch in sorted({r.batch for r in records}):
        texts = sorted({r.text for r in records if r.batch == batch})
        rng.shuffle(texts)
        test_texts |= set(texts[round(len(texts) * TRAIN_SHARE) :])
    train = [r for r in records if r.text not in test_texts]
    test = [r for r in records if r.text in test_texts]
    return train, test


def ambiguous(texts: dict[Pair, list[str]], blind: dict[str, list[str]]) -> dict[Pair, list[str]]:
    """Keeps only texts a blind labeller couldn't settle to one side of their pair."""
    return {
        pair: [t for t in kept if set(pair) <= set(blind.get(t, []))]
        for pair, kept in texts.items()
    }


def read_texts(sheet: Path) -> dict[Pair, list[str]]:
    texts: dict[Pair, list[str]] = {}
    for line in parse_sheet(sheet.read_text(encoding="utf-8")):
        pair = (line.labels[0], line.labels[1])
        if pair not in PAIRS:
            raise ValueError(f"{pair} is not a state-slice pair")
        texts.setdefault(pair, []).append(line.text)
    return texts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the state slice.")
    commands = parser.add_subparsers(dest="command", required=True)
    blind = commands.add_parser("blind", help="write key<TAB>text for a blind labeller")
    blind.add_argument("sheet", type=Path)
    blind.add_argument("out", type=Path)
    make = commands.add_parser("build", help="keep ambiguous texts and write the slice")
    make.add_argument("sheet", type=Path)
    make.add_argument("labels", type=Path, help="the blind labeller's JSONL: key and labels")
    make.add_argument("out", type=Path, help="folder for train.jsonl and test.jsonl")
    args = parser.parse_args()

    texts = read_texts(args.sheet)
    flat = [t for pair in PAIRS for t in texts.get(pair, [])]
    keys = {f"s{n:03d}": t for n, t in enumerate(flat, 1)}
    if args.command == "blind":
        args.out.write_text("".join(f"{k}\t{t}\n" for k, t in keys.items()), encoding="utf-8")
        print(f"{len(keys)} texts in {args.out}")
        return
    rows = [json.loads(line) for line in args.labels.read_text(encoding="utf-8").splitlines()]
    labels_by_text = {keys[r["key"]]: r["labels"] for r in rows}
    kept = ambiguous(texts, labels_by_text)
    train, test = split_by_text(build(kept, load_catalog()))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, records in (("train", train), ("test", test)):
        path = args.out / f"{name}.jsonl"
        lines = (json.dumps(r.model_dump(exclude_none=True), ensure_ascii=False) for r in records)
        path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    kept_count = sum(map(len, kept.values()))
    print(
        f"{kept_count} of {len(flat)} texts kept; {len(train)} train and {len(test)} test records"
    )
