# int8 decision graph on the proxy test set

Written by `uv run unstuk-quantized-test`; do not edit by hand. M6's calibrated model as the int8 ONNX graph the app runs, behind gate lines re-tuned on it; `decision.int8-matmul.onnx` (sha256 `dbfec62fd18a…`) from run `cosine-lr5e-05-typos-state-vague-brier1`, commit `6985ab3`, gate lines {'automatic_at': 0.6, 'clarify_below': 0.6, 'clarify_margin': 0.35}, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 87.8% | 84.5% to 91.1% |
| Top-1 accuracy, all clear lines | 89.0% | 86.2% to 91.7% |
| Macro-F1 | 88.6% | 85.5% to 91.3% |
| Out-of-scope recall | 92.1% | 87.5% to 95.9% |
| Out-of-scope precision | 87.3% | 82.1% to 92.3% |
| **Confident and wrong** | 4.2% | 2.6% to 5.9% |
| Vague lines answered with a question or decline | 21.4% | 7.7% to 37.9% |
| Expected calibration error | 4.1% | 2.4% to 6.5% |
| Held-out intents (their options are offered; none was trained) | 73.8% | 64.2% to 83.0% |
| Expected calibration error, before temperature | 3.9% | 2.8% to 6.6% |

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 354 | 0 | 34 | 22 |
| out of scope (164) | 9 | 0 | 4 | 151 |
| vague (28) | 22 | 0 | 4 | 2 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 88.6% | 79.5% to 97.7% |
| slice: indian_english | 46 | 87.0% | 76.1% to 95.7% |
| slice: long_story | 39 | 89.7% | 79.5% to 97.4% |
| slice: multi | 33 | 97.0% | 90.9% to 100.0% |
| slice: negation | 39 | 79.5% | 66.7% to 92.3% |
| slice: oos_near | 32 | 84.4% | 71.9% to 96.9% |
| slice: paraphrase | 82 | 81.7% | 73.2% to 90.2% |
| slice: plain | 192 | 94.8% | 91.7% to 97.4% |
| slice: short_vague | 5 | 100.0% | 100.0% to 100.0% |
| slice: typo | 73 | 84.9% | 76.7% to 93.2% |
| writer: chatgpt | 223 | 94.2% | 90.6% to 96.9% |
| writer: claude-blind | 96 | 91.7% | 85.4% to 96.9% |
| writer: gemini | 255 | 83.5% | 78.8% to 88.2% |

## Most common mistakes

- **cant_hear_call → phone_not_ringing** (4): `The call is connected but I am getting no useful sound from the person speaking`; `call connects but othr person voice not coming propely`
- **cant_hear_call → out_of_scope** (4): `cant here the person on call`; `The person speaking to me is too quiet to understand.`
- **text_too_small → out_of_scope** (4): `writing on the phone is very fine, my eyes are paining while reading`; `The writing is completely microscopic and impossible to make out.`
- **wrong_time → out_of_scope** (4): `the date at the top says 2019 and my bank site says something about a certificate`; `clck is 2 hrs behnd how fix`
- **colours_wrong → screen_too_dim** (3): `It's not night mode, I know what that looks like. My pictures look like negatives from the old camera film.`; `evrythng is negtive n looks scary`
- **screen_too_dim → text_too_small** (2): `I can hardly make out what is on the screen`; `lit keeps going awy very hard to read`
- **out_of_scope → screen_wont_rotate** (2): `The screen rotates even when I don't want it to`; `When I lie down in bed, the display spins around when I don't want it to.`
- **out_of_scope → phone_not_ringing** (2): `How do I stop the alarm from ringing every day`; `My caller tune is not playing Bollywood songs for my friends.`
- **out_of_scope → screen_turns_off_fast** (2): `My phone freezes when I try to open settings`; `Apps are taking too long to open`
- **wifi_no_load → no_internet** (2): `Not asking about mobile data, that I have switched off. The house connection shows full bars yet YouTube says no connection.`; `Only showing the full symbol but practically it is not working at all.`

## Against M6's float model

Pre-registered in the M7 spec, section 4. Each model is under its own temperatures and lines; differences are int8 minus float, with paired 95% intervals.

| Metric | Float | int8 | Difference | Must | Passes |
| --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 89.5% | 87.8% | -3.6% to +0.2% | not worse | yes |
| Confident and wrong | 3.0% | 4.2% | +0.2% to +2.3% | not worse | **no** |
| Expected calibration error | 2.6% | 4.1% | -0.7% to +2.8% | not worse | yes |
| Out-of-scope recall | 91.5% | 92.1% | -1.9% to +3.3% | not worse | yes |
| Vague lines asked about or declined | 17.9% | 21.4% | -8.3% to +15.8% | reported | |
| Macro-F1 | 89.8% | 88.6% | -3.1% to +0.6% | reported | |
| Held-out intents | 76.2% | 73.8% | -9.0% to +3.3% | reported | |

**Not worse than float by the spec's rule: no.**

## Graph sizes

| Graph | int8 ops | Size | Note |
| --- | --- | --- | --- |
| `decision.float.onnx` | none | 134.4 MB | M6's model |
| `decision.int8.onnx` | MatMul, Gather | 35.0 MB | failed the dev check |
| `decision.int8-matmul.onnx` | MatMul | 70.7 MB | passed the dev check, **ships** |
