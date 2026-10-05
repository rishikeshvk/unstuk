# M5 spec: Encoder and decision heads

2026-10-05 · Status: **approved, in progress.** Background: [plan.md](plan.md), roadmap step 5, and
[m4-results.md](m4-results.md).

M5 answers one question: **does a fine-tuned encoder that chooses among option texts clear the M4 bar on the frozen
proxy test, metric by metric, while still naming intents it was never trained on?**

It is done when the fixed-head rung and the decision model are each tuned on dev only, scored once on the 602 frozen
test lines, checked against the M4 bar by paired bootstrap, and `m5-results.md` says whether the decision model
clears it.

```text
M4 bar (per metric, set by the best baseline)
   ├─► fine-tuned bge-small + linear 13-way head     does fine-tuning help? (the plan's fixed-head rung)
   └─► fine-tuned bge-small + Choice and Noul heads  the product: options supplied at runtime
```

The bar, from [m4-results.md](m4-results.md): **better** on in-scope accuracy (73.9%, zero-shot) and macro-F1
(69.1%, frozen encoder); **not worse** on confident and wrong (1.9%, TF-IDF), out-of-scope recall (95.1%, TF-IDF),
held-out intents (93.8%, zero-shot) and expected calibration error (6.1%, zero-shot).

## 1. The model

- **Backbone:** `BAAI/bge-small-en-v1.5` at M4's pinned revision (`5c38ec7c`): 33M parameters, 384 dimensions,
  CLS pooling. Loaded with `transformers` for training. ONNX export is M7, so the heads use only operators ONNX
  exports.
- **Input:** the complaint as segment A and the device state as segment B, rendered from the catalog's check IDs
  (`ringer_not_normal` becomes "ringer not normal"). Segment B is empty when there is no state.
- **Choice head:** options go through the same backbone, so the catalog's options can be cached at build time.
  Each option vector attends to the complaint's token vectors (one cross-attention layer), then one set-attention
  layer runs across the options, then a linear layer gives one score per option; softmax. There is no positional
  encoding over options, so their order can't matter, and a test checks it. Ablation on dev: with the head off,
  the score is a scaled cosine, which is the zero-shot rung fine-tuned.
- **Noul head, "is this out of scope?":** a sigmoid on the pooled complaint vector. M4 finding 5 showed that out of
  scope can't be one option text. For the shared report, `out_of_scope = p` and each intent gets
  `(1 − p) · choice_i`, so `evaluate.Scored` and the gate read it unchanged.
- **No Score head** in M5: there are no urgency labels and no code reads it yet.

## 2. Training data

- `data/clean/train.jsonl` (5,833 lines), plus `data/state/train.jsonl` (117) and `data/nodes/train.jsonl` (828) as
  extra Choice questions with their own options. Dev is `data/clean/dev.jsonl` and `data/nodes/dev.jsonl`.
- **Options per example:** the gold intent plus a random subset of 3 to 11 other trained intents, drawn again each
  epoch, so the head learns to choose among whatever it is given (plan, training step 1). The held-out intents'
  option texts never appear in training.
- **Out-of-scope lines:** Noul target 1, Choice loss masked. In-scope lines have Noul target 0.
- **Lines with two labels:** the Choice loss is on the summed probability of both gold options.
- **Typo noise** (M4 finding 2): a seeded share of lines gets one character dropped, swapped or doubled. On or off
  is a grid choice.
- **State:** lines from the main set get 0 to 2 random distractor checks from the catalog, so the model learns that
  the complaint dominates; the state slice teaches state to break a tie.
- **Loss:** cross-entropy for Choice plus binary cross-entropy for Noul. The Brier / proper-scoring loss is M6.

## 3. Tuning, on dev only

- **Grid:** learning rate {2e-5, 5e-5} × typo noise {off, on} × Choice head {cosine, attention}: eight runs. The
  epoch count, at most 6, is the one with the best dev macro-F1 in each run.
- **Zero-shot guard, without touching the held-out intents.** Dev has no held-out intents, so three
  *leave-intents-out folds* each remove 4 of the 12 trained intents (their lines and option texts) from training
  and score those intents' dev lines. The frozen zero-shot rung is scored on the same folds.
- **Selection rule, fixed before any run:** among the configs whose mean fold accuracy is not below the zero-shot
  rung's, the highest dev macro-F1 wins, ties going to the lower dev log-loss. If no config qualifies, that is the
  finding, and the best config on the folds is reported before anything is scored on the test.
- **Calibration:** one temperature per head (Choice and Noul), fitted on dev by log-loss, as in M4. Raw and
  calibrated ECE are both reported.
- **Fixed-head rung:** the same backbone with a 13-way linear head; grid of learning rate × typo noise, the same
  epoch rule.

### Round 1 failed the guard; round 2 (decided 2026-10-05, before any decision-model test score)

The zero-shot rung scores 78.7% on the folds (87.5%, 85.6%, 62.9%). No round-1 config came near it: the best
mean fold accuracy at the kept epoch was 62.0% (attention, 2e-5, typos), and the best at any single epoch was
63.5%, reached after the first epoch. Fold accuracy then falls every epoch while dev macro-F1 rises, and 5e-5
falls faster than 2e-5. Fine-tuning forgets how to name unseen options from the start.

Round 2 aims at that forgetting. Each config runs on all the data and on the three folds, as before:

