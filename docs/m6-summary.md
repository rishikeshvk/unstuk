# M6 in plain words: honest confidence, and when to ask

2026-10-08 · Summary of the sixth phase. The detailed numbers are in [m6-results.md](m6-results.md).

## The question we set out to answer

M5's model was accurate, but too sure of itself on unclear messages like "phone not making noise". Those could mean
calls, or messages, or something else, and the right reply is "which do you mean?". M5's model asked that only one
time in ten. M6 tried to fix this in two ways:

- **Teach the model to be unsure.** We wrote about 400 unclear messages, kept the 184 that a second, independent
  reader also found unclear, and trained the model to spread its confidence across the possible problems. We also
  added a training penalty that rewards confidence matching how often the model is right.
- **Set the app's lines from data.** The app runs a fix by itself, asks first, or asks "which do you mean?",
  depending on how sure the model is. Until now those lines were guesses (80% and 50%). M6 set them from practice
  data: run by itself at 75% or more, ask "which do you mean?" below 70%.

## What we found

- **The new model is better at its main job.** It picks the right problem **89.5%** of the time, up from 87.1%.
  For the three problems it was never trained on, it improved from 64% to **76%**.
- **Its confidence is still honest:** 2.6% calibration error.
- **But it didn't get better at asking.** On the test's 28 unclear messages it asked or declined **18%** of the
  time, up from 11%, but with so few messages that could be luck. By the rule we wrote down first, that isn't an
  improvement.
- **The new lines did the most.** M5's old model, with the new lines, would have asked about **36%** of the
  unclear messages. Training on unclear messages made the new model surer of some of the test's unclear messages,
  not less sure.
- **The "not something I can help with" check is still too quick to refuse new problems.** We tried once more,
  with a check trained on models that really hadn't seen some problems. It refused fewer of them, but still too
  many, so we kept the old check, as we had agreed to beforehand.

## Things we learned

- **Where you draw the line can matter more than how you train.** Moving one number in the app did more for
  unclear messages than a new training method.
- **Practice data written by the same kind of writer is too easy.** The new model asked about 37% of the practice
  unclear messages and 18% of the test's. The test was written by other chatbots, and they write differently.
- **Check that a message is really unclear before you teach it as unclear.** Over half of the "unclear" messages
  the writers produced were clear to an independent reader.
- **Small test slices give wide answers.** With 28 unclear messages, the improvement could be anywhere from 0 to 18
  points. Real users (M8) will give a better answer.
