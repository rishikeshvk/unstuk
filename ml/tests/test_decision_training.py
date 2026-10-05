import argparse

import pytest
import torch
from records import make
from tiny_model import tiny_model
from tokenizers import Tokenizer

from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_training import (
    HEAD_LEARNING_RATE,
    Data,
    RunConfig,
    add_run_arguments,
    config_from,
    learning_rate_factor,
    parameter_groups,
    removed_intents,
    run_arguments,
    train,
)
from unstuk_ml.encoder import download, downloaded
from unstuk_ml.folds import trained_intents
from unstuk_ml.node_labels import NodeQuestion

pytestmark = pytest.mark.skipif(
    not downloaded(), reason="bge-small's tokenizer isn't in ml/cache/hub; run encoder.download()"
)

CATALOG = load_catalog()
INTENTS = trained_intents(CATALOG)
LINES = [make(f"t{n}", f"complaint {n} about {i}", i) for n, i in enumerate(INTENTS * 2)]
NODES = [
    NodeQuestion(
        id="q",
        target="airplane_mode",
        question="Which item is the airplane mode switch?",
        options=["Airplane mode", "Torch"],
        answer="Airplane mode",
        source="aosp:values",
        oem="aosp",
    )
]
DATA = Data([*LINES, make("o", "book a cab", "out_of_scope")], NODES, LINES[:12], NODES)


@pytest.fixture(scope="module")
def tokenizer() -> Tokenizer:
    return decision_tokenizer(download()[1])


def config(**changes: object) -> RunConfig:
    fields: dict[str, object] = {
        "head": "attention",
        "learning_rate": 5e-5,
        "typos": False,
        "state": True,
        "epochs": 2,
        "batch_size": 8,
    }
    return RunConfig.model_validate(fields | changes)


def test_a_runs_name_says_what_it_tried() -> None:
    assert config().name == "attention-lr5e-05-state"
    assert (
        config(typos=True, fold=1, limit=64).name == "attention-lr5e-05-typos-state-fold1-limit64"
    )


def test_the_heads_learn_at_their_own_rate() -> None:
    model = tiny_model("attention")

    backbone, heads = parameter_groups(model, 5e-5)

    assert (backbone["lr"], heads["lr"]) == (5e-5, HEAD_LEARNING_RATE)
    ids = {id(p) for p in heads["params"]}
    assert {id(model.log_scale), id(model.noul.weight)} <= ids
    assert not ids & {id(p) for p in model.backbone.parameters()}


def test_the_rate_warms_up_over_a_tenth_then_decays_to_zero() -> None:
    factors = [learning_rate_factor(step, steps=100) for step in (0, 5, 10, 55, 100)]

    assert factors == [0.0, 0.5, 1.0, 0.5, 0.0]


def test_a_fold_removes_one_of_the_folds() -> None:
    assert removed_intents(config(), CATALOG) == frozenset()
    assert len(removed_intents(config(fold=2), CATALOG)) == 4


def test_training_checks_dev_each_epoch_and_keeps_the_best_weights(tokenizer: Tokenizer) -> None:
    model = tiny_model("attention")

    results, weights = train(config(), DATA, model, tokenizer, torch.device("cpu"))

    assert [r.epoch for r in results] == [0, 1]
    assert all(r.fold_accuracy is None for r in results)
    assert set(weights) == set(model.state_dict())


def test_a_fold_run_reports_accuracy_on_the_intents_it_never_saw(tokenizer: Tokenizer) -> None:
    results, _ = train(
        config(fold=0, epochs=1), DATA, tiny_model("cosine"), tokenizer, torch.device("cpu")
    )

    assert results[0].fold_accuracy is not None


def test_the_same_config_trains_the_same_on_cpu(tokenizer: Tokenizer) -> None:
    runs = [
        train(config(epochs=1), DATA, tiny_model("attention"), tokenizer, torch.device("cpu"))[0]
        for _ in range(2)
    ]

    assert runs[0][0].train_loss == runs[1][0].train_loss


@pytest.mark.parametrize(
    "run",
    [
        RunConfig(head="attention", learning_rate=5e-5, typos=False, state=True),
        RunConfig(head="cosine", learning_rate=2e-5, typos=True, state=False, fold=2, limit=64),
    ],
)
def test_a_config_survives_the_command_line(run: RunConfig) -> None:
    parser = argparse.ArgumentParser()
    add_run_arguments(parser)

    assert config_from(parser.parse_args(run_arguments(run))) == run
