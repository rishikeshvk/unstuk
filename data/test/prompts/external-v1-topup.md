# Proxy test prompt, v1 top-up (one round, ChatGPT or Gemini)

The review left out of scope at 134 (target 150) and the `collision` slice at 26 (target 30). This tops both up
with a non-Claude writer. Paste the prompt below into a **fresh** chat, and save the inside of the reply's code
block (without the ``` lines) exactly as returned to `data/test/sheets/<generator>-topup.txt`. Note which model
wrote it.

---

You are helping test a phone help app for people who are not good with technology, many of them in India. People
type their phone problem into the app in their own words. The app can only fix these phone problems: no internet,
Wi-Fi connected but nothing loads, the phone not ringing for calls, not hearing the caller during a call, late or
missing message notifications, the phone reading the screen aloud, wrong screen colours, a too-dark screen, the
screen switching off too fast, the screen not turning sideways, text too small, Bluetooth earphones not connecting,
an app not allowed to use the camera, microphone or location, a wrong clock or date, and resetting network
settings.

Write messages the app must NOT treat as any of those problems.

- 18 messages that use words from those problems (ring, dark, colour, signal, connect, sound, time, speaker,
  rotate, small, voice, network, reset, permission and so on) but mean something completely different: health,
  jewellery, food, clothes, weather, vehicles, family, work, school. Under `## out_of_scope | collision`.
- 12 messages about phone matters the app can't fix: hardware damage, SIM cards, recharges and bills, apps
  crashing or not installing, storage, battery, passwords, contacts, photos, the phone being stolen or lost. Under
  `## out_of_scope | plain`.

Write as many different kinds of people: elderly parents, teenagers, shopkeepers, people with weak English,
annoyed people. Vary length from two words to three sentences; some with typos, some in Indian English. Each
message on its own line, ending with its tag after `|`. Output only a single code block in exactly this format:

```
## out_of_scope | collision
first message | collision
...

## out_of_scope | plain
first message | plain
...
```
