---
name: claude-gif-optimize
description: >
  Optimize GIF file size and quality. Multi-strategy optimization: gifsicle lossy compression,
  color reduction, dimension reduction, frame rate reduction, dithering changes.
  Platform auto-fit for Discord (256KB), Slack (500KB), Twitter (15MB), web (2MB).
  Use when user says "optimize gif", "reduce gif size", "compress gif", "gif too large",
  "fit discord", "fit slack", "gif file size", or "shrink gif".

---

# claude-gif-optimize -- GIF Size Optimization

Multi-strategy GIF optimizer that iteratively reduces file size while preserving
visual quality. Targets specific platform size limits or custom byte budgets.

## Pipeline Overview

```
Analyze GIF --> Choose Strategy --> Apply --> Check Size --> Iterate if Needed --> Report
```

## Step-by-Step Procedure

### 1. Read Reference

Before optimizing:
```
Read ~/.claude/skills/claude-gif/references/gif-optimization.md
Read ~/.claude/skills/claude-gif/references/platform-specs.md
```

### 2. Analyze Current GIF

```bash
# File size
stat -c%s INPUT.gif

# Frame count, dimensions, duration
ffprobe -v error -show_entries stream=width,height,nb_frames,r_frame_rate,duration \
  -show_entries format=duration,size -of json INPUT.gif

# Detailed frame info
gifsicle --info INPUT.gif | head -20
```

Record baseline: file size, dimensions (WxH), frame count, duration, FPS.

### 3. Determine Target

**Platform auto-detection** (from user's words):

| User Says | Target Size | Preset |
|-----------|------------|--------|
| "for Discord", "Discord" | 256 KB | discord |
| "Discord Nitro" | 50 MB | (custom) |
| "for Slack" | 500 KB | slack |
| "for Twitter", "for X" | 15 MB | twitter |
| "for Reddit" | 20 MB | (custom) |
| "for GitHub", "README gif" | 10 MB | (custom) |
| "for email" | 1 MB | (custom) |
| "for web", "website" | 2 MB | web |
| "small as possible" | minimize | aggressive |
| Specific number (e.g., "under 1MB") | parse number | custom |

### 4. Optimization Chain

Apply strategies in order from least to most destructive. Stop when target size is reached.

#### Strategy 1: Gifsicle Lossless Optimization
```bash
gifsicle -O3 --no-comments --no-names INPUT.gif -o OPTIMIZED.gif
```
Typical savings: 5-15%. Always apply first.

#### Strategy 2: Gifsicle Lossy Compression
```bash
gifsicle -O3 --lossy=30 INPUT.gif -o OPTIMIZED.gif     # Light (barely visible)
gifsicle -O3 --lossy=80 INPUT.gif -o OPTIMIZED.gif     # Medium (some artifacts)
gifsicle -O3 --lossy=150 INPUT.gif -o OPTIMIZED.gif    # Heavy (visible artifacts)
gifsicle -O3 --lossy=200 INPUT.gif -o OPTIMIZED.gif    # Maximum (significant artifacts)
```
Start with `--lossy=30`, increase by 30 until target is met.
Typical savings: 10-40% depending on level.

#### Strategy 3: Color Reduction
```bash
gifsicle --colors 192 -O3 INPUT.gif -o OPTIMIZED.gif   # Slight reduction
gifsicle --colors 128 -O3 INPUT.gif -o OPTIMIZED.gif   # Moderate
gifsicle --colors 64 -O3 INPUT.gif -o OPTIMIZED.gif    # Significant
gifsicle --colors 32 -O3 INPUT.gif -o OPTIMIZED.gif    # Heavy (posterization)
```
Typical savings: 10-30%. Works best on GIFs with many similar colors.

#### Strategy 4: Dimension Reduction
Re-encode at smaller dimensions via FFmpeg two-pass:
```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.gif \
  --width NEW_WIDTH \
  --fps ORIGINAL_FPS \
  --output OPTIMIZED.gif \
  -y
```

Dimension scaling guide:
- Current 640px --> 480px (43% fewer pixels)
- Current 480px --> 320px (56% fewer pixels)
- Current 320px --> 240px (44% fewer pixels)
- Each step roughly halves file size.

#### Strategy 5: Frame Rate Reduction
Re-encode with lower FPS:
```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.gif \
  --fps NEW_FPS \
  --width CURRENT_WIDTH \
  --output OPTIMIZED.gif \
  -y
```

Frame rate reduction guide:
- 20fps --> 15fps (25% fewer frames)
- 15fps --> 10fps (33% fewer frames)
- 10fps --> 8fps (20% fewer frames)
- Below 8fps looks noticeably choppy.

#### Strategy 6: Frame Dropping (gifsicle)
Remove every Nth frame:
```bash
# Keep only even-numbered frames (drops 50%)
gifsicle INPUT.gif --unoptimize $(seq -f '#%g' 0 2 $(gifsicle --info INPUT.gif | grep -oP '\d+ images' | grep -oP '\d+')) -O3 -o OPTIMIZED.gif
```
Use sparingly -- creates uneven timing.

#### Strategy 7: Dither Change (Re-encode)
Switch dithering algorithm for smaller output:
```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.gif \
  --dither "bayer:bayer_scale=3" \
  --stats-mode diff \
  --width CURRENT_WIDTH \
  --fps CURRENT_FPS \
  --output OPTIMIZED.gif \
  -y
```
`bayer` + `diff` mode often produces smaller files than `floyd_steinberg` + `full`.

### 5. Automated Optimization Script

For automated multi-strategy optimization:
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_optimize.py \
  --input INPUT.gif \
  --target-size 256 \
  --output ~/Documents/gif_output/optimized.gif
```

The script applies strategies in order, checking size after each step.

### 6. Before/After Report

Always report results:

```
Optimization Report
-------------------
Original:  1,245 KB  (640x360, 60 frames, 20fps, 3.0s)
Optimized:   248 KB  (320x180, 40 frames, 13fps, 3.0s)
Reduction: 80.1%

Applied strategies:
  1. Gifsicle -O3 --lossy=30    --> 1,058 KB (-15%)
  2. Colors 128                  --> 892 KB (-16%)
  3. Dimensions 640->320         --> 312 KB (-65%)
  4. Gifsicle --lossy=80         --> 248 KB (-21%)

Target: Discord (256 KB) -- PASS
```

## Platform Auto-Fit Algorithm

When targeting a specific platform:

```
1. Apply gifsicle -O3 --lossy=30
2. If still over target:
   a. Reduce colors to 128
3. If still over target:
   b. Reduce width by one step (640->480->320->240)
4. If still over target:
   c. Increase lossy to 80
5. If still over target:
   d. Reduce FPS by one step (20->15->10->8)
6. If still over target:
   e. Increase lossy to 150, colors to 64
7. If still over target:
   f. Reduce width by another step
8. If still over target after all steps:
   Report failure, suggest shorter duration or different content
```

## Quality Floor

Never go below these minimums (the GIF becomes unusable):
- Width: 160px
- FPS: 6
- Colors: 16
- Lossy: 200

If the target cannot be reached without going below quality floor, inform the user
and suggest trimming the duration or splitting into multiple GIFs.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| gifsicle: no such file | gifsicle not installed | `sudo apt install gifsicle` |
| Output larger than input | Re-encoding added overhead | Use gifsicle-only optimization (no FFmpeg) |
| Visible banding | Too few colors | Increase colors, switch to floyd_steinberg dither |
| Flickering frames | lossy too aggressive | Reduce lossy value |
| Still too large | Content inherently complex | Suggest shorter duration, smaller dimensions, or video format instead |
