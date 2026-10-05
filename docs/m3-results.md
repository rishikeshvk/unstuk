# M3 results: Data

2026-10-05 · Status: **done.** Spec: [m3-spec.md](m3-spec.md). Plain-language summary:
[m3-summary.md](m3-summary.md). Data card: [data/CARD.md](../data/CARD.md)

M3 asked whether we can build data that teaches a small model to map plain complaints to the right fix, and a test
honest enough to tell whether that model beats the keyword matcher. The data and the test exist; the keyword matcher
now has a score to beat. On the Moto, plain string matching finds nearly every switch, so the node-label model has
little to add on this phone.

## Targets

| Metric | Target | Result |
| --- | --- | --- |
| Clean training phrasings | ≥ 300 per trained intent, ≥ 1000 out of scope | **Met:** 409–480 per intent, 1,717 out of scope (train and dev) |
| Proxy test set | ≥ 25 per intent, ≥ 150 out of scope, every slice ≥ 30 | **Mostly met:** ≥ 25 per intent counting two-problem lines (three have 24 single-label lines), 164 out of scope, every slice ≥ 30 except `vague` (28) |
| Test leakage | 0 near duplicates | **Met:** 52 training lines at similarity ≥ 0.8 to a test line were removed |
| Hand label audit | ≥ 95% agreement on 200 lines | **Met:** 200/200, Cohen's kappa 1.00 (blind second labeller) |
| Node labels | Moto dumps for every A-rung screen; AOSP and selector variants for every target | **Met:** 960 training and dev questions; 8 Moto screens dumped, 10 test questions. One A-rung place (airplane mode in Settings) is hidden from Unstuk, so it has no question |
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

## Node labels: string matching on the Moto

"Which item on the screen is {target}?", asked on the Moto Edge 30 (Android 14) screens the debug-only dumper read:
eight Quick Settings tiles, the DND screen's "Turn off now" button and TalkBack in Accessibility. Each question offers
every labelled item on its screen, 18 to 48 options. The baseline knows only AOSP and Pixel labels; `motorola.json`
is the answer key. File: [data/nodes/test.jsonl](../data/nodes/test.jsonl).

| Baseline | Right |
| --- | --- |
| Exact, normalised, then fuzzy match (spec section 9) | 8/10 |
| The same, after first stripping a tile's state as the app's own matcher does | 9/10 |

- **"Wi-Fi, Off"** is missed by the plain baseline: the state suffix drops its similarity to "Wi-Fi" to 0.73, under
  the 0.8 cutoff. Stripping the state, as `LabelMatch.kt` does, fixes it.
- **The DND screen's "Turn off now"** is missed by both: they pick the screen's title, "Do Not Disturb". The control
  to tap isn't named after the thing it controls.

**Plainly: string matching finds every Moto switch once it strips the tile state, so the model isn't needed to name
switches on this phone.** What strings can't do is find an action button named for the action ("Turn off now"). The
evidence is thin, though: 10 questions on one phone whose wording is close to stock Android. The dev set's Xiaomi
wording is the better check that the model generalises, and a phone with heavier wording (Samsung, Xiaomi) the
better test.

Three places on the Moto have no question:
- **Airplane mode in Settings: hidden from Unstuk.** The row is on screen (seen in a screenshot) and in the view tree,
  but Unstuk's accessibility tree has 7 rows instead of 8, and the whole row with its title and switch is missing.
  That matches Android 14 hiding sensitive views from services that don't set `isAccessibilityTool` (invariant 11).
  The Aeroplane mode Quick Settings tile is visible. So on this Moto the executor can never use `motorola.json`'s
  Settings route for airplane mode; the tile, the Settings screen opened for the user, and guided steps remain.
- **The DND screen's button, first dump: not there in that state.** "Turn off now" exists only while DND is on. The
  dump script now turns DND on for that screen alone, the state the executor meets it in, and it became a question.
- **Auto-rotate tile, first build: a question-builder bug.** The builder compared whole strings, so "Auto-rotate,
  Off" never matched the label "Auto-rotate". It now uses the app's rule (the text before the first ',' or '.'), and
  each item on screen gives one option, not one per wording: as two options, picking the right tile by its other
  wording counted as wrong and flattered the baseline (the first build scored 8/8 on 8 questions).

## The data

| Part | Size | Notes |
| --- | --- | --- |
| Raw pool | 7,090 lines | 40 persona batches (4,800), 10 out-of-scope batches (1,200), 336 contrast pairs (672), 300 Mobile Actions requests, 118 seeds |
| Clean | 5,833 train, 1,095 dev | Dev is 9 whole batches plus the Mobile Actions eval rows, covering every grid value |
| Proxy test | 602 lines, frozen | ChatGPT 237, Gemini 265, context-free Claude 100 |
| State slice | 71 texts, 117 train and 47 test records | Four of five pairs; see the finding below |
| Node labels | 828 train, 132 dev, 10 test questions | Dev is one maker (Xiaomi) the model won't have seen; test is the Moto's own screens |

Cleaning: 49 exact and 58 same-label near duplicates, 52 lines close to the test and 3 guide examples removed. Two
runs of the pipeline give byte-identical output. The node-label build did not: Python salts string hashes per process,
and the build sorted a set by a key that ties. It is fixed, tested across hash seeds, and train and dev were rebuilt
(same counts, new shuffles).

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
7. **"Deterministic" needs a test across processes.** The node-label build gave the same output twice in one
   process and different output in each new one. Only a test that runs the build under several `PYTHONHASHSEED`s
   catches that.
8. **Not being an accessibility tool has a cost.** The Moto hides its Settings airplane-mode row from Unstuk. The
   ladder still has other routes, which is why accessibility automation is never the only path (invariant 5).

## What changed from the spec

| Change | Why |
| --- | --- |
| No per-intent cap after cleaning | The data was generated balanced; the gap comes from contrast pairs |
| Mobile Actions: 300 out-of-scope requests from five tools | None of its tools is a symptom we fix; Wi-Fi settings and calendar requests left out |
| Blind second labeller for review and audit, instead of a person | Chosen in planning; it makes agreement a measurement between independent labellers |
| `ids.lock` checked by a Kotlin test, not a Python one | `ml/` didn't exist yet in step 2 |
| The state slice keeps only texts a blind labeller left open | So it measures state, not words |
| Node-label test: one option per item on screen, answers found by the app's label rule | Two options for one item marked a right pick wrong; whole-string matching missed tiles that show their state |
| The DND screen is dumped with DND on | Its "Turn off now" button, the selector's step, only shows then |

## The phone run

- The Kotlin written in M3 compiled without changes. `ktlintCheck testDebugUnitTest` passes. The `ids.lock` test
  and the keyword parity test (all 15 fixture cases) ran and passed, with none skipped.
- The label dumper and `dump-labels.sh` ran on the Moto: all 8 screens dumped on the first try, with no
  `uiautomator dump`. The dumps hold no Wi-Fi network, Bluetooth device or phone names. They do show the carrier,
  the build number, the time zone and the time and battery level at dump time, which identify no one.

## Open for later

- Guide §5 and the state slice (finding 5), and the risk gate's 50/50 tie (finding 6).
- `motorola.json` keeps a Settings route for airplane mode that this Moto hides from Unstuk (finding 8).
