import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from records import make

from unstuk_ml import encoder, encoder_rung
from unstuk_ml.embedding_cache import EmbeddingCache
from unstuk_ml.encoder import downloaded
from unstuk_ml.rung import score, train

needs_model = pytest.mark.skipif(
    not downloaded(), reason="bge-small isn't in ml/cache/hub; run unstuk_ml.encoder.download()"
)

TEXTS = {
    "no_internet": ["internet not working", "no internet on phone", "mobile data stopped"],
    "phone_not_ringing": ["phone does not ring", "no ringtone for calls", "calls come silently"],
    "out_of_scope": ["what is the weather", "book a taxi", "play some music"],
}
TRAIN = [
    make(f"{label}-{i}", text, label)
    for label, texts in TEXTS.items()
    for i, text in enumerate(texts)
]


def test_a_warm_cache_never_opens_the_encoder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "e.npz"
    texts = [r.text for r in TRAIN]
    fake = np.random.default_rng(0).normal(size=(len(texts), 4)).astype(np.float32)
    EmbeddingCache(cache, lambda _: fake).get(texts)
    monkeypatch.setattr(encoder, "CACHE", cache)

    def refuse() -> None:
        raise AssertionError("the encoder was opened")

    monkeypatch.setattr(encoder, "load_encoder", refuse)

    model = train(encoder_rung.ENCODER, TRAIN, c=1.0, class_weight=None)

    assert set(score(model, 1.0, TRAIN[:1])[0].probabilities) == set(TEXTS)


@needs_model
def test_the_probe_reads_meaning_the_words_do_not_share(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(encoder, "CACHE", tmp_path / "e.npz")
    model = train(encoder_rung.ENCODER, TRAIN, c=10.0, class_weight=None)

    lines = [
        make("a", "my mobile stays quiet when someone calls me"),
        make("b", "cannot go online"),
    ]

    assert [s.top[0] for s in score(model, 1.0, lines)] == ["phone_not_ringing", "no_internet"]


@needs_model
def test_training_and_scoring_do_not_depend_on_string_hashing(tmp_path: Path) -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "import sys; sys.path.insert(0, 'tests')\n"
        "from pathlib import Path\n"
        "from test_encoder_rung import TRAIN\n"
        "from records import make\n"
        "from unstuk_ml import encoder, encoder_rung\n"
        "from unstuk_ml.rung import score, train\n"
        f"encoder.CACHE = Path({str(tmp_path / 'e.npz')!r})\n"
        "model = train(encoder_rung.ENCODER, TRAIN, c=1.0, class_weight=None)\n"
        "print(score(model, 1.5, [make('t', 'no ring and no internet')])[0].probabilities)\n"
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
