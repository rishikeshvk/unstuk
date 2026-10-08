"""Exports M6's calibrated model as the graph the app runs (M7 spec section 1).

The float graph is written beside its checkpoint, then checked against PyTorch on every dev line,
clear and vague, with every catalog intent offered as the app offers them.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from unstuk_ml import rung
from unstuk_ml.calibrated_rung import SETTINGS, Settings
from unstuk_ml.calibrated_test import calibrated_model
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import export, scale
from unstuk_ml.decision_scoring import Logits, decision_logits
from unstuk_ml.decision_test import offered
from unstuk_ml.encoder import download
from unstuk_ml.fine_tuning import RUNS_DIR
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.record import Record, read_records
from unstuk_ml.validate import DEFAULT_DATA_DIR

FLOAT_GRAPH = "decision.float.onnx"
# Spec section 1: float ONNX must give PyTorch's logits to this.
PARITY_TOLERANCE = 1e-4


@dataclass(frozen=True)
class Parity:
    choice: float
    noul: float
    """The largest absolute difference in each head's logits."""

    @property
    def passes(self) -> bool:
        return max(self.choice, self.noul) <= PARITY_TOLERANCE


def parity(expected: Logits, actual: Logits) -> Parity:
    return Parity(
        choice=float(np.abs(expected.choice - actual.choice).max()),
        noul=float(np.abs(expected.out_of_scope - actual.out_of_scope).max()),
    )


def dev_lines() -> list[Record]:
    return rung.read_clean("dev") + read_records(DEFAULT_DATA_DIR / "vague" / "dev.jsonl")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    model = calibrated_model(settings)
    graph = RUNS_DIR / settings.run / FLOAT_GRAPH
    export(model, graph)

    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    lines, intents = dev_lines(), offered(catalog)
    expected = decision_logits(model, lines, intents, catalog, tokenizer)
    actual = GraphDecider(graph, tokenizer, scale(model)).logits(lines, intents, catalog)
    result = parity(expected, actual)
    print(
        f"{graph} ({_megabytes(graph):.1f} MB): on {len(lines)} dev lines the largest logit "
        f"differences are {result.choice:.2e} (Choice) and {result.noul:.2e} (Noul)"
    )
    if not result.passes:
        raise SystemExit(f"the float graph differs from PyTorch by more than {PARITY_TOLERANCE}")


def _megabytes(path: Path) -> float:
    return path.stat().st_size / 1e6
