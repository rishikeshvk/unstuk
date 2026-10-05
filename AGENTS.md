# Unstuk: agent instructions

## What this is
An offline Android app that fixes a non-technical user's phone from a plain complaint ("phone doesn't ring"). A tiny
on-device decision model picks one fix from a fixed catalog; deterministic code performs it and checks that it
worked. Plan and philosophy: @docs/plan.md. Milestone specs are in `docs/mN-spec.md`.

## Hard invariants: never violate
1. The model decides; code acts. Model output is only a choice among supplied options, a probability or a level.
   Never execute, parse or display model-generated free text as an action.
2. No action reports success until a fresh read of device state confirms it. A timeout is a failure, never a
   success.
3. Every fix goes through the risk gate: automatic only when it is low risk and above the confidence threshold,
   confirmed by the user when it is low risk below the threshold or medium risk, and guided steps only when it is
   high risk. Out-of-scope or very low-confidence complaints get a polite decline or a clarifying question.
   Destructive fixes are never automated.
4. The app has no `INTERNET` permission, and logs and traces stay on the device.
5. The executor tries the ladder in order, skipping rungs a fix doesn't have: direct API, then Settings Panel or
   deep link (the app opens the screen and the user taps), then accessibility automation (the app's service taps,
   in Quick Settings or in Settings), then guided steps. Accessibility automation is never the only path to a fix.
6. OEM selectors (resource-ids, label variants) are data files, not code.
7. Anything that triggers automation from outside the app (test receivers, debug intents) exists only in debug
   builds.
8. The catalog (intents, option texts, playbooks, risk tiers) has one source of truth, which both training and the
   app read. Option IDs are stable once used.
9. Real user messages are never committed, never used for training or prompt seeding, and held-out intents stay
   held out.
10. The neural model ships only if it beats the baselines on the real test set.
11. The accessibility service never sets `isAccessibilityTool`. Unstuk is not an accessibility tool, and the
    Advanced Protection fallback depends on being honest about that.

## Stack and layout
Directories are created by the milestone that first needs them.
- `android/`: Kotlin, Jetpack Compose, Gradle. Native only, because the accessibility service and the system
  APIs need it. (M1)
- `catalog/`: intents, option texts, playbooks and risk tiers. (M2)
- `ml/`: Python 3.12 with uv for data, baselines, training, evaluation and ONNX export. Training runs on Colab,
  since this machine has no GPU, through the `colab` CLI (google-colab-cli; the colab-operator skill drives it).
  Only code, the catalog and `data/clean`, `data/state` and `data/nodes` go to the VM. (M3+)
- `data/`: seed phrasings (committed) and `data/real/` (gitignored, never committed).
- `docs/`: plan, milestone specs and research notes.

## Conventions
- Kotlin: ktlint and Android lint. Python: ruff, mypy strict and pytest.
- Conventional commits, one logical change per commit.

## Code style
- Code should read on its own: clear names, small focused functions and early returns. Prefer the simplest thing
  that works, and refactor when a second use appears, not before.
- Comments explain *why*, never *what*: only where the code can't say it, in one short line.
- One concept per file. No `utils` or `helpers` catch-alls.
- No speculative code: no unused parameters, flags, config or abstractions "for later".
- Handle errors at boundaries. Don't catch what you can't handle, and never swallow an error silently.
- Add dependencies through the official tools (Android Studio / Gradle version catalog, `uv add`), latest
  compatible. Prefer official generators and templates over hand-written boilerplate.
- Tests check behaviour through public interfaces.

## How to work with me
- I'm building this to learn on-device ML and Android systems work. Use plan mode for any new module: propose a
  design, wait for my approval, then implement.
- One step at a time. Never implement beyond the step I asked for.
- When you make a non-obvious choice, state the alternative you rejected.
- After finishing a task, add a short "what to study from this change" note: the key concepts and one thing worth
  reading further.
