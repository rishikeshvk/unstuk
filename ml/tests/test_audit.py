import pytest
from records import make

from unstuk_ml.audit import agreement, sample


def test_counts_a_line_as_agreed_when_the_blind_label_is_among_the_given() -> None:
    result = agreement(
        [["no_internet"], ["no_internet", "screen_too_dim"], ["out_of_scope"]],
        [["no_internet"], ["screen_too_dim"], ["text_too_small"]],
    )

    assert (result.agreed, result.total) == (2, 3)
    assert result.share == pytest.approx(2 / 3)


def test_perfect_agreement_has_kappa_one() -> None:
    labels = [["no_internet"], ["out_of_scope"], ["talkback_on"]]

    assert agreement(labels, labels).kappa == pytest.approx(1.0)


def test_the_sample_is_the_same_every_run() -> None:
    records = [make(f"r{n}", f"line {n}") for n in range(300)]

    assert sample(records) == sample(records)
    assert len(sample(records)) == 200
