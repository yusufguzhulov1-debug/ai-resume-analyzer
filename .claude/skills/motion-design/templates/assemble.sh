#!/bin/bash
# Assemble one motion design project (template of the motion-design skill).
# Copy it into <project>/, fill the settings below, run: bash <project>/assemble.sh
#
# 1. Marks every storyboard frame as animated, runs HeyGen's assembler and transition injector
#    (.claude/skills/product-launch-video/scripts), which rebuild index.html from scratch.
# 2. Adds the orchestrator's own layer on top of the fresh index.html (idempotent, re-run after every change):
#    the audio mix mounted at the root, the paper bed under the light world, the light flash from the dark
#    problem world into the light solution world, the iris from an object into the dark end card.
# 3. Runs the HyperFrames lint (pinned local CLI).
set -euo pipefail
cd "$(dirname "$0")"
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_UPDATE_CHECK=1

# ---- settings (times in seconds on the final timeline, see STORYBOARD.md) ------------------------------------------
FIRST_FRAME="01-hook"      # id of the first frame (basename of its src, without .html)
END_CARD="09-fin"          # id of the end card frame (the iris opens it)
TOTAL="45.0"               # final duration = STORYBOARD duration = TOTAL in build-audio.sh
AUDIO="assets/audio/${MIX:-mix.wav}"   # mix from build-audio.sh or build-music-options.py (MIX=mix-M2.wav bash assemble.sh); empty = silent

# Light flash, dark world -> light world (empty LEAK_AT = no flash). The flash covers the screen from
# LEAK_AT+0.15 to LEAK_AT+0.30: put the cut between the last dark frame and the first light frame at LEAK_AT+0.25.
LEAK_AT="14.25"
LEAK_X="960"               # flash center in px (the object the light comes from, e.g. a caret or a word)
LEAK_Y="540"

# Iris, light world -> dark end card (empty IRIS_AT = no iris). The end card must start at IRIS_AT+0.05 with
# transition_in: cut. The frame under the iris is kept mounted until IRIS_AT+0.80: its own internal clips must
# last that long too, or the iris opens on black (see references/pitfalls.md).
IRIS_AT="36.1"
IRIS_X="1400"              # iris center in px (the object the iris grows from)
IRIS_Y="450"
IRIS_FROM=""               # id of the frame under the iris (empty = the frame just before END_CARD)

# Paper bed under the light world, so a crossfade between two light frames never shows the dark root.
# Default span: LEAK_AT+0.20 to IRIS_AT+0.80. Empty PAPER = no bed.
PAPER="#f6f1e9"
BED_START=""               # optional override
BED_END=""                 # optional override

# Colors of the flash and the iris ring: copy accent, accent-light and accent-glow from frame.md.
ACCENT="#c25b28"
ACCENT_LIGHT="#d4703f"
ACCENT_GLOW="#e08a5c"

RUN_LINT="${RUN_LINT:-1}"  # RUN_LINT=0 skips the lint
# ---------------------------------------------------------------------------------------------------------------------

S=../.claude/skills/product-launch-video/scripts
[ -d "$S" ] || { echo "assemble: $S not found (the project must sit at the repository root)" >&2; exit 1; }
export FIRST_FRAME END_CARD TOTAL AUDIO LEAK_AT LEAK_X LEAK_Y IRIS_AT IRIS_X IRIS_Y IRIS_FROM PAPER BED_START BED_END \
  ACCENT ACCENT_LIGHT ACCENT_GLOW

python3 - <<'EOF'
# a frame whose HTML exists on disk is marked animated; the others stay outline and are skipped by the assembler
import os, re
p = "STORYBOARD.md"
s = open(p, encoding="utf-8").read()
parts = re.split(r"(?m)^(?=## Frame\b)", s)
missing = []
for i, block in enumerate(parts):
    src = re.search(r"(?m)^- src: (\S+)", block)
    if not block.startswith("## Frame") or not src:
        continue
    if os.path.exists(src.group(1)):
        parts[i] = re.sub(r"(?m)^- status: (outline|built)$", "- status: animated", block)
    else:
        parts[i] = re.sub(r"(?m)^- status: (built|animated)$", "- status: outline", block)
        missing.append(os.path.basename(src.group(1)))
s2 = "".join(parts)
if s2 != s:
    open(p, "w", encoding="utf-8").write(s2)
if missing:
    print("frames not built yet (skipped):", ", ".join(missing))
