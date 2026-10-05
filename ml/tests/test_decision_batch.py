import pytest
import torch

from unstuk_ml.decision_batch import DecisionBatch, collate, decision_tokenizer
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.training_examples import Example

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

INTERNET, RING, DARK = "No internet", "Phone doesn't ring", "Screen too dark"
EXAMPLES = [
    Example("no net", "dnd on", (INTERNET, RING), frozenset({0}), False),
    Example("book a cab", "", (DARK, RING, INTERNET), frozenset(), True),
    Example("which is wifi?", "", ("Wi-Fi", "Torch"), frozenset({0}), None),
]


@pytest.fixture(scope="module")
def batch() -> DecisionBatch:
    return collate(EXAMPLES, decision_tokenizer(download()[1]))


def test_the_state_is_segment_b_and_a_line_without_one_is_encoded_alone(
    batch: DecisionBatch,
) -> None:
    tokenizer = decision_tokenizer(download()[1])
    types = batch.queries.token_type_ids

    assert types[0].sum() > 0
    assert types[1].sum() == 0
    alone = tokenizer.encode("book a cab").ids
    assert batch.queries.input_ids[1, : len(alone)].tolist() == alone


def test_each_distinct_option_is_encoded_once(batch: DecisionBatch) -> None:
    assert batch.options.input_ids.shape[0] == 5


def test_examples_point_at_their_own_options(batch: DecisionBatch) -> None:
    tokenizer = decision_tokenizer(download()[1])
    for n, example in enumerate(EXAMPLES):
        for k, option in enumerate(example.options):
            row = batch.options.input_ids[batch.option_index[n, k]]
            ids = tokenizer.encode(option).ids
            assert row[: len(ids)].tolist() == ids


def test_masks_follow_option_counts_answers_and_the_noul(batch: DecisionBatch) -> None:
    assert batch.option_mask.tolist() == [[True, True, False], [True] * 3, [True, True, False]]
    assert batch.answers.tolist() == [[True, False, False], [False] * 3, [True, False, False]]
    assert torch.equal(batch.out_of_scope, torch.tensor([0.0, 1.0, 0.0]))
    assert batch.asks_out_of_scope.tolist() == [True, True, False]
