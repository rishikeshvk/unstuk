# unstuk-ml

Data tooling for Unstuk's decision model: reading the catalog, and checking data files against the
[labelling guide](../docs/m3-labelling-guide.md). See the [M3 spec](../docs/m3-spec.md).

```sh
uv sync                                          # install
uv run ruff check && uv run ruff format --check && uv run mypy src tests && uv run pytest
uv run unstuk-validate ../data                   # check every data file
```

## Training the decision model (M5)

```sh
uv run unstuk-train-decision --head attention --learning-rate 5e-5 --state --limit 64 --epochs 1  # CPU smoke run
uv run unstuk-colab-train decision --head attention --learning-rate 5e-5 --state                 # one run on a Colab T4
```

`unstuk-colab-train` needs the `colab` CLI signed in (`colab sessions` should answer). It ships only committed
files under `ml/`, `catalog/`, `data/clean`, `data/state` and `data/nodes`, so commit first; `data/test` and
`data/real` never leave this machine. Each run writes `result.json` (per-epoch dev metrics, the chosen epoch, the
checkpoint's sha256 and the commit) and `model.pt` to `ml/runs/<run name>/`, which is gitignored. The session is
stopped when the run ends or fails.
