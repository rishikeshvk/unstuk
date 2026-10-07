# Unstuk: On-Device Decision Model Plan

Oct 1, 2026 · @Rishikesh V K

This file is the source of truth for the plan; dated corrections and decisions are added here.

## Philosophy

The model decides; code acts. A tiny on-device decision model maps a lay complaint plus the phone's current state to one fix from a fixed catalog, and deterministic code performs that fix.

- **Decide, don't generate.** Non-technical users describe symptoms ("phone is talking to me"), not settings (TalkBack). The hard part is that mapping, which is a classification over a known set of fixes. Generating text adds size, latency and risk with no gain. Following Jev's contract, every decision is a typed question (Choice, Noul or Score) about the same state, with options supplied at runtime.
- **State is half the answer.** "Internet not working" means different things when airplane mode is on vs. mobile data is off. The model reads the query and a snapshot of device state together, in the Jev style of state plus typed question.
- **Calibrated confidence gates autonomy.** The model returns a probability, not just a label. Low-risk fix with high confidence runs automatically; anything else asks or guides. Calibration is a feature, not a metric.
- **Capable first, then small.** Budget is 50–100 MB; target about 40–60 MB. Spend bytes on one stronger backbone that answers many typed questions, not on generic runtime bloat.
- **Offline first.** The user whose internet is broken is exactly the user who needs help, so nothing depends on a server.
- **Honest baseline.** A keyword or fastText baseline is built first. The neural model must beat it on real user queries, or it does not ship.

## Problem catalog

About 40 recurring issues cover most everyday phone-support requests; the MVP takes roughly 15 of them. Each issue becomes one intent with a playbook and a risk tier.

| Area | Lay complaint (example) | Likely causes the app checks | Risk |
| --- | --- | --- | --- |
| Connectivity | "Internet not working" | Airplane mode on, mobile data off, Wi-Fi off, data saver, data limit hit, Private DNS set wrong | Low |
| Connectivity | "Wi-Fi connected but nothing loads" | Captive portal, wrong date/time, Private DNS, forget-and-rejoin network | Medium |
| Calls & sound | "Phone doesn't ring" | Do Not Disturb, ringer silent/vibrate, ring volume zero, bedtime mode | Low |
| Calls & sound | "Can't hear the person on call" | Audio routed to Bluetooth earbuds/car, call volume low | Low |
| Notifications | "WhatsApp messages come late or not at all" | Battery optimization, notification permission off, DND, data saver | Low |
| Accidental modes | "Phone is talking to me / double tap needed" | TalkBack on | Medium |
| Accidental modes | "Screen is black and white / colours inverted / zoomed" | Bedtime grayscale, colour inversion, magnification, display size | Low |
| Display | "Screen too dim / turns off too fast / won't rotate" | Brightness, adaptive brightness, screen timeout, rotation lock | Low |
| Display | "Letters too small" | Font size, display size | Low |
| Bluetooth | "Earphones not connecting" | Bluetooth off, paired to another device, re-pair | Medium |
| Storage & speed | "Phone is slow / storage full" | Storage nearly full, WhatsApp media, cache | Medium |
| Battery | "Battery drains fast" | Brightness, battery saver off, location always on | Low |
| Permissions | "Camera/mic/location not working in an app" | Permission denied for that app | Low |
| Messages | "OTP not coming" | SMS default app, spam filter, inbox full, wrong SIM for SMS | Medium |
| Time | "Apps say certificate/time error" | Automatic date and time off | Low |
| Apps | "App icon disappeared" | App disabled, hidden, removed from home screen | Medium |
| Network | "No signal / only 2G" | Preferred network type, VoLTE off, SIM disabled | Medium |
| Destructive | "Nothing works, reset network" | Reset network settings, clear app data | High |

Accidentally enabled TalkBack deserves early attention: it is the most panic-inducing case, and it also blocks the user from operating your own app.

## Architecture

```text
complaint + device-state snapshot
        │
        ▼
decide(state, questions)   one batched call: Choice over intents, Noul "out of scope?", Score urgency
        │  intent + calibrated probability
        ▼
risk gate ── out of scope or very low confidence ──► polite decline or clarifying question
        ├── low risk, above threshold ───────────────► run automatically
        ├── low risk below threshold, or medium risk ─► confirm with the user first
        └── high risk ───────────────────────────────► guided steps only
        ▼
playbook → executor ladder: direct API → Settings Panel / deep link → accessibility automation → guided steps
        ▼
verify against fresh device state → report
```

