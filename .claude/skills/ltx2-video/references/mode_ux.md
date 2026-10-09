# ltx2-video — Mode UX & Interaction Design

Implementation-ready interaction design for the `ltx2-video` Claude Code skill. Wraps the self-hosted **LTX-2.3 (22B)** backend on Modal (`ltx2-fast-inference`) via `scripts/submit_video.py`. Five modes: **i2v, t2v, keyframe (A→B), v2v (retake window), control (IC-LoRA union: canny/depth/pose)**.

Grounded in the actual code:
- Script: `scripts/submit_video.py`
- Backend: `deploy/ltx2_model.py`
- Backend runs at **24 fps**; frame counts must be **8k+1** (17, 49, 97, 121, 217, 241). 97f ≈ 4s, 217f ≈ 9s, 241f ≈ 10s. Returns `latency_s` per job.

> The skill drives the user's **own self-hosted LTX-2.3** on their Modal GPU. It never recommends a SaaS or any paid per-clip API, and never routes through fal-mcp.

---

## PART 1 — Design principles

Three principles shape every mode below. They turn a bare CLI into a good conversational video tool.

### 1.1 Named motion presets (the prompt *is* the control surface)
LTX has no preset dropdown — the preset **is** prompt engineering. So expose a small library of **intent words** (`subtle idle`, `slow push-in`, `orbit`, `hair / wind`, …) that each expand into a full, model-ready motion/camera clause using standard cinematography vocabulary (dolly, crane, jib, pan, orbit, rack focus, handheld, crash zoom). The user picks an intent; the skill writes the clause. Full expansions in PART 3.2.

### 1.2 Start frame → end frame, and coherence
Keyframe = **A is your start, B is the frame the video should arrive at**; the model fills the in-between. The hard rule: **A and B must be the same subject/scene** for a clean motion. Unrelated A/B has no coherent interpolation — you get a morph/cross-dissolve (identity melt). Treat "coherent interpolation" and "morph between unrelated images" as two different things, and surface the distinction to the user (PART 2 keyframe, PART 3.3-B). A nice default: **same image for both ends → a smooth loop / 360° pulse.**

### 1.3 Image-grounded prompting (don't make the user describe their own photo)
For i2v, the skill **reads the image first** and writes the subject/setting/lighting description itself, then appends only the *motion + camera*. The image carries identity; the prompt carries motion. A prompt that contradicts the photo (e.g. "golden hour" on a flat-lit indoor face) fights the model. This is the single biggest lever for i2v quality.

---

## PART 2 — Per-mode interaction contract

Each mode below gives: **when it fires**, **what the skill says/does**, **how it elicits the prompt**, and **the exact `submit_video.py` args** it maps to. Default render is **vertical 9:16, 768×1280**.

### 2.1 i2v — animate a single photo (DEFAULT when one image is present)

**Conversational contract.** User drops one image and says "animate this" / "make it move" / "bring this to life." Default to i2v.

**The image-grounded prompting rule (core i2v-quality technique):** the user should NOT have to describe their own photo. The skill does the description, then adds motion. Concretely:
1. **Read the image first** (it already validates with `file`; also actually `Read` the pixels) and silently form a 1-sentence description of subject + setting + lighting.
2. **Author the motion**, not the subject. Final prompt = `<image description (subject/setting/light)> , <motion clause> , <camera clause>`. Keep the description faithful so identity/scene is preserved; only the motion + camera are new.
3. Offer **named motion presets** (the user picks an intent word; the skill expands it). Default to **"subtle idle"** if the user gives nothing — it's the safest, most coherent i2v motion.

**Named motion preset library (i2v)** — full expansions in PART 3.2. Minimum set the SKILL.md should know:
`subtle idle`, `slow push-in`, `slow pull-out`, `hair / wind`, `turn to camera`, `orbit (arc)`, `parallax / drift`, `rack focus`, `ambient life` (crowd/water/fire moving), `handheld energy`.

**What to say (one image, ambiguous):** fire the **AskUserQuestion** in PART 3.3 (animate vs keyframe-A vs control). On "animate," optionally offer the preset chips.

