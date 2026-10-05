from collections.abc import Sequence
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from unstuk_ml.embedding_cache import EmbeddingCache, cache_path


class CountingEmbed:
    """Stands in for the encoder: a vector made from the text's length, and a record of calls."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, texts: Sequence[str]) -> NDArray[np.float32]:
        self.calls.append(list(texts))
        return np.array([[len(t), 1.0] for t in texts], dtype=np.float32)


def test_each_text_reaches_the_encoder_once_even_across_runs(tmp_path: Path) -> None:
    path, embed = tmp_path / "e.npz", CountingEmbed()

    first = EmbeddingCache(path, embed).get(["bb", "a", "bb"])
    again = EmbeddingCache(path, embed).get(["a", "ccc", "bb"])

    assert [sorted(call) for call in embed.calls] == [["a", "bb"], ["ccc"]]
    assert first.tolist() == [[2, 1], [1, 1], [2, 1]]
    assert np.array_equal(again, np.array([[1, 1], [3, 1], [2, 1]], dtype=np.float32))


def test_another_model_revision_or_pooling_gets_its_own_file() -> None:
    paths = {cache_path("5c38ec7c405e", "cls-l2"), cache_path("aaaaaaaaaaaa", "cls-l2")}
    paths.add(cache_path("5c38ec7c405e", "mean-l2"))

    assert len(paths) == 3


def test_a_finished_save_leaves_no_partial_file(tmp_path: Path) -> None:
    EmbeddingCache(tmp_path / "e.npz", CountingEmbed()).get(["a"])

    assert [p.name for p in tmp_path.iterdir()] == ["e.npz"]
