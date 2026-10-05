# Label audit

2026-10-05 · M3 spec section 3 target: ≥ 95% agreement on 200 clean training lines.

| Check | Lines | Agreement | Cohen's kappa |
| --- | --- | --- | --- |
| Flagged by confident learning, labelled blind | 37 | 36 (97%) | — |
| Random sample of clean train (`unstuk-audit`, seed 11), labelled blind | 200 | 200 (100%) | 1.00 |

How: a fresh agent with no project context read only the labelling guide and a file of anonymous keys and texts
(no labels, no IDs that hint at them), and labelled each line. Its labels are in `data/clean/review-blind.jsonl`
and `data/clean/audit-blind.jsonl`; `data/clean/audit.jsonl` maps keys back to records. The one flagged
disagreement ("The screen dims down while I'm reading a recipe, and I have to keep tapping it") was relabelled
`screen_turns_off_fast` by guide §4, where the blind labeller and the model agreed.

What it means: the given labels match the guide, so label noise is low. A perfect score also says the training
lines are unambiguous, and so easier than real messages. The proxy test set has deliberately hard slices
(paraphrase, collision, negation, vague) to measure exactly that gap; a model that only learned easy lines will
show it there, not here.
