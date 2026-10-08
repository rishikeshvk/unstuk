"""int8 for the shipped graph, and the dev check it must pass (M7 spec sections 2 and 3).

Dynamic quantization stores weights as int8, one scale per output channel, and quantizes
activations per call, so no calibration data is needed. The check compares the int8 model with
M6's float model on dev, each under its own temperatures, by thresholds written before any run.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic

from unstuk_ml.evaluate import Scored, expected_calibration_error, macro_f1

# Gather reads the embedding tables: a third of the weights.
WITH_EMBEDDINGS = ("MatMul", "Gather")
WITHOUT_EMBEDDINGS = ("MatMul",)

MIN_TOP_AGREEMENT = 0.99
MAX_MACRO_F1_LOSS = 0.01
MAX_ECE_RISE = 0.01
MIN_OUTCOME_AGREEMENT = 0.98


def quantize(float_graph: Path, int8_graph: Path, ops: Sequence[str]) -> None:
    model = onnx.load(float_graph)
    # The exporter's intermediate shapes contradict the quantizer's own inference; ONNX Runtime
    # infers them again on load, so dropping them loses nothing.
    del model.graph.value_info[:]
    quantize_dynamic(
        model,
        int8_graph,
        op_types_to_quantize=list(ops),
        per_channel=True,
        weight_type=QuantType.QInt8,
    )


@dataclass(frozen=True)
class DevCheck:
    top_agreement: float
    """Of every dev line, clear and vague, the share whose top answer is unchanged."""
    macro_f1_change: float
    ece_change: float
    """On clear dev lines; a rise is worse."""
    outcome_agreement: float
    """Of every dev line, the share the gate treats the same way."""

    @property
    def passes(self) -> bool:
        return (
            self.top_agreement >= MIN_TOP_AGREEMENT
            and self.macro_f1_change >= -MAX_MACRO_F1_LOSS
            and self.ece_change <= MAX_ECE_RISE
            and self.outcome_agreement >= MIN_OUTCOME_AGREEMENT
        )


def dev_check(
    float_clear: Sequence[Scored],
    int8_clear: Sequence[Scored],
    float_vague: Sequence[Scored],
    int8_vague: Sequence[Scored],
) -> DevCheck:
    """Each pair scores the same lines in the same order, under the same gate lines."""
    every_float, every_int8 = [*float_clear, *float_vague], [*int8_clear, *int8_vague]
    return DevCheck(
        top_agreement=_agreement(every_float, every_int8, lambda s: s.top[0]),
        macro_f1_change=macro_f1(int8_clear) - macro_f1(float_clear),
        ece_change=expected_calibration_error(int8_clear) - expected_calibration_error(float_clear),
        outcome_agreement=_agreement(every_float, every_int8, lambda s: s.outcome),
    )


def _agreement(
    base: Sequence[Scored], other: Sequence[Scored], answer: Callable[[Scored], str]
) -> float:
    if [s.record.id for s in base] != [s.record.id for s in other]:
        raise ValueError("the two models must score the same lines in the same order")
    return sum(answer(a) == answer(b) for a, b in zip(base, other, strict=True)) / len(base)
