"""bge-small in PyTorch for fine-tuning (M5 spec section 1): the pinned weights M4 ran through ONNX.

The text side stays M4's: the same `tokenizer.json` through `tokenizers`, and the CLS token's last
hidden state, so training reads the model as the baselines did and as the app will.
"""

from pathlib import Path

from huggingface_hub import hf_hub_download, try_to_load_from_cache
from transformers import BertModel

from unstuk_ml.encoder import HUB_CACHE, REPO, REVISION

WEIGHTS = ("config.json", "model.safetensors")


def load_backbone() -> BertModel:
    """The pinned weights; fetched once, then read from `ml/cache/hub` offline."""
    paths = [hf_hub_download(REPO, n, revision=REVISION, cache_dir=HUB_CACHE) for n in WEIGHTS]
    model: BertModel = BertModel.from_pretrained(Path(paths[0]).parent, add_pooling_layer=False)
    return model


def backbone_downloaded() -> bool:
    return all(
        isinstance(try_to_load_from_cache(REPO, name, cache_dir=HUB_CACHE, revision=REVISION), str)
        for name in WEIGHTS
    )


def freeze_lower(backbone: BertModel, layers: int) -> None:
    """Stops training the embeddings and the lowest layers, so fine-tuning can't move them."""
    if layers == 0:
        return
    frozen = [backbone.embeddings, *backbone.encoder.layer[:layers]]
    for parameter in (p for module in frozen for p in module.parameters()):
        parameter.requires_grad = False
