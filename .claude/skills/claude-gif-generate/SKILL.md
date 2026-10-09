---
name: claude-gif-generate
description: >
  AI video-to-GIF generation using Veo 3.1. Generates short AI video clips and converts
  to optimized GIFs with palette optimization and perfect loops. Best for cinematic loops,
  product demos, abstract art, realistic motion. Use when user says "AI gif",
  "cinematic gif", "generate realistic gif", "product demo gif", "Veo gif",
  "abstract art gif", or "movie quality gif".

---

# claude-gif-generate -- AI Video-to-GIF (Veo 3.1)

Generates photorealistic or stylized AI video clips using Google Veo, then converts
them to optimized GIFs with palette optimization, perfect loops, and platform sizing.

## Pipeline Overview

```
Prompt Engineering --> Veo Generate (MP4) --> gif_convert.sh (GIF) --> gif_loop.py (Loop) --> gif_optimize.py (Shrink)
```

## Step-by-Step Procedure

### 1. MANDATORY: Read Prompt Reference

Before constructing ANY Veo prompt for GIF output:
```
Read ~/.claude/skills/claude-gif/references/prompt-engineering.md
```

This is not optional. GIF-optimized prompts differ significantly from general video prompts.
Loop-friendly prompts and static-background strategies reduce file size dramatically.

### 2. Cost Confirmation

Veo generation costs real money. ALWAYS confirm with the user before proceeding.

| Model | Duration | Approximate Cost |
|-------|----------|-----------------|
| veo-3.0-fast-generate-001 | 4 seconds | ~$0.60 |
| veo-3.0-fast-generate-001 | 8 seconds | ~$1.20 |
| veo-3.0-generate-001 | 4 seconds | ~$1.20 |
| veo-3.0-generate-001 | 8 seconds | ~$2.40 |

**Recommendation**: Use `veo-3.0-fast-generate-001` with 4 seconds for GIFs. Shorter clips
make better GIFs (smaller files, easier to loop). Fast model quality is excellent for GIF
resolution (480px).

Tell the user: "This will use Veo 3.0 Fast (4s) costing approximately $0.60. Proceed?"

### 3. Analyze GIF Concept

Determine from the user's request:
- **Loop requirement**: Most GIFs should loop. Identify if the content naturally loops.
- **Aspect ratio**: 16:9 (landscape), 9:16 (portrait/mobile), 1:1 (square, best for GIFs)
- **Duration**: 4 seconds minimum (Veo constraint). 4s is ideal for GIFs.
- **Subject matter**: Affects prompt engineering strategy.
- **Target platform**: Determines final optimization pass.

### 4. Construct Loop-Friendly Prompt

Read `references/prompt-engineering.md` for detailed patterns. Key principles:

**Natural loops** (motion returns to start):
- Circular camera orbits: "Camera slowly orbits 360 degrees around..."
- Pendulum motion: "swinging", "rocking", "bobbing"
- Cyclical natural motion: fire, waves, rain, clouds, breathing, flickering

**Static background strategy** (reduces GIF file size via diff_mode):
- "A [moving subject] against a solid [color] background"
- "Isolated [subject] on a clean, minimalist backdrop"
- Moving subject on static background = only changed pixels encoded = smaller GIF

**What to AVOID in prompts:**
- Narrative progression ("walks across", "enters the room", "picks up")
- Scene changes or cuts
- Camera movement that doesn't return to start
- Complex multi-subject interactions

### 5. Generate Video

```bash
~/.video-skill/bin/python3 ~/.claude/skills/veo/scripts/generate.py \
  --prompt "A single candle flame flickering gently against a solid black background, close-up macro shot, the flame dances in a continuous loop, warm orange and yellow tones, 4K quality" \
  --model veo-3.0-fast-generate-001 \
  --duration 4 \
  --aspect-ratio 16:9 \
  --resolution 720p \
  --output /tmp/claude-gif/veo_output.mp4
```

Parameters:
- `--model`: Use `veo-3.0-fast-generate-001` for cost efficiency
- `--duration`: 4 (minimum and ideal for GIF)
- `--aspect-ratio`: Match GIF intent (16:9 for landscape, 1:1 for social)
- `--resolution`: 720p is sufficient; GIF will be downscaled to 480px anyway

### 6. Convert to GIF

```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input /tmp/claude-gif/veo_output.mp4 \
  --preset web \
  --output ~/Documents/gif_output/candle.gif
```

Choose preset based on target. For unknown targets, use `web` (480px, 15fps, 256 colors, 2MB cap).

### 7. Perfect Loop (If Needed)

Inspect the GIF. If the loop has a visible "jump" at the seam:

```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_loop.py \
  --input ~/Documents/gif_output/candle.gif \
  --method crossfade \
  --frames 5 \
  --output ~/Documents/gif_output/candle_looped.gif
```

Methods:
- `crossfade`: Alpha-blend last N frames into first N frames. Best for most content.
- `pingpong`: Play forward then reverse. Best for pendulum/oscillating motion.
- `freeze`: Blend first and last frames. Subtle, good for slow-moving content.

Read `references/perfect-loops.md` for detailed technique guidance.

### 8. Platform Optimization (If Needed)

If the GIF exceeds the target platform's size limit:

```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_optimize.py \
  --input ~/Documents/gif_output/candle_looped.gif \
  --target-size 256 \
  --output ~/Documents/gif_output/candle_discord.gif
```

### 9. Cleanup

```bash
rm -f /tmp/claude-gif/veo_output.mp4
```

## Prompt Templates by GIF Type

### Cinematic Loop (Nature)
```
"[Natural element] in continuous seamless motion, [lighting], static camera,
[color palette], cinematic quality, the motion naturally repeats"
```
Examples: crackling fire, ocean waves, falling rain, swirling smoke, flickering aurora

### Product Demo (Turntable)
```
"A [product] slowly rotating 360 degrees on a clean [color] surface,
studio lighting, product photography, the rotation completes one full cycle"
```

### Abstract Art Loop
```
"Abstract [pattern/shape] flowing and morphing in a continuous cycle,
[color palette], minimalist background, mesmerizing seamless loop"
```

### Cinemagraph (Partial Motion)
```
"A [scene description] where only the [specific element] moves,
everything else perfectly still, cinematic quality, subtle continuous motion"
```
Examples: steam rising from a cup (cup static), hair blowing in wind (person still)

### Reaction GIF
```
"Close-up of a [subject/character] [facial expression or gesture],
[emotion], isolated against [simple background], short expressive motion"
```

## Decision Matrix: Veo vs Remotion

| Factor | Use Veo (generate) | Use Remotion (create) |
|--------|-------------------|-----------------------|
| Content | Photorealistic, nature, people, products | Text, UI, geometric, data |
| Motion | Complex physics, fluid dynamics | Programmatic, spring-based |
| Cost | ~$0.60+ per generation | Free (local render) |
| Speed | 30-90 seconds generation | 5-15 seconds render |
| Looping | Needs post-processing | Designed into component |
| File size | Larger (complex scenes) | Smaller (flat colors) |
| Predictability | AI may vary | Exact output every time |

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Veo rate limit | Too many requests | Wait 60 seconds, retry |
| Veo safety filter | Prompt flagged | Rephrase prompt, remove potentially sensitive terms |
| Video too dark | Prompt lacks lighting cues | Add "well-lit", "bright", specific lighting description |
| Loop seam visible | Motion doesn't naturally cycle | Apply crossfade via gif_loop.py |
| GIF too large | Complex scene, many colors | Use discord/slack preset, or optimize aggressively |
| Generation failed | API error | Check ~/.claude/skills/veo/scripts/generate.py logs |
