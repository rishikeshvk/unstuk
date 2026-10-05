"""Node-label questions (M3 spec section 9): "which item on the screen is the {target}?".

Training uses only what we'd know before meeting a phone: AOSP strings, the Pixel selectors
and other makers' wording. The Moto's screens are the test, so the Moto selector file is never
read here.
"""

import argparse
import difflib
import html
import json
import random
import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

OPTIONS = (5, 10)
PER_LABEL = 12
DEV_OEM = "xiaomi"
FUZZY = 0.8
SEED = 17
_STRING = re.compile(r'<string name="([a-z0-9_]+)"[^>]*>(.*?)</string>', re.S)
_PUNCT = re.compile(r"[^a-z0-9]+")


class NodeQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    target: str = Field(min_length=1)
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    answer: str
    source: str
    oem: str

    @model_validator(mode="after")
    def answer_is_an_option(self) -> "NodeQuestion":
        if self.options.count(self.answer) != 1:
            raise ValueError("the answer must appear exactly once among the options")
        return self


@dataclass(frozen=True)
class Label:
    item: str
    text: str
    source: str
    oem: str


def aosp_labels(
    strings_dir: Path, targets: dict[str, list[str]], neighbours: list[str]
) -> list[Label]:
    """Labels for the mapped resources, from `<module>-<values dir>.xml` files fetched from AOSP."""
    strings: dict[tuple[str, str], dict[str, str]] = {}
    for path in sorted(strings_dir.glob("*.xml")):
        module, values = path.stem.split("-", 1)
        found = _STRING.findall(path.read_text(encoding="utf-8"))
        strings[(module, values)] = {name: _clean(text) for name, text in found}
    wanted = [(t, r) for t, resources in targets.items() for r in resources]
    wanted += [(r.split(":", 1)[1], r) for r in neighbours]
    labels = []
    for item, resource in wanted:
        module, name = resource.split(":", 1)
        for (file_module, values), table in sorted(strings.items()):
            if file_module == module and name in table:
                labels.append(Label(item, table[name], f"aosp:{values}", "aosp"))
    return _unique(labels)


def selector_labels(selectors: dict[str, object]) -> list[Label]:
    """Tile labels and each Settings path's first step."""
    qs, settings = selectors["quickSettings"], selectors["settings"]
    assert isinstance(qs, dict) and isinstance(settings, dict)
    labels = [
        Label(t, text, "selectors:pixel", "google")
        for t, s in qs["tiles"].items()
        for text in s["labels"]
    ]
    labels += [
        Label(t, text, "selectors:pixel", "google")
        for t, steps in settings["paths"].items()
        for text in steps[0].get("labels", [])
    ]
    return _unique(labels)


def oem_labels(sheet: str) -> list[Label]:
    """`## item` headers, then `maker | label` lines. Not the complaint-sheet format: here `|`
    splits maker from label, not text from tags."""
    labels = []
    item = None
    for raw in sheet.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            item = line.removeprefix("## ").strip()
        elif "|" in line and item is not None:
            oem, _, text = line.partition("|")
            labels.append(Label(item, text.strip(), "oem-variants", oem.strip().lower()))
    return _unique(labels)


def build(
    labels: Sequence[Label], descriptions: dict[str, str], seed: int = SEED
) -> list[NodeQuestion]:
    """Questions for every label of every target; distractors never belong to the target."""
    rng = random.Random(seed)
    own: dict[str, set[str]] = defaultdict(set)
    for label in labels:
        own[label.item].add(_key(label.text))
    pool = sorted({label.text for label in labels}, key=_key)
    questions = []
    for label in labels:
        if label.item not in descriptions:
            continue
        candidates = [text for text in pool if _key(text) not in own[label.item]]
        for n in range(PER_LABEL):
            distractors = _distinct(
                rng.sample(candidates, len(candidates)), rng.randint(*OPTIONS) - 1
            )
            options = [label.text, *distractors]
            rng.shuffle(options)
            questions.append(
                NodeQuestion(
                    id=f"node-{label.item}-{_key(label.text)}-{label.oem}-{n:02d}",
                    target=label.item,
                    question=f"Which item on the screen is {descriptions[label.item]}?",
                    options=options,
                    answer=label.text,
                    source=label.source,
                    oem=label.oem,
                )
            )
    return questions


def split_by_oem(
    questions: Sequence[NodeQuestion],
) -> tuple[list[NodeQuestion], list[NodeQuestion]]:
    """One maker's wording is held out, so dev measures a maker the model hasn't seen."""
    return [q for q in questions if q.oem != DEV_OEM], [q for q in questions if q.oem == DEV_OEM]


def match(options: Sequence[str], known: Sequence[str]) -> str | None:
    """The baseline: an exact, then a normalised, then a fuzzy match against known labels."""
    for option in options:
        if option in known:
            return option
    keys = {_key(k) for k in known}
    for option in options:
        if _key(option) in keys:
            return option
    scored = [
        (max(difflib.SequenceMatcher(None, _key(o), k).ratio() for k in keys), o) for o in options
    ]
    score, best = max(scored)
    return best if score >= FUZZY else None


# The Settings screen whose first path step names each target; Quick Settings tiles are on "qs".
SETTINGS_SCREEN = {"airplane_mode": "network", "dnd": "dnd", "talkback": "accessibility"}
MAX_LABEL = 40


def screen_options(dump: dict[str, object]) -> list[str]:
    """Every distinct short label on a dumped screen, text and content description alike."""
    nodes = dump["nodes"]
    assert isinstance(nodes, list)
    texts = [n.get(field) for n in nodes for field in ("text", "description")]
    return _distinct([t for t in texts if t and len(t) <= MAX_LABEL], len(texts))


