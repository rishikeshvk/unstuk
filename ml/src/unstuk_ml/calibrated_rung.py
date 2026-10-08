"""The calibrated decision model (M6 spec section 3): M5's chosen config, trained on the vague
slice too, with a Brier term of weight λ beside each head's log-loss.

λ = 0 adds only the vague lines, so comparing it with M5 isolates what they do.
"""

from unstuk_ml.decision_rung import runs_of
from unstuk_ml.decision_training import RunConfig

BRIER_WEIGHTS = (0.0, 0.5, 1.0)
CONFIGS = [
    RunConfig(
        head="cosine", learning_rate=5e-5, typos=True, state=True, vague=True, brier_weight=weight
    )
    for weight in BRIER_WEIGHTS
]
GRID = [run for config in CONFIGS for run in runs_of(config)]
