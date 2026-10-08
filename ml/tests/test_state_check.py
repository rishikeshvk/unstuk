from records import make

from unstuk_ml.decision_training import RunConfig
from unstuk_ml.state_check import Verdict, twin, without_state


def test_state_stays_if_surely_better_on_its_test_and_not_surely_worse_on_dev() -> None:
    assert Verdict(state_test=(0.05, 0.30), dev_macro_f1=(-0.02, 0.01)).keeps_state
    assert not Verdict(state_test=(-0.01, 0.30), dev_macro_f1=(-0.02, 0.01)).keeps_state
    assert not Verdict(state_test=(0.05, 0.30), dev_macro_f1=(-0.04, -0.01)).keeps_state


def test_the_twin_is_the_chosen_config_without_state() -> None:
    chosen = RunConfig(head="cosine", learning_rate=5e-5, typos=True, state=True)

    assert twin(chosen) == chosen.model_copy(update={"state": False})
    assert twin(chosen).name == "cosine-lr5e-05-typos"


def test_the_twin_never_sees_a_records_state() -> None:
    records = [make("a", "silent", "phone_not_ringing", state=["dnd_on"]), make("b", "no net")]

    assert [r.state for r in without_state(records)] == [None, None]
    assert [r.text for r in without_state(records)] == ["silent", "no net"]
