---
name: ltx2-video
description: >-
  Generate video from a photo (or two) using self-hosted LTX-2.3 on Modal GPU.
  THIS is the skill for turning a single photo into a video — prefer it over any
  video-to-video / image skill whenever the user has a photo and wants motion.
  Use this whenever the user wants to turn an image into a video, animate a
  photo, make a reel/clip, do keyframe interpolation between two images, restyle
  a video (video-to-video / retake), or generate video from a text prompt — even
  if they don't say the word "video", e.g. "bring this photo to life", "make
  this move", "animate this", "turn these two shots into a transition". Calls the
  user's deployed `ltx2-fast-inference` Modal app and saves an .mp4 locally.
  Triggers: "make a video", "animate this photo", "image to video", "i2v",
  "keyframe", "interpolate", "video to video", "retake", "restyle this clip",
  "generate a clip/reel", "follow this pose/edges/depth", "canny/pose/depth
  control", "match this motion".
argument-hint: "[/abs/path/image.jpg] [\"prompt\"] [i2v|keyframe|v2v|t2v|control]"

---

# ltx2-video — photo → video via self-hosted LTX-2.3

Turns a local image (or two, or a video) into an `.mp4` by calling the user's
**deployed** `ltx2-fast-inference` Modal app (LTX-2.3, 22B). Five modes:

| Mode | Input | What it does |
|---|---|---|
| `i2v` (default) | 1 image + prompt | animates the photo into a clip |
| `keyframe` | 2 images + prompt | interpolates A → B |
| `v2v` | 1 video + prompt | regenerates a time window (retake) |
| `t2v` | prompt only | text-to-video, no image |
| `control` | control render (+ optional init image) + prompt | IC-LoRA structural control — `union` follows a canny/depth/pose render. Canny auto-derives from a source video via ffmpeg; depth/pose need a pre-rendered control video. |

The work is done by `scripts/submit_video.py`, which calls the deployed app's
methods remotely via `modal.Cls.from_name` (no repo path needed).

## Setup (one-time)

- `pip install modal && modal token new`
- The backend must be deployed: `modal app list | grep ltx2-fast-inference`.
  If absent, deploy it from the `ltx2-fast-inference` repo: `./deploy.sh`.

## Workflow

1. **Resolve + validate the image.** Get the absolute path and confirm it's an image:
   ```bash
   realpath "<user-path>"            # normalize ~, relative, drag-dropped paths
   file "<abs-path>"                 # must contain JPEG / PNG / image data
   ```
   If not found or not an image, report and stop.
2. **Confirm before running** (it costs GPU time). Use **AskUserQuestion**:
   - header: `LTX-2.3`
   - question: `Generate video from <name>? Cold start ~90–200s. Warm: short/low-res ~7–9s, but full 10s 720p ~1–2 min (v2v ~8 min). A few cents either way.`
   - options:
     - `Quick smoke (cheap)` — low-res sanity check, confirms the container is warm
     - `Full quality` — 97 frames @ 768×1280 (vertical reel)
     - `Cancel`
3. **Run** the script (set `--timeout 300` on the Bash call — the first run cold-starts):
   ```bash
   # i2v (full)
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode i2v --image "<abs>" --prompt "<prompt>" --frames 97 --height 1280 --width 768

   # quick smoke (cheap warm-check)
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode i2v --image "<abs>" --prompt "<prompt>" --frames 17 --height 320 --width 512 --steps 8

   # keyframe (two images)
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode keyframe --image "<absA>" --image "<absB>" --prompt "<prompt>"

   # video-to-video retake
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode v2v --video "<abs.mp4>" --prompt "<prompt>" --start 2 --end 5

   # text-to-video
   python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py --mode t2v --prompt "<prompt>"

   # control (IC-LoRA union): auto-derive a CANNY edge render from a source video and follow it
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode control --video "<abs.mp4>" --control-type canny --prompt "<prompt>" [--image "<init.jpg>"]

   # control with a PRE-RENDERED control video (depth map / openpose / canny you already have)
   uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
     --mode control --control-video "<abs_control.mp4>" --prompt "<prompt>" [--image "<init.jpg>"]
   ```
   Immediately tell the user "waiting for container cold start (~90s)…" so it doesn't look hung.
   Output lands in `./video_out/` by default — override with `--out-dir <dir>`. (The flag is
   `--out-dir <directory>`, NOT `--out`.)
4. **Report.** The script prints `SAVED <path>` and `PREVIEW <png>`. **Read** the
   PREVIEW png so the user sees a still inline, then report the saved mp4 path +
   latency. Offer follow-ups (longer clip via `--frames`, keyframe, v2v restyle).

## Prompting

