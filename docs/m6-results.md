# M6 results: Calibrate and gate

2026-10-08 · Status: **done.** Spec: [m6-spec.md](m6-spec.md). Plain-language summary:
[m6-summary.md](m6-summary.md). Report: [ml/reports/calibrated.md](../ml/reports/calibrated.md).

M6 asked whether a model trained with a Brier term and soft targets for vague lines, behind gate lines tuned on
dev, acts more safely than M5's. **By the pre-registered rule it does not.** Three of the four safety rows hold,
but vague lines, the row that had to improve, rose from 10.7% to 17.9% with an interval that touches 0 (+0.0 to
+18.2). The new model is more accurate than M5's: +2.4 points in scope, +2.7 macro-F1, and **+12.5 on held-out
intents** (76.2%, +4.2 to +21.7). Out of scope fitted out of fold failed its guard on every model, so Noul stays.
The tuned lines alone would have done more for vague lines than the new model did.

## The calibrated model against M5's, on the test

All 602 frozen test lines, scored once. M5 is under M2's placeholder lines, as it was reported. Differences are
paired 95% bootstrap intervals.

| Metric | M5 | **M6** | Difference | Must | Passes |
| --- | --- | --- | --- | --- | --- |
| Vague lines asked about or declined (28) | 10.7% | 17.9% | +0.0 to +18.2 | be better | **no** |
| Confident and wrong | 2.6% | 3.0% | −1.0 to +1.7 | not be worse | yes |
| Expected calibration error | 2.8% | 2.6% | −2.3 to +1.8 | not be worse | yes |
| Out-of-scope recall | 92.1% | 91.5% | −4.3 to +2.9 | not be worse | yes |
| Top-1 accuracy, in scope | 87.1% | **89.5%** | +0.2 to +4.7 | reported | |
| Macro-F1 | 87.1% | **89.8%** | +0.6 to +5.0 | reported | |
| Held-out intents | 63.7% | **76.2%** | +4.2 to +21.7 | reported | |

By M4's rung rule, M6 beats M5: accuracy and macro-F1 both lie above 0, and confident and wrong does not.

### The lines did more than the model

| Vague lines asked about or declined | Placeholder lines (0.8 / 0.5) | Tuned lines (0.75 / 0.7) |
| --- | --- | --- |
| M5's model | 10.7% | **35.7%** |
| M6's model | | 17.9% |

On the test, M6's model is surer on vague lines than M5's: it sends 19 of 28 vague lines straight to a fix. On the
vague dev lines the same model and lines handle 36.7%. With 28 test lines, the intervals are wide either way.

### Against the M4 bar

| Metric | Bar | Set by | Must | M6 | Difference | Passes |
| --- | --- | --- | --- | --- | --- | --- |
| In-scope accuracy | 73.9% | Zero-shot | be better | 89.5% | +11.1 to +20.6 | yes |
| Macro-F1 | 69.1% | Frozen encoder | be better | 89.8% | +17.4 to +23.8 | yes |
| Confident and wrong | 1.9% | TF-IDF | not be worse | 3.0% | −0.3 to +2.5 | yes |
| Out-of-scope recall | 95.1% | TF-IDF | not be worse | 91.5% | −7.8 to +0.0 | yes, at the edge |
| Held-out intents | 93.8% | Zero-shot | not be worse | 76.2% | −26.6 to −8.8 | **no** |
| Expected calibration error | 6.1% | Zero-shot | not be worse | 2.6% | −7.1 to −0.4 | yes (better) |

M4's baselines are under the placeholder lines and M6 is under its tuned lines, so confident and wrong compares
two gates as well as two models.

### What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 347 | 7 | 38 | 18 |
| out of scope (164) | 8 | 0 | 6 | 150 |
| vague (28) | 19 | 4 | 3 | 2 |

The confirm band is now narrow (0.70 to 0.75): a low-risk fix is mostly either run or asked about.

## Choosing on dev

### λ

| λ | Dev macro-F1 | Dev log-loss | Dev Brier |
| --- | --- | --- | --- |
| 0 (vague lines only) | 97.5% | 0.0889 | 0.0405 |
| 0.5 | 97.8% | 0.0816 | 0.0382 |
| **1** | **97.9%** | **0.0773** | **0.0369** |

All three are within a point of M5's 98.2%. λ = 1 has the lowest Brier score and log-loss, and was chosen:
`cosine-lr5e-05-typos-state-vague-brier1`, epoch 5, temperatures 0.867 (Choice) and 1.514 (Noul).

### Out of scope fitted out of fold: fails, Noul stays

