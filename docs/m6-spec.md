# M6 spec: Calibrate and gate

2026-10-08 · Status: **in progress.** Background: [plan.md](plan.md), roadmap step 6, and
[m5-results.md](m5-results.md).

M6 answers one question: **does a decision model trained with a proper-scoring loss and soft targets for vague
lines, behind a gate whose thresholds are tuned on dev, act more safely than the M5 model?** More safely means
three things: more vague lines answered with a question, no more confident mistakes, and out of scope no worse.

It is done when the new model and the gate are each chosen on dev by rules written here first, scored once on the
602 frozen test lines, compared with the M5 decision model by paired bootstrap, and `m6-results.md` says whether
the model is safer.

```text
M5 decision model (87.1% in scope, 2.8% ECE, 10.7% of vague lines asked)
   ├─► + vague lines with soft targets       teach "unsure" with data that shows it
   ├─► + Brier term in the loss (λ)          a proper scoring rule beside cross-entropy
   ├─► out-of-scope gate fitted out of fold  one try at "unfamiliar is not out of scope"
   └─► gate thresholds from dev              automatic, clarify and a new margin rule
```

M5 left three gaps: vague lines (10.7% asked, against 32–39% for M4's rungs), out of scope that declines new
intents with recall at the edge of the bar, and the gate's placeholder thresholds (0.8 and 0.5).

## 1. Vague data

Dev has no vague lines and train has three, so nothing can be tuned for them, and the model never sees what
"several readings" looks like.

- **Writers:** fourteen fresh agents with no project context, one writer persona per batch from the diversity grid
  ([`data/vague/plan.json`](../data/vague/plan.json)), as in M3. Each reads only its rendered
  [prompt](../data/vague/prompts/vague-v1.md) and makes one tool call: the Write of its own 30-line sheet. Each
  line's header lists the two or three intents it could mean. The sheets are committed as returned.
- **Blind check:** a fresh agent labels the 420 texts by the guide in shuffled order, with keys that hide the batch
  (`unstuk-vague-slice ../data/vague blind`). A line is kept only if it shares at least two readings with the
  labeller, and its labels become those shared readings. It is vague by two independent judgements, as the state
  slice's texts were. The first seven batches kept 102 of 210 lines (73 train, 29 dev), short of the aim of
  about 150 and 60, so seven more batches from the same prompt, with new grid cells, were added before anything
  was trained. One labeller then labelled all 420 texts.
- **Split:** `vague-06`, `-07`, `-13` and `-14` go to dev and the other ten batches to train, split by batch so that
  one writer's style never lands on both sides. The output is `data/vague/train.jsonl` and `dev.jsonl`. The slice
  lives outside `data/raw/`, so `unstuk-clean` leaves M5's split unchanged.
- **Leakage:** lines within 0.8 similarity of a test line are dropped (`duplicates.leaking`, the M3 threshold),
  and so are exact duplicates. The test is read for nothing else.
- **Held-out intents** never appear as a label (invariant 9). A line whose writer named one is dropped, and the
  blind labeller's readings count only where the writer gave them too.

## 2. The loss

- **Choice:** cross-entropy plus λ times the Brier score over the offered options,
  `Σ_i (p_i − y_i)²`. **Noul:** binary cross-entropy plus λ times `(p − y)²`.
- **Vague lines:** the Choice target spreads evenly over the line's labels that are offered, and Noul's target
  is 0. The summed-probability loss that M5 used for two-label lines would let the model put all its probability
  on one reading; a soft target asks for the spread.
- **λ = 0 reproduces M5's loss** on lines that aren't vague, and a test checks it.

## 3. Training

- **Config:** M5's chosen config (`cosine-lr5e-05-typos-state`), unchanged except for the loss and data:
  λ ∈ {0, 0.5, 1}. λ = 0 isolates the effect of the vague data.
- Each λ gets a full run and the three leave-intents-out folds: 12 runs on Colab through `unstuk-colab-train`.
  The epoch rule is M5's (best dev macro-F1, at most 6).
- One temperature per head is refitted on dev by log-loss, as in M5.

## 4. Out of scope, fitted out of fold (one try)

Every out-of-scope check in M5 was calibrated on trained intents only, so it learned that a never-trained intent
looks out of scope. The fold models offer what M5's checks lacked: in-scope lines of intents the model really
never trained on.

- **The gate:** `p(out of scope) = sigmoid(a · best Choice logit + b · Noul logit + c)`, a two-feature logistic
  regression by log-loss. It is fitted on the fold models' dev scores, where each fold's removed intents' lines are
  in scope (target 0) and out-of-scope lines are 1. The intents share `1 − p` in proportion to Choice, as before.
- **Guard (nested):** fit on two folds, then score the third fold's unseen intents. The gate passes if it calls out
  of scope on at most 10% of those lines on average (M5: 15–38%), and if, applied to the full model, its dev
  out-of-scope recall is at most 2 points below Noul's.
- **Applied to:** M5's existing fold checkpoints first (no training), then step 3's.
- **Stop rule, written before any run:** if no gate passes, M6 keeps Noul, records the result, and runs no further
  rounds.

## 5. The gate's thresholds

- **One source of truth:** `catalog/gate.json` holds `automatic_at`, `clarify_below` and `clarify_margin`.
  `evaluate.py` and `RiskGate.kt` both read it, replacing their constants.
- **New rule:** clarify also when the top two intents are within `clarify_margin` of each other. A vague line
  often splits between two readings, neither of which is low on its own.
- **Tuning rule, on dev only:**
  - `automatic_at` is the lowest value in {0.50, 0.55, …, 0.95, 0.99} at which automatic decisions on dev are
    wrong at most 2% of the time.
  - `clarify_below` ∈ {0.3, 0.4, …, 0.7} and `clarify_margin` ∈ {0, 0.05, …, 0.4} maximise vague-handled on dev's
    vague lines, subject to at most 8% of clear in-scope dev lines being clarified. Ties go to the smaller values.
- Medium- and high-risk fixes keep their tiers. The thresholds only move the low-risk line (invariant 3).

## 6. Choosing, and scoring the test once

- **λ:** among the three, the lowest dev Brier score whose dev macro-F1 is no more than 1 point below M5's
  (98.2%), with ties going to the lower log-loss. If the out-of-fold gate passed, it is fitted on that λ's folds.
  The choice is recorded in `ml/settings/calibrated.json` with the checkpoint's sha256 and the commit.
- **The test is scored once**, locally on CPU, from that checkpoint and `catalog/gate.json`.
- **Against the M5 decision model, paired bootstrap, pre-registered:**

  | Metric | Must |
  | --- | --- |
  | Vague lines answered with a question or decline | be better |
  | Confident and wrong | not be worse |
  | Expected calibration error | not be worse |
  | Out-of-scope recall | not be worse |
  | In-scope accuracy, macro-F1, held-out intents | reported |

  "Not worse" uses M4's rule: the interval of the difference must not lie wholly on the bad side.
- The M4 bar table is re-run for the new model.
- **Report:** `ml/reports/calibrated.md`, with the comparison, the bar, the gate's outcome table, and a
  reliability table before and after.

## 7. Decisions (approved 2026-10-08)

| # | Question | Chosen | Rejected |
| --- | --- | --- | --- |
| 1 | int8 | Moved to M7, quantizing the ONNX graph that ships | PyTorch dynamic int8 here: it measures a model that never ships |
| 2 | Proper-scoring loss | CE + λ·Brier | NanoJev's paired proper reward: with fixed labels it needs sampling and adds nothing Brier lacks |
| 3 | Vague lines | Soft targets on new train and dev lines | Only a margin rule in the gate: dev has no vague lines to tune it on |
| 4 | Out of scope | One out-of-fold gate, with a stop rule | No try (out-of-scope recall stays at the edge); a new research round (seven M5 rounds failed) |
| 5 | Thresholds | An error-rate target on dev | A cost-weighted rule: its costs would be invented numbers |
| 6 | Where thresholds live | `catalog/gate.json`, read by training and the app | Constants in two languages kept in step by hand |
| 7 | Distillation | Left out | A Laya / NanoJev teacher: ECE is already 2.8%, and licences and the free tier's limits cost more than it could win |

## 8. Not in M6

- int8, ONNX export and the Kotlin `decide` API (M7).
- Distillation and a Score head.
- Real user messages (M8).
- More out-of-scope rounds after section 4's stop rule.

## Steps

One commit each, or a few where a step is large. Each step ends with a short "what to study" note.

1. **This spec**, and a plan.md correction for int8 and distillation.
   *Learn:* why calibration comes before thresholds.
2. **Vague data:** prompt, sheets, blind check, leakage check, train and dev split.
   *Learn:* why a model can't learn "be unsure" from data that never shows it.
3. **The loss:** Brier terms and soft vague targets, with CPU tests.
   *Learn:* proper scoring rules, and why cross-entropy alone drifts overconfident.
4. **Training:** 12 runs on Colab and refitted temperatures.
   *Learn:* what λ trades between sharpness and calibration.
5. **Out-of-fold gate:** fitted and guarded, on M5's folds and then M6's.
   *Learn:* open-set recognition, and why the calibration data must include the unfamiliar.
6. **Gate thresholds:** `catalog/gate.json`, the margin rule, tuned on dev; `evaluate.py` and `RiskGate.kt` read
   it.
   *Learn:* selective prediction and risk–coverage curves.
7. **Choose and score once:** `calibrated.json`, the test scoring and `calibrated.md`.
   *Learn:* paired bootstrap for "not worse".
8. **Results and summary:** `m6-results.md`, `m6-summary.md`.
