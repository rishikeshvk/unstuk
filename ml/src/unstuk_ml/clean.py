"""The cleaning pipeline (M3 spec section 6): raw batches in, train and dev out, drops explained."""

import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

from unstuk_ml import decisions, duplicates, label_issues, shortcuts, split
from unstuk_ml.catalog import load_catalog
from unstuk_ml.normalize import normalize
from unstuk_ml.record import Record
from unstuk_ml.report import Cleaning, Leakage, render
from unstuk_ml.validate import DEFAULT_DATA_DIR, validate

REPO = DEFAULT_DATA_DIR.parent
GUIDE = REPO / "docs" / "m3-labelling-guide.md"
REPORT = REPO / "ml" / "reports" / "clean.md"
NEAR_DUPLICATE = 0.9
LEAKAGE = 0.8
LEAKAGE_SHOWN = (0.7, 0.8, 0.9)
SEED = 3


def run(data: Path = DEFAULT_DATA_DIR) -> Cleaning:
    problems = validate(data, load_catalog())
    if problems:
        raise ValueError(f"{len(problems)} validation problems; run unstuk-validate first")
    out = data / "clean"
    pool = _read(
        [*sorted((data / "seed").glob("*.jsonl")), *sorted((data / "raw").rglob("*.jsonl"))]
    )
    test = _read(sorted((data / "test").glob("*.jsonl")))
    stages = [("raw pool", len(pool))]

    decided = decisions.load(out / "decisions.jsonl")
    pool, dropped = decisions.apply(pool, decided)
    stages.append(("after review decisions", len(pool)))
    pool = [r.model_copy(update={"text": normalize(r.text)}) for r in pool]
    pool, more = duplicates.exact_duplicates(pool)
    dropped += more
    stages.append(("after exact duplicates", len(pool)))
    pool, more = duplicates.near_duplicates(pool, NEAR_DUPLICATE)
    dropped += more
    stages.append((f"after near duplicates (same label, {NEAR_DUPLICATE})", len(pool)))
    leakage = _leakage(pool, test)
    more = duplicates.leaking(pool, test, LEAKAGE)
    leaked = {d.record.id for d in more}
    dropped += more
    guide = _guide_examples()
    dropped += [
        duplicates.Drop(r, "a labelling-guide example") for r in pool if r.text.lower() in guide
    ]
    pool = [r for r in pool if r.id not in leaked and r.text.lower() not in guide]
    stages.append((f"after test leakage ({LEAKAGE}) and guide examples", len(pool)))

    # A line someone already decided on doesn't go back to the review queue.
    flags = [f for f in label_issues.flag(pool, SEED) if f.record.id not in decided]
    train, dev = split.split(pool, SEED)
    return Cleaning(
        stages,
        dropped,
        leakage,
        flags,
        shortcuts.profiles(pool),
        shortcuts.giveaways(pool),
        train,
        dev,
    )


def write(result: Cleaning, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write(out / "train.jsonl", (r.model_dump(exclude_none=True) for r in result.train))
    _write(out / "dev.jsonl", (r.model_dump(exclude_none=True) for r in result.dev))
    _write(
        out / "review.jsonl",
        (
            {
                "id": f.record.id,
                "text": f.record.text,
                "labels": f.record.labels,
                "predicted": f.predicted,
                "confidence": round(f.confidence, 3),
                "batch": f.record.batch,
            }
            for f in result.flags
        ),
    )
    _write(
        out / "dropped.jsonl",
        ({"id": d.record.id, "text": d.record.text, "reason": d.reason} for d in result.dropped),
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render(result), encoding="utf-8")


def _leakage(pool: Sequence[Record], test: Sequence[Record]) -> Leakage:
    best = duplicates.similarity([r.text for r in pool], [t.text for t in test])
    counts = {t: int((best[:, 0] >= t).sum()) for t in LEAKAGE_SHOWN}
    order = best[:, 0].argsort()[::-1][:8]
    examples = [(pool[i].text, test[int(best[i, 1])].text, float(best[i, 0])) for i in order]
    return Leakage(counts, examples)


def _guide_examples() -> set[str]:
    quoted = re.findall(r'"([^"]{3,})"', GUIDE.read_text(encoding="utf-8"))
    return {normalize(q).lower() for q in quoted}


def _read(paths: Iterable[Path]) -> list[Record]:
    return [
        Record.model_validate_json(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write(path: Path, rows: Iterable[object]) -> None:
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    result = run()
    write(result, DEFAULT_DATA_DIR / "clean")
    sizes = f"train {len(result.train)}, dev {len(result.dev)}, flagged {len(result.flags)}"
    print(f"{sizes}; see {REPORT}")
