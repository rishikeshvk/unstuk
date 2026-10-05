"""Freezes the proxy test set: its files' hashes go in a lock, and any later change is a problem.

The test set is built before any training data, so no score can have been tuned to it (M3 spec
section 5).
"""

import hashlib
import json
import sys
from pathlib import Path

LOCK = "test.lock"


def file_hashes(test_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(test_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(test_dir.rglob("*.jsonl"))
    }


def freeze(test_dir: Path) -> None:
    lock = test_dir / LOCK
    if lock.exists():
        raise FileExistsError(f"{lock} exists; the test set is frozen already")
    lock.write_text(json.dumps(file_hashes(test_dir), indent=2) + "\n", encoding="utf-8")


def frozen_changes(test_dir: Path) -> list[str]:
    """What differs from the lock; empty when the lock matches or the set isn't frozen yet."""
    lock = test_dir / LOCK
    if not lock.exists():
        return []
    locked: dict[str, str] = json.loads(lock.read_text(encoding="utf-8"))
    now = file_hashes(test_dir)
    changes = [
        f"{name} changed after freezing"
        for name in locked
        if name in now and now[name] != locked[name]
    ]
    changes += [f"{name} removed after freezing" for name in locked if name not in now]
    changes += [f"{name} added after freezing" for name in now if name not in locked]
    return changes


def main() -> None:
    test_dir = Path(sys.argv[1])
    freeze(test_dir)
    print(f"froze {len(file_hashes(test_dir))} files in {test_dir / LOCK}")
