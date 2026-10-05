# TF-IDF + logistic regression on the proxy test set

Written by `uv run unstuk-tfidf test`; do not edit by hand. Word 1-2-grams and character 2-5-grams, read by logistic regression trained on `data/clean/train.jsonl`; C = 100.0, class weight none, temperature 0.7767 fitted on dev, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 64.9% | 60.4% to 69.7% |
| Top-1 accuracy, all clear lines | 73.5% | 70.0% to 77.2% |
| Macro-F1 | 68.7% | 65.3% to 71.8% |
| Out-of-scope recall | 95.1% | 91.6% to 98.2% |
| Out-of-scope precision | 57.8% | 51.9% to 63.6% |
| **Confident and wrong** | 1.9% | 0.9% to 3.1% |
| Vague lines answered with a question or decline | 32.1% | 14.8% to 50.0% |
| Expected calibration error | 17.4% | 14.1% to 20.7% |
| Held-out intents (no output for them; only a two-problem line whose other problem is trained can count as right) | 6.2% | 1.4% to 11.9% |
| Expected calibration error, before temperature | 13.9% | 10.9% to 17.2% |

## Against the rung below: Keyword baseline

Differences are this rung minus the one below, with paired 95% bootstrap intervals: both are scored on the same resampled lines.

| Metric | Keyword baseline | TF-IDF + logistic regression | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 40.2% | 64.9% | +24.6% | +19.0% to +30.4% |
| Macro-F1 | 50.6% | 68.7% | +18.2% | +14.0% to +23.2% |
| **Confident and wrong** | 8.7% | 1.9% | -6.8% | -9.2% to -4.5% |
| Out-of-scope recall | 81.1% | 95.1% | +14.0% | +8.0% to +20.4% |
| Expected calibration error | 22.6% | 17.4% | -5.2% | -11.9% to -0.0% |

**Beats Keyword baseline: yes.** The rule (M4 spec section 3): the intervals for in-scope accuracy and macro-F1 both lie above 0, and the one for confident and wrong does not.

### Mistakes fixed: 158

- **wifi_no_load → out_of_scope** (16): `The WiFi symbol is there and strong, but every online page just waits`; `wifi conneted but nothng loading`
- **talkback_on → out_of_scope** (16): `I have to touch things twice now and there is a box around everything`; `The phone is reading the screen aloud and one touch does not open anything`
- **screen_turns_off_fast → out_of_scope** (15): `The phone locks while I am still using it`; `The display disappears before I finish reading`
- **notifications_missing → out_of_scope** (13): `Messages are there but the phone does not tell me when they arrive`; `I only discover new messages after checking the apps myself`
- **phone_not_ringing → out_of_scope** (12): `Calls are coming in but the phone stays quiet`; `People say they called me but I only notice afterwards`
- **no_internet → out_of_scope** (10): `Everything online is stuck but the phone itself is working`; `I can use the phone but anything that needs online connection just sits there`
- **reset_network → out_of_scope** (10): `I want to reset all the phone's connection settings`; `I need to clear the saved connection setup and start again`
- **out_of_scope → screen_too_dim** (7): `I want to turn on dark mode, not change the brightness`; `weather is so dim and grey today, will it rain`
- **screen_too_dim → out_of_scope** (6): `I can hardly make out what is on the screen`; `How can I make my phone screen brighter?`
- **text_too_small → out_of_scope** (6): `The words are difficult to make out on the screen`; `text on my phone is very tinny`

### Mistakes introduced: 34

