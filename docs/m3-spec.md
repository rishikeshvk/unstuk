# M3 spec: Data

2026-10-05 · Status: **data built; phone run pending.** Results: [m3-results.md](m3-results.md). Plain-language
summary: [m3-summary.md](m3-summary.md). Labelling guide: [m3-labelling-guide.md](m3-labelling-guide.md)

M3 answers one question: **can we build data that teaches a small model to map plain complaints to the right fix,
and a test honest enough to tell us whether that model beats the keyword matcher?**

It is done when these exist and are committed: a clean training pool, a frozen proxy test set, a node-label set,
`catalog/ids.lock`, a data card, and a score for M2's keyword matcher on the proxy test set, with an error analysis
that says where and why it fails.

Background: [plan.md](plan.md), roadmap step 3, and [m2-results.md](m2-results.md). M2 proved that the app can go
from a complaint to a checked fix with keyword rules in place of the model. M3 builds what the model will learn
from, and the test that decides whether a model is worth shipping at all.

```text
seeds ─► generated batches ─► cleaning pipeline ─► train / dev        (what the model learns from)
                                     ▲
                                     │ leakage check: nothing in train may look like the test
                                     │
proxy test set (built first, frozen) ─┘                               (what decides if it ships)
```

**Why data is the hard part.** A model can only be as good as the examples it sees. A 33M-parameter encoder will
happily learn whatever pattern makes the training loss go down, including patterns we never meant to teach, such as
"complaints written by one LLM start with *Hey*". Most of M3 is about making sure the only pattern that works is the
one we want: the meaning of the complaint.

## 1. Why a model at all?

This is the question the whole project has to answer. The answer must be a number on a test, not an opinion, and
M3 builds that test. Here is the case we expect the numbers to make.

### What the keyword matcher gets wrong

The M2 matcher counts how many of an intent's phrases appear in the complaint and turns the counts into shares.
Each failure below becomes a *slice* of the proxy test set (section 5), so we can measure it.

| Failure | Example | What M2 does |
| --- | --- | --- |
| Paraphrase with no keyword | "my phone stays quiet when mum calls" | No phrase matches, so it declines |
| Keyword collision | "my ring finger hurts" | Matches "ring", so `phone_not_ringing` at probability 1.0 |
| In-scope words, out-of-scope meaning | "my internet bill is too high", "how do I turn on dark mode" | `no_internet` / `screen_too_dim` at 1.0 |
| Negation | "the screen isn't dark, it's way too bright" | Matches "dark", so `screen_too_dim` |
| Typos and spellings | "intrnet not wrking", "wify" | No match |
| Indian English | "net is not coming", "mobile is hanging" | Partly covered by hand-added phrases; every new idiom needs a new rule |
| Long story, buried clue | "I was at my daughter's place and when I came home I noticed nobody could reach me…" | Depends on luck |
| Vague | "my phone is acting weird" | Declines; a clarifying question would serve better |

The second and third rows are the dangerous ones. **One keyword hit always gives probability 1.0.** The risk gate
runs a low-risk fix *automatically* above 0.8, so "my ring finger hurts" on a phone with DND on would turn DND off
without asking. The matcher's numbers have the right shape but mean nothing. That alone is a reason to want a
model: the gate needs a probability that tells the truth.

### What a model adds

1. **A probability that can be calibrated.** When the model says 0.9, it should be right about 9 times in 10.
   That is what lets the gate decide between "run it", "ask first" and "ask which one you mean" (M6 tunes this).
2. **"Is this out of scope?" as its own question,** instead of "no keyword matched".
3. **Generalisation over wording.** The encoder was pre-trained on a huge amount of English, so it already knows
   that "quiet", "silent" and "doesn't ring" are close. Rules only know what we typed.
4. **New options without retraining.** Options are text ("The screen is too dark"), so a new intent can work
   zero-shot from its option text, and so can a new phone's Settings label ("Flight mode").

What the model never does: act, or write text anyone sees (invariant 1). It only picks among options we supply.

### The honest counter-argument

