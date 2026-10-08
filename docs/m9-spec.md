# M9 spec: The write-up

2026-10-08 · Status: **approved.** Background: [plan.md](plan.md), roadmap step 9, and every results doc from
[m1-results.md](m1-results.md) to [m7-results.md](m7-results.md).

M9 answers one question: **what did it take to put a calibrated decision model on a phone, and where does it
still fail?** The roadmap names four parts: a size waterfall, calibration plots, the baseline comparison and a
failure analysis. Today the story is spread over seven results docs and twelve reports, without a figure.

It is done when `docs/writeup.md` holds those four parts and screenshots of the app, the README links to it as
the project's front page, and every number in it matches a committed report. M8's real messages are still to
come; the write-up has a section for them, marked pending until `ml/reports/real.md` exists.

## 1. Rules

- **No new decisions on the test.** M9 re-scores frozen deciders from their committed settings only to draw
  figures. Nothing is tuned, chosen or retrained. Each re-scored headline number must match its committed
  report, or the work stops and the mismatch is explained before anything is drawn.
- **Real messages are never read.** The M8 section quotes only `ml/reports/real.md`'s aggregates.
- **Deletion moves.** M8 spec section 3 deletes `data/real/` "once the M9 write-up is done". Since M9 is written
  before the sittings, that now means once the M8 section of the write-up is filled in.
- **Proxy test lines may be quoted.** They were written by LLMs (M3 spec, section 5), not by users, so the
  failure analysis can show them.

## 2. Test scores for the figures

`unstuk-writeup-scores` scores the 602 frozen test lines with each decider, as its own report scored it, and
caches per-line results (ids and probabilities, no text) in `ml/cache/writeup/`, which is gitignored.

| Decider | Loaded by | Settings |
| --- | --- | --- |
| Keyword | `keyword_matcher.load_matcher` | M2's, under M2's placeholder lines |
| TF-IDF + LR, frozen bge-small + LR, zero-shot | `decision_test.baselines` | M4's, under M2's placeholder lines |
| M6's float graph | `graph_scoring.GraphDecider` | M6's temperatures and lines, as M7 scored it |
| **int8 graph (ships)** | `quantized_test.load_shipped` | `ml/settings/quantized.json` |

**Correction (2026-10-08), before any figure:** M5's decision model and its fine-tuned linear head can't be
re-scored. Their checkpoints are no longer on this machine (only `result.json` is), and the Colab sessions that
trained them are gone. They stay in the write-up's tables from [m5-results.md](m5-results.md), but not in the
figures. *Rejected:* retraining them on Colab. Training isn't bit-exact, so the sha256 check would refuse the
new weights, and they'd no longer be the models M5 reported.

Before writing, it checks in-scope accuracy, confident and wrong and ECE against each decider's results table,
to the table's precision, and fails on any mismatch.

*Rejected:* copying the numbers from the results docs into the figure code. It is faster, but the figures would
then prove nothing, and the per-line probabilities a reliability diagram needs are in no doc.

## 3. Figures

`unstuk-figures` reads the cache and writes SVGs to `docs/figures/`. matplotlib comes in through a `writeup`
dependency group, so training and the app's tools don't carry it.

| Figure | Shows |
| --- | --- |
| `size-waterfall.svg` | The float graph, int8's saving, then ONNX Runtime, dex and assets adding up to the release APK, against the 60 MB target and the 100 MB budget. Sizes are measured from the graph files and the APK's zip entries |
| `ladder.svg` | The six deciders of section 2, keyword to int8, on the bar's rows (in-scope accuracy, confident and wrong, out-of-scope recall, held-out intents), as points with 95% bootstrap intervals |
| `reliability.svg` | Reliability diagram (10 bins) for the int8 graph against zero-shot (the best-calibrated baseline) and TF-IDF, with how many lines fall in each bin |
| `gate.svg` | Where the int8 graph's test lines land: automatic, confirm, clarify or decline, for in-scope, out-of-scope and vague lines |
| `failures.svg` | The int8 graph's test mistakes by cause (section 4) |

