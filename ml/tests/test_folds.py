from records import make

from unstuk_ml.catalog import load_catalog
from unstuk_ml.folds import folds, naming, trained_intents, without
from unstuk_ml.labels import HELD_OUT

CATALOG = load_catalog()


def test_trained_intents_leave_out_the_held_out_ones() -> None:
    intents = trained_intents(CATALOG)

    assert len(intents) == 12
    assert not HELD_OUT & set(intents)


def test_folds_split_the_trained_intents_into_three_groups_of_four() -> None:
    groups = folds(trained_intents(CATALOG))

    assert [len(g) for g in groups] == [4, 4, 4]
    assert frozenset().union(*groups) == set(trained_intents(CATALOG))


def test_folds_depend_on_the_seed_not_on_input_order() -> None:
    intents = trained_intents(CATALOG)

    assert folds(intents) == folds(list(reversed(intents)))
    assert folds(intents, seed=1) != folds(intents, seed=2)


def test_a_fold_trains_on_no_line_naming_a_removed_intent_and_scores_those_lines() -> None:
    removed = frozenset({"talkback_on"})
    records = [
        make("a", "phone talks", "talkback_on"),
        make("b", "no net", "no_internet"),
        make("c", "talks and no net", labels=["talkback_on", "no_internet"]),
        make("d", "book a cab", "out_of_scope"),
    ]

    assert [r.id for r in without(records, removed)] == ["b", "d"]
    assert [r.id for r in naming(records, removed)] == ["a", "c"]
