# Keyword baseline on the proxy test set

Written by `uv run unstuk-evaluate-keywords`; do not edit by hand. M2's keyword matcher, ported to Python, scored on all 602 frozen test lines. Intervals are 95% bootstrap intervals.

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 40.2% | 35.5% to 44.6% |
| Top-1 accuracy, all clear lines | 51.9% | 47.8% to 56.0% |
| Macro-F1 | 50.6% | 45.4% to 54.6% |
| Out-of-scope recall | 81.1% | 75.2% to 87.0% |
| Out-of-scope precision | 38.6% | 33.9% to 43.6% |
| **Confident and wrong** | 8.7% | 6.5% to 10.9% |
| Vague lines answered with a question or decline | 67.9% | 50.0% to 85.2% |
| Expected calibration error | 22.6% | 18.1% to 28.7% |
| Held-out intents (not zero-shot: the matcher has rules for them) | 35.0% | 24.7% to 45.2% |

## What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 170 | 28 | 0 | 212 |
| out of scope (164) | 25 | 6 | 0 | 133 |
| vague (28) | 9 | 0 | 0 | 19 |

## By slice and by writer

Vague lines are left out: they have no single right answer.

| Group | Clear lines | Accuracy | 95% interval |
| --- | --- | --- | --- |
| slice: collision | 44 | 52.3% | 38.6% to 65.9% |
| slice: indian_english | 46 | 41.3% | 26.1% to 54.3% |
| slice: long_story | 39 | 38.5% | 23.1% to 53.8% |
| slice: multi | 33 | 75.8% | 60.6% to 87.9% |
| slice: negation | 39 | 33.3% | 17.9% to 48.7% |
| slice: oos_near | 32 | 81.2% | 65.6% to 93.8% |
| slice: paraphrase | 82 | 23.2% | 14.6% to 31.7% |
| slice: plain | 192 | 74.5% | 68.2% to 80.2% |
| slice: short_vague | 5 | 40.0% | 0.0% to 80.0% |
| slice: typo | 73 | 24.7% | 15.1% to 35.6% |
| writer: chatgpt | 223 | 61.4% | 54.7% to 67.7% |
| writer: claude-blind | 96 | 52.1% | 41.7% to 62.5% |
| writer: gemini | 255 | 43.5% | 37.6% to 49.0% |

## Most common mistakes

- **wifi_no_load → out_of_scope** (18): `The WiFi symbol is there and strong, but every online page just waits`; `wifi conneted but nothng loading`
- **cant_hear_call → out_of_scope** (18): `I can talk but the voice from the other side is missing`; `cant here the person on call`
- **phone_not_ringing → out_of_scope** (17): `Calls are coming in but the phone stays quiet`; `People say they called me but I only notice afterwards`
- **talkback_on → out_of_scope** (17): `I have to touch things twice now and there is a box around everything`; `The phone is reading the screen aloud and one touch does not open anything`
- **screen_turns_off_fast → out_of_scope** (17): `The phone locks while I am still using it`; `The display disappears before I finish reading`
- **reset_network → out_of_scope** (17): `I want to reset all the phone's connection settings`; `I need to clear the saved connection setup and start again`
- **no_internet → out_of_scope** (16): `Everything online is stuck but the phone itself is working`; `I can use the phone but anything that needs online connection just sits there`
- **notifications_missing → out_of_scope** (16): `Messages are there but the phone does not tell me when they arrive`; `I only discover new messages after checking the apps myself`
- **screen_too_dim → out_of_scope** (13): `I can hardly make out what is on the screen`; `The picture on the phone looks faint, especially outside`
- **wrong_time → out_of_scope** (13): `The time on my phone is wrong`; `time on my phne is rong`
