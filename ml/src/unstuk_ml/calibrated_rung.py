"""The calibrated decision model (M6 spec sections 3 to 6): M5's chosen config, trained on the vague
slice too, with a Brier term of weight λ beside each head's log-loss; then out of scope and the
gate's lines, all chosen on dev.

λ = 0 adds only the vague lines, so comparing it with M5 isolates what they do.
"""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from unstuk_ml import rung
from unstuk_ml.backbone import load_backbone
from unstuk_ml.catalog import load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.decision_rung import SETTINGS as M5_SETTINGS
from unstuk_ml.decision_rung import Settings as M5Settings
from unstuk_ml.decision_rung import runs_of
from unstuk_ml.decision_scoring import (
    Logits,
    Temperatures,
    decision_logits,
    fit_temperatures,
    log_loss,
    scored,
)
from unstuk_ml.decision_training import DecisionRun, RunConfig, noul_input
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import GATE_FILE, brier_score
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.folds import trained_intents
from unstuk_ml.gate_tuning import tune
from unstuk_ml.oof_gate import TwoFeatureGate, run_guard
from unstuk_ml.record import Record, read_records
from unstuk_ml.validate import DEFAULT_DATA_DIR

BRIER_WEIGHTS = (0.0, 0.5, 1.0)
CONFIGS = [
    RunConfig(
        head="cosine", learning_rate=5e-5, typos=True, state=True, vague=True, brier_weight=weight
    )
    for weight in BRIER_WEIGHTS
]
GRID = [run for config in CONFIGS for run in runs_of(config)]
# Dev macro-F1 may fall at most this far below M5's to buy calibration.
MAX_MACRO_F1_LOSS = 0.01
SETTINGS = rung.SETTINGS_DIR / "calibrated.json"


class WeightRow(BaseModel):
    run: str
    brier_weight: float
    epoch: int
    dev_macro_f1: float
    dev_log_loss: float
    dev_brier: float
    eligible: bool


class GuardRow(BaseModel):
    run: str
    unseen_declined: list[float]
    unseen_accuracy: list[float]
    noul_recall: float
    gate_recall: float
    passes: bool


class Settings(BaseModel):
    run: str
    epoch: int
    checkpoint_sha256: str
    commit: str
    choice_temperature: float
    out_of_scope: Literal["noul", "out-of-fold gate"]
    noul_temperature: float | None
    gate: dict[str, float] | None
    """The out-of-fold gate's weights, when it passed its guard."""
    lines: dict[str, float]
    """The gate's tuned lines, as written to `catalog/gate.json`."""
    automatic_wrong: float
    clear_clarified: float
    vague_handled: float
    weights: list[WeightRow]
    guards: list[GuardRow]


def pick(rows: Sequence[WeightRow]) -> WeightRow:
    """The lowest dev Brier among eligible rows, ties to the lower log-loss."""
    eligible = [r for r in rows if r.eligible]
    if not eligible:
        raise ValueError("every Brier weight loses more than a point of dev macro-F1")
    return min(eligible, key=lambda r: (r.dev_brier, r.dev_log_loss))


