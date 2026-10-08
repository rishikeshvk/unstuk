# M7 results: On-device inference

2026-10-08 · Status: **done.** Spec: [m7-spec.md](m7-spec.md). Plain-language summary:
[m7-summary.md](m7-summary.md). Report: [ml/reports/quantized.md](../ml/reports/quantized.md).

M7 asked whether the int8 model, running on the phone, decides like M6's float model at a size and speed fit to
ship. **It does.** With every weight in 8 bits (U8U8, 35.0 MB), it is not worse than float on any pre-registered
test row, and on the Moto Edge 30 it gives Python's top answer on all 1,144 dev lines, in 9.6 ms at the median.
The release APK is 71.4 MB, inside the 100 MB budget and above the 40–60 MB target; ONNX Runtime's 33 MB library is
now the largest lever. Getting there took a correction: the first int8 check measured batched x86 answers the
phone never gives.

## The shipped graph against M6's float model, on the test

All 602 frozen test lines, the second scoring (see [the correction](#the-correction)). Both through ONNX Runtime,
one line at a time, every catalog intent offered, behind M6's gate lines. Paired 95% bootstrap intervals.

| Metric | Float | **int8 (U8U8)** | Difference | Must | Passes |
| --- | --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 89.5% | 89.3% | −1.9 to +1.5 | not be worse | yes |
| Confident and wrong | 3.0% | 3.0% | −0.5 to +0.5 | not be worse | yes |
| Expected calibration error | 2.6% | 3.6% | −0.9 to +2.3 | not be worse | yes |
| Out-of-scope recall | 91.5% | 92.1% | −1.3 to +2.7 | not be worse | yes |
| Vague lines asked about or declined (28) | 17.9% | 17.9% | 0 to 0 | reported | |
| Macro-F1 | 89.8% | 90.0% | −1.5 to +1.9 | reported | |
| Held-out intents | 76.2% | 77.5% | −4.2 to +7.0 | reported | |

### What the gate would do

| Lines | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- |
| in scope (410) | 333 | 11 | 45 | 21 |
| out of scope (164) | 8 | 0 | 5 | 151 |
| vague (28) | 19 | 4 | 2 | 3 |

## Choosing on dev

Every graph scored one line at a time. The tries ran in the spec's order and stopped at the first pass.

| Graph | 8-bit ops | Size | Top-1 agreement | Macro-F1 | ECE | Gate outcomes | Passes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **`decision.int8.onnx`** | MatMul, Gather | **35.0 MB** | 99.30% | −0.07 | −0.15 | 98.16% | **yes** |

Bars: top-1 at least 99%, macro-F1 within 1 point, ECE at most 1 point worse, gate outcomes at least 98%.
Temperatures refitted on dev: 0.8405 (Choice), 1.4864 (Noul). M6's rule would move the lines to automatic 0.65,
clarify below 0.3, margin 0.4; the app keeps M6's 0.75, 0.7 and 0 (spec correction, point 3).

## On the phone

Moto Edge 30, Android 14, release-like debug build, the instrumented test over all 1,144 dev lines.

| Measure | Value |
| --- | --- |
| Same top answer as Python | 1,144 of 1,144 |
| Same gate outcome as Python | 99.65% (bar: 99%) |
| Largest probability gap: median, 95th percentile, max | 1.5e-7, 1.9e-3, 0.13 |
| Model load (session from the mapped APK) | 375 ms |
| Decide: median, 95th percentile, max | 9.6 ms, 18.0 ms, 53.9 ms |
| Native heap added by the model | +48.7 MB |
| App with the model warm: total PSS (native heap, APK mappings) | 242 MB (61 MB, 85 MB) |
| Cold launch to first frame (`am start -W`) | 1.8 s, with the model loading in the background |

### Size

| Component | In the release APK |
| --- | --- |
| `decision.onnx` (U8U8, stored) | 34.97 MB |
| `libonnxruntime.so` (arm64, stored) | 32.99 MB |
| Dex | 2.90 MB |
| Resources, vocabulary, option vectors, catalog, JNI | 0.53 MB |
| **Total** | **71.4 MB** |

Against plan.md's budget: the model is at the low end of its 25–35 MB line; the runtime is over its 5–20 MB line.
A reduced-operator ONNX Runtime build is the next lever.

### End to end

`e2e.sh` on the Moto, the 17 cases that don't cut the host's connection (airplane mode, mobile data and Data
Saver were left out): **14 pass, 0 false successes.** Every fix that ran was verified by a fresh read.

| Case | Expected | Got | Why |
| --- | --- | --- | --- |
| `app_permission` | all clear | decline | "Camera not working in Zoom": out of scope at 0.73. A model miss |
| `gate_confirm` | confirm | no result | wrong_time at 0.94, so the fix ran and waited for a tap the case never sends; the broadcast hit Android's 60 s limit |
| `gate_clarify` | clarify | all clear | "Dark colours and small": colours_wrong at 0.75 |

The `gate_*` cases were written to land in the keyword matcher's bands. The model is surer on both, so they no
longer test the confirm and clarify paths; `TriageTest` still does, at the unit level.

## The correction

The first phone run disagreed with Python on 8 dev lines, by up to 0.48. Two causes, found before anything was
rerun and recorded in the [spec](m7-spec.md#correction-2026-10-08-one-line-at-a-time-and-u8u8):

1. **Batching.** Dynamic int8 scales each activation by its whole batch, padding included, so a line's answer
   depended on the 63 lines beside it. Scored one line at a time, as the app runs, the first chosen graph
   (int8 weights, embeddings in float) agrees with float on 98.78% of dev lines, under the 99% bar it had passed
   at 99.39%.
2. **The CPU.** This machine (i5-8250U: AVX2, no VNNI) computes uint8 × int8 products with an instruction that can
   saturate; the phone's ARM CPU doesn't. Against float on dev, x86 agreed on 98.78% and the phone on 99.04%, and
   they disagreed with each other on 1.3% of lines. With uint8 weights (U8U8) both compute exactly, and the phone
   then matched Python's top answer on every line.

Activations are still rounded to 8 bits per call, so a tiny float difference between CPUs can flip one rounding
step: the spec's "every probability within 1e-3" can't hold for dynamic int8, and was replaced before the rerun.

## Findings

1. **The graph you score must be run the way the app runs it.** Batch composition changed int8 answers, and the
   batched dev check passed a graph that fails one line at a time. Parity on the phone is what caught it.
2. **Integer kernels differ by CPU.** The same int8 graph gave different answers on x86 and ARM. U8U8 made them
   agree; a dev machine without VNNI is otherwise not a faithful stand-in for the phone.
3. **Done right, full int8 costs nothing measurable.** Every row is within its interval of float, at a quarter of
   the size, and the embedding tables quantize fine once the arithmetic is exact.
4. **Re-tuning the gate on a small dev set chases noise.** On the first graph it moved automatic from 0.75 to
   0.6 on about three lines, and confident-and-wrong rose on the test (4.2% against 3.0%). On the second it would
   move to 0.65 with clarify at 0.3. The app keeps M6's lines.
5. **Speed is not the problem; the runtime's size is.** 9.6 ms per decision and a 375 ms load, but ONNX Runtime
   is as large as the model.
6. **The keyword-shaped e2e cases need new complaints.** A calibrated model is surer than the matcher on the
   complaints written to sit in its middle bands.

## What changed from the spec

| Change | Why |
| --- | --- |
| Scoring one line at a time; U8U8 weights; the int8 check and the test rerun | The correction above, written before the rerun |
| The app keeps M6's gate lines; re-tuning is reported, not applied | After the first test scoring (decided then) and pre-registered for the rerun |
| Phone bar: same top answer everywhere, gate outcome on 99%, gaps reported | 1e-3 can't hold for dynamic int8 across CPUs |
| The tokenizer fixture (4.9 MB) and vocabulary are generated and gitignored | Too large to review in git; the test names the command when they are missing |
| No `choose(question, options)` in Kotlin | Nothing calls it yet (AGENTS.md: no speculative code); the graph already encodes any option |
| The head arithmetic is checked against Python by the phone test, not a JVM fixture | The phone test runs the whole path; JVM tests cover the formula by hand |
| The app leaves out held-out intents' checks and `always` from the state text | Training never showed them (invariant 9); the manifest lists the checks it may read |
| The Kotlin keyword matcher was deleted; its fixture moved to `ml/tests` | The Python baseline still reads it |

## Every test scoring

| When (IST) | What | Settings | Note |
| --- | --- | --- | --- |
| 2026-10-08, report committed 19:51 | int8 weights, embeddings in float, batched on x86, re-tuned lines | `83ddabe` | Confident and wrong worse (4.2% against 3.0%). Superseded: batched x86 answers aren't the app's |
| 2026-10-08, report committed 21:29 | **U8U8, every weight, one line at a time, M6's lines** | `c0a2160`, `ml/settings/quantized.json` | Not worse on every row. Second scoring, after the correction |

After the first scoring, the app's lines went back to M6's; nothing else was changed after a test score was seen.

## Open for later

- **Size:** a reduced-operator ONNX Runtime build, or LiteRT if that can't shrink it enough.
- **e2e:** new complaints for `gate_confirm` and `gate_clarify` that land in the model's middle bands, and a case
  that taps the date panel.
- **M8:** real messages decide whether the neural model ships (invariant 10), with the decision's probabilities
  and time already in the local trace.
