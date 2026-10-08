"""Draws every figure of the write-up into docs/figures (M9 spec section 3).

Reads the test scores `unstuk-writeup-scores` cached, the graphs the settings name and the release
APK; run `./gradlew assembleRelease` in android/ first if the APK is missing.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from unstuk_ml.decision_graph import FLOAT_GRAPH
from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.figures import gate_outcomes, ladder, reliability, size_waterfall, style
from unstuk_ml.fine_tuning import RUNS_DIR
from unstuk_ml.quantized_rung import SETTINGS, Settings
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.writeup_scores import ENTRIES, load_all
from unstuk_ml.zero_shot import ZERO_SHOT

APK = (
    Path(__file__).resolve().parents[4]
    / "android/app/build/outputs/apk/release/app-release-unsigned.apk"
)
SHIPS = "int8"
# The bar names the baseline that set each row by its report's title.
BAR_SETTERS = {
    TFIDF.decider.title: "tfidf",
    ENCODER.decider.title: "encoder",
    ZERO_SHOT.title: "zero-shot",
}


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    style.apply()
    scores = load_all()
    titles = {e.key: e.title for e in ENTRIES}
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    float_graph = (RUNS_DIR / settings.run / FLOAT_GRAPH).stat().st_size

    drawn = {
        "size-waterfall.svg": size_waterfall.draw(
            size_waterfall.steps(float_graph, size_waterfall.apk_parts(APK))
        ),
        "ladder.svg": ladder.draw(
            {titles[k]: v for k, v in scores.items()},
            {rung: titles[key] for rung, key in BAR_SETTERS.items()},
            titles[SHIPS],
        ),
        "reliability.svg": reliability.draw(
            [
                reliability.Panel(titles["tfidf"], scores["tfidf"], ships=False),
                reliability.Panel(titles["zero-shot"], scores["zero-shot"], ships=False),
                reliability.Panel(titles[SHIPS], scores[SHIPS], ships=True),
            ]
        ),
        "gate.svg": gate_outcomes.draw(scores[SHIPS]),
    }
    for name, figure in drawn.items():
        print(f"wrote {style.save(figure, name)}")
        plt.close(figure)
