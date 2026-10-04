# M1 spec: Executor spike

2026-10-03 · Status: **ready**. Decisions are settled; implementation starts once the environment below is installed

M1 answers one question: **can a normal third-party app reliably undo an accidental phone state, and prove that it
did?** It is done when a host-side trial runner switches airplane mode and Do Not Disturb off through the app on
both test targets, and each action meets its success target with zero false successes.

Background: [plan.md](plan.md), roadmap step 1. This comes first because it is the riskiest part of the project
and has no ML in it. If the executor can't act, the model has nothing to drive.

## What changed from the plan

The plan listed DND as a direct-API action. That is no longer true. For apps targeting Android 15+,
`setInterruptionFilter` only switches the app's own implicit `AutomaticZenRule` and cannot turn off DND that the
user or bedtime mode turned on ([behaviour changes](https://developer.android.com/about/versions/15/behavior-changes-15)).
On Android 15+, DND therefore moves to the accessibility rung, beside airplane mode.

The restriction depends on the Android version the phone runs, not only on our targetSdk. The test phone, a Moto
Edge 30, stopped at Android 14 (API 34), so the direct DND call still works there. The `DndOff` playbook picks its
rung from `Build.VERSION.SDK_INT`: on API ≤ 34 it calls `setInterruptionFilter` with notification policy access, and
on API ≥ 35 it uses Quick Settings automation. As a result, the two targets cover both rungs.

## Targets

| Metric | Target | Meaning |
| --- | --- | --- |
| Success, Pixel emulator (latest stable image) | ≥ 95% per action | State verified as changed, out of 20 trials per action |
| Success, Moto Edge 30 (Android 14) | ≥ 90% per action | Same, on Motorola's skin |
| False success | 0 | The app reported success, but a fresh state read disagrees |
| Time to verified result | median < 5 s | From the trigger to a verified state |

With 20 trials, 19/20 has a 95% Wilson interval of about 76–99%. The report shows counts and intervals and claims
nothing beyond them.

## Scope

**In M1**
- `android/`: a single-module Kotlin and Compose app, created from Android Studio's Empty Activity template.
  Application id `com.rishikeshvk.unstuk`, minSdk 29 (Android 10), targetSdk the current stable SDK.
- **State reader.** A typed `DeviceState` snapshot with only the fields M1 needs: airplane mode
  (`Settings.Global.AIRPLANE_MODE_ON`), current interruption filter, enabled accessibility services (including
  TalkBack), Advanced Protection (`AdvancedProtectionManager`, behind an API-level check), and make, model, SDK
  and build.
- **Accessibility service.** Minimal config: window content retrieval and view-id reporting, and only the event
  types the actions need. It does not set the `isAccessibilityTool` flag, because Unstuk is not one, and the
  Advanced Protection fallback depends on being honest about that.
- **Two actions, `AirplaneModeOff` and `DndOff`.** On API ≥ 35 each one is the sequence of steps below. `DndOff` on
  API ≤ 34 runs only steps 1 and 5, around the direct call.
  1. Check the precondition with a fresh state read. If the state is already off, report "nothing to do".
  2. Open Quick Settings (`GLOBAL_ACTION_QUICK_SETTINGS`).
  3. Find the tile: resource-id first, then the label variants from the OEM selector file. If the tile isn't on
     the first page, swipe through the remaining pages.
  4. Click the tile and wait for the state change, with a timeout.
  5. Verify the result with a fresh state read, then close the shade.
  6. If the tile isn't found, open the Settings screen (airplane mode, or Modes/DND) and click the switch there.
     This is still the accessibility rung, because the service taps (invariant 5). If that also fails, return a
     `NeedsGuidance` result. M1 shows a text placeholder; real guide cards come in M2.
- **Selectors as data:** `android/app/src/main/assets/selectors/{pixel,motorola}.json`.
- **Trace.** Each step is written as a JSON line with its timestamp, the strategy that found the node, and the
  outcome, to app-private storage. There is no network.
- **Debug screen.** It shows the live `DeviceState`, has one button per action, and lists the last trace.
- **Trial runner** (`android/scripts/trials.sh`). Over adb, it sets the starting state
  (`cmd connectivity airplane-mode enable`, `cmd notification set_dnd on`), varies the starting condition, triggers
  the action through a debug-only receiver, and reads the trace with `run-as`. It then prints counts, intervals
  and median time per action and per device.
  - Starting conditions: home screen, another app in the foreground, shade already open. A few manual trials also
    cover the tile moved off page one, and a locked device (the expected result is "needs unlock", not a tap
    behind the keyguard).
  - The receiver lives in the `debug` source set, so it cannot exist in a release build (invariant 7).

**Not in M1**
- Any ML, the catalog and intents, and the risk gate (M2).
- Colour inversion and the other accidental modes.
- Onboarding UX for restricted settings. In M1, the service is enabled by hand or with
  `adb shell settings put secure enabled_accessibility_services ...`.
- Settings Panels for Wi-Fi and Bluetooth (M2, with the catalog).
- Release builds and signing.

## Stretch goal: `TalkBackOff`

TalkBack is the plan's most panic-inducing case. The question is whether our service can still find and act on
nodes while TalkBack owns touch input. Path: Settings → Accessibility → TalkBack, then the switch, then verify that
TalkBack has left the enabled-services list. The guided fallback is the volume-key shortcut (hold both volume keys
for 3 s), but only where the shortcut is set up. The stretch goal has no target number; we record what happens on
both targets.

## Decisions (2026-10-03)

| # | Decision | Chosen |
| --- | --- | --- |
| 1 | Physical test phone | Moto Edge 30, Android 14 (API 34, its final OS update) |
| 2 | targetSdk | Current stable SDK; DND automation on Android 15+ |
| 3 | TalkBack-off | Stretch goal in M1 |
| 4 | minSdk | 29 (Android 10) |

The Moto skin (My UX) is close to stock Android, so M1 says little about heavier skins like One UI or HyperOS. That
gap is accepted for now; the M8 field test on test users' phones is where it gets measured.

### Original options

1. **Physical test phone.** Samsung One UI or Xiaomi HyperOS, and which Android version?
2. **targetSdk.** *Recommended: current SDK.* DND then has to go through automation, which matches what any shipped
   app faces. The rejected alternative is targeting API 34, which keeps the old direct DND API for a sideloaded MVP
   but builds on a loophole that closes the moment a Play release is considered.
3. **TalkBack-off as a stretch goal?** *Recommended: yes.* It is the plan's most panic-inducing case, and the
   spike is the right place to learn whether our service can act while TalkBack owns touch input.
4. **minSdk.** *Recommended: 29 (Android 10)*, which is the first version with Settings Panels. It may need to go
   lower if a test user's phone is older, so it depends on the oldest phone in the field test.

## Environment setup (before any code)

Checked 2026-10-04. The machine has an i5-8250U (4 cores, 8 threads), 7.6 GB of RAM, 4 GB of swap, an SSD with
about 60 GB free, KVM, and X11. Android Studio fits, but the IDE, Gradle and an emulator together need about
9–10 GB, so they never run at the same time.
- **Daily development:** Android Studio and the Moto Edge 30 over USB. Studio's heap stays at its 2 GB default
  (*Help → Change Memory Settings*), and the project's `gradle.properties` sets `org.gradle.jvmargs=-Xmx2g`.
- **Trial runs:** Studio closed, and the emulator started headless (`emulator -avd <name> -no-window`) for
  `trials.sh`. One AVD: a recent Pixel image with Google APIs, not Play Store, so `adb root` works, and 2 GB of RAM.
- **Fallback:** if Studio is too slow, use the command-line SDK tools and Gradle with a lighter editor. Studio is
  still used once to generate the project from the Empty Activity template.

Setup steps:
1. Install Android Studio (`android-studio` from the AUR; it bundles its own JDK) and let it install the SDK.
2. Install `android-udev` so adb can reach the phone, and turn on USB debugging on the phone.
3. Check that `adb devices` lists the Moto, then create the AVD.

## Milestones after M1

These follow the plan's roadmap. Each one gets its own spec when it starts.

| M | Step | Done when |
| --- | --- | --- |
| M2 | Catalog + rules | 15 intents, playbooks and risk tiers; a keyword matcher drives the app end to end |
| M3 | Data | Seed phrasings, synthetic set and real user test set exist; held-out intents chosen |
| M4 | Baseline | fastText and frozen bge-small + LR scored on the real set: the bar |
| M5 | Encoder + heads | Choice / Noul / Score heads trained on Colab; fixed-head baseline alongside |
| M6 | Compress + calibrate | Brier/proper-scoring loss, temperature scaling, int8; ECE reported after quantization |
| M7 | On-device inference | Kotlin `decide(state, questions)` on ONNX Runtime or LiteRT; node matching through it |
| M8 | Field test | Installed on test users' phones; MVP metrics measured |
| M9 | Write-up | Size waterfall, calibration plots, baseline comparison, failure analysis |
