# M3 results: Data

2026-10-05 · Status: **data built; phone run pending.** Spec: [m3-spec.md](m3-spec.md). Plain-language summary:
[m3-summary.md](m3-summary.md). Data card: [data/CARD.md](../data/CARD.md)

M3 asked whether we can build data that teaches a small model to map plain complaints to the right fix, and a test
honest enough to tell whether that model beats the keyword matcher. The data and the test exist; the keyword matcher
now has a score to beat. The Moto label dumps (node-label test) and the Kotlin-side tests wait for one run on the
phone.

## Targets

| Metric | Target | Result |
| --- | --- | --- |
| Clean training phrasings | ≥ 300 per trained intent, ≥ 1000 out of scope | **Met:** 409–480 per intent, 1,717 out of scope (train and dev) |
| Proxy test set | ≥ 25 per intent, ≥ 150 out of scope, every slice ≥ 30 | **Mostly met:** ≥ 25 per intent counting two-problem lines (three have 24 single-label lines), 164 out of scope, every slice ≥ 30 except `vague` (28) |
| Test leakage | 0 near duplicates | **Met:** 52 training lines at similarity ≥ 0.8 to a test line were removed |
| Hand label audit | ≥ 95% agreement on 200 lines | **Met:** 200/200, Cohen's kappa 1.00 (blind second labeller) |
| Node labels | Moto dumps for every A-rung screen; AOSP and selector variants for every target | **Half met:** 960 training and dev questions; Moto dumps pending the phone run |
| Keyword baseline | Scored with 95% intervals, per slice | **Met:** below |

## The keyword baseline: the bar to beat

M2's matcher, ported to Python (a shared fixture keeps the two versions identical), scored on all 602 frozen test
lines. Full report: [ml/reports/keyword-baseline.md](../ml/reports/keyword-baseline.md).

| Metric | Value | 95% interval |
| --- | --- | --- |
| Top-1 accuracy, in scope | 40.2% | 35.5–44.6% |
| Macro-F1 | 50.6% | 45.4–54.6% |
| Out-of-scope recall / precision | 81.1% / 38.6% | 75.2–87.0% / 33.9–43.6% |
| **Confident and wrong** (would run a fix automatically on the wrong problem) | **8.7%** | 6.5–10.9% |
| Expected calibration error | 22.6% | 18.1–28.7% |

| Slice | Accuracy |
| --- | --- |
| plain | 74.5% |
| paraphrase | 23.2% |
| typo | 24.7% |
| negation | 33.3% |
| long story | 38.5% |
| Indian English | 41.3% |

Error analysis:
- **Most mistakes are declines.** 212 of 410 in-scope lines got no keyword at all: "Calls are coming in but the
  phone stays quiet", "The display disappears before I finish reading". Rules only know the words we typed.
- **The dangerous mistakes are confident ones.** 8.7% of clear lines would run a fix by themselves on the wrong
  problem, because one keyword hit always means probability 1.0. 25 of 164 out-of-scope lines would trigger an
  automatic fix.
- **The confidence means nothing.** An ECE of 22.6% says a "100% sure" answer is right far less often; the gate
  can't use these numbers.
- **The writer matters.** ChatGPT's plainer lines score 61%, Gemini's 44%: the matcher rewards wording close to our
  keyword list, which is exactly what real users won't use.

These are the failures spec section 1 predicted, now measured. A model must beat them on the same test, especially on
paraphrase, typo and the confident-and-wrong rate (invariant 10).

## The data

| Part | Size | Notes |
| --- | --- | --- |
| Raw pool | 7,090 lines | 40 persona batches (4,800), 10 out-of-scope batches (1,200), 336 contrast pairs (672), 300 Mobile Actions requests, 118 seeds |
| Clean | 5,833 train, 1,095 dev | Dev is 9 whole batches plus the Mobile Actions eval rows, covering every grid value |
| Proxy test | 602 lines, frozen | ChatGPT 237, Gemini 265, context-free Claude 100 |
| State slice | 71 texts, 117 train and 47 test records | Four of five pairs; see the finding below |
| Node labels | 828 train, 132 dev questions | Dev is one maker (Xiaomi) the model won't have seen |

Cleaning: 49 exact and 58 same-label near duplicates, 52 lines close to the test and 3 guide examples removed. Two
runs of the pipeline give byte-identical output.

## Findings

1. **Generation must be isolated from the test.** This session read every test line while reviewing it, so no
   training line was written here: every batch came from a fresh agent that read only its own prompt, confirmed in
   all 56 generation transcripts.
2. **Pilots pay.** The first training pilot echoed the prompt's own definitions ("full bars", "scrolling needs two
   fingers"); prompt v2 cut "full bars" from 1.7% of lines to 0.5% before the other 38 batches were written.
3. **A blind labeller needs blind keys.** The first review file's IDs named the label (`seed-phone_not_ringing-08`),
   and the first state-slice file listed texts in pair order. Both were fixed before labelling.
4. **A perfect audit is a warning too.** 200/200 agreement means the training lines are unambiguous, so easier than
   the test; the test's hard slices carry the real measurement.
5. **The guide settles some complaints by default.** Rule §5 sends "Wi-Fi not working" (without "connected") to
   `no_internet`, so the state slice's internet pairs nearly vanished, though on a real phone the device state
   could show the other cause. Open for M5: keep §5, or call such complaints vague.
6. **Two-way ties are never clarified.** The risk gate clarifies only below 0.5, so a 50/50 tie is confirmed. M6
   should decide whether that is intended.

## What changed from the spec

| Change | Why |
| --- | --- |
| No per-intent cap after cleaning | The data was generated balanced; the gap comes from contrast pairs |
| Mobile Actions: 300 out-of-scope requests from five tools | None of its tools is a symptom we fix; Wi-Fi settings and calendar requests left out |
| Blind second labeller for review and audit, instead of a person | Chosen in planning; it makes agreement a measurement between independent labellers |
| `ids.lock` checked by a Kotlin test, not a Python one | `ml/` didn't exist yet in step 2 |
| The state slice keeps only texts a blind labeller left open | So it measures state, not words |

## Not done in M3 (pending the phone run)

- Moto label dumps and the node-label test set, with the baseline's score on it.
- The Kotlin tests written in M3 (`ids.lock`, keyword parity) and the label dumper have only been checked with
  ktlint: this environment has no Android SDK. They compile and run in the phone stretch.
