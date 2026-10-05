# Proxy test set

The final score for every model (M3 spec section 5). Written before any training data, by writers other than the
one that writes training data, and frozen by hash. Nothing here is ever trained on or tuned on.

| Sheet | Writer | Batch | Lines |
| --- | --- | --- | --- |
| `sheets/chatgpt-a.txt`, `chatgpt-b.txt` | ChatGPT, [prompt v1](prompts/external-v1.md) | `test-chatgpt-a`, `-b` | 237 |
| `sheets/gemini-a.txt`, `gemini-b.txt` | Gemini app, same prompt | `test-gemini-a`, `-b` | 238 |
| `sheets/claude-blind.txt` | Claude as a fresh agent with no project context or file access, in place of a hand-written slice; recorded as `generated` | `test-claude-blind` | 100 |
| `sheets/handwritten.txt` | Empty template, kept for a person's slice later | | 0 |

The sheets were committed exactly as returned; the next commit is the review against the guide, so its diff
shows every label change. Training data is written by Claude, so M5 reports scores per writer: a gap between the
Claude sheet and the other two means a model learned a writer's style.

Sheets are the source; each becomes a JSONL file here with `uv run unstuk-import-sheet` (from `ml/`). Once every
sheet is imported, reviewed against the [labelling guide](../../docs/m3-labelling-guide.md) and validated, the set
is frozen with `uv run unstuk-freeze ../data/test`. After that, `unstuk-validate` reports any change.
