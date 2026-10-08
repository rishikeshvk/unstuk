"""State in or out (M5 spec section 4): the chosen model against its twin trained without state.

Both are scored on the state slice's test, whose complaints only the device state settles, and on
dev, each with its own dev-fitted temperatures. State stays only if it is surely more accurate on
the state test and not surely worse on dev macro-F1. Decided before the main test is scored.
"""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from tokenizers import Tokenizer

from unstuk_ml import rung
from unstuk_ml.backbone import load_backbone
from unstuk_ml.baseline_report import REPORTS
from unstuk_ml.catalog import Catalog, load_catalog
from unstuk_ml.decision_batch import decision_tokenizer
from unstuk_ml.decision_model import DecisionModel
from unstuk_ml.decision_rung import SETTINGS, Settings
from unstuk_ml.decision_scoring import Temperatures, decision_logits, fit_temperatures, predict
from unstuk_ml.decision_training import DecisionRun, RunConfig, noul_input
from unstuk_ml.encoder import download
from unstuk_ml.evaluate import Scored, accuracy, macro_f1, paired_bootstrap
from unstuk_ml.fine_tuning import RESULT, RUNS_DIR, load_weights
from unstuk_ml.folds import trained_intents
from unstuk_ml.record import Record, read_records
from unstuk_ml.validate import DEFAULT_DATA_DIR

STATE_TEST = DEFAULT_DATA_DIR / "state" / "test.jsonl"
REPORT = REPORTS / "state.md"


@dataclass(frozen=True)
class Verdict:
    state_test: tuple[float, float]
    """Paired 95% interval on state-test accuracy, with state minus without."""
    dev_macro_f1: tuple[float, float]
    """Paired 95% interval on dev macro-F1, with state minus without."""

    @property
    def keeps_state(self) -> bool:
        return self.state_test[0] > 0 and self.dev_macro_f1[1] >= 0


def twin(config: RunConfig) -> RunConfig:
    """The same config trained without the state segment."""
    return config.model_copy(update={"state": False})


def without_state(records: Sequence[Record]) -> list[Record]:
    return [r.model_copy(update={"state": None}) for r in records]


@dataclass(frozen=True)
class _Model:
    result: DecisionRun
    model: DecisionModel
    temperatures: Temperatures


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = Settings.model_validate_json(SETTINGS.read_text(encoding="utf-8"))
    catalog = load_catalog()
    tokenizer = decision_tokenizer(download()[1])
    intents = trained_intents(catalog)
    dev, state_test = rung.read_clean("dev"), read_records(STATE_TEST)

    stated = _load(settings.run, catalog, tokenizer, dev)
    stateless = _load(twin(stated.result.config).name, catalog, tokenizer, dev)
    with_state = predict(stated.model, state_test, intents, catalog, tokenizer, stated.temperatures)
    blind = predict(
        stateless.model,
        without_state(state_test),
        intents,
        catalog,
        tokenizer,
        stateless.temperatures,
    )
    dev_with = predict(stated.model, dev, intents, catalog, tokenizer, stated.temperatures)
    dev_without = predict(stateless.model, dev, intents, catalog, tokenizer, stateless.temperatures)
    verdict = Verdict(
        state_test=paired_bootstrap(blind, with_state, accuracy),
        dev_macro_f1=paired_bootstrap(dev_without, dev_with, macro_f1),
    )
    REPORT.write_text(
        _report(
            settings.run,
            stateless.result.config.name,
            with_state,
            blind,
            dev_with,
            dev_without,
            verdict,
        ),
        encoding="utf-8",
    )
    print(f"state {'stays' if verdict.keeps_state else 'goes'}; see {REPORT}")
    if verdict.keeps_state:
        return
    updated = settings.model_copy(
        update={
            "run": stateless.result.config.name,
            "epoch": stateless.result.chosen_epoch,
            "checkpoint_sha256": stateless.result.checkpoint_sha256,
            "commit": stateless.result.commit,
            "choice_temperature": stateless.temperatures.choice,
            "noul_temperature": stateless.temperatures.noul,
        }
    )
    SETTINGS.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"{SETTINGS.name} now names {updated.run}; commit it with the report")


def _load(run: str, catalog: Catalog, tokenizer: Tokenizer, dev: Sequence[Record]) -> _Model:
    """A run's checkpoint, checked by hash, with temperatures fitted on dev."""
    result = DecisionRun.model_validate_json((RUNS_DIR / run / RESULT).read_text("utf-8"))
    model = DecisionModel(load_backbone(), result.config.head, noul_input(result.config))
    model.load_state_dict(load_weights(RUNS_DIR / run, result.checkpoint_sha256))
    intents = trained_intents(catalog)
    logits = decision_logits(model, dev, intents, catalog, tokenizer)
    return _Model(result, model, fit_temperatures(logits, dev, intents))


def _report(
    stated: str,
    stateless: str,
    with_state: Sequence[Scored],
    blind: Sequence[Scored],
    dev_with: Sequence[Scored],
    dev_without: Sequence[Scored],
    verdict: Verdict,
) -> str:
    def interval(bounds: tuple[float, float]) -> str:
        return f"{bounds[0]:+.1%} to {bounds[1]:+.1%}"

    lines = [
        "# State in or out",
        "",
        "Written by `uv run unstuk-state-check`; do not edit by hand. M5 spec section 4: "
        f"`{stated}` against its twin trained without state, `{stateless}`, on the "
        f"{len(with_state)} records of `data/state/test.jsonl` and on dev, each with its own "
        "dev-fitted temperatures. Intervals are paired 95% bootstrap intervals, with state minus "
        "without.",
        "",
        "| Measure | With state | Without | Difference |",
        "| --- | --- | --- | --- |",
        f"| State-test accuracy (clear lines) | {accuracy(with_state):.1%} | {accuracy(blind):.1%} "
        f"| {interval(verdict.state_test)} |",
        f"| Dev macro-F1 | {macro_f1(dev_with):.1%} | {macro_f1(dev_without):.1%} "
        f"| {interval(verdict.dev_macro_f1)} |",
        "",
        f"**State {'stays' if verdict.keeps_state else 'goes'}.** The rule: the state-test "
        "interval lies above 0, and the dev macro-F1 interval does not lie below 0.",
        "",
        "## Each record",
        "",
        "| Complaint | State | Label | With state | Without |",
        "| --- | --- | --- | --- | --- |",
    ]
    for a, b in zip(with_state, blind, strict=True):
        record = a.record
        lines.append(
            f"| {record.text} | {', '.join(record.state or [])} | {', '.join(record.labels)} "
            f"| {a.top[0]} | {b.top[0]} |"
        )
    return "\n".join(lines) + "\n"
