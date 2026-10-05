# Mobile Actions subset

Out-of-scope commands from Google's [Mobile Actions](https://huggingface.co/datasets/google/mobile-actions)
dataset, licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: Google, "Mobile Actions"
(2025). Changes: only the user's request text is kept, relabelled `out_of_scope` for Unstuk.

- Source: `dataset.jsonl` at dataset revision `e920309bc2acbc2e99a5e3201cf37df2b9fd9151`, SHA-256
  `91d251ee958cfd295af6c4504c236a3a1ad19517de240c3bc680bacfcbf7e7d9` (9,654 rows). Not committed.
- Built with `uv run unstuk-import-mobile-actions <dataset.jsonl> ../data/raw/mobile-actions/subset.jsonl`.
- Kept: rows with exactly one tool call; 50 per tool from `train` and 10 per tool from `eval`, seeded, for the
  five tools left (flashlight on, flashlight off, contact, email, map): 300 records.
- Left out: `open_wifi_settings` (too close to the Wi-Fi intents to call out of scope with confidence) and
  `create_calendar_event` (dates and times would bias the held-out `wrong_time` intent). 19 email requests still
  mention a meeting time in passing; they are kept, as incidental.

Why so few: none of the dataset's seven tools is a fix Unstuk makes, and its requests are polished commands, not
symptoms. It adds a writing style the generated out-of-scope lines lack; more of it would teach "long polite
request means out of scope".
