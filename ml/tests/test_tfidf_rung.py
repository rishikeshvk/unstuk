import os
import subprocess
import sys

from records import make

from unstuk_ml.record import Record
from unstuk_ml.tfidf_rung import Trial, best, examples, score, train

TEXTS = {
    "no_internet": ["internet not working", "no internet on phone", "internet gone since morning"],
    "screen_too_dim": ["screen too dark", "screen very dim", "cant see screen it is dark"],
    "out_of_scope": ["what is the weather", "book a taxi", "play some music"],
}
TRAIN = [
    make(f"{label}-{i}", text, label)
    for label, texts in TEXTS.items()
    for i, text in enumerate(texts)
]


def _trial(macro_f1: float, log_loss: float) -> Trial:
    return Trial(
        c=1.0,
        class_weight=None,
        dev_macro_f1=macro_f1,
        dev_log_loss=log_loss,
        dev_in_scope_accuracy=0.5,
    )


def test_a_line_with_two_problems_teaches_both() -> None:
    both = make("b", "no net and dark screen", labels=["no_internet", "screen_too_dim"])

    assert examples([both]) == (["no net and dark screen"] * 2, ["no_internet", "screen_too_dim"])


def test_character_ngrams_carry_a_misspelt_word() -> None:
    model = train(TRAIN, c=10.0, class_weight=None)

    [scored] = score(model, 1.0, [make("t", "intrnet not workng")])

    assert scored.top[0] == "no_internet"
    assert set(scored.probabilities) == set(TEXTS)


def test_the_best_trial_is_by_macro_f1_then_log_loss_then_grid_order() -> None:
    first, sharper, same = _trial(0.8, 0.5), _trial(0.8, 0.3), _trial(0.8, 0.3)

    assert best([_trial(0.7, 0.1), first]) is first
    assert best([first, sharper, same]) is sharper


def test_training_and_scoring_do_not_depend_on_string_hashing() -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "import sys; sys.path.insert(0, 'tests')\n"
        "from test_tfidf_rung import TRAIN\n"
        "from records import make\n"
        "from unstuk_ml.tfidf_rung import score, train\n"
        "model = train(TRAIN, c=1.0, class_weight='balanced')\n"
        "print(score(model, 1.5, [make('t', 'screen dark no internet')])[0].probabilities)\n"
    )
    outputs = {
        subprocess.run(
            [sys.executable, "-c", script],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for seed in range(8)
    }

    assert len(outputs) == 1


def test_records_keep_their_order_in_the_scores() -> None:
    model = train(TRAIN, c=1.0, class_weight=None)
    lines: list[Record] = [make("x", "play music"), make("y", "screen dim")]

    assert [s.record.id for s in score(model, 1.0, lines)] == ["x", "y"]
