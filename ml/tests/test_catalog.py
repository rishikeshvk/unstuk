import json

from unstuk_ml.catalog import CATALOG_DIR, load_catalog


def test_reads_every_intent_with_its_option_text() -> None:
    intents = json.loads((CATALOG_DIR / "intents.json").read_text(encoding="utf-8"))

    catalog = load_catalog()

    assert catalog.intents == {intent["id"]: intent["option"] for intent in intents}
    assert len(catalog.intents) == 15


def test_reads_the_checks_that_causes_name() -> None:
    catalog = load_catalog()

    assert "airplane_on" in catalog.checks
    assert "dnd_on" in catalog.checks
    assert "airplane_off" not in catalog.checks


def test_each_check_reads_as_its_fixs_finding() -> None:
    catalog = load_catalog()

    assert set(catalog.findings) == catalog.checks
    assert catalog.findings["dnd_on"] == "Do Not Disturb is on."
