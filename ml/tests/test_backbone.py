import numpy as np
import pytest
import torch
from tokenizers import Tokenizer

from unstuk_ml.backbone import backbone_downloaded, load_backbone
from unstuk_ml.encoder import download, downloaded, load_encoder

pytestmark = pytest.mark.skipif(
    not (downloaded() and backbone_downloaded()),
    reason="bge-small isn't in ml/cache/hub; run load_backbone() and encoder.download()",
)

TEXTS = ["my phone doesn't ring", "Wi-Fi is connected but websites and apps don't load"]


def test_pytorch_reads_the_model_as_the_onnx_baselines_did() -> None:
    tokenizer = Tokenizer.from_file(str(download()[1]))
    backbone = load_backbone()
    assert not backbone.training
    for text, expected in zip(TEXTS, load_encoder().embed(TEXTS), strict=True):
        encoding = tokenizer.encode(text)
        with torch.no_grad():
            hidden = backbone(
                input_ids=torch.tensor([encoding.ids]),
                attention_mask=torch.tensor([encoding.attention_mask]),
                token_type_ids=torch.tensor([encoding.type_ids]),
            ).last_hidden_state
        cls = hidden[0, 0].numpy()

        assert np.allclose(cls / np.linalg.norm(cls), expected, atol=1e-4)
