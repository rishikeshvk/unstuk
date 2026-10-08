# Vague prompt, v1

M6 spec section 1. Dev has no vague lines and train has three, so the model has never seen a complaint whose
right answer is "which of these do you mean?". These batches supply them, for train and dev only.

The setup is the same as [train-v2](../../raw/prompts/train-v2.md): one writer per batch from [`plan.json`](../plan.json),
filled in with train-v2's phrase table, and no example sentences, because example lines get copied and the guide's
examples must never become data. Each batch has 30 lines. The writer saved them itself to
`data/raw/sheets/<batch>.txt`; they were then moved, unedited, to `data/vague/sheets/`, so that `unstuk-clean`,
which reads all of `data/raw/`, leaves M5's train and dev split unchanged.

`vague-06`, `-07`, `-13` and `-14` go to dev and the other ten to train. `vague-08` to `-14` are a top-up, from
a second grid draw (seed 62), after the blind check kept only half of the first seven; they saved straight to
`data/vague/sheets/`. The split is by batch, so one
writer's style never lands on both sides.

## Template

```text
Do not read any files or run any commands. Use only your own imagination. Use exactly one tool, once: when
you have written all the messages, save them with the Write tool to {path}, then reply only "done".

Context: a phone help app for people who are not comfortable with technology. They type their phone trouble
into a box in their own words. I need realistic messages to train the app. They are invented, not from real
people.

The writer for every message in this batch is {age} {comfort} {variety}. {style} {typos}
Keep that one writer's voice, but vary the situation, the wording and the length from message to message.

This batch is only UNCLEAR messages: each one could honestly mean two or three of the problems below, and a
careful reader could not tell which without asking. For example, the writer names an app or a feeling but not
what actually goes wrong. Write exactly 30 messages. Each must:
- fit two or three of the problems below about equally well, and none better than the others;
- not be about anything outside the list, and never about the screen not turning sideways, the clock or date
  being wrong, or not hearing the other person during a call;
- not be so empty that it could mean anything at all ("help", "hi").
Spread the messages across many different pairs and triples of problems; use no pair more than four times.

Problems (id: what it is):
- no_internet: nothing online works, because mobile data is off, airplane mode is on, Wi-Fi is switched off, or
  a data-saving mode blocks apps.
- wifi_no_load: the phone shows it is connected to Wi-Fi, yet websites and apps don't load.
- phone_not_ringing: incoming calls make no sound; the person finds missed calls later.
- notifications_missing: messages and app alerts arrive late, silently, or only when the app is opened.
- talkback_on: the phone speaks everything aloud and needs a double tap to open things.
- colours_wrong: the screen is grey, black and white, inverted or oddly tinted.
- screen_too_dim: the screen is too dark or dims by itself.
- screen_turns_off_fast: the screen goes black or locks too quickly while reading or watching.
- text_too_small: the letters, text or icons are too small to read.
- bluetooth_earphones: wireless earbuds, a speaker, a watch or a car won't connect.
- app_permission: the camera, microphone or location doesn't work inside one particular app.
- reset_network: the person asks to reset the phone's network settings.

Write the file in only this plain-text format, with nothing before or after it and no code fences. Before each
message, write a header line with the two or three problem ids it could mean, separated by commas:

## first_id, second_id
the message
## first_id, second_id, third_id
the next message
```

`unstuk-vague-slice` reads the sheets directly; see the [README](../README.md).
