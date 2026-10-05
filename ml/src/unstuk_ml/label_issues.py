"""Lines whose label a simple model doubts: confident learning (Northcutt et al.) via cleanlab."""

from collections.abc import Sequence
from dataclasses import dataclass

from cleanlab.filter import find_label_issues
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from unstuk_ml.record import Record

FOLDS = 5


@dataclass(frozen=True)
class Flag:
    record: Record
    predicted: str
    confidence: float
    """The model's probability for the given label: low means it doubts the label."""


def flag(records: Sequence[Record], seed: int) -> list[Flag]:
    """Out-of-fold probabilities, so no line is judged by a model that saw it; single-label only."""
    single = [r for r in records if len(r.labels) == 1]
    labels = sorted({r.labels[0] for r in single})
    targets = [labels.index(r.labels[0]) for r in single]
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2),
        LogisticRegression(max_iter=2000, C=4.0),
    )
    folds = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=seed)
    probs = cross_val_predict(
        model, [r.text for r in single], targets, cv=folds, method="predict_proba"
    )
    # cleanlab's worker processes fork; forking after onnxruntime is loaded can deadlock.
    issues = find_label_issues(targets, probs, return_indices_ranked_by="self_confidence", n_jobs=1)
    return [
        Flag(single[i], labels[int(probs[i].argmax())], float(probs[i][targets[i]])) for i in issues
    ]
