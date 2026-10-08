from pathlib import Path

from records import make

from unstuk_ml.labels import VAGUE
from unstuk_ml.record import Record
from unstuk_ml.vague_slice import agreed, blind_keys, build, read_batches

CELL = {"age": "teen", "comfort": "low", "variety": "indian", "style": "terse", "typos": "many"}


def vague(record_id: str, text: str, labels: list[str], batch: str = "vague-01") -> Record:
    return make(record_id, text, labels=labels, tags=[VAGUE], batch=batch)


def test_reads_sheets_as_vague_records_with_their_persona(tmp_path: Path) -> None:
    (tmp_path / "vague-01.txt").write_text(
        "## no_internet, wifi_no_load, reset_network\nnet  gone\n", encoding="utf-8"
    )

    [record] = read_batches(tmp_path, {"vague-01": CELL})

    assert record.id == "vague-01-001"
    assert record.text == "net gone"
    assert record.labels == ["no_internet", "wifi_no_load", "reset_network"]
    assert record.tags == [VAGUE]
    assert record.persona == CELL


def test_keeps_only_the_readings_both_labellers_gave() -> None:
    record = vague("v-1", "no sound", ["phone_not_ringing", "notifications_missing", "talkback_on"])

    kept = agreed(record, ["notifications_missing", "phone_not_ringing", "screen_too_dim"])

    assert kept is not None
    assert kept.labels == ["phone_not_ringing", "notifications_missing"]


def test_drops_a_line_the_blind_labeller_settled() -> None:
    record = vague("v-1", "no sound", ["phone_not_ringing", "notifications_missing"])

    assert agreed(record, ["phone_not_ringing"]) is None


def test_splits_by_batch_and_drops_held_out_and_leaked_lines() -> None:
    lines = [
        vague("a", "screen looks funny", ["colours_wrong", "screen_too_dim"]),
        vague("b", "whatsapp is not working at all", ["no_internet", "notifications_missing"]),
        vague("c", "phone acting weird today", ["talkback_on", "colours_wrong"], "vague-06"),
        vague("d", "call problem", ["phone_not_ringing", "cant_hear_call"]),
    ]
    blind = {r.id: r.labels for r in lines}
    test = [make("t", "whatsapp is not working at all!", "no_internet")]

    result = build(lines, blind, test)

    assert [r.id for r in result.train] == ["a"]
    assert [r.id for r in result.dev] == ["c"]
    assert {d.record.id for d in result.dropped} == {"b", "d"}


def test_blind_keys_hide_the_batch_order() -> None:
    readings = ["no_internet", "wifi_no_load"]
    lines = [vague(f"vague-01-{n:03d}", f"text {n}", readings) for n in range(20)]

    keys = blind_keys(lines)

    assert list(keys) == [f"v{n:03d}" for n in range(1, 21)]
    assert [r.id for r in keys.values()] != [r.id for r in lines]
