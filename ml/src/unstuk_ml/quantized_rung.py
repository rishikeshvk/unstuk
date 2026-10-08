"""The int8 graph, chosen on dev (M7 spec sections 2 and 3).

Tries run in the spec's order and stop at the first that passes the dev check: every weight in
int8, then the embedding tables left in float. Temperatures are refitted for the int8 graph, and
M6's rule re-tunes the gate's lines on its dev scores, since the app ships this graph.
"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from pydantic import BaseModel

from unstuk_ml import rung
from unstuk_ml.calibrated_rung import SETTINGS as M6_SETTINGS
from unstuk_ml.calibrated_rung import Settings as M6Settings
from unstuk_ml.calibrated_test import calibrated_model
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import scale
from unstuk_ml.decision_scoring import Temperatures, fit_temperatures, scored
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import GATE_FILE, Scored, load_gate
from unstuk_ml.export import FLOAT_GRAPH
from unstuk_ml.fine_tuning import RUNS_DIR, sha256, source_commit
from unstuk_ml.folds import trained_intents
from unstuk_ml.gate_tuning import tune
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.quantization import WITH_EMBEDDINGS, WITHOUT_EMBEDDINGS, dev_check, quantize
from unstuk_ml.record import read_records
from unstuk_ml.validate import DEFAULT_DATA_DIR

SETTINGS = rung.SETTINGS_DIR / "quantized.json"
TRIES = (("decision.int8.onnx", WITH_EMBEDDINGS), ("decision.int8-matmul.onnx", WITHOUT_EMBEDDINGS))


class TryRow(BaseModel):
    graph: str
    ops: list[str]
    megabytes: float
    top_agreement: float
    macro_f1_change: float
    ece_change: float
    outcome_agreement: float
    passes: bool


@dataclass(frozen=True)
class DevScores:
    clear: list[Scored]
    vague: list[Scored]
    temperatures: Temperatures


class Settings(BaseModel):
    run: str
    """M6's run, whose checkpoint the graphs come from."""
    float_sha256: str
    graph: str
    graph_sha256: str
    ops: list[str]
    """The ops whose weights are int8."""
    scale: float
    choice_temperature: float
    noul_temperature: float
    lines: dict[str, float]
    """Re-tuned on the int8 graph's dev scores, as written to `catalog/gate.json`."""
    automatic_wrong: float
    clear_clarified: float
    vague_handled: float
    commit: str
    tries: list[TryRow]


def choose() -> Settings:
    m6 = M6Settings.model_validate_json(M6_SETTINGS.read_text(encoding="utf-8"))
    directory = RUNS_DIR / m6.run
    float_graph = directory / FLOAT_GRAPH
    if not float_graph.exists():
        raise SystemExit(f"{float_graph} is missing; run `uv run unstuk-export` first")
    catalog = load_catalog()
    intents = trained_intents(catalog)
    tokenizer = decision_tokenizer(download()[1])
    clear = rung.read_clean("dev")
    vague = read_records(DEFAULT_DATA_DIR / "vague" / "dev.jsonl")
    factor = scale(calibrated_model(m6))
    gate = load_gate()

    def scores(graph: Path, temperatures: Temperatures | None) -> DevScores:
        """Temperatures are refitted on clear dev when none are given."""
        decider = GraphDecider(graph, tokenizer, factor)
        clear_logits = decider.logits(clear, intents, catalog)
        vague_logits = decider.logits(vague, intents, catalog)
        fitted = temperatures or fit_temperatures(clear_logits, clear, intents)
        return DevScores(
            [replace(s, gate=gate) for s in scored(clear_logits, clear, intents, fitted)],
            [replace(s, gate=gate) for s in scored(vague_logits, vague, intents, fitted)],
            fitted,
        )

    base = scores(float_graph, Temperatures(m6.choice_temperature, m6.noul_temperature or 1.0))
    tries = []
    for name, ops in TRIES:
        graph = directory / name
        quantize(float_graph, graph, ops)
        int8 = scores(graph, None)
        check = dev_check(base.clear, int8.clear, base.vague, int8.vague)
        tries.append(
            TryRow(
                graph=name,
                ops=list(ops),
                megabytes=graph.stat().st_size / 1e6,
                passes=check.passes,
                **asdict(check),
            )
        )
        if check.passes:
            tuning = tune(int8.clear, int8.vague)
            return Settings(
                run=m6.run,
                float_sha256=sha256(float_graph),
                graph=name,
                graph_sha256=sha256(graph),
                ops=list(ops),
                scale=factor,
                choice_temperature=int8.temperatures.choice,
                noul_temperature=int8.temperatures.noul,
                lines=asdict(tuning.lines),
                automatic_wrong=tuning.automatic_wrong,
                clear_clarified=tuning.clear_clarified,
                vague_handled=tuning.vague_handled,
                commit=source_commit(),
                tries=tries,
            )
    _print_tries(tries)
    raise SystemExit("no int8 graph passed the dev check; by the stop rule M7 ships fp16")


def write(settings: Settings) -> None:
    SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
    GATE_FILE.write_text(json.dumps(settings.lines, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = choose()
    _print_tries(settings.tries)
    print(
        f"chose {settings.graph}: temperatures {settings.choice_temperature:.4f} (Choice), "
        f"{settings.noul_temperature:.4f} (Noul); gate lines {settings.lines}"
    )
    write(settings)


def _print_tries(tries: Sequence[TryRow]) -> None:
    for row in tries:
        print(
            f"{row.graph} ({row.megabytes:.1f} MB, int8 {'+'.join(row.ops)}): top-1 agreement "
            f"{row.top_agreement:.2%}, macro-F1 {row.macro_f1_change:+.2%}, ECE "
            f"{row.ece_change:+.2%}, gate outcomes agree {row.outcome_agreement:.2%}: "
            f"{'passes' if row.passes else 'fails'}"
        )
