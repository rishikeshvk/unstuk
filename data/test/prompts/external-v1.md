# Proxy test prompt, v1 (Gemini app and open models in opencode)

This prompt is deliberately unlike the training recipe: no example sentences are shown, problems are described
as situations, and the writer is asked for specific kinds of difficulty. Paste **Part A** into a fresh chat, save
the reply, then paste **Part B** into the same chat. Save the inside of each reply's code block (without the ``` lines) exactly as returned, without
editing, to `data/test/sheets/<generator>-a.txt` and `<generator>-b.txt`. Note which model wrote it.

---

## Part A

You are helping test a phone help app for people who are not good with technology, many of them in India. People
type their phone problem into the app in their own words. Write the messages that real people would type for each
problem below.

Rules:
- Write as many different kinds of people: elderly parents, teenagers, busy shopkeepers, people with weak English,
  people who are annoyed. Vary length from two words to four sentences.
- Never use the problem's name or its ID in the message. People describe what they see, not the setting.
- Write exactly 10 messages per problem, one per line, with these kinds, ending each line with its tag after `|`:
  - 2 ordinary messages: `| plain`
  - 2 that avoid the obvious words for the problem (for example, not "ring" for a phone that doesn't ring):
    `| paraphrase`
  - 2 with realistic typing mistakes and no punctuation: `| typo`
  - 1 in Indian English, the way people speak in India: `| indian_english`
  - 1 long message, two to four sentences, where the problem comes only at the end: `| long_story`
  - 1 that first says what the problem is NOT, then what it is: `| negation`
  - 1 that is a command or a how-to question about fixing it: `| plain`
- Output only a single code block in exactly this format, with each problem's header copied exactly:

```
## no_internet
first message | plain
...
```

Problems:

## no_internet
The phone has no internet at all: mobile data is off, airplane mode is on, Wi-Fi is off, or a data-saving mode
blocks apps. Websites, YouTube and WhatsApp don't load.

## wifi_no_load
The phone shows it is connected to Wi-Fi, often with full signal, but websites and apps still don't load.

## phone_not_ringing
People call but the phone makes no sound: it is on silent or vibrate, Do Not Disturb is on, or the ring volume is
at zero. The person only sees missed calls later.

## cant_hear_call
During a call the person can't hear the caller, or the voice is very faint, or the sound goes to earbuds or a car
they are not using.

## notifications_missing
Messages and app alerts (WhatsApp, SMS from friends, email, bank apps) arrive late, silently or only when the app is
opened.

## talkback_on
A screen reader was switched on by accident: the phone speaks everything aloud, draws a box around items, and a
single tap no longer works, it needs a double tap.

## colours_wrong
The screen suddenly shows wrong colours: black and white, grey, or inverted like a photo negative.

## screen_too_dim
The screen is too dark to see comfortably, especially outdoors, or keeps dimming.

## screen_turns_off_fast
The screen switches off or locks after a few seconds while the person is still reading or watching.

## screen_wont_rotate
The screen stays upright when the phone is turned sideways, so videos and photos don't fill the screen.

## text_too_small
The letters and text on the phone are too small for the person to read.

## bluetooth_earphones
Wireless earphones, earbuds, a speaker, a watch or a car won't connect to the phone.

## app_permission
The camera, microphone or location doesn't work inside one particular app, or the app says it needs permission.

## wrong_time
The phone's time or date is wrong, or apps and websites complain about the time, the date or a certificate.

## reset_network
The person has tried everything with their connection and now asks how to reset the phone's network settings.

---

## Part B

Now write messages for the same app that it must NOT treat as one of the problems above, plus some unclear ones.
Same people, same variety, same output format (one code block, headers copied exactly, tag after `|`).

- 12 messages that use words from the problems above but mean something else, such as body parts, jewellery,
  food or weather: under `## out_of_scope | collision`
- 13 messages about real phone topics close to the problems above that the app can't fix, such as bills,
  recharges, dark mode, alarms, a broken screen, a phone that is too bright or rotates when it shouldn't:
  under `## out_of_scope | oos_near`
- 20 messages about other phone problems: battery, storage, slow phone, crashing apps, forgotten passwords, a phone
  that gets hot: under `## out_of_scope | plain`
- 15 messages that are not phone problems at all: greetings, thanks, questions about other things, requests to call
  someone: under `## out_of_scope | plain`
- 15 short, unclear messages that could mean two or three of the problems in Part A. For each one, write a header
  with the two or three problem IDs it could mean, then the message tagged `| vague short_vague`, for example:

```
## phone_not_ringing, notifications_missing
no sound | vague short_vague
```

- 15 messages that describe two problems from Part A at once. For each, a header with the two IDs, the main problem
  first, then the message tagged `| multi`.
