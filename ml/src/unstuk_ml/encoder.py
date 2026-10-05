"""The frozen sentence encoder: BAAI/bge-small-en-v1.5 run from its own ONNX file, no PyTorch.

A text becomes the CLS token's final hidden state, scaled to length 1, as the model card says;
any other pooling would read the model differently from how it was trained.
"""

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download, try_to_load_from_cache
from numpy.typing import NDArray
from tokenizers import Tokenizer

from unstuk_ml.embedding_cache import EmbeddingCache, cache_path

REPO = "BAAI/bge-small-en-v1.5"
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
POOLING = "cls-l2"
MODEL_FILE, TOKENIZER_FILE = "onnx/model.onnx", "tokenizer.json"
HUB_CACHE = Path(__file__).resolve().parents[2] / "cache" / "hub"
MAX_TOKENS = 512
DIMENSIONS = 384
CACHE = cache_path(REVISION, POOLING)


def download() -> tuple[Path, Path]:
    """The pinned model and tokeniser; fetched once, then read from `ml/cache/hub` offline."""
    model, tokenizer = (
        Path(hf_hub_download(REPO, name, revision=REVISION, cache_dir=HUB_CACHE))
        for name in (MODEL_FILE, TOKENIZER_FILE)
    )
    return model, tokenizer


def downloaded() -> bool:
    return all(
        isinstance(try_to_load_from_cache(REPO, name, cache_dir=HUB_CACHE, revision=REVISION), str)
        for name in (MODEL_FILE, TOKENIZER_FILE)
    )


class Encoder:
    def __init__(self, model: Path, tokenizer: Path) -> None:
        self._tokenizer = Tokenizer.from_file(str(tokenizer))
        self._tokenizer.enable_truncation(MAX_TOKENS)
        options = ort.SessionOptions()
        options.use_deterministic_compute = True
        self._session = ort.InferenceSession(
            str(model), options, providers=["CPUExecutionProvider"]
        )
        self._inputs = {i.name for i in self._session.get_inputs()}

    def embed(self, texts: Sequence[str]) -> NDArray[np.float32]:
        vectors = np.zeros((len(texts), DIMENSIONS), dtype=np.float32)
        for row, text in enumerate(texts):
            vectors[row] = self._embed_one(text)
        return vectors

    def _embed_one(self, text: str) -> NDArray[np.float32]:
        # One text per pass: padding in a batch would let batch-mates nudge the last bits.
        encoding = self._tokenizer.encode(text)
        feeds = {
            "input_ids": encoding.ids,
            "attention_mask": encoding.attention_mask,
            "token_type_ids": encoding.type_ids,
        }
        inputs = {
            name: np.array([values], dtype=np.int64)
            for name, values in feeds.items()
            if name in self._inputs
        }
        (hidden,) = self._session.run(["last_hidden_state"], inputs)
        cls = np.asarray(hidden[0, 0], dtype=np.float32)
        return (cls / np.linalg.norm(cls)).astype(np.float32)


def load_encoder() -> Encoder:
    return Encoder(*download())


def embed_cached(texts: Sequence[str]) -> NDArray[np.float32]:
    """Vectors from the cache; the encoder is opened only when the cache lacks a text."""
    return EmbeddingCache(CACHE, lambda missing: load_encoder().embed(missing)).get(texts)
