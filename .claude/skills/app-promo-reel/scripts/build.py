#!/usr/bin/env python3
"""Build <project>/index.html from <project>/src.html.tmpl.

Tokens (the `{{ }}` delimiter never appears in CSS, so @font-face/@media/@keyframes are safe):
  {{D bar}} / {{D bar beat}}   time of that beat (see common.py for the addressing)
  {{E bar}} / {{E bar beat}}   the "and" after that beat
  {{LEN a b}}                  D(b) - D(a) (the build fails when b comes before a)
  {{TO_END bar}}               duration - D(bar) (the build fails when D(bar) is past the end)
  {{calc <expr>}}              arithmetic: numbers, + - * /, parentheses, D(), E(), DURATION
  {{BEFORE_END margin expr}}   renders nothing; the build fails when calc(expr) is less than
                               `margin` seconds before the end (text that must be read)
  {{BEATS}}                    JSON array of every beat time
  {{DOWNBEAT_INDEX}}           index in BEATS of the first downbeat
  {{BEATS_PER_BAR}}            from project.json
  {{DURATION}}                 from project.json
  {{STORES}}                   JSON array of the project's stores (project.json)
  {{WIDTH}} / {{HEIGHT}}       the frame size of the project's format (project.json)
  {{FORMAT}}                   the format: 9:16, 4:5 or 16:9
  {{FRAME_SCALE}}              the frame height divided by the 9:16 height (1 for 9:16): scales
                               pixel distances, e.g. a camera shake, to the frame
  {{MOTION}}                   the text of <project>/motion.js (the spring eases and the MOTION
                               table); the build fails when the file is missing

SFX: cues.json -> <audio> tags in place of `<!--SFX-->`, plus cues.realized.json, the list of
cues actually mixed (finish.py checks sync against that list only). A cue whose file is
missing is skipped with a warning. Cue fields: id, sfx (key in the "sfx" map), at (a calc
expression), offset (s, default 0), volume (default 0.5), align ("attack" default: the
sound's audible attack lands on `at`, skipping any leading silence in the file; "start": the
file starts at `at`; "end": the sound ends at `at`, e.g. a riser tail into the drop), sync
(default true, false for align "end": finish.py checks only cues with a sharp attack).

A silent format (16:9, a web hero) has no beat grid and no sound: no beats.json is read, every
beat token (D, E, LEN, TO_END, BEFORE_END, BEATS, DOWNBEAT_INDEX, BEATS_PER_BAR, and D()/E() inside
calc) exits 2, cues in cues.json or an <audio>/<video> tag in the page exit 2, and cues.realized.json
is written as an empty list. Time the scenes with {{DURATION}} and {{calc DURATION*0.4}}.

Usage: build.py <project_dir>
"""
import ast
import html
import json
import operator
import re
import secrets
import shlex
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FEED_BOXES, FORMATS, SCENE_SETTLE, SCENE_SETTLE_END, SILENT_FORMATS, Grid,  # noqa: E402
                    attack_seconds, die, is_number, is_silent, load_project, media_duration, read_json,
                    scene_spans, scene_windows)

TOKEN = re.compile(r"\{\{\s*([A-Za-z_]+)\s*(.*?)\s*\}\}", re.S)
SFX_FIRST_TRACK = 21
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


class CalcError(ValueError):
    pass


BEAT_TOKENS = ("D", "E", "LEN", "TO_END", "BEFORE_END", "BEATS", "DOWNBEAT_INDEX", "BEATS_PER_BAR")
NO_GRID = (f"{', '.join(SILENT_FORMATS)} is silent and has no beat grid: time the scenes with "
           f"{{{{DURATION}}}} (for example {{{{calc DURATION*0.4}}}})")


def calc(expr, grid, duration):
    """Evaluate arithmetic over D()/E()/DURATION without eval()."""
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise CalcError(f"bad expression {expr!r}: {e.msg}") from None

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = ev(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.Name) and node.id == "DURATION":
            return duration
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("D", "E")
                and not node.keywords and 1 <= len(node.args) <= 2):
            if grid is None:
                raise CalcError(NO_GRID)
            args = [ev(a) for a in node.args]
            if any(a != int(a) for a in args):
                raise CalcError(f"{node.func.id}() takes whole numbers in {expr!r}")
            return getattr(grid, node.func.id)(*[int(a) for a in args])
        raise CalcError(f"not allowed in calc: {ast.dump(node)[:60]} in {expr!r}")

    try:
        return float(ev(tree))
    except (ValueError, ArithmeticError) as e:  # ArithmeticError: 1/0, overflow
        raise CalcError(f"{e} in {expr!r}") from None