Fifteen intents in English is a modest task. A TF-IDF or fastText classifier trained on the same data might be good
enough. The plan already treats that as a valid finding (invariant 10). So M4 and M5 climb a ladder, and each step
must beat the one below it on the proxy test set to earn its place:

```text
keyword matcher (M2) → TF-IDF + logistic regression / fastText (M4) → frozen encoder + logistic regression (M4)
                     → fine-tuned encoder with Choice / Noul heads (M5)
```

If the fine-tuned encoder doesn't clearly win, especially on the collision, paraphrase and out-of-scope slices and
on the confident-and-wrong rate (section 10), we ship the simpler model. M3's job is to make that comparison fair.

## 2. What changed from the plan

| Change | Why |
| --- | --- |
| **No real user messages in M3.** The test set is a *proxy* test set, built to be as unlike the training data as possible (section 5) | Collecting messages from other people isn't possible now. The real-message check behind invariant 10 moves to the M8 field test: M5 picks a model on the proxy test, and M8 confirms it on real messages before it counts as shipped |
| **Consent and storage rules for real messages move to the M8 spec** | plan.md asked to settle them in M3 because M3 would collect first. Nothing real is collected now |
| **No API calls for generation.** Training phrasings are written in Claude Code sessions as committed batch files. Small test batches come from the Gemini app and open models in opencode: you paste a committed prompt and save the output | There is no API access, and the opencode limits are low. Every batch records its prompt and generator in a manifest, so we know where each line came from |
| **Labels come from the words alone, plus a small state slice** | The Diagnoser already reads device state, deterministically. If state were on every sample, the model could learn to read state and ignore the words. The slice (section 8) lets M5 measure whether state helps instead of assuming it |
| **On-screen node labels are in scope** (section 9) | The executor's "which switch is it?" question goes through the same model, so its data belongs here |
| **Google's Mobile Actions dataset is used narrowly** | Its phrasings are commands ("turn on the flashlight"), not symptoms. It is used for out-of-scope examples and command-style phrasings of our fixes, after a fit check (step 7). Licence CC-BY-4.0, credited in the data card |

## 3. Targets

| Metric | Target | Meaning |
| --- | --- | --- |
| Clean training phrasings | ≥ 300 per trained intent, ≥ 1000 out of scope | Counted after cleaning, not before |
| Proxy test set | ≥ 25 per intent (all 15), ≥ 150 out of scope, every slice ≥ 30 | About 600 items |
| Test leakage | 0 | No test item is a near-duplicate of a training item |
| Hand label audit | ≥ 95% | 200 random training items checked by hand against the labelling guide |
| Node labels | Every A-rung target | Moto dumps for each screen the accessibility rung visits, plus AOSP and selector variants for each target |
| Keyword baseline | Scored | On the proxy test, per slice, with 95% intervals |

**What a 600-item test can tell us.** At 85% accuracy on 600 items the 95% interval is about ±3 points, so a
2-point gap between two models is noise. A 30-item slice is much rougher: at 80% the interval is about ±14 points.
Slices show *where* a model fails; only the whole set decides *which* model wins.

## 4. The label contract

### Labels

- Each complaint gets an ordered list of labels: intent IDs from the catalog, or `out_of_scope`. Most have one.
  A complaint with two problems ("no internet and the screen is dark") lists both, main one first. A prediction
  counts as right if it is anywhere in the list.
- A `vague` tag marks complaints where the right reply is a clarifying question ("my phone is acting weird"). They
  are scored by "the model is not confident", not by a label.
- **The labelling guide is written before any data is generated** (`docs/m3-labelling-guide.md`, step 2). It
  settles every confusable pair with a rule and examples, so that two people (or two LLMs) label the same complaint
  the same way:

| Pair | The question the rule must answer |
| --- | --- |
| `no_internet` / `wifi_no_load` | Does the user say Wi-Fi is connected? |
| `phone_not_ringing` / `notifications_missing` | Calls or messages? "WhatsApp calls don't ring" is which? |
| `screen_too_dim` / `colours_wrong` | "The screen looks dark and grey" |
| `wrong_time` / `wifi_no_load` | They share a cause (automatic time); which words decide? |
| `cant_hear_call` / `bluetooth_earphones` | "I can't hear calls on my earbuds" |
| `talkback_on` / `text_too_small` | "everything is zoomed and big" is magnification, so which? |

