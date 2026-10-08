# Calibrated decision model on the proxy test set

Written by `uv run unstuk-calibrated-test`; do not edit by hand. M5's decision model trained on the vague slice too, with a Brier term, behind gate lines tuned on dev; run `cosine-lr5e-05-typos-state-vague-brier1`, epoch 5, checkpoint sha256 `c8d66d0d3c42…` from commit `cf5f6a5`, out of scope by noul, gate lines {'automatic_at': 0.75, 'clarify_below': 0.7, 'clarify_margin': 0.0}, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 89.5% | 86.3% to 92.5% |
| Top-1 accuracy, all clear lines | 90.1% | 87.6% to 92.6% |
| Macro-F1 | 89.8% | 86.9% to 92.3% |
| Out-of-scope recall | 91.5% | 86.7% to 95.7% |
| Out-of-scope precision | 89.3% | 84.4% to 94.1% |
| **Confident and wrong** | 3.0% | 1.6% to 4.5% |
| Vague lines answered with a question or decline | 17.9% | 4.2% to 33.3% |
| Expected calibration error | 2.6% | 1.7% to 5.1% |
| Held-out intents (their options are offered; none was trained) | 76.2% | 67.0% to 85.1% |
| Expected calibration error, before temperature | 3.6% | 2.4% to 6.3% |

## Against the rung below: Fine-tuned bge-small + Choice and Noul heads

Differences are this rung minus the one below, with paired 95% bootstrap intervals: both are scored on the same resampled lines.

| Metric | Fine-tuned bge-small + Choice and Noul heads | Calibrated decision model | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 87.1% | 89.5% | +2.4% | +0.2% to +4.7% |
| Macro-F1 | 87.1% | 89.8% | +2.7% | +0.6% to +5.0% |
| **Confident and wrong** | 2.6% | 3.0% | +0.3% | -1.0% to +1.7% |
| Out-of-scope recall | 92.1% | 91.5% | -0.6% | -4.3% to +2.9% |
| Expected calibration error | 2.8% | 2.6% | -0.2% | -2.3% to +1.8% |

**Beats Fine-tuned bge-small + Choice and Noul heads: yes.** The rule (M4 spec section 3): the intervals for in-scope accuracy and macro-F1 both lie above 0, and the one for confident and wrong does not.

### Mistakes fixed: 21

- **wrong_time → screen_turns_off_fast** (4): `The time on my phone is wrong`; `time on my phne is rong`
- **wrong_time → out_of_scope** (2): `dat on phone is incorect calender showing yesterday`; `Websites give me a security error about my date.`
- **wrong_time → notifications_missing** (2): `The numbers at the top right are showing hours ahead of reality.`; `How do I sync my device to show the actual current hours?`
- **out_of_scope → reset_network** (2): `How do I change my WhatsApp DP?`; `need green net screen for balcony`
- **cant_hear_call → phone_not_ringing** (1): `The call is not disconnected and my microphone is not the problem, but I cannot hear the person talking to me`
- **text_too_small → out_of_scope** (1): `writing on the phone is very fine, my eyes are paining while reading`
- **out_of_scope → notifications_missing** (1): `How do I make the bank OTP messages pop up right away instead of after an hour?`
- **no_internet → out_of_scope** (1): `My brother sent me a video but it just keeps spinning forever.`
- **wifi_no_load → app_permission** (1): `cnnectd to home but nt wroking at all`
- **phone_not_ringing → cant_hear_call** (1): `How do I make my device loud again for incoming calls?`

### Mistakes introduced: 12

- **out_of_scope → phone_not_ringing** (3): `How do I stop the alarm from ringing every day`; `Why does my alarm clock keep ringing at 5 AM even on Sundays?`
- **cant_hear_call → phone_not_ringing** (1): `The call is connected but I am getting no useful sound from the person speaking`
- **out_of_scope → cant_hear_call** (1): `I cannot hear properly from my left ear`
- **out_of_scope → screen_wont_rotate** (1): `The screen rotates even when I don't want it to`
- **phone_not_ringing → notifications_missing** (1): `The speaker works for music, but I get no alerts when someone tries to reach me.`
- **cant_hear_call → out_of_scope** (1): `Give me instructions to increase the earpiece output during a conversation.`
- **screen_too_dim → out_of_scope** (1): `The lighting on the glass is way too weak to see comfortably.`
- **screen_turns_off_fast → out_of_scope** (1): `The glass shuts down way too quickly when I'm looking at it.`
- **app_permission → out_of_scope** (1): `I wanted to book a cab to go to the hospital for my routine checkup. I opened the ride booking software but it kept putting my pickup point in another city. It gave me a popup error saying I need to grant access to my GPS coordinates but I don't know where that is.`
- **text_too_small → out_of_scope** (1): `The writing is microscopic and impossible to read, plus my calendar widget is stuck on yesterday.`

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 347 | 7 | 38 | 18 |
| out of scope (164) | 8 | 0 | 6 | 150 |
| vague (28) | 19 | 4 | 3 | 2 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 86.4% | 75.0% to 95.5% |
| slice: indian_english | 46 | 93.5% | 84.8% to 100.0% |
| slice: long_story | 39 | 89.7% | 79.5% to 97.4% |
| slice: multi | 33 | 93.9% | 84.8% to 100.0% |
| slice: negation | 39 | 84.6% | 71.8% to 94.9% |
| slice: oos_near | 32 | 84.4% | 71.9% to 96.9% |
| slice: paraphrase | 82 | 85.4% | 76.8% to 92.7% |
| slice: plain | 192 | 95.3% | 92.2% to 97.9% |
| slice: short_vague | 5 | 100.0% | 100.0% to 100.0% |
| slice: typo | 73 | 86.3% | 78.1% to 93.2% |
| writer: chatgpt | 223 | 94.2% | 91.0% to 96.9% |
| writer: claude-blind | 96 | 95.8% | 91.7% to 99.0% |
| writer: gemini | 255 | 84.3% | 80.0% to 89.0% |

