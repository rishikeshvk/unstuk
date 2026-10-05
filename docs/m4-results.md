# M4 results: Baselines

2026-10-05 · Status: **done.** Spec: [m4-spec.md](m4-spec.md). Plain-language summary:
[m4-summary.md](m4-summary.md). Reports: [ml/reports/](../ml/reports/).

M4 asked whether a cheap learned classifier beats the keyword matcher on the frozen proxy test, and by how much.
It does, by a wide margin: TF-IDF + logistic regression raises in-scope accuracy from 40.2% to 64.9% and cuts the
confident-and-wrong rate from 8.7% to 1.9%. Above that, no single rung wins everywhere. The frozen encoder is more
accurate but less safe than TF-IDF, and zero-shot similarity names held-out intents it never trained on but can't
say no. So M5 has to clear a bar set per metric by whichever rung is best at it.

## The ladder on the test set

All 602 frozen test lines, each rung scored once after its settings were frozen on dev. Intervals are 95%
bootstrap intervals.

| Metric | Keyword | TF-IDF + LR | Frozen bge-small + LR | Zero-shot bge-small |
| --- | --- | --- | --- | --- |
| Top-1 accuracy, in scope | 40.2% | 64.9% (60.4–69.7) | 70.0% (65.5–74.3) | **73.9%** (69.2–77.9) |
| Macro-F1 | 50.6% | 68.7% (65.3–71.8) | **69.1%** (66.0–71.8) | 65.6% (61.2–69.1) |
| Out-of-scope recall | 81.1% | **95.1%** (91.6–98.2) | 93.3% (89.4–97.0) | 33.5% (26.0–40.9) |
| Out-of-scope precision | 38.6% | 57.8% | **69.9%** | 68.8% |
| **Confident and wrong** | 8.7% | **1.9%** (0.9–3.1) | 3.8% (2.3–5.6) | 3.8% (2.3–5.4) |
| Vague lines answered with a question or decline | **67.9%** | 32.1% | 32.1% | 39.3% |
| Expected calibration error | 22.6% | 17.4% (raw 13.9%) | 12.3% (raw 12.8%) | **6.1%** (4.4–10.0) |
| Held-out intents | 35.0%¹ | 6.2%² | 3.8%² | **93.8%** (87.6–98.7) |

¹ Not zero-shot: the keyword matcher has hand-written rules for them.
² Fixed-head rungs have no output for held-out intents. These are the two-problem lines whose other problem is
trained.

Reports: [keyword-baseline.md](../ml/reports/keyword-baseline.md), [tfidf.md](../ml/reports/tfidf.md),
[encoder.md](../ml/reports/encoder.md), [zero-shot.md](../ml/reports/zero-shot.md).

### Each rung against the one below (paired bootstrap, spec section 3)

| Comparison | In-scope accuracy | Macro-F1 | Confident and wrong | Beats? |
| --- | --- | --- | --- | --- |
| TF-IDF − keyword | +24.6 (+19.0 to +30.4) | +18.2 (+14.0 to +23.2) | −6.8 (−9.2 to −4.5) | **Yes** |
| Encoder − TF-IDF | +5.1 (+1.3 to +8.8) | +0.4 (−2.4 to +3.4) | +1.9 (+0.3 to +3.5) | **No** |

The encoder is surely more accurate on in-scope lines, but not on macro-F1, and it is surely more often confident
and wrong. By the rule fixed before any score, it does not beat TF-IDF. Zero-shot is not a rung on this ladder.
Decision 3 added it as the bar for held-out intents.

### By slice

Accuracy on clear lines. The best rung per row is in bold.

