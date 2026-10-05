import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from unstuk_ml.node_labels import (
    Label,
    NodeQuestion,
    aosp_labels,
    baseline_accuracy,
    build,
    match,
    oem_labels,
    phone_questions,
    selector_labels,
    split_by_oem,
)

LABELS = [
    Label("wifi", "Wi-Fi", "aosp:values", "aosp"),
    Label("wifi", "Internet", "selectors:pixel", "google"),
    Label("mobile_data", "Internet", "selectors:pixel", "google"),
    Label("mobile_data", "Mobile data", "aosp:values", "aosp"),
    Label("airplane_mode", "Flight mode", "oem-variants", "samsung"),
    Label("airplane_mode", "Aeroplane mode", "oem-variants", "xiaomi"),
    *[Label(f"n{i}", f"Neighbour {i}", "aosp:values", "aosp") for i in range(12)],
]
DESCRIPTIONS = {
    "wifi": "the switch for Wi-Fi",
    "mobile_data": "the switch for mobile data",
    "airplane_mode": "the airplane switch",
}


def test_every_answer_is_an_option_and_no_distractor_belongs_to_the_target() -> None:
    questions = build(LABELS, DESCRIPTIONS)

    own = {"wifi": {"wi-fi", "internet"}, "mobile_data": {"internet", "mobile data"}}
    for q in questions:
        assert q.answer in q.options
        others = {o.lower() for o in q.options if o != q.answer}
        assert not others & own.get(q.target, set())


def test_only_targets_get_questions_and_the_build_is_repeatable() -> None:
    questions = build(LABELS, DESCRIPTIONS)

    assert {q.target for q in questions} == set(DESCRIPTIONS)
    assert questions == build(LABELS, DESCRIPTIONS)


def test_one_maker_is_held_out_for_dev() -> None:
    train, dev = split_by_oem(build(LABELS, DESCRIPTIONS))

    assert {q.oem for q in dev} == {"xiaomi"}
    assert "xiaomi" not in {q.oem for q in train}


def test_a_question_must_have_its_answer_once() -> None:
    with pytest.raises(ValidationError):
        NodeQuestion(
            id="q", target="wifi", question="?", options=["a", "b"], answer="c", source="s", oem="o"
        )


def test_the_baseline_matches_exactly_then_loosely_then_fuzzily() -> None:
    assert match(["Bluetooth", "Wi-Fi"], ["Wi-Fi"]) == "Wi-Fi"
    assert match(["Bluetooth", "wifi"], ["Wi-Fi"]) == "wifi"
    assert match(["Bluetooth", "Aeroplane mode"], ["Airplane mode"]) == "Aeroplane mode"
    assert match(["Bluetooth", "Torch"], ["Flight mode"]) is None


def test_reads_aosp_strings_selectors_and_maker_sheets(tmp_path: Path) -> None:
    (tmp_path / "systemui-values-en-rGB.xml").write_text(
        '<resources><string name="status_bar_airplane" msgid="1">"Aeroplane mode"</string>'
        '<string name="x">Other</string></resources>'
    )
    aosp = aosp_labels(tmp_path, {"airplane_mode": ["systemui:status_bar_airplane"]}, [])
    pixel = selector_labels(
        json.loads(
            '{"quickSettings": {"tiles": {"wifi": {"labels": ["Internet"]}}},'
            ' "settings": {"paths": {"talkback": [{"labels": ["TalkBack"]}]}}}'
        )
    )
    makers = oem_labels("## dnd\nsamsung | Do not disturb\n")

    assert aosp == [Label("airplane_mode", "Aeroplane mode", "aosp:values-en-rGB", "aosp")]
    assert {(lb.item, lb.text) for lb in pixel} == {("wifi", "Internet"), ("talkback", "TalkBack")}
    assert makers == [Label("dnd", "Do not disturb", "oem-variants", "samsung")]


def test_builds_phone_questions_from_dumps_and_scores_the_baseline() -> None:
    dumps: dict[str, dict[str, object]] = {
        "qs": {
            "manufacturer": "motorola",
            "nodes": [
                {"text": "Flight mode", "description": None},
                {"text": "Wi-Fi", "description": "Wi-Fi,Off"},
                {"text": "Torch", "description": None},
            ],
        }
    }
    phone = {
        "quickSettings": {
            "tiles": {
                "airplane_mode": {"labels": ["Flight mode"]},
                "wifi": {"labels": ["Wi-Fi"]},
                "bluetooth": {"labels": ["Bluetooth"]},
            }
        },
        "settings": {"paths": {"talkback": [{"labels": ["TalkBack"]}]}},
    }
    descriptions = {t: t for t in ("airplane_mode", "wifi", "bluetooth", "talkback")}

    questions, missing = phone_questions(dumps, phone, descriptions)

    assert [(q.target, q.answer) for q in questions] == [
        ("airplane_mode", "Flight mode"),
        ("wifi", "Wi-Fi"),
    ]
    assert questions[0].options == ["Flight mode", "Wi-Fi", "Wi-Fi,Off", "Torch"]
    assert missing == [
        "bluetooth on qs: no label on screen matches the selector file",
        "talkback on accessibility: screen not dumped",
    ]
    known = [
        Label("airplane_mode", "Airplane mode", "aosp", "aosp"),
        Label("wifi", "Wi-Fi", "a", "a"),
    ]
    assert baseline_accuracy(questions, known) == [
        ("node-test-qs-airplane_mode", False),
        ("node-test-qs-wifi", True),
    ]
