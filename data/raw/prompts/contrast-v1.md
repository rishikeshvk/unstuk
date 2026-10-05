# Contrast-pair prompt, v1

Contrast pairs (M3 spec section 5; Gardner et al. 2020): two messages that differ only in the words that move them
across a boundary, so the model must look at those words. Written by fresh agents, one grid cell per batch from
[`plan-contrast.json`](../plan-contrast.json), with the persona phrases of [train-v2](train-v2.md). Each pair is
written as two consecutive sections, so its records get consecutive IDs.

Boundaries that involve a held-out intent are left out (invariant 9), and so are out-of-scope sides next to them.

```text
Do not read any files or run any commands. Use only your own imagination. Use exactly one tool, once: when
you have written all the messages, save them with the Write tool to {path}, then reply only "done".

Context: a phone help app for people who are not comfortable with technology. They type their phone trouble
into a box in their own words. I need realistic message pairs to teach the app where one problem ends and the next
begins. They are invented, not from real people.

The writer for every message in this batch is {age} {comfort} {variety}. {style} {typos}

A pair is two messages that are as alike as possible: same situation, same voice, mostly the same words. Only the
few words that decide which side it belongs to change. For each of the 14 boundaries below, write exactly 4 pairs,
each a different situation. That is 56 pairs, 112 messages.

Boundaries (left id / right id: what decides it):
1. no_internet / wifi_no_load: Wi-Fi off, mobile data off or airplane mode, versus the phone showing it is
   connected to Wi-Fi while nothing loads.
2. phone_not_ringing / notifications_missing: incoming calls make no sound, versus messages or app alerts arriving
   late or silently.
3. screen_too_dim / colours_wrong: the screen is too dark, versus the screen turned grey, black and white or
   inverted.
4. screen_too_dim / out_of_scope: the screen is too dark, versus the screen is too bright or the person wants dark
   mode.
5. screen_turns_off_fast / out_of_scope: the screen goes black too quickly while reading, versus the whole phone
   switching off or restarting.
6. text_too_small / out_of_scope: the letters are too small, versus the whole screen being zoomed in or magnified.
7. talkback_on / out_of_scope: the phone reads aloud whatever is touched and needs double taps, versus a car
   system or voice assistant reading messages aloud.
8. bluetooth_earphones / out_of_scope: wireless earbuds or a speaker won't connect, versus wired earphones not
   working or the earbuds' battery being dead.
9. app_permission / out_of_scope: one app can't use the camera, microphone or location, versus the camera being
   broken or cracked in every app.
10. reset_network / no_internet: asking to reset the network settings, versus saying the internet doesn't work
    without asking for a reset.
11. reset_network / out_of_scope: resetting only the network settings, versus factory resetting the whole phone.
12. notifications_missing / out_of_scope: messages or app alerts arriving late, versus one-time passcodes by SMS
    not arriving.
13. phone_not_ringing / out_of_scope: calls make no sound, versus the ringtone being too loud or wanting a
    different ringtone.
14. no_internet / out_of_scope: mobile data or Wi-Fi switched off, versus the data pack or recharge running out.

Write the file in only this plain-text format, with nothing before or after it and no code fences. Each pair is
two sections in a row, left side first, each with its own header:

## left_id
first message of the pair
## right_id
second message of the pair
```
