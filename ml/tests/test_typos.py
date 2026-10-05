import random

from unstuk_ml.typos import add_typo

TEXT = "my phone does not ring anymore"


def one_edit_apart(a: str, b: str) -> bool:
    """True when b is a with one letter dropped, doubled, or swapped with its neighbour."""
    if len(b) == len(a) - 1:
        return any(a[:i] + a[i + 1 :] == b for i in range(len(a)))
    if len(b) == len(a) + 1:
        return any(b[:i] + b[i + 1 :] == a and b[i] == b[i + 1] for i in range(len(b) - 1))
    diffs = [i for i in range(len(a)) if a[i] != b[i]]
    return len(diffs) == 2 and diffs[1] == diffs[0] + 1 and a[diffs[0]] == b[diffs[1]]


def test_every_typo_is_one_letter_edit() -> None:
    rng = random.Random(0)
    for _ in range(300):
        noisy = add_typo(TEXT, rng)

        assert noisy != TEXT
        assert one_edit_apart(TEXT, noisy)


def test_only_letters_are_touched() -> None:
    rng = random.Random(1)
    for _ in range(300):
        noisy = add_typo("my 4g, 5g?!", rng)

        assert [c for c in noisy if not c.isalpha()] == list(" 4, 5?!")


def test_text_without_letters_is_left_alone() -> None:
    assert add_typo("123 ?!", random.Random(2)) == "123 ?!"


def test_the_same_seed_gives_the_same_typo() -> None:
    assert add_typo(TEXT, random.Random(3)) == add_typo(TEXT, random.Random(3))
