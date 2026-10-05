"""A training run on a Colab GPU (M5 spec section 6), driven through the `colab` CLI.

Only committed training inputs go up, so a run reproduces a commit and the test set never
leaves this machine. The session is stopped even when the run fails, since an idle VM still costs.
"""

import argparse
import io
import subprocess
import tarfile
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from unstuk_ml.decision_training import RunConfig, add_run_arguments, config_from, run_arguments
from unstuk_ml.fine_tuning import CHECKPOINT, COMMIT_FILE, REPO_ROOT, RESULT, RUNS_DIR
from unstuk_ml.fixed_head_rung import GRID as FIXED_HEAD_GRID

SESSION = "unstuk-m5"
GPU = "T4"
SHIPPED = ("ml", "catalog", "data/clean", "data/state", "data/nodes")
NEVER_SHIPPED = ("data/test/", "data/real/")
REMOTE_ROOT = "/content/unstuk"
REMOTE_BUNDLE = "/content/unstuk.tar.gz"
# The CLI gives up after 30 seconds by default; a full run takes most of an hour.
SETUP_TIMEOUT = 15 * 60
RUN_TIMEOUT = 4 * 60 * 60
OUTPUTS = (RESULT, CHECKPOINT)


def shipped_files(repo: Path = REPO_ROOT) -> list[str]:
    """The committed training inputs; refuses uncommitted changes to them."""
    changed = _git(repo, "status", "--porcelain", "--", *SHIPPED)
    if changed:
        raise RuntimeError(f"commit these before training on Colab:\n{changed}")
    files = _git(repo, "ls-files", "--", *SHIPPED).splitlines()
    leaked = [f for f in files if f.startswith(NEVER_SHIPPED)]
    if leaked:
        raise RuntimeError(f"these must never leave this machine: {leaked}")
    return files


def bundle(archive: Path, repo: Path = REPO_ROOT) -> Path:
    """The shipped files, plus the commit they come from (the VM gets no .git directory)."""
    commit = _git(repo, "rev-parse", "HEAD").encode()
    with tarfile.open(archive, "w:gz") as tar:
        for name in shipped_files(repo):
            tar.add(repo / name, arcname=name)
        info = tarfile.TarInfo(COMMIT_FILE.name)
        info.size = len(commit)
        tar.addfile(info, io.BytesIO(commit))
    return archive


def setup_code() -> str:
    """Unpacks the bundle and installs the package; Colab's own CUDA torch stays."""
    return (
        "import pathlib, shutil, subprocess, tarfile\n"
        f"root = pathlib.Path({REMOTE_ROOT!r})\n"
        "if root.exists():\n"
        "    shutil.rmtree(root)\n"
        f"tarfile.open({REMOTE_BUNDLE!r}).extractall(root, filter='data')\n"
        "subprocess.run(['pip', 'install', '-q', '-e', str(root / 'ml')], check=True)\n"
    )


@dataclass(frozen=True)
class ColabRun:
    command: str
    """A console script the package installs on the VM."""
    arguments: tuple[str, ...]
    name: str
    """The run's directory under `ml/runs`, where the command writes its outputs."""


def decision_run(config: RunConfig) -> ColabRun:
    return ColabRun("unstuk-train-decision", tuple(run_arguments(config)), config.name)


def fixed_head_grid() -> list[ColabRun]:
    return [
        ColabRun("unstuk-fixed-head", ("train", *c.arguments()), c.name) for c in FIXED_HEAD_GRID
    ]


def run_code(run: ColabRun) -> str:
    """Runs one training command on the VM, echoing its output line by line as it comes."""
    command = [run.command, *run.arguments, "--out", _remote_runs()]
    return (
        "import subprocess\n"
        f"process = subprocess.Popen({command!r}, stdout=subprocess.PIPE,\n"
        "                           stderr=subprocess.STDOUT, text=True)\n"
        "for line in process.stdout:\n"
        "    print(line, end='', flush=True)\n"
        "if process.wait():\n"
        "    raise SystemExit(process.returncode)\n"
    )


def train_on_colab(runs: Sequence[ColabRun]) -> None:
    """One session for all the runs; each run's outputs come back as soon as it finishes."""
    with tempfile.TemporaryDirectory() as scratch:
        archive = bundle(Path(scratch) / "unstuk.tar.gz")
        _colab("new", "-s", SESSION, "--gpu", GPU)
        try:
            _colab("upload", "-s", SESSION, str(archive), REMOTE_BUNDLE)
            _exec(setup_code(), SETUP_TIMEOUT)
            for run in runs:
                _exec(run_code(run), RUN_TIMEOUT)
                _download(run)
        finally:
            _colab("stop", "-s", SESSION)


def _download(run: ColabRun) -> None:
    local = RUNS_DIR / run.name
    local.mkdir(parents=True, exist_ok=True)
    for name in OUTPUTS:
        _colab("download", "-s", SESSION, f"{_remote_runs()}/{run.name}/{name}", str(local / name))
    print(f"{run.name}: written to {local}", flush=True)


def _remote_runs() -> str:
    return f"{REMOTE_ROOT}/ml/runs"


def _exec(code: str, timeout: int) -> None:
    command = ["colab", "exec", "-s", SESSION, "--timeout", str(timeout)]
    subprocess.run(command, input=code, text=True, check=True)


def _colab(*arguments: str) -> None:
    subprocess.run(["colab", *arguments], check=True)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    jobs = parser.add_subparsers(dest="job", required=True)
    add_run_arguments(jobs.add_parser("decision", help="one decision-model run"))
    jobs.add_parser("fixed-head", help="the fixed-head rung's grid, in one session")
    args = parser.parse_args()

    if args.job == "fixed-head":
        train_on_colab(fixed_head_grid())
    else:
        train_on_colab([decision_run(config_from(args))])
