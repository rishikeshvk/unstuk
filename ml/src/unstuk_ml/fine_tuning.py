"""Fine-tuning bge-small with a new head on top (M5 spec section 3), whatever the head.

A run checks dev after every epoch and keeps the epoch with the best dev macro-F1, ties to the
lower log-loss, the rule every rung follows. Its weights are written with their sha256 and the
commit they came from, so a later test score can prove which model it read.
"""

import hashlib
import math
import random
import subprocess
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Protocol, Self

import torch
from pydantic import BaseModel
from torch import nn

from unstuk_ml import rung
from unstuk_ml.validate import DEFAULT_DATA_DIR

REPO_ROOT = DEFAULT_DATA_DIR.parent
RUNS_DIR = REPO_ROOT / "ml" / "runs"
# Written into a Colab bundle, which carries no .git directory.
COMMIT_FILE = REPO_ROOT / "COMMIT"
# The heads start from scratch, so the backbone's fine-tuning rate would barely move them.
HEAD_LEARNING_RATE = 1e-3
WEIGHT_DECAY = 0.01
WARMUP_SHARE = 0.1
MAX_GRADIENT_NORM = 1.0
CHECKPOINT, RESULT = "model.pt", "result.json"


class Batch(Protocol):
    def to(self, device: torch.device) -> Self: ...


class EpochCheck(BaseModel):
    """What every run records after each epoch; a model adds its own dev checks."""

    epoch: int
    train_loss: float
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float
    seconds: float


@dataclass(frozen=True)
class Training[B: Batch, E: EpochCheck]:
    model: nn.Module
    backbone: nn.Module
    learning_rate: float
    """The backbone's rate; everything else learns at `HEAD_LEARNING_RATE`."""
    epochs: int
    seed: int
    steps_per_epoch: int
    batches: Callable[[int], Iterable[B]]
    """One epoch's batches, by epoch number."""
    loss: Callable[[B], torch.Tensor]
    check: Callable[[int, float, float], E]
    """An epoch's dev check, from its number, mean training loss and seconds."""


class RunResult[C: BaseModel, E: EpochCheck](BaseModel):
    config: C
    epochs: list[E]
    chosen_epoch: int
    checkpoint_sha256: str
    commit: str
    device: str


def training_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def parameter_groups(
    model: nn.Module, backbone: nn.Module, learning_rate: float
) -> list[dict[str, Any]]:
    in_backbone = {id(p) for p in backbone.parameters()}
    heads = [p for p in model.parameters() if id(p) not in in_backbone]
    return [
        {"params": list(backbone.parameters()), "lr": learning_rate},
        {"params": heads, "lr": HEAD_LEARNING_RATE},
    ]


def learning_rate_factor(step: int, steps: int) -> float:
    """A linear warm-up over the first tenth of training, then a linear decay to zero."""
    warmup = max(1, int(WARMUP_SHARE * steps))
    if step < warmup:
        return step / warmup
    return max(0.0, (steps - step) / (steps - warmup))


def fine_tune[B: Batch, E: EpochCheck](
    training: Training[B, E], device: torch.device
) -> tuple[list[E], dict[str, torch.Tensor]]:
    """Every epoch's dev check, and the weights of the best epoch."""
    torch.manual_seed(training.seed)
    model = training.model.to(device)
    optimizer = torch.optim.AdamW(
        parameter_groups(model, training.backbone, training.learning_rate),
        weight_decay=WEIGHT_DECAY,
    )
    steps = training.epochs * training.steps_per_epoch
    schedule = torch.optim.lr_scheduler.LambdaLR(
        optimizer, partial(learning_rate_factor, steps=steps)
    )
    # fp16 halves the T4's work; the scaler keeps small gradients from rounding to zero.
    cuda = device.type == "cuda"
    scaler = torch.amp.GradScaler(device.type, enabled=cuda)
    results: list[E] = []
    best: dict[str, torch.Tensor] = {}
    for number in range(training.epochs):
        start = time.perf_counter()
        model.train(True)
        losses = []
        for batch in training.batches(number):
            on_device = batch.to(device)
            with torch.autocast(device.type, dtype=torch.float16, enabled=cuda):
                loss = training.loss(on_device)
            optimizer.zero_grad(set_to_none=True)
            torch.autograd.backward(scaler.scale(loss))
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), MAX_GRADIENT_NORM)
            scaler.step(optimizer)
            scaler.update()
            schedule.step()
            losses.append(loss.item())
        result = training.check(
            number, sum(losses) / len(losses), round(time.perf_counter() - start, 1)
        )
        results.append(result)
        print(result.model_dump_json(), flush=True)
        if rung.best(results) is result:
            best = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    return results, best


def shuffled[T](items: list[T], seed: int, number: int) -> list[T]:
    """The epoch's order, the same for the same seed and epoch on any machine."""
    order = list(items)
    random.Random(f"{seed}/{number}/order").shuffle(order)
    return order


def chunks[T](items: list[T], size: int) -> list[list[T]]:
    return [items[start : start + size] for start in range(0, len(items), size)]


def steps_per_epoch(rows: int, batch_size: int) -> int:
    return math.ceil(rows / batch_size)


def save_run[C: BaseModel, E: EpochCheck](
    directory: Path,
    config: C,
    epochs: list[E],
    weights: dict[str, torch.Tensor],
    device: torch.device,
) -> RunResult[C, E]:
    """Writes `model.pt` and `result.json`; the result names the checkpoint by its sha256."""
    directory.mkdir(parents=True, exist_ok=True)
    checkpoint = directory / CHECKPOINT
    torch.save(weights, checkpoint)
    result = RunResult[C, E](
        config=config,
        epochs=epochs,
        chosen_epoch=rung.best(epochs).epoch,
        checkpoint_sha256=sha256(checkpoint),
        commit=source_commit(),
        device=torch.cuda.get_device_name() if device.type == "cuda" else "cpu",
    )
    (directory / RESULT).write_text(result.model_dump_json(indent=2) + "\n", "utf-8")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_commit() -> str:
    if COMMIT_FILE.exists():
        return COMMIT_FILE.read_text(encoding="utf-8").strip()
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
