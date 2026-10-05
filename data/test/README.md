# Proxy test set

The final score for every model (M3 spec section 5). Written before any training data, by writers other than the
one that writes training data, and frozen by hash. Nothing here is ever trained on or tuned on.

| Sheet | Writer | Batch |
| --- | --- | --- |
| `sheets/handwritten.txt` | You, by hand | `test-hand-01` |
| `sheets/gemini-a.txt`, `gemini-b.txt` | Gemini app, [prompt v1](prompts/external-v1.md) | `test-gemini-01` |
| `sheets/<open model>-a.txt`, `-b.txt` | An open model in opencode, same prompt | `test-<model>-01` |

Sheets are the source; each becomes a JSONL file here with `uv run unstuk-import-sheet` (from `ml/`). Once every
sheet is imported, reviewed against the [labelling guide](../../docs/m3-labelling-guide.md) and validated, the set
is frozen with `uv run unstuk-freeze ../data/test`. After that, `unstuk-validate` reports any change.
