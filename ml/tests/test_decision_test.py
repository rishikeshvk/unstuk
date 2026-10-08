from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_rung import SETTINGS, Settings
from unstuk_ml.decision_test import guard_note, offered
from unstuk_ml.labels import HELD_OUT


def test_every_catalog_intent_is_offered_in_catalog_order() -> None:
    catalog = load_catalog()

    assert offered(catalog) == list(catalog.intents)
    assert set(offered(catalog)) >= HELD_OUT
    assert len(offered(catalog)) == 15


def test_a_model_chosen_without_the_guard_says_so() -> None:
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))

    unguarded = "\n".join(guard_note(settings.model_copy(update={"guarded": False})))
    guarded = "\n".join(guard_note(settings.model_copy(update={"guarded": True})))

    assert "Without the zero-shot guard" in unguarded
    assert "expected to fail" in unguarded
    assert "Without" not in guarded
