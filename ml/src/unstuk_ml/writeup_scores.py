"""Per-line test scores for the write-up's figures (M9 spec section 2).

Every frozen decider whose weights are still on this machine is scored on the test as its own
report scored it, checked against the
numbers its results doc published, and cached with ids and probabilities only. Nothing is chosen
here: a mismatch stops the run before anything is written.
"""

import argparse
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from unstuk_ml.baseline_report import load_test
from unstuk_ml.calibrated_rung import SETTINGS as M6_SETTINGS
from unstuk_ml.calibrated_rung import Settings as M6Settings
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import FLOAT_GRAPH
from unstuk_ml.decision_scoring import Temperatures, scored
from unstuk_ml.decision_test import baselines, offered
from unstuk_ml.encoder import download
from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import (
    GateLines,
    Metric,
    Scored,
    confident_and_wrong,
    expected_calibration_error,
    in_scope_accuracy,
)
from unstuk_ml.fine_tuning import RUNS_DIR, sha256
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.keyword_matcher import load_matcher
from unstuk_ml.quantized_test import load_shipped
from unstuk_ml.record import Record
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.zero_shot import ZERO_SHOT

CACHE_DIR = Path(__file__).resolve().parents[2] / "cache" / "writeup"
CHECKED: tuple[tuple[str, Metric], ...] = (
    ("in-scope accuracy", in_scope_accuracy),
    ("confident and wrong", confident_and_wrong),
    ("ECE", expected_calibration_error),
)


@dataclass(frozen=True)
class Published:
    """A decider's test numbers as its results doc printed them, to a tenth of a point."""

    in_scope_accuracy: float
    confident_and_wrong: float
    ece: float

    def values(self) -> tuple[float, float, float]:
        return self.in_scope_accuracy, self.confident_and_wrong, self.ece


@dataclass(frozen=True)
class Entry:
    key: str
    title: str
    published: Published
    """From m4-results.md (the four baselines) and m7-results.md (float and int8)."""


ENTRIES = (
    Entry("keyword", "Keyword", Published(0.402, 0.087, 0.226)),
    Entry("tfidf", "TF-IDF + LR", Published(0.649, 0.019, 0.174)),
    Entry("encoder", "Frozen bge-small + LR", Published(0.700, 0.038, 0.123)),
    Entry("zero-shot", "Zero-shot bge-small", Published(0.739, 0.038, 0.061)),
    Entry("m6-float", "M6 float graph", Published(0.895, 0.030, 0.026)),
    Entry("int8", "int8 graph (ships)", Published(0.893, 0.030, 0.036)),
)


def mismatches(items: Sequence[Scored], published: Published) -> list[str]:
    """Each checked metric that doesn't print as its results doc printed it."""
    return [
        f"{name} {metric(items):.1%}, published {expected:.1%}"
        for (name, metric), expected in zip(CHECKED, published.values(), strict=True)
        if f"{metric(items):.1%}" != f"{expected:.1%}"
    ]


def save(items: Sequence[Scored], path: Path) -> None:
    gates = {s.gate for s in items}
    if len(gates) != 1:
        raise ValueError("a decider's lines must all sit behind one gate")
    payload = {
        "gate": asdict(gates.pop()),
        "probabilities": {s.record.id: s.probabilities for s in items},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def load(path: Path, lines: Sequence[Record]) -> list[Scored]:
    """The cached scores, joined back onto the test lines they were made from."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    probabilities: dict[str, dict[str, float]] = payload["probabilities"]
    if set(probabilities) != {r.id for r in lines}:
        raise ValueError(f"{path} was scored on other lines; run unstuk-writeup-scores again")
    gate = GateLines(**payload["gate"])
    return [Scored(r, probabilities[r.id], gate) for r in lines]


def load_all(cache_dir: Path = CACHE_DIR) -> dict[str, list[Scored]]:
    lines = load_test()
    return {e.key: load(cache_dir / f"{e.key}.json", lines) for e in ENTRIES}


def scorers(lines: Sequence[Record]) -> dict[str, Callable[[], list[Scored]]]:
    """How each decider's report scored it, keyed as in `ENTRIES`."""
    catalog = load_catalog()
    intents = offered(catalog)

    def keyword() -> list[Scored]:
        matcher = load_matcher()
        return [Scored(r, matcher.choose(r.text)) for r in lines]

    def m6_float() -> list[Scored]:
        shipped, _, _ = load_shipped()
        m6 = M6Settings.model_validate_json(M6_SETTINGS.read_text(encoding="utf-8"))
        graph = RUNS_DIR / shipped.run / FLOAT_GRAPH
        if sha256(graph) != shipped.float_sha256:
            raise ValueError("the float graph differs from the one the settings name")
        decider = GraphDecider(graph, decision_tokenizer(download()[1]), shipped.scale)
        temperatures = Temperatures(m6.choice_temperature, m6.noul_temperature or 1.0)
        logits = decider.logits(lines, intents, catalog)
        gate = GateLines(**m6.lines)
        return [replace(s, gate=gate) for s in scored(logits, lines, intents, temperatures)]

    def int8() -> list[Scored]:
        settings, gate, decider = load_shipped()
        temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature)
        logits = decider.logits(lines, intents, catalog)
        return [replace(s, gate=gate) for s in scored(logits, lines, intents, temperatures)]

    scored_baselines: dict[str, list[Scored]] = {}

    def baseline(title: str) -> Callable[[], list[Scored]]:
        def run() -> list[Scored]:
            # The three M4 baselines are scored together, once.
            if not scored_baselines:
                scored_baselines.update(baselines(lines))
            return scored_baselines[title]

        return run

    return {
        "keyword": keyword,
        "tfidf": baseline(TFIDF.decider.title),
        "encoder": baseline(ENCODER.decider.title),
        "zero-shot": baseline(ZERO_SHOT.title),
        "m6-float": m6_float,
        "int8": int8,
    }


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    lines = load_test()
    score = scorers(lines)
    results = {}
    for entry in ENTRIES:
        items = score[entry.key]()
        wrong = mismatches(items, entry.published)
        if wrong:
            raise SystemExit(f"{entry.title} doesn't reproduce its report: {'; '.join(wrong)}")
        results[entry.key] = items
        print(f"{entry.title}: matches its report")
    for key, items in results.items():
        save(items, CACHE_DIR / f"{key}.json")
    print(f"cached {len(results)} deciders' scores on {len(lines)} test lines in {CACHE_DIR}")
