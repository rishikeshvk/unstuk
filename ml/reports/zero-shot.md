# Zero-shot bge-small on the proxy test set

Written by `uv run unstuk-zero-shot test`; do not edit by hand. The catalog option text (or the out-of-scope option) whose frozen bge-small vector is closest to the complaint's; nothing trained. Complaints with bge's query instruction; out-of-scope option “A question or request that has nothing to do with fixing the phone's settings”; temperature 0.0309 fitted on dev, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 73.9% | 69.2% to 77.9% |
| Top-1 accuracy, all clear lines | 62.4% | 58.3% to 66.0% |
| Macro-F1 | 65.6% | 61.2% to 69.1% |
| Out-of-scope recall | 33.5% | 26.0% to 40.9% |
| Out-of-scope precision | 68.8% | 57.1% to 78.5% |
| **Confident and wrong** | 3.8% | 2.3% to 5.4% |
| Vague lines answered with a question or decline | 39.3% | 21.7% to 58.6% |
| Expected calibration error | 6.1% | 4.4% to 10.0% |
| Held-out intents (zero-shot: their options are offered, none was trained) | 93.8% | 87.6% to 98.7% |

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 167 | 129 | 89 | 25 |
| out of scope (164) | 14 | 32 | 63 | 55 |
| vague (28) | 6 | 11 | 8 | 3 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 6.8% | 0.0% to 15.9% |
| slice: indian_english | 46 | 82.6% | 69.6% to 91.3% |
| slice: long_story | 39 | 66.7% | 53.8% to 82.1% |
| slice: multi | 33 | 84.8% | 72.7% to 97.0% |
| slice: negation | 39 | 71.8% | 59.0% to 84.6% |
| slice: oos_near | 32 | 28.1% | 15.6% to 43.8% |
| slice: paraphrase | 82 | 72.0% | 62.2% to 80.5% |
| slice: plain | 192 | 68.2% | 62.0% to 75.0% |
| slice: short_vague | 5 | 0.0% | 0.0% to 0.0% |
| slice: typo | 73 | 61.6% | 52.1% to 72.6% |
| writer: chatgpt | 223 | 72.2% | 66.4% to 77.6% |
| writer: claude-blind | 96 | 65.6% | 56.2% to 75.0% |
| writer: gemini | 255 | 52.5% | 46.7% to 58.8% |

## Most common mistakes

- **out_of_scope → screen_too_dim** (16): `My eyes are seeing everything too dark today`; `The food is too hot, how can I cool it down`
- **out_of_scope → screen_turns_off_fast** (16): `The display is flickering after I dropped the phone`; `My battery is finishing very fast`
- **out_of_scope → wrong_time** (15): `My watch is not showing the right time`; `Apps are taking too long to open`
- **phone_not_ringing → cant_hear_call** (11): `People say they called me but I only notice afterwards`; `i dont here any sound for calls only see missd call`
- **out_of_scope → screen_wont_rotate** (10): `The screen rotates even when I don't want it to`; `My phone screen is cracked after it fell down`
- **out_of_scope → talkback_on** (9): `My legs are aching after walking, can you tell me why`; `WhatsApp keeps crashing whenever I open it`
- **out_of_scope → cant_hear_call** (8): `My ear is ringing all day and it is irritating me`; `I cannot hear properly from my left ear`
- **wifi_no_load → no_internet** (6): `My phone shows full WiFi but internet does not work`; `Not asking about mobile data, that I have switched off. The house connection shows full bars yet YouTube says no connection.`
- **screen_turns_off_fast → talkback_on** (6): `The phone locks while I am still using it`; `phone locks while im reding`
- **out_of_scope → colours_wrong** (6): `The colours of this shirt look wrong to me`; `My phone cover has a bright colour and I don't like it`

## Tuning on dev

| Instruction | Out-of-scope option | T | Macro-F1 | Log-loss | In-scope accuracy |  |
| --- | --- | --- | --- | --- | --- | --- |
| off | “Something else that is not a problem with this phone” | 0.0428 | 67.9% | 1.542 | 79.9% |  |
| off | “A question or request that has nothing to do with fixing the phone's settings” | 0.0343 | 69.6% | 1.290 | 78.9% |  |
| off | “I want help with something other than my phone not working” | 0.0315 | 70.4% | 1.188 | 77.0% |  |
| on | “Something else that is not a problem with this phone” | 0.0418 | 67.1% | 1.532 | 79.7% |  |
| on | “A question or request that has nothing to do with fixing the phone's settings” | 0.0309 | 70.6% | 1.173 | 76.3% | **chosen** |
| on | “I want help with something other than my phone not working” | 0.0319 | 69.0% | 1.215 | 76.7% |  |
