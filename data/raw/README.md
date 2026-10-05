# Training pool, raw

Batches written by fresh agents with no project context (M3 spec section 5), one per cell of the diversity grid
in [`plan.json`](plan.json). Each agent saved its own sheet to `sheets/`; nothing in a sheet is edited by hand.
Each sheet is imported to `<batch>.jsonl` with its grid cell as `persona`. Cleaning (step 8) reads these files and
writes `data/clean/`.

| Batches | Prompt |
| --- | --- |
| `train-01`, `train-02` (pilot) | [v1](prompts/train-v1.md) |
| `train-03` to `train-40` | [v2](prompts/train-v2.md) |

## Generated 2026-10-05

4,800 lines: 40 batches × 12 intents × 10, so 400 per intent before cleaning. Each of the 40 agents made exactly
one tool call (its Write), so none read the test set or anything else in the repository. Every grid value appears
in 13 or 14 batches (age, typos) or exactly evenly (comfort, variety), and `style` 6 or 7 times.

Known before cleaning: 47 exact duplicate texts across batches; the word "clock" appears 19 times, as WhatsApp's
pending-message icon in `no_internet` and `wifi_no_load` lines, while the held-out `wrong_time` also uses it, which
the zero-shot test will probe. Prompt v2 cut the echo of definition phrases ("full bars" from 1.7% of lines to
0.5%).
