"""Embeddings on disk, so each text goes through the encoder once.

The file name carries the model revision and the pooling, so changing either starts a new cache
instead of reading vectors made another way.
"""

import hashlib
import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

Embed = Callable[[Sequence[str]], NDArray[np.float32]]
CACHE_DIR = Path(__file__).resolve().parents[2] / "cache" / "embeddings"


class EmbeddingCache:
    def __init__(self, path: Path, embed: Embed) -> None:
        self._path = path
        self._embed = embed
        self._vectors: dict[str, NDArray[np.float32]] = {}
        if path.exists():
            with np.load(path) as stored:
                self._vectors = {key: stored[key] for key in stored.files}

    def get(self, texts: Sequence[str]) -> NDArray[np.float32]:
        """One row per text, in order; only texts never seen before reach the encoder."""
        keys = [_key(t) for t in texts]
        missing = sorted(
            {k: t for k, t in zip(keys, texts, strict=True) if k not in self._vectors}.items()
        )
        if missing:
            fresh = self._embed([t for _, t in missing])
            self._vectors.update({k: fresh[i] for i, (k, _) in enumerate(missing)})
            self._save()
        return np.stack([self._vectors[k] for k in keys])

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        partial = self._path.with_suffix(".partial.npz")
        arrays: dict[str, Any] = dict(sorted(self._vectors.items()))
        np.savez(partial, **arrays)
        # A rename is atomic, so an interrupted run leaves the old cache, not half a new one.
        os.replace(partial, self._path)


def cache_path(revision: str, pooling: str) -> Path:
    return CACHE_DIR / f"{revision[:12]}-{pooling}.npz"


def _key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
