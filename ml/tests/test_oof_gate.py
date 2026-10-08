import numpy as np
from records import make

from unstuk_ml.decision_scoring import Logits
from unstuk_ml.evaluate import Scored
from unstuk_ml.oof_gate import FoldScores, Guard, TwoFeatureGate, declined, fit_out_of_fold, guard

INTENTS = ["no_internet", "screen_too_dim"]
DEV = [
    *(make(f"i{n}", "no net", "no_internet") for n in range(20)),
    *(make(f"d{n}", "too dark", "screen_too_dim") for n in range(20)),
    *(make(f"o{n}", "book a cab", "out_of_scope") for n in range(20)),
]


def fold(removed: str) -> FoldScores:
    """A fold model: sure on its trained intent; a removed intent's lines fit less well and its
    complaint-only Noul leans out of scope, as in M5; out-of-scope lines fit nothing."""
    choice, noul = [], []
    for record in DEV:
        label = record.labels[0]
        right = [3.0 if i == label else 0.0 for i in INTENTS]
        if label == "out_of_scope":
            choice.append([0.0, 0.0])
            noul.append(3.0)
        elif label == removed:
            choice.append([r / 2 for r in right])
            noul.append(0.5)
        else:
            choice.append(right)
            noul.append(-3.0)
    return FoldScores(Logits(np.array(choice), np.array(noul)), frozenset({removed}))


def test_a_gate_fitted_out_of_fold_keeps_unseen_intents_in_scope() -> None:
    folds_scores = [fold("no_internet"), fold("screen_too_dim")]
    full = fold("none").logits

    result = guard(folds_scores, full, DEV, INTENTS)

    assert result.unseen_declined == [0.0, 0.0]
    assert result.unseen_accuracy == [1.0, 1.0]
    assert result.gate_recall == result.noul_recall == 1.0
    assert result.passes


def test_the_gate_reads_both_features() -> None:
    gate = TwoFeatureGate(choice_weight=-1.0, noul_weight=2.0, bias=0.5)
    logits = Logits(np.array([[1.0, 3.0]]), np.array([4.0]))

    assert gate.apply(logits).out_of_scope.tolist() == [-3.0 + 8.0 + 0.5]
    assert fit_out_of_fold([fold("no_internet")], DEV).noul_weight > 0


def test_declined_counts_lines_whose_top_answer_is_out_of_scope() -> None:
    line = DEV[0]
    items = [
        Scored(line, {"no_internet": 0.6, "out_of_scope": 0.4}),
        Scored(line, {"no_internet": 0.3, "out_of_scope": 0.7}),
    ]

    assert declined(items) == 0.5


def test_the_guard_fails_on_too_many_declines_or_too_much_lost_recall() -> None:
    fine = Guard([0.05, 0.1, 0.1], [0.8] * 3, noul_recall=0.95, gate_recall=0.94)

    assert fine.passes
    assert not Guard([0.2, 0.1, 0.1], [0.8] * 3, noul_recall=0.95, gate_recall=0.95).passes
    assert not Guard([0.0] * 3, [0.8] * 3, noul_recall=0.95, gate_recall=0.92).passes
