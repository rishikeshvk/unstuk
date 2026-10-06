# Option wordings prompt, v1

For M5 round 3 ([spec](../../docs/m5-spec.md), section 3). A fresh agent with no project context reads only the
text below the line and returns the sheet. The reply's code block is saved exactly as returned to
`catalog/sheets/option-wordings-v1.txt`, then imported to `catalog/option-wordings.json` with
`uv run unstuk-option-wordings import` (from `ml/`).

---

A phone help app shows a short list of problem descriptions and picks the one that matches what a user typed.
Each problem has one description today. Write 8 more descriptions of each problem below, so the app learns what
the problem *is* rather than one exact sentence.

Rules for every description:
- Describe what the person notices, in plain everyday English, 5 to 15 words. Some can start "My phone", some
  "The phone", some neither.
- Use different words from the current description wherever you can: other verbs, other nouns, other order.
- Never name a setting or a cause (no "Airplane mode", "Do Not Disturb", "TalkBack", "brightness setting", "Private
  DNS" and so on). The causes are listed only so you know what the problem covers.
- Each description must fit its own problem and no other problem in the list.
- No numbering, no quotes, no trailing full stop.

The problems, with their current description and, for background only, their usual causes:

- `no_internet`: The internet or mobile data is not working. Causes: airplane mode on, mobile data off, Wi-Fi off,
  data saver on.
- `wifi_no_load`: Wi-Fi is connected but websites and apps don't load. Causes: the clock not set automatically, a
  custom private DNS server.
- `phone_not_ringing`: The phone does not ring when someone calls. Causes: do not disturb, ringer on silent or
  vibrate, ring volume at zero.
- `notifications_missing`: Messages or notifications arrive late or not at all. Causes: do not disturb, data
  saver.
- `talkback_on`: The phone talks to me and I have to tap twice. Causes: the screen reader is on.
- `colours_wrong`: The screen colours look wrong, inverted or black and white. Causes: colour inversion,
  greyscale.
- `screen_too_dim`: The screen is too dark. Causes: very low brightness.
- `screen_turns_off_fast`: The screen turns off too quickly. Causes: a screen timeout of a few seconds.
- `text_too_small`: The letters and text on the screen are too small. Causes: text at its standard size.
- `bluetooth_earphones`: My Bluetooth earphones or speaker won't connect. Causes: Bluetooth off.
- `app_permission`: The camera, microphone or location doesn't work in an app. Causes: the app was denied
  permission.
- `reset_network`: Nothing on the network works and I want to reset the network settings. Causes: none to check;
  the person wants a network reset.

Reply with a single code block in exactly this format, every problem in this order, 8 lines under each header:

```
## no_internet
<description>
<description>
...
## wifi_no_load
<description>
...
```
