# Vague slice

Complaints that could honestly mean two or three problems, where the right reply is "which of these do you mean?"
(guide §8). They are for training and dev only ([M6 spec](../../docs/m6-spec.md), section 1). Before M6, dev had no
vague lines and train had three.

## How it was built

1. Fourteen fresh agents with no project context each wrote 30 lines. Each had one writer persona from the
   diversity grid ([`plan.json`](plan.json)) and read only its rendered [prompt](prompts/vague-v1.md). Each made
   one tool call: the Write of its own sheet in `sheets/`, checked in every transcript. Every line's header
   lists the intents it could mean. `vague-01` to `-07` came first. When the blind check below kept only 102 of
   their 210 lines, `vague-08` to `-14` were added from a second grid draw, before anything was trained.
2. `uv run unstuk-vague-slice ../data/vague blind` writes `blind.tsv` with the 420 texts in shuffled order, under
   keys that hide the batch.
3. A fresh agent labelled those texts by the [labelling guide](../../docs/m3-labelling-guide.md), reading only the
   guide and `blind.tsv`, and wrote [`blind-labels.ndjson`](blind-labels.ndjson). It gave one label to 215 texts,
   two to 192 and three to 13.
4. `uv run unstuk-vague-slice ../data/vague build` keeps a line only if the labeller shares at least two of the
   writer's readings, and gives it just those shared readings, tagged `vague`. It then drops exact duplicates
   and lines within 0.8 of a test line. Batches `vague-06`, `-07`, `-13` and `-14` become `dev.jsonl` and the rest
   `train.jsonl`.

| Stage | Lines |
| --- | --- |
| Written | 420 |
| Settled to one problem (or out of scope) by the blind labeller | −233 |
| Same text with different labels | −2 |
| Close to a test line (0.81) | −1 |
| **Kept** | **184: 135 train, 49 dev** |

Nearly every kept line has two readings (179 of 184). `notifications_missing`, `phone_not_ringing`,
`text_too_small` and `colours_wrong` appear most often. `screen_turns_off_fast`, `wifi_no_load` and
`reset_network` appear least: the labeller usually settled those by guide §5.

The slice lives outside `data/raw/` so that `unstuk-clean`, which reads all of `data/raw/`, leaves M5's train and
dev split unchanged.