| Slice (lines) | Keyword | TF-IDF | Encoder | Zero-shot |
| --- | --- | --- | --- | --- |
| plain (192) | 74.5% | 83.3% | **87.0%** | 68.2% |
| paraphrase (82) | 23.2% | 57.3% | 67.1% | **72.0%** |
| typo (73) | 24.7% | **64.4%** | 61.6% | 61.6% |
| negation (39) | 33.3% | 59.0% | 64.1% | **71.8%** |
| long story (39) | 38.5% | 59.0% | **71.8%** | 66.7% |
| Indian English (46) | 41.3% | 60.9% | 67.4% | **82.6%** |
| collision (44) | 52.3% | 86.4% | **88.6%** | 6.8% |
| out of scope, near (32) | 81.2% | **93.8%** | 81.2% | 28.1% |
| multi (33) | 75.8% | **93.9%** | 81.8% | 84.8% |
| writer: Gemini (255) | 43.5% | 62.4% | **70.6%** | 52.5% |

### What the gate would do

| Lines | Rung | Automatic | Confirm | Clarify | Decline |
| --- | --- | --- | --- | --- | --- |
| in scope (410) | Keyword | 170 | 28 | 0 | 212 |
| | TF-IDF | 235 | 47 | 14 | 114 |
| | Encoder | 262 | 67 | 15 | 66 |
| | Zero-shot | 167 | 129 | 89 | 25 |
| out of scope (164) | Keyword | 25 | 6 | 0 | 133 |
| | TF-IDF | 5 | 3 | 0 | 156 |
| | Encoder | 6 | 5 | 0 | 153 |
| | Zero-shot | 14 | 32 | 63 | 55 |

## The bar for M5 (decided 2026-10-05)

No rung is best on every metric, so the bar is set per metric by the best rung, using the same paired bootstrap.
The rule mirrors spec section 3: M5 must be **surely better** on accuracy, and **not surely worse** on each guard
rail.

| Metric | Bar | Set by | M5 must |
| --- | --- | --- | --- |
| In-scope accuracy | 73.9% | Zero-shot | be better: the paired interval lies above 0 |
| Macro-F1 | 69.1% | Encoder | be better: the paired interval lies above 0 |
| **Confident and wrong** | 1.9% | TF-IDF | not be worse: the interval doesn't lie above 0 |
| Out-of-scope recall | 95.1% | TF-IDF | not be worse: the interval doesn't lie below 0 |
| Held-out intents | 93.8% | Zero-shot | not be worse: the interval doesn't lie below 0 |
| Expected calibration error | 6.1% | Zero-shot | not be worse: the interval doesn't lie above 0 |

Rejected: taking the spec's ladder literally, which would make TF-IDF, the last rung that passed `beats`, the only bar.
That is simpler, but M5's option-text heads would then never be measured against zero-shot's 93.8% on held-out
intents, the bar decision 3 was approved to create. The vague-line rate is not in the bar: answering unclear
complaints with a question is the gate's job, and M6 owns it. This is still the proxy test. Invariant 10's real
test set comes in M8.

## Node labels: similarity doesn't beat string matching

"Which item on the screen is the switch for X?": frozen bge-small picks the option closest in meaning to the question,
beside M3's string baseline, on the same questions. Report: [node-similarity.md](../ml/reports/node-similarity.md).

| Method | Dev (132, Xiaomi wording) | Moto test (10) |
| --- | --- | --- |
| String baseline | 90.9% (85.6–95.5) | 8/10, or 9/10 with tile state cut |
| Similarity | 82.6% (76.5–88.6) | 8/10, with or without the cut |

Similarity finds "Wi-Fi, Off" where exact matching finds nothing, but it picks "Screen reader" over "TalkBack":
the category sits closer in meaning than the product's name. Labels on a screen are names more than descriptions,
and string matching suits names. Both miss DND's "Turn off now", the one place where the answer is an action rather
than the switch's label.

## Findings

1. **Learning from examples beats a word list by a wide margin.** TF-IDF more than doubles paraphrase and typo
   accuracy and cuts automatic wrong fixes by three-quarters, with eight fits that take seconds each.
2. **Meaning and spelling pull in opposite directions.** The frozen encoder wins on paraphrase, negation and long
   stories. Character n-grams win on typos ("cnnectd to home but nt wroking") and on out-of-scope lines that borrow
   our words, because a misspelt word breaks into sub-word tokens that carry no meaning for the encoder.
