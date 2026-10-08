# M5 results: Encoder and decision heads

2026-10-08 · Status: **done.** Spec: [m5-spec.md](m5-spec.md). Plain-language summary:
[m5-summary.md](m5-summary.md). Reports: [ml/reports/](../ml/reports/).

M5 asked whether a fine-tuned encoder that chooses among option texts clears the M4 bar on the frozen proxy test,
metric by metric, while still naming intents it was never trained on. **Five of six bar rows pass; the held-out
row fails.** On the 12 trained intents the decision model is the best decider so far by a wide margin: 87.1%
in-scope accuracy against the best baseline's 73.9%, 2.8% calibration error, and confident-and-wrong no worse than
TF-IDF's. But it names the three held-out intents 63.7% of the time against zero-shot's 93.8%. Seven pre-registered
rounds on dev traced why: fine-tuning keeps the encoder's zero-shot *naming*, but every out-of-scope check tried
learns that a never-trained intent is unfamiliar and declines it.

## The ladder on the test set

All 602 frozen test lines. M4's rungs are copied from [m4-results.md](m4-results.md); M5's two were each scored
once. Intervals are 95% bootstrap intervals in the reports.

| Metric | TF-IDF + LR | Frozen bge-small + LR | Zero-shot bge-small | Fine-tuned + linear head | **Decision model** |
| --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 64.9% | 70.0% | 73.9% | 75.4% | **87.1%** (83.7–90.2) |
| Macro-F1 | 68.7% | 69.1% | 65.6% | 71.5% | **87.1%** (83.7–89.5) |
| Out-of-scope recall | **95.1%** | 93.3% | 33.5% | 93.9% | 92.1% (87.8–95.9) |
| Out-of-scope precision | 57.8% | 69.9% | 68.8% | 83.2% | **88.3%** |
| **Confident and wrong** | **1.9%** | 3.8% | 3.8% | 5.2% | 2.6% (1.4–4.0) |
| Vague lines answered with a question or decline | 32.1% | 32.1% | **39.3%** | 7.1% | 10.7% |
| Expected calibration error | 17.4% | 12.3% | 6.1% | 10.2% | **2.8%** (2.0–5.6) |
| Held-out intents | 6.2% | 3.8% | **93.8%** | 5.0% | 63.7% (53.2–74.0) |

Reports: [fixed-head.md](../ml/reports/fixed-head.md), [decision-model.md](../ml/reports/decision-model.md).

### Against the bar (decided in M4, paired bootstrap)

| Metric | Bar | Set by | Must | Decision model | Difference | Passes |
| --- | --- | --- | --- | --- | --- | --- |
| In-scope accuracy | 73.9% | Zero-shot | be better | 87.1% | +8.7 to +18.3 | yes |
| Macro-F1 | 69.1% | Frozen encoder | be better | 87.1% | +14.5 to +21.4 | yes |
| Confident and wrong | 1.9% | TF-IDF | not be worse | 2.6% | −0.5 to +2.1 | yes |
| Out-of-scope recall | 95.1% | TF-IDF | not be worse | 92.1% | −6.4 to +0.0 | yes, at the edge |
| Held-out intents | 93.8% | Zero-shot | not be worse | 63.7% | −40.4 to −19.8 | **no** |
| Expected calibration error | 6.1% | Zero-shot | not be worse | 2.8% | −6.8 to −0.3 | yes (better) |

**The decision model does not clear the bar.** It surely beats the fixed-head rung on accuracy (+11.7, +7.8 to
+15.6) and macro-F1 (+15.6), with fewer confident mistakes (−2.6, −4.5 to −0.7). The fixed-head rung in turn does
not beat the frozen encoder by M4's rule: its macro-F1 interval touches 0 (−0.1 to +5.0).

### By slice

Accuracy on clear lines. The best rung per row is in bold.

