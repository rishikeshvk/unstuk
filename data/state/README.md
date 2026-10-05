# State slice

Complaints the words can't settle between two intents, each paired with device states that can (M3 spec section 8).
M5 trains with and without state and compares on `test.jsonl`; if state doesn't help here, it stays out of the
model.

## How it was built

1. A fresh agent wrote 25 complaints per pair ([prompt](prompts/ambiguous-v1.md), [sheet](sheets/ambiguous.txt)),
   reading only its prompt.
2. A second fresh agent labelled the 125 texts blind by the guide, in shuffled order with shuffled keys
   ([labels](blind-labels.ndjson); keys come from `unstuk-state-slice`, which re-derives them from the sheet).
3. `uv run unstuk-state-slice build` kept only texts the labeller left open between both intents of their pair
   (71 of 125), then gave each text a state with one side's deciding check (label = that side) and, for one text in
   three, a state with no deciding check (labels = both, tag `vague`). Half the states also carry a distractor
   check that belongs to neither side. Deciding checks come from the catalog's causes, minus shared checks and the
   held-out intents' checks.
4. Split 70/30 by text, so a text and all its states sit on one side: 117 train and 47 test records.

| Pair | Texts kept | Records |
| --- | --- | --- |
| `phone_not_ringing` / `notifications_missing` | 22 of 25 | 51 |
| `screen_too_dim` / `colours_wrong` | 19 of 25 | 44 |
| `talkback_on` / `colours_wrong` | 25 of 25 | 58 |
| `no_internet` / `notifications_missing` | 5 of 25 | 11 |
| `no_internet` / `wifi_no_load` | 0 of 25 | 0 |

## Finding: the guide settles two pairs by default

The labeller settled every `no_internet` / `wifi_no_load` text with guide §5 ("Wi-Fi not working" without saying
"connected" is `no_internet`), and most `no_internet` / `notifications_missing` texts with §5's "messages and alerts
are `notifications_missing`". So by our label contract the words are never open there. On a real phone the cause
could still be either side (a connected Wi-Fi with a broken Private DNS looks the same to the user as Wi-Fi off),
and the device state would tell them apart. If the model follows §5 and the real cause is the other side,
diagnosis finds nothing and the app says "all clear". Whether §5 should call such complaints vague instead is an
open decision for M5, where the state comparison can show the cost.
