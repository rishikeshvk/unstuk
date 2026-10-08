from records import make

from unstuk_ml.calibrated_test import against_m5, m5_section, reliability_section
from unstuk_ml.evaluate import Scored

READINGS = ["phone_not_ringing", "notifications_missing"]


def vague(n: int, top: float) -> Scored:
    line = make(f"v{n}", "no sound", labels=READINGS, tags=["vague"])
    rest = (1 - top) / 2
    return Scored(
        line, {"phone_not_ringing": top, "notifications_missing": rest, "talkback_on": rest}
    )


def clear(n: int) -> Scored:
    return Scored(make(f"c{n}", "no net"), {"no_internet": 0.95, "out_of_scope": 0.05})


def oos(n: int) -> Scored:
    return Scored(make(f"o{n}", "book a cab", "out_of_scope"), {"out_of_scope": 0.9})


def test_asking_about_more_vague_lines_with_nothing_else_changed_is_safer() -> None:
    base = [clear(n) for n in range(30)] + [oos(n) for n in range(10)]
    m5 = base + [vague(n, 0.9) for n in range(20)]
    ours = base + [vague(n, 0.4) for n in range(20)]

    rows = against_m5(ours, m5)

    assert [r.passes for r in rows] == [True, True, True, True]
    assert "Safer than M5 by the spec's rule: yes" in "\n".join(m5_section(rows, ours, m5))


def test_the_reliability_table_has_a_row_per_bin() -> None:
    items = [clear(n) for n in range(3)]

    table = reliability_section(items, items)

    assert "| 0.9 to 1.0 | 3 | 100% | 3 | 100% |" in table
    assert sum(line.startswith("| 0.") for line in table) == 10
