from records import make

from unstuk_ml.bar import BAR, BarRow, check
from unstuk_ml.encoder_rung import ENCODER
from unstuk_ml.evaluate import Scored
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.tfidf_rung import TFIDF
from unstuk_ml.zero_shot import ZERO_SHOT


def row(name: str, interval: tuple[float, float]) -> BarRow:
    requirement = next(r for r in BAR if r.name == name)
    return BarRow(requirement, bar=0.5, value=0.5, interval=interval)


def test_better_needs_the_whole_interval_on_the_good_side() -> None:
    assert row("Macro-F1", (0.01, 0.05)).passes
    assert not row("Macro-F1", (-0.01, 0.05)).passes


def test_not_worse_fails_only_when_the_interval_lies_on_the_bad_side() -> None:
    assert row("Out-of-scope recall", (-0.03, 0.01)).passes
    assert not row("Out-of-scope recall", (-0.05, -0.01)).passes
    assert row("Confident and wrong", (-0.01, 0.02)).passes
    assert not row("Confident and wrong", (0.01, 0.04)).passes


def test_the_bar_is_m4s_table() -> None:
    assert [(r.name, r.rung, r.must) for r in BAR] == [
        ("Top-1 accuracy, in scope", ZERO_SHOT.title, "better"),
        ("Macro-F1", ENCODER.decider.title, "better"),
        ("Confident and wrong", TFIDF.decider.title, "not worse"),
        ("Out-of-scope recall", TFIDF.decider.title, "not worse"),
        ("Held-out intents", ZERO_SHOT.title, "not worse"),
        ("Expected calibration error", ZERO_SHOT.title, "not worse"),
    ]


def test_each_requirement_is_checked_against_its_own_baseline() -> None:
    lines = [make(f"l{n}", "x", "no_internet") for n in range(20)]
    right = [Scored(r, {"no_internet": 0.9, OUT_OF_SCOPE: 0.1}) for r in lines]
    wrong = [Scored(r, {"no_internet": 0.1, OUT_OF_SCOPE: 0.9}) for r in lines]
    baselines = {ZERO_SHOT.title: wrong, ENCODER.decider.title: right, TFIDF.decider.title: right}

    rows = {r.requirement.name: r for r in check(right, baselines)}

    assert rows["Top-1 accuracy, in scope"].bar == 0.0
    assert rows["Top-1 accuracy, in scope"].passes
    assert rows["Macro-F1"].interval == (0.0, 0.0)
    assert not rows["Macro-F1"].passes