Subject + action first, then lighting/camera, photorealistic detail; keep it tight.
Frame counts must be `8k+1` (17, 49, 97, 121, 217, 241). bf16, no quantization.

**Resolution presets (`--format`)** — render native to the target platform, don't
crop. Default is `reel`.

| `--format` | Aspect | W×H | Use for |
|---|---|---|---|
| `reel` / `tiktok` / `shorts` / `vertical` *(default)* | 9:16 | 768×1280 | IG Reels, TikTok, YT Shorts |
| `youtube` / `landscape` / `wide` | 16:9 | 1280×704 | YouTube, landscape embed |
| `square` / `post` | 1:1 | 1024×1024 | IG/FB feed post |

`--width/--height` override the preset (must be divisible by 32).

**Image-grounded prompting (i2v) — do this for quality.** Don't make the user
describe their own photo. First **Read the image** and silently form a one-line
description (subject + setting + lighting), then build the prompt as
`<image description> , <motion> , <camera>`. Keep the description faithful so
identity/scene is preserved; only the motion + camera are new. A prompt that
contradicts the photo (e.g. "golden hour" on a flat-lit indoor face) fights the
model. Default motion = "subtle idle" if the user gives none.

**Keyframe coherence — the #1 keyframe rule.** Interpolation is only coherent when
A and B are the **same subject/scene** (same person, slightly different
pose/expression/camera). Unrelated A/B → a morph/dissolve (identity melt), not a
clean motion. If the user has only A, offer to make B by **editing A** (same
subject, one change) for a coherent pair; first/last frames of one clip are also
coherent by construction; A==B → a smooth loop. If A and B look unrelated, **warn**
before running (see references/mode_ux.md §3.3-B) and offer to make B a variant of A.

**Named motion presets, the per-mode interaction contracts, the decision tree,
the clarifying AskUserQuestion prompts, and per-mode latency** live in
`references/mode_ux.md` — read it when choosing a mode or expanding a motion prompt.

## Audio & batching

- **Audio is ON by default.** LTX-2.3 generates **synced audio** with the video. So
  put the *sound* in your prompt too — ambience, foley, a music mood (e.g. "rain
  patter and distant thunder", "soft lo-fi pad", "crowd murmur"). The model scores
  the audio from the same prompt.
- **Silent clip:** add `--skip-audio`. The **video pixels are byte-identical** with
  or without audio — skipping only drops the audio decode (slightly faster, smaller
  file). Use it for B-roll you'll score later, or when audio isn't wanted.
- **Batching — two kinds, both in one warm container (only the first take cold-starts):**
  - **Multiple passes of the same prompt** — `--variations N` runs N takes with seeds
    `seed..seed+N-1`. This is the "run a prompt 20 ways, keep the 1 good one" loop —
    fail-free iteration. Files: `<ts>_<mode>_s<seed>.mp4`. Pair with `--seed` to set
    the base / reproduce a take.
  - **Multiple different prompts** — `--prompts-file prompts.txt` (one prompt per line;
    i2v / t2v / keyframe). Files: `<ts>_<mode>_pNN.mp4`. For i2v/keyframe pass the
    `--image`(s) once — they apply to every prompt.
  - **They compose:** N prompts × M variations = N×M clips in one warm run. Cost scales
    with clip count; each clip is still a few cents. Suggest a cheap-smoke pass
    (`--frames 17 --height 320 --width 512 --steps 8 --variations 8`) to scan directions
    before committing to full-res takes.
  ```bash
  # 8 takes of one prompt to find a keeper
  uv run --with modal python3 ${CLAUDE_SKILL_DIR}/scripts/submit_video.py \
    --mode i2v --image "<abs>" --prompt "<prompt>" --variations 8
  ```

## Guardrails

- Always confirm via AskUserQuestion before a full run (GPU cost). Offer the cheap smoke first.
- First call after idle cold-starts (~90–200s). Warm latency is resolution-dependent: short/low-res ~7–9s, but full-res 10s clips ~95–120s (v2v ~470s) — at 768×1280 only one stage transformer fits resident, so stages rebuild per call. Use `--timeout 600` for full-res/v2v.
- Do NOT route through fal-mcp. For Hail Films / @patrawtf canon reels, use the `hail-films-reel` skill instead.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `modal not installed` | `pip install modal && modal token new` |
| `from_name` can't find app | deploy the backend: `./deploy.sh` in the ltx2-fast-inference repo |
| no mp4 / `no video returned` | check `modal app logs ltx2-fast-inference` |
| `CUDA out of memory` | should not happen on mode-switching anymore — the backend evicts resident transformers automatically (activation-aware cap) so each forward fits. If it ever appears, just retry once; the backend also has OOM-recovery. |
| looks hung | normal cold start — wait up to ~120s |
