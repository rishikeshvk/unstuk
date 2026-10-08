# M5 in plain words: the real model, and what it can't do yet

2026-10-08 · Summary of the fifth phase. The detailed numbers are in [m5-results.md](m5-results.md).

## The question we set out to answer

M4 set a bar: the real model had to beat the best simple model at each thing it did best. M5 built the real model:
the small language model from M4, now trained further on our examples, picking the best match among short
descriptions of each problem ("The phone does not ring when someone calls"). Because it reads descriptions, it
should also recognise a problem it was never trained on, as long as it is given that problem's description.

## What we found

- **It is much better at the problems it was trained on.** It picks the right problem **87%** of the time, against
  74% for the best simple model, and gets better on every awkward kind of message: typos (82%, against 62–69%),
  roundabout wording (85%) and Indian English (89%).
- **Its confidence is honest.** When it says it is 80% sure, it is right about 80% of the time (2.8% calibration
  error, the best yet). It would change a setting automatically for the wrong problem about one time in forty, close
  to the safest simple model's one in fifty.
- **Reading descriptions beats one output per problem.** The same language model trained the usual way, with one
  output per problem, got 75% right and was wrong-and-sure twice as often.
- **The phone's state helps when the words can't decide.** For a complaint like "phone not making any noise at all",
  knowing that the ring volume is at zero lets it pick the right problem **81%** of the time, against 45% without.
- **It finds the right switch on screens it never saw.** 98% on one maker's settings screens, and 9 of 10 on the
  Moto, better than matching names letter by letter.

## What it can't do yet

For the three problems kept out of all training, it is right **64%** of the time. The untrained "closest
description" model from M4 manages 94%. So the real model misses the one part of the bar that measures this.

We spent seven rounds of experiments, all on practice data, finding out why. The answer surprised us. The model
still *recognises* new problems almost as well as before training. What fails is its check for "this isn't
something I can help with": it learns that anything unfamiliar is off-topic, and a new problem is unfamiliar. Every
version of that check we tried learned the same thing. Telling "not my job" from "a job I haven't learned" is a
known hard problem, and it moves to M6.

The practical consequence is small: when Unstuk learns a new problem, it needs a few dozen example complaints, not
just a one-line description.

## Things we learned

- **Split a score into its parts before trying to fix it.** For three rounds we tried to stop the model
  "forgetting", because the combined score fell. When we finally measured its two halves separately, the forgetting
  turned out to be small; the off-topic check was the real problem.
- **Write down when to stop.** We committed to a last experiment before running it, so a disappointing result
  couldn't turn into an eighth and ninth try.
- **The most accurate model on practice data isn't always the one you want.** With the new-problem check dropped,
  the rules picked the model that is best on known problems and worst on new ones.
- **The test is still the one we built.** The final word comes from real users' messages (M8).
