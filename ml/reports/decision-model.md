# Fine-tuned bge-small + Choice and Noul heads on the proxy test set

Written by `uv run unstuk-decision-test`; do not edit by hand. BAAI/bge-small-en-v1.5 fine-tuned to choose among option texts, with every catalog intent offered; run `cosine-lr5e-05-typos-state`, epoch 5, checkpoint sha256 `e16431e01306…` from commit `85603cb`, out of scope by noul, temperatures 1.3074 (Choice) and 1.6121 (Noul) fitted on dev, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 87.1% | 83.7% to 90.2% |
| Top-1 accuracy, all clear lines | 88.5% | 85.8% to 91.0% |
| Macro-F1 | 87.1% | 83.7% to 89.5% |
| Out-of-scope recall | 92.1% | 87.8% to 95.9% |
| Out-of-scope precision | 88.3% | 82.5% to 92.9% |
| **Confident and wrong** | 2.6% | 1.4% to 4.0% |
| Vague lines answered with a question or decline | 10.7% | 0.0% to 24.0% |
| Expected calibration error | 2.8% | 2.0% to 5.6% |
| Held-out intents (their options are offered; none was trained) | 63.7% | 53.2% to 74.0% |
| Expected calibration error, before temperature | 5.3% | 4.1% to 8.1% |

## Against the rung below: Fine-tuned bge-small + linear head

Differences are this rung minus the one below, with paired 95% bootstrap intervals: both are scored on the same resampled lines.

| Metric | Fine-tuned bge-small + linear head | Fine-tuned bge-small + Choice and Noul heads | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 75.4% | 87.1% | +11.7% | +7.8% to +15.6% |
| Macro-F1 | 71.5% | 87.1% | +15.6% | +12.3% to +18.8% |
| **Confident and wrong** | 5.2% | 2.6% | -2.6% | -4.5% to -0.7% |
| Out-of-scope recall | 93.9% | 92.1% | -1.8% | -4.6% to +0.6% |
| Expected calibration error | 10.2% | 2.8% | -7.5% | -9.3% to -3.9% |

**Beats Fine-tuned bge-small + linear head: yes.** The rule (M4 spec section 3): the intervals for in-scope accuracy and macro-F1 both lie above 0, and the one for confident and wrong does not.

### Mistakes fixed: 59

- **cant_hear_call → phone_not_ringing** (8): `I cannot hear the other person during a call`; `The call is connected but I am getting no useful sound from the person speaking`
- **screen_wont_rotate → app_permission** (7): `The video stays in the same upright view even when I hold the phone sideways`; `vidio stays uprght when phone is side ways`
- **screen_wont_rotate → screen_too_dim** (5): `My screen does not turn sideways`; `The phone stays vertical when I turn it sideways`
- **screen_wont_rotate → talkback_on** (4): `Turning the phone around does not change the way the picture is shown`; `The phone is not frozen and the video is playing, but turning the phone sideways does not change the screen`
- **wrong_time → notifications_missing** (4): `My phone is showing the wrong date and time`; `I noticed the clock was showing a different time this morning and later one website would not open properly. I checked again and the date also looked strange. I want the phone to show the correct date and time automatically`
- **wrong_time → out_of_scope** (4): `Websites are saying my phone's date or time is incorrect`; `date is showng wrong and apps giving error`
- **cant_hear_call → out_of_scope** (3): `The caller's voice is very low and I cannot hear properly`; `The earpiece is dead quiet when I hold it to my head.`
- **cant_hear_call → screen_too_dim** (3): `voice is very low i cant heer anythng`; `during calls the other side voice is very low`
- **cant_hear_call → talkback_on** (2): `How do I get the caller's voice back on my phone?`; `I have to put people on speaker just to talk to them.`
- **screen_wont_rotate → colours_wrong** (2): `When I turn my mobile sideways, screen is not changing`; `when I turn the phone sideways the picture stays straight`

### Mistakes introduced: 14

