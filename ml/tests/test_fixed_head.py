import pytest
import torch
from records import make
from tiny_model import tiny_backbone
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.fixed_head import (
    FixedHeadModel,
    collate_rows,
    fixed_head_logits,
    fixed_head_loss,
    fixed_labels,
    rows,
)
from unstuk_ml.folds import trained_intents
from unstuk_ml.labels import OUT_OF_SCOPE

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

CATALOG = load_catalog()
LABELS = fixed_labels(CATALOG)
RECORDS = [
    make("a", "no internet since morning"),
    make("b", "silent and no net", labels=["phone_not_ringing", "no_internet"]),
    make("c", "book me a cab", "out_of_scope"),
]


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def tiny_fixed_head() -> FixedHeadModel:
    return FixedHeadModel(tiny_backbone(), LABELS)


def test_the_labels_are_the_trained_intents_then_out_of_scope() -> None:
    assert [*trained_intents(CATALOG), OUT_OF_SCOPE] == LABELS


def test_a_line_with_two_problems_gives_a_row_for_each() -> None:
    labelled = rows(RECORDS, LABELS, seed=7, number=0, typos=False)

    assert [LABELS[r.label] for r in labelled] == [
        "no_internet",
        "phone_not_ringing",
        "no_internet",
        OUT_OF_SCOPE,
    ]
    assert [r.text for r in labelled][:2] == ["no internet since morning", "silent and no net"]


def test_typos_appear_only_when_asked_for() -> None:
    lines = [make(f"l{n}", "my phone does not ring anymore") for n in range(80)]

    plain = rows(lines, LABELS, seed=7, number=0, typos=False)
    noisy = rows(lines, LABELS, seed=7, number=0, typos=True)

    assert all(r.text == lines[0].text for r in plain)
    assert 0.1 < sum(r.text != lines[0].text for r in noisy) / len(noisy) < 0.4


def test_the_model_gives_one_logit_per_label_and_a_finite_loss(tokenizer: Tokenizer) -> None:
    model = tiny_fixed_head()
    batch = collate_rows(rows(RECORDS, LABELS, seed=7, number=0, typos=False), tokenizer)

    assert model(batch.texts).shape == (4, len(LABELS))
    assert torch.isfinite(fixed_head_loss(model, batch))


def test_logits_come_one_row_per_line_and_leave_the_mode_alone(tokenizer: Tokenizer) -> None:
    model = tiny_fixed_head()
    model.train(True)

    logits = fixed_head_logits(model, RECORDS, tokenizer)

    assert logits.shape == (3, len(LABELS))
    assert model.training
