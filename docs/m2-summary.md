# M2 in plain words: from a complaint to a checked fix

2026-10-04 · Summary of the second phase. The detailed numbers are in [m2-results.md](m2-results.md).

## The question we set out to answer

In M1, Unstuk could switch off two settings when told exactly which one. M2 asked: if someone just types what's
wrong, in their own words, can the app work out what they mean, look at the phone, pick the right fix, apply it
safely and check that it worked?

There is no AI model yet. A simple keyword list stands in for it, so that every other part of the app gets built
and tested first. On the Moto Edge 30 the answer is **yes**.

## What you can see it do today

Open the app and you get three tabs:

- **Help:** type a complaint, such as "Phone doesn't ring" or "Screen is too dark", and tap **Help me**.
- **Setup:** shows which permissions Unstuk has and gives a button for each one that is missing.
- **Debug:** the phone's state and a button per fix, as in M1.

After **Help me**, Unstuk answers with one card:

- **"Done: … I checked, and it worked."** It found the cause, fixed it and confirmed the fix on the phone.
- **"I can … for you. Shall I?"** When it isn't sure enough, or the fix is a bigger change (like turning off
  TalkBack), it asks first.
- **"Which of these is closest?"** When the words fit more than one problem, it offers the likely ones as buttons.
- **"Here's how to …"** with numbered steps. For risky changes (resetting network settings) it only ever explains,
  and the same happens when it can't do a fix itself. A button opens the right Settings screen.
- **"Everything I can check looks fine,"** with tips, when nothing it can check is wrong.
- **"Sorry, I can't help with that yet,"** with a list of what it can help with, when the complaint isn't about
  anything it knows.

## What it can fix

Fifteen kinds of problem, from "internet not working" to "letters too small". Behind them are 20 fixes, and each
one is done in the least intrusive way that works:

1. **Ask Android directly** when the phone allows it: brightness, screen timeout, rotation, ringer and volumes.
   This takes a fraction of a second.
2. **Open the right Settings screen and let the person tap**, when there's nothing safer: text size, automatic time
   and Private DNS.
3. **Tap the switch for the person**, in the pull-down Quick Settings panel or in Settings: airplane mode, mobile
   data, Wi-Fi, Bluetooth, Data Saver, colour inversion and TalkBack.
4. **Show step-by-step instructions** when none of those is possible.

## How we know it works

A test script on the computer breaks a setting on the phone, types a complaint into Unstuk, and then checks the
phone itself to see whether Unstuk told the truth.

- **20 out of 20 scripted complaints** got the right answer. They cover all 15 problems and every kind of reply.
- **Every switch Unstuk taps for the person worked 10 times out of 10**: mobile data, Wi-Fi, Bluetooth, Data Saver,
  colour inversion, auto-rotate and TalkBack.
- **It never claimed a fix that hadn't happened.**

## Two things we learned

- **Unstuk can turn TalkBack off** even while TalkBack is running and changing how the screen responds to touch.
  That is the most panic-inducing case in the plan, and it works.
- **Android hides some Settings switches from apps like Unstuk.** It could see every row on the Date & time screen
  except the "Set time automatically" switch itself. Rather than pretend to be an accessibility tool (it isn't), Unstuk
  opens that screen and asks the person to tap.

## What comes next

M3 builds the data: example complaints, a large set of practice phrasings, and a set of real messages from test users
(with consent) to measure against. Those are what the real model will learn from, replacing the keyword list.
