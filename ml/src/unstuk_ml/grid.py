"""The diversity grid: each training batch is written for one cell (M3 spec section 5)."""

import argparse
import json
import random
from pathlib import Path

AXES: dict[str, tuple[str, ...]] = {
    "age": ("teen", "adult", "senior"),
    "comfort": ("low", "medium"),
    "variety": ("indian", "british", "american", "second_language"),
    "style": ("plain", "question", "story", "frustrated", "dictated", "terse"),
    "typos": ("none", "some", "many"),
}

Cell = dict[str, str]


def plan_batches(count: int, seed: int) -> list[Cell]:
    """Cells where every value of every axis appears equally often, give or take one."""
    rng = random.Random(seed)
    columns: dict[str, list[str]] = {}
    for axis, values in AXES.items():
        column = [values[i % len(values)] for i in range(count)]
        rng.shuffle(column)
        columns[axis] = column
    return [{axis: columns[axis][i] for axis in AXES} for i in range(count)]


def check_cell(cell: Cell) -> None:
    for axis, value in cell.items():
        if axis not in AXES:
            raise ValueError(f"unknown axis {axis}")
        if value not in AXES[axis]:
            raise ValueError(f"unknown {axis} value {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan training batches over the diversity grid.")
    parser.add_argument("count", type=int)
    parser.add_argument("out", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    plan = {f"train-{i:02d}": cell for i, cell in enumerate(plan_batches(args.count, args.seed), 1)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"{len(plan)} batches planned in {args.out}")
