# M2 spec: Catalog + rules

2026-10-04 · Status: **Moto target met** (2026-10-04). Results: [m2-results.md](m2-results.md). Plain-language
summary: [m2-summary.md](m2-summary.md)

M2 answers one question: **can the whole pipeline, from a typed complaint to a verified fix, run end to end with
plain rules in place of the model?** It is done when, on the Moto Edge 30, a scripted complaint for each of the 15
intents reaches its expected outcome (a verified fix, a confirmation, guided steps or a decline), and an
independent adb read agrees with every outcome the app reports.

Background: [plan.md](plan.md), roadmap step 2, and [m1-results.md](m1-results.md). M1 proved that the executor can
undo airplane mode and DND and prove it. M2 builds the rest of the app around it, still with no ML, so that M7 can
swap a keyword matcher for the model without touching anything else.

```text
complaint ─► keyword matcher ─► risk gate ─► diagnosis ─► executor ladder ─► verify ─► report
             (IntentChoice)       │            (fresh       D → P → A → G      (fresh
                                  │             snapshot)                       read)
                                  └─► decline / clarifying question
```

## What changed from the plan

- **The risk tier belongs to the fix, not the intent.** The plan's catalog table gives one tier per complaint, but
  one complaint can have fixes of different tiers: "Wi-Fi connected but nothing loads" might call for turning on
  automatic time (low) or for clearing Private DNS (medium). The gate uses the tier of the fix that diagnosis
  picks.
- **More accessibility automation than the plan's roadmap implied.** Besides airplane mode and DND, M2 automates
  colour inversion, mobile data, Wi-Fi, Bluetooth, auto-rotate, data saver and automatic time where a Quick
  Settings tile or a Settings switch exists. Each one is still only one rung of its fix, never the only path
  (invariant 5).
- **The TalkBack-off spike moves from M1's stretch goal into M2.**
- **No P rung on a fix that has an A rung** (decided 2026-10-04, while implementing). Invariant 5 tries P before A,
  and a Settings Panel can always open, so an A rung after it would never run. A fix with automation therefore
  lists D, A and G only, and its guide card carries an "Open settings" button for when A is blocked. P stays for
  fixes with no automation (`private_dns_off`, `font_size_settings`). This keeps the invariant as written.

## Targets

