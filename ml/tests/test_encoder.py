import os
import subprocess
import sys

import numpy as np
import pytest

from unstuk_ml.encoder import DIMENSIONS, downloaded, load_encoder

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small isn't in ml/cache/hub; run unstuk_ml.encoder.download()"
)

TEXTS = ["my phone doesn't ring", "phone stays silent when someone calls", "screen is too dark"]


def test_vectors_have_the_models_width_and_unit_length() -> None:
    vectors = load_encoder().embed(TEXTS)

    assert vectors.shape == (3, DIMENSIONS)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)


def test_a_texts_vector_does_not_depend_on_its_neighbours() -> None:
    encoder = load_encoder()

    alone = encoder.embed([TEXTS[0]])
    among = encoder.embed([TEXTS[2] * 20, TEXTS[0]])

    assert np.array_equal(alone[0], among[1])


def test_similar_complaints_sit_closer_than_different_ones() -> None:
    ring, silent, dark = load_encoder().embed(TEXTS)

    assert ring @ silent > ring @ dark


def test_vectors_do_not_depend_on_string_hashing() -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "from unstuk_ml.encoder import load_encoder\n"
        f"print(load_encoder().embed({TEXTS!r}).tobytes().hex())\n"
    )
    outputs = {
        subprocess.run(
            [sys.executable, "-c", script],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for seed in range(8)
    }

    assert len(outputs) == 1
