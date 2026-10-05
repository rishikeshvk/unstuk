"""The hand audit (M3 spec section 3): a blind second labeller checks clean training lines."""

import argparse
import json
import random
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

from unstuk_ml.record import Record

SIZE = 200
SEED = 11


@dataclass(frozen=True)
class Agreement:
    agreed: int
    total: int
    kappa: float
    """Cohen's kappa: agreement corrected for what two labellers would reach by chance."""

    @property
    def share(self) -> float:
        return self.agreed / self.total


def sample(records: Sequence[Record], size: int = SIZE, seed: int = SEED) -> list[Record]:
    return random.Random(seed).sample(list(records), size)


def agreement(given: Sequence[Sequence[str]], blind: Sequence[Sequence[str]]) -> Agreement:
    """A line agrees when the blind labeller's main label is among the given labels."""
    agreed = sum(b[0] in g for g, b in zip(given, blind, strict=True))
    kappa = float(cohen_kappa_score([g[0] for g in given], [b[0] for b in blind]))
    return Agreement(agreed, len(given), kappa)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample lines for a blind audit, or score one.")
    commands = parser.add_subparsers(dest="command", required=True)
    draw = commands.add_parser("sample")
    draw.add_argument("train", type=Path)
    draw.add_argument("out", type=Path, help="audit lines with their given labels")
    draw.add_argument("blind", type=Path, help="key<TAB>text only, for the labeller")
    score = commands.add_parser("score")
    score.add_argument("audit", type=Path)
    score.add_argument("labels", type=Path, help="the labeller's JSONL: key and labels")
    args = parser.parse_args()

    if args.command == "sample":
        lines = args.train.read_text(encoding="utf-8").splitlines()
        chosen = sample([Record.model_validate_json(line) for line in lines])
        rows = [
            {"key": f"a{i:03d}", "id": r.id, "text": r.text, "labels": r.labels}
            for i, r in enumerate(chosen, 1)
        ]
        args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        args.blind.write_text("".join(f"{r['key']}\t{r['text']}\n" for r in rows))
        print(f"{len(rows)} lines in {args.out}; blind copy in {args.blind}")
        return
    audit = {r["key"]: r for r in map(json.loads, args.audit.read_text().splitlines())}
    labels = {r["key"]: r["labels"] for r in map(json.loads, args.labels.read_text().splitlines())}
    keys = sorted(audit)
    result = agreement([audit[k]["labels"] for k in keys], [labels[k] for k in keys])
    print(
        f"agreement {result.agreed}/{result.total} = {result.share:.1%}, kappa {result.kappa:.3f}"
    )