| Model | Unseen intents' lines declined, per fold | Mean | Dev recall, gate vs Noul |
| --- | --- | --- | --- |
| M5 | 32.3%, 14.8%, 14.7% | 20.6% | 93.8% vs 96.0% |
| M6, λ = 0 | 26.5%, 5.1%, 16.2% | 15.9% | 93.2% vs 94.1% |
| M6, λ = 0.5 | 21.4%, 8.2%, 15.4% | 15.0% | 92.2% vs 94.7% |
| M6, λ = 1 | 17.1%, 8.2%, 19.3% | 14.9% | 92.5% vs 94.7% |

The guard required at most 10% declined and at most 2 points of lost recall. Fitting on fold models narrows the
declines from M5's 15–38% range, but no model gets under 10%, and every gate costs more than 2 points of recall.
By the stop rule, M6 keeps Noul and runs no further rounds.

### The gate's lines

| Line | Before | Tuned | Rule |
| --- | --- | --- | --- |
| Automatic at | 0.8 | **0.75** | The lowest at which automatic picks on dev are wrong at most 2% of the time (1.7%) |
| Clarify below | 0.5 | **0.7** | The most vague dev lines handled (36.7%) with at most 8% of clear lines asked (0.9%) |
| Clarify margin | (none) | **0** | A margin added no vague lines beyond what 0.7 already caught |

## Vague data

Fourteen fresh agents wrote 420 lines. A blind labeller left 184 open between at least two problems: 135 for train
and 49 for dev. See [data/vague/README.md](../data/vague/README.md). The first seven batches kept only 102 lines,
so seven more were written before anything was trained.

## Findings

1. **The gate's lines matter more than the loss for vague lines.** Under the tuned lines, M5's own model asks about
   35.7% of vague test lines, against 17.9% for M6's. Training on vague lines made the model surer of some test
   vague lines, not less sure. 135 training lines are few beside 6,000 clear ones.
2. **Vague dev and vague test disagree.** M6 handles 36.7% of the vague dev lines and 17.9% of the test's. The
   dev lines come from the same agents as the training lines; the test's come from ChatGPT, Gemini and a
   context-free Claude. That is the writer gap of M4 and M5 again, now on vague lines.
3. **Calibration training helps accuracy and new intents, not safety.** λ = 1 and the vague lines together add
   2.4 points in scope and 12.5 on held-out intents, with ECE unchanged (2.6% against 2.8%). On dev's
   leave-intents-out folds, with Noul, the chosen config names never-trained intents a little better than M5's
   (48.0% against 43.6%), still far under zero-shot's 78.7%. Why the test's held-out intents gained 12.5 points
   was not split by head, so the cause is open.
4. **Fitting out of fold narrows open-set declines but doesn't fix them.** Fold models still decline 8–27% of
   unseen intents' lines, and the fitted gate loses more out-of-scope recall than Noul. M5's finding 3 stands.
5. **A sharper model leaves little room between the lines.** With 448 of 574 clear test lines above 0.9, tuning
   pushes clarify up to 0.7 and the confirm band shrinks to 0.70–0.75. A medium-risk fix still always confirms.
6. **Confident and wrong is at the edge.** 3.0% against M5's 2.6% and TF-IDF's 1.9%; the lower automatic line
   (0.75) trades a little safety for fewer confirmations. Both intervals pass, but neither by much.

## What changed from the spec

| Change | Why |
| --- | --- |
| A blind labeller checks the vague lines; only shared readings are kept | So a line is vague by two independent judgements, as the state slice's were |
| Fourteen batches, not seven | The blind check kept 102 of the first 210 lines |
| Writers are fresh agents, not a chat app | Decided before writing: the same writer family as the rest of training |
| The vague slice lives in `data/vague/`, outside `data/raw/` | `unstuk-clean` reads all of `data/raw/`, and must leave M5's split as it was |
| `Scored` carries its gate lines; M2's lines are kept as `M2_GATE` | So M3 to M5's reports reproduce, and M5 can be shown under both sets of lines |
| The Brier score for two-problem (not vague) lines treats the correct options as one outcome | It matches the summed log-loss those lines already had |

## Every test scoring

| When (IST) | What | Settings | Note |
| --- | --- | --- | --- |
| 2026-10-08, report committed 18:26 | **Calibrated model, scored** | `6ec06d9` (sha256 `c8d66d0d…`), `catalog/gate.json` | The one scoring; M5 and M4's rungs re-scored from their committed settings |

No setting was changed after its test score was seen.

## Open for later

- **M7:** int8 on the ONNX graph, then re-check calibration and these lines on the quantized model. The app must
  read `gate.json` beside the model's probabilities; today it reads it beside the keyword matcher's.
- **Vague lines:** the tuned lines, not the loss, did the work. Real users' vague messages (M8) should decide
  whether clarify-below 0.7 asks too often or too little.
- **Out of scope for new intents** stays open after M5's seven rounds and M6's one try. A new intent ships with
  training lines.
- **M8:** real messages decide whether the neural model ships (invariant 10). The held-out bar still fails.