**Args mapping:**
```bash
uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
  --mode i2v --image "<abs>" --prompt "<image-desc + motion preset expansion>" \
  --format reel
```
- Cheap warm-check: `--frames 17 --height 320 --width 512 --steps 8`.
- Longer clip: bump `--frames` (97≈4s, 217≈9s, 241≈10s). Keep 8k+1.

---

### 2.2 t2v — text only, no image

**Conversational contract.** User describes a scene with **no image** ("generate a video of a neon alley in the rain"). No conditioning frame exists, so identity is invented — use t2v.

**When t2v vs i2v:** If the user has *any* representative still, prefer **i2v** (far better subject/identity control and coherence). Use t2v only when there's genuinely no image, or the user explicitly wants the model to invent everything. State this tradeoff if they ask for t2v while holding an image.

**Prompt scaffolding (the skill builds this, in order):**
> **Subject → Action → Camera → Lighting → Style**

Template the skill fills:
```
<subject, concrete & specific>, <action/motion>, <camera move + framing>, <lighting>, <style/film-look>, 9:16 vertical.
```
Example: `a lone swordsman on a cliff edge, cloak whipping in the wind, slow push-in on his face, stormy overcast light, cinematic anamorphic film grain, 9:16 vertical.`

Keep it tight (one to two sentences). The backend appends a strong negative prompt internally — the skill does **not** need to author negatives.

**Args mapping:**
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py --mode t2v \
  --prompt "<scaffolded prompt>" --format reel
```

---

### 2.3 keyframe — interpolate A → B (the coherence-critical mode)

**Conversational contract.** User has two images, or says "transition from this to that," "morph A to B," "first frame / last frame." Maps to `--mode keyframe --image A --image B`.

**THE key UX problem: coherence.** LTX interpolates between A and B. If A and B are the **same subject/scene** (same character, same room, slightly different pose/expression/camera), the result is a **clean, coherent motion**. If A and B are **unrelated** (different person, different place), there is no coherent in-between — the model produces a **morph/cross-dissolve** (smearing, identity melt). This is a fundamental property of interpolation, not a bug.

**How the skill should guide A/B selection (in priority order):**
1. **Best — B derived from A.** If the user has only A, offer to **produce B by editing A** (same subject, changed pose/expression/lighting/angle) using an image-edit skill (`qwen-image-edit`). This guarantees a coherent pair. Say: *"For a clean transition, B should be the same subject as A with one thing changed. Want me to generate B by editing A (e.g. 'turn head left', 'open eyes', 'sunset light')?"*
2. **Good — A and B are first/last frames of an intended shot** (same scene, two moments). Coherent by construction.
3. **Same image for A and B** → smooth **loop / 360° pulse**. Offer this when the user wants a seamless looping clip.
4. **Risky — unrelated A and B.** Allow it, but **warn first** (PART 3.3-B). Frame it honestly: *"These look like different subjects/scenes — expect a morph/dissolve, not a clean motion. Proceed as a morph, or should I make B a variant of A instead?"*

**Prompt for keyframe:** describe the *shared* subject + the *change* across the transition, not two separate scenes. e.g. `the same woman, head turning from profile to facing camera, soft window light, subtle smile forming`.

**Args mapping:**
```bash
uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
  --mode keyframe --image "<absA>" --image "<absB>" \
  --prompt "<shared subject + the change>" --format reel
```
(Script enforces two `--image` args; errors if fewer.)

---

### 2.4 v2v — retake / restyle a time window (slowest mode)

**Conversational contract.** User has a **video** and wants to "change the look but keep the motion," "restyle this clip," "redo seconds 2–5," "retake." Maps to `--mode v2v --video … --start … --end …`.

**Two intents to disambiguate (restyle vs retake-window):**
- **Restyle (whole clip, keep motion):** keep the original motion/composition, change the aesthetic ("make it anime," "make it night"). A **style-only prompt** over the **full duration** (`--start 0 --end <clip length>`). Name the *new look* and assert *keep the motion/subject*.
- **Retake-window (fix a segment):** regenerate only a slice (e.g. a botched 2–5s stretch) while leaving the rest. Use a **tight `--start`/`--end`** around the bad window. The prompt describes what should happen *in that window*.

**How to choose the window.** Ask the user the segment in seconds, or default to `--start 2 --end 5`. For full-clip restyle, set the window to the entire clip. Keep windows as short as the fix allows — it directly drives cost.

**Strength / adherence.** The v2v path (`smoke_retake`) is a denoise-window retake; there is **no exposed strength slider** (unlike `control`, which has `--control-strength`). Adherence is governed by **window size + prompt specificity**, not a numeric knob: a wider window changes more; a narrower window changes less. (Don't promise a strength lever; it isn't wired today.)

**Realistic expectations — SET THESE OUT LOUD.** v2v is the **slowest mode by far: ~470s for a 10s window** (plus cold start on first call). Always warn: *"Heads up — v2v is the slow one, roughly 8 minutes for a 10s window. Want a shorter window or a quick low-res test first?"*

**Args mapping:**
```bash
# restyle whole clip (keep motion)
uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
  --mode v2v --video "<abs.mp4>" --start 0 --end <clip_len> \
  --prompt "<NEW look>, keep the original motion and composition"

