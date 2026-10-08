# M7 in plain words: the model moves onto the phone

2026-10-08 · Summary of the seventh phase. The detailed numbers are in [m7-results.md](m7-results.md).

## The question we set out to answer

Until now the model lived on a laptop, and the app guessed with a list of keywords. M7 put the real model inside
the app. That meant shrinking it to fit, rewriting the part that turns words into numbers in the phone's own
language, and checking that the phone gives the same answers as the laptop.

## What we found

- **It fits and it's fast.** The model shrank from 134 MB to **35 MB** by storing each number in one byte instead
  of four. It loads in under half a second and answers in about **10 milliseconds**.
- **Shrinking it didn't make it worse.** On the test it picks the right problem 89.3% of the time (89.5% before),
  and it is confidently wrong just as rarely: 3.0%.
- **The phone agrees with the laptop.** On all 1,144 practice messages, the phone picked the same answer as the
  laptop.
- **The app is 71 MB.** That's inside the 100 MB limit we set, but above the 40–60 MB we hoped for. Half of it is
  the engine that runs the model, not the model.
- **In a full run on the phone,** 14 of 17 scripted complaints ended as expected, and no fix ever claimed success
  without being checked. The three misses were cases written for the old keyword list, plus one real mistake:
  the model thought "Camera not working in Zoom" wasn't something it could help with.

## Things we learned

- **Test the model the way the app uses it.** Our first check fed the laptop 64 messages at a time, while the
  phone reads one. The shrunken model's answers depended on its neighbours, so the first check passed a version
  that didn't really pass.
- **Different chips do maths slightly differently.** The laptop's chip rounded some sums differently from the
  phone's. A small change to how the numbers are stored made both exact.
- **Checking on the real phone catches what the laptop can't.** Both problems showed up only when the phone's
  answers were compared with the laptop's, line by line.
- **Small practice sets make jumpy settings.** Re-tuning the app's "how sure before acting" lines on the
  shrunken model moved them on just three messages, so we kept the old lines.
