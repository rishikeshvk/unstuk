import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from records import make

from unstuk_ml import encoder
from unstuk_ml.encoder import downloaded, embed_cached
from unstuk_ml.zero_shot import INSTRUCTION, OUT_OF_SCOPE_OPTIONS, cosines, options, score, tune

needs_model = pytest.mark.skipif(
    not downloaded(), reason="bge-small isn't in ml/cache/hub; run unstuk_ml.encoder.download()"
)
LABELS, TEXTS = options(OUT_OF_SCOPE_OPTIONS[0])


class OneHot:
    """Each option text is its own axis; a complaint points along the axis of the label it names."""

    def __init__(self, complaints: dict[str, str]) -> None:
        self.complaints = complaints
        self.seen: list[str] = []

    def __call__(self, texts: Sequence[str]) -> NDArray[np.float32]:
        self.seen += texts
        return np.stack([self._vector(t) for t in texts])

    def _vector(self, text: str) -> NDArray[np.float32]:
        vector = np.zeros(len(TEXTS) + 2, dtype=np.float32)
        text = text.removeprefix(INSTRUCTION)
        if text in self.complaints:
            vector[LABELS.index(self.complaints[text])] = 1.0
        elif text in TEXTS:
            vector[TEXTS.index(text)] = 1.0
        else:
            vector[-1] = 1.0  # another out-of-scope wording: matches nothing here
        return vector


def test_the_nearest_option_wins_out_of_scope_included() -> None:
    embed = OneHot({"phone silent": "phone_not_ringing", "rain today?": "out_of_scope"})
    lines = [make("a", "phone silent"), make("b", "rain today?", "out_of_scope")]

    scored = score(cosines(embed, lines, TEXTS, instruction=False), LABELS, lines, 0.05)

    assert [s.top[0] for s in scored] == ["phone_not_ringing", "out_of_scope"]
    assert len(scored[0].probabilities) == 16


def test_the_instruction_goes_on_complaints_only() -> None:
    embed = OneHot({"phone silent": "phone_not_ringing"})

    cosines(embed, [make("a", "phone silent")], TEXTS, instruction=True)

    assert embed.seen[0] == INSTRUCTION + "phone silent"
    assert not any(t.startswith(INSTRUCTION) for t in embed.seen[1:])


def test_tuning_tries_every_wording_and_keeps_a_small_temperature() -> None:
    embed = OneHot({"phone silent": "phone_not_ringing", "rain today?": "out_of_scope"})
    dev = [make("a", "phone silent", "phone_not_ringing"), make("b", "rain today?", "out_of_scope")]

    settings = tune(embed, dev)

    assert len(settings.grid) == 2 * len(OUT_OF_SCOPE_OPTIONS)
    # Only the first wording is the one these complaints point at, so it wins.
    assert settings.out_of_scope_option == OUT_OF_SCOPE_OPTIONS[0]
    assert 0 < settings.temperature < 1


@needs_model
def test_a_held_out_intent_is_named_without_any_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(encoder, "CACHE", tmp_path / "e.npz")
    line = make("a", "my screen won't turn sideways when I tilt the phone", "screen_wont_rotate")

    [scored] = score(cosines(embed_cached, [line], TEXTS, instruction=False), LABELS, [line], 0.02)

    assert scored.top[0] == "screen_wont_rotate"


@needs_model
def test_scoring_does_not_depend_on_string_hashing(tmp_path: Path) -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "import sys; sys.path.insert(0, 'tests')\n"
        "from pathlib import Path\n"
        "from records import make\n"
        "from unstuk_ml import encoder\n"
        "from unstuk_ml.zero_shot import OUT_OF_SCOPE_OPTIONS, cosines, options, score\n"
        f"encoder.CACHE = Path({str(tmp_path / 'e.npz')!r})\n"
        "labels, texts = options(OUT_OF_SCOPE_OPTIONS[1])\n"
        "lines = [make('a', 'clock is wrong and no ring')]\n"
        "print(score(cosines(encoder.embed_cached, lines, texts, True), labels, lines, 0.03))\n"
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