The figures use the app's colour tokens ([design-spec.md](design-spec.md)): Ground behind, Ink for text,
Tangerine for the model that ships and greys for the rest. The background is solid, so they read in a dark
theme too.

*Rejected:* hand-written SVG. It is more code to own, for figures matplotlib already draws.

## 4. Failure analysis

Every test line the int8 graph gets wrong is given one cause. A line is wrong when its top answer is the wrong
intent, when an in-scope line is declined, or when an out-of-scope line is answered. The causes are fixed here,
before any mistake is read:

| Cause | Means |
| --- | --- |
| `lexical_pull` | The words name or suggest another setting, and the model followed the words |
| `needs_state` | The words can't settle it; the phone's state would |
| `collision` | A line that isn't about the phone but sounds like one (or the reverse) |
| `held_out` | A held-out intent's line declined or named as another intent |
| `two_problems` | The line describes two problems and the model picked the one not labelled |
| `debatable_label` | A careful reader could label it either way under the labelling guide |
| `wording` | Dialect, typos or unusual phrasing the training lines don't cover |

If a mistake fits none, it is coded `other` with a note, and the count of `other` is reported; the list isn't
changed after reading. Claude proposes the codes in `data/failures/test-int8.jsonl` (`id`, `cause`, `note`) and
the developer reviews them before they're committed. The analysis also reports the most common confusions and
the mistakes by writer and by tag, with `baseline_report`'s splits.

## 5. Screenshots

On the Moto, `android/scripts/screenshots.sh` types four complaints into the app and captures the reply: a fix
run and verified, a confirm, a clarifying question and a decline. None of them touches airplane mode or mobile
data, because the Moto is the development machine's internet connection. They are saved, reduced, to
`docs/figures/screens/`.

**Note (2026-10-08):** on the phone the state text moves the model's confidence, so two complaints picked on the
laptop landed elsewhere ("the screen looks strange" asked a question instead of confirming). Candidates were tried
through the debug receiver, which reports the reply without the UI, and the script keeps the ones checked on the
Moto. The confirm band is 0.70 to 0.75; "my phone is too quiet", at 0.71, lands in it.

## 6. The write-up

`docs/writeup.md`, for a reader who knows some ML and no Android, in about 2,000 words:

1. The problem, and "the model decides, code acts".
2. How it works: the typed questions, the gate and the executor ladder.
3. The data, and why the test set is a proxy.
4. Baselines and the bar (`ladder.svg`).
5. Calibration and the gate (`reliability.svg`, `gate.svg`).
6. On the phone (`size-waterfall.svg`, latency, the batching and CPU correction).
7. Where it fails (`failures.svg`).
8. What didn't work: zero-shot on new intents, out of scope fitted out of fold, the vague lines.
9. Real messages: pending M8.
10. What's next.

The README becomes the front page: one paragraph, a screenshot, three headline numbers and links to the
write-up and the plan. `m9-summary.md` tells it in plain words, as the other summaries do.

## Scope

- In: the scores cache, the figures, the failure codes, the screenshots, the write-up, the README and the summary.
- Out: any change to a model, the gate's lines, the catalog or the app; a reduced-operator ONNX Runtime build;
  M8's sittings; a blog post or a published page (the write-up can become one later).

## Steps

One commit each. Each step ends with a short "what to study" note.

1. This spec, and the README's milestone line.
2. `unstuk-writeup-scores`, with tests on the cache round-trip and the match check.
3. `unstuk-figures` and the first four figures, with tests on the waterfall and the reliability bins.
4. The failure codes, reviewed by the developer, and `failures.svg`.
5. The screenshots, on the Moto.
6. `writeup.md`, the README, `m9-summary.md`, and this spec marked done.
