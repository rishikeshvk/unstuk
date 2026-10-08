from pathlib import Path

import numpy as np
import pytest
from records import make
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import DecisionGraph, export, scale
from unstuk_ml.decision_scoring import decision_logits
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.export import parity
from unstuk_ml.graph_scoring import GraphDecider

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

CATALOG = load_catalog()
INTENTS = list(CATALOG.intents)
RECORDS = [
    make("a", "no internet since morning"),
    make(
        "b", "phone is silent and nobody can reach me at all", "phone_not_ringing", state=["dnd_on"]
    ),
    make("c", "book me a cab", "out_of_scope"),
]


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def test_the_graph_decides_as_the_model_does(tmp_path: Path, tokenizer: Tokenizer) -> None:
    model = tiny_model("cosine")
    graph = tmp_path / "decision.onnx"

    export(model, graph)
    expected = decision_logits(model, RECORDS, INTENTS, CATALOG, tokenizer)
    actual = GraphDecider(graph, tokenizer, scale(model)).logits(RECORDS, INTENTS, CATALOG)

    assert parity(expected, actual).passes


def test_vectors_have_unit_length(tmp_path: Path, tokenizer: Tokenizer) -> None:
    graph = tmp_path / "decision.onnx"
    export(tiny_model("cosine"), graph)

    vectors, noul = GraphDecider(graph, tokenizer, 1.0).embed(["wifi is off", ("no sound", "x")])

    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-6)
    assert noul.shape == (2,)


@pytest.mark.parametrize("model", [tiny_model("attention"), tiny_model("cosine", "fit")])
def test_a_head_that_reads_the_complaint_with_its_options_cannot_split(model: object) -> None:
    with pytest.raises(ValueError, match="one graph"):
        DecisionGraph(model)  # type: ignore[arg-type]