def _ints(name, args, n_min, n_max):
    parts = args.split()
    if not n_min <= len(parts) <= n_max or not all(re.fullmatch(r"-?\d+", p) for p in parts):
        raise CalcError(f"{{{{{name} {args}}}}} needs {n_min}-{n_max} whole-number arguments")
    return [int(p) for p in parts]


def substitute(src, grid, project, motion=None):
    duration = project["duration"]

    def sub(m):
        name, args = m.group(1), m.group(2)
        if grid is None and name in BEAT_TOKENS:
            raise CalcError(NO_GRID)
        if name in ("D", "E"):
            return f"{getattr(grid, name)(*_ints(name, args, 1, 2)):.3f}"
        if name == "LEN":
            a, b = _ints(name, args, 2, 2)
            if grid.D(b) < grid.D(a):
                raise CalcError(f"{{{{LEN {args}}}}}: bar {b} comes before bar {a}")
            return f"{grid.D(b) - grid.D(a):.3f}"
        if name == "TO_END":
            (a,) = _ints(name, args, 1, 1)
            if grid.D(a) > duration:
                raise CalcError(f"{{{{TO_END {args}}}}}: D({a}) = {grid.D(a):.2f}s is past the {duration:g}s end")
            return f"{duration - grid.D(a):.3f}"
        if name == "calc":
            return f"{calc(args, grid, duration):.3f}"
        if name == "BEFORE_END":
            margin, _, expr = args.partition(" ")
            t = calc(expr, grid, duration)
            if t > duration - float(margin):
                die(f"{expr} is at {t:.2f}s; the template needs it at least {float(margin):g}s before the "
                    f"{duration:g}s end so the text after it can be read. The storyboard needs fewer bars at "
                    f"this tempo/duration: re-map the scenes (references/storyboard.md)")
            return ""
        if args:
            raise CalcError(f"{{{{{name}}}}} takes no arguments")
        if name == "BEATS":
            return json.dumps([round(b, 3) for b in grid.beats])
        if name == "DOWNBEAT_INDEX":
            return str(grid.first)
        if name == "BEATS_PER_BAR":
            return str(grid.bpb)
        if name == "DURATION":
            return f"{duration:g}"
        if name == "STORES":
            return json.dumps(project["stores"])
        if name in ("WIDTH", "HEIGHT"):
            return str(project[name.lower()])
        if name == "FORMAT":
            return project["format"]
        if name == "FRAME_SCALE":
            return f"{project['height'] / FORMATS['9:16'][1]:g}"
        if name == "MOTION":
            if motion is None:
                raise CalcError("the template has {{MOTION}} but the project has no motion.js: copy it "
                                "from template/motion.js")
            if "{{" in motion or "}}" in motion:
                raise CalcError("motion.js must not contain a double brace (it would read as a token): "
                                "put a space between the braces")
            return motion
        raise CalcError(f"unknown token {{{{{name}}}}}")

    try:
        out = TOKEN.sub(sub, src)
    except ValueError as e:
        die(str(e))
    left = re.search(r"\{\{.*?\}\}", out, re.S)
    if left:
        die(f"leftover token after build: {left.group(0)[:60]!r}")
    if "{{" in out:
        i = out.index("{{")
        die(f"unclosed token (no closing }}}}) in the template: {out[i:i + 40]!r}")
    return out


