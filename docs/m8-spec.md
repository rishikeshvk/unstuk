# M8 spec: Real messages

2026-10-08 · Status: **approved; tools built, sittings pending.** Background: [plan.md](plan.md), roadmap step 8, and [m7-results.md](m7-results.md).

M8 answers one question: **on complaints written by real people, does the shipped int8 model still beat the
baselines?** Invariant 10 makes that the condition for shipping it. Every number so far comes from the proxy test
set, written by us and by other LLM families (M3 spec, section 5).

It is done when at least 150 clear lines from at least 4 participants are labelled and frozen, scored once by the
rule in section 4, and `m8-results.md` says whether the model ships.

## 1. What changed from the plan: a lean field test

The plan's step 8 installs the app on test users' phones for two weeks and logs what they type. M8 does less:

| Plan | M8 | Why |
| --- | --- | --- |
| Two weeks of organic use, logged in the app | **Sittings with symptom cards** (section 2), plus three lines per person about a problem they really had | Phones don't break often: two weeks would give a few dozen messages, not 150 |
| A field mode in the app: consent screen, local text log, export | **No app changes.** Messages are typed into a chat or a note and copied into a sitting file | The question is about words, which Python scores exactly as the phone does (M7: 1,144 of 1,144 dev lines agree) |
| Fix success and latency on users' own phones | Cited from M7 on the Moto: 0 false successes and 9.6 ms median | Those numbers measure the executor and the runtime, which M8 doesn't change |

*Rejected:* the full field test. It would take two weeks and an app feature for a set too small to decide on. It
can follow as v2 work if the lean set shows wording the cards miss.

## 2. Sittings

- **Cards.** `data/field/cards.json` holds 40 cards. Each is a short story of a problem that never names the
  setting or uses its option text: "Your daughter says she called you three times this morning. Your phone was
  next to you and made no sound." There are 2 per intent (the 3 held-out intents included), 8 out of scope and 2
  vague. Three `free` prompts follow, each asking for a phone problem the person really had. A card is a
  stimulus, not a label: a person may well describe something else.
- **The prompt,** read once at the start: *"Imagine this just happened to you. Unstuk asks 'What's wrong with
  your phone?'. Type what you would write, the way you'd type it."* Nothing else is said about the cards, and no
  answer is corrected.
- **Typed on a phone.** In person, the participant types each answer on their own phone into a chat with the
  developer or into a note. Remotely, the developer sends the cards one at a time over chat. Either way the text
  is a phone keyboard's, with its typos and autocorrect.
- **Order.** `unstuk-real-sheet` shuffles the cards per participant, seeded by the participant's code, so no card
  is always first or last. The free prompts come last.
- **Participants.** Adults who'd use the app, not people who build software. Nobody who has seen the training
  data, the labelling guide or the cards' list. The developer doesn't take part. At least 4 people.
- **No model in the loop.** Participants never see Unstuk's answer, so later lines can't adapt to it.

## 3. Consent and storage

This settles plan.md's open question, moved here from M3.

- **Consent, in plain words, before the first card:** *"I'm testing an app that helps fix phone problems. I'll
  describe some situations and you type what you'd ask. I keep your messages on my laptop only, without your
  name, to test the app. They are never shared or put online, and I'll delete them when the project is written
  up, or sooner if you ask."* A "yes" is required. The date and consent version (`v1`) go in the sitting file's
  header.
- **What's kept:** a participant code (P01, P02…), the medium (`in_person` or `chat`), each card's id and the
  text. There are no names, phone numbers or ages. A name or number inside a message becomes `[name]` or
  `[number]` when it's pasted. That is the only edit allowed; typos and wording stay as written.
- **Where:** `data/real/` only. It is gitignored, so the text is never committed. It never goes to the Colab VM
  and is never used for training, tuning or prompt seeding (invariant 9). The chat copy is deleted once it's
  pasted.
- **Claude never reads `data/real/`.** The developer runs the sittings and does the labelling. The tools print
  counts, not text, and the committed report holds aggregates only and quotes no message. That way no real
  message reaches any external service.
- **Deletion:** a participant's lines are removed on request, at any time. Everything in `data/real/` is deleted
  once the M9 write-up is done, along with the embeddings the baselines cache in `ml/cache/` (gitignored, vectors
  keyed by a hash, with no text).

## 4. Labelling

- **The developer labels by `docs/m3-labelling-guide.md`,** using `unstuk-real-label`. It shows one message at a
  time, in an order shuffled across participants. It shows neither the card nor any model's answer. Labels are one
  or two intents or `out_of_scope`, the `vague` tag where the guide allows it, or **drop** for a line that is
  mostly not English (guide, section 9). Dropped lines are counted, not scored.
