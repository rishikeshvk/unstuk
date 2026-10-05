"""The frozen-encoder rung (M4 spec section 2): bge-small's sentence vectors read by a linear probe.

Nothing in the encoder is trained; logistic regression learns which directions of its 384
dimensions separate the intents, so this rung measures what pre-training alone already knows.
"""

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer

from unstuk_ml import rung
from unstuk_ml.baseline_report import REPORTS, Below, Decider
from unstuk_ml.embedding_cache import EmbeddingCache, cache_path
from unstuk_ml.encoder import POOLING, REVISION, load_encoder
from unstuk_ml.record import Record
from unstuk_ml.rung import ClassWeight, Rung
from unstuk_ml.tfidf_rung import TFIDF

CACHE = cache_path(REVISION, POOLING)


def embeddings(texts: Sequence[str]) -> NDArray[np.float32]:
    # The encoder is opened only when the cache lacks a text.
    return EmbeddingCache(CACHE, lambda missing: load_encoder().embed(missing)).get(texts)


def build(c: float, class_weight: ClassWeight) -> Pipeline:
    return make_pipeline(
        FunctionTransformer(embeddings),
        LogisticRegression(C=c, class_weight=class_weight, max_iter=5000),
    )


ENCODER = Rung(
    decider=Decider(
        title="Frozen bge-small + logistic regression",
        command="unstuk-encoder test",
        about="BAAI/bge-small-en-v1.5 sentence vectors (CLS, L2-normalised, frozen), read by "
        "logistic regression trained on `data/clean/train.jsonl`",
        held_out_note="no output for them; only a two-problem line whose other problem is "
        "trained can count as right",
        report=REPORTS / "encoder.md",
    ),
    grid=[(c, None) for c in (0.1, 0.3, 1.0, 3.0, 10.0)],
    build=build,
    settings=rung.SETTINGS_DIR / "encoder.json",
    extensions=(30.0, 100.0, 300.0),
)


def tfidf_below(lines: list[Record]) -> Below:
    settings, model = rung.load(TFIDF)
    return Below(TFIDF.decider, rung.score(model, settings.temperature, lines))


def main() -> None:
    rung.main(ENCODER, tfidf_below)
