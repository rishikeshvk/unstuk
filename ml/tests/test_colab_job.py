import subprocess
import tarfile
from pathlib import Path

import pytest

from unstuk_ml.colab_job import bundle, decision_run, run_code, setup_code, shipped_files
from unstuk_ml.decision_training import RunConfig, run_arguments

FILES = {
    "ml/pyproject.toml": "[project]\n",
    "catalog/intents.json": "[]\n",
    "data/clean/train.jsonl": "{}\n",
    "data/test/test-a.jsonl": "{}\n",
    "android/build.gradle.kts": "\n",
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for name, text in FILES.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text)
    for command in (
        ["init", "-q"],
        ["add", "."],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"],
    ):
        subprocess.run(["git", *command], cwd=tmp_path, check=True)
    return tmp_path


def test_only_committed_training_inputs_are_shipped(repo: Path) -> None:
    assert sorted(shipped_files(repo)) == [
        "catalog/intents.json",
        "data/clean/train.jsonl",
        "ml/pyproject.toml",
    ]


def test_uncommitted_changes_to_training_inputs_stop_the_job(repo: Path) -> None:
    (repo / "catalog" / "intents.json").write_text("[1]\n")

    with pytest.raises(RuntimeError, match=r"intents\.json"):
        shipped_files(repo)


def test_changes_outside_the_training_inputs_dont_matter(repo: Path) -> None:
    (repo / "android" / "build.gradle.kts").write_text("changed\n")

    assert "ml/pyproject.toml" in shipped_files(repo)


def test_the_bundle_carries_the_commit_and_never_the_test_set(repo: Path, tmp_path: Path) -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    with tarfile.open(bundle(tmp_path / "b.tar.gz", repo)) as tar:
        names = tar.getnames()
        commit = tar.extractfile("COMMIT")
        assert commit is not None
        assert commit.read().decode() == head
    assert not [n for n in names if n.startswith("data/test")]


def test_the_remote_code_is_python_that_runs_the_configs_command() -> None:
    config = RunConfig(head="attention", learning_rate=5e-5, typos=False, state=True, fold=1)

    code = run_code(decision_run(config))

    compile(setup_code(), "setup", "exec")
    compile(code, "run", "exec")
    assert repr(["unstuk-train-decision", *run_arguments(config)])[:-1] in code
    assert decision_run(config).name == config.name