Out-of-scope queries exit at the risk gate with a polite decline. Every action is checked against fresh device state before the app reports success.

The executor asks the same model its own questions: a Choice over on-screen node labels to find the target switch, and a Choice over guide cards for issues the app cannot automate.

## Model plan

Unstuk runs a pocket System One model: a \~33M-parameter encoder backbone with NanoJev-style decision heads. It answers typed questions about one device state, with options supplied at runtime and calibrated probabilities. An earlier draft had drifted into a fixed-head classifier; that is now a baseline, not the product.

**The contract (mirrors Jev).**

| Question type | Returns | Unstuk examples |
| --- | --- | --- |
| Choice (2–255 options) | One option, a probability per option, confidence | Which issue is this? Which on-screen node is the airplane switch? Which guide card fits? |
| Noul (yes/no) | Probability the statement is true | Is this out of scope? Does the user name a specific app? Is a follow-up question needed? |
| Score (2–10 ordered levels) | Level distribution and expected value | How urgent does the user sound? |

All questions about one state go in a single batched call; the app's code branches on the answers.

**Architecture (adapted from NanoJev).** NanoJev puts decision heads on a 0.6B Qwen3 backbone; Unstuk uses a small encoder so it fits on the phone.

- The backbone encodes state plus question once.
- Option texts go through the same backbone. Catalog options are cached at build time; runtime options such as on-screen node labels are encoded in one batch.
- Choice head: light cross-attention plus set attention over the state and all options, one score per option, softmax. Noul: a sigmoid head. Score: a Choice over ordered level descriptions plus an expected value.
- A new issue is new option text plus a playbook. It works zero-shot at first and gets fine-tuned later.

**Backbone candidates (approximate sizes).**

| Candidate | Params | int8 size | Notes |
| --- | --- | --- | --- |
| all-MiniLM-L6-v2 | 22M | \~23 MB | Fastest; good starting point |
| bge-small-en-v1.5 | 33M | \~34 MB | Strong English; the supervised encoder in the independent Jev eval |
| Ettin small encoder | \~32M (check model card) | \~33 MB | Modern open recipe that outperforms ModernBERT |

Pick by accuracy on the real user test set.

**Training.**

1. Data: each sample is (state, question, options, correct option). Seed phrasings expanded by an LLM to 300–1000 per intent, plus Google's Mobile Actions dataset (CC-BY-4.0) for command-style phrasings, plus accessibility-tree dumps from Pixel, Samsung and Xiaomi for node questions. Shuffle option order and sample distractor subsets so the model learns to choose among whatever it is given.
2. Real test set: 150–300 real user messages. Hold out 3–5 intents entirely to measure zero-shot accuracy on unseen options.
3. Baselines: fastText, and a frozen bge-small + logistic regression classifier (the strongest option in the independent Jev eval when labels exist).
4. Train backbone and heads with cross-entropy, then add a Brier / proper-scoring loss: an "RLCD-lite" that rewards probabilities matching observed frequencies, following NanoJev's CE, Brier and paired proper-reward recipe.
5. Optional teacher: soft labels from a larger open System One model (Laya, Kev or NanoJev on a Colab GPU), then distill. Check each model's licence before training on its outputs.
6. Calibrate: temperature scaling per question type. Report ECE, reliability diagrams, and how often confidence is ≥ 0.99 yet wrong.
7. Quantize to int8 and re-check calibration afterwards.
8. Export to ONNX for ONNX Runtime Android or LiteRT, behind a Kotlin `decide(state, questions)` API.

**Correction (2026-10-05): data.** Real user messages can't be collected during M3. M3 builds a *proxy* test set
instead, written by hand and by other LLM families than the training data, and frozen before any training data
exists. M5 picks a model on it; the M8 field test confirms that choice on real messages before the model counts as
shipped (invariant 10). Intent labels come from the words alone, and a separate state slice measures whether state
helps. Generation runs in Claude Code sessions and chat apps, not through an API. See the
[M3 spec](m3-spec.md).

