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

## Out of scope and contrast pairs (step 7), 2026-10-05

| Batches | Prompt | Plan | Lines |
| --- | --- | --- | --- |
| `oos-01` to `oos-10` | [oos-v1](prompts/oos-v1.md) | [`plan-oos.json`](plan-oos.json) | 1,200 out of scope |
| `contrast-01` to `contrast-06` | [contrast-v1](prompts/contrast-v1.md) | [`plan-contrast.json`](plan-contrast.json) | 672 (336 pairs; 240 out of scope, 432 across 12 intents) |

Each agent read only its own rendered prompt and wrote only its own sheet (checked in every transcript). The first
of each kind was a pilot, read in full; neither needed a prompt change. No training line mentions rotation, and
the two "clock" lines are WhatsApp's pending icon.

The raw pool is now 6,672 lines: 5,232 across the 12 trained intents and 1,440 out of scope.

**Not done: Google's Mobile Actions fit check.** This environment's network policy blocks `huggingface.co`. The
data is complete without it; the check runs when the host is allowed.
