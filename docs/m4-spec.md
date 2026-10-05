# M4 spec: Baselines

2026-10-05 · Status: **done.** Results: [m4-results.md](m4-results.md). Background: [plan.md](plan.md), roadmap step 4, and
[m3-results.md](m3-results.md).

M4 answers one question: **does a cheap learned classifier beat the keyword matcher on the frozen proxy test, and
by how much?** Whichever rung wins becomes the bar the fine-tuned encoder of M5 must clear (invariant 10).

It is done when each rung below is trained on `data/clean/train.jsonl`, tuned only on `dev.jsonl`, scored once on
the 602 frozen test lines with `ml/src/unstuk_ml/evaluate.py`, and compared with the rung beneath it by a paired
bootstrap; and when `m4-results.md` says which rung M5 has to beat.

```text
keyword matcher (M3: 40.2% in scope, 8.7% confident and wrong)
   └─► TF-IDF + logistic regression        words and character n-grams; cheap, fast, no pre-training
          └─► frozen bge-small + logistic regression   a pre-trained encoder's sense of meaning, nothing fine-tuned
                 └─► (M5) fine-tuned encoder with Choice / Noul heads
```

## 1. What each rung tests

| Rung | What it can learn | What it can't |
| --- | --- | --- |
| Keyword matcher (scored in M3) | The phrases we typed | Anything we didn't type; its probabilities are fake |
| TF-IDF + logistic regression | Which words and spellings go with which intent, from 5,833 lines; character n-grams cover typos ("intrnet") | Meaning: "stays quiet" and "doesn't ring" share no n-grams |
| Frozen encoder + logistic regression | Meaning the encoder learned in pre-training, read by a linear layer (a "linear probe") | Anything the frozen embedding doesn't already separate |

Both learned rungs are **fixed-head classifiers**: one output per label they were trained on. The three held-out
intents (`screen_wont_rotate`, `wrong_time`, `cant_hear_call`) never appear in training, so these rungs score
**0% on them by construction**, except on the 5 two-problem test lines whose other problem is trained. That is reported, not hidden: it is the case for M5's option-text heads.

## 2. Training setup, shared by both rungs

- **Labels:** the 12 trained intents' IDs (the catalog's 15 minus the 3 held out) plus `out_of_scope`, as one
  13-way softmax. The gate reads the output exactly as `evaluate.Scored.outcome` does today: top `out_of_scope` →
  decline, top below 0.5 → clarify, 0.5 to 0.8 → confirm, 0.8 and above → automatic.
- **Lines with two labels** (3 in train) count once per label.
- **Tuning on dev only.** A small grid per rung (below), chosen by dev macro-F1, ties broken by dev log-loss.
  Dev is split by batch (M3), so near-twins can't inflate it.
- **Calibration:** one temperature per rung, fitted on dev by log-loss, applied before scoring. Both raw and
  calibrated ECE are reported. (M6 tunes the gate's thresholds; M4 only makes the probabilities honest enough to
  compare.)
- **The test is scored once per rung**, after its settings are frozen. A later change to a rung, other than a bug
  fix, means a new rung with its own name. Results list every test scoring.
- **Deterministic:** fixed seeds, and the same output under different `PYTHONHASHSEED`s, tested across processes
  (the M3 lesson).

### TF-IDF + logistic regression

scikit-learn, already a dependency. Features: word 1–2-grams and `char_wb` 2–5-grams, joined. Grid: regularisation
`C` ∈ {0.3, 1, 3, 10, 30, 100}, class weights none or balanced. Twelve fits, about 20 seconds each.

*Changed before any test score (2026-10-05):* the approved grid stopped at `C` = 10, and that was the dev winner, with
macro-F1 still rising. So the grid was extended to 30 and 100 on dev alone, before the settings were frozen.

### Frozen encoder + logistic regression

- **Encoder:** `BAAI/bge-small-en-v1.5` (33M parameters, 384 dimensions, MIT licence), the plan's first candidate.
  CLS pooling and L2 normalisation, as its model card says. Revision pinned by commit hash (`5c38ec7c`, current today); the repository ships `onnx/model.onnx`.
- **Runtime:** the model's own ONNX file through `onnxruntime` and `tokenizers`, on this machine's CPU. Embedding
  about 7,500 short lines takes minutes, so no Colab.
- **Cache:** embeddings stored under `ml/cache/` (gitignored), keyed by model revision and text hash.
- **Head:** logistic regression, grid `C` ∈ {0.1, 0.3, 1, 3, 10}.
- **Grid edge, decided before any encoder score (2026-10-05):** if dev's winner is the largest `C`, the grid
  extends to 30, then 100, then 300, one at a time, until the winner sits inside it. The TF-IDF grid needed this
  extension, and fixing the rule in advance means it can't be bent to fit a result.

