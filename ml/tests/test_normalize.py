from unstuk_ml.normalize import normalize


def test_plain_quotes_dashes_and_single_spaces() -> None:
    # The curly quotes and dash are the point of this test.
    assert normalize("  it’s  “dead” — again\n") == 'it\'s "dead" - again'  # noqa: RUF001


def test_keeps_what_the_person_typed() -> None:
    assert normalize("Net NOT wrking sinse mrng!!") == "Net NOT wrking sinse mrng!!"
