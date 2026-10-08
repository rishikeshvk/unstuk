from records import make

from unstuk_ml.evaluate import Scored
from unstuk_ml.gate_tuning import tune


def line(n: int, label: str, probabilities: dict[str, float], **changes: object) -> Scored:
    return Scored(make(f"l{n}", f"line {n}", label, **changes), probabilities)


def clear_lines() -> list[Scored]:
    """60 right at 0.9, 10 wrong at 0.72 and 10 right at 0.65."""
    right = {"no_internet": 0.9, "wifi_no_load": 0.1}
    wrong = {"wifi_no_load": 0.72, "no_internet": 0.28}
    unsure = {"no_internet": 0.65, "wifi_no_load": 0.35}
    return (
        [line(n, "no_internet", right) for n in range(60)]
        + [line(100 + n, "no_internet", wrong) for n in range(10)]
        + [line(200 + n, "no_internet", unsure) for n in range(10)]
    )


def vague_lines() -> list[Scored]:
    readings = ["phone_not_ringing", "notifications_missing"]
    split = {"phone_not_ringing": 0.58, "notifications_missing": 0.42}
    return [line(300 + n, "", split, labels=readings, tags=["vague"]) for n in range(10)]


def test_automatic_is_the_lowest_line_with_few_wrong_picks() -> None:
    tuning = tune(clear_lines(), vague_lines())

    # 0.7 would pick the 10 wrong lines automatically.
    assert tuning.lines.automatic_at == 0.75
    assert tuning.automatic_wrong == 0.0


def test_the_clarify_lines_catch_vague_splits_within_the_clear_budget() -> None:
    tuning = tune(clear_lines(), vague_lines())

    assert tuning.vague_handled == 1.0
    assert tuning.clear_clarified == 0.0
    # 0.6 alone or 0.3 with a margin of 0.2 both catch a 0.58 to 0.42 split; the smaller wins.
    assert tuning.lines.clarify_below == 0.3
    assert tuning.lines.clarify_margin == 0.2