## 3. When does a rung "beat" the one below?

On the test set, with a **paired** bootstrap: each resample draws the same lines for both rungs, so the interval
is on the *difference*, which is tighter than comparing two separate intervals. A rung beats the one below when:

1. the 95% interval of the difference in in-scope accuracy **and** in macro-F1 lies above 0, and
2. the confident-and-wrong rate is not higher: the interval of its difference does not lie above 0.

The second rule is there because a model can be right more often and still be dangerous: the safety number is the
automatic fix on the wrong problem.

## 4. Reports

`baseline_report.py` becomes the report for any decider: the same tables (headline metrics, what the gate would do,
slices and writers, common mistakes), with the decider's name in the title. A second use exists now, so the
refactor is due. Added:
- a comparison table with each rung's paired difference against the one below;
- raw and calibrated ECE;
- confusion pairs that each learned rung fixed or introduced compared with the rung below it. For the encoder that
  is TF-IDF, which shows what meaning adds over n-grams; against the keyword matcher it would mostly repeat what
  TF-IDF already fixed.

One generated report per rung under `ml/reports/`, plus `docs/m4-results.md` and a plain-language summary.

## 5. Decisions (approved 2026-10-05)

| # | Question | Chosen |
| --- | --- | --- |
| 1 | What counts as "beats" | Section 3: paired bootstrap on accuracy and macro-F1, and no worse on confident and wrong |
| 2 | fastText | **Leave it out.** Meta archived the repository in March 2024; its last release (0.9.3) ships one wheel, for Python 3.9 on Apple-silicon macOS, so here it would build from C++ source with no maintainer behind it. Its strength, sub-word n-grams for typos, is what the `char_wb` features give the TF-IDF rung |
| 3 | A zero-shot rung | **Add it.** The frozen encoder compares the complaint with each intent's catalog option text ("The internet or mobile data is not working") and with an out-of-scope option, without any training. It is the only rung that can score on the held-out intents, so it gives M5 a zero-shot bar |
| 4 | Node labels | **Add a similarity baseline.** The same encoder picks the option closest to the question, scored on the 132 dev questions (Xiaomi wording) and the 10 Moto questions, beside M3's string baseline (8/10) |

### Rejected alternatives

1. **`sentence-transformers`** is the easy way to run bge-small, but it pulls in PyTorch, over a gigabyte for a
   frozen forward pass. ONNX is also what the app will run in M7, so meeting its tokeniser and pooling now is
   useful.
2. **Fine-tuning the encoder's top layers** here would blur M4 into M5 and leave no frozen bar to compare against.
3. **Tuning on the test** in any form, including picking the rung's grid after seeing a test score: then the test
   no longer measures anything (M3 section 10).
4. **Choosing the rung by dev accuracy alone** ignores the safety number. Log-loss breaks ties because it punishes
   confident mistakes.

## 6. Not in M4

- Fine-tuning, decision heads and their losses (M5).
- The gate's thresholds and per-question temperature (M6).
- ONNX export for the app, quantisation and the Kotlin `decide` API (M7).
- Real user messages (M8).

## Steps

One commit each, or a few where a step is large. Each step ends with a short "what to study" note.

1. **This spec.**
   *Learn:* why baselines come in a ladder, and why each rung's test score is taken only once.
2. **Paired bootstrap and the shared report:** `evaluate.paired_bootstrap`, `baseline_report.py` generalised, the
   keyword report regenerated unchanged.
   *Learn:* paired versus unpaired comparisons, and why a paired interval is tighter.
3. **TF-IDF rung:** train, dev grid, temperature, one test score, report.
   *Learn:* TF-IDF, character n-grams, logistic regression and temperature scaling.
4. **Encoder embeddings:** pinned ONNX download, tokeniser, CLS pooling, cache; tests for shape, normalisation and
   determinism.
   *Learn:* how a sentence embedding is made, and why pooling must match the model's training.
5. **Encoder rung:** the same protocol as step 3.
   *Learn:* linear probes, and what a frozen representation can and can't separate.
6. **Zero-shot and node-label similarity**, if decisions 3 and 4 are approved.
   *Learn:* zero-shot classification by similarity, and why option wording matters.
7. **Results:** `m4-results.md`, a plain-language summary, the comparison and an error analysis against the keyword
   matcher.
   *Learn:* reading a paired difference, and when "no significant difference" is the finding.