When generation finds a new ambiguity, we add a rule to the guide first, then label.

### Held-out intents

Three intents never appear in training or dev data (invariant 9). The test set has them, so we can measure how
well the model handles an intent it only knows from its option text. Chosen (2026-10-05):

- `screen_wont_rotate`: distinct from everything; the easy case.
- `wrong_time`: shares a cause and some words with `wifi_no_load`; a hard case.
- `cant_hear_call`: close to `phone_not_ringing` and `bluetooth_earphones`; a hard case.

### Frozen IDs

`catalog/ids.lock` lists every intent, fix and check ID (invariant 8; an intent's ID is also its option's ID).
`CatalogConsistencyTest` fails if a locked ID is renamed or removed, or if a new catalog ID is missing from the
lock, so adding one is a deliberate edit to both. The test is Kotlin, beside the catalog's other rules, because
`ml/` doesn't exist yet; the Python validator (step 3) checks that every data label exists in the catalog.

## 5. Sources and splits

| Set | Folder | Who writes it | Used for |
| --- | --- | --- | --- |
| Seeds | `data/seed/` | Claude drafts about 8 per intent; you review and edit | Showing the generator what a label means |
| Proxy test set | `data/test/` | You (by hand), the Gemini app, open models in opencode | The final score. Never trained on, never tuned on |
| Training pool | `data/raw/` → `data/clean/` | Claude, in batches | Training |
| Dev set | `data/clean/` | Split from the training pool | Tuning (thresholds, epochs, temperature) |

### The proxy test set comes first

The test set is built and frozen **before any training data exists**. If we write the training data first, we
end up writing a test that looks like it, and the score flatters us. Once frozen, its SHA-256 goes into a lock file,
and the pipeline refuses to run if the file changes.

It is made to differ from the training data in every way we control:

- **Different writers.** About 5 per intent plus out-of-scope ones written by you by hand (about an hour; the
  closest thing to a real user we have), and batches from Gemini and open models. Training data comes from Claude,
  so a model that only learned "Claude's style" will be caught.
- **A different prompt recipe** from the training prompts.
- **Slices** in the spirit of CheckList (Ribeiro et al., 2020), each tagged on the item:

| Slice | Example |
| --- | --- |
| `plain` | "my phone doesn't ring" |
| `paraphrase` (no catalog keyword) | "nobody can get through to me, it just stays quiet" |
| `typo` | "intrnet not wrking since mrng" |
| `collision` (in-scope word, other meaning) | "my ring finger hurts" |
| `negation` | "it's not dark, it's too bright" |
| `oos_near` (out of scope, sounds in scope) | "my internet bill is too high" |
| `long_story` | Three sentences, the clue in the last one |
| `indian_english` | "net is not coming", "mobile is hanging" |
| `short_vague` | "phone problem" |
| `multi` | "no internet and the screen is dark" |

### The training pool: diversity over volume