| Slice (lines) | Frozen encoder | Zero-shot | Fixed head | Decision model |
| --- | --- | --- | --- | --- |
| plain (192) | 87.0% | 68.2% | 86.5% | **92.2%** |
| paraphrase (82) | 67.1% | 72.0% | 73.2% | **85.4%** |
| typo (73) | 61.6% | 61.6% | 68.5% | **82.2%** |
| negation (39) | 64.1% | 71.8% | 71.8% | **82.1%** |
| long story (39) | 71.8% | 66.7% | 74.4% | **89.7%** |
| Indian English (46) | 67.4% | 82.6% | 73.9% | **89.1%** |
| collision (44) | **88.6%** | 6.8% | 86.4% | 84.1% |
| out of scope, near (32) | 81.2% | 28.1% | **93.8%** | 90.6% |
| multi (33) | 81.8% | 84.8% | 93.9% | **97.0%** |
| writer: Gemini (255) | 70.6% | 52.5% | 77.3% | **82.4%** |

### What the gate would do

| Lines | Rung | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- | --- |
| in scope (410) | Fixed head | 306 | 41 | 32 | 31 |
| | Decision model | 319 | 52 | 19 | 20 |
| out of scope (164) | Fixed head | 8 | 2 | 0 | 154 |
| | Decision model | 5 | 5 | 3 | 151 |

## Choosing the model: seven rounds on dev

The spec's guard: a config qualifies only if, on three leave-intents-out folds of dev, it names intents it never
trained on at least as well as the frozen zero-shot rung does (78.7%). Each round was written into the spec before
any of its runs.

| Round | What changed | Configs | Best fold accuracy |
| --- | --- | --- | --- |
| 1 | Learning rate 2e-5 or 5e-5, typo noise, cosine or attention head | 8 | 62.0% |
| 2 | Lower rates (1e-5, 5e-6); the lower 8 layers frozen | 5 | 63.1% |
| 3 | Training on paraphrased option texts (87 wordings, agent-written) | 6 | 66.9% |
| 4 | WiSE-FT: fine-tuned and frozen backbones blended (α 0.25–0.75) | 12 blends | 75.3% (dev macro-F1 85.0%) |
| 5 | Out of scope from the best Choice score instead of Noul | 19 re-scored | 67.7% |
| 6 | Noul reads the complaint against the options; correct options dropped from a quarter of training lines | 4 | 68.2% |
| 7 | Noul reads only how well the options fit | 4 | 69.7% (dev macro-F1 63.8%) |

**The diagnosis, after round 4.** Splitting the fold score into its two heads changed the reading of rounds 1–3:

| On never-trained intents' lines | Choice alone right | Declined as out of scope |
| --- | --- | --- |
| Frozen zero-shot rung | 83.5% | about 5% |
| Best fine-tuned configs | 82.6%, 82.4%, 82.3% | 15–38% |
| Round 6 (option-aware Noul) | 69.4–80.6% | 18–22% |

Fine-tuning costs the Choice head about one point of zero-shot naming. The loss is out of scope: a check learned
from trained intents treats a new intent as unfamiliar, whether it reads the complaint (Noul), the best score (the
gate) or the fit of the options (round 7), since a new intent's own option fits less well than a trained one's.

**The stop rule.** Round 7 was pre-committed as the last. Nothing qualified, so the guard was dropped and the rung
rule alone picked `cosine-lr5e-05-typos-state` (complaint-only Noul, epoch 5, dev macro-F1 98.2%), which has the
lowest fold accuracy of any config (43.6%). `decision.json` records `"guarded": false`. On the test, its held-out
mistakes are the ones dev predicted: `wrong_time → out_of_scope` (5) and `cant_hear_call → out_of_scope` (4) lead
the list. In all: 31 configs, 109 runs, 71 scored variants.

## State: in or out

Spec section 4, on the 47 records whose intent only the device state settles. Report:
[state.md](../ml/reports/state.md).

| Measure | With state | Without | Paired difference |
| --- | --- | --- | --- |
| State-test accuracy (clear lines) | **81.0%** | 45.2% | +22.2 to +50.0 |
| Dev macro-F1 | 98.2% | 98.4% | −0.7 to +0.5 |

**State stays.** Without it the model can only guess between the two sides of a pair; with it, it reads the
finding ("Do Not Disturb is on.") and picks the side whose cause holds.

## Node labels

The same Choice head, asked which item on the screen is the switch. Dev is Xiaomi wording; the test is the Moto.

| Method | Dev (132) | Moto test (10) |
| --- | --- | --- |
| String baseline (M3) | 90.9% | 8/10 |
| Similarity, frozen (M4) | 82.6% | 8/10 |
| **Decision model** | **97.7%** | **9/10** |