- **screen_turns_off_fast → out_of_scope** (2): `I love reading long recipes before I start cooking in the kitchen. My hands are usually covered in flour so I can't keep touching the device. But every time I look away for just a few moments to stir the pot, the display completely dies and puts me back on the password page.`; `It's not out of battery, it just goes black after a few seconds of no touching.`
- **text_too_small → out_of_scope** (2): `The writing is completely microscopic and impossible to make out.`; `I usually check the daily news on my mobile right after waking up. Since I turned fifty, my eyesight isn't as sharp as it used to be. Yesterday an update happened and now all the articles have shrunk so much that the characters are barely visible to my naked eye.`
- **reset_network → out_of_scope** (2): `I want to wipe all the memory of my home routers and mobile carriers.`; `I don't want to wipe my photos, I just want to restore all my signal data to factory defaults.`
- **out_of_scope → reset_network** (2): `How do I change my WhatsApp DP?`; `need green net screen for balcony`
- **screen_too_dim → colours_wrong** (1): `I can hardly make out what is on the screen`
- **out_of_scope → talkback_on** (1): `My phone freezes when I try to open settings`
- **wifi_no_load → reset_network** (1): `Tell me how to fix a connection that shows full strength but delivers nothing.`
- **phone_not_ringing → cant_hear_call** (1): `How do I make my device loud again for incoming calls?`
- **notifications_missing → no_internet** (1): `watsap only showing text whn i open it`
- **out_of_scope → no_internet** (1): `My internet friend is not talking to me today.`

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 319 | 52 | 19 | 20 |
| out of scope (164) | 5 | 5 | 3 | 151 |
| vague (28) | 15 | 10 | 1 | 2 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 84.1% | 72.7% to 93.2% |
| slice: indian_english | 46 | 89.1% | 78.3% to 97.8% |
| slice: long_story | 39 | 89.7% | 79.5% to 97.4% |
| slice: multi | 33 | 97.0% | 90.9% to 100.0% |
| slice: negation | 39 | 82.1% | 69.2% to 92.3% |
| slice: oos_near | 32 | 90.6% | 78.1% to 100.0% |
| slice: paraphrase | 82 | 85.4% | 78.0% to 92.7% |
| slice: plain | 192 | 92.2% | 88.5% to 95.3% |
| slice: short_vague | 5 | 100.0% | 100.0% to 100.0% |
| slice: typo | 73 | 82.2% | 74.0% to 90.4% |
| writer: chatgpt | 223 | 94.2% | 90.6% to 96.9% |
| writer: claude-blind | 96 | 91.7% | 86.5% to 96.9% |
| writer: gemini | 255 | 82.4% | 77.3% to 87.1% |

## Most common mistakes

- **wrong_time → out_of_scope** (5): `the date at the top says 2019 and my bank site says something about a certificate`; `dat on phone is incorect calender showing yesterday`
- **cant_hear_call → out_of_scope** (4): `cant here the person on call`; `The person speaking to me is too quiet to understand.`
- **wrong_time → screen_turns_off_fast** (4): `The time on my phone is wrong`; `time on my phne is rong`
- **text_too_small → out_of_scope** (3): `writing on the phone is very fine, my eyes are paining while reading`; `The writing is completely microscopic and impossible to make out.`
- **reset_network → out_of_scope** (3): `I want to wipe all the memory of my home routers and mobile carriers.`; `need to clr all signls now`
- **cant_hear_call → talkback_on** (2): `I can talk but the voice from the other side is missing`; `I can talk but can't catch what my daughter is saying on the line, her voice is like a whisper`
- **out_of_scope → screen_too_dim** (2): `My eyes are seeing everything too dark today`; `The weather is so dim outside I can't see the road.`
- **out_of_scope → colours_wrong** (2): `The colours of this shirt look wrong to me`; `aree wrong colour saree delivered by flipkart!`
- **wrong_time → no_internet** (2): `The phone time is wrong and now some websites are not opening`; `it says im in 2015 cnt use browser`
- **wrong_time → screen_wont_rotate** (2): `clock is showing different from my wall clock, kindly correct it`; `The clock on the top corner is completely incorrect.`

## How this model was chosen

**Without the zero-shot guard.** Seven rounds on dev ([M5 spec](../../docs/m5-spec.md), section 3) found no config that names never-trained intents as well as the frozen zero-shot rung once out of scope is decided: the Choice head names them about as well, but every out-of-scope check tried declines a fifth or more of their lines. By the pre-registered stop rule the guard was dropped and the rung rule alone picked this model, the most accurate on dev and the least able to name unseen intents on the folds. The held-out bar below is expected to fail for that reason.

## Against the M4 bar

From `m4-results.md`: better than the best baseline on accuracy and macro-F1, not worse on each guard rail. Differences are this model minus the baseline, paired 95% intervals.

| Metric | Bar | Set by | Must | This model | Difference | Passes |
| --- | --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 73.9% | Zero-shot bge-small | better | 87.1% | +8.7% to +18.3% | yes |
| Macro-F1 | 69.1% | Frozen bge-small + logistic regression | better | 87.1% | +14.5% to +21.4% | yes |
| Confident and wrong | 1.9% | TF-IDF + logistic regression | not worse | 2.6% | -0.5% to +2.1% | yes |
| Out-of-scope recall | 95.1% | TF-IDF + logistic regression | not worse | 92.1% | -6.4% to +0.0% | yes |
| Held-out intents | 93.8% | Zero-shot bge-small | not worse | 63.7% | -40.4% to -19.8% | **no** |
| Expected calibration error | 6.1% | Zero-shot bge-small | not worse | 2.8% | -6.8% to -0.3% | yes |

**Clears the bar: no.**

## Node labels

Which item on the screen is the switch: dev is Xiaomi wording, the test is the Moto's screens. The decision model answers with its Choice head; the others are M4's.

| Method | Dev (132) | Moto test (10) |
| --- | --- | --- |
| String baseline | 90.9% | 8/10 |
| Similarity (frozen) | 82.6% | 8/10 |
| Decision model | 97.7% | 9/10 |