| Metric | Target | Meaning |
| --- | --- | --- |
| End to end, Moto | 15/15 intents | A scripted complaint with its cause set up over adb reaches the expected outcome |
| Gate branches | 5/5 exercised | Auto, confirm, guided only, clarifying question and decline each occur in the scripted run |
| New accessibility rungs, Moto | ≥ 90% per rung | Verified out of 10 trials per rung, using M1's trial method |
| False success | 0 | The app reported success, but an independent adb read disagrees |
| Catalog consistency | Unit test green | Every rule in [Catalog](#catalog) below holds |

Ten trials is a smoke test, not a measurement: 9/10 has a 95% Wilson interval of about 60–98%. The M1 rungs
already have 20-trial numbers; M2 adds breadth, and M8 measures fix success on test users' phones.

## Intents

Rungs are listed in ladder order (invariant 5): **D** direct API, **P** Settings Panel or deep link (the app
opens the screen and the user taps), **A** accessibility automation (our service taps, in Quick Settings or
Settings), **G** guided steps. Every fix ends in G, so every fix has a path when automation is blocked (Advanced
Protection, the service not enabled, a tile not found).

| Intent | Example complaint | Cause checked → fix (rungs, risk) |
| --- | --- | --- |
| `no_internet` | "Internet not working" | airplane mode on → `airplane_off` (A, low) · offline with mobile data off → `mobile_data_on` (A, low) · offline with Wi-Fi off → `wifi_on` (A, low) · data saver on → `data_saver_off` (A, low) |
| `wifi_no_load` | "Wi-Fi connected but nothing loads" | automatic time off → `auto_time_on` (A, low) · Private DNS set to a hostname → `private_dns_off` (P, medium) · otherwise G: forget and rejoin the network (medium) |
| `phone_not_ringing` | "Phone doesn't ring" | DND on → `dnd_off` (D on API ≤ 34, A, low) · ringer silent or vibrate → `ringer_normal` (D, low) · ring volume 0 → `ring_volume_up` (D, low) |
| `cant_hear_call` | "Can't hear the person on the call" | call volume low → `call_volume_up` (D, low) · Bluetooth audio connected → G: switch the audio output |
| `notifications_missing` | "WhatsApp messages come late" | DND on → `dnd_off` · data saver on → `data_saver_off` · otherwise G: battery optimisation for the app |
| `talkback_on` | "Phone is talking to me, I have to tap twice" | TalkBack on → `talkback_off` (A in Settings, **spike**; G: volume-key shortcut; medium) |
| `colours_wrong` | "Screen went black and white" | colour inversion on → `inversion_off` (A, low) · greyscale on → G |
| `screen_too_dim` | "Screen is too dark" | brightness low → `brightness_up` (D, low) |
| `screen_turns_off_fast` | "Screen goes off too quickly" | timeout under 30 s → `timeout_longer` (D, low) |
| `screen_wont_rotate` | "Screen won't turn sideways" | rotation locked → `rotation_unlock` (D, A, low) |
| `text_too_small` | "Letters are too small" | font scale at or below default → `font_size_settings` (P display settings, low; verified when the scale goes up) |
| `bluetooth_earphones` | "Earphones won't connect" | Bluetooth off → `bluetooth_on` (A, low) · otherwise G: re-pair (medium) |
| `app_permission` | "Camera doesn't work in an app" | G only. Fixing this needs to know which app, which is a Noul question for the model, not a keyword rule |
| `wrong_time` | "Apps say there's a time error" | automatic time off → `auto_time_on` (A, low) |
| `reset_network` | "Nothing works, reset the network" | `reset_network` (G only, **high**). Destructive fixes are never automated (invariant 3); this intent exists so the gate's high-risk branch is exercised |

If no cause holds, the result is the intent's guide card: "Everything Unstuk can check looks fine. Try …".

`app_permission` and `reset_network` have no automated path at all in M2. They stay in the catalog because the
model in M5 must still learn to recognise them, and because M3 needs their phrasings.

## Scope

**In M2**

### Catalog

`catalog/` at the repository root, in JSON. It is the single source of truth (invariant 8): the app reads it now,
and M3's Python code reads the same files with the standard library.

| File | Holds |
| --- | --- |
| `intents.json` | Per intent: `id`, `option` (the plain-language text the model will choose between in M5), and an ordered list of causes, each `{ "check": <check id>, "fix": <fix id> }`, plus a fallback guide card |
| `fixes.json` | Per fix: `id`, `risk` (`low`, `medium`, `high`), the ordered `rungs` it has, and its guide steps |
| `keywords.json` | The keyword matcher's rules, per intent |

- **Checks and fixes are named, not encoded.** The catalog says *which* check and fix apply; Kotlin implements
  each one under that ID, the same way selector files name `SettingTarget`s in M1.
- **Keywords live in their own file**, so training code never mistakes hand-written rules for data. They are
  deleted when the model ships.
- **The app gets the catalog through an AGP variant-API hook** that adds `../catalog` as an assets source
  directory. There is no copy to drift out of date.
- **A unit test enforces the catalog's rules:** IDs are unique; every check and fix the catalog names is
  implemented in Kotlin, and every implementation is named in the catalog; every fix ends in G; a `high` fix has
  only G; every fix ID appears in some intent.
- **IDs are frozen once M3 data uses them.** An `ids.lock` that enforces this is added in M3, when "used" first
  means something.

### Device state

`DeviceState` grows the fields the checks need: ringer mode, ring and call volume, Wi-Fi enabled, mobile data
enabled, validated internet, data saver, automatic time, Private DNS mode, brightness, screen timeout, rotation
lock, font scale, colour inversion, greyscale and Bluetooth enabled. Everything is still read fresh on every call.

`awaitState` currently hard-codes the airplane-mode URI and the DND broadcast. It now observes the whole Global,
System and Secure settings tables, the system broadcasts for DND, ringer, Wi-Fi and data saver, and a 500 ms poll for
state with no signal (mobile data, validated internet). An extra wake-up costs one read; a missed one costs a false
timeout. It keeps M1's rule of subscribing first and reading second.

### Executor

- `AccessibilityRung.switchOff` becomes `toggle(target)`, because several new fixes turn a setting *on*. Tiles and
  switches toggle, and the runner only taps when the fix hasn't taken effect, so no desired value is needed.
- New rungs: `DirectRung` (system APIs, skipped when a grant is missing), `PanelRung` and `GuidedRung`. A
  `FixRunner` walks a fix's rungs in catalog order. `verifyOff` becomes a check against the *desired* state, and
  remains the final word on success.
- **P-rung verification.** The app opens the screen and waits until the predicate holds, until the user comes back
  to Unstuk, or for 2 minutes, whichever comes first. A fresh read then decides. If the state hasn't changed, the
  result is `NeedsGuidance`, never success (invariant 2).
- `UnstukAction` gives way to catalog fix IDs, and the trial receiver and `trials.sh` take a fix ID.
- Selector files gain tiles and Settings paths for inversion, mobile data, Wi-Fi, Bluetooth, auto-rotate, data
  saver and automatic time, on both `pixel.json` and `motorola.json` (invariant 6).

### Diagnosis

`Diagnoser` walks an intent's causes in order against a fresh snapshot and returns the first fix whose check holds.
After a verified fix, it runs once more and offers the next cause if one still holds, for example when airplane
mode is now off but mobile data is still off.

### Keyword matcher and risk gate

The matcher returns an `IntentChoice`: a probability per intent ID, computed as hitsᵢ / Σ hits over the matched
keywords, plus the top pick. This is the same shape as a Choice answer from the model, so the gate doesn't change
in M7. These probabilities aren't calibrated; they only stand in for the model's probabilities until M6.

| Condition | Result |
| --- | --- |
| No keyword matches | Polite decline that lists what Unstuk can help with |
| Top probability < 0.5 | Clarifying question: a Choice between the top intents' option texts |
| Fix is high risk | Guided steps only |
| Fix is medium risk, or low risk with top probability < 0.8 | Ask the user to confirm, then run |
| Fix is low risk and top probability ≥ 0.8 | Run automatically |

The threshold of 0.8 is a placeholder; M6 tunes it on calibrated probabilities. Diagnosis runs before the last
three rows, because the risk tier comes from the fix it picks.

The matcher's unit tests use complaints we write ourselves, labelled as test fixtures and kept out of `data/`, so
they never mix with real user messages or seed phrasings (invariant 9).

### UI and permissions

- **Complaint screen:** a text field, then one result card: the fix is done, a confirmation dialog, a guide card,
  a clarifying choice or a decline.
- **Setup screen:** the grants each rung needs (the accessibility service, notification-policy access,
  `WRITE_SETTINGS`), each with a button to the right Settings screen. A missing grant only
  skips the rungs that need it.
- The M1 debug screen stays.
- New manifest permissions: `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE` and `WRITE_SETTINGS`. There is still no
  `INTERNET` permission (invariant 4).

### TalkBack-off spike

The path is Settings → Accessibility → TalkBack, then the switch, then a check that TalkBack has left the
enabled-services list. The question is whether our service can still find and click nodes while TalkBack owns
touch input. The guided fallback is the volume-key shortcut, where it is set up. There is no target number; we
record what happens on the Moto.

### Test tooling

- A debug-only complaint receiver (debug source set, invariant 7) that runs the whole pipeline from a complaint
  string and writes a trace line for each stage: the decision, the gate result, the diagnosis, each rung and the
  verification.
- `android/scripts/e2e.sh`: for each intent, set the cause up over adb, send the complaint, and compare the trace's
  outcome with an independent adb read. It reuses `trials.sh`'s habits: it restores airplane mode on exit, waits
  for the service to bind, and never calls `uiautomator dump`.

**Not in M2**
- Any ML, and the `decide()` API (M7). The matcher is a concrete class; the shared interface is extracted when the
  model becomes the second implementation.
- Identifying which app a complaint is about (`app_permission`, per-app battery optimisation).
- Data collection, seed phrasings and `ids.lock` (M3).
- Screenshots in guide cards. Text steps only.
- Onboarding UX for restricted settings beyond the setup screen's buttons.
- The Pixel emulator, except for a fix that can't be checked on the Moto.

## Unverified API assumptions

These are checked first in their step. If one fails, the affected cause falls back to a guided step, and the spec
records the change.

| Assumption | Used by |
| --- | --- |
| `TelephonyManager.isDataEnabled` works with `ACCESS_NETWORK_STATE`, without `READ_PHONE_STATE` | `no_internet` |
| An app targeting API 37 can read `private_dns_mode`, `accessibility_display_inversion_enabled` and the daltonizer settings (hidden keys must be `@Readable` since Android 12) | `wifi_no_load`, `colours_wrong` |
| Writing `SCREEN_BRIGHTNESS`, `SCREEN_OFF_TIMEOUT` and `ACCELEROMETER_ROTATION` with `WRITE_SETTINGS` takes effect at once on the Moto | display fixes |
| Bedtime-mode greyscale shows up in a readable setting | `colours_wrong` |

## Decisions (2026-10-04)

| # | Decision | Chosen |
| --- | --- | --- |
| 1 | New executor work | Accessibility automation for the new toggles as well as the cheap rungs |
| 2 | Catalog format | JSON |
| 3 | TalkBack-off | Automation spike in M2, with guided fallback |
| 4 | Confidence threshold | 0.8 (placeholder, tuned in M6) |

### Rejected alternatives

1. **Cheap rungs only** (direct API, panels and guided steps for new fixes) would have kept M2 to the catalog,
   diagnosis and gate. It was rejected in favour of exercising the full ladder now, while the M1 executor code is
   fresh.
2. **YAML** is easier to write by hand (comments, multi-line guide steps), but it needs a parser on both sides or a
   conversion step. **TOML** handles nested playbook lists awkwardly.
3. **Generating Kotlin from the catalog at build time** gives compile-time IDs, but adds a code generator. A
   runtime asset load is simpler, and M7 needs option texts at runtime anyway. The consistency test catches
   mismatches instead.
4. **A `Decider` interface now** would have only one implementation, and its shape would be a guess before the
   model exists.
5. **A tier per intent**, as in the plan's table. It can't express one complaint whose fixes differ in risk.

## Steps

One commit each, or a few where a step is large.

1. This spec.
2. Catalog files, loader and consistency test.
3. Device state fields and generalised `awaitState`.
4. Executor ladder: `toggle`, the new rungs, `FixRunner`, and selectors for the new targets.
5. `Diagnoser`.
6. Keyword matcher and risk gate.
7. Complaint screen and setup screen.
8. Debug complaint receiver and `e2e.sh`.
9. TalkBack-off spike.
10. `m2-results.md` and a plain-language summary.