# retake a bad window
... --mode v2v --video "<abs.mp4>" --start 2 --end 5 --prompt "<what should happen in 2–5s>"
```
(`--steps` is the only other v2v lever exposed.)

---

### 2.5 control — IC-LoRA structural control (union: canny / depth / pose)

**Conversational contract.** User wants the **structure/motion of a source** to drive a **new render** — "use the motion of this video," "match this pose/depth/edges," "same camera move, different content." Maps to `--mode control` (union IC-LoRA: Canny+Depth+Pose; the backend also has `motion_track` for trajectory control).

**control vs i2v — when to use which:**
- **i2v** = "animate *this image*." One still, model invents the motion. Use for "bring a photo to life."
- **control** = "follow *this structure/motion*." A control video dictates edges/depth/pose per frame; the prompt + optional init image dictate appearance. Use when the user **already has the motion they want** (a reference clip) and wants to re-skin / re-content it while preserving structure.

**Control-render acquisition — explain the three cases clearly:**
1. **Canny (auto, built-in).** Edges derive from any source video **with no extra model** — the script renders them via `ffmpeg edgedetect`. User just supplies `--video <src>`; the skill derives the canny control automatically. *Easiest path; offer first.* (Dense thresholds matter — a soft-lit face gives sparse edges and the model drifts; the script defaults to a dense `--canny-low 0.05 --canny-high 0.2`.)
2. **Depth (needs a pre-rendered control video).** Depth maps require a depth estimator (Depth-Anything / MiDaS) run beforehand. The skill **cannot** auto-derive depth — ask for a pre-rendered **depth-map video** via `--control-video`.
3. **Pose (needs a pre-rendered control video).** OpenPose/DWPose skeleton video must be rendered beforehand; pass via `--control-video`.

**What to ask the user (control):** see PART 3.3-D. Optional **init image** (`--image`) seeds the first-frame appearance. **Adherence:** `--control-strength` (default 1.0); lower (~0.6–0.8) loosens it for more prompt freedom.

**Args mapping:**
```bash
# canny auto-derived from a source clip
uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
  --mode control --video "<src.mp4>" --control-type canny \
  --prompt "<new appearance>" --format reel

# user-supplied depth or pose control video (+ optional init image)
... --mode control --control-video "<depth_or_pose.mp4>" --image "<init.jpg>" \
    --control-strength 0.9 --prompt "<new appearance>"
