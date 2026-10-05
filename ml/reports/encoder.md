# Frozen bge-small + logistic regression on the proxy test set

Written by `uv run unstuk-encoder test`; do not edit by hand. BAAI/bge-small-en-v1.5 sentence vectors (CLS, L2-normalised, frozen), read by logistic regression trained on `data/clean/train.jsonl`; C = 100.0, class weight none, temperature 1.0373 fitted on dev, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 70.0% | 65.5% to 74.3% |
| Top-1 accuracy, all clear lines | 76.7% | 73.0% to 80.1% |
| Macro-F1 | 69.1% | 66.0% to 71.8% |
| Out-of-scope recall | 93.3% | 89.4% to 97.0% |
| Out-of-scope precision | 69.9% | 63.5% to 75.7% |
| **Confident and wrong** | 3.8% | 2.3% to 5.6% |
| Vague lines answered with a question or decline | 32.1% | 16.0% to 51.5% |
| Expected calibration error | 12.3% | 9.7% to 15.6% |
| Held-out intents (no output for them; only a two-problem line whose other problem is trained can count as right) | 3.8% | 0.0% to 8.3% |
| Expected calibration error, before temperature | 12.8% | 10.0% to 15.8% |

## Against the rung below: TF-IDF + logistic regression

Differences are this rung minus the one below, with paired 95% bootstrap intervals: both are scored on the same resampled lines.

| Metric | TF-IDF + logistic regression | Frozen bge-small + logistic regression | Difference | 95% interval |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 64.9% | 70.0% | +5.1% | +1.3% to +8.8% |
| Macro-F1 | 68.7% | 69.1% | +0.4% | -2.4% to +3.4% |
| **Confident and wrong** | 1.9% | 3.8% | +1.9% | +0.3% to +3.5% |
| Out-of-scope recall | 95.1% | 93.3% | -1.8% | -5.1% to +1.2% |
| Expected calibration error | 17.4% | 12.3% | -5.0% | -7.8% to -1.8% |

**Beats TF-IDF + logistic regression: no.** The rule (M4 spec section 3): the intervals for in-scope accuracy and macro-F1 both lie above 0, and the one for confident and wrong does not.

### Mistakes fixed: 46

- **bluetooth_earphones → out_of_scope** (6): `The car audio system can't find my device anymore.`; `The smart band on my wrist says disconnected from the handset.`
- **app_permission → out_of_scope** (6): `The map software keeps complaining that it doesn't know where I am.`; `ig cant take pics says denied`
- **reset_network → out_of_scope** (6): `I'm fed up and want to wipe my internet configurations.`; `How can I completely erase all the saved signal data and start fresh?`
- **colours_wrong → out_of_scope** (5): `The pictures on my glass look completely washed out and weird.`; `It's like looking at an x-ray of my apps instead of normal graphics.`
- **notifications_missing → out_of_scope** (4): `Popups from my bank just stopped appearing on my lock screen.`; `I have to manually check my inbox to see if anyone texted me.`
- **screen_too_dim → out_of_scope** (3): `The picture on the phone looks faint, especially outside`; `The lighting on the glass is way too weak to see comfortably.`
- **text_too_small → out_of_scope** (2): `Everything is written in a size that is hard for me to see`; `I usually check the daily news on my mobile right after waking up. Since I turned fifty, my eyesight isn't as sharp as it used to be. Yesterday an update happened and now all the articles have shrunk so much that the characters are barely visible to my naked eye.`
- **no_internet → out_of_scope** (2): `Can't open any websites at all.`; `Sir my mobile connection is fully gone, kindly do the needful.`
- **wifi_no_load → out_of_scope** (2): `Home broadband joined but zero signal is coming through.`; `The broadband box is on but my device gets zero data from it.`
- **talkback_on → out_of_scope** (2): `A green square keeps highlighting my icons and I can't click normally.`; `My mobile has started speaking on its own, it is giving me a headache.`

### Mistakes introduced: 28

