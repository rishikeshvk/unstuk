# M3 labelling guide

2026-10-05 · Part of [M3](m3-spec.md), step 2

This guide says which label a complaint gets. Every line of M3 data is labelled by it, whoever wrote the line:
you, Claude, Gemini or an open model. It exists so that two labellers, given the same complaint, pick the same
label. Most "model errors" on a small task like ours turn out to be labels that disagree, so this guide matters as
much as the model.

All examples here are invented. They are never copied into `data/`, so the guide can't leak into the test set.

## 1. How to use it

1. Read the whole complaint, not just the first words.
2. Ask: **what does this person want fixed?** Label the problem, not the words. "My ring finger hurts" contains
   "ring" but isn't about the phone ringing.
3. If two labels seem possible, find the rule in [section 5](#5-confusable-pairs).
4. If no rule settles it, **stop and add a rule here first**, with an example, then label. Never guess silently:
   a guess made once becomes an inconsistency across a hundred lines.

## 2. Labels

Each complaint gets an ordered list of labels:

- Usually **one** label.
- **Two** when the complaint clearly describes two separate problems ("no internet, and the screen is too dark").
  The main one comes first: the one the person stresses, or else the one they say first. Never more than two.
- A label is one of the 15 intent IDs below, or `out_of_scope`. `out_of_scope` is never combined with an intent.

| Intent | Option text (what the model chooses between) |
| --- | --- |
| `no_internet` | The internet or mobile data is not working |
| `wifi_no_load` | Wi-Fi is connected but websites and apps don't load |
| `phone_not_ringing` | The phone does not ring when someone calls |
| `cant_hear_call` | I can't hear the other person during a call |
| `notifications_missing` | Messages or notifications arrive late or not at all |
| `talkback_on` | The phone talks to me and I have to tap twice |
| `colours_wrong` | The screen colours look wrong, inverted or black and white |
| `screen_too_dim` | The screen is too dark |
| `screen_turns_off_fast` | The screen turns off too quickly |
| `screen_wont_rotate` | The screen does not turn sideways when I turn the phone |
| `text_too_small` | The letters and text on the screen are too small |
| `bluetooth_earphones` | My Bluetooth earphones or speaker won't connect |
| `app_permission` | The camera, microphone or location doesn't work in an app |
| `wrong_time` | The time or date is wrong, or apps show a time or certificate error |
| `reset_network` | Nothing on the network works and I want to reset the network settings |

The option texts come from `catalog/intents.json`; if they change there, this table changes with them.

## 3. What every intent includes

A complaint belongs to an intent when it is any of these:

- **A symptom** of the problem: "my phone doesn't ring".
- **A how-to question** about it: "how do I make the letters bigger?"
- **A command** for one of its fixes: "turn off airplane mode" (see [section 6](#6-commands)).

## 4. Intent by intent

### `no_internet`
- **In:** no internet, mobile data not working, "net is not coming", airplane or flight mode stuck on, Wi-Fi off or
  "not working" (without saying it's connected), Data Saver blocking everything, "no 4G".
- **Not in:** Wi-Fi *connected* but pages don't load (`wifi_no_load`); a recharge or bill question
  (`out_of_scope`); no signal bars for calls only, "no service" (`out_of_scope`).
- "Net not working since morning" → `no_internet`
- "Wi-Fi shows connected but YouTube won't load" → `wifi_no_load`
- "How much data is left in my pack" → `out_of_scope`

### `wifi_no_load`
- **In:** the person says Wi-Fi is connected, or shows full bars or a Wi-Fi symbol, yet websites or apps don't
  load; "connected, no internet" shown under the Wi-Fi name; Private DNS questions.
- **Not in:** time or certificate errors (`wrong_time`); Wi-Fi off or "not working" with no mention of being
  connected (`no_internet`); forgotten Wi-Fi password (`out_of_scope`).
- "It says connected without internet" → `wifi_no_load`
- "Wi-Fi is not working" → `no_internet`

### `phone_not_ringing`
- **In:** incoming calls don't ring or make no sound, in any app (phone, WhatsApp, Meet); missed calls the person
  never heard; the phone is stuck on silent or vibrate; Do Not Disturb on.
- **Not in:** can't hear the caller *during* the call (`cant_hear_call`); messages with no sound
  (`notifications_missing`); ringtone too loud or wanting a new ringtone (`out_of_scope`).
- "WhatsApp calls don't ring, only show missed" → `phone_not_ringing`
- "My phone is always on vibrate" → `phone_not_ringing`

### `cant_hear_call` (held out)
- **In:** during a call the other person's voice is missing or too quiet; call sound goes to earbuds or the car
  when the person wants it on the phone.
- **Not in:** the earbuds won't connect at all (`bluetooth_earphones`); the *other* person can't hear me
  (microphone, `out_of_scope`); no ringing (`phone_not_ringing`).
- "I can't hear anything when I pick up" → `cant_hear_call`
- "People say they can't hear me" → `out_of_scope`

### `notifications_missing`
- **In:** messages, WhatsApp texts, emails or app alerts arrive late, silently or not at all; no notification sound
  for messages.
- **Not in:** calls (`phone_not_ringing`); an app that won't open (`out_of_scope`); OTP SMS not arriving
  (`out_of_scope`: the cause is usually the network operator or SIM, which we don't check).
- "I only see WhatsApp messages when I open the app" → `notifications_missing`
- "OTP is not coming" → `out_of_scope`

### `talkback_on`
- **In:** the phone speaks or reads out everything; a green or coloured box around items; single taps don't work,
  the person has to tap twice; scrolling needs two fingers.
- **Not in:** the phone reads messages aloud through the car or Assistant (`out_of_scope`); zoomed-in screen
  (`out_of_scope`).
- "A lady's voice reads everything I touch" → `talkback_on`
- "Have to double tap to open anything" → `talkback_on`

### `colours_wrong`
- **In:** the screen is black and white, grey, inverted ("like a photo negative"), or has a strange tint.
- **Not in:** the whole screen is dark (`screen_too_dim`); the person wants dark mode (`out_of_scope`); a warm,
  yellow tint at night is Night Light, which isn't in the catalog (`out_of_scope`).
- "Everything turned grey suddenly" → `colours_wrong`
- "White became black and black became white" → `colours_wrong`

### `screen_too_dim`
- **In:** the screen is too dark, hard to see outdoors, dims by itself, brightness won't go up.
- **Not in:** grey or inverted colours (`colours_wrong`); the screen goes *black* after a few seconds
  (`screen_turns_off_fast`); the screen is too bright (`out_of_scope`: the fix only brightens).
- "Can't see the screen in sunlight" → `screen_too_dim`
- "The screen is too bright at night" → `out_of_scope`

### `screen_turns_off_fast`
- **In:** the screen goes off, black or locks too quickly while reading or watching.
- **Not in:** the screen goes black during calls, near the ear (proximity sensor, `out_of_scope`); the phone
  restarts or switches off fully (`out_of_scope`).
- "Screen keeps going off while I read a recipe" → `screen_turns_off_fast`
- "Screen goes black when I'm on a call" → `out_of_scope`

### `screen_wont_rotate` (held out)
- **In:** the screen doesn't turn sideways when the phone is turned; videos stay upright; auto-rotate.
- **Not in:** the screen turns sideways when the person *doesn't* want it to (`out_of_scope`: the fix only turns
  rotation on).
- "Videos don't go full screen when I turn the phone" → `screen_wont_rotate`
- "The screen keeps turning sideways in bed" → `out_of_scope`

### `text_too_small`
- **In:** letters, text or icons too small to read; how to make the font or text bigger.
- **Not in:** the screen is zoomed or magnified (`out_of_scope`); text is too big (`out_of_scope`); blurry
  eyesight in general (`out_of_scope`).
- "I need my glasses to read messages" → `text_too_small`
- "Everything suddenly became huge and zoomed" → `out_of_scope`

### `bluetooth_earphones`
- **In:** earphones, earbuds, a speaker, a smartwatch or a car won't connect or pair over Bluetooth; Bluetooth
  turned off.
- **Not in:** connected but no sound in a call (`cant_hear_call`); wired earphones (`out_of_scope`); earbud
  battery or charging case problems (`out_of_scope`).
- "My buds are not connecting to the phone" → `bluetooth_earphones`
- "Earbuds connected but can't hear the caller" → `cant_hear_call`

### `app_permission`
- **In:** the camera, microphone or location doesn't work *in an app*, or an app says it needs permission;
  "Google Maps can't find my location".
- **Not in:** the camera is broken or cracked in every app, or the lens is black (`out_of_scope`); "the other
  person can't hear me on calls" (`out_of_scope`).
- "WhatsApp can't use my camera" → `app_permission`
- "My camera glass is cracked" → `out_of_scope`

### `wrong_time` (held out)
- **In:** the clock, date or time zone is wrong; apps or websites show a time, date, clock or certificate error.
- **Not in:** an alarm that didn't go off (`out_of_scope`).
- "Chrome says your clock is ahead" → `wrong_time`
- "The phone shows yesterday's date" → `wrong_time`

### `reset_network`
- **In:** the person explicitly asks to reset network settings, or to reset Wi-Fi, mobile and Bluetooth
  settings.
- **Not in:** "nothing on the network works" without asking for a reset (`no_internet`); factory reset of the
  whole phone (`out_of_scope`).
- "How do I reset network settings" → `reset_network`
- "Should I factory reset my phone?" → `out_of_scope`

## 5. Confusable pairs

| Pair | Rule |
| --- | --- |
| `no_internet` / `wifi_no_load` | Only "Wi-Fi is **connected** (or shows full bars) but nothing loads" is `wifi_no_load`. "Wi-Fi not working" without saying it's connected is `no_internet`, because Wi-Fi being off is one of `no_internet`'s causes |
| `phone_not_ringing` / `notifications_missing` | **Incoming calls**, in any app, are `phone_not_ringing`. **Messages and alerts** are `notifications_missing`. Both described → both labels |
| `screen_too_dim` / `colours_wrong` | **Overall darkness** is `screen_too_dim`. **Grey, black and white, inverted or tinted** is `colours_wrong`. "Dark and grey" describes colour, so `colours_wrong` |
| `wrong_time` / `wifi_no_load` | Any mention of **time, date, clock or a certificate or time error** is `wrong_time`, even if pages don't load |
| `cant_hear_call` / `bluetooth_earphones` | The device **won't connect or pair** is `bluetooth_earphones`. Connected, or no device at all, but **the caller's voice can't be heard** is `cant_hear_call` |
| `talkback_on` / `text_too_small` | **Speaking, double tap, green box** is `talkback_on`. **Small letters** is `text_too_small`. A **zoomed or magnified** screen is `out_of_scope` |

## 6. Commands

A command that names one of our fixes, with no symptom, gets the intent that owns the fix. The Diagnoser then
checks the phone and only runs the fix if it is needed. Three fixes are shared by two intents
(`data_saver_off`, `auto_time_on`, `dnd_off`); the table names one owner for each, the intent a command for it most
often means.

| Fix | Example command | Owning intent |
| --- | --- | --- |
| `airplane_off` | "turn off flight mode" | `no_internet` |
| `mobile_data_on` | "switch on mobile data" | `no_internet` |
| `wifi_on` | "turn Wi-Fi on" | `no_internet` |
| `data_saver_off` | "disable data saver" | `no_internet` |
| `auto_time_on` | "set the time automatically" | `wrong_time` |
| `private_dns_off` | "turn off private DNS" | `wifi_no_load` |
| `dnd_off` | "turn off do not disturb" | `phone_not_ringing` |
| `ringer_normal` | "take the phone off silent" | `phone_not_ringing` |
| `ring_volume_up` | "increase the ringtone volume" | `phone_not_ringing` |
| `call_volume_up` | "increase the call volume" | `cant_hear_call` |
| `audio_output_switch` | "move the call sound to the phone" | `cant_hear_call` |
| `talkback_off` | "turn off TalkBack" | `talkback_on` |
| `inversion_off` | "turn off colour inversion" | `colours_wrong` |
| `greyscale_off` | "remove the black and white mode" | `colours_wrong` |
| `brightness_up` | "increase the brightness" | `screen_too_dim` |
| `timeout_longer` | "make the screen stay on longer" | `screen_turns_off_fast` |
| `rotation_unlock` | "turn on auto-rotate" | `screen_wont_rotate` |
| `font_size_settings` | "make the font bigger" | `text_too_small` |
| `bluetooth_on` | "turn on Bluetooth" | `bluetooth_earphones` |
| `reset_network` | "reset the network settings" | `reset_network` |

A command for the **opposite** of a fix ("turn on airplane mode", "turn on do not disturb", "turn off
Bluetooth"), or for any other setting ("turn on the torch"), is `out_of_scope`: Unstuk can't do it.

## 7. `out_of_scope`

`out_of_scope` means Unstuk can't help, so the right reply is the polite decline. It covers:

- **Phone problems not in the catalog:** cracked screen or camera, battery draining or swelling, storage full, the
  phone is slow or hangs, apps crashing or not opening, zoomed screen, the screen going black during calls, OTPs
  not arriving, no signal for calls, a forgotten password or PIN.
- **In-scope words with another meaning:** "my ring finger hurts", "my internet bill is too high", "how do I turn on
  dark mode", "my Bluetooth speaker's battery died".
- **Things that aren't phone problems at all:** chit-chat ("hello", "thank you"), questions ("what's the weather"),
  and requests for things Unstuk doesn't do ("call my son", "set an alarm").

"Mobile is hanging" means the phone is slow or frozen, so it is `out_of_scope`, even though it sounds like a
network word.

## 8. The `vague` tag

Some complaints could mean several of our problems, and the right reply is "which of these do you mean?":

- "My phone is acting weird"
- "WhatsApp is not working"
- "I'm not getting anything"
- "Phone problem"

They get the tag `vague` and may list up to three plausible labels instead of one sure label, for example
`["no_internet", "notifications_missing"]` for "WhatsApp is not working". A model is scored on them by **not being
confident**, never by picking one. A vague complaint whose every reading is out of scope is just `out_of_scope`.

Don't over-use the tag: if a careful reader would pick one label, it isn't vague.

## 9. Language

- Any variety of English counts: Indian, British, American, second-language English, with typos, missing
  punctuation and mixed case. Common Indian English words keep their meaning: "net" (the internet), "mobile" (the
  phone), "recharge" (a prepaid top-up), "hanging" (frozen).
- Lines that are mostly Hindi or another language are **dropped**, not labelled. Hinglish is planned for v2.
  A single borrowed word in an English sentence ("my mobile is not working yaar") is fine.

## 10. Held-out intents

Three intents never appear in seeds, training or dev data. They appear **only** in the proxy test set, to measure
how well the model handles an intent it knows only from its option text (zero-shot).

| Intent | Why it was chosen |
| --- | --- |
| `screen_wont_rotate` | Unlike anything else in the catalog: the easy case |
| `wrong_time` | Shares a cause (automatic time) and some words with `wifi_no_load`: a hard case |
| `cant_hear_call` | Close to both `phone_not_ringing` and `bluetooth_earphones`: a hard case |

The same list is in `ml/src/unstuk_ml/labels.py`, where the data validator enforces it.

This guide still defines them, because the test set needs them labelled the same way as everything else, and
training data needs to know what they are so it can keep them out. A training line that turns out to belong to a
held-out intent is removed, not relabelled.

## 11. Practice set

Label these yourself before labelling any data, then compare. Each answer names the rule that decides it.

| # | Complaint | Labels | Rule |
| --- | --- | --- | --- |
| 1 | "my phone wont ring when my daughter calls" | `phone_not_ringing` | §4 |
| 2 | "wifi has full signal but google doesn't open" | `wifi_no_load` | §5 connected |
| 3 | "wifi not working" | `no_internet` | §5 not said to be connected |
| 4 | "net is not coming since recharge" | `no_internet` | §9 "net" |
| 5 | "my recharge is over how to recharge" | `out_of_scope` | §4 `no_internet`, not in |
| 6 | "whatsapp calls dont ring" | `phone_not_ringing` | §5 incoming calls |
| 7 | "whatsapp msgs come only when i open it" | `notifications_missing` | §5 messages |
| 8 | "whatsapp not working" | `vague`: `no_internet`, `notifications_missing` | §8 |
| 9 | "screen became dark and grey" | `colours_wrong` | §5 grey is colour |
| 10 | "can't see anything outside in the sun" | `screen_too_dim` | §4 |
| 11 | "how do i turn on dark mode" | `out_of_scope` | §7 another meaning |
| 12 | "it talks every time I touch something" | `talkback_on` | §4 |
| 13 | "everything is zoomed in and huge" | `out_of_scope` | §5 zoomed |
| 14 | "letters are very small for my eyes" | `text_too_small` | §4 |
| 15 | "earbuds connected but can't hear the caller" | `cant_hear_call` | §5 connected |
| 16 | "my earbuds won't pair" | `bluetooth_earphones` | §5 won't pair |
| 17 | "people can't hear me on calls" | `out_of_scope` | §4 `cant_hear_call`, not in |
| 18 | "chrome says certificate error" | `wrong_time` | §5 certificate |
| 19 | "screen goes black when I hold it to my ear" | `out_of_scope` | §7 proximity |
| 20 | "the screen locks while I'm reading" | `screen_turns_off_fast` | §4 |
| 21 | "videos stay small when I turn the phone" | `screen_wont_rotate` | §4 |
| 22 | "turn off flight mode" | `no_internet` | §6 command |
| 23 | "turn on do not disturb" | `out_of_scope` | §6 opposite |
| 24 | "turn off do not disturb" | `phone_not_ringing` | §6 owner |
| 25 | "zoom app can't use my mic" | `app_permission` | §4 in an app |
| 26 | "my ring finger hurts" | `out_of_scope` | §7 another meaning |
| 27 | "mobile is hanging a lot" | `out_of_scope` | §7 "hanging" |
| 28 | "no internet and the screen is too dark also" | `no_internet`, `screen_too_dim` | §2 two problems |
| 29 | "everything on the network is broken, how do I reset it" | `reset_network` | §4 asks for a reset |
| 30 | "otp not coming" | `out_of_scope` | §4 `notifications_missing`, not in |

Step 8's hand audit checks 200 training lines against this guide; agreement below 95% means the guide or the data
needs work.

## Changes

New rules are added with a date and the complaint that prompted them, so we can see how the guide grew.
