"""Decisions from the exported graph through ONNX Runtime, as the app will make them (M7 spec).

The Choice head is the arithmetic the app repeats in Kotlin: the complaint's vector against each
option's, times the learned scale. The result is `decision_scoring.Logits`, so temperatures,
`scored` and every metric read the graph as they read the PyTorch model.
"""

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray
from tokenizers import Tokenizer

from unstuk_ml.catalog import Catalog
from unstuk_ml.decision_batch import encode
from unstuk_ml.decision_graph import INPUTS
from unstuk_ml.decision_scoring import Logits
from unstuk_ml.record import Record
from unstuk_ml.training_examples import render_state


class GraphDecider:
    def __init__(self, graph: Path, tokenizer: Tokenizer, scale: float) -> None:
        options = ort.SessionOptions()
        options.use_deterministic_compute = True
        self._session = ort.InferenceSession(
            str(graph), options, providers=["CPUExecutionProvider"]
        )
        self._tokenizer = tokenizer
        self._scale = scale

    def embed(
        self, inputs: Sequence[str | tuple[str, str]]
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Each text's unit vector and Noul logit; a pair is a complaint and its state."""
        vectors, noul = [], []
        # One at a time, as the app runs it: int8 activations are scaled by their whole batch,
        # padding included, so a batched answer depends on its batchmates.
        for one in inputs:
            encoded = encode(self._tokenizer, [one])
            feed = {name: getattr(encoded, name).numpy() for name in INPUTS}
            vector, logit = self._session.run(None, feed)
            vectors.append(vector)
            noul.append(logit)
        return np.concatenate(vectors), np.concatenate(noul)

    def logits(self, records: Sequence[Record], intents: Sequence[str], catalog: Catalog) -> Logits:
        """Each line against the given intents' options, with its state if it has one."""
        options, _ = self.embed([catalog.intents[i] for i in intents])
        queries, noul = self.embed(
            [(r.text, render_state(r.state, catalog)) if r.state else r.text for r in records]
        )
        choice = self._scale * (queries @ options.T)
        return Logits(choice.astype(np.float64), noul.astype(np.float64))
