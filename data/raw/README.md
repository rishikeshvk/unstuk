# Training pool, raw

Batches written by fresh agents with no project context (M3 spec section 5), one per cell of the diversity grid
in [`plan.json`](plan.json). Each agent saved its own sheet to `sheets/`; nothing in a sheet is edited by hand.
Each sheet is imported to `<batch>.jsonl` with its grid cell as `persona`. Cleaning (step 8) reads these files and
writes `data/clean/`.

| Batches | Prompt |
| --- | --- |
| `train-01`, `train-02` (pilot) | [v1](prompts/train-v1.md) |
| `train-03` to `train-40` | [v2](prompts/train-v2.md) |
