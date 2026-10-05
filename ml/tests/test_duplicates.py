from records import make

from unstuk_ml.duplicates import exact_duplicates, leaking, near_duplicates


def test_keeps_the_first_of_an_exact_repeat() -> None:
    first, again = make("a", "No internet"), make("b", "no internet ")

    kept, dropped = exact_duplicates([first, again])

    assert kept == [first]
    assert [(d.record.id, d.reason) for d in dropped] == [("b", "exact duplicate of a")]


def test_drops_every_copy_when_labels_disagree() -> None:
    kept, dropped = exact_duplicates(
        [make("a", "no sound"), make("b", "no sound", "phone_not_ringing")]
    )

    assert kept == []
    assert {d.reason for d in dropped} == {"same text, different labels"}


def test_drops_near_duplicates_with_the_same_label() -> None:
    background = [make(f"x{n}", f"unrelated line number {n} about something") for n in range(30)]
    records = [
        make("a", "my wifi is off and nothing loads at all"),
        make("b", "my wifi is off and nothing loads at all!"),
        *background,
    ]

    kept, dropped = near_duplicates(records, threshold=0.9)

    assert "b" not in {r.id for r in kept}
    assert dropped[0].reason == "near duplicate of a"


def test_keeps_near_duplicates_with_different_labels() -> None:
    records = [
        make("a", "the wifi has gone off and nothing will open"),
        make("b", "the wifi says connected and nothing will open", "wifi_no_load"),
    ]

    kept, _ = near_duplicates(records, threshold=0.5)

    assert [r.id for r in kept] == ["a", "b"]


def test_flags_training_lines_close_to_a_test_line() -> None:
    train = [make("a", "whatsapp not sending messages today"), make("b", "screen is too dark")]
    test = [make("t", "whatsapp is not sending messages today", batch="test-x")]

    dropped = leaking(train, test, threshold=0.8)

    assert [d.record.id for d in dropped] == ["a"]
    assert dropped[0].reason.startswith("close to test t")
