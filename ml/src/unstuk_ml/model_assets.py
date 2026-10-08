"""The model files the app ships, and the manifest that pins them (M7 spec section 5).

The graph, the catalog's option vectors and the vocabulary are derived files, gitignored. The
committed manifest names their sha256s and the `intents.json` the vectors came from, so the
build can refuse files that drifted from what was exported.
"""

import shutil
from pathlib import Path

from pydantic import BaseModel
from tokenizers import Tokenizer

from unstuk_ml.catalog import CATALOG_DIR, Catalog
from unstuk_ml.decision_batch import MAX_TOKENS
from unstuk_ml.fine_tuning import sha256
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.quantized_rung import Settings

ASSETS = (
    Path(__file__).resolve().parents[3] / "android" / "app" / "src" / "main" / "assets" / "model"
)
GRAPH, OPTIONS, VOCAB, MANIFEST = "decision.onnx", "options.bin", "vocab.txt", "model.json"


class Manifest(BaseModel):
    graph_sha256: str
    options_sha256: str
    vocab_sha256: str
    catalog_sha256: str
    """Of `catalog/intents.json`, whose option texts the vectors encode."""
    intents: list[str]
    """The intents in the order of their vectors in `options.bin`."""
    dimensions: int
    scale: float
    choice_temperature: float
    noul_temperature: float
    max_tokens: int


def write_assets(
    graph: Path, settings: Settings, catalog: Catalog, tokenizer: Tokenizer, assets: Path = ASSETS
) -> Manifest:
    """`graph` must be the one `settings` names; the vectors are its own, little-endian float32."""
    if sha256(graph) != settings.graph_sha256:
        raise ValueError(f"{graph} is not the graph the settings name")
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(graph, assets / GRAPH)
    intents = list(catalog.intents)
    vectors, _ = GraphDecider(graph, tokenizer, settings.scale).embed(
        [catalog.intents[i] for i in intents]
    )
    (assets / OPTIONS).write_bytes(vectors.astype("<f4").tobytes())
    (assets / VOCAB).write_text(_vocabulary(tokenizer), encoding="utf-8")
    manifest = Manifest(
        graph_sha256=settings.graph_sha256,
        options_sha256=sha256(assets / OPTIONS),
        vocab_sha256=sha256(assets / VOCAB),
        catalog_sha256=sha256(CATALOG_DIR / "intents.json"),
        intents=intents,
        dimensions=int(vectors.shape[1]),
        scale=settings.scale,
        choice_temperature=settings.choice_temperature,
        noul_temperature=settings.noul_temperature,
        max_tokens=MAX_TOKENS,
    )
    (assets / MANIFEST).write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return manifest


def _vocabulary(tokenizer: Tokenizer) -> str:
    """One token per line, in id order, as BERT's `vocab.txt`."""
    vocab = tokenizer.get_vocab(with_added_tokens=True)
    tokens = sorted(vocab, key=vocab.__getitem__)
    if [vocab[t] for t in tokens] != list(range(len(tokens))):
        raise ValueError("the vocabulary's ids are not 0 to n - 1")
    return "\n".join(tokens) + "\n"