- **screen_wont_rotate → out_of_scope** (7): `My screen does not turn sideways`; `The phone stays vertical when I turn it sideways`
- **wrong_time → out_of_scope** (6): `My phone is showing the wrong date and time`; `The clock on the phone does not match the actual time`
- **wrong_time → no_internet** (3): `I noticed the clock was showing a different time this morning and later one website would not open properly. I checked again and the date also looked strange. I want the phone to show the correct date and time automatically`; `The battery is fine and the phone is working, but the clock and date are not correct`
- **app_permission → out_of_scope** (3): `mic blocked in telegram pls hlp`; `I wanted to book a cab to go to the hospital for my routine checkup. I opened the ride booking software but it kept putting my pickup point in another city. It gave me a popup error saying I need to grant access to my GPS coordinates but I don't know where that is.`
- **screen_wont_rotate → screen_turns_off_fast** (2): `The phone is not frozen and the video is playing, but turning the phone sideways does not change the screen`; `How do I make the screen turn sideways when I rotate the phone?`
- **bluetooth_earphones → out_of_scope** (2): `I go for a jog every morning at 6 AM and need my music to keep me motivated. I charged my new wireless headset all night so it would be ready. But when I try to link it up, it just keeps searching endlessly and never establishes a link.`; `The headset is fully charged, but it simply refuses to link with the handset.`
- **cant_hear_call → phone_not_ringing** (1): `I cannot hear the other person during a call`
- **cant_hear_call → talkback_on** (1): `The caller's voice is very low and I cannot hear properly`
- **cant_hear_call → bluetooth_earphones** (1): `The call is not disconnected and my microphone is not the problem, but I cannot hear the person talking to me`
- **screen_wont_rotate → bluetooth_earphones** (1): `I wanted to watch a video properly and turned the phone sideways like I normally do. I waited and turned it again, but the picture stayed upright. The phone works otherwise, but it is not changing the screen view when I turn it`

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 235 | 47 | 14 | 114 |
| out of scope (164) | 5 | 3 | 0 | 156 |
| vague (28) | 14 | 5 | 0 | 9 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 86.4% | 75.0% to 95.5% |
| slice: indian_english | 46 | 60.9% | 45.7% to 76.1% |
| slice: long_story | 39 | 59.0% | 43.6% to 74.4% |
| slice: multi | 33 | 93.9% | 84.8% to 100.0% |
| slice: negation | 39 | 59.0% | 43.6% to 74.4% |
| slice: oos_near | 32 | 93.8% | 84.4% to 100.0% |
| slice: paraphrase | 82 | 57.3% | 46.3% to 68.3% |
| slice: plain | 192 | 83.3% | 78.1% to 88.0% |
| slice: short_vague | 5 | 60.0% | 20.0% to 100.0% |
| slice: typo | 73 | 64.4% | 53.4% to 74.0% |
| writer: chatgpt | 223 | 83.4% | 78.0% to 88.3% |
| writer: claude-blind | 96 | 80.2% | 71.9% to 87.5% |
| writer: gemini | 255 | 62.4% | 56.5% to 67.5% |

## Most common mistakes

- **wrong_time → out_of_scope** (22): `My phone is showing the wrong date and time`; `The clock on the phone does not match the actual time`
- **screen_wont_rotate → out_of_scope** (17): `My screen does not turn sideways`; `The phone stays vertical when I turn it sideways`
- **cant_hear_call → out_of_scope** (16): `cant here the person on call`; `voice is very low i cant heer anythng`
- **bluetooth_earphones → out_of_scope** (8): `The car audio system can't find my device anymore.`; `The smart band on my wrist says disconnected from the handset.`
- **reset_network → out_of_scope** (8): `I'm fed up and want to wipe my internet configurations.`; `How can I completely erase all the saved signal data and start fresh?`
- **screen_too_dim → out_of_scope** (6): `The picture on the phone looks faint, especially outside`; `The lighting on the glass is way too weak to see comfortably.`
- **no_internet → out_of_scope** (6): `Can't open any websites at all.`; `My brother sent me a video but it just keeps spinning forever.`
- **colours_wrong → out_of_scope** (6): `The pictures on my glass look completely washed out and weird.`; `It's like looking at an x-ray of my apps instead of normal graphics.`
- **app_permission → out_of_scope** (6): `The map software keeps complaining that it doesn't know where I am.`; `ig cant take pics says denied`
- **phone_not_ringing → out_of_scope** (5): `People are complaining I don't pick up.`; `My mobile stays perfectly quiet when someone tries to reach me.`

## Tuning on dev

| C | Class weight | Macro-F1 | Log-loss | In-scope accuracy |  |
| --- | --- | --- | --- | --- | --- |
| 0.3 | none | 94.0% | 0.564 | 92.2% |  |
| 0.3 | balanced | 92.8% | 0.677 | 97.7% |  |
| 1.0 | none | 95.9% | 0.317 | 95.2% |  |
| 1.0 | balanced | 95.0% | 0.388 | 97.9% |  |
| 3.0 | none | 96.4% | 0.204 | 96.1% |  |
| 3.0 | balanced | 96.4% | 0.244 | 98.3% |  |
| 10.0 | none | 96.8% | 0.143 | 96.9% |  |
| 10.0 | balanced | 96.9% | 0.163 | 98.3% |  |
| 30.0 | none | 97.3% | 0.112 | 97.7% |  |
| 30.0 | balanced | 97.1% | 0.128 | 98.4% |  |
| 100.0 | none | 97.5% | 0.099 | 98.2% | **chosen** |
| 100.0 | balanced | 97.3% | 0.104 | 98.6% |  |
