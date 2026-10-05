import math

import pytest
import torch
from records import make
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_scoring import log_loss, node_accuracy, predict
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.evaluate import Scored
from unstuk_ml.folds import trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.node_labels import NodeQuestion

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
    for scored in predict(tiny_model("attention"), RECORDS, INTENTS, CATALOG, tokenizer):
        assert set(scored.probabilities) == {*INTENTS, OUT_OF_SCOPE}
        assert sum(scored.probabilities.values()) == pytest.approx(1, abs=1e-5)


def test_out_of_scope_takes_the_noul_probability_and_the_intents_share_the_rest(
    tokenizer: Tokenizer,
) -> None:
    model = tiny_model("cosine")
    with torch.no_grad():
        model.noul.weight.zero_()
        model.noul.bias.fill_(math.log(3))

    (scored,) = predict(model, RECORDS[:1], INTENTS, CATALOG, tokenizer)

    assert scored.probabilities[OUT_OF_SCOPE] == pytest.approx(0.75, abs=1e-5)
    assert scored.top[0] == OUT_OF_SCOPE


def test_scoring_leaves_the_model_in_the_mode_it_found(tokenizer: Tokenizer) -> None:
    model = tiny_model("attention")
    model.train(True)

    predict(model, RECORDS, INTENTS, CATALOG, tokenizer)

    assert model.training


def test_log_loss_reads_the_first_labels_probability() -> None:
    scored = [
        Scored(make("a", "x"), {"no_internet": 0.5, OUT_OF_SCOPE: 0.5}),
        Scored(make("b", "y"), {"no_internet": 0.0, OUT_OF_SCOPE: 1.0}),
    ]

    assert log_loss(scored) == pytest.approx((math.log(2) + -math.log(1e-12)) / 2)


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
