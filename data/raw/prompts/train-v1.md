# Training prompt, v1

Each training batch is written by a fresh agent with no project context, so nothing it writes can echo the
proxy test set (M3 spec section 5). The prompt below is filled in for the batch's grid cell from
[`plan.json`](../plan.json), using the phrase table, and the reply is saved as returned to
`data/raw/sheets/<batch>.txt`. It shows no example sentences: example lines get copied, and the guide's examples
must never become data.

## Phrase table

| Axis | Value | Phrase |
| --- | --- | --- |
| age | teen | a teenager |
| age | adult | an adult in their thirties or forties |
| age | senior | a person over seventy |
| comfort | low | who finds phones confusing and doesn't know the names of settings |
| comfort | medium | who uses a phone every day but doesn't know technical terms |
| variety | indian | and writes Indian English, the way people in India commonly phrase things |
| variety | british | and writes British English |
| variety | american | and writes American English |
| variety | second_language | and whose first language isn't English, so sentences are simple and sometimes ungrammatical |
| style | plain | They state the problem simply. |
| style | question | They ask about it as a question. |
| style | story | They tell a short story of two to four sentences about what happened before getting to the problem. |
| style | frustrated | They are annoyed or worried, and it shows. |
| style | dictated | They use voice typing: no punctuation, run-on sentences, the odd misheard word. |
| style | terse | They write only two to five words. |
| typos | none | They spell correctly. |
| typos | some | About a third of their messages have a typing mistake. |
| typos | many | They make many typing mistakes and skip capitals and apostrophes. |

## Template

```text
Do not use any tools and do not read any files. Answer only from your own imagination, in a single reply.

Context: a phone help app for people who are not comfortable with technology. They type their phone trouble
into a box in their own words. I need realistic messages to train the app. They are invented, not from real
people.

The writer for every message in this batch is {age} {comfort} {variety}. {style} {typos}
Keep that one writer's voice, but vary the situation, the wording and the length from message to message. In
about a third of the messages, mention an app (WhatsApp, YouTube, Google Maps, a bank or payment app, and so on)
or what happened just before the problem.

Write exactly 10 messages for each of the 12 problems below. Use the problem's own technical name (such as the
name of a setting) in at most two of its 10 messages; people describe what they see. One or two of the 10 may be
a request or a "how do I" question about fixing it. Each message must clearly be about its problem and not about
anything listed under "Not".

Do not write about any other phone problem. In particular, never write about the screen not turning sideways,
the clock or date being wrong, or not hearing the other person during a call.

Problems (id: what it is. Not: what belongs elsewhere):
- no_internet: nothing online works on the phone, because mobile data is off, airplane mode is on, Wi-Fi is
  switched off, or a data-saving mode blocks apps. Not: Wi-Fi showing as connected while pages fail to load;
  bills, recharges or data balance.
- wifi_no_load: the person says the phone is connected to Wi-Fi (the network's name, a tick, full bars), yet
  websites and apps don't load. Not: Wi-Fi switched off or "not working" without saying it is connected;
  forgotten Wi-Fi passwords.
- phone_not_ringing: incoming calls, ordinary or WhatsApp, make no sound: the phone is stuck on silent or
  vibrate, do-not-disturb is on, or the ring volume is at zero; the person finds missed calls later. Not: messages
  that make no sound; choosing a ringtone or a ringtone that is too loud.
- notifications_missing: messages and app alerts arrive late, silently, or only when the app is opened. Not:
  calls; one-time passcodes not arriving; apps that won't open.
- talkback_on: the phone speaks everything aloud, draws a box around items, one tap no longer opens things and a
  double tap is needed, scrolling needs two fingers. Not: a car or voice assistant reading messages; a zoomed-in
  screen.
- colours_wrong: the screen is grey, black and white, inverted like a photo negative, or oddly tinted. Not: the
  whole screen being too dark; wanting dark mode; a warm night-time tint.
- screen_too_dim: the screen is too dark, hard to see outdoors, dims by itself, or brightness won't go up. Not:
  wrong colours; the screen switching off; a screen that is too bright.
- screen_turns_off_fast: the screen goes black or locks too quickly while reading or watching. Not: the screen
  going black during calls near the ear; the phone shutting down or restarting.
- text_too_small: the letters, text or icons are too small to read; the person wants a bigger font. Not: a zoomed
  or magnified screen; text that is too big.
- bluetooth_earphones: wireless earbuds, a speaker, a watch or a car won't connect or pair, or Bluetooth is off.
  Not: wired earphones; earbud batteries or charging cases.
- app_permission: the camera, microphone or location doesn't work inside one particular app, or the app asks for
  permission. Not: a camera broken in every app; the other person not hearing me.
- reset_network: the person explicitly asks to reset the phone's network settings (Wi-Fi, mobile and Bluetooth
  settings). Not: the network not working without asking for a reset; factory resetting the whole phone.

Output only this plain-text format, with nothing before or after it and no code fences:

## problem_id
first message
second message
...
```