def choose(runs: Path = RUNS_DIR) -> Settings:
    catalog = load_catalog()
    intents = trained_intents(catalog)
    tokenizer = decision_tokenizer(download()[1])
    dev = rung.read_clean("dev")
    vague_dev = read_records(DEFAULT_DATA_DIR / "vague" / "dev.jsonl")
    m5 = M5Settings.model_validate_json(M5_SETTINGS.read_text(encoding="utf-8"))
    m5_macro_f1 = next(row.dev_macro_f1 for row in m5.grid if row.run == m5.run)

    def logits_on(config: RunConfig, lines: Sequence[Record]) -> Logits:
        result = _result(runs, config)
        model = DecisionModel(load_backbone(), config.head, noul_input(config))
        model.load_state_dict(load_weights(runs / config.name, result.checkpoint_sha256))
        return decision_logits(model, lines, intents, catalog, tokenizer)

    rows = []
    for config in CONFIGS:
        result = _result(runs, config)
        logits = logits_on(config, dev)
        items = scored(logits, dev, intents, fit_temperatures(logits, dev, intents))
        kept = result.epochs[result.chosen_epoch]
        rows.append(
            WeightRow(
                run=config.name,
                brier_weight=config.brier_weight,
                epoch=result.chosen_epoch,
                dev_macro_f1=kept.dev_macro_f1,
                dev_log_loss=log_loss(items),
                dev_brier=brier_score(items),
                eligible=kept.dev_macro_f1 >= m5_macro_f1 - MAX_MACRO_F1_LOSS,
            )
        )
    best = pick(rows)
    config = next(c for c in CONFIGS if c.name == best.run)
    guards = []
    chosen_gate: TwoFeatureGate | None = None
    for guarded in [m5.run, *(c.name for c in CONFIGS)]:
        guard, gate = run_guard(_result(runs, guarded).config, runs)
        guards.append(GuardRow(run=guarded, passes=guard.passes, **asdict(guard)))
        if guarded == config.name and guard.passes:
            chosen_gate = gate

    logits = logits_on(config, dev)
    temperatures = fit_temperatures(logits, dev, intents)
    vague_logits = logits_on(config, vague_dev)
    if chosen_gate is not None:
        temperatures = Temperatures(choice=temperatures.choice, noul=1.0)
        logits, vague_logits = chosen_gate.apply(logits), chosen_gate.apply(vague_logits)
    clear_items = scored(logits, dev, intents, temperatures)
    vague_items = scored(vague_logits, vague_dev, intents, temperatures)
    tuning = tune(clear_items, vague_items)
    result = _result(runs, config)
    return Settings(
        run=config.name,
        epoch=result.chosen_epoch,
        checkpoint_sha256=result.checkpoint_sha256,
        commit=result.commit,
        choice_temperature=temperatures.choice,
        out_of_scope="noul" if chosen_gate is None else "out-of-fold gate",
        noul_temperature=None if chosen_gate else temperatures.noul,
        gate=asdict(chosen_gate) if chosen_gate else None,
        lines=asdict(tuning.lines),
        automatic_wrong=tuning.automatic_wrong,
        clear_clarified=tuning.clear_clarified,
        vague_handled=tuning.vague_handled,
        weights=rows,
        guards=guards,
    )


def _result(runs: Path, config: RunConfig | str) -> DecisionRun:
    name = config if isinstance(config, str) else config.name
    return DecisionRun.model_validate_json((runs / name / RESULT).read_text(encoding="utf-8"))


def write(settings: Settings) -> None:
    SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
    GATE_FILE.write_text(json.dumps(settings.lines, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = choose()
    for row in settings.weights:
        mark = "" if row.eligible else " (loses more than a point of macro-F1)"
        print(
            f"{row.run}: dev macro-F1 {row.dev_macro_f1:.1%}, log-loss {row.dev_log_loss:.4f}, "
            f"Brier {row.dev_brier:.4f}{mark}"
        )
    for guard in settings.guards:
        declined = sum(guard.unseen_declined) / len(guard.unseen_declined)
        print(
            f"out-of-fold gate on {guard.run}: {declined:.1%} of unseen declined, recall "
            f"{guard.gate_recall:.1%} against Noul's {guard.noul_recall:.1%}: "
            f"{'passes' if guard.passes else 'fails'}"
        )
    print(f"chose {settings.run}, out of scope by {settings.out_of_scope}")
    print(
        f"gate lines {settings.lines}: automatic picks wrong {settings.automatic_wrong:.1%}, "
        f"clear lines clarified {settings.clear_clarified:.1%}, "
        f"vague handled {settings.vague_handled:.1%}"
    )
    write(settings)
    print(f"written to {SETTINGS} and {GATE_FILE}; commit both before scoring the test")
