# Out-of-scope prompt, v1

Out-of-scope training lines (M3 spec section 5), written by fresh agents like the training batches, one grid cell
per batch from [`plan-oos.json`](../plan-oos.json), with the persona phrases of [train-v2](train-v2.md). No example
sentences are shown.

Topics next to the held-out intents (the screen rotating, the clock or date, hearing during calls) are kept out, so
training never teaches "rotation means out of scope" and the zero-shot test stays clean. The proxy test set still
has such lines, written before this rule.

```text
Do not read any files or run any commands. Use only your own imagination. Use exactly one tool, once: when
you have written all the messages, save them with the Write tool to {path}, then reply only "done".

Context: a phone help app for people who are not comfortable with technology. They type their phone trouble
into a box in their own words. The app can fix only these problems: no internet; Wi-Fi connected but nothing
loads; the phone not ringing for calls; late or missing message notifications; the phone reading the screen
aloud; wrong screen colours; a screen that is too dark; the screen switching off too quickly; text too small;
wireless earphones or speakers not connecting; an app not allowed to use the camera, microphone or location; and
resetting network settings. I need realistic messages the app must NOT treat as any of those, to train it to say
"sorry, I can't help with that". They are invented, not from real people.

The writer for every message in this batch is {age} {comfort} {variety}. {style} {typos}
Keep that one writer's voice, but vary the situation and the wording from message to message.

Write exactly 120 messages, in four groups:
- 40 about real phone problems the app cannot fix: battery draining or swelling, charging, the phone getting
  hot, storage full, a slow or frozen phone, apps crashing or not installing, updates, a cracked or broken screen,
  a broken speaker or camera, wired earphones, forgotten passwords or patterns, SIM cards, no signal for calls,
  one-time passcodes not arriving, a zoomed-in screen, a screen that is too bright, dark mode, a warm night-time
  tint, choosing or changing a ringtone, a ringtone that is too loud, contacts or photos gone, a lost or stolen
  phone, factory resetting the whole phone, bills and recharges.
- 30 that use words from the fixable problems (ring, dark, colour, connect, signal, network, speaker, small,
  sound, voice, reset, permission, notification, Bluetooth, Wi-Fi and so on) with a completely different meaning:
  health, jewellery, food, clothes, weather, vehicles, family, work, school, money.
- 25 commands or requests for things the app doesn't do, including the opposite of a fix: turning airplane mode
  or do-not-disturb on, switching Wi-Fi or Bluetooth off, turning the torch on, calling or messaging someone,
  setting an alarm or reminder, taking a photo, opening an app, playing music.
- 25 that are not phone problems at all: greetings, thanks, small talk, questions about weather, news, sport,
  recipes, prices, directions, religion, health.

Never write about the screen turning or rotating, the clock, time or date, or hearing or being heard during a
call.

Write the file in only this plain-text format, with nothing before or after it and no code fences, keeping the
four headers exactly:

## out_of_scope | plain
(the 40 unfixable phone problems, one per line)
## out_of_scope | collision
(the 30)
## out_of_scope | oos_near
(the 25 commands and requests)
## out_of_scope | plain
(the 25 non-phone messages)
```
