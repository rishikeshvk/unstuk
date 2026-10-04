# M1 results: Executor spike

2026-10-04 · Status: **Moto target met; Pixel emulator target not measured.** Spec: [m1-spec.md](m1-spec.md)

M1 asked whether a normal third-party app can reliably undo an accidental phone state and prove that it did. On the
Moto Edge 30 (Android 14) the answer is yes for both actions, with no false successes. On the Pixel emulator
(Android 17), the executor worked in development runs, but the formal 20-trial run could not be done: the emulator
does not run SystemUI reliably on this machine.

## Moto Edge 30 (Android 14, API 34), final build

Run with `android/scripts/trials.sh 20 <action>`. Starting conditions rotate between the home screen, another app in
the foreground and the notification shade open. DND alternates between priority-only and total silence. After every
trial, an independent adb read checks the trace's verdict.

| Action | Rung | Verified | 95% Wilson | False successes | Median time | Range |
| --- | --- | --- | --- | --- | --- | --- |
| `dnd_off` | Direct API (`setInterruptionFilter`) | 20/20 | 84–100% | 0 | 19 ms | 12–30 ms |
| `airplane_off` | Quick Settings tile, page 2 of 4 | 20/20 | 84–100% | 0 | 1.34 s | 1.10–1.37 s |

Targets: ≥ 90% success, 0 false successes and median < 5 s. All three are met. Times run from the receiver's first
trace event to the `result` line, so they leave out adb and broadcast delivery.

Other rungs, exercised during development on the same device (not formal runs):

| Path | Runs | Result |
| --- | --- | --- |
| `dnd_off` through Quick Settings (policy access revoked), tile on page 3 | 7 | 7 verified, about 2.3 s |
| `dnd_off` through the Settings fallback (tile missed) | 10 | 10 verified, about 4–5 s |

## Manual cases

| Case | Device | Result |
| --- | --- | --- |
| Tile not on page one | Moto | Covered by the runs above: airplane mode is on page 2 and DND on page 3 |
| Locked device | Moto | `airplane_off` returned `needs_unlock` in 4 ms and did not tap behind the keyguard |
| Tile removed from Quick Settings | Pixel emulator | Fell through to Settings, then `needs_guidance` (see below) |

## Pixel emulator (Pixel 8, Android 17, API 37)

**Not measured.** The image renders in software (SwANGLE/lavapipe) on a 4-core i5 with 7.6 GB of RAM. In later
sessions the shade often rendered blank, and on the final attempt (machine otherwise idle) SystemUI hit an
"isn't responding" dialog right after boot. Numbers from that state would say more about the host than the executor.

Development runs before the emulator degraded:
- `airplane_off` through the Quick Settings tile: 8/8 verified, about 2.2 s, host read agreeing every time.
- `dnd_off` through the Quick Settings tile: verified when the tile was found. Clicking the tile toggles DND
  directly on API 37.

Findings that hold regardless:
- **Settings switches are hidden from us.** In Settings, our service cannot see the "Airplane mode" switch row or the
  DND mode page's "Turn off" button, while it sees every other row on the same screens. `uiautomator` (privileged)
  sees both. Adding `flagIncludeNotImportantViews` did not help. The likely cause is that Settings marks these
  controls as accessibility-data-sensitive, which only exposes them to services with `isAccessibilityTool`, and
  Unstuk never sets that flag (invariant 11). *Unconfirmed.* The effect is that on stock Android 17 the Settings
  fallback ends in `needs_guidance`, the honest result, so guided steps matter more there.
- Quick Settings tiles have no resource-ids, and their labels sit in the tile's content description
  ("Do Not Disturb. On"). Label matching compares the text before the first `,` or `.`.

## Bugs found and fixed during M1

| Bug | Symptom | Fix |
| --- | --- | --- |
| Read before subscribe | A state change between the first read and the observer registering was never seen, so a working tap timed out | Register observers, then do the first read (`StateChange.kt`) |
| Merged tile labels | The Moto DND tile merges its label into the `Switch` ("Do Not Disturb, Shell"), so tree walks missed the `tile_label` view | When a selector names label ids, look them up by view id (`NodeFinder.kt`) |
| Rewind loop | `return@repeat` continued rather than broke, always making 8 scroll attempts (about 2 s on Pixel) | Bounded `while` loop (`QuickSettings.kt`) |
| Short screen waits | A cold Settings start and the first shade open after a tile change took about 3 s on the emulator | Waits of 6 s and 5 s that return as soon as the node appears |

Every one of these failed safe: the trace said `failed` or `needs_guidance`, never `verified`.

## Testing lessons

- `uiautomator dump` suppresses other accessibility services while it runs, so reading the screen with it during a
  trial disconnects our service. The trial runner only uses `screencap` and `run-as`.
- `cmd statusbar set-tiles` on Android 17 returns at once and applies a few seconds later. `sysui_qs_tiles` written
  with `settings put` is overwritten by SystemUI.
- Re-enabling the accessibility service right after `adb install` can race with package registration. The runner
  waits for the service to bind.
- The Moto is also this machine's internet connection, so airplane trials there cut the host offline. The runner
  switches airplane mode off on exit, whatever happens.

## Not done in M1

- The Pixel 20-trial run (above). It needs a host that can run the API 37 image with hardware rendering, or a
  physical Android 15+ phone, which would also exercise the DND accessibility rung for real.
- Stretch goal `TalkBackOff`.
