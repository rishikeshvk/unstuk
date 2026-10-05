"""Out-of-scope commands sampled from Google's Mobile Actions dataset (CC-BY-4.0).

None of its tools is a fix Unstuk makes, so its requests are out of scope, in a polished
assistant-command style that the generated data lacks (M3 spec section 2).
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.record import Record

# Wi-Fi settings sit too close to the Wi-Fi intents; calendar requests are full of dates and times, which
# would teach "time words mean out of scope" and bias the held-out wrong_time intent.
EXCLUDED_TOOLS = frozenset({"open_wifi_settings", "create_calendar_event"})
PER_TOOL = {"train": 50, "eval": 10}
SEED = 9


def sample(rows: list[dict[str, Any]]) -> list[Record]:
    by_split_and_tool: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        tool, text = _single_call(row)
        if tool is not None and text is not None and tool not in EXCLUDED_TOOLS:
            by_split_and_tool[(row["metadata"], tool)].append(text)
    rng = random.Random(SEED)
    records: list[Record] = []
    for (split, _tool), texts in sorted(by_split_and_tool.items()):
        if split not in PER_TOOL:
            continue
        batch = f"mobile-actions-{split}"
        for text in rng.sample(texts, PER_TOOL[split]):
            records.append(_record(f"{batch}-{len(records):03d}", text, batch))
    return records


def _single_call(row: dict[str, Any]) -> tuple[str | None, str | None]:
    calls = [call for m in row["messages"] for call in (m.get("tool_calls") or [])]
    users = [m["content"] for m in row["messages"] if m.get("role") == "user"]
    if len(calls) != 1 or len(users) != 1:
        return None, None
    return calls[0]["function"]["name"], users[0]


def _record(record_id: str, text: str, batch: str) -> Record:
    return Record(
        id=record_id,
        text=text,
        labels=[OUT_OF_SCOPE],
        tags=["oos_near"],
        source="mobile_actions",
        generator="google",
        batch=batch,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample out-of-scope commands from Mobile Actions."
    )
    parser.add_argument("dataset", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    records = sample(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out:
        for record in records:
            out.write(json.dumps(record.model_dump(exclude_none=True), ensure_ascii=False) + "\n")
    print(f"{len(records)} records written to {args.out}")
