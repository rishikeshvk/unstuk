import math

import numpy as np
import pytest
import torch
from records import make
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_scoring import (
    Logits,
    Temperatures,
    fit_temperatures,
    log_loss,
    node_accuracy,
    predict,
    scored,
)
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.evaluate import Scored
from unstuk_ml.folds import trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion
from unstuk_ml.record import Record

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

CATALOG = load_catalog()
INTENTS = trained_intents(CATALOG)
RECORDS = [
    make("a", "no internet since morning"),
    make("b", "phone is silent", "phone_not_ringing", state=["dnd_on"]),
    make("c", "book me a cab", "out_of_scope"),
]


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def test_every_line_gets_a_distribution_over_the_intents_and_out_of_scope(
    tokenizer: Tokenizer,
) -> None:
    for item in predict(tiny_model("attention"), RECORDS, INTENTS, CATALOG, tokenizer):
        assert set(item.probabilities) == {*INTENTS, OUT_OF_SCOPE}
        assert sum(item.probabilities.values()) == pytest.approx(1, abs=1e-5)


def test_out_of_scope_takes_the_noul_probability_and_the_intents_share_the_rest(
    tokenizer: Tokenizer,
) -> None:
    model = tiny_model("cosine")
    with torch.no_grad():
        model.noul.weight.zero_()
        model.noul.bias.fill_(math.log(3))

    (item,) = predict(model, RECORDS[:1], INTENTS, CATALOG, tokenizer)

    assert item.probabilities[OUT_OF_SCOPE] == pytest.approx(0.75, abs=1e-5)
    assert item.top[0] == OUT_OF_SCOPE


def test_scoring_leaves_the_model_in_the_mode_it_found(tokenizer: Tokenizer) -> None:
    model = tiny_model("attention")
    model.train(True)

    predict(model, RECORDS, INTENTS, CATALOG, tokenizer)

    assert model.training


def test_log_loss_reads_the_first_labels_probability() -> None:
    items = [
        Scored(make("a", "x"), {"no_internet": 0.5, OUT_OF_SCOPE: 0.5}),
        Scored(make("b", "y"), {"no_internet": 0.0, OUT_OF_SCOPE: 1.0}),
    ]

    assert log_loss(items) == pytest.approx((math.log(2) + -math.log(1e-12)) / 2)


def test_node_accuracy_counts_the_top_option_against_the_answer(tokenizer: Tokenizer) -> None:
    question = NodeQuestion(
        id="q",
        target="airplane_mode",
        question="Which item is the airplane mode switch?",
        options=["Airplane mode", "Torch"],
        answer="Airplane mode",
        source="aosp:values",
        oem="aosp",
    )
    flipped = question.model_copy(update={"answer": "Torch"})

    model = tiny_model("cosine")

    assert node_accuracy(model, [question, flipped], tokenizer) == 0.5


def overconfident(lines: int = 3000) -> tuple[Logits, list[Record]]:
    """Labels drawn from softmax(base) and sigmoid(base_z), with logits twice as sharp."""
    rng = np.random.default_rng(0)
    base = rng.normal(size=(lines, 3))
    base_z = rng.normal(size=lines)
    choice = np.exp(base) / np.exp(base).sum(axis=1, keepdims=True)
    records = [
        make(
            f"r{n}",
            "x",
            OUT_OF_SCOPE
            if rng.random() < 1 / (1 + np.exp(-base_z[n]))
            else ["a", "b", "c"][rng.choice(3, p=choice[n])],
        )
        for n in range(lines)
    ]
    return Logits(choice=2 * base, out_of_scope=2 * base_z), records


def test_each_heads_temperature_undoes_its_overconfidence() -> None:
    logits, records = overconfident()

    temperatures = fit_temperatures(logits, records, ["a", "b", "c"])

    assert temperatures.choice == pytest.approx(2, rel=0.15)
    assert temperatures.noul == pytest.approx(2, rel=0.15)


def test_temperatures_soften_both_heads() -> None:
    logits = Logits(choice=np.array([[2.0, 0.0]]), out_of_scope=np.array([2.0]))
    record = [make("a", "x")]

    softer = Temperatures(choice=2.0, noul=2.0)

    sharp = scored(logits, record, ["a", "b"])[0].probabilities
    soft = scored(logits, record, ["a", "b"], softer)[0].probabilities

    assert soft[OUT_OF_SCOPE] == pytest.approx(1 / (1 + math.exp(-1)))
    assert sharp[OUT_OF_SCOPE] == pytest.approx(1 / (1 + math.exp(-2)))
    assert soft["a"] / soft["b"] == pytest.approx(math.e)
