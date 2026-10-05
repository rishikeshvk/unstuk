"""Zero-shot intents (M4 spec decision 3): the catalog option closest to the complaint, untrained.

Every intent's option text is offered, the held-out ones included, so this is the only M4 rung
that can name an intent it has never seen an example of.
"""

import argparse
from collections.abc import Callable, Sequence
from dataclasses import replace

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

from unstuk_ml import rung
from unstuk_ml.baseline_report import REPORTS, Decider, Table, load_test, write
from unstuk_ml.catalog import load_catalog
from unstuk_ml.encoder import embed_cached
from unstuk_ml.evaluate import Scored, in_scope_accuracy, macro_f1
from unstuk_ml.labels import OUT_OF_SCOPE
from unstuk_ml.record import Record
from unstuk_ml.temperature import fit_temperature, negative_log_likelihood, softmax

Embed = Callable[[Sequence[str]], NDArray[np.float32]]
# bge's prefix for short queries searching longer passages; whether it helps here is tuned on dev.
INSTRUCTION = "Represent this sentence for searching relevant passages: "
OUT_OF_SCOPE_OPTIONS = (
    "Something else that is not a problem with this phone",
    "A question or request that has nothing to do with fixing the phone's settings",
    "I want help with something other than my phone not working",
)
# Cosines between bge vectors differ by hundredths, so the temperature sits far below 1.
BOUNDS = (0.001, 1.0)
SETTINGS = rung.SETTINGS_DIR / "zero-shot.json"
ZERO_SHOT = Decider(
    title="Zero-shot bge-small",
    command="unstuk-zero-shot test",
    about="The catalog option text (or the out-of-scope option) whose frozen bge-small vector is "
    "closest to the complaint's; nothing trained",
    held_out_note="zero-shot: their options are offered, none was trained",
    report=REPORTS / "zero-shot.md",
)


class Trial(BaseModel):
    instruction: bool
    out_of_scope_option: str
    temperature: float
    dev_macro_f1: float
    dev_log_loss: float
    dev_in_scope_accuracy: float


class Settings(BaseModel):
    instruction: bool
    out_of_scope_option: str
    temperature: float
    grid: list[Trial]


def options(out_of_scope_option: str) -> tuple[list[str], list[str]]:
    """Labels and their texts: every catalog intent, then out of scope."""
    intents = load_catalog().intents
    return [*intents, OUT_OF_SCOPE], [*intents.values(), out_of_scope_option]


def cosines(
    embed: Embed, records: Sequence[Record], texts: Sequence[str], instruction: bool
) -> NDArray[np.float64]:
    prefix = INSTRUCTION if instruction else ""
    complaints = embed([prefix + r.text for r in records])
    return np.asarray(complaints @ embed(texts).T, dtype=np.float64)


def score(
    logits: NDArray[np.float64],
    labels: Sequence[str],
    records: Sequence[Record],
    temperature: float,
) -> list[Scored]:
    probabilities = softmax(logits, temperature)
    return [
        Scored(r, dict(zip(labels, map(float, row), strict=True)))
        for r, row in zip(records, probabilities, strict=True)
    ]


def tune(embed: Embed, dev: Sequence[Record]) -> Settings:
    """Each instruction and out-of-scope wording on dev at its own fitted T; the rung rule picks."""
    trials = []
    for instruction in (False, True):
        for text in OUT_OF_SCOPE_OPTIONS:
            labels, texts = options(text)
            logits = cosines(embed, dev, texts, instruction)
            targets = _targets(labels, dev)
            temperature = fit_temperature(logits, targets, BOUNDS)
            scored = score(logits, labels, dev, temperature)
            trials.append(
                Trial(
                    instruction=instruction,
                    out_of_scope_option=text,
                    temperature=temperature,
                    dev_macro_f1=macro_f1(scored),
                    dev_log_loss=negative_log_likelihood(logits, targets, temperature),
                    dev_in_scope_accuracy=in_scope_accuracy(scored),
                )
            )
    chosen = rung.best(trials)
    return Settings(
        instruction=chosen.instruction,
        out_of_scope_option=chosen.out_of_scope_option,
        temperature=chosen.temperature,
        grid=trials,
    )


def _targets(labels: Sequence[str], records: Sequence[Record]) -> NDArray[np.int64]:
    return np.array([labels.index(r.labels[0]) for r in records], dtype=np.int64)


def _tuning_table(settings: Settings) -> Table:
    rows = [
        [
            "on" if t.instruction else "off",
            f"“{t.out_of_scope_option}”",
            str(t.temperature),
            f"{t.dev_macro_f1:.1%}",
            f"{t.dev_log_loss:.3f}",
            f"{t.dev_in_scope_accuracy:.1%}",
            "**chosen**"
            if (t.instruction, t.out_of_scope_option)
            == (settings.instruction, settings.out_of_scope_option)
            else "",
        ]
        for t in settings.grid
    ]
    header = [
        "Instruction",
        "Out-of-scope option",
        "T",
        "Macro-F1",
        "Log-loss",
        "In-scope accuracy",
        "",
    ]
    return Table(header, rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tune", help=f"choose settings on dev and write {SETTINGS.name}")
    commands.add_parser("test", help="score the frozen test set once with the written settings")
    args = parser.parse_args()

    if args.command == "tune":
        settings = tune(embed_cached, rung.read_clean("dev"))
        SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS.write_text(settings.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(
            f"instruction {settings.instruction}, “{settings.out_of_scope_option}”, "
            f"T={settings.temperature}"
        )
        print(f"written to {SETTINGS}; commit it before running `test`")
        return

    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    lines = load_test()
    labels, texts = options(settings.out_of_scope_option)
    logits = cosines(embed_cached, lines, texts, settings.instruction)
    instruction = "with" if settings.instruction else "without"
    about = (
        f"{ZERO_SHOT.about}. Complaints {instruction} bge's query instruction; out-of-scope option "
        f"“{settings.out_of_scope_option}”; temperature {settings.temperature} fitted on dev"
    )
    write(
        replace(ZERO_SHOT, about=about),
        score(logits, labels, lines, settings.temperature),
        tuning=_tuning_table(settings),
    )