3. **Higher accuracy can come with more risk.** The encoder answers 262 in-scope lines automatically against
   TF-IDF's 235, and more of those are wrong. A rule that looked at accuracy alone would have picked it.
4. **Dev is far easier than the test.** Dev macro-F1 was 96–98% for every learned rung; the test gives 66–69%.
   A temperature fitted on dev sharpened TF-IDF (T = 0.78) and made its test calibration worse (ECE 13.9% → 17.4%).
   The encoder's dev temperature was about 1, and it barely moved.
5. **Zero-shot knows what it was never shown, but can't say no.** 93.8% on held-out intents with no training. But
   one out-of-scope sentence can't sit near everything that isn't a fix: "My ear is ringing all day" became
   `cant_hear_call`, and the collision slice scores 6.8%. The out-of-scope wording alone moved dev macro-F1 by
   2.5 points.
6. **No learned rung handles vague lines.** The keyword matcher "handled" 68% of them by declining what it didn't
   recognise. The learned rungs answer about two-thirds of them instead of asking. This is for the gate in M6.
7. **The writer still matters.** Gemini's lines are the hardest for every rung (43–71%), 12–21 points below
   ChatGPT's, so wording unlike the training style costs that much. Real users will differ more.
8. **Grid edges need a rule fixed in advance.** TF-IDF's best `C` sat at the grid's top twice; for the encoder, a
   rule written before any score extended the grid until the winner was inside.

## What changed from the spec

| Change | Why |
| --- | --- |
| No fastText (decision 2) | Archived in March 2024 with one wheel; `char_wb` n-grams cover typos |
| Zero-shot rung and node-label similarity added (decisions 3 and 4) | The only bar for held-out intents; meaning versus string matching on screens |
| 13 classes, not 16 | The catalog has 15 intents, 3 held out: 12 trained plus `out_of_scope` |
| TF-IDF grid extended to `C` 30 and 100 | The dev winner sat at `C` = 10, the old edge. Decided on dev, before any test score |
| Grid-edge rule for the encoder | Written before any encoder score, so it couldn't be bent to fit a result |
| "Fixed and introduced" compares with the rung below | Against the keyword matcher it would repeat what TF-IDF already fixed |
| Held-out "0% by construction" corrected | 5 held-out test lines also name a trained problem |
| The test set loads only while it matches `test.lock` | Every scoring checks the lock first |
| `label_issues` runs cleanlab in one process | Forking after onnxruntime loads can deadlock; results are identical |

## Every test scoring

| When (2026-10-05, IST) | What | Settings | Note |
| --- | --- | --- | --- |
| During step 2 | Keyword report regenerated | — | Byte-identical to M3's, a check of the shared report |
| 19:10 | **TF-IDF, scored** | `a16457b` (sha256 `13b0d2ee…`) | The one scoring |
| After 19:10 | TF-IDF regenerated | same | Only the held-out note's wording changed; scores identical |
| Step 5 | TF-IDF regenerated | same | Byte-identical, a check of the shared rung protocol |
| 19:54 | **Encoder, scored** | `24066cb` (sha256 `9b845b58…`) | The one scoring |
| Step 6 | Encoder regenerated | same | Byte-identical, a check after moving the embedding cache |
| 20:13 | **Zero-shot, scored** | `45817ac` (sha256 `cd6f9a11…`) | The one scoring |
| 20:14 | **Node-label similarity, scored** | none to tune | Dev and the 10 Moto questions |

No setting was changed after its test score was seen.

## Open for later

- **M5:** out-of-scope needs its own head, not an option text (finding 5); typo robustness (finding 2); and the
  bar above.
- **M6:** vague lines (finding 6), calibration on harder lines than dev (finding 4), and the risk gate's 50/50 tie,
  which it confirms instead of clarifying.
- **Guide §5** labels "Wi-Fi not working" as `no_internet` even where the device could show `wifi_no_load`.
  Zero-shot's six `wifi_no_load → no_internet` mistakes touch it. Still undecided; changing it would relabel
  frozen test lines.
- **The Moto hides its Settings airplane-mode row** from Unstuk's accessibility service; `motorola.json`'s Settings
  route can't work there.
