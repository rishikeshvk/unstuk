import os
import subprocess
import sys

from records import make

from unstuk_ml.rung import score, train
from unstuk_ml.tfidf_rung import TFIDF

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


def test_character_ngrams_carry_a_misspelt_word() -> None:
    model = train(TFIDF, TRAIN, c=10.0, class_weight=None)

    [scored] = score(model, 1.0, [make("t", "intrnet not workng")])

    assert scored.top[0] == "no_internet"
    assert set(scored.probabilities) == set(TEXTS)


def test_training_and_scoring_do_not_depend_on_string_hashing() -> None:
    # Python salts str hashes per process, so only separate processes expose set-order effects.
    script = (
        "import sys; sys.path.insert(0, 'tests')\n"
        "from test_tfidf_rung import TRAIN\n"
        "from records import make\n"
        "from unstuk_ml.rung import score, train\n"
        "from unstuk_ml.tfidf_rung import TFIDF\n"
        "model = train(TFIDF, TRAIN, c=1.0, class_weight='balanced')\n"
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
