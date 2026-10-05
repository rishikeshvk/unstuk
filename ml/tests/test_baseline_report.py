import json
from pathlib import Path

import pytest
from records import make

from unstuk_ml.baseline_report import Decider, load_test, render
from unstuk_ml.evaluate import Scored
from unstuk_ml.freeze import freeze


def _test_dir(tmp_path: Path) -> Path:
    lines = [make("t1", "no net").model_dump_json(), make("t2", "weather?").model_dump_json()]
    (tmp_path / "chatgpt.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


def test_the_report_names_its_decider_and_why_held_out_scores_as_it_does(tmp_path: Path) -> None:
    decider = Decider("TF-IDF", "unstuk-tfidf", "A linear model", "0% by construction", tmp_path)
    # One line of each kind, so every headline metric has something to score.
    items = [
        Scored(make("a", "no net"), {"no_internet": 0.9}),
        Scored(make("b", "weather?", "out_of_scope"), {"out_of_scope": 0.7}),
        Scored(make("c", "no sound", tags=["vague"]), {"no_internet": 0.4}),
        Scored(make("d", "screen stuck sideways", "screen_wont_rotate"), {}),
    ]

    text = render(decider, items)

    assert text.startswith("# TF-IDF on the proxy test set\n")
    assert "`uv run unstuk-tfidf`" in text
    assert "A linear model, scored on all 4 frozen test lines." in text
    assert "| Held-out intents (0% by construction) |" in text


def test_the_test_set_loads_only_while_it_matches_its_lock(tmp_path: Path) -> None:
    test_dir = _test_dir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_test(test_dir)

    freeze(test_dir)
    assert [r.id for r in load_test(test_dir)] == ["t1", "t2"]

    with (test_dir / "chatgpt.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(make("t3", "edited").model_dump()) + "\n")
    with pytest.raises(ValueError, match="changed after freezing"):
        load_test(test_dir)
