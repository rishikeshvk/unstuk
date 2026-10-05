"""Typo noise for training lines (M5 spec section 2), for the misspellings M4 finding 2 showed."""

import random

EDITS = ("drop", "swap", "double")


def add_typo(text: str, rng: random.Random) -> str:
    """One letter dropped, swapped with the next letter, or doubled."""
    edit = rng.choice(EDITS)
    spots = _spots(text, edit)
    if not spots:
        return text
    i = rng.choice(spots)
    if edit == "drop":
        return text[:i] + text[i + 1 :]
    if edit == "double":
        return text[:i] + text[i] + text[i:]
    return text[:i] + text[i + 1] + text[i] + text[i + 2 :]


def _spots(text: str, edit: str) -> list[int]:
    if edit != "swap":
        return [i for i, c in enumerate(text) if c.isalpha()]
    return [
        i
        for i in range(len(text) - 1)
        if text[i].isalpha() and text[i + 1].isalpha() and text[i] != text[i + 1]
    ]
