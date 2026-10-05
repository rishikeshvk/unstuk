"""Checks every data file against the record format and the catalog."""

import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.freeze import frozen_changes
from unstuk_ml.labels import HELD_OUT, OUT_OF_SCOPE
from unstuk_ml.record import Record

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# Real messages are never training data (invariant 9); only the test set may hold held-out intents.
REAL_DIR = "real"
TEST_DIR = "test"


@dataclass(frozen=True)
class Place:
    path: Path
    line: int | None = None

    def __str__(self) -> str:
        return str(self.path) if self.line is None else f"{self.path}:{self.line}"


@dataclass(frozen=True)
class Problem:
    place: Place
    message: str

    def __str__(self) -> str:
        return f"{self.place}: {self.message}"


def validate(data_dir: Path, catalog: Catalog) -> list[Problem]:
    problems: list[Problem] = []
    first_seen: dict[str, Place] = {}
    for path in _data_files(data_dir):
        allows_held_out = path.relative_to(data_dir).parts[0] == TEST_DIR
        for place, line in _lines(path):
            try:
                record = Record.model_validate_json(line)
            except ValidationError as error:
                problems += [Problem(place, _describe(e)) for e in error.errors()]
                continue
            for message in _catalog_problems(record, catalog, allows_held_out):
                problems.append(Problem(place, message))
            if record.id in first_seen:
                problems.append(
                    Problem(place, f"duplicate id {record.id}, first at {first_seen[record.id]}")
                )
            else:
                first_seen[record.id] = place
    test_dir = data_dir / TEST_DIR
    problems += [Problem(Place(test_dir), change) for change in frozen_changes(test_dir)]
    return problems


def _data_files(data_dir: Path) -> Iterator[Path]:
    for path in sorted(data_dir.rglob("*.jsonl")):
        if path.relative_to(data_dir).parts[0] != REAL_DIR:
            yield path


def _lines(path: Path) -> Iterator[tuple[Place, str]]:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            yield Place(path, number), line


def _describe(error: ErrorDetails) -> str:
    where = ".".join(str(part) for part in error["loc"])
    return f"{where}: {error['msg']}" if where else error["msg"]


def _catalog_problems(record: Record, catalog: Catalog, allows_held_out: bool) -> Iterator[str]:
    for label in record.labels:
        if label != OUT_OF_SCOPE and label not in catalog.intents:
            yield f"unknown label {label}"
        if label in HELD_OUT and not allows_held_out:
            yield f"held-out intent {label} outside {TEST_DIR}/"
    for check in record.state or []:
        if check not in catalog.checks:
            yield f"unknown check {check} in state"


def main() -> None:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_DIR
    if not data_dir.is_dir():
        sys.exit(f"{data_dir} is not a directory")
    problems = validate(data_dir, load_catalog())
    for problem in problems:
        print(problem)
    print(f"{len(problems)} problems in {data_dir}")
    sys.exit(1 if problems else 0)