def phone_questions(
    dumps: dict[str, dict[str, object]], selectors: dict[str, object], descriptions: dict[str, str]
) -> tuple[list[NodeQuestion], list[str]]:
    """Test questions from a phone's dumps: options are the labels really on the screen, and the
    answer is the one the phone's selector file names there. Places with no match are listed."""
    oem = str(next(iter(dumps.values()))["manufacturer"]).lower() if dumps else "unknown"
    qs, settings = selectors["quickSettings"], selectors["settings"]
    assert isinstance(qs, dict) and isinstance(settings, dict)
    places = [(t, "qs", tile["labels"]) for t, tile in qs["tiles"].items()]
    places += [
        (t, SETTINGS_SCREEN[t], steps[0].get("labels", []))
        for t, steps in settings["paths"].items()
        if t in SETTINGS_SCREEN
    ]
    questions, missing = [], []
    for target, where, labels in sorted(places):
        if target not in descriptions:
            continue
        if where not in dumps:
            missing.append(f"{target} on {where}: screen not dumped")
            continue
        options = screen_options(dumps[where])
        answers = [o for o in options if _key(o) in {_key(label) for label in labels}]
        if not answers:
            missing.append(f"{target} on {where}: no label on screen matches the selector file")
            continue
        questions.append(
            NodeQuestion(
                id=f"node-test-{where}-{target}",
                target=target,
                question=f"Which item on the screen is {descriptions[target]}?",
                options=options,
                answer=answers[0],
                source=f"dump:{where}",
                oem=oem,
            )
        )
    return questions, missing


def baseline_accuracy(
    questions: Sequence[NodeQuestion], known: Sequence[Label]
) -> list[tuple[str, bool]]:
    """Whether the string-matching baseline picks each answer, from labels known in advance."""
    by_target: dict[str, list[str]] = defaultdict(list)
    for label in known:
        by_target[label.item].append(label.text)
    return [(q.id, match(q.options, by_target[q.target]) == q.answer) for q in questions]


def _distinct(texts: Sequence[str], count: int) -> list[str]:
    chosen: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if _key(text) not in seen:
            chosen.append(text)
            seen.add(_key(text))
        if len(chosen) == count:
            break
    return chosen


def _unique(labels: Sequence[Label]) -> list[Label]:
    seen: set[tuple[str, str, str]] = set()
    kept = []
    for label in labels:
        key = (label.item, _key(label.text), label.oem)
        if label.text and key not in seen:
            seen.add(key)
            kept.append(label)
    return kept


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        text = text[1:-1]
    return html.unescape(text.replace("\\'", "'").replace('\\"', '"'))


def _key(text: str) -> str:
    return _PUNCT.sub("", text.lower())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build node-label questions.")
    commands = parser.add_subparsers(dest="command", required=True)
    aosp = commands.add_parser("aosp", help="extract the mapped AOSP strings")
    aosp.add_argument("strings_dir", type=Path)
    aosp.add_argument("mapping", type=Path)
    aosp.add_argument("out", type=Path)
    make = commands.add_parser("build", help="write train and dev questions")
    make.add_argument("mapping", type=Path)
    make.add_argument("aosp", type=Path)
    make.add_argument("pixel", type=Path)
    make.add_argument("oem_sheet", type=Path)
    make.add_argument("out", type=Path)
    test = commands.add_parser("test", help="test questions from a phone's dumps, and the baseline")
    test.add_argument("mapping", type=Path)
    test.add_argument("aosp", type=Path)
    test.add_argument("pixel", type=Path)
    test.add_argument("phone", type=Path, help="the phone's own selector file")
    test.add_argument("dumps", type=Path, help="folder of <screen>.json dumps")
    test.add_argument("out", type=Path)
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    if args.command == "test":
        descriptions = {t: spec["description"] for t, spec in mapping["targets"].items()}
        dumps = {
            p.stem: json.loads(p.read_text(encoding="utf-8")) for p in args.dumps.glob("*.json")
        }
        phone = json.loads(args.phone.read_text(encoding="utf-8"))
        questions, missing = phone_questions(dumps, phone, descriptions)
        lines = "".join(q.model_dump_json() + "\n" for q in questions)
        args.out.write_text(lines, encoding="utf-8")
        known = [Label(**row) for row in json.loads(args.aosp.read_text(encoding="utf-8"))]
        known += selector_labels(json.loads(args.pixel.read_text(encoding="utf-8")))
        scores = baseline_accuracy(questions, known)
        right = sum(ok for _, ok in scores)
        print(f"{len(questions)} test questions in {args.out}; baseline {right}/{len(scores)}")
        for qid, ok in scores:
            print(f"  {'right' if ok else 'wrong'}  {qid}")
        for line in missing:
            print(f"  missing  {line}")
        return
    if args.command == "aosp":
        targets = {t: spec["resources"] for t, spec in mapping["targets"].items()}
        found = aosp_labels(args.strings_dir, targets, mapping["neighbours"])
        rows = [label.__dict__ for label in found]
        args.out.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{len(rows)} AOSP labels in {args.out}")
        return
    labels = [Label(**row) for row in json.loads(args.aosp.read_text(encoding="utf-8"))]
    labels += selector_labels(json.loads(args.pixel.read_text(encoding="utf-8")))
    labels += oem_labels(args.oem_sheet.read_text(encoding="utf-8"))
    descriptions = {t: spec["description"] for t, spec in mapping["targets"].items()}
    train, dev = split_by_oem(build(_unique(labels), descriptions))
    for name, questions in (("train", train), ("dev", dev)):
        lines = "".join(q.model_dump_json() + "\n" for q in questions)
        (args.out / f"{name}.jsonl").write_text(lines, encoding="utf-8")
    print(f"{len(train)} train and {len(dev)} dev questions in {args.out}")
