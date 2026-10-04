# M2 results: Catalog + rules

2026-10-04 · Status: **Moto target met.** Spec: [m2-spec.md](m2-spec.md). Plain-language summary:
[m2-summary.md](m2-summary.md)

M2 asked whether the whole pipeline, from a typed complaint to a verified fix, runs end to end with plain rules in
place of the model. On the Moto Edge 30 (Android 14) it does: all 15 intents and all five gate branches reach their
expected reply, every new accessibility rung verified 10 out of 10, and there were no false successes.

## End to end, Moto Edge 30 (Android 14, API 34), final build

Run with `android/scripts/e2e.sh`. Each case breaks one setting over adb, sends a scripted complaint through the
debug receiver (which stands in for the user's confirm and clarify taps), and compares the last reply with the
expected one. A "verified" reply must also pass an independent adb read.

| Case | Intent | Fix and rung | Reply | Host read | Time |
| --- | --- | --- | --- | --- | --- |
| no_internet_airplane | `no_internet` | `airplane_off`, A | verified | agrees | 1.43 s |
| no_internet_data | `no_internet` | `mobile_data_on`, A | verified | agrees | 0.48 s |
| wifi_no_load | `wifi_no_load` | `auto_time_on`, P (simulated tap) | verified | agrees | 2.97 s |
| not_ringing_dnd | `phone_not_ringing` | `dnd_off`, D | verified | agrees | 56 ms |
| not_ringing_ringer | `phone_not_ringing` | `ringer_normal`, D | verified | agrees | 139 ms |
| cant_hear_call | `cant_hear_call` | `call_volume_up`, D | verified | agrees | 47 ms |
| notifications_data_saver | `notifications_missing` | `data_saver_off`, A | verified | agrees | 2.51 s |
| talkback_on | `talkback_on` | `talkback_off`, A after confirm (medium) | verified | agrees | 1.14 s |
| colours_wrong | `colours_wrong` | `inversion_off`, A | verified | agrees | 3.49 s |
| screen_too_dim | `screen_too_dim` | `brightness_up`, D | verified | agrees | 69 ms |
| screen_off_fast | `screen_turns_off_fast` | `timeout_longer`, D | verified | agrees | 26 ms |
| wont_rotate | `screen_wont_rotate` | `rotation_unlock`, D | verified | agrees | 25 ms |
| text_too_small | `text_too_small` | `font_size_settings`, P (simulated tap) | verified | agrees | 3.03 s |
| bluetooth | `bluetooth_earphones` | `bluetooth_on`, A | verified | agrees | 0.41 s |
| app_permission | `app_permission` | none (no causes) | all_clear | — | 6 ms |
| wrong_time | `wrong_time` | `auto_time_on`, P (simulated tap) | verified | agrees | 2.93 s |
| reset_network | `reset_network` | `reset_network`, high risk | guide | — | 5 ms |
| gate_confirm | `wrong_time` at p = 0.67 | `auto_time_on`, low risk below 0.8 | confirm | — | 10 ms |
| gate_clarify | three-way tie at p = 0.33 | — | clarify | — | 7 ms |
| gate_decline | nothing matched | — | decline | — | 6 ms |

**20/20 passed, 0 false successes.** All five gate branches occur: automatic (most rows), confirm, guided only
(`reset_network`), clarify and decline. P-rung times include the script's 3 s wait before its simulated tap.

The Help tab was also checked by hand on the phone: "Dark colours and small" produced the clarifying question, and
picking "The screen is too dark" ran `brightness_up` and showed "Done … I checked, and it worked."

## New accessibility rungs, 10 trials each

Run with `android/scripts/trials.sh 10 <fix>`, using M1's method: starting conditions rotate between the home screen,
another app and the shade already open, and an independent adb read checks every verdict.

| Fix | Path on the Moto | Verified | 95% Wilson | False successes | Median |
| --- | --- | --- | --- | --- | --- |
| `mobile_data_on` | Mobile data tile, page 1 | 10/10 | 72–100% | 0 | 0.46 s |
| `wifi_on` | Wi-Fi tile, page 1 | 10/10 | 72–100% | 0 | 0.96 s |
| `bluetooth_on` | Bluetooth tile, page 1 | 10/10 | 72–100% | 0 | 2.05 s |
| `data_saver_off` | Data Saver tile, page 3 | 10/10 | 72–100% | 0 | 2.50 s |
| `inversion_off` | Colour inversion tile, page 4 | 10/10 | 72–100% | 0 | 3.53 s |
| `rotation_unlock` | Auto-rotate tile, page 1 (WRITE_SETTINGS revoked, so D skipped) | 10/10 | 72–100% | 0 | 0.45 s |
| `talkback_off` | Settings → Accessibility → TalkBack → Use TalkBack → Stop | 10/10 | 72–100% | 0 | 1.10 s |

`data_saver_off` and `inversion_off` ran on a build before the last two rung fixes below. Those fixes change only
what happens after a rejected click or when a fix has no tile, and neither happened in those 20 trials. The
`rotation_unlock` run used a one-off script, because `trials.sh` always grants WRITE_SETTINGS; every trace shows
`rung_direct: needs_guidance` and then `rung_accessibility: verified`, so the ladder fell through as designed.

As the spec warned, ten trials is a smoke test: 10/10 has a 95% Wilson interval of 72–100%.

## TalkBack-off spike

**Our service can turn TalkBack off while TalkBack owns touch input.** It went 10/10 in trials plus the e2e case,
median 1.1 s, through Settings → Accessibility → TalkBack, the "Use TalkBack" switch (found by its `switch_text` view
id) and the "Stop" button in the confirmation dialog. `performAction(ACTION_CLICK)` doesn't go through touch, so
TalkBack's double-tap model doesn't get in the way.

One finding for the guided fallback: the TalkBack shortcut (hold both volume keys) is **off** on this phone, so the
first guided step would do nothing here. The guide card offers the Settings path as its second step.

## Unverified API assumptions, checked

| Assumption | Result on the Moto (API 34, app targeting 37) |
| --- | --- |
| `TelephonyManager.isDataEnabled` works with `ACCESS_NETWORK_STATE` alone | Yes |
| Hidden settings `private_dns_mode`, `accessibility_display_inversion_enabled` and the daltonizer keys are readable | Yes, no `SecurityException`. An unset `private_dns_mode` reads null and now means the platform default, "opportunistic" |
| `WRITE_SETTINGS` writes to brightness, timeout and rotation take effect at once | Yes (21–69 ms to a verified read) |
| Bedtime-mode greyscale shows up in a readable setting | **Not checked.** On the Moto it is a Digital Wellbeing tile, not the daltonizer, so `greyscale_on` probably misses it; the `colours_wrong` fallback card covers it |

These hold on API 34. The `@Readable` question matters most on Android 15+, which the Pixel run would cover.

## What changed from the spec

| Change | Why |
| --- | --- |
| `auto_time_on` moved from A to P | Our service sees every row of Date & time except the "Set time automatically" switch. A test pointing the same path at the "Date" row found and clicked it. This is M1's hidden-switch finding again, now confirmed on the Moto too. With no working automation, the user taps (allowed by the ladder decision) |
| No P rung on a fix that has an A rung | Decided while implementing (recorded in the spec); keeps invariant 5 as written |
| No `BLUETOOTH_CONNECT` | `Settings.Global.BLUETOOTH_ON` is readable without it |
| `awaitState` watches whole settings tables plus a 500 ms poll | Simpler than per-predicate keys; an extra wake-up costs one read |

## Bugs found and fixed during M2

| Bug | Symptom | Fix |
| --- | --- | --- |
| Stale header tile | Wi-Fi and Mobile data also appear in the collapsed header. Opened from a closed shade, the finder sometimes returned the header's copy, which rejected every click (6 of 20 trials) | After a rejection, look the tile up again and retry, up to three attempts (`AccessibilityRung.kt`) |
| Retry could toggle back | One Bluetooth trial: a "rejected" click seems to have landed, and the retry switched Bluetooth off again | After a rejection, wait up to 1.5 s for the state to change before retrying |
| Shade covering Settings | TalkBack has no tile, so its rung opened Settings with the shade still open on top (3 of 10 trials) | Close the shade before the Settings path |
| Matcher matched nothing | Phrases were padded twice | Caught by unit tests before any device run |

All of these failed safe: the reply was guided steps or `failed`, never `verified`.

## Test tooling lessons

- **The shell's volume command is ignored on the Moto.** `cmd media_session volume --set` reports success and changes
  nothing. A debug-only `AudioSetupReceiver` lets the app break audio state instead, which also shows an app can set
  ring volume, call volume and vibrate mode. Silent falls back to vibrate.
- **`mode_ringer` lags.** It is persisted about a second after the ringer mode changes, while `AudioManager` is right
  at once. The host check first flagged a FALSE_SUCCESS that wasn't one. Host checks now allow 3 s to settle.
- **Mobile data is stored per SIM** (`mobile_data1`), so the first host check read the wrong key and never changed.
- **Data Saver stops USB tethering**, which re-enumerates USB and drops adb for a second or two. Every script adb call
  now waits for the device.
- **`am broadcast` blocks until the receiver finishes**, so a P-rung case never got its simulated tap, and the
  receiver hit the background-broadcast timeout. The e2e script now sends the broadcast in the background.
- **The first restore switched Wi-Fi and Bluetooth on**, though both started off. Radios are now restored to how they
  were found.

## Not done in M2

- **Pixel emulator:** not run (the minimize-emulator rule). Pixel selectors for the new tiles, the Internet-tile
  dialog and the TalkBack path are still first guesses from AOSP. On Android 15+ DND also moves to the A rung there.
- **Panel rung with a real user:** P cases used a simulated tap. Waiting for the user to come back to Unstuk (the
  process-lifecycle signal) was not exercised by the scripts; the hand test only covered a D fix.
- **D rungs in repeated trials:** each D fix ran once in e2e (M1 already has 20/20 for `dnd_off`).
- **Greyscale through Bedtime mode** (above).
