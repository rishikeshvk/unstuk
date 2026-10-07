import copy
import math

import pytest
import torch
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.decision_batch import collate, decision_tokenizer
from unstuk_ml.decision_model import DecisionModel, Head
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.training_examples import Example

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

HEADS: list[Head] = ["cosine", "attention"]
OPTIONS = ("The internet is not working", "The phone doesn't ring", "The screen is too dark")
SHORT = Example("no net", "", OPTIONS, frozenset({0}), False)
LONG = Example(
    "my phone has been acting strange for days and nothing loads at all anywhere",
    "dnd on; bluetooth off",
    (*OPTIONS, "Text is too small", "Bluetooth earphones won't connect"),
    frozenset({0}),
    False,
)


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def scores(model: DecisionModel, examples: list[Example], tokenizer: Tokenizer) -> torch.Tensor:
    with torch.no_grad():
        logits: torch.Tensor = model(collate(examples, tokenizer)).choice_logits
    return logits


@pytest.mark.parametrize("head", HEADS)
def test_shapes_and_padded_options(head: Head, tokenizer: Tokenizer) -> None:
    with torch.no_grad():
        decision = tiny_model(head)(collate([SHORT, LONG], tokenizer))

    assert decision.choice_logits.shape == (2, 5)
    assert decision.out_of_scope_logit.shape == (2,)
    assert decision.choice_logits[0, 3:].tolist() == [-math.inf, -math.inf]
    assert torch.isfinite(decision.choice_logits[1]).all()


@pytest.mark.parametrize("head", HEADS)
def test_reordering_options_reorders_their_scores(head: Head, tokenizer: Tokenizer) -> None:
    model = tiny_model(head)
    order = [3, 0, 4, 2, 1]
    shuffled = Example(
        LONG.text, LONG.state, tuple(LONG.options[i] for i in order), frozenset(), False
    )

    before = scores(model, [LONG], tokenizer)[0]
    after = scores(model, [shuffled], tokenizer)[0]

    assert torch.allclose(after, before[order], atol=1e-5)


@pytest.mark.parametrize("head", HEADS)
def test_an_example_scores_the_same_alone_and_beside_a_longer_one(
    head: Head, tokenizer: Tokenizer
) -> None:
    model = tiny_model(head)

    alone = scores(model, [SHORT], tokenizer)[0]
    beside = scores(model, [LONG, SHORT], tokenizer)[1, :3]

    assert torch.allclose(alone, beside, atol=1e-5)


def test_before_training_the_attention_head_scores_as_the_cosine_head(
    tokenizer: Tokenizer,
) -> None:
    cosine = tiny_model("cosine")
    attention = tiny_model("attention")
    attention.backbone = copy.deepcopy(cosine.backbone)

    assert torch.equal(
        scores(cosine, [SHORT, LONG], tokenizer), scores(attention, [SHORT, LONG], tokenizer)
    )


def noul_logits(
    model: DecisionModel, examples: list[Example], tokenizer: Tokenizer
) -> torch.Tensor:
    with torch.no_grad():
        logits: torch.Tensor = model(collate(examples, tokenizer)).out_of_scope_logit
    return logits


@pytest.mark.parametrize("head", HEADS)
def test_the_option_aware_noul_ignores_option_order(head: Head, tokenizer: Tokenizer) -> None:
    model = tiny_model(head, "options")
    shuffled = Example(
        LONG.text, LONG.state, tuple(LONG.options[i] for i in [3, 0, 4, 2, 1]), frozenset(), False
    )

    before = noul_logits(model, [LONG], tokenizer)
    after = noul_logits(model, [shuffled], tokenizer)

    assert torch.allclose(before, after, atol=1e-5)


@pytest.mark.parametrize("head", HEADS)
def test_the_option_aware_noul_scores_an_example_the_same_beside_a_longer_one(
    head: Head, tokenizer: Tokenizer
) -> None:
    model = tiny_model(head, "options")

    alone = noul_logits(model, [SHORT], tokenizer)[0]
    beside = noul_logits(model, [LONG, SHORT], tokenizer)[1]

    assert torch.allclose(alone, beside, atol=1e-5)


def test_the_option_aware_noul_reads_the_options(tokenizer: Tokenizer) -> None:
    model = tiny_model("cosine", "options")
    other = Example(SHORT.text, SHORT.state, LONG.options[2:], frozenset(), False)

    first, second = noul_logits(model, [SHORT, other], tokenizer)

    assert not torch.isclose(first, second)
    same_complaint = noul_logits(tiny_model("cosine"), [SHORT, other], tokenizer)
    assert torch.isclose(same_complaint[0], same_complaint[1])
