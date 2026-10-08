"""What the phone must answer on every dev line (M7 spec section 9): Python's int8 probabilities.

Each line carries its complaint and its state text as the app renders it, so the instrumented test
can run the app's whole decision path and compare. Dev only, clear and vague; never the test.
"""

import argparse
import json
from pathlib import Path

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_scoring import Temperatures, scored
from unstuk_ml.decision_test import offered
from unstuk_ml.encoder import download
from unstuk_ml.export import dev_lines
from unstuk_ml.fine_tuning import RUNS_DIR
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.quantized_rung import SETTINGS, Settings
from unstuk_ml.training_examples import render_state
from unstuk_ml.validate import DEFAULT_DATA_DIR

FIXTURE = (
    DEFAULT_DATA_DIR.parent
    / "android"
    / "app"
    / "src"
    / "androidTest"
    / "assets"
    / "dev-decisions.jsonl"
)


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    lines, intents = dev_lines(), offered(catalog)
    decider = GraphDecider(RUNS_DIR / settings.run / settings.graph, tokenizer, settings.scale)
    temperatures = Temperatures(settings.choice_temperature, settings.noul_temperature)
    items = scored(decider.logits(lines, intents, catalog), lines, intents, temperatures)
    write(
        FIXTURE,
        [
            {
                "id": item.record.id,
                "complaint": item.record.text,
                "state": render_state(item.record.state, catalog) if item.record.state else "",
                "probabilities": {i: p for i, p in item.probabilities.items() if i != OUT_OF_SCOPE},
                "out_of_scope": item.probabilities[OUT_OF_SCOPE],
            }
            for item in items
        ],
    )
    print(f"wrote {len(items)} dev decisions to {FIXTURE}")


def write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
