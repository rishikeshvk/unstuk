from records import make

from unstuk_ml.evaluate import GateLines, Scored
from unstuk_ml.figures.gate_outcomes import counts, groups

GATE = GateLines(automatic_at=0.75, clarify_below=0.7, clarify_margin=0.0)


def test_lines_are_split_as_the_results_docs_split_them() -> None:
    clear = Scored(make("c", "no net"), {"no_internet": 0.9}, GATE)
    oos = Scored(make("o", "book a cab", "out_of_scope"), {"out_of_scope": 0.9}, GATE)
    vague = Scored(make("v", "phone is weird", tags=["vague"]), {"no_internet": 0.9}, GATE)

    split = groups([clear, oos, vague])

    assert {k: [s.record.id for s in v] for k, v in split.items()} == {
        "In scope": ["c"],
        "Out of scope": ["o"],
        "Vague": ["v"],
    }


def test_every_outcome_is_counted_even_when_none_happen() -> None:
    sure = Scored(make("a", "no net"), {"no_internet": 0.9}, GATE)
    unsure = Scored(make("b", "no net"), {"no_internet": 0.5}, GATE)

    assert counts([sure, unsure]) == {"automatic": 1, "confirm": 0, "clarify": 1, "decline": 0}
