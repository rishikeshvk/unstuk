from pathlib import Path

import numpy as np
import pytest
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import export
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.fine_tuning import sha256
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.model_assets import GRAPH, MANIFEST, OPTIONS, VOCAB, Manifest, write_assets
from unstuk_ml.quantized_rung import Settings

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

CATALOG = load_catalog()


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def settings(graph: Path) -> Settings:
    return Settings(
        run="tiny",
        float_sha256="",
        graph=graph.name,
        graph_sha256=sha256(graph),
        ops=[],
        scale=20.0,
        choice_temperature=0.9,
        noul_temperature=1.5,
        lines={},
        retuned={},
        automatic_wrong=0.0,
        clear_clarified=0.0,
        vague_handled=0.0,
        commit="",
        tries=[],
    )


def test_the_manifest_pins_every_file_it_names(tmp_path: Path, tokenizer: Tokenizer) -> None:
    graph, assets = tmp_path / "graph.onnx", tmp_path / "assets"
    export(tiny_model("cosine"), graph)

    write_assets(graph, settings(graph), CATALOG, tokenizer, assets)
    manifest = Manifest.model_validate_json((assets / MANIFEST).read_text(encoding="utf-8"))

    assert manifest.graph_sha256 == sha256(assets / GRAPH)
    assert manifest.options_sha256 == sha256(assets / OPTIONS)
    assert manifest.vocab_sha256 == sha256(assets / VOCAB)
    assert manifest.intents == list(CATALOG.intents)
    assert "always" not in manifest.state_checks
    assert manifest.state_checks == sorted(manifest.state_checks)


def test_option_vectors_are_the_graphs_own_in_intent_order(
    tmp_path: Path, tokenizer: Tokenizer
) -> None:
    graph, assets = tmp_path / "graph.onnx", tmp_path / "assets"
    export(tiny_model("cosine"), graph)

    manifest = write_assets(graph, settings(graph), CATALOG, tokenizer, assets)
    stored = np.frombuffer((assets / OPTIONS).read_bytes(), dtype="<f4")
    expected, _ = GraphDecider(graph, tokenizer, 1.0).embed(
        [CATALOG.intents[i] for i in manifest.intents]
    )

    assert np.array_equal(stored.reshape(-1, manifest.dimensions), expected)


def test_the_vocabulary_has_one_token_per_id(tmp_path: Path, tokenizer: Tokenizer) -> None:
    graph, assets = tmp_path / "graph.onnx", tmp_path / "assets"
    export(tiny_model("cosine"), graph)

    write_assets(graph, settings(graph), CATALOG, tokenizer, assets)
    tokens = (assets / VOCAB).read_text(encoding="utf-8").splitlines()

    assert len(tokens) == tokenizer.get_vocab_size()
    assert tokens.index("[CLS]") == tokenizer.token_to_id("[CLS]")


def test_a_graph_the_settings_do_not_name_is_refused(tmp_path: Path, tokenizer: Tokenizer) -> None:
    graph = tmp_path / "graph.onnx"
    export(tiny_model("cosine"), graph)
    named = settings(graph)
    graph.write_bytes(graph.read_bytes() + b"\0")

    with pytest.raises(ValueError, match="not the graph"):
        write_assets(graph, named, CATALOG, tokenizer, tmp_path / "assets")
