from records import make

from unstuk_ml.label_issues import flag

INTERNET = ["no internet on my phone", "mobile data is off", "airplane mode is on, nothing loads"]
DARK = ["screen is too dark", "the display is very dim", "brightness is too low to read"]


def test_flags_a_line_whose_label_contradicts_its_words() -> None:
    records = [
        make(f"i{n}-{k}", f"{text} {k}", "no_internet")
        for n, text in enumerate(INTERNET)
        for k in range(10)
    ]
    records += [
        make(f"d{n}-{k}", f"{text} {k}", "screen_too_dim")
        for n, text in enumerate(DARK)
        for k in range(10)
    ]
    records.append(make("wrong", "the screen is too dark and dim", "no_internet"))

    flags = flag(records, seed=3)

    assert "wrong" in {f.record.id for f in flags}
    wrong = next(f for f in flags if f.record.id == "wrong")
    assert wrong.predicted == "screen_too_dim"
    assert wrong.confidence < 0.5
