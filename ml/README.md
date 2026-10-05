# unstuk-ml

Data tooling for Unstuk's decision model: reading the catalog, and checking data files against the
[labelling guide](../docs/m3-labelling-guide.md). See the [M3 spec](../docs/m3-spec.md).

```sh
uv sync                                          # install
uv run ruff check && uv run ruff format --check && uv run mypy src tests && uv run pytest
uv run unstuk-validate ../data                   # check every data file
```