- If no rule in the guide settles a line, a rule is added to the guide first (guide, section 1), then the line is
  labelled.
- **Freeze:** `unstuk-freeze data/real` locks `messages.jsonl` and `labels.jsonl` before anything is scored. The
  hashes go into `m8-results.md`.
- **Label noise:** a week after freezing, the developer labels a random 40 lines again, blind to the first labels.
  Agreement and kappa (`audit.agreement`) are reported. The frozen labels don't change.

## 5. Scoring, fixed before any message exists

- **Deciders:** the shipped int8 graph as `ml/settings/quantized.json` names it, scored one line at a time with
  every catalog intent offered and behind `catalog/gate.json`'s lines. Against it, the three M4 baselines, from
  their committed settings, are scored as `decision_test.baselines` scores them.
- **The ship rule:** the model ships if it passes every row of the M4 bar (`bar.BAR`) except held-out intents, and
  still does with any one participant left out. The held-out row is reported, not gated. It failed on the proxy
  test (M5 and M6), and plan.md's correction of 2026-10-08 already accepts that the model doesn't name a new
  intent zero-shot: a new intent ships with training lines.
- **Intervals:** paired 95% bootstrap intervals, resampling lines within each participant, so each person keeps
  their share of the lines. *Rejected:* resampling whole participants, the cluster bootstrap. With 4–6
  participants it has too few distinct resamples to give a 95% interval. The leave-one-out rule guards against
  what it would catch, a result carried by one person.
- **Also reported, against plan.md's MVP targets:** top-1 in scope (target 85%), out-of-scope recall (90%), ECE
  (5%) and held-out intents (70%). Also: the gate's outcomes; accuracy per participant, per medium, and for card
  lines against free lines; how often a line's label matches its card's intent; and the most common mistakes, as
  label pairs with counts and no text.
- **Too few lines:** `unstuk-real-test` refuses to score below 150 clear lines or 4 participants. More sittings
  are run until both are met, and only then is the set scored, once.
- **If the model fails:** plan.md's rule applies, and the baseline with the best in-scope accuracy on these lines
  is the one to ship. M8 records that decision, and putting it in the app is new work, since the app now runs only
  the model.

## 6. Tools

| Command | Does |
| --- | --- |
| `unstuk-real-sheet P01 --medium chat` | Writes `data/real/sittings/P01.txt`: the consent header to fill in, then the cards in this participant's order, each with a blank answer line |
| `unstuk-real-import` | Checks every sitting file and writes `data/real/messages.jsonl`. It refuses unknown cards, missing consent, or a participant listed twice |
| `unstuk-real-label` | The blind, resumable labelling loop. It appends to `data/real/labels.jsonl` |
| `unstuk-freeze data/real` | Locks both files (M3's freeze) |
| `unstuk-real-test` | Scores once and writes `ml/reports/real.md`, with aggregates only |

**Order of work:** `unstuk-real-sheet` for each participant, then the sitting, then `unstuk-real-import`,
`unstuk-real-label`, `unstuk-freeze data/real` and `unstuk-real-test`. The relabelling (`unstuk-real-label
--again`) runs a week after the freeze.

**Dry run (2026-10-08).** The whole path ran in a scratch folder on 5 made-up participants built from proxy test
lines, with no real messages. Sheets, import, labels, freeze and scoring all worked, and the report quoted no text.
Confident and wrong failed its row there: 4.9% for the model against TF-IDF's 2.0%. TF-IDF is scored with M2's
placeholder lines (`evaluate.M2_GATE`), as in M5 to M7. The lines repeat proxy test lines, so this says nothing
about real messages, but it is the row to watch.

## Scope

- In: the cards, the four tools, the sittings, labelling, one scoring, and `m8-results.md` with a plain-language
  summary.
- Out: any app change, organic logging, fix success on participants' phones, voice and Hinglish (v2), and new
  training data from real messages (never, by invariant 9).

## Steps

One commit each. Each step ends with a short "what to study" note.

1. This spec, the cards, plan.md's correction and the data card row.
2. `unstuk-real-sheet` and `unstuk-real-import`, with tests on made-up sittings.
3. `unstuk-real-label`, with tests on its parsing and resume behaviour.
4. `unstuk-real-test`, the stratified paired bootstrap and the leave-one-out check, with tests on synthetic lines.
5. *The developer's part:* sittings, labelling and the freeze.
6. Scoring once, `m8-results.md` and `m8-summary.md`.