**Correction (2026-10-05): baselines.** fastText is left out: it was archived in March 2024 and ships no wheel for
this platform, and character n-grams in a TF-IDF baseline cover its typo strength. M4 adds a zero-shot baseline,
which compares the complaint with each option text using the frozen encoder, and is the only baseline that can
score held-out intents. No single baseline won everywhere, so M5's bar is set per metric by the best baseline. See
[M4 results](m4-results.md).

**Correction (2026-10-08): new intents.** "A new issue works zero-shot at first" doesn't hold for the fine-tuned
model. On dev, its Choice head names never-trained intents about as well as the frozen encoder (77–83% against
83.5%), but every out-of-scope check tried in M5 declines a fifth or more of a new intent's lines as unfamiliar.
A new intent therefore ships with training lines, not option text alone. See the
[M5 spec](m5-spec.md), section 3.

**Why not a small LLM?** Even at 100 MB, 0.5B-class models (\~300 MB+ at 4-bit) don't fit. FunctionGemma 270M is the closest generative option for phone actions, but it maps explicit commands ("turn on the flashlight") rather than symptoms, and at 270M parameters it is likely past the budget. Gemini Nano is used only as an optional System 2 where the phone has it.

## Size budget

Target about 40–60 MB for the arm64 APK, inside the 50–100 MB budget, with headroom kept for v2 voice. Figures are approximate and must be measured.

| Component | Plan | Approx. size |
| --- | --- | --- |
| App code + UI | Jetpack Compose + R8 | 3–5 MB |
| Inference runtime | ONNX Runtime Android or LiteRT, arm64 only | 5–20 MB (smaller with a reduced-operator build) |
| Backbone + decision heads | \~33M params, int8 | 25–35 MB |
| Tokenizer, cached option encodings, guide cards, playbooks | Bundled assets | 1–3 MB |
| Voice (v2) | Android's on-device SpeechRecognizer | \~0 MB |
| **Total** |  | **\~35–60 MB** |

**Where the bytes go.** The encoder dominates. In a 384-dim encoder with a 30k-token vocabulary, the embedding table alone is about 11.7M parameters, roughly a third of the model. Pruning the vocabulary to domain tokens could save around 10 MB; it is now a lever to pull only if needed, not a requirement.

**Lessons from browser-side models.** Transformers.js runs this same class of quantized ONNX sentence encoders inside browsers, which is good evidence they run comfortably on mid-range phones. Carry over its habits: ship one ABI via App Bundle splits, keep weights uncompressed in assets and memory-map them, and load the model once in the background at app start. Expect inference in the tens of milliseconds for short inputs; measure on the oldest test phone.

## Android constraints

Reading state is easy; changing it is mostly blocked for normal apps. That makes the executor, not the model, the hardest engineering in this project.

