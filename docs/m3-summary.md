# M3 in plain words: the data, and the bar a model must clear

2026-10-05 · Summary of the third phase. The detailed numbers are in [m3-results.md](m3-results.md).

## The question we set out to answer

M2 showed that Unstuk can go from a typed complaint to a checked fix, with a simple keyword list deciding what the
person meant. M3 asked: can we build the examples a small AI model would learn from, and a fair test that shows
whether such a model is actually better than the keyword list?

The answer is yes, and the test has already given its first verdict: the keyword list is not good enough.

## What we built

- **A rulebook for labels.** Before writing any examples, we wrote down what each problem means, with rules for the
  look-alikes ("Wi-Fi connected but nothing loads" is a different problem from "no internet").
- **A locked test of 602 complaints**, written by ChatGPT, Gemini and a fresh Claude that knew nothing about the
  project. It includes deliberately hard kinds: typos, Indian English, complaints that avoid the obvious words, and
  messages that use our words with another meaning ("my ring finger hurts"). It was locked before any training
  examples existed, so nothing could be tuned to it.
- **About 7,000 training examples**, each batch written in the voice of a different kind of person (a teenager, a
  worried 70-year-old, someone dictating without punctuation), plus examples Unstuk must say no to, and pairs of
  near-identical sentences that fall on different sides of a line.
- **A cleaning step** that removed repeats, removed anything too close to the test, and had an independent checker
  re-label samples blind. It agreed with all 200 lines it checked.
- **Two smaller sets** for later: complaints where only the phone's settings can tell the problem apart, and
  questions for finding the right switch on a phone's screen.

## The verdict on the keyword list

On the locked test, the keyword list picks the right problem only **40%** of the time. It fails most on exactly the
complaints real people write: about **one in four** right when someone avoids the obvious word or makes typos.

Worse, it is often **sure and wrong**. One matching word makes it 100% sure, so for about **one complaint in eleven**
it would change a setting automatically for the wrong problem. Its confidence means nothing, which matters because
Unstuk decides whether to act alone or ask first based on that confidence.

That is the answer to "why a model?" in numbers. A model has to beat these scores on the same test, especially the
sure-and-wrong rate, or the simpler keyword list stays.

## Things we learned

- **The person who has seen the test must not write the training data.** Every training example was written by a
  fresh assistant that saw nothing of the test.
- **Try a small batch first.** The first two batches copied our own definitions' wording; one changed sentence in
  the instructions fixed it for the other 38.
- **A perfect score can be a warning.** The checker agreed with every training example, which means they are clear
  and easy. Real complaints are messier, which is why the test has hard parts.
- **Our own rulebook hides some real ambiguity.** "Wi-Fi not working" is always labelled "no internet", but the phone
  itself might show a different cause. A later phase will decide whether to change that rule.

## What is left for M3

One sitting with the phone on a computer: build and install the app, run its tests, and record the labels on the
phone's own settings screens. Those screens become the test for "find the right switch".
