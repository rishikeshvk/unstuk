from collections import Counter

from unstuk_ml.catalog import load_catalog
from unstuk_ml.field_cards import FREE, load_cards
from unstuk_ml.labels import OUT_OF_SCOPE, VAGUE

# Words that name a setting: a card that uses one tests reading, not describing (m8-spec section 2).
SETTING_NAMES = (
    "airplane",
    "flight mode",
    "do not disturb",
    "silent",
    "talkback",
    "bluetooth",
    "brightness",
    "font",
    "rotat",
    "permission",
    "greyscale",
    "invert",
    "data saver",
    "dns",
)


def test_two_cards_per_intent_and_the_spec_s_mix() -> None:
    abouts = Counter(card.about for card in load_cards())

    assert {i: abouts[i] for i in load_catalog().intents} == dict.fromkeys(
        load_catalog().intents, 2
    )
    assert (abouts[OUT_OF_SCOPE], abouts[VAGUE], abouts[FREE]) == (8, 2, 3)


def test_ids_are_unique() -> None:
    ids = [card.id for card in load_cards()]

    assert len(ids) == len(set(ids))


def test_no_story_names_a_setting_or_uses_its_option_text() -> None:
    options = [text.lower() for text in load_catalog().intents.values()]
    for card in load_cards():
        story = card.story.lower()
        assert not [name for name in SETTING_NAMES if name in story], card.id
        assert not [option for option in options if option in story], card.id
