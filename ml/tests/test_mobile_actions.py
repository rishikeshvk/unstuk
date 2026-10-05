from typing import Any

from unstuk_ml.mobile_actions import PER_TOOL, sample


def row(split: str, text: str, *tools: str) -> dict[str, Any]:
    return {
        "metadata": split,
        "messages": [
            {"role": "developer", "content": "You can call functions."},
            {"role": "user", "content": text},
            {"role": "assistant", "tool_calls": [{"function": {"name": t}} for t in tools]},
        ],
    }


def rows_for(split: str, tool: str, count: int) -> list[dict[str, Any]]:
    return [row(split, f"{tool} request {i}", tool) for i in range(count)]


def test_samples_a_fixed_number_per_tool_and_split_as_out_of_scope() -> None:
    rows = rows_for("train", "send_email", 60) + rows_for("eval", "send_email", 15)

    records = sample(rows)

    assert sum(r.batch == "mobile-actions-train" for r in records) == PER_TOOL["train"]
    assert sum(r.batch == "mobile-actions-eval" for r in records) == PER_TOOL["eval"]
    assert {(r.labels[0], r.source, r.generator) for r in records} == {
        ("out_of_scope", "mobile_actions", "google")
    }


def test_skips_multi_call_rows_and_wifi_settings() -> None:
    rows = (
        rows_for("train", "send_email", 50)
        + rows_for("train", "open_wifi_settings", 50)
        + [row("train", "email and map", "send_email", "show_map")] * 50
    )

    texts = {r.text for r in sample(rows)}

    assert all(t.startswith("send_email") for t in texts)


def test_the_sample_is_the_same_every_run() -> None:
    rows = rows_for("train", "show_map", 80)

    assert sample(rows) == sample(rows)