The main risk with LLM-written data is that it is too clean and too similar. Asking the same prompt 500 times gives
500 cousins of one sentence. Research on LLM-generated classification data finds that diversity matters more than
quantity, and that conditioning each request on a varied topic or persona helps most
([Li et al. 2024](https://arxiv.org/abs/2407.12813), [SynthesizRR](https://arxiv.org/abs/2405.10040)).

So each batch is generated for one cell of a **diversity grid**, and the cell is recorded on every line:

| Axis | Values (examples) |
| --- | --- |
| Persona | Age (teen, adult, 70+), comfort with phones (low, medium), English variety (Indian, British, American, second language) |
| Style | One or two words, a question, a story, frustrated, polite, dictated (no punctuation, run-on) |
| Length | Short (≤ 5 words), medium, long (2–4 sentences) |
| Typos | None, a few, many |
| Context | An app named (WhatsApp, YouTube, PhonePe), what happened just before ("after the update", "my grandson was using it") |

Two more kinds of training data teach the boundaries, which plain examples don't:

- **Hard negatives:** out-of-scope complaints that use our words ("my ring finger hurts", "dark mode",
  "Bluetooth speaker battery died"), and real phone problems we can't fix (cracked screen, battery swelling, "how do
  I take a screenshot").
- **Contrast pairs** ([Gardner et al. 2020](https://arxiv.org/abs/2004.02709)): the smallest edit that flips the
  label. "The screen is too *dark*" → `screen_too_dim`; "the screen went *grey*" → `colours_wrong`. They force the
  model to look at the word that matters.

### Dev split by batch

The dev set is split off **by batch**, never by row. Lines from one batch are near-twins; if they sit on both sides
of a split, dev accuracy looks great and means nothing.

## 6. Cleaning pipeline

Python in `ml/` (Python 3.12, uv, ruff, mypy strict, pytest; AGENTS.md conventions). Raw batches stay committed
exactly as written; every step after them is deterministic code, so anyone can rebuild `data/clean/` from
`data/raw/`.

| Step | What it does | Why |
| --- | --- | --- |
| 1. Schema check | Every line has the fields of section 7; labels exist in the catalog | Catch broken batches early |
| 2. Light normalisation | Unicode (NFC), curly quotes, whitespace. **Typos, casing and slang stay** | Real users type messily. Cleaning that away trains a model for users who don't exist |
| 3. Exact duplicates | Drop repeats after normalisation | Repeats over-weight one phrasing |
| 4. Near duplicates | Character n-gram similarity, inside the pool and against the test set. A train line too close to a test line is dropped from train, never from test | Leakage makes test scores lie |
| 5. Label check | A quick TF-IDF + logistic regression model, cross-validated, plus confident learning ([cleanlab](https://docs.cleanlab.ai/stable/tutorials/datalab/datalab_quickstart.html)) flags lines whose label looks wrong. You review the queue and fix the line or the guide | LLMs mislabel; so do people |
| 6. Shortcut check | Per label: length, top words, first words. A habit found mostly in one label (say every `out_of_scope` line starts with "How do I") is a bug to fix in generation | The model will use any shortcut it finds |
| 7. Balance | Cap each intent at the same count | Our label mix is our choice, not the real one; don't let one intent dominate by accident |
| 8. Report | Counts, lengths, distinct n-grams and slice coverage, written to `ml/reports/` | One page that shows the state of the data |

## 7. Record format

One JSON object per line (JSONL), the same shape in every folder:

```json
{"id": "raw-0042-017", "text": "phone not ringing when my son calls", "labels": ["phone_not_ringing"],
 "tags": ["plain"], "source": "generated", "generator": "claude", "batch": "raw-0042",
 "persona": {"age": "70+", "comfort": "low", "variety": "indian", "style": "plain", "typos": "none"}}
```

- `state` (optional) is a list of catalog check IDs that hold, for example `["airplane_on"]`. It reuses the
  catalog's names (invariant 8) instead of inventing a second state format.
- `source` is `seed`, `generated`, `handwritten` or `mobile_actions`.
- M5 will turn records into training samples of the plan's shape (state, question, options, correct option), with
  shuffled option order and random distractor subsets. M3 does not build that step; it would be code with no user
  yet.

## 8. State slice

About 200 complaints that are ambiguous from the words alone, such as "nothing works on my phone" or "I'm not
getting anything". Each is paired with states built from the catalog's causes: with `airplane_on`, the label is
`no_internet`; with `dnd_on` alone, it is `phone_not_ringing`. The label is the intent whose cause holds, so it is
computed, not guessed.

It is split by complaint text (the same text never appears in both train and test). M5 trains with and without
state and compares on this slice. If state doesn't help there, it stays out of the model.

## 9. Node-label data

The executor's question: **"Which item on the screen is the {target}?"** The options are the labels visible on that
screen. Today the selector files list exact labels per phone; the model would let a new phone's wording
("Flight mode") work without a new rule.

| Source | What it gives | Use |
| --- | --- | --- |
| `android/app/src/main/assets/selectors/pixel.json`, `motorola.json` | The labels we already confirmed | Train |
| AOSP SystemUI and Settings strings (English, British English and Indian English resources; Apache-2.0) | Each target's official label and its neighbours | Train |
| Claude-written OEM variants (Samsung, Xiaomi, Oppo wording) | Label variety | Train |
| Labels dumped from the Moto | Real screens with real neighbours | **Test** |

The Moto dumps come from a small dumper in the app's own accessibility service, in the debug build only
(invariant 7), not from `uiautomator dump` (the scripts' rule from M1). Splitting by phone maker keeps the test
honest: the model is tested on a skin it never saw in training.

The baseline to beat is exact and fuzzy string matching against the selector labels. If it already finds the
right switch every time, the model isn't needed for this question, and that is a finding too.

## 10. Evaluation, fixed before any model exists

We decide how to score before we see any score, so we can't pick the metric that flatters us.

| Metric | What it tells us |
| --- | --- |
| Top-1 accuracy, in scope | How often the first pick is right |
| Macro-F1 | Same, but every intent counts equally, so small intents can't hide |
| Out-of-scope precision and recall | Does it say "I can't help with that" when it should, and only then? |
| Accuracy per slice | Where it breaks |
| **Confident-and-wrong rate** | Share of items with top probability ≥ 0.8 and a wrong pick. These would run a fix *automatically* on the wrong problem. This is the safety number |
| ECE (expected calibration error) | Does a 0.9 mean right 9 times in 10? |
| Zero-shot accuracy | On the three held-out intents |
| Node-label accuracy | Right switch picked on the Moto dumps |

Every number gets a 95% bootstrap interval. The keyword matcher is scored the same way, with its fake
probabilities, to show in numbers why they can't drive the gate.

**A warning about calibration on synthetic data.** How often each intent appears in our data is our choice. Real
users will complain about the internet far more than about rotation. A model calibrated on our mix may be
over- or under-confident on real traffic. M6 calibrates on the dev set; M8 checks calibration again on real
messages.

## 11. Senior notes: the lessons we apply

1. **Freeze the test set first.** Everything else can be redone; a contaminated test can't be un-seen.
2. **Diversity beats volume.** 300 varied lines teach more than 3000 similar ones. Measure diversity (distinct
   n-grams, near-duplicate rate) instead of trusting it.
3. **Split by group, not by row.** Batches, templates and paraphrases of one seed are groups.
4. **Write the labelling guide before the labels.** Most "model errors" on small tasks are label disagreements.
5. **Expect label noise and look for it** with a simple model's disagreements (confident learning), then fix by
   hand.
6. **Don't over-clean.** Keep the typos, the missing punctuation and the odd grammar. They are the task.
7. **Hunt for shortcuts.** If one label has a giveaway (length, a first word, an app name), the model will use it
   and fail on real users.
8. **Teach the boundaries.** Hard negatives and contrast pairs, not just more positives.
9. **Mix generators.** Every LLM has a house style. Train on one family, test on others.
10. **Document the data.** A data card ([Gebru et al., Datasheets for Datasets](https://arxiv.org/abs/1803.09010))
    records sources, sizes, licences, known gaps and what the data must not be used for.
11. **Synthetic data suits this task.** It works best when labels are objective, and "which setting is wrong" is
    far more objective than, say, sentiment. It still can't show us how real people write, which is why M8 exists.

## Scope

**In M3**
- Labelling guide, label contract, `catalog/ids.lock` and its test.
- The `ml/` Python project: catalog reader, record schema, validator and the cleaning pipeline.
- Seeds, the proxy test set, the training pool, hard negatives and contrast pairs, the state slice and node-label
  data.
- A debug-only label dumper for the node-label test.
- The keyword matcher ported to Python, a shared parity fixture both the Kotlin and Python tests check, its score on
  the proxy test, and an error analysis.
- Data card, `m3-results.md` and a plain-language summary.

**Not in M3**
- Any training, including TF-IDF and fastText baselines (M4) and the encoder (M5). The cleaning step's quick
  TF-IDF model only flags suspect labels; it is never scored or shipped.
- The sample expander that builds (state, question, options, answer) samples (M5).
- Data for the urgency Score and for guide-card questions: nothing uses them yet.
- Real user messages, and consent rules for them (M8).
- Hinglish or other languages (v2).

## Changes during M3

| Date | Change | Why |
| --- | --- | --- |
| 2026-10-05 | No cap per intent in cleaning (section 6, step 7) | The data was generated balanced; the remaining gap comes from contrast pairs, the most valuable lines. Training can weight classes |
| 2026-10-05 | Mobile Actions gives 300 out-of-scope commands from five tools; Wi-Fi settings and calendar requests are left out | None of its tools is a symptom we fix; Wi-Fi is too close to our intents, and calendar dates would bias the held-out `wrong_time` |
| 2026-10-05 | Every training batch is written by a fresh agent with no project context | This session read the test set while reviewing it; isolation keeps test phrasing out of training |
| 2026-10-05 | The label review and the 200-line audit use a blind, context-free agent as the second labeller | Chosen in planning; it makes agreement a measurement between two independent labellers |

## Decisions (2026-10-05)

| # | Decision | Chosen |
| --- | --- | --- |
| 1 | Test set | Proxy test set now; real messages in M8 |
| 2 | Generators | Claude for training; you by hand, Gemini and open models for the test |
| 3 | Device state | Labels from words; a separate state slice |
| 4 | Breadth | Intents, out of scope and node labels |
| 5 | Held-out intents | `screen_wont_rotate`, `wrong_time`, `cant_hear_call` |
| 6 | Commands with no symptom | Labelled with the intent that owns the fix |
| 7 | Nearby problems not in the catalog (zoom, proximity, broken camera) | `out_of_scope` |

### Rejected alternatives

1. **One generator for everything** is simpler, but a test written in the same style as training data measures
   style-matching, not understanding.
2. **State on every sample**, as plan.md describes, invites the model to read state and ignore words, because in
   generated data the state usually gives the answer away.
3. **A random row-level split** puts near-twins on both sides and inflates dev scores.
4. **Spell-correcting complaints** before the model would hide the messiness the model has to learn, and add a
   component that can be wrong on its own.
5. **Running the Kotlin matcher over adb** to score it gives the exact app code, but needs a phone for every
   evaluation. A short Python port plus a shared parity fixture is checked by both test suites instead.
6. **Waiting for real messages before building anything** would stall M4–M7. The proxy test lets work continue,
   and M8 is the honest final check.

## Steps

One commit each, or a few where a step is large. Each step ends with a short "what to study" note.

1. **This spec** and a dated correction in plan.md.
   *Learn:* why the test set comes first, and what "proxy" means.
2. **Labelling guide, label contract, `ids.lock`** and its test.
   *Learn:* annotation guidelines and inter-annotator agreement.
3. **`ml/` skeleton:** uv project, catalog reader, record schema and validator.
   *Learn:* how one source of truth feeds two languages.
4. **Seeds:** Claude drafts about 8 per intent; you edit them.
   *Learn:* what makes a seed useful (variety, not polish).
5. **Proxy test set:** your hand-written slice, Gemini and open-model batches, slice tags, freeze by hash.
   *Learn:* evaluation design, slices and behavioural testing (CheckList).
6. **Training pool:** batches over the diversity grid, with the manifest.
   *Learn:* prompt design for diversity, and measuring it.
7. **Hard negatives, contrast pairs and out of scope,** plus the Mobile Actions fit check.
   *Learn:* decision boundaries, and why negatives teach more than positives.
8. **Cleaning pipeline,** your review of flagged lines, and the 200-line hand audit.
   *Learn:* deduplication, leakage, confident learning and shortcut learning.
9. **State slice.**
   *Learn:* confounding, and why a feature can help or hurt.
10. **Node-label data** and the debug-only dumper.
    *Learn:* splitting by domain (phone maker) to test generalisation.
11. **Keyword baseline:** Python port, parity fixture, score on the proxy test, error analysis; data card,
    `m3-results.md` and a plain-language summary.
    *Learn:* bootstrap confidence intervals, and reading a confusion matrix.