```
(Script: `--control` selects `union` vs `motion_track`; `--control-type` only auto-derives `canny`; depth/pose must arrive via `--control-video`.)

---

## PART 3 — Skill UX deliverables

### 3.1 Decision tree — "user has X, wants Y → mode Z"

```
What did the user provide?
│
├─ Nothing but a text description ─────────────────────────────► t2v
│       (subject→action→camera→lighting→style; 9:16)
│
├─ ONE image
│     └─ What do they want?
│          ├─ "animate / bring to life / make it move" ────────► i2v   (DEFAULT)
│          ├─ "transition to another look/pose" ──────────────► keyframe
│          │        → offer to generate B by editing A (qwen-image-edit)
│          ├─ "loop it / seamless" ───────────────────────────► keyframe (A==B loop)
│          └─ "follow this image's structure for a render" ────► control (init image)
│          └─ AMBIGUOUS → AskUserQuestion 3.3-A (animate vs keyframe-A vs control)
│
├─ TWO images ────────────────────────────────────────────────► keyframe (A→B)
│       → coherence check: same subject? yes=clean / no=warn morph (3.3-B)
│
├─ ONE video
│     └─ What do they want?
│          ├─ "change the look, keep the motion" ─────────────► v2v restyle (window = full clip)
│          ├─ "redo seconds X–Y" ─────────────────────────────► v2v retake-window
│          ├─ "use this motion/edges/pose for a NEW render" ──► control
│          │        ├─ edges → canny (auto via ffmpeg)
│          │        └─ depth/pose → ask for pre-rendered control video
│          └─ AMBIGUOUS → AskUserQuestion 3.3-C (restyle vs retake vs control)
│
└─ A control-render video already (depth/pose/canny map) ──────► control (--control-video)
```

Speed tiebreaker when undecided: **control (4s) ≈ fastest structural path; i2v fast; keyframe ~ i2v; v2v slowest by 5–10×.**

### 3.2 Named-preset table (preset → expanded prompt + recommended frames/res/mode)

Default res for all: **768×1280 (9:16)**. `{img}` = the skill's auto-description of the source image (i2v); for t2v, replace `{img}` with the user's subject.

| Preset | Mode | Frames (≈dur) | Expanded prompt fragment (appended after `{img}`) |
|---|---|---|---|
| **subtle idle** *(i2v default)* | i2v | 97 (4s) | `subtle natural motion — slight breathing, micro head movement, blinking, gentle ambient sway; locked-off camera; photorealistic` |
| **slow push-in** | i2v / t2v | 97 (4s) | `slow steady dolly push-in toward the subject, gradually tightening framing; cinematic, shallow depth of field` |
| **slow pull-out** | i2v / t2v | 97 (4s) | `slow dolly pull-out revealing more of the environment; cinematic, stable` |
| **hair / wind** | i2v | 97 (4s) | `a steady breeze moves the hair and fabric, natural flowing motion; subject otherwise still; soft directional light` |
| **turn to camera** | i2v | 97 (4s) | `the subject slowly turns their head to face the camera, eyes meeting lens, subtle expression shift` |
| **orbit (arc)** | i2v / t2v | 121 (5s) | `smooth arcing orbit around the subject, parallax revealing form and depth; steady cinematic motion` |
| **parallax / drift** | i2v | 97 (4s) | `slow lateral camera drift creating parallax between foreground and background; subtle, dreamlike` |
| **rack focus** | i2v | 97 (4s) | `focus racks from foreground to subject, cinematic shallow depth of field, otherwise still` |
| **ambient life** | i2v | 121 (5s) | `the scene comes alive — {water/fire/crowd/foliage} moves naturally, atmospheric particles drift; subject anchored` |
| **handheld energy** | i2v / t2v | 97 (4s) | `subtle handheld camera movement, organic micro-shake, documentary energy; natural motion` |
| **crash zoom in** | t2v / i2v | 49 (2s) | `rapid crash zoom in toward the subject, sudden punch-in, energetic` |
| **360 loop** | keyframe (A==B) | 97 (4s) | `seamless looping motion, smooth continuous camera arc returning to start; perfect loop` |
| **establishing** | t2v | 217 (9s) | `wide establishing shot, slow majestic camera move across the landscape, epic scale, cinematic lighting` |

Notes:
- Frame counts are all **8k+1**. Bump to 217 (≈9s) / 241 (≈10s) only when the user wants a long clip — cost scales with frames.
- For t2v, prepend the **subject→action** scaffold; for i2v, the preset is appended after the auto image-description so identity is preserved.

### 3.3 Exact AskUserQuestion prompts the SKILL.md should use

**3.3-A — One image dropped, intent unclear** (the most common fork):
- `header`: `What to do with this image?`
- `question`: `You gave me one image. How should I use it?`
- options:
  - **Animate it (i2v)** — *"Bring the photo to life with motion. Fastest, keeps the subject. (~31–45s for 4s, warm.)"*
  - **Use as start frame (keyframe A)** — *"Transition from this image to a second one. I can generate frame B by editing this image so the result stays coherent."*
  - **Use as structural control** — *"Drive a new render from this image's structure (pose/edges). More setup; tightest control."*
  - **Cancel**

**3.3-B — Two images that look unrelated** (coherence warning):
- `header`: `A and B look different`
- `question`: `These two images look like different subjects/scenes. Interpolating unrelated images gives a morph/dissolve, not a clean motion. How do you want to proceed?`
- options:
  - **Make B a variant of A (recommended)** — *"I'll regenerate B as the same subject as A with one change, for a clean transition."*
  - **Proceed as a morph** — *"Render the dissolve between them as-is."*
  - **Switch to i2v on A** — *"Just animate the first image instead."*
  - **Cancel**

**3.3-C — One video dropped, intent unclear:**
- `header`: `What to do with this video?`
- `question`: `You gave me a video. What's the goal?`
- options:
  - **Restyle, keep the motion (v2v)** — *"Change the look across the whole clip, preserve motion. Slowest mode (~8 min for 10s)."*
  - **Retake a time window (v2v)** — *"Regenerate just seconds X–Y. Shorter window = faster/cheaper."*
  - **Use its motion/structure for a NEW render (control)** — *"Follow edges/depth/pose. Edges (canny) are automatic; depth/pose need a pre-rendered control video."*
  - **Cancel**

