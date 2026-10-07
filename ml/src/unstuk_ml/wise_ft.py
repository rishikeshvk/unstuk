"""WiSE-FT (M5 spec section 3, round 4): a fine-tuned backbone blended with the frozen one.

weights = alpha * fine-tuned + (1 - alpha) * frozen (Wortsman et al., 2022). Only the backbone is
blended: the heads have no frozen weights to move toward, and zero-shot naming lives in the encoder.
"""

from collections.abc import Mapping

import torch
from torch import nn


def blend(backbone: nn.Module, frozen: Mapping[str, torch.Tensor], alpha: float) -> None:
    """Moves `backbone` in place to `alpha` of the way from `frozen`, its own state dict."""
    state = backbone.state_dict()
    if set(state) != set(frozen):
        raise ValueError("the frozen weights don't match the backbone's tensors")
    backbone.load_state_dict(
        {
            # Integer buffers (token positions) are the same in both and can't be averaged.
            name: alpha * tensor + (1 - alpha) * frozen[name]
            if tensor.is_floating_point()
            else tensor
            for name, tensor in state.items()
        }
    )
