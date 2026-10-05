"""The TF-IDF rung (M4 spec section 2): word and character n-grams read by logistic regression."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline, make_pipeline

from unstuk_ml import rung
from unstuk_ml.baseline_report import KEYWORDS, REPORTS, Below, Decider
from unstuk_ml.evaluate import Scored
from unstuk_ml.keyword_matcher import load_matcher
from unstuk_ml.record import Record
from unstuk_ml.rung import ClassWeight, Rung


def build(c: float, class_weight: ClassWeight) -> Pipeline:
    features = FeatureUnion(
        [
            ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2))),
            ("characters", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))),
        ]
    )
    return make_pipeline(
        features, LogisticRegression(C=c, class_weight=class_weight, max_iter=5000)
    )


TFIDF = Rung(
    decider=Decider(
        title="TF-IDF + logistic regression",
        command="unstuk-tfidf test",
        about="Word 1-2-grams and character 2-5-grams, read by logistic regression trained on "
        "`data/clean/train.jsonl`",
        held_out_note="no output for them; only a two-problem line whose other problem is "
        "trained can count as right",
        report=REPORTS / "tfidf.md",
    ),
    grid=[(c, w) for c in (0.3, 1.0, 3.0, 10.0, 30.0, 100.0) for w in (None, "balanced")],
    build=build,
    settings=rung.SETTINGS_DIR / "tfidf.json",
)


def keywords_below(lines: list[Record]) -> Below:
    matcher = load_matcher()
    return Below(KEYWORDS, [Scored(r, matcher.choose(r.text)) for r in lines])


def main() -> None:
    rung.main(TFIDF, keywords_below)