EOF
node $S/assemble-index.mjs --storyboard ./STORYBOARD.md --hyperframes . | tail -3
node $S/transitions.mjs inject --storyboard ./STORYBOARD.md --hyperframes . | tail -2
node $S/transitions.mjs verify --storyboard ./STORYBOARD.md --index ./index.html | tail -1

python3 - <<'EOF'
import os, re

env = os.environ
p = "index.html"
s = open(p, encoding="utf-8").read()
total = float(env["TOTAL"])
f = lambda key: float(env[key]) if env.get(key, "").strip() else None
leak_at, iris_at = f("LEAK_AT"), f("IRIS_AT")

def rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgba(hex_color, alpha, white=0.0):
    r, g, b = (round(c + (255 - c) * white) for c in rgb(hex_color))
    return f"rgba({r},{g},{b},{alpha})"

def scene_bounds():
    out = []
    for m in re.finditer(r"<div\b[^>]*?data-composition-id=\"([^\"]+)\"[^>]*>", s):
        tag = m.group(0)
        start = re.search(r'data-start="([0-9.]+)"', tag)
        dur = re.search(r'data-duration="([0-9.]+)"', tag)
        if start and dur:
            out.append((m.group(1), float(start.group(1)), float(dur.group(1)), m.start(), m.end()))
    return sorted(out, key=lambda x: x[1])

scenes = scene_bounds()
ids = [x[0] for x in scenes]
absent = [f"{key}={env[key]}" for key in ("FIRST_FRAME", "END_CARD") if env[key] not in ids]
if absent:
    # pilot or partial build: no orchestrator layer until the first frame and the end card are assembled
    print(f"orchestrator layer skipped: {', '.join(absent)} not in index.html (frames: {', '.join(ids)})")
    raise SystemExit(0)

accent, light, glow, paper = env["ACCENT"], env["ACCENT_LIGHT"], env["ACCENT_GLOW"], env.get("PAPER") or "#f6f1e9"

# the frame under the iris stays mounted until the iris has fully opened
if iris_at is not None:
    under = env.get("IRIS_FROM") or ids[ids.index(env["END_CARD"]) - 1]
    sc = next(x for x in scene_bounds() if x[0] == under)
    tag = s[sc[3]:sc[4]]
    new_dur = round(iris_at + 0.80 - sc[1], 3)
    s = s[:sc[3]] + re.sub(r'data-duration="[0-9.]+"', f'data-duration="{new_dur}"', tag, count=1) + s[sc[4]:]

# layers inserted right after the end card element
end = next(x for x in scene_bounds() if x[0] == env["END_CARD"])
close = s.index("</div>", end[4]) + len("</div>")
fx = ""
if env.get("AUDIO"):
    fx += f'\n      <audio id="mix" data-start="0" data-duration="{total}" data-track-index="11" src="{env["AUDIO"]}" data-volume="1"></audio>'
if leak_at is not None:
    x, y = int(float(env["LEAK_X"])), int(float(env["LEAK_Y"]))
    fx += f'''
      <div id="fxleak" class="clip" data-start="{leak_at}" data-duration="0.9" data-track-index="30" style="position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:60">
        <div id="fxleak-sweep" style="position:absolute;left:0;top:-200px;width:1400px;height:1480px;opacity:0;mix-blend-mode:screen;background:radial-gradient(ellipse at 50% 50%,{rgba(glow, .85, .35)} 0%,{rgba(light, .5)} 35%,{rgba(accent, 0)} 70%)"></div>
        <div id="fxleak-core" style="position:absolute;left:{x}px;top:{y}px;width:600px;height:600px;margin:-300px 0 0 -300px;border-radius:50%;opacity:0;background:radial-gradient(circle,{rgba(paper, 1, .6)} 0%,{paper} 30%,{rgba(glow, .9, .25)} 50%,{rgba(accent, .5)} 64%,{rgba(accent, 0)} 76%)"></div>
        <div id="fxleak-streak" style="position:absolute;left:-240px;top:{y - 3}px;width:2400px;height:6px;border-radius:3px;opacity:0;background:linear-gradient(90deg,{rgba(glow, 0, .6)},{rgba(glow, 1, .8)} 50%,{rgba(glow, 0, .6)});box-shadow:0 0 34px 12px {rgba(glow, .7)}"></div>
        <div id="fxleak-flash" style="position:absolute;inset:0;opacity:0;background:{paper}"></div>
      </div>'''