## Findings

1. **Choosing among option texts beats a fixed head by a wide margin.** The same backbone and data, read through
   option texts instead of one output per intent: +11.7 points of in-scope accuracy, +15.6 of macro-F1, fewer
   confident mistakes and a quarter of the calibration error.
2. **Fine-tuning keeps zero-shot naming; out of scope is what forgets.** Rounds 1–3 were aimed at forgetting in the
   encoder. Round 4's split showed that most of the loss was the out-of-scope head declining unfamiliar intents.
   Splitting a combined metric into its parts earlier would have saved two rounds.
3. **Every out-of-scope signal learned from trained intents encodes "seen before".** The complaint, the best score
   and the fit of the options all do. Telling "not our problem" from "a problem we haven't trained" is open-set
   recognition, and M5 didn't solve it.
4. **Fine-tuning without a guard picks the model least able to generalise.** The rung rule's pick is the most
   accurate on dev and the worst on the folds. The guard was right to exist; it just found no config that passed.
5. **State earns its place.** +36 points on the complaints only state can settle, at no cost on dev.
6. **One head serves complaints and screens.** Trained jointly, Choice finds the right switch on a maker's screens
   it never saw (97.7%), past string matching.
7. **Dev is still much easier than the test.** Dev macro-F1 98.2%, test 87.1%; the Gemini writer is still the
   hardest (82.4%). The gap is smaller than M4's (96–98% against 66–69%).
8. **Vague lines are worse handled than by any baseline.** 10.7% get a question or a decline, against 32–39% for
   M4's rungs: a sharper model answers more confidently. This is for M6's gate.

## What changed from the spec

| Change | Why |
| --- | --- |
| Rounds 2 to 7 added to tuning, each pre-registered | Round 1 failed the guard; each later round tested one stated cause |
| The guard dropped by a stop rule written before round 7 | No config of seven rounds qualified |
| State rendered as the catalog's findings, not check IDs | "dnd on" tokenises as `d ##nd`; the findings are the sentences the app shows |
| `catalog/option-wordings.json` (training only) | Round 3; the app's catalog parser is strict, so `intents.json` stays as it was |
| Out of scope by a gate, and Noul heads that read options or option fit | Rounds 5–7, after round 4's diagnosis |
| The fixed-head rung reads text only | The fine-tuned counterpart of M4's text-only probe |
| The state twin is one run, with no folds | The guard no longer applied when step 7 ran |
| The Colab runner resumes, and gives up on a run after 30 minutes | The free tier reclaimed VMs mid-grid; `colab exec` waited out its timeout |
| Notes after rounds 1–3 blamed forgetting | Corrected after round 4; the spec keeps both, the correction dated |

## Every test scoring

| When (IST) | What | Settings | Note |
| --- | --- | --- | --- |
| 2026-10-05 21:38 | **Fixed-head rung, scored** | `b2ec962` (sha256 `2d25b699…`) | The one scoring |
| 2026-10-08, step 7 | State test (`data/state/test.jsonl`), both state models | `ae617ee` and the twin | Its own test set, designated by M3 for this decision |
| 2026-10-08 08:12 | **Decision model, scored** | `ae617ee` (sha256 `e16431e0…`), state kept in `c0173a4` | The one scoring; M4's rungs re-scored from their committed settings for the bar |

No setting was changed after its test score was seen.

## Open for later

- **M6:** out of scope that doesn't decline new intents (finding 3); out-of-scope recall sits at the edge of the
  bar; vague lines (finding 8); the gate's thresholds on this model's calibration (2.8% ECE is a good start).
- **M7:** export the decision model (backbone, Choice and Noul) to ONNX; the option vectors for the catalog can be
  cached at build time.
- **M8:** real messages decide whether the neural model ships (invariant 10); the held-out bar fails here.
- **Product:** a new intent ships with training lines, not option text alone ([plan.md](plan.md), correction of
  2026-10-08).
- **Infrastructure:** Colab's free tier repeatedly dropped or reclaimed sessions; the runner resumes, but a paid
  runtime or a local GPU would make long grids routine.
- **Unchanged from M4:** guide §5's `wifi_no_load` question; the Moto hides its Settings airplane-mode row.
