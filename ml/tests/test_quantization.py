from pathlib import Path

import pytest
from records import make
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_graph import export
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.evaluate import GateLines, Scored
from unstuk_ml.graph_scoring import GraphDecider
from unstuk_ml.quantization import WITH_EMBEDDINGS, dev_check, quantize

GATE = GateLines(automatic_at=0.75, clarify_below=0.7, clarify_margin=0.0)
LINES = [
    make(f"l{n}", f"line {n}", "no_internet" if n % 2 else "phone_not_ringing") for n in range(100)
]


def scored(sure: float, wrong: int = 0) -> list[Scored]:
    """Every line's top answer is its label at `sure`, except the first `wrong` lines."""
    items = []
    for n, line in enumerate(LINES):
        gold = line.labels[0]
        other = "no_internet" if gold == "phone_not_ringing" else "phone_not_ringing"
        top = other if n < wrong else gold
        bottom = gold if n < wrong else other
        items.append(Scored(line, {top: sure, bottom: 1 - sure}, GATE))
    return items


def test_the_same_answers_pass() -> None:
    check = dev_check(scored(0.9), scored(0.9), [], [])

    assert check.top_agreement == 1.0
    assert check.passes


def test_two_changed_answers_in_a_hundred_fail() -> None:
    assert not dev_check(scored(0.9), scored(0.9, wrong=2), [], []).passes


def test_moving_lines_across_the_automatic_line_fails() -> None:
    check = dev_check(scored(0.9), scored(0.72), [], [])

    assert check.top_agreement == 1.0
    assert check.outcome_agreement == 0.0
    assert not check.passes


def test_lines_must_be_paired() -> None:
    with pytest.raises(ValueError, match="same lines"):
        dev_check(scored(0.9), list(reversed(scored(0.9))), [], [])


@pytest.mark.skipif(not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub")
def test_the_int8_graph_is_smaller_and_still_answers(tmp_path: Path) -> None:
    tokenizer: Tokenizer = decision_tokenizer(download()[1])
    float_graph, int8_graph = tmp_path / "float.onnx", tmp_path / "int8.onnx"
    export(tiny_model("cosine"), float_graph)

    quantize(float_graph, int8_graph, WITH_EMBEDDINGS)
    vectors, noul = GraphDecider(int8_graph, tokenizer, 1.0).embed(["wifi is off"])

    assert int8_graph.stat().st_size < float_graph.stat().st_size / 2
    assert vectors.shape[0] == noul.shape[0] == 1
