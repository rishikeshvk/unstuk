# M7 spec: On-device inference

2026-10-08 · Status: **approved.** Background: [plan.md](plan.md), roadmap step 7, and
[m6-results.md](m6-results.md).

M7 answers one question: **does the int8 model, running on the phone, decide like M6's float model, at a size and
speed fit to ship?** Like it means the same answers on dev, a calibration that holds, and no safety metric worse
on the test.

It is done when the int8 graph passes the dev checks written here first, is scored once on the 602 frozen test
lines against M6's float model by paired bootstrap, the app decides with it on the Moto with the same
probabilities as Python, and `m7-results.md` records size, speed and parity.

```text
complaint + state text ─► WordPiece (Kotlin) ─► int8 ONNX graph ─► CLS vector (384) + Noul logit
catalog option vectors (an asset, made at export) ─────────────────────┘
        Kotlin: cosine × scale ÷ T → softmax over options; sigmoid(Noul ÷ T) → p(out of scope)
```

M6 chose the cosine head with Noul reading the complaint alone, so only the encoder is heavy. Choice is a cosine
between the complaint's vector and each option's, times a learned scale; the intents share `1 − p(out of scope)`
in proportion to Choice, as `decision_scoring.scored` does.

## 1. Export

- `unstuk-export` loads M6's checkpoint through the sha256-checked loader that scored the test
  (`ml/settings/calibrated.json`), and exports one graph: `(input_ids, attention_mask, token_type_ids) →
  (vector [batch, 384], noul_logit [batch])`, where `vector` is the CLS state scaled to length 1.
- The same graph encodes option texts, with its Noul output ignored. One set of weights serves Choice over the
  catalog's options now and runtime options, such as node labels, later.
- **Parity:** float ONNX against PyTorch on dev, on CPU. Choice and Noul logits within 1e-4.

## 2. int8

- ONNX Runtime dynamic quantization: int8 weights for MatMul and Gather, per channel, so the embedding table
  (11.7M of 33M parameters) shrinks too. Activations stay float and are quantized per call.
- The catalog's option vectors are computed **from the int8 graph** and written beside it, so Choice compares
  vectors from one model.
- Temperatures are refitted on dev for the int8 model by log-loss (`fit_temperatures`, as in M5 and M6); the
  learned scale is read from the checkpoint.

## 3. The dev check, written before any int8 run

Against M6's float model, both with their own temperatures, on dev:

| Check | Must |
| --- | --- |
| Top-1 agreement, every dev line | at least 99% |
| Macro-F1 | within 1 point |
| Expected calibration error | at most 1 point worse |
| Gate outcome agreement (automatic, confirm, clarify, decline) under `catalog/gate.json` | at least 98% |

- **The gate's lines:** M6's tuning rule (`gate_tuning.py`) is re-run on the int8 model's dev scores. If it picks
  different lines, `gate.json` changes, since the app ships the int8 model, and the change is recorded.
- **Stop rule:** if dynamic int8 fails, one try with the embedding table left in float. If that fails too, M7 ships
  the float graph in fp16 and records why. No further rounds.
- The choice is recorded in `ml/settings/quantized.json`: the graph's sha256, temperatures, scale, lines and the
  commit.

## 4. Scoring the test once

- Locally on CPU, from `quantized.json` and `catalog/gate.json`.
- **Against M6's float model, paired bootstrap, pre-registered:**

  | Metric | Must |
  | --- | --- |
  | In-scope accuracy | not be worse |
  | Confident and wrong | not be worse |
  | Expected calibration error | not be worse |
  | Out-of-scope recall | not be worse |
  | Vague lines asked about or declined, macro-F1, held-out intents | reported |

  "Not worse" uses M4's rule: the interval of the difference must not lie wholly on the bad side.
- **Report:** `ml/reports/quantized.md`, with the comparison, the gate's outcome table, and file sizes of the
  float, fp16 and int8 graphs.

## 5. Getting the model into the APK

- `unstuk-export` writes the int8 graph and the option vectors to `android/app/src/main/assets/model/`. Both are
  gitignored.
- Beside them, a committed `model.json` holds their sha256s, the sha256 of the `catalog/intents.json` the vectors
  were made from, the temperatures, the scale and the token limit (128, as `decision_batch.MAX_TOKENS`).
- A Gradle task runs before `preBuild` and fails, naming `uv run unstuk-export`, when a file is missing, a hash
  differs, or the catalog changed since export.
- The model asset is stored uncompressed, so it can be read without inflating a copy.

## 6. The tokenizer in Kotlin

- A hand-written BERT WordPiece, as bge's `tokenizer.json` defines it: lowercase, strip accents, split on
  whitespace and punctuation, greedy longest match with `##` pieces, `[CLS] a [SEP] b [SEP]` with type ids 0 and
  1, truncation to 128 tokens longest-first. The vocabulary is read from `tokenizer.json`.
