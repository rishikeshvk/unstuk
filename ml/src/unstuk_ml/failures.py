"""The shipped graph's test mistakes, each coded with one cause (M9 spec section 4).

The causes were fixed in the spec before any mistake was read; a mistake that fits none is `other`.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict

from unstuk_ml.evaluate import Scored
from unstuk_ml.validate import DEFAULT_DATA_DIR

FAILURES = DEFAULT_DATA_DIR / "failures" / "test-int8.jsonl"
Cause = Literal[
    "lexical_pull",
    "needs_state",
    "collision",
    "held_out",
    "two_problems",
    "debatable_label",
    "wording",
    "other",
]
CAUSES: tuple[Cause, ...] = get_args(Cause)


class Failure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    cause: Cause
    note: str


def mistakes(items: Sequence[Scored]) -> list[Scored]:
    """Clear lines whose top answer isn't a label: a wrong intent, a decline, or an answered
    out-of-scope line. Vague lines have no single right answer, so they're left out."""
    return [s for s in items if not s.vague and not s.correct]


def load_failures(items: Sequence[Scored], path: Path = FAILURES) -> list[tuple[Scored, Failure]]:
    """Each mistake with its code; refused unless every mistake has exactly one."""
    failures = [
        Failure.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    coded = {f.id: f for f in failures}
    wrong = {s.record.id: s for s in mistakes(items)}
    if len(coded) != len(failures) or coded.keys() != wrong.keys():
        missing = sorted(wrong.keys() - coded.keys())
        extra = sorted(coded.keys() - wrong.keys())
        raise ValueError(f"{path} must code each mistake once; missing {missing}, extra {extra}")
    return [(wrong[i], coded[i]) for i in sorted(wrong)]
