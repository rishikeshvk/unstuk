# M1 in plain words: what Unstuk can do now

2026-10-04 · Summary of the first phase. The detailed numbers are in [m1-results.md](m1-results.md).

## The question we set out to answer

Can an ordinary app, one you install yourself without any special system powers, fix a phone setting that someone
switched on by accident, and then prove that the fix really worked?

For the Moto Edge 30 the answer is **yes**.

## What you can see it do today

Install the debug build on the Moto, switch on the Unstuk accessibility service, and open the app. You get a
simple screen that shows:

- **The phone's current state:** whether airplane mode is on, whether Do Not Disturb is on, whether the phone is
  locked, whether TalkBack is on, the phone model and its Android version.
- **Whether Unstuk's helper service is connected.**
- **Two buttons, "airplane_off" and "dnd_off".**
- **A step-by-step log of the last fix**, with how long each step took.

Press **airplane_off** while airplane mode is on, and you watch the app do what a person would do:

1. It pulls down the Quick Settings panel.
2. It swipes to the page that has the airplane tile.
3. It taps the tile.
4. It closes the panel.
5. It checks the phone's real state, and only then says "verified".

All of this takes about a second and a half.

Press **dnd_off** while Do Not Disturb is on, and it switches off in a fraction of a second. On this phone the app
can ask Android directly, so no tapping is needed.

## What it does when it can't fix something

This matters as much as the fixes:

- **The phone is locked:** it does nothing and says it needs the phone unlocked. It never taps behind the lock
  screen.
- **The setting is already off:** it says there is nothing to do.
- **It can't find the switch:** it says the person needs guidance instead of pretending. In M2 that answer becomes
  step-by-step help on screen.
- **It never claims success unless a fresh check of the phone agrees.** In 40 formal trials and many more test runs,
  it never once said "fixed" when the setting was still on.

## How we know it works

A test script on the computer drives the phone over USB. For each trial it:

1. Switches the setting on.
2. Puts the phone in a different starting position: home screen, another app open, or the notification panel
   already pulled down.
3. Asks Unstuk to fix it.
4. Checks the phone itself to see whether Unstuk told the truth.

| Fix | Result on the Moto Edge 30 | Typical time |
| --- | --- | --- |
| Turn off Do Not Disturb | 20 out of 20 fixed, 0 false claims | 0.02 seconds |
| Turn off airplane mode | 20 out of 20 fixed, 0 false claims | 1.3 seconds |

The target was at least 18 out of 20 and under 5 seconds, so both fixes pass.

## What we learned

- **Every phone brand lays things out differently.** On the Moto, the airplane tile is on page 2 of the Quick
  Settings panel and Do Not Disturb is on page 3. The names differ too: "Aeroplane mode" on the Moto, "Airplane
  mode" on a Pixel. We keep these differences in small data files, one per brand, not in the code.
- **Newer Android hides some switches from apps like ours.** On Android 17, the airplane-mode switch inside
  Settings is invisible to Unstuk, though the Quick Settings tile still works. On newer phones, step-by-step
  guidance will matter more.
- **Careful checking catches real bugs.** We found and fixed four, including one where the app tapped correctly
  but didn't notice the change. Each time, the app reported a failure rather than a false success, which is the
  safety rule doing its job.

## What isn't done yet

- **The Pixel (Android 17) test wasn't completed.** The Pixel emulator is too heavy for this computer and froze.
  It needs a real Android 15+ phone or a faster machine.
- **Turning off TalkBack** (the screen reader that makes a phone "talk") was an optional extra and hasn't been
  started.
- **The app is a test tool, not something a real user can pick up yet.** There's no complaint box, no friendly
  screens and no guidance cards. Those start in M2.

## What comes next

M2 builds the catalogue of about 15 common problems ("phone doesn't ring", "internet not working"), what to check
for each and how risky each fix is. A simple keyword matcher will then connect a typed complaint to the right fix,
end to end, before any machine learning is added.
