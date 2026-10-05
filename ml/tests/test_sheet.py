import pytest

from unstuk_ml.sheet import SheetLine, parse_sheet, to_records

SHEET = """\
# written by hand, 2026-10-05
## phone_not_ringing
my phone doesnt ring
nobody can get through, it stays quiet | paraphrase

## no_internet, screen_too_dim | multi
no net and screen too dark | typo
"""


def test_reads_labels_and_tags_from_headers_and_lines() -> None:
    assert parse_sheet(SHEET) == [
        SheetLine("my phone doesnt ring", ["phone_not_ringing"], []),
        SheetLine("nobody can get through, it stays quiet", ["phone_not_ringing"], ["paraphrase"]),
        SheetLine(
            "no net and screen too dark", ["no_internet", "screen_too_dim"], ["multi", "typo"]
        ),
    ]


def test_rejects_a_complaint_before_any_header() -> None:
    with pytest.raises(ValueError, match="line 1"):
        parse_sheet("my phone doesnt ring\n")


def test_numbers_records_within_the_batch() -> None:
    records = to_records(parse_sheet(SHEET), "handwritten", "human", "test-hand-01")

    assert [r.id for r in records] == ["test-hand-01-001", "test-hand-01-002", "test-hand-01-003"]
    assert {(r.source, r.generator, r.batch) for r in records} == {
        ("handwritten", "human", "test-hand-01")
    }


def test_rejects_a_tag_outside_the_contract() -> None:
    with pytest.raises(ValueError, match="unknown tags"):
        to_records(parse_sheet("## no_internet\nno net | sarcasm\n"), "handwritten", "human", "b")