- **app_permission → out_of_scope** (2): `The app is asking to be allowed to use something on my phone`; `It is asking for access every time I try to click a photo in Instagram.`
- **no_internet → out_of_scope** (2): `whasapp not workng yutube dead`; `My data is completely off and on top of that my phone doesn't make a sound when people call.`
- **wifi_no_load → out_of_scope** (2): `full bars but nothn loading y`; `cnnectd to home but nt wroking at all`
- **text_too_small → out_of_scope** (2): `I can't see the words clearly without my strongest reading glasses.`; `The writing is microscopic and impossible to read, plus my calendar widget is stuck on yesterday.`
- **out_of_scope → screen_turns_off_fast** (2): `My dog keeps sleeping fast after eating.`; `How to put a screen lock password on my gallery?`
- **out_of_scope → phone_not_ringing** (2): `Why does my alarm clock keep ringing at 5 AM even on Sundays?`; `My caller tune is not playing Bollywood songs for my friends.`
- **no_internet → wifi_no_load** (1): `Everything online is stuck but the phone itself is working`
- **notifications_missing → no_internet** (1): `whatsap mesages only show when i open app`
- **screen_too_dim → text_too_small** (1): `I can hardly make out what is on the screen`
- **screen_turns_off_fast → out_of_scope** (1): `phone locks while im reding`

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 262 | 67 | 15 | 66 |
| out of scope (164) | 6 | 5 | 0 | 153 |
| vague (28) | 15 | 4 | 4 | 5 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 88.6% | 79.5% to 97.7% |
| slice: indian_english | 46 | 67.4% | 54.3% to 80.4% |
| slice: long_story | 39 | 71.8% | 59.0% to 84.6% |
| slice: multi | 33 | 81.8% | 66.7% to 93.9% |
| slice: negation | 39 | 64.1% | 48.7% to 79.5% |
| slice: oos_near | 32 | 81.2% | 65.6% to 93.8% |
| slice: paraphrase | 82 | 67.1% | 57.3% to 76.8% |
| slice: plain | 192 | 87.0% | 82.3% to 91.1% |
| slice: short_vague | 5 | 80.0% | 40.0% to 100.0% |
| slice: typo | 73 | 61.6% | 50.7% to 72.6% |
| writer: chatgpt | 223 | 82.5% | 77.6% to 87.4% |
| writer: claude-blind | 96 | 79.2% | 70.8% to 86.5% |
| writer: gemini | 255 | 70.6% | 65.1% to 76.1% |

## Most common mistakes

- **wrong_time → out_of_scope** (15): `The time on my phone is wrong`; `The clock on the phone does not match the actual time`
- **cant_hear_call → phone_not_ringing** (12): `I cannot hear the other person during a call`; `The call is connected but I am getting no useful sound from the person speaking`
- **cant_hear_call → out_of_scope** (10): `The caller's voice is very low and I cannot hear properly`; `cant here the person on call`
- **screen_wont_rotate → out_of_scope** (10): `The video stays in the same upright view even when I hold the phone sideways`; `screen wont rotat when i turn it`
- **screen_wont_rotate → colours_wrong** (5): `Turning the phone around does not change the way the picture is shown`; `When I turn my mobile sideways, screen is not changing`
- **screen_too_dim → out_of_scope** (5): `I take my phone on my morning walk to see the steps count. Since last week the display has become so dull that outside I see only my own reflection.`; `The backlight drops to zero completely randomly.`
- **no_internet → out_of_scope** (5): `My brother sent me a video but it just keeps spinning forever.`; `evrything is stopng to load pls fix`
- **phone_not_ringing → out_of_scope** (5): `People are complaining I don't pick up.`; `My mobile stays perfectly quiet when someone tries to reach me.`
- **wrong_time → no_internet** (4): `date is showng wrong and apps giving error`; `I noticed the clock was showing a different time this morning and later one website would not open properly. I checked again and the date also looked strange. I want the phone to show the correct date and time automatically`
- **text_too_small → out_of_scope** (4): `writing on the phone is very fine, my eyes are paining while reading`; `The writing is completely microscopic and impossible to make out.`

## Tuning on dev

| C | Class weight | Macro-F1 | Log-loss | In-scope accuracy |  |
| --- | --- | --- | --- | --- | --- |
| 0.1 | none | 89.0% | 0.946 | 87.3% |  |
| 0.3 | none | 92.5% | 0.576 | 92.8% |  |
| 1.0 | none | 94.1% | 0.353 | 94.8% |  |
| 3.0 | none | 95.0% | 0.239 | 95.5% |  |
| 10.0 | none | 95.5% | 0.173 | 96.0% |  |
| 30.0 | none | 95.9% | 0.138 | 96.2% |  |
| 100.0 | none | 95.9% | 0.135 | 96.2% | **chosen** |
| 300.0 | none | 95.8% | 0.141 | 96.0% |  |
