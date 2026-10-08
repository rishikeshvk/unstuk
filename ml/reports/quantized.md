# int8 decision graph on the proxy test set

Written by `uv run unstuk-quantized-test`; do not edit by hand. M6's calibrated model as the int8 ONNX graph the app runs, behind gate lines re-tuned on it; `decision.int8.onnx` (sha256 `e3a739784daf…`) from run `cosine-lr5e-05-typos-state-vague-brier1`, commit `c0a2160`, gate lines {'automatic_at': 0.75, 'clarify_below': 0.7, 'clarify_margin': 0.0}, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 89.3% | 86.1% to 92.4% |
| Top-1 accuracy, all clear lines | 90.1% | 87.5% to 92.6% |
| Macro-F1 | 90.0% | 86.9% to 92.4% |
| Out-of-scope recall | 92.1% | 87.7% to 95.9% |
| Out-of-scope precision | 87.8% | 82.4% to 92.8% |
| **Confident and wrong** | 3.0% | 1.6% to 4.5% |
| Vague lines answered with a question or decline | 17.9% | 4.2% to 33.3% |
| Expected calibration error | 3.6% | 2.3% to 6.1% |
| Held-out intents (their options are offered; none was trained) | 77.5% | 67.6% to 86.5% |
| Expected calibration error, before temperature | 4.1% | 2.7% to 6.6% |

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 333 | 11 | 45 | 21 |
| out of scope (164) | 8 | 0 | 5 | 151 |
| vague (28) | 19 | 4 | 2 | 3 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 90.9% | 81.8% to 97.7% |
| slice: indian_english | 46 | 93.5% | 84.8% to 100.0% |
| slice: long_story | 39 | 87.2% | 76.9% to 97.4% |
| slice: multi | 33 | 97.0% | 90.9% to 100.0% |
| slice: negation | 39 | 84.6% | 71.8% to 94.9% |
| slice: oos_near | 32 | 81.2% | 65.6% to 93.8% |
| slice: paraphrase | 82 | 84.1% | 75.6% to 91.5% |
| slice: plain | 192 | 95.3% | 92.2% to 97.9% |
| slice: short_vague | 5 | 100.0% | 100.0% to 100.0% |
| slice: typo | 73 | 86.3% | 78.1% to 93.2% |
| writer: chatgpt | 223 | 94.6% | 91.5% to 97.3% |
| writer: claude-blind | 96 | 94.8% | 89.6% to 99.0% |
| writer: gemini | 255 | 84.3% | 79.6% to 89.0% |

## Most common mistakes

- **wrong_time → out_of_scope** (5): `the date at the top says 2019 and my bank site says something about a certificate`; `Websites give me a security error about my date.`
- **cant_hear_call → out_of_scope** (4): `cant here the person on call`; `The person speaking to me is too quiet to understand.`
- **screen_turns_off_fast → out_of_scope** (3): `The glass shuts down way too quickly when I'm looking at it.`; `I love reading long recipes before I start cooking in the kitchen. My hands are usually covered in flour so I can't keep touching the device. But every time I look away for just a few moments to stir the pot, the display completely dies and puts me back on the password page.`
- **text_too_small → out_of_scope** (3): `The writing is completely microscopic and impossible to make out.`; `I usually check the daily news on my mobile right after waking up. Since I turned fifty, my eyesight isn't as sharp as it used to be. Yesterday an update happened and now all the articles have shrunk so much that the characters are barely visible to my naked eye.`
- **cant_hear_call → talkback_on** (2): `I can talk but the voice from the other side is missing`; `I can talk but can't catch what my daughter is saying on the line, her voice is like a whisper`
- **screen_too_dim → text_too_small** (2): `I can hardly make out what is on the screen`; `lit keeps going awy very hard to read`
- **out_of_scope → screen_wont_rotate** (2): `The screen rotates even when I don't want it to`; `When I lie down in bed, the display spins around when I don't want it to.`
- **out_of_scope → phone_not_ringing** (2): `How do I stop the alarm from ringing every day`; `Why does my alarm clock keep ringing at 5 AM even on Sundays?`
- **out_of_scope → screen_turns_off_fast** (2): `My phone freezes when I try to open settings`; `Apps are taking too long to open`
- **wifi_no_load → no_internet** (2): `Not asking about mobile data, that I have switched off. The house connection shows full bars yet YouTube says no connection.`; `Only showing the full symbol but practically it is not working at all.`

## Against M6's float model

Pre-registered in the M7 spec, section 4. Each model is under its own temperatures and lines; differences are int8 minus float, with paired 95% intervals.

| Metric | Float | int8 | Difference | Must | Passes |
| --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 89.5% | 89.3% | -1.9% to +1.5% | not worse | yes |
| Confident and wrong | 3.0% | 3.0% | -0.5% to +0.5% | not worse | yes |
| Expected calibration error | 2.6% | 3.6% | -0.9% to +2.3% | not worse | yes |
| Out-of-scope recall | 91.5% | 92.1% | -1.3% to +2.7% | not worse | yes |
| Vague lines asked about or declined | 17.9% | 17.9% | +0.0% to +0.0% | reported | |
| Macro-F1 | 89.8% | 90.0% | -1.5% to +1.9% | reported | |
| Held-out intents | 76.2% | 77.5% | -4.2% to +7.0% | reported | |

**Not worse than float by the spec's rule: yes.**

## Graph sizes

| Graph | int8 ops | Size | Note |
| --- | --- | --- | --- |
| `decision.float.onnx` | none | 134.4 MB | M6's model |
| `decision.int8.onnx` | MatMul, Gather | 35.0 MB | passed the dev check, **ships** |