- **Parity fixture:** Python `tokenizers` encodes every train, dev, vague, state and node text, with and without
  their state, plus a typo'd copy of each (`typos.py`). The ids are committed as a fixture; a Kotlin unit test
  requires identical ids. The test split and `data/real/` are never read (invariant 9).

## 7. Runtime

- ONNX Runtime Android from the version catalog, arm64-v8a only (`abiFilters`), as the Moto Edge 30 and current
  phones are.
- One session, created once on a background dispatcher at app start. The first complaint waits for it if needed.
- A reduced-operator ONNX Runtime build is a lever to pull only if the size waterfall needs it.

## 8. The Kotlin API

- `decide/DecisionModel.kt`: `decide(complaint, state): IntentChoice`, where `IntentChoice` now carries
  `outOfScope` beside the intents' probabilities, and `choose(question, options): List<Double>` for options given
  at runtime.
- **State text:** the findings of the checks that hold, sorted by check id and joined by spaces, as
  `training_examples.render_state` reads the sorted state of `data/state`. No state means the complaint is encoded
  alone, as in training.
- `ComplaintFlow` reads the device state **before** deciding, and the model replaces `KeywordMatcher`, which is
  deleted from Kotlin. `catalog/keywords.json` stays: the ML keyword baseline reads it.
- `Triage` declines when out of scope is the top answer, as `evaluate.Scored.outcome` does, and otherwise passes
  through the gate as now.
- The trace records the decision's probabilities and its time in milliseconds; never the complaint text.

## 9. On the phone

- **Parity:** an instrumented test scores every dev line on the Moto and compares with Python's int8
  probabilities: the same top answer on every line and every probability within 1e-3.
- **Measured on the Moto:** release APK size by component (a size waterfall against plan.md's budget), session
  load time from a cold start, decide latency p50 and p95 over dev, and peak memory.
- The Moto is asked for when this step starts; no emulator.

## 10. Decisions

| # | Question | Proposed | Rejected |
| --- | --- | --- | --- |
| 1 | What the graph holds | The encoder and Noul; cosine and softmax in Kotlin | The whole head in the graph with option vectors as input: a second graph to encode options would double the weights |
| 2 | Quantization | Dynamic int8, weights per channel | Static QDQ with a calibration set: usually worse for BERT-class encoders on CPU, and needs its own data |
| 3 | Model into the APK | An export step with a pinned sha256 and a Gradle check | Git LFS: not installed, quota-limited on GitHub, and the checkpoint it derives from isn't in git, so a clone still couldn't build |
| 4 | Tokenizer | Hand-written WordPiece with a parity fixture | ONNX Runtime Extensions' tokenizer op (another native library and custom ops); HF tokenizers over JNI (a Rust toolchain in the build) |
| 5 | Runtime | ONNX Runtime Android | LiteRT: a second export path (PyTorch to TFLite) with its own numerics, when the pipeline already speaks ONNX |
| 6 | Node matching through the model | Left out: the API supports it, selectors stay | Wiring it now: string matching beat frozen similarity on dev (90.9% against 82.6%), and the test has 10 node questions |
| 7 | The keyword matcher | Deleted from the app | Kept as a fallback: two decision paths, one uncalibrated, for a model that ships inside the APK |

## 11. Not in M7

- Node matching and guide cards through the model. Guides are chosen by the diagnoser, not asked of the model.
- A hand-written forward pass (stretch goal).
- Real user messages (M8).

## Steps

One commit each, or a few where a step is large. Each step ends with a short "what to study" note.

1. **This spec**, and a plan.md answer to the model-file question.
   *Learn:* why the graph that ships, not the training model, is the one to measure.
2. **Export:** the float ONNX graph and its parity test against PyTorch.
   *Learn:* ONNX tracing, dynamic axes and opsets.
3. **int8:** quantization, option vectors, refitted temperatures, the dev check and the lines.
   *Learn:* affine quantization, scales and zero points, and why per-channel matters.
4. **Score the test once:** `quantized.md`.
   *Learn:* why quantization noise can move calibration more than accuracy.
5. **Into the APK:** the manifest, the Gradle check and ONNX Runtime.
   *Learn:* APK asset compression and memory-mapping.
6. **Tokenizer:** Kotlin WordPiece and its parity fixture.
   *Learn:* WordPiece and why tokenizer drift silently breaks a model.
7. **Decide:** `DecisionModel.kt`, the head arithmetic, `ComplaintFlow` and `Triage`.
   *Learn:* keeping one calibrated number intact from Python to Kotlin.
8. **On the phone:** parity and measurements on the Moto.
   *Learn:* cold-start costs and latency percentiles on mobile CPUs.
9. **Results and summary:** `m7-results.md`, `m7-summary.md`.