if iris_at is not None:
    ix, iy = int(float(env["IRIS_X"])), int(float(env["IRIS_Y"]))
    fx += f'''
      <div id="fxiris" class="clip" data-start="{iris_at}" data-duration="0.95" data-track-index="31" style="position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:61">
        <svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;inset:0"><circle id="fxiris-ring" cx="{ix}" cy="{iy}" r="0" fill="none" stroke="{light}" stroke-width="6" style="filter:drop-shadow(0 0 16px {glow}) drop-shadow(0 0 40px {rgba(accent, .8)})"/></svg>
      </div>'''
s = s[:close] + fx + s[close:]

# paper bed under the light world, on a track below the frames
if env.get("PAPER"):
    bed_start = f("BED_START") if env.get("BED_START") else (round(leak_at + 0.20, 3) if leak_at is not None else None)
    bed_end = f("BED_END") if env.get("BED_END") else (round(iris_at + 0.80, 3) if iris_at is not None else None)
    if bed_start is not None and bed_end is not None and bed_end > bed_start:
        first = re.search(r'<div\s+id="el-' + re.escape(env["FIRST_FRAME"]) + '"', s)
        if not first:
            raise SystemExit(f'assemble: element el-{env["FIRST_FRAME"]} not found in index.html')
        bed = (f'<div id="paperbed" class="clip" data-start="{bed_start}" data-duration="{round(bed_end - bed_start, 3)}" '
               f'data-track-index="12" style="position:absolute;inset:0;background:{env["PAPER"]}"></div>\n\n      ')
        s = s[:first.start()] + bed + s[first.start():]

# orchestrator tweens, inserted before the full-span anchor of the main timeline
tl = "        // orchestrator layer (motion-design skill): light flash and iris\n"
if leak_at is not None:
    t = lambda d: round(leak_at + d, 3)
    tl += f'''        tl.fromTo("#fxleak-core", {{ scale: 0.02, opacity: 0 }}, {{ scale: 4.6, opacity: 1, duration: 0.22, ease: "expo.in", immediateRender: false }}, {t(0.03)});
        tl.fromTo("#fxleak-streak", {{ scaleX: 0, opacity: 0 }}, {{ scaleX: 1, opacity: 1, duration: 0.16, ease: "power3.in", immediateRender: false }}, {t(0.05)});
        tl.fromTo("#fxleak-sweep", {{ x: 1100, opacity: 0 }}, {{ x: -700, opacity: 1, duration: 0.5, ease: "power2.inOut", immediateRender: false }}, {t(0.03)});
        tl.fromTo("#fxleak-flash", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1, ease: "power2.in", immediateRender: false }}, {t(0.15)});
        tl.to("#fxleak-flash", {{ opacity: 0, duration: 0.5, ease: "power2.out" }}, {t(0.30)});
        tl.to(["#fxleak-core", "#fxleak-streak", "#fxleak-sweep"], {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, {t(0.27)});
'''
if iris_at is not None:
    t = lambda d: round(iris_at + d, 3)
    card = env["END_CARD"]
    tl += f'''        tl.fromTo("#el-{card}", {{ clipPath: "circle(0% at {ix}px {iy}px)" }}, {{ clipPath: "circle(160% at {ix}px {iy}px)", duration: 0.75, ease: "power2.inOut", immediateRender: false }}, {t(0.05)});
        tl.fromTo("#fxiris-ring", {{ attr: {{ r: 0 }} }}, {{ attr: {{ r: 2492 }}, duration: 0.75, ease: "power2.inOut", immediateRender: false }}, {t(0.05)});
        tl.fromTo("#fxiris-ring", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08, immediateRender: false }}, {t(0.05)});
        tl.to("#fxiris-ring", {{ opacity: 0, duration: 0.15 }}, {t(0.70)});
'''
anchor = re.search(r"(?m)^[ \t]*tl\.to\(\{\}, \{ duration: [0-9.]+ \}, 0\);", s)
if not anchor:
    raise SystemExit("assemble: full-span anchor tl.to({}, { duration: N }, 0); not found in index.html")
s = s[:anchor.start()] + tl + s[anchor.start():]
open(p, "w", encoding="utf-8").write(s)
print("orchestrator layer patched:", ", ".join(k for k, v in (("audio", env.get("AUDIO")), ("flash", leak_at is not None),
      ("iris", iris_at is not None), ("paper bed", "paperbed" in s)) if v) or "nothing")
EOF

if [ "$RUN_LINT" = "1" ]; then
  npx hyperframes lint 2>&1 | grep -E "✗|error\(s\)|warning\(s\)" || echo "lint: no error reported"
fi
