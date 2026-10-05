"""Light text normalisation: only what a keyboard varies, never what a person chose to type."""

import re
import unicodedata

_LOOKALIKES = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
    }
)
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Unicode NFC, plain quotes and dashes, single spaces. Case, typos and slang stay."""
    text = unicodedata.normalize("NFC", text).translate(_LOOKALIKES)
    return _SPACES.sub(" ", text).strip()
