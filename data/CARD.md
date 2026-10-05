# Data card: Unstuk M3

2026-10-05 · Following the questions of Gebru et al., *Datasheets for Datasets*. Spec:
[m3-spec.md](../docs/m3-spec.md). Results: [m3-results.md](../docs/m3-results.md).

## Why it exists

To teach a small on-device model to map a non-technical person's phone complaint to one of 15 fixable problems, or to
"I can't help with that", and to measure honestly whether a model beats the keyword matcher it would replace.

## What is in it

| Folder | What | Size |
| --- | --- | --- |
| `seed/` | Hand-reviewed example complaints, 8 per trained intent, plus out of scope and vague | 118 |
| `raw/` | Generated training complaints (`train-*`), out-of-scope lines (`oos-*`), contrast pairs (`contrast-*`) and a Mobile Actions subset | 6,972 |
| `clean/` | The cleaned pool, split by batch: `train.jsonl`, `dev.jsonl`; plus review decisions, blind labels and the audit sample | 5,833 train, 1,095 dev |
| `test/` | The frozen proxy test set (`test.lock`) | 602 |
| `state/` | Complaints the words can't settle, paired with device states | 117 train, 47 test records |
| `nodes/` | "Which item on the screen is the {target}?" questions | 828 train, 132 dev; 10 test from the Moto's screens |
| `real/` | Real user messages: gitignored, never committed, empty in M3 | 0 |

Each complaint is one JSON line: `id`, `text`, `labels` (intent IDs from `catalog/intents.json` or `out_of_scope`),
`tags` (test slices, `vague`), `source`, `generator`, `batch`, and for generated lines the writer `persona`
(age, comfort with phones, English variety, style, typos). Clean lines per label, train and dev together: 409–480
per trained intent and 1,717 out of scope.

## How it was made

- **Labels** follow [the labelling guide](../docs/m3-labelling-guide.md), written before any data.
- **Training data** was written by fresh Claude agents with no project context, one writer persona per batch from a
  diversity grid, each agent reading only its own prompt and writing only its own sheet (checked in every
  transcript). This session had read the test set, so it wrote no training lines itself.
- **Out-of-scope lines** came from the same kind of agent, plus 300 requests from Google's Mobile Actions dataset
  (flashlight, contacts, email, maps).
- **The test set** was written before any training data, by ChatGPT (237 lines), Gemini (265) and a context-free
  Claude agent (100), reviewed against the guide, deduplicated and frozen by hash.
- **Node labels** come from AOSP strings, the Pixel selector file and an agent's knowledge of five makers' wording;
  the Moto selector file is kept out, because the Moto's screens are the test. Those screens were dumped from a Moto
  Edge 30 (Android 14) by the debug-only dumper; the dumps show the carrier, build number and time zone, but no
  network, device or phone names.

## Cleaning and checks

Unicode and whitespace normalised (typos kept); 49 exact and 58 same-label near duplicates removed; 52 training lines
too close to a test line (character n-gram cosine ≥ 0.8) and 3 labelling-guide examples removed. Confident learning
flagged 37 labels; a blind labeller agreed with 36, and the other was relabelled by guide rule. A blind audit of 200
random training lines agreed on all 200 (Cohen's kappa 1.00). Reports: `ml/reports/clean.md`, `ml/reports/audit.md`.

## Held out, on purpose

- Three intents never appear in training or dev: `screen_wont_rotate`, `wrong_time`, `cant_hear_call`. Out-of-scope
  training lines avoid their topics, and Mobile Actions calendar requests are left out for the same reason.
- The test set is frozen; nothing in it was tuned on.

## Licences and credit

- Mobile Actions subset: Google, CC-BY-4.0 ([details](raw/mobile-actions/README.md)).
- AOSP strings: The Android Open Source Project, Apache-2.0 ([details](nodes/README.md)).
- Everything else was generated for this project.

## Known gaps

- **Synthetic only.** No real user wrote any line; real wording, spelling and topics will differ. The M8 field test
  is the real check.
- **English only**, with Indian English as one variety; mostly-Hindi lines were never generated or labelled.
- **Training lines are easier than the test.** The blind audit's perfect agreement says the training lines are
  unambiguous; the test's paraphrase, typo, negation and vague slices are not.
- **The vague slice has 28 lines**, two short of the 30 target; its scores are rough.
- **Guide §5 settles some complaints by default** ("Wi-Fi not working" without "connected" is `no_internet`), while
  the device could show the other cause. See [state/README.md](state/README.md).
- **The node-label test is small and easy:** 10 questions on one phone whose wording is close to stock Android.
  String matching gets 8 of 10.
- **Label mix is our choice**, not real traffic, so calibration measured here is not calibration on real users.

## Not for

Estimating how real users behave or how often each problem occurs; languages other than English; a public benchmark
claim. Real user messages must never be added here (invariant 9).