## Most common mistakes

- **cant_hear_call → out_of_scope** (4): `cant here the person on call`; `The person speaking to me is too quiet to understand.`
- **wrong_time → out_of_scope** (4): `the date at the top says 2019 and my bank site says something about a certificate`; `clck is 2 hrs behnd how fix`
- **out_of_scope → phone_not_ringing** (3): `How do I stop the alarm from ringing every day`; `Why does my alarm clock keep ringing at 5 AM even on Sundays?`
- **text_too_small → out_of_scope** (3): `The writing is completely microscopic and impossible to make out.`; `I usually check the daily news on my mobile right after waking up. Since I turned fifty, my eyesight isn't as sharp as it used to be. Yesterday an update happened and now all the articles have shrunk so much that the characters are barely visible to my naked eye.`
- **cant_hear_call → talkback_on** (2): `I can talk but the voice from the other side is missing`; `I can talk but can't catch what my daughter is saying on the line, her voice is like a whisper`
- **cant_hear_call → phone_not_ringing** (2): `The call is connected but I am getting no useful sound from the person speaking`; `The ringer is loud, but I get total silence from the person on the line.`
- **screen_too_dim → text_too_small** (2): `I can hardly make out what is on the screen`; `lit keeps going awy very hard to read`
- **out_of_scope → colours_wrong** (2): `The colours of this shirt look wrong to me`; `aree wrong colour saree delivered by flipkart!`
- **out_of_scope → screen_wont_rotate** (2): `The screen rotates even when I don't want it to`; `When I lie down in bed, the display spins around when I don't want it to.`
- **wifi_no_load → no_internet** (2): `Only showing the full symbol but practically it is not working at all.`; `Tell me how to fix a connection that shows full strength but delivers nothing.`

## Against the M5 decision model

Pre-registered in the M6 spec, section 6. M5 is scored under M2's placeholder lines, as it was reported; differences are this model minus M5, with paired 95% intervals.

| Metric | M5 | This model | Difference | Must | Passes |
| --- | --- | --- | --- | --- | --- |
| Vague lines answered with a question or decline | 10.7% | 17.9% | +0.0% to +18.2% | better | **no** |
| Confident and wrong | 2.6% | 3.0% | -1.0% to +1.7% | not worse | yes |
| Expected calibration error | 2.8% | 2.6% | -2.3% to +1.8% | not worse | yes |
| Out-of-scope recall | 92.1% | 91.5% | -4.3% to +2.9% | not worse | yes |
| Top-1 accuracy, in scope | 87.1% | 89.5% | +0.2% to +4.7% | reported | |
| Macro-F1 | 87.1% | 89.8% | +0.6% to +5.0% | reported | |
| Held-out intents | 63.7% | 76.2% | +4.2% to +21.7% | reported | |

**Safer than M5 by the spec's rule: no.**

## M5's model under the tuned lines

Lines: automatic at 0.75, clarify below 0.7, clarify margin 0.0.

| Metric | M5, placeholder lines | M5, tuned lines |
| --- | --- | --- |
| Vague lines answered with a question or decline | 10.7% | 35.7% |
| Confident and wrong | 2.6% | 3.3% |
| Expected calibration error | 2.8% | 2.8% |

## Reliability

Clear lines by the top answer's probability: how many, and how often right.

| Confidence | M5 lines | M5 right | This model's lines | This model right |
| --- | --- | --- | --- | --- |
| 0.0 to 0.1 | 0 | - | 0 | - |
| 0.1 to 0.2 | 0 | - | 0 | - |
| 0.2 to 0.3 | 0 | - | 0 | - |
| 0.3 to 0.4 | 9 | 33% | 0 | - |
| 0.4 to 0.5 | 18 | 44% | 12 | 50% |
| 0.5 to 0.6 | 32 | 62% | 22 | 36% |
| 0.6 to 0.7 | 21 | 67% | 23 | 65% |
| 0.7 to 0.8 | 18 | 56% | 26 | 77% |
| 0.8 to 0.9 | 43 | 72% | 43 | 77% |
| 0.9 to 1.0 | 433 | 97% | 448 | 97% |

## Against the M4 bar

From `m4-results.md`: better than the best baseline on accuracy and macro-F1, not worse on each guard rail. Differences are this model minus the baseline, paired 95% intervals.

| Metric | Bar | Set by | Must | This model | Difference | Passes |
| --- | --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 73.9% | Zero-shot bge-small | better | 89.5% | +11.1% to +20.6% | yes |
| Macro-F1 | 69.1% | Frozen bge-small + logistic regression | better | 89.8% | +17.4% to +23.8% | yes |
| Confident and wrong | 1.9% | TF-IDF + logistic regression | not worse | 3.0% | -0.3% to +2.5% | yes |
| Out-of-scope recall | 95.1% | TF-IDF + logistic regression | not worse | 91.5% | -7.8% to +0.0% | yes |
| Held-out intents | 93.8% | Zero-shot bge-small | not worse | 76.2% | -26.6% to -8.8% | **no** |
| Expected calibration error | 6.1% | Zero-shot bge-small | not worse | 2.6% | -7.1% to -0.4% | yes |

**Clears the bar: no.**