| Config | Head | Learning rate | Typos | Frozen |
| --- | --- | --- | --- | --- |
| 1, 2 | cosine, attention | 1e-5 | on | none |
| 3, 4 | cosine, attention | 5e-6 | on | none |
| 5 | attention | 2e-5 | on | embeddings and the lower 8 of 12 layers |

Typo noise stays on because it gave the higher fold accuracy for both heads in round 1. The guard, the selection
rule and the heads' 1e-3 rate are unchanged, and the pool is both rounds' configs. If nothing qualifies after
round 2, M5 records that fine-tuning costs zero-shot naming and asks how to go on; the test is still untouched.

## 4. State: in or out

The chosen config is trained twice, with and without the state segment, and both are scored on
`data/state/test.jsonl` (47 records). State stays in if the paired interval on state-test accuracy lies above 0
and dev macro-F1 is not surely worse. This is decided before the main test is scored, as the
[state slice](../data/state/README.md) planned.

## 5. Scoring and the bar

- Each rung's test is scored **once**, locally on CPU, from a checkpoint whose sha256 is in the rung's committed
  settings. GPU training isn't bit-for-bit reproducible, so the test reads the checkpoint rather than retraining.
- **The bar check:** a new `evaluate` function pairs the decision model with each bar-setting M4 rung (re-scored
  deterministically from their committed settings) and applies the rule in [m4-results.md](m4-results.md) per
  metric. The fixed-head rung is compared with the frozen-encoder rung by M4's `beats`.
- **Node labels:** the decision model's Choice accuracy on node dev (132 questions) and the Moto test (10), beside
  the string baseline (90.9%, 8/10) and similarity (82.6%, 8/10). Reported only; M7 decides what the executor
  uses.
- Reports under `ml/reports/`: `fixed-head.md`, `decision-model.md` (with the bar table and the node table) and
  `state.md`.

## 6. Running on Colab

- With the `colab` CLI: `colab new -s unstuk-m5 --gpu T4`; upload a tarball of `ml/`, `catalog/`, `data/clean`,
  `data/state` and `data/nodes`; `colab exec` the training entry point; `colab download` the settings and
  checkpoints into `ml/checkpoints/` (gitignored); `colab stop`. `data/test` and `data/real` never go to the VM,
  so training can't read them by mistake.
- If no GPU is granted, bge-small fine-tunes on this machine's CPU (8 cores), more slowly, with the same grid.
- `torch` and `transformers` go in a `train` dependency group (CPU wheels locally), so M4's commands and tests
  don't need them.

## 7. Decisions (approved 2026-10-05)

| # | Question | Chosen | Rejected |
| --- | --- | --- | --- |
| 1 | Out of scope | A Noul head | An out-of-scope option text (M4 finding 5); a learned "none" option vector, which doesn't fit the Choice / Noul contract |
| 2 | Choice head | Attention head, with cosine as a dev ablation | A cross-encoder (complaint and option in one pass): one forward pass per option, too slow for node labels at runtime |
| 3 | Zero-shot guard | Leave-intents-out folds on train and dev | Tuning on the held-out test lines, which breaks invariant 9; no guard, which lets fine-tuning overfit 12 option strings |
| 4 | Backbones | bge-small only | Comparing MiniLM and Ettin now; revisit only if bge-small misses the bar |
| 5 | Node labels | Trained jointly, reported only | Leaving them out: fewer option wordings to learn from, and the shared Choice head goes untested |
| 6 | Score head | Left out | Building it on invented urgency labels |
| 7 | Training stack | PyTorch and `transformers` on Colab | `sentence-transformers`' trainer, which hides the heads this milestone is about |

## 8. Not in M5

- Brier / RLCD-lite training, distillation and int8 (M6).
- The gate's thresholds and vague lines (M6).
- ONNX export and the Kotlin `decide` API (M7).
- Real user messages (M8).
- Guide §5's `wifi_no_load` question stays open: changing it would relabel frozen test lines.

## Steps

One commit each, or a few where a step is large. Each step ends with a short "what to study" note.

1. **This spec**, and a note in `AGENTS.md` that training runs through the `colab` CLI.
   *Learn:* why a zero-shot guard needs intents held out of training, not just lines.
2. **Training examples:** option sampling, typo noise, state rendering, leave-intents-out folds. Pure Python,
   tested.
   *Learn:* negative sampling, and why the option set is redrawn each epoch.
3. **Model:** backbone, Choice and Noul heads; CPU tests for shapes, option-order invariance and masking.
   *Learn:* cross-attention and set attention, and permutation invariance.
4. **Training loop and Colab runner:** a local smoke run on a few lines, then one Colab run end to end.
   *Learn:* fine-tuning learning rates, and reproducibility on a GPU.
5. **Fixed-head rung:** tune on Colab, commit the settings, score once, report.
   *Learn:* what fine-tuning changes compared with a linear probe.
6. **Decision model tuning:** grid and folds on Colab, commit the settings.
   *Learn:* model selection under a constraint.
7. **State in or out** (section 4).
   *Learn:* conditioning on structured context.
8. **Decision model scored once**, the bar check and the node table.
   *Learn:* reading several paired intervals at once.
9. **Results:** `m5-results.md` and a plain-language summary.
   *Learn:* writing up a mixed result honestly.
