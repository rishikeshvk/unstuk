# Node-label questions

"Which item on the screen is the {target}?", with the labels on a screen as options (M3 spec section 9). The
executor asks the model this when a phone's wording differs from our selector files.

## Training and dev (built without the phone)

| Source | What it gives | File |
| --- | --- | --- |
| AOSP SystemUI, SettingsLib and Settings strings, English, British and Indian English | Each target's official labels and its neighbours' (27 labels) | [`aosp-labels.json`](aosp-labels.json), from [`aosp-map.json`](aosp-map.json) |
| `android/app/src/main/assets/selectors/pixel.json` | Labels confirmed on the Pixel | read at build time |
| A fresh agent's knowledge of Samsung, Xiaomi, Oppo, Vivo and OnePlus wording | 115 labels for 20 items | [`sheets/oem-variants.txt`](sheets/oem-variants.txt), [prompt](oem-variants-prompt.md) |

`selectors/motorola.json` is never read for training: the Moto's screens are the test.

Built with `uv run unstuk-node-labels build` (from `ml/`): for each label of each target, 12 questions with 5–10
options, distractors drawn from other items' labels and never from the target's own (on the Pixel, "Internet" is
the label of both `wifi` and `mobile_data`). **828 train and 132 dev questions**; dev is every question whose answer
comes from Xiaomi's wording, so it measures a maker the model hasn't seen.

AOSP strings are from android.googlesource.com, `refs/heads/main`: `platform/frameworks/base` at
`1cdfff555f4a21f71ccc978290e2e212e2f8b168` and `platform/packages/apps/Settings` at
`7c598253ff60f06f8e6fe046f18fd88e9daa72d3`, fetched as `<module>-<values dir>.xml` and read with
`uv run unstuk-node-labels aosp <dir> aosp-map.json aosp-labels.json`. The Android Open Source Project, licensed
Apache-2.0. TalkBack's label lives in the TalkBack app, not in these files; it comes from the Pixel selectors and
the makers' sheet.

## Test (needs the phone)

The Moto's real screens, dumped by the debug-only label dumper (`android/scripts/dump-labels.sh`), become the test:
the options are the labels actually on each screen, and the answer is the label `motorola.json` names for the
target. Each item on a screen gives one option, its text or else its description, and the answer is the option the
app's own rule (`LabelMatch.kt`: the text before the first ',' or '.') matches to the selector label. The baseline to
beat is `node_labels.match`: exact, normalised, then fuzzy matching against the labels known before meeting the Moto
(AOSP and Pixel only).

On a Moto Edge 30 (Android 14), with the phone unlocked and Unstuk's service on:

```sh
ANDROID_SERIAL=<serial> android/scripts/dump-labels.sh moto     # from the repo root; writes moto/<screen>.json
uv run unstuk-node-labels test ../data/nodes/aosp-map.json ../data/nodes/aosp-labels.json \
  ../android/app/src/main/assets/selectors/pixel.json ../android/app/src/main/assets/selectors/motorola.json \
  ../data/nodes/moto ../data/nodes/test.jsonl                   # from ml/
```

**8 screens, 10 test questions** in [`test.jsonl`](test.jsonl): eight Quick Settings tiles, the DND screen's "Turn off
now" button (dumped with DND on, the state the executor meets it in) and TalkBack in Accessibility. **The baseline
gets 8/10**; see [m3-results.md](../../docs/m3-results.md). The Settings airplane-mode row has no question: the Moto
hides it from Unstuk's accessibility service.
