# Fine-tuned bge-small + linear head on the proxy test set

Written by `uv run unstuk-fixed-head test`; do not edit by hand. BAAI/bge-small-en-v1.5 fine-tuned on `data/clean/train.jsonl` with one output per trained intent and out of scope; run `fixed-head-lr5e-05`, epoch 2, checkpoint sha256 `2d25b6998374…` from commit `9e92817`, temperature 1.1377 fitted on dev, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 75.4% | 71.3% to 79.7% |
| Top-1 accuracy, all clear lines | 80.7% | 77.2% to 84.0% |
| Macro-F1 | 71.5% | 68.5% to 74.4% |
| Out-of-scope recall | 93.9% | 90.1% to 97.3% |
| Out-of-scope precision | 83.2% | 77.3% to 88.8% |
| **Confident and wrong** | 5.2% | 3.4% to 7.2% |
| Vague lines answered with a question or decline | 7.1% | 0.0% to 19.2% |
| Expected calibration error | 10.2% | 7.6% to 12.9% |
| Held-out intents (no output for them; only a two-problem line whose other problem is trained can count as right) | 5.0% | 1.1% to 10.3% |
| Expected calibration error, before temperature | 11.7% | 9.0% to 14.6% |

## Against the rung below: Frozen bge-small + logistic regression

Differences are this rung minus the one below, with paired 95% bootstrap intervals: both are scored on the same resampled lines.

| Metric | Frozen bge-small + logistic regression | Fine-tuned bge-small + linear head | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 70.0% | 75.4% | +5.4% | +2.6% to +8.3% |
| Macro-F1 | 69.1% | 71.5% | +2.4% | -0.1% to +5.0% |
| **Confident and wrong** | 3.8% | 5.2% | +1.4% | -0.5% to +3.5% |
| Out-of-scope recall | 93.3% | 93.9% | +0.6% | -3.8% to +4.7% |
| Expected calibration error | 12.3% | 10.2% | -2.1% | -4.9% to +0.3% |

**Beats Frozen bge-small + logistic regression: no.** The rule (M4 spec section 3): the intervals for in-scope accuracy and macro-F1 both lie above 0, and the one for confident and wrong does not.

### Mistakes fixed: 36

- **out_of_scope → screen_turns_off_fast** (3): `The screen rotates even when I don't want it to`; `My dog keeps sleeping fast after eating.`
- **screen_too_dim → out_of_scope** (3): `I take my phone on my morning walk to see the steps count. Since last week the display has become so dull that outside I see only my own reflection.`; `The backlight drops to zero completely randomly.`
- **text_too_small → out_of_scope** (3): `The writing is completely microscopic and impossible to make out.`; `I can't see the words clearly without my strongest reading glasses.`
- **no_internet → wifi_no_load** (2): `Everything online is stuck but the phone itself is working`; `pages not opening`
- **app_permission → out_of_scope** (2): `The app is asking to be allowed to use something on my phone`; `It is asking for access every time I try to click a photo in Instagram.`
- **bluetooth_earphones → out_of_scope** (2): `Not the wired ones, those are fine. It's the cordless earphones my daughter gifted, the phone just doesn't find them.`; `The car audio system can't find my device, and my bank popups are completely delayed.`
- **no_internet → out_of_scope** (2): `evrything is stopng to load pls fix`; `My data is completely off and on top of that my phone doesn't make a sound when people call.`
- **phone_not_ringing → out_of_scope** (2): `My mobile stays perfectly quiet when someone tries to reach me.`; `Simply it is keeping quiet when relatives are calling me.`
- **text_too_small → screen_too_dim** (2): `wrds r tiny cant see them`; `The display isn't blurry, but the words are shrunken down too much to see.`
- **out_of_scope → phone_not_ringing** (2): `Why does my alarm clock keep ringing at 5 AM even on Sundays?`; `My caller tune is not playing Bollywood songs for my friends.`

### Mistakes introduced: 13

