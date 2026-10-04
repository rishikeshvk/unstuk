# Unstuk design: Soft Tactile

2026-10-04 · The design and UX pass between M2 and M3. The canvas with every screen, the logo and the motion
storyboard is the Claude Design artifact
[Unstuk app design](https://claude.ai/artifact/W8xwDLo8Ak3RKrJ6TX12ZT) (private to the owner until shared).

## Philosophy: calm core, expressive surface

- **The flow is calm and single-task**, in the Google Go / Android Go manner: one question or action per screen,
  plain words, large type (body 18sp and up), 48dp+ targets, and the main action pinned where a thumb finds it.
- **The surface has character**, because Unstuk is also a portfolio piece: a signature line animation, scalloped
  shapes, a display typeface, haptics, and an optional look at the engineering under each fix.
- **No decoration ever gates an action.** Every animation runs alongside the work, snaps to its end state when
  "Remove animations" is on, and has a text equivalent for TalkBack.

Rejected directions: *Night Signal* (dark instrument panel; reads as technical for non-technical users) and
*Cobalt Thread* (colour-blocked editorial; its header costs space on every screen). Both are kept on the canvas.

## Tokens

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Ground | `#F6F1EA` | `#17141F` | Screen background, window background, splash |
| Surface | `#FFFFFF` | `#24202E` | Cards, tiles, fields |
| Ink (primary) | `#1F1B2E` | `#F3EEE8` | Text and every primary button |
| Muted | `#4A4458` | `#BDB5C8` | Secondary text |
| Tangerine (tertiary) | `#E8693A` | `#FF8A57` | Shapes, icons, "found"/"fixed" marks; never under text |
| Tint (tertiaryContainer) | `#FCE3D3` | `#3B2A2A` | Icon wells, banner, "needs you" shapes |

Dynamic colour is off: a wallpaper must never make the main button low-contrast. Type is Bricolage Grotesque
ExtraBold for headlines and Figtree for everything read, bundled as Latin subsets (about 105 KB, OFL, licences in
`android/app/src/main/assets/licenses/`). Shapes: pill buttons, 22–32dp cards, 14dp icon wells, and the
scallop shapes (`ScallopShape.Cookie` for progress and success, `ScallopShape.Burst` for "needs you").

## The Unknot

One lead-in, one round loop, then a tick: the snag, then the fix. Its path lives once, in
`res/values/paths.xml`, and feeds the adaptive icon (with a themed monochrome layer), the animated splash, and
`UnknotMark`, which has four moments:

| Moment | Where | What it does |
| --- | --- | --- |
| Loop | Working | A segment travels the line for as long as the fix runs |
| Untangle | Done | The loop pulls straight into a tick, with a confirm haptic; only after a fresh read verified the fix |
| Wobble | Didn't catch that, guides | The knot stays tied and rocks gently |
| Tick | Already fine | The plain tick, still |

## UX map

| Moment | Screen |
| --- | --- |
| App open | Home: the question, a field that types example complaints, Help me, and six topics. A dot on Access and a dismissible banner while a grant is missing |
| Topic | The tile grows into the topic screen (container transform); its 1–5 problems as option cards |
| No match | "I didn't quite catch that": the words kept in the field, an example, and topics. Never the full list |
| Unsure | "Which sounds most like it?": the user's words quoted, up to three options, "None of these" |
| Confirm | "Found it", the finding and why, the diagnosis scan, what will happen (screen moves by itself, or you tap in Settings), and a button named after the action |
| Working | The looping line and "Working on Do Not Disturb…"; back is blocked so a run never loses its result |
| Done | The untangle, the fix's own success line, the scan, a collapsed "How I fixed it" ladder timeline, and at most one next cause as a card |
| Already fine / All clear / Still not working? | Calm states with the intent's tips |
| Guide | Steps with the reason they are steps (risky, couldn't do it, still the same), Open settings, and "I've done it, check for me", which counts as fixed only after a fresh read |
| Locked phone | "Unlock your phone first", then Try again for the same fix |

Copy rule: success text states only what was verified ("The ringer is set to ring", never "Your phone will ring
again"). The fix copy (`subject`, `finding`, `why`, `done`) and each intent's `area` live in the catalog.

## Verification (Moto Edge 30, Android 14)

- e2e suite: 19/20 on the full run, 0 false successes. `no_internet_data` replied "all clear" when it ran
  straight after the airplane-mode case, before the phone had dropped offline; it passed 3/3 on rerun. The
  harness needs a settle wait there; the app's answer matched the state it read.
- Walked by hand through the real UI: phone doesn't ring → verified Done; decline; clarify; confirm (panel
  hint); high-risk guide; topic → all clear with tips. Checked in light and dark, at 1.3× font scale (topics
  drop to one column), and with animations removed.
- Not yet checked: a full TalkBack pass over every screen.
