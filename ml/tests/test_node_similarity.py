from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from unstuk_ml import encoder
from unstuk_ml.encoder import downloaded, embed_cached
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.node_similarity import cut, similarity_picker

QUESTION = NodeQuestion(
    id="q",
    target="wifi",
    question="Which item on the screen is the switch for Wi-Fi?",
    options=["Torch, Off", "Wi-Fi, Off", "Bluetooth, On"],
    answer="Wi-Fi, Off",
    source="dump:qs",
    oem="motorola",
)


def _fake(texts: Sequence[str]) -> NDArray[np.float32]:
    """The question points at whichever option mentions Wi-Fi."""
    return np.array([[1.0, 0.0] if "Wi-Fi" in t else [0.0, 1.0] for t in texts], dtype=np.float32)


def test_the_option_nearest_the_question_is_picked() -> None:
    pick = similarity_picker(_fake, [QUESTION])

    assert pick(QUESTION) == "Wi-Fi, Off"


def test_cutting_drops_a_tiles_state_from_options_and_answer() -> None:
    plain = cut(QUESTION)

    assert plain.options == ["Torch", "Wi-Fi", "Bluetooth"]
    assert plain.answer == "Wi-Fi"


@pytest.mark.skipif(not downloaded(), reason="bge-small isn't in ml/cache/hub")
def test_the_encoder_matches_a_switch_by_meaning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(encoder, "CACHE", tmp_path / "e.npz")
    question = cut(QUESTION).model_copy(update={"options": ["Torch", "Wireless network"]})

    assert similarity_picker(embed_cached, [question])(question) == "Wireless network"