- **out_of_scope → screen_turns_off_fast** (2): `Apps are taking too long to open`; `When I lie down in bed, the display spins around when I don't want it to.`
- **screen_turns_off_fast → out_of_scope** (2): `The glass shuts down way too quickly when I'm looking at it.`; `The glass shuts down way too quickly while reading, and it never spins horizontally for videos.`
- **out_of_scope → colours_wrong** (2): `The colors of my new shirt washed out completely.`; `aree wrong colour saree delivered by flipkart!`
- **out_of_scope → screen_too_dim** (1): `My eyes are seeing everything too dark today`
- **colours_wrong → screen_too_dim** (1): `It's not night mode, I know what that looks like. My pictures look like negatives from the old camera film.`
- **wifi_no_load → no_internet** (1): `The broadband box is on but my device gets zero data from it.`
- **talkback_on → colours_wrong** (1): `A green square keeps highlighting my icons and I can't click normally.`
- **colours_wrong → bluetooth_earphones** (1): `scrin luks like old tv no colr`
- **screen_too_dim → out_of_scope** (1): `The lighting on the glass is way too weak to see comfortably.`
- **out_of_scope → app_permission** (1): `how to hide private photos in gallery`

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 306 | 41 | 32 | 31 |
| out of scope (164) | 8 | 2 | 0 | 154 |
| vague (28) | 16 | 10 | 0 | 2 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 86.4% | 75.0% to 95.5% |
| slice: indian_english | 46 | 73.9% | 60.9% to 87.0% |
| slice: long_story | 39 | 74.4% | 61.5% to 87.2% |
| slice: multi | 33 | 93.9% | 84.8% to 100.0% |
| slice: negation | 39 | 71.8% | 56.4% to 87.2% |
| slice: oos_near | 32 | 93.8% | 84.4% to 100.0% |
| slice: paraphrase | 82 | 73.2% | 64.6% to 81.7% |
| slice: plain | 192 | 86.5% | 81.8% to 91.1% |
| slice: short_vague | 5 | 100.0% | 100.0% to 100.0% |
| slice: typo | 73 | 68.5% | 57.5% to 79.5% |
| writer: chatgpt | 223 | 84.3% | 79.4% to 89.2% |
| writer: claude-blind | 96 | 81.2% | 74.0% to 88.5% |
| writer: gemini | 255 | 77.3% | 71.8% to 82.4% |

## Most common mistakes

- **wrong_time → out_of_scope** (14): `Websites are saying my phone's date or time is incorrect`; `time on my phne is rong`
- **cant_hear_call → phone_not_ringing** (10): `I cannot hear the other person during a call`; `The call is connected but I am getting no useful sound from the person speaking`
- **screen_wont_rotate → app_permission** (7): `The video stays in the same upright view even when I hold the phone sideways`; `vidio stays uprght when phone is side ways`
- **cant_hear_call → out_of_scope** (6): `The caller's voice is very low and I cannot hear properly`; `cant here the person on call`
- **wrong_time → screen_turns_off_fast** (6): `The time on my phone is wrong`; `The clock on the phone does not match the actual time`
- **screen_wont_rotate → screen_too_dim** (5): `My screen does not turn sideways`; `The phone stays vertical when I turn it sideways`
- **screen_wont_rotate → talkback_on** (5): `Turning the phone around does not change the way the picture is shown`; `The phone is not frozen and the video is playing, but turning the phone sideways does not change the screen`
- **cant_hear_call → talkback_on** (4): `I can talk but the voice from the other side is missing`; `How do I get the caller's voice back on my phone?`
- **wrong_time → notifications_missing** (4): `My phone is showing the wrong date and time`; `I noticed the clock was showing a different time this morning and later one website would not open properly. I checked again and the date also looked strange. I want the phone to show the correct date and time automatically`
- **cant_hear_call → screen_too_dim** (3): `voice is very low i cant heer anythng`; `during calls the other side voice is very low`

## Tuning on dev

| Run | Kept epoch | Macro-F1 | Log-loss | In-scope accuracy |  |
| --- | --- | --- | --- | --- | --- |
| `fixed-head-lr2e-05` | 2 | 97.6% | 0.108 | 98.4% |  |
| `fixed-head-lr2e-05-typos` | 5 | 97.6% | 0.104 | 98.2% |  |
| `fixed-head-lr5e-05` | 2 | 98.4% | 0.079 | 98.8% | **chosen** |
| `fixed-head-lr5e-05-typos` | 3 | 98.2% | 0.084 | 98.2% |  |