def sfx_tags(project_dir, cues_doc, grid, duration):
    """Return (html_lines, realized) for the cues whose sound file exists."""
    audio_dir = Path(project_dir) / "assets" / "audio"
    files, cues = cues_doc.get("sfx", {}), cues_doc.get("cues", [])
    if not isinstance(files, dict) or not isinstance(cues, list):
        die('cues.json: "sfx" must be an object and "cues" an array')
    bad = [k for k, v in files.items() if not isinstance(v, str)]
    if bad:
        die(f'cues.json: every "sfx" value is a file name (a string); not {", ".join(map(repr, bad))}')
    lines, realized, track_end, leads, seen, durations = [], [], {}, {}, set(), {}
    for cue in cues:
        if not isinstance(cue, dict) or any(k not in cue for k in ("id", "sfx", "at")):
            die(f"cues.json: every cue needs id, sfx and at, got {str(cue)[:80]}")
        cid, key = cue["id"], cue["sfx"]
        if cid in seen:
            die(f"cues.json: cue id {cid!r} is used twice")
        seen.add(cid)
        at, offset, vol = str(cue["at"]), cue.get("offset", 0), cue.get("volume", 0.5)
        if not (is_number(offset) and is_number(vol)):
            die(f"cue {cid!r}: offset and volume must be JSON numbers, got {offset!r} and {vol!r}")
        if vol < 0:
            die(f"cue {cid!r}: volume must be 0 or more, got {vol}")
        sync = cue.get("sync")
        if "sync" in cue and not isinstance(sync, bool):
            die(f'cue {cid!r}: "sync" must be true or false (no quotes), got {sync!r}')
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(cid)):
            die(f"cue id {cid!r} must use only letters, digits, - and _")
        if key not in files:
            die(f"cue {cid!r} uses sfx {key!r}, which is not in the cues.json sfx map")
        path = audio_dir / files[key]
        if not path.is_file():
            print(f"warning: skipping cue {cid!r}: {path} not found", file=sys.stderr)
            continue
        try:
            t = calc(at, grid, duration) + offset
        except CalcError as e:
            die(f"cue {cid!r}: {e}")
        if path not in durations:
            durations[path] = media_duration(path)
            leads[path] = attack_seconds(path)
        align = cue.get("align", "attack")
        if align not in ("attack", "start", "end"):
            die(f"cue {cid!r}: align must be attack, start or end")
        if align == "attack":
            t -= leads[path]  # the audible attack, not the file's leading silence, lands on `at`
        elif align == "end":
            t -= durations[path]
        if not 0 <= t < duration:
            print(f"warning: skipping cue {cid!r}: time {t:.3f} is outside 0-{duration:g}", file=sys.stderr)
            continue
        d = min(durations[path], duration - t)
        track = SFX_FIRST_TRACK
        while track_end.get(track, -1.0) > t:
            track += 1
        track_end[track] = t + d
        rel = f"assets/audio/{files[key]}"
        lines.append(f'      <audio id="sfx-{cid}" src="{html.escape(rel, quote=True)}" data-start="{t:.3f}" data-duration="{d:.3f}" '
                     f'data-track-index="{track}" data-volume="{vol:g}"></audio>')
        sync = sync if "sync" in cue else align != "end"
        realized.append({"id": cid, "file": rel, "time": round(t, 4), "volume": vol, "track": track,
                         "align": align, "sync": sync})
    return lines, realized


MIN_SCENE_TAIL = 2.0  # seconds a scene (the end card above all) must have before the video ends


def check_scenes(html_out, duration):
    """Every scene must start inside the video, at least MIN_SCENE_TAIL before its end: a scene
    past the end is silently never shown, and one that starts 0.1 s before it cannot be read."""
    bad = []
    live = re.sub(r"<!--.*?-->", "", html_out, flags=re.S)  # a commented-out scene is never shown
    for tag in re.findall(r"<section\b[^>]*>", live):
        start = re.search(r"""\bdata-start\s*=\s*(["'])(.*?)\1""", tag)
        if not start:
            continue
        name = re.search(r"""\bid\s*=\s*(["'])(.*?)\1""", tag)
        try:
            t = float(start.group(2))
        except ValueError:
            t = float("nan")
        if not 0 <= t <= duration - MIN_SCENE_TAIL:
            bad.append(f"{name.group(2) if name else tag[:40]} at {start.group(2)}s")
    if bad:
        die(f"scenes outside the {duration:g}s video or starting less than {MIN_SCENE_TAIL:g}s before its "
            f"end: {', '.join(bad)}. The storyboard needs fewer bars at "
            f"this tempo/duration: re-map the scenes (references/storyboard.md)")


SHOTLIST_HEADER = ["scene", "purpose", "entry state", "exit state"]


