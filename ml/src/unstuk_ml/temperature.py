"""Temperature scaling: one number that softens or sharpens a classifier's probabilities.

Dividing every logit by the same temperature never changes the top pick, only how sure it looks,
so it fixes overconfidence without touching accuracy (Guo et al., 2017).
"""

import math

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import minimize_scalar
from scipy.special import log_softmax
from scipy.special import softmax as _softmax

# Wide enough for any sane model; the search runs on log T, where halving and doubling are alike.
LOWEST, HIGHEST = 0.05, 20.0


def softmax(logits: NDArray[np.float64], temperature: float) -> NDArray[np.float64]:
    return np.asarray(_softmax(logits / temperature, axis=1), dtype=np.float64)


def negative_log_likelihood(
    logits: NDArray[np.float64], targets: NDArray[np.int64], temperature: float
) -> float:
    """Mean log-loss of the true classes; `targets` holds each row's true column."""
    log_p = log_softmax(logits / temperature, axis=1)
    return float(-log_p[np.arange(len(targets)), targets].mean())


def fit_temperature(logits: NDArray[np.float64], targets: NDArray[np.int64]) -> float:
    """The temperature with the lowest log-loss on these lines, rounded to be written down."""
    result = minimize_scalar(
        lambda log_t: negative_log_likelihood(logits, targets, math.exp(log_t)),
        bounds=(math.log(LOWEST), math.log(HIGHEST)),
        method="bounded",
    )
    return round(math.exp(float(result.x)), 4)
