from records import make

from unstuk_ml.evaluate import GateLines, Scored
from unstuk_ml.quantized_test import against_float, float_section

GATE = GateLines(automatic_at=0.75, clarify_below=0.5, clarify_margin=0.0)


def clear(n: int, right: bool = True) -> Scored:
    label = "no_internet" if right else "phone_not_ringing"
    return Scored(make(f"c{n}", "no net"), {label: 0.95, "out_of_scope": 0.05}, GATE)


def oos(n: int) -> Scored:
    return Scored(make(f"o{n}", "book a cab", "out_of_scope"), {"out_of_scope": 0.9}, GATE)


def test_the_same_answers_are_not_worse() -> None:
    items = [clear(n) for n in range(30)] + [oos(n) for n in range(10)]

    rows = against_float(items, items)

    assert all(r.passes for r in rows)
    assert "Not worse than float by the spec's rule: yes" in "\n".join(
        float_section(rows, items, items)
    )


def test_confident_mistakes_on_every_line_are_worse() -> None:
    base = [clear(n) for n in range(30)] + [oos(n) for n in range(10)]
    worse = [clear(n, right=False) for n in range(30)] + [oos(n) for n in range(10)]

    rows = {r.requirement.name: r.passes for r in against_float(worse, base)}

    assert not rows["Confident and wrong"]
    assert not rows["Top-1 accuracy, in scope"]