def shotlist_rows(text):
    """The rows of the one table headed `scene | purpose | entry state | exit state`: a list of
    four-cell lists, or a string that says what is wrong with the file."""
    lines = text.splitlines()
    tables = [i for i, line in enumerate(lines) if split_row(line) is not None
              and [c.lower() for c in split_row(line)] == SHOTLIST_HEADER]
    if len(tables) != 1:
        return (f"it needs exactly one table headed `{' | '.join(SHOTLIST_HEADER)}`, "
                f"found {len(tables)}")
    sep = split_row(lines[tables[0] + 1]) if tables[0] + 1 < len(lines) else None
    if sep is None or len(sep) != len(SHOTLIST_HEADER) or not all(re.fullmatch(r":?-+:?", c) for c in sep):
        return "the line under the header must be a separator row: | --- | --- | --- | --- |"
    rows = []
    for line in lines[tables[0] + 2:]:
        cells = split_row(line)
        if cells is None:
            break
        rows.append(cells)
    if not rows:
        return "the table has no rows"
    return rows


def split_row(line):
    line = line.strip()
    if not line.startswith("|"):
        return None
    line = line[1:-1] if line.endswith("|") and len(line) > 1 else line[1:]
    return [c.strip() for c in line.split("|")]


def check_shotlist(project_dir, html_out):
    """When <project>/shotlist.md exists, every live scene needs exactly one row with a purpose, an
    entry state and an exit state: a scene whose job nobody can state does not belong in the render."""
    path = Path(project_dir) / "shotlist.md"
    if not path.is_file():
        return
    try:
        rows = shotlist_rows(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as e:
        die(f"{path} is not UTF-8 text ({e}); save it as UTF-8")
    if isinstance(rows, str):
        die(f"shotlist.md: {rows}")
    problems = []
    live = re.sub(r"<!--.*?-->", "", html_out, flags=re.S)
    scenes = []
    for tag in re.findall(r"<section\b[^>]*>", live):
        if not re.search(r"""\bdata-start\s*=\s*(["']).*?\1""", tag):
            continue
        name = re.search(r"""\bid\s*=\s*(["'])(.*?)\1""", tag)
        if name and name.group(2):
            scenes.append(name.group(2))
        else:
            problems.append(f"a scene has no id: {tag[:60]}")
    seen = {}
    for row in rows:
        if len(row) != len(SHOTLIST_HEADER):
            problems.append(f"the row for {row[0] if row else '?'!r} has {len(row)} cells, not "
                            f"{len(SHOTLIST_HEADER)}")
            continue
        scene = row[0]
        seen[scene] = seen.get(scene, 0) + 1
        if seen[scene] == 2:
            problems.append(f"scene {scene} has more than one row")
        for label, cell in zip(SHOTLIST_HEADER[1:], row[1:]):
            if not cell or cell.upper() == "TODO":
                problems.append(f"scene {scene}: the {label} is empty or TODO")
    for scene in scenes:
        if scene not in seen:
            problems.append(f"scene {scene} has no row: add one to shotlist.md")
    for scene in seen:
        if scene not in scenes:
            problems.append(f"shotlist.md has a row for {scene}, which is not a scene in the page")
    if problems:
        die("shotlist.md does not match the scenes:\n  " + "\n  ".join(problems))


# Injected by build.py as the LAST script of the page. The label is not part of the template: this
# script creates it from CONFIG.aiLabel, with an id drawn at build time (no Math.random in the page:
# HyperFrames needs deterministic scripts) that no template rule or tween can know, and
# every visual property inline !important (which no stylesheet rule overrides), as the last child
# of the composition root. It then checks the label's box and every ancestor, and throws
# (hyperframes check: page_error; render: nothing) when the label would not be seen.
AI_LABEL_GUARD = r"""<script data-ai-label-guard>
(() => {
  const fail = (why) => { throw new Error(`the AI-generated label ${why}: it must stay on screen`); };
  const text = typeof CONFIG === "object" && CONFIG !== null ? CONFIG.aiLabel : undefined;
  // spaces, format/control/combining marks and the letters that draw nothing (Hangul fillers, braille blank)
  const visible = typeof text === "string" ?
    [...text.replace(/[\p{Z}\p{C}\p{M}\u115F\u1160\u3164\uFFA0\u2800]/gu, "")].length : 0;
  if (!visible) fail("(CONFIG.aiLabel) is missing, empty or has no visible character");
  const root = document.querySelector("[data-composition-id]");
  if (!root) fail("has no composition root to sit in");
  const el = document.createElement("div");
  el.id = "__AI_LABEL_ID__";
  // "all: initial" first, so no template rule reaches the label box; then the look, which comes
  // after and wins
  const look = {
    all: "initial", display: "block", position: "absolute", __AI_LABEL_PLACE__, "z-index": "2147483647",
    margin: "0", padding: "10px 22px", "border-radius": "999px", background: "rgba(0, 0, 0, 0.62)",
    border: "1px solid rgba(255, 255, 255, 0.35)", "white-space": "nowrap", visibility: "visible",
    opacity: "1", transform: "none", filter: "none", "clip-path": "none", "pointer-events": "none",
  };
  for (const [k, v] of Object.entries(look)) el.style.setProperty(k, v, "important");
  // the words live in a closed shadow root: no template selector reaches them, pseudo-elements
  // included; its !important rules beat the page's !important rules on the host's ::before/::after
  const shadow = el.attachShadow({ mode: "closed" });
  const sheet = document.createElement("style"), words = document.createElement("span");
  sheet.textContent = ":host::before, :host::after { content: none !important; display: none !important; }" +
    " span { all: initial !important; display: inline-block !important; color: #ffffff !important;" +
    " -webkit-text-fill-color: #ffffff !important; font: 700 __AI_LABEL_PX__px/1.25 sans-serif !important;" +
    " letter-spacing: 0.04em !important; white-space: nowrap !important; }";
  words.textContent = text;
  shadow.append(sheet, words);
  root.appendChild(el);
  const own = getComputedStyle(words);
  const alpha = (c) => { const m = c.match(/rgba?\(([^)]*)\)/); const v = m ? m[1].split(/[\s,\/]+/) : [];
    return m ? (v.length > 3 ? parseFloat(v[3]) : 1) : 0; };
  if (alpha(own.color) < 0.5 || alpha(own.webkitTextFillColor) < 0.5 || own.fontSize !== "__AI_LABEL_PX__px") {
    fail("text is restyled out of sight");
  }
  for (const pseudo of ["::before", "::after"]) {
    if (!["none", "normal"].includes(getComputedStyle(el, pseudo).content)) fail(`is covered by its ${pseudo}`);
  }
  // the label's own inline visibility: visible wins over any hidden ancestor (the runtime hides
  // [data-start] elements until its first seek), and its own look is reset above; its ancestors
  // (the composition root, body, html) can still hide it by display, opacity, clip-path, mask,
  // filter or blend mode, so none of those is allowed on them
  let opacity = 1;
  for (let n = el; n; n = n.parentElement) {
    const cs = getComputedStyle(n);
    if (cs.display === "none") fail("sits in an element with display: none");
    if (cs.clipPath !== "none") fail("is clipped");
    if (n !== el && (cs.maskImage !== "none" || cs.webkitMaskImage !== "none")) fail("is masked");
    if (n !== el && (cs.filter !== "none" || cs.mixBlendMode !== "normal")) fail("sits in a filtered or blended element");
    opacity *= parseFloat(cs.opacity);
  }
  if (opacity < 0.5) fail("is faded out (opacity of the label and its ancestors)");
  // the painted words, not only the pill: at 24px each visible character is well over 6px wide
  const range = document.createRange();
  range.selectNodeContents(words);
  const ink = range.getBoundingClientRect(), root_box = root.getBoundingClientRect();
  if (ink.width < Math.max(12, 6 * visible) || ink.height < 16) fail("text has no width on screen");
  // a feed format keeps the label inside its safe box (the feed's own UI covers the rest)
  const safe = __AI_LABEL_BOX__;
  const frame = safe ? { left: root_box.left + safe[0], top: root_box.top + safe[1], right: root_box.left + safe[2],
    bottom: root_box.top + safe[3] } : root_box;
  for (const box of [el.getBoundingClientRect(), ink]) {
    if (box.left < frame.left || box.top < frame.top || box.right > frame.right || box.bottom > frame.bottom) {
      fail(safe ? "is not fully inside the feed safe box (references/storyboard.md)" : "is not fully inside the frame");
    }
  }
})();
</script>
"""


BLANK_GLYPHS = "\u115f\u1160\u3164\uffa0\u2800"  # letters that draw nothing (Hangul fillers, braille blank)


SEEKABLE_BANNED = (
    ("Math.random", r"(?<![\w$])Math\s*\.\s*random(?![\w$])"),
    ("Date.now", r"(?<![\w$])Date\s*\.\s*now(?![\w$])"),
    ("new Date", r"(?<![\w$])new\s+Date(?![\w$])"),
    ("Date(", r"(?<![\w$])Date\s*\("),
    ("performance.now", r"(?<![\w$])performance\s*\.\s*now(?![\w$])"),
    ("setTimeout", r"(?<![\w$])setTimeout(?![\w$])"),
    ("setInterval", r"(?<![\w$])setInterval(?![\w$])"),
    ("requestAnimationFrame", r"(?<![\w$])requestAnimationFrame(?![\w$])"),
    ("crypto.getRandomValues", r"(?<![\w$])crypto\s*\.\s*getRandomValues(?![\w$])"),
    ("crypto.randomUUID", r"(?<![\w$])crypto\s*\.\s*randomUUID(?![\w$])"),
)
SCRIPT_TAG = r"<script\b((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>(.*?)</script\s*>"
ATTRIBUTE = r"""([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?"""
JS_TYPES = ("", "module", "text/javascript", "application/javascript")


def blank_js(src):
    """Return src with every comment, string and template-literal text replaced by spaces (newlines
    kept, so offsets and line numbers stay). The code inside `${...}` stays. One pass, so a `//` in a
    string is not a comment and a quote in a comment does not open a string. A regex literal that holds
    a quote is not understood."""
    out = list(src)
    n = len(src)

    def blank(a, b):
        for k in range(a, min(b, n)):
            if out[k] != "\n":
                out[k] = " "

    stack = [["code", 0]]  # ["code", brace depth] or ["tpl", 0]
    i = 0
    while i < n:
        kind, c = stack[-1][0], src[i]
        if kind == "code":
            two = src[i:i + 2]
            if two == "//":
                j = src.find("\n", i)
                j = n if j < 0 else j
                blank(i, j)
                i = j
            elif two == "/*":
                j = src.find("*/", i + 2)
                j = n if j < 0 else j + 2
                blank(i, j)
                i = j
            elif c in "'\"":
                j = i + 1
                while j < n and src[j] != c and src[j] != "\n":
                    j += 2 if src[j] == "\\" else 1
                j = min(j + 1, n)
                blank(i, j)
                i = j
            elif c == "`":
                stack.append(["tpl", 0])
                blank(i, i + 1)
                i += 1
            elif c == "{":
                stack[-1][1] += 1
                i += 1
            elif c == "}":
                if stack[-1][1] > 0:
                    stack[-1][1] -= 1
                elif len(stack) > 1:
                    stack.pop()
                    blank(i, i + 1)
                i += 1
            else:
                i += 1
        elif c == "\\":
            blank(i, i + 2)
            i += 2
        elif c == "`":
            stack.pop()
            blank(i, i + 1)
            i += 1
        elif src[i:i + 2] == "${":
            stack.append(["code", 0])
            blank(i, i + 2)
            i += 2
        else:
            blank(i, i + 1)
            i += 1
    return "".join(out)


def inline_scripts(html_out):
    """(body, blanked code) of each inline JavaScript script of the page; scripts with a src and other
    script types are skipped. The code has comments, strings and template-literal text blanked."""
    for m in re.finditer(SCRIPT_TAG, html_out, re.S | re.I):
        attrs, body = {}, m.group(2)
        for a in re.finditer(ATTRIBUTE, m.group(1)):
            attrs.setdefault(a.group(1).lower(), next((g for g in a.groups()[1:] if g is not None), ""))
        script_type = attrs.get("type", "").split(";")[0].strip(" \t\n\f\r").lower()
        if "src" in attrs or script_type not in JS_TYPES:
            continue
        yield body, blank_js(body)


PUNCH_CAP = 2  # shakes and flashes per reel (references/motion.md)


def punch_warnings(html_out):
    """A warning for each of shake() and flash() called more than PUNCH_CAP times in the page's
    inline scripts. Calls in comments and strings do not count, and neither does a definition."""
    warnings = []
    for name in ("shake", "flash"):
        calls = sum(len(re.findall(rf"(?<![\w$.])(?<!function ){name}\s*\(", code)) for _, code in inline_scripts(html_out))
        if calls > PUNCH_CAP:
            warnings.append(f"{calls} {name}() calls in the page (at most {PUNCH_CAP}, on the drop and the end card: "
                            "references/motion.md)")
    return warnings


def check_seekable(html_out):
    """A frame must depend only on the time: no clock, no timer, no random value in the page's inline
    scripts (scripts with a src and inline event-handler attributes are not read). Comments, strings and
    template-literal text are blanked first, so a name in prose does not fail the build. Runs before the
    AI-label guard is added, so the guard's own code is never read."""
    found = []
    for body, code in inline_scripts(html_out):
        hits = sorted((h.start(), name) for name, rx in SEEKABLE_BANNED for h in re.finditer(rx, code))
        for pos, name in hits:
            line = body.split("\n")[body.count("\n", 0, pos)].strip()
            found.append(f"  remove {name} in `{line[:140]}`")
    if found:
        die("a frame must depend only on t (a hidden clock or a random value makes two renders differ):\n"
            + "\n".join(found))


def has_visible_character(label):
    return isinstance(label, str) and any(
        unicodedata.category(c)[0] not in "ZCM" and c not in BLANK_GLYPHS for c in label)


def check_ai_label(html_out):
    """Static half of the AI-generated label (EU AI Act): CONFIG.aiLabel must be a string with a
    visible character. The runtime half, AI_LABEL_GUARD, creates the label and checks it can be seen
    (it is the one that counts: this check only fails a build early).
    Comments are removed first, so an example in a comment neither passes nor fails the build: HTML
    <!-- -->, JS /* */ and lines that start with //. A `/*` inside a string can hide text from this
    check, and so can a `<!--` inside a string when a later `-->` exists; the runtime guard still
    throws for an empty label."""
    code = re.sub(r"<!--.*?-->|/\*.*?\*/", "", html_out, flags=re.S)
    code = re.sub(r"(?m)^[ \t]*//.*$", "", code)
    values = re.findall(r'"aiLabel"\s*:\s*("(?:[^"\\]|\\.)*"|[^,}\s]+)', code)
    labels = []
    for v in values:
        try:
            labels.append(json.loads(v))
        except ValueError:
            labels.append(None)
    if not labels or not all(has_visible_character(x) for x in labels):
        die("CONFIG.aiLabel is missing, empty, not a string or has no visible character: the "
            "AI-generated label must stay on screen (SKILL.md rule 7). A comment after code on the same "
            "line is not removed before this check")


# Where the label sits and its text size, per format: inside the feed safe box at the format's
# minimum readable size (9:16 and 4:5, references/storyboard.md), or the corner of a 16:9 web hero.
AI_LABEL_PLACES = {
    "9:16": ('left: "64px", bottom: "428px"', 32),
    "4:5": ('left: "64px", bottom: "104px"', 30),
    "16:9": ('right: "44px", bottom: "40px"', 24),
}


def add_ai_label_guard(html_out, fmt):
    end = html_out.rfind("</body>")
    if end < 0:
        die("the page has no </body>: build.py puts the AI-generated label check just before it")
    place, px = AI_LABEL_PLACES[fmt]
    box = FEED_BOXES.get(fmt)
    guard = (AI_LABEL_GUARD.replace("__AI_LABEL_ID__", "ai-label-" + secrets.token_hex(6))
             .replace("__AI_LABEL_PLACE__", place).replace("__AI_LABEL_PX__", str(px))
             .replace("__AI_LABEL_BOX__", json.dumps(list(box)) if box else "null"))
    return html_out[:end] + guard + html_out[end:]


HYPERFRAMES = "hyperframes@0.8.78"


def settled_times(spans, duration):
    """Two settled times per scene window: SCENE_SETTLE after the start (what entered with the scene
    has landed) and SCENE_SETTLE_END before the window's end (what entered late has landed too). A
    time outside its window or the video is dropped; equal times are merged."""
    times = set()
    for start, lo, hi in scene_windows(spans, duration):
        for t in (start + SCENE_SETTLE, hi - SCENE_SETTLE_END):
            if lo <= t < hi and 0 <= t < duration:
                times.add(round(t, 3))
    return sorted(times)


def check_command(project_dir, html_out, project):
    """The hyperframes check command for this page. A feed format adds the bottom zone of its safe box
    as an error band, sampled only at settled times, when nothing is in motion."""
    cmd = f"npx --yes {HYPERFRAMES} check {shlex.quote(str(project_dir))}"
    box = FEED_BOXES.get(project["format"])
    times = settled_times(scene_spans(html_out), project["duration"]) if box else []
    if not times:
        return cmd
    height = FORMATS[project["format"]][1]
    seek = ",".join(f"{t / project['duration']:.4f}" for t in times)
    return cmd + f' --caption-zone "x0=0;y0={box[3] / height:.5f};x1=1;y1=1;severity=error;seek={seek}"'


def check_silent(html_out, cues_doc, fmt):
    """A silent format carries no sound: no cues, and no <audio> or <video> in the page (the render
    would put it in the file; finish.py strips audio too, this stops it before the render)."""
    if cues_doc.get("cues"):
        die(f"{fmt} is silent: cues.json has cues. Empty the cue list (or delete cues.json)")
    live = re.sub(r"<!--.*?-->", "", html_out, flags=re.S)
    tag = re.search(r"<(audio|video)\b", live, re.I)
    if tag:
        die(f"{fmt} is silent: the page has a <{tag.group(1).lower()}> tag. Remove it")


def build(project_dir):
    project_dir = Path(project_dir)
    # a build that fails, for any reason, must not leave the previous build behind for a render
    for old in ("index.html", "cues.realized.json"):
        (project_dir / old).unlink(missing_ok=True)
    project = load_project(project_dir)
    tmpl = project_dir / "src.html.tmpl"
    beats = project_dir / "beats.json"
    silent = is_silent(project)
    for p in (tmpl,) if silent else (tmpl, beats):
        if not p.is_file():
            die(f"{p} not found")
    grid = None if silent else Grid.load(beats, project["beats_per_bar"])
    try:
        src = tmpl.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        die(f"{tmpl} is not UTF-8 text ({e}); save it as UTF-8")
    motion_path = project_dir / "motion.js"
    try:
        motion = motion_path.read_text(encoding="utf-8") if motion_path.is_file() else None
    except UnicodeDecodeError as e:
        die(f"{motion_path} is not UTF-8 text ({e}); save it as UTF-8")
    out = substitute(src, grid, project, motion)
    cues_path = project_dir / "cues.json"
    cues_doc = read_json(cues_path) if cues_path.is_file() else {}
    if silent:
        check_silent(out, cues_doc, project["format"])
        lines, realized = [], []
    else:
        lines, realized = sfx_tags(project_dir, cues_doc, grid, project["duration"])
    if out.count("<!--SFX-->") > 1:
        die("src.html.tmpl has more than one <!--SFX--> marker: every sound would play twice")
    if "<!--SFX-->" in out:
        out = out.replace("<!--SFX-->", "\n".join(lines).lstrip() if lines else "")
    elif lines:
        die("src.html.tmpl has no <!--SFX--> marker for the SFX tags")
    check_scenes(out, project["duration"])
    check_shotlist(project_dir, out)
    check_seekable(out)
    for w in punch_warnings(out):
        print(f"warning: {w}", file=sys.stderr)
    check_ai_label(out)
    out = add_ai_label_guard(out, project["format"])
    (project_dir / "index.html").write_text(out)
    (project_dir / "cues.realized.json").write_text(json.dumps(realized, indent=1) + "\n")
    if silent:
        print(f"built {project_dir / 'index.html'}: silent {project['format']} loop, {project['duration']:g} s")
    else:
        print(f"built {project_dir / 'index.html'}: {len(realized)} SFX cues mixed; downbeats "
              f"{[round(b, 2) for b in grid.beats[grid.first::grid.bpb]]}")
    print(f"check: {check_command(project_dir, out, project)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        die(__doc__.strip().splitlines()[-1])
    build(sys.argv[1])