| Action | Direct API for a third-party app? | Fallback |
| --- | --- | --- |
| Read connectivity, airplane mode, DND, storage, battery, permissions | Yes | — |
| Toggle Wi-Fi | No (blocked for apps targeting Android 10+) | Internet / Wi-Fi Settings Panel, one tap |
| Toggle Bluetooth | No (blocked for apps targeting Android 13+) | System enable prompt or Settings |
| Toggle airplane mode | No (system apps only) | Accessibility automation in Quick Settings |
| DND, ringer mode | Ringer: yes, with notification policy access. DND: **no** for apps targeting Android 15+ (see note) | Accessibility automation in Quick Settings or Modes |
| Brightness, screen timeout, rotation | Yes, with WRITE\_SETTINGS special permission | — |
| Turn off TalkBack, colour inversion | No | Accessibility automation or guided steps |
| App permissions, battery optimization | Partly (deep-link to the app's settings page) | Accessibility automation |

**Correction (2026-10-03): DND.** Apps targeting Android 15 (API 35) or higher can no longer change global DND
state. `setInterruptionFilter` now only switches the app's own implicit `AutomaticZenRule`, so it cannot turn off DND
the user (or bedtime mode) turned on. See the
[Android 15 behaviour changes](https://developer.android.com/about/versions/15/behavior-changes-15). On phones
running Android 15+, DND therefore moves to the accessibility rung, beside airplane mode. Older phones keep the
direct call.

**Executor ladder (try in order).** Direct API, then a Settings Panel or deep-link intent, then accessibility automation with per-OEM selectors, then guided steps with screenshots. A rung is defined by who taps: on the Settings Panel / deep-link rung the app opens the screen and the user taps; on the accessibility rung the app's service taps, whether in Quick Settings or in a Settings screen. A fix skips rungs it doesn't have (airplane mode has no direct API).

**Accessibility automation is fragile.** Settings labels, paths and layouts differ across Pixel, One UI, HyperOS and ColorOS, and change with updates. Prefer resource-ids, fall back to semantic matching of on-screen labels with the encoder (so "Flight mode" and "Aeroplane mode" resolve to the same target), verify state after every action, and treat each OEM as a separately tested target.

**Distribution friction.** On Android 13+, sideloaded apps hit "restricted settings" and cannot have their accessibility service enabled until the user allows it from App info. Play Store release requires an Accessibility API declaration and review, and Google scrutinizes non-accessibility uses. Verify current policy before planning a Play launch.

**Android 17 Advanced Protection.** With Advanced Protection on, Android 17 blocks accessibility services for any app not flagged as an accessibility tool, and Google says assistants and automation apps don't qualify. Detect the mode with `AdvancedProtectionManager` and skip straight to Settings Panels and guided steps.

## MVP scope and validation

The MVP answers one question: do real users' typed complaints map to the right fix often enough to be useful?

**In scope.** Typed English only; about 15 intents from the catalog (connectivity, ringer/DND, notifications, accidental modes, display, permissions, date/time); two targets (Pixel emulator plus a Moto Edge 30 on Android 14, chosen in the M1 spec); risk-tiered execution (auto for low-risk + high confidence, confirm otherwise, guide-only for high risk).

**Out of scope.** Voice (v2, via Android's on-device recognizer at \~0 MB), more OEMs, Play Store release, destructive fixes.

**Success metrics.**

| Metric | Target |
| --- | --- |
| Top-1 intent accuracy on real user queries | ≥ 85% |
| Out-of-scope detection (correctly says "I can't help with this") | ≥ 90% |
| Expected calibration error | ≤ 0.05 |
| Fix success rate on device, end to end | ≥ 70% |
| Inference latency on a mid-range phone | < 100 ms |
| APK size (arm64) | < 60 MB |
| System One model vs. fastText and fixed-head encoder baselines | Clear win on real queries, or ship the baseline |
| UI label matching on both test devices (right switch found) | ≥ 95% |
| Zero-shot accuracy on held-out intents (added as option text only) | ≥ 70% |

## Learning roadmap

Build the riskiest, non-ML part first, so the model never waits on an executor that can't work. Each step ends in something demo-able.

1. **Executor spike (1–2 weeks).** Accessibility service that turns off airplane mode and DND on two devices, with state verification. Proves the hard part.
2. **Catalog + rules (1 week).** 15 intents, playbooks, risk tiers, device-state snapshot. A keyword matcher drives it end to end.
3. **Data (1–2 weeks).** Seed phrasings, LLM-generated synthetic set, real user test set.
4. **Baseline (2–3 days).** fastText-style classifier, evaluated on the real set. This is the bar.
5. **Encoder + heads (1–2 weeks).** Train the encoder backbone with NanoJev-style Choice, Noul and Score heads on Colab; train the fixed-head classifier baseline alongside.
6. **Compress + calibrate (1 week).** Brier / proper-scoring training (RLCD-lite), temperature scaling, int8 quantization; optional distillation from an open System One teacher.
7. **On-device inference (1–2 weeks).** ONNX Runtime or LiteRT on device behind a Kotlin decide(state, questions) API; node matching and guide cards go through the same API. A hand-written forward pass is a stretch goal.
8. **Field test (2 weeks).** Install on test users' phones; log decisions locally; measure the MVP metrics.
9. **Portfolio write-up.** Size waterfall, calibration plots, baseline comparison, failure analysis.

## Recent developments considered

Eight recent developments shaped the plan above; the biggest change is copying the open Jev replicas' decision-head design at encoder scale.

| Development | What it is | Effect on Unstuk |
| --- | --- | --- |
| [Jev](https://ahmetbalaman.com/en/blog/what-is-jev-system-one-reflex-model-en/) (TypeSafe, Sep 2026) | Closed, hosted System One model: state plus typed Choice / Score / Noul questions, calibrated probabilities, trained with RLCD | Unstuk copies the contract, not the model |
| [NanoJev](https://github.com/chenyangcun/NanoJev) | Open 0.6B replica: decision heads on Qwen3-0.6B, dynamic 2–255 candidates, CE / Brier / paired proper-reward training | Reference architecture and training recipe, scaled down to a \~33M encoder |
| [Open System One models](https://github.com/rupeshpoojary9/awesome-open-system-one) (Laya 421M, Von, Kev, poorjev) | Local Jev-style models, hundreds of millions of parameters and up | Too big to ship; usable as Colab teachers for soft labels (check licences) |
| [Independent Jev eval](https://github.com/ickma2311/jev-baselines-eval) | With 10k labels, a frozen bge-small + logistic regression beat Jev on Banking77 (0.933 vs 0.832); Jev gave confidence 1.0 on 102 of 200 CLINC150 items, 6 of them wrong | Supervised training on in-domain data is the core; calibration must be measured, never assumed |
| [FunctionGemma 270M + Mobile Actions](https://developers.googleblog.com/on-device-function-calling-in-google-ai-edge-gallery/) | Google's on-device function-calling model and an open Android-actions dataset | Not shipped (likely over budget, command- not symptom-oriented); dataset used for augmentation |
| [Gemini Nano Prompt API](https://developers.google.com/ml-kit/genai) | Shared on-device LLM via AICore, zero app size, flagship phones only | Optional System 2 for explanations when present; never required |
| [EmbeddingGemma](https://developers.googleblog.com/introducing-embeddinggemma/) (308M) | Best open multilingual embedding model under 500M; \~200M of its parameters are embeddings | Too large to ship; strong teacher for v2 Hinglish distillation |
| [Android 17 Advanced Protection](https://thehackernews.com/2026/03/android-17-blocks-non-accessibility.html) | Blocks accessibility services for apps not flagged as accessibility tools while the mode is on | Executor must detect it and fall back to Settings Panels and guided steps |

## Key risks and open questions

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| The model is the easy part | Most fixes need accessibility automation, which is OEM-specific and breaks with updates | Executor spike first; Settings Panels and deep-links before automation |
| A simple baseline may match the neural model | 15 intents in English is a modest task | Treat "fastText wins" as a valid finding; the neural model must earn its place on messy real queries |
| Synthetic data mismatch | LLM-written complaints are cleaner than real ones | Real user test set from day one; add hard negatives and typos |
| Calling it "Jev-like" | A 33M model has far less zero-shot breadth than Jev | Keep Jev's Choice / Noul / Score contract; report zero-shot accuracy separately from trained intents |
| Onboarding paradox | Users who can't find settings must install the app and enable an accessibility service, via restricted settings | You install and set it up for them; one-time cost |
| Competition from built-ins | Gemini on Android and OEM device-care apps already toggle common settings | Differentiate on symptom-to-cause diagnosis using device state, offline |
| Trust and safety | An app that can tap anything is a security-sensitive component | No network permission, local-only logs, risk tiers, confirm before medium-risk actions |
| Bigger model, slower start | A 25–35 MB encoder adds load time and RAM on low-end phones | Memory-map weights, warm up in the background at launch, benchmark on the oldest test phone |
| Accessibility access shrinking | Android 17 Advanced Protection blocks non-accessibility tools; more restrictions likely | Keep accessibility automation one rung of the ladder, never the only path |

**Open questions.**
- *Answered (2026-10-03):* test targets are a Pixel emulator and a Moto Edge 30 (Android 14); see the M1 spec.
- *Answered (2026-10-04):* a low-risk fix below the confidence threshold is confirmed with the user, not run
  automatically. The threshold value is set in the M2 spec and tuned in M6.
- *Answered (2026-10-04):* the app's look and UX are set before M3: the "calm core, expressive surface" design
  in [design-spec.md](design-spec.md), with the Unknot logo and one screen per reply.
- *Settle in the M8 spec (moved from M3, 2026-10-05):* consent and storage rules for real user messages. M3 uses
  a proxy test set, so real messages are first collected in the M8 field test.
- *Settle in the M7 spec:* how the int8 model file reaches the APK (Git LFS or a build step). Until then `*.onnx` is
  gitignored.
- *Open:* voice or Hinglish in v2?
