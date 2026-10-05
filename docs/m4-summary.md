# M4 in plain words: simple models, and the bar for the real one

2026-10-05 · Summary of the fourth phase. The detailed numbers are in [m4-results.md](m4-results.md).

## The question we set out to answer

M3 built a locked test of 602 complaints and showed that the keyword list picks the right problem only 40% of the
time. M4 asked: do simple learned models do better, and which is the best of them? Whatever wins becomes the score
the real model, built next, has to beat.

## What we tried

Three quick approaches, each trained on the same examples and tested once on the locked test:

- **Word and spelling patterns** (TF-IDF): learns which words, and which bits of words, go with which problem. It
  never understands meaning, but "intrnet" still looks like "internet" to it.
- **A ready-made language model with a simple layer on top** (frozen bge-small): a small model, trained by others on
  lots of text, turns each complaint into a set of numbers that capture its meaning. We only trained the last layer.
- **Closest description** (zero-shot): no training at all. The same language model compares the complaint with the
  one-line description of each problem Unstuk can fix, and picks the closest.

## What we found

- **Learning beats a word list, by a lot.** The word-pattern model picks the right problem **65%** of the time,
  against the keyword list's 40%. It would change a setting automatically for the wrong problem about **one time in
  fifty**, against one in eleven.
- **Understanding meaning helps, but costs safety.** The language-model version gets **70%** right and copes much
  better with unusual wording ("the phone stays quiet when people call"). But it is wrong-and-sure twice as often,
  and it struggles with typos, so by our rule it does not beat the simpler one.
- **Closest description knows problems it was never taught.** For the three problems we kept out of all training,
  it is right **94%** of the time. But it can't say "I can't help with that": complaints like "my ear is ringing"
  land on the closest phone problem. Only a third of off-topic messages are turned away.
- **None of them asks when a complaint is unclear.** On vague messages like "phone not working properly", every
  learned model answers two times in three instead of asking a question. Unstuk's decision rules (M6) must handle that.
- **Finding the right switch on screen:** matching names letter by letter still beats matching by meaning (91% vs
  83%), because screens show names like "TalkBack", not descriptions.

## The bar for the real model

No single approach wins everywhere, so the real model (M5) must beat the best one at each thing:
- more often right than closest description (74%), and more balanced across problems than the language model;
- no more often wrong-and-sure than the word-pattern model (one in fifty);
- turning away off-topic messages as well as the word-pattern model (95%);
- recognising the never-taught problems as well as closest description (94%), with confidence as honest as its own.

That is a hard bar, which is the point: the real model is only worth its complexity if it beats every cheap
alternative on what that alternative does best. And this is still a test we built. The final check uses messages
from real users (M8).

## Things we learned

- **Decide the rules before seeing the scores.** What "better" means, which settings to try and when to widen the
  search were all written down before each test score, so no result could bend them.
- **The practice set was much easier than the test.** Every trained model scored about 97% on the practice set
  and 65–70% on the test, and adjusting confidence on the easy set made one model's confidence less honest on the
  hard one.
- **One wording can't stand for "everything else".** Zero-shot needs a separate way to say no.
