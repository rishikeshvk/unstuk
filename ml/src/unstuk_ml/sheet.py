"""Plain-text sheets that people and chat apps write complaints in, turned into records.

A sheet is a list of sections. A header names the labels, and optionally tags for its lines:

    ## phone_not_ringing
    ## no_internet, screen_too_dim | multi

Each following line is one complaint, optionally ending in its own tags: `net gone | typo`.
Blank lines and lines starting with `#` (but not `##`) are ignored.
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from unstuk_ml.record import Record

HEADER = "## "
COMMENT = "#"
TAG_SEPARATOR = "|"


@dataclass(frozen=True)
class SheetLine:
    text: str
    labels: list[str]
    tags: list[str]


def parse_sheet(text: str) -> list[SheetLine]:
    lines: list[SheetLine] = []
    labels: list[str] | None = None
    header_tags: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith(HEADER):
            labels, header_tags = _split_header(line.removeprefix(HEADER))
        elif line and not line.startswith(COMMENT):
            if labels is None:
                raise ValueError(f"line {number}: complaint before any '## label' header")
            complaint, line_tags = _split_tags(line)
            lines.append(SheetLine(complaint, labels, _merge(header_tags, line_tags)))
    return lines


def to_records(lines: list[SheetLine], source: str, generator: str, batch: str) -> list[Record]:
    return [
        Record.model_validate(
            {
                "id": f"{batch}-{index:03d}",
                "text": line.text,
                "labels": line.labels,
                "tags": line.tags,
                "source": source,
                "generator": generator,
                "batch": batch,
            }
        )
        for index, line in enumerate(lines, start=1)
    ]


def _split_header(header: str) -> tuple[list[str], list[str]]:
    labels, tags = _split_tags(header)
    return [label.strip() for label in labels.split(",") if label.strip()], tags


def _split_tags(line: str) -> tuple[str, list[str]]:
    text, _, tags = line.partition(TAG_SEPARATOR)
    return text.strip(), tags.split()


def _merge(first: list[str], second: list[str]) -> list[str]:
    return first + [tag for tag in second if tag not in first]


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn a complaint sheet into a JSONL data file.")
    parser.add_argument("sheet", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()

    lines = parse_sheet(args.sheet.read_text(encoding="utf-8"))
    records = to_records(lines, args.source, args.generator, args.batch)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record.model_dump(exclude_none=True), ensure_ascii=False) + "\n")
    print(f"{len(records)} records written to {args.out}")