**3.3-D — Control sub-type** (after user picks "control"):
- `header`: `Which control signal?`
- `question`: `Structural control follows one signal per frame. Which?`
- options:
  - **Edges (canny) — automatic** — *"I'll derive the edge map from your source video. No extra files."*
  - **Depth — needs a control video** — *"Give me a pre-rendered depth-map video (Depth-Anything/MiDaS)."*
  - **Pose — needs a control video** — *"Give me a pre-rendered OpenPose/DWPose skeleton video."*
  - **Cancel**

**3.3-E — Cost/quality gate before any full run:**
- `header`: `LTX-2.3`
- `question`: `Generate <mode> from <name>? <per-mode latency line from 3.4>. First run cold-starts ~90–200s. A few cents of GPU.`
- options: **Quick smoke (cheap)** · **Full quality (9:16)** · **Cancel**

### 3.4 Cost / latency expectations to surface, per mode

Backend is **24 fps**; warm = container already running; cold start (first call after idle) adds **~90–200s** on top. State the warm number, then mention cold start once.

| Mode | Warm latency | Notes to say out loud |
|---|---|---|
| **i2v** | **4s clip (97f) ≈ 31–45s** · **10s clip (241f) ≈ 100s** | Fastest image path. Default to 4s; offer 10s if they want length. |
| **t2v** | ≈ i2v at same frame count | No image to load; comparable to i2v. |
| **keyframe** | ≈ i2v at same frame count | Two-image interpolation; similar cost to i2v. |
| **v2v** | **10s window ≈ 470s (~8 min)** | **Slowest by far (5–10×).** Always warn; push short window / low-res smoke first. |
| **control** | **4s clip (97f) ≈ 28s** | Fastest structural path (distilled base, few steps). Canny adds a quick local ffmpeg pass. |
| **cold start** | **+90–200s on first call** | One-time per idle container. Say "waiting for container cold start (~90s)…" so it doesn't look hung. Use `--timeout 600` for full-res / v2v. |

**Cheap smoke (any image mode):** `--frames 17 --height 320 --width 512 --steps 8` → confirms the container is warm and the prompt direction is right before spending on a full render.

---

## Summary for SKILL.md authoring

- **Default mode = i2v, default render = 9:16 768×1280 (`--format reel`), default motion = "subtle idle."**
- **i2v technique: describe the image first (skill-authored), then append a named motion preset.** Never make the user describe their own photo.
- **keyframe is coherence-gated:** same-subject A/B = clean; unrelated = morph → warn (3.3-B) and offer to derive B by editing A.
- **v2v is the slow one (~470s/10s):** always set expectations; prefer a tight window.
- **control: canny is auto (ffmpeg, dense thresholds), depth/pose need a pre-rendered control video** — ask explicitly (3.3-D).
- **Always gate a full run behind AskUserQuestion (3.3-E)** with the per-mode latency line; offer the cheap smoke.
- **Never recommend a SaaS or paid per-clip API; never route through fal-mcp.** This is the user's own self-hosted LTX-2.3.
