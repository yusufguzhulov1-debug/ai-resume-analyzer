---
name: claude-gif-edit
description: >
  Edit and modify existing GIFs. Speed change, reverse, ping-pong, crop, resize,
  text overlay, frame extraction, loop control, trim. Uses gifsicle for frame-level
  operations and FFmpeg for filters. Use when user says "edit gif", "gif speed",
  "reverse gif", "crop gif", "resize gif", "add text to gif", "gif text overlay",
  "extract frames", "loop gif", "ping pong gif", or "trim gif".

---

# claude-gif-edit -- GIF Editing and Modification

Modifies existing GIFs using gifsicle for frame-level operations and FFmpeg for
filters and complex transformations. All edits preserve the original file (output
to a new path).

## Pre-Flight

Before ANY edit:
```bash
bash ~/.claude/skills/claude-gif/scripts/preflight.sh INPUT.gif OUTPUT.gif
```

## Analyze Before Editing

Always inspect the GIF first:
```bash
# Quick stats
gifsicle --info INPUT.gif

# Detailed: dimensions, frame count, duration
ffprobe -v error -show_entries stream=width,height,nb_frames,r_frame_rate \
  -show_entries format=duration -of json INPUT.gif

# File size
stat -c%s INPUT.gif
```

---

## Edit Operations

### 1. Speed Change

**Speed up** (shorter delay between frames):
```bash
# 2x speed: halve the delay
gifsicle --delay 3 INPUT.gif -O3 -o OUTPUT.gif

# General formula: --delay is in centiseconds (1/100th of a second)
# 10fps = --delay 10, 15fps = --delay 7, 20fps = --delay 5, 30fps = --delay 3
```

**Slow down**:
```bash
# 0.5x speed: double the delay
gifsicle --delay 13 INPUT.gif -O3 -o OUTPUT.gif
```

**Precise speed change via FFmpeg** (re-encodes, so also apply palette):
```bash
# 2x speed
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] setpts=0.5*PTS,fps=15,scale=480:-1:flags=lanczos,split [a][b]; \
   [a] palettegen=stats_mode=diff [p]; \
   [b][p] paletteuse=dither=floyd_steinberg:diff_mode=rectangle" \
  -loop 0 OUTPUT.gif

# 0.5x speed
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] setpts=2.0*PTS,fps=15,scale=480:-1:flags=lanczos,split [a][b]; \
   [a] palettegen=stats_mode=diff [p]; \
   [b][p] paletteuse=dither=floyd_steinberg:diff_mode=rectangle" \
  -loop 0 OUTPUT.gif
```

Speed multiplier to PTS factor: `PTS_factor = 1.0 / speed_multiplier`
- 2x speed: `setpts=0.5*PTS`
- 3x speed: `setpts=0.333*PTS`
- 0.5x speed: `setpts=2.0*PTS`

### 2. Reverse

```bash
# Simple reverse via FFmpeg (re-encodes with palette)
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] reverse,fps=15,scale=480:-1:flags=lanczos,split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse=dither=floyd_steinberg" \
  -loop 0 OUTPUT.gif
```

**Frame-level reverse via gifsicle** (preserves quality, no re-encode):
```bash
# Get frame count
FRAMES=$(gifsicle --info INPUT.gif | grep -oP '\d+ images' | grep -oP '\d+')
# Reverse frame order
gifsicle INPUT.gif $(seq $((FRAMES-1)) -1 0 | sed 's/^/#/') -O3 -o OUTPUT.gif
```

### 3. Ping-Pong (Boomerang)

Play forward then backward for a seamless bounce effect:
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_loop.py \
  --input INPUT.gif \
  --method pingpong \
  --output OUTPUT.gif
```

**Manual via gifsicle**:
```bash
FRAMES=$(gifsicle --info INPUT.gif | grep -oP '\d+ images' | grep -oP '\d+')
FORWARD=$(seq 0 $((FRAMES-1)) | sed 's/^/#/')
REVERSE=$(seq $((FRAMES-2)) -1 1 | sed 's/^/#/')
gifsicle INPUT.gif $FORWARD $REVERSE -O3 --loop -o OUTPUT.gif
```

### 4. Crop

```bash
# Crop to region: --crop X,Y+WxH (from top-left corner)
gifsicle --crop 50,20+300x200 INPUT.gif -O3 -o OUTPUT.gif

# Center crop to square
W=$(gifsicle --info INPUT.gif | grep -oP 'logical screen \K\d+')
H=$(gifsicle --info INPUT.gif | grep -oP 'logical screen \d+x\K\d+')
SIZE=$((W < H ? W : H))
X=$(( (W - SIZE) / 2 ))
Y=$(( (H - SIZE) / 2 ))
gifsicle --crop ${X},${Y}+${SIZE}x${SIZE} INPUT.gif -O3 -o OUTPUT.gif
```

**FFmpeg crop** (with re-palette):
```bash
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] crop=300:200:50:20,split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse" \
  -loop 0 OUTPUT.gif
```

### 5. Resize

```bash
# Resize with gifsicle (fast, no re-palette)
gifsicle --resize-width 320 INPUT.gif -O3 -o OUTPUT.gif
gifsicle --resize-height 240 INPUT.gif -O3 -o OUTPUT.gif
gifsicle --resize 320x240 INPUT.gif -O3 -o OUTPUT.gif  # Exact (may distort)
gifsicle --resize-fit 320x240 INPUT.gif -O3 -o OUTPUT.gif  # Fit within (aspect preserved)

# Resize with FFmpeg (re-palettes for better quality)
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.gif \
  --width 320 \
  --output OUTPUT.gif
```

### 6. Text Overlay

Add text to a GIF using FFmpeg drawtext filter:
```bash
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] fps=15,scale=480:-1:flags=lanczos, \
   drawtext=text='Hello World':fontsize=36:fontcolor=white:borderw=2:bordercolor=black: \
   x=(w-text_w)/2:y=h-text_h-20,split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse=dither=floyd_steinberg" \
  -loop 0 OUTPUT.gif
```

**Meme-style top and bottom text**:
```bash
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] fps=15,scale=480:-1:flags=lanczos, \
   drawtext=text='TOP TEXT':fontsize=40:fontcolor=white:borderw=3:bordercolor=black: \
   x=(w-text_w)/2:y=20:font='Impact', \
   drawtext=text='BOTTOM TEXT':fontsize=40:fontcolor=white:borderw=3:bordercolor=black: \
   x=(w-text_w)/2:y=h-text_h-20:font='Impact',split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse=dither=floyd_steinberg" \
  -loop 0 OUTPUT.gif
```

**Animated text** (fade in):
```bash
# Text fades in over first 30 frames
ffmpeg -n -i INPUT.gif -filter_complex \
  "[0:v] fps=15,scale=480:-1:flags=lanczos, \
   drawtext=text='Appearing Text':fontsize=36:fontcolor=white@%{eif\\:min(1\\,n/30)\\:d}: \
   borderw=2:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2,split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse" \
  -loop 0 OUTPUT.gif
```

### 7. Frame Extraction

**Extract all frames**:
```bash
mkdir -p /tmp/claude-gif/extracted_frames
gifsicle --explode INPUT.gif -o /tmp/claude-gif/extracted_frames/frame

# Or via FFmpeg (as PNG with transparency):
ffmpeg -i INPUT.gif /tmp/claude-gif/extracted_frames/frame_%04d.png
```

**Extract specific frame** (e.g., frame 0 as thumbnail):
```bash
gifsicle INPUT.gif '#0' -o thumbnail.gif
# Or as PNG:
ffmpeg -i INPUT.gif -vf "select=eq(n\,0)" -vframes 1 thumbnail.png
```

**Extract frame range**:
```bash
gifsicle INPUT.gif '#10-#20' -O3 -o segment.gif
```

### 8. Loop Control

```bash
# Infinite loop (default for most GIFs)
gifsicle --loop INPUT.gif -o OUTPUT.gif

# Play exactly 3 times then stop
gifsicle --loop-count=3 INPUT.gif -o OUTPUT.gif

# Play once (no loop)
gifsicle --loop-count=1 INPUT.gif -o OUTPUT.gif

# Remove loop (play once, different from loop-count=1 in some viewers)
gifsicle --no-loop INPUT.gif -o OUTPUT.gif
```

### 9. Trim

**Trim by frame numbers**:
```bash
# Keep frames 10 through 40
gifsicle INPUT.gif '#10-#40' -O3 -o OUTPUT.gif

# Remove first 5 frames
FRAMES=$(gifsicle --info INPUT.gif | grep -oP '\d+ images' | grep -oP '\d+')
gifsicle INPUT.gif "#5-#$((FRAMES-1))" -O3 -o OUTPUT.gif

# Remove last 5 frames
gifsicle INPUT.gif "#0-#$((FRAMES-6))" -O3 -o OUTPUT.gif
```

**Trim by time** (via FFmpeg):
```bash
# Keep from 1.0s to 3.5s
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.gif \
  --start 1.0 \
  --duration 2.5 \
  --output OUTPUT.gif
```

### 10. Merge / Concatenate

**Append GIFs** (play one after another):
```bash
gifsicle INPUT1.gif INPUT2.gif -O3 -o MERGED.gif
```

**Side-by-side** (via FFmpeg):
```bash
ffmpeg -n -i LEFT.gif -i RIGHT.gif -filter_complex \
  "[0:v][1:v] hstack=inputs=2,split [a][b]; \
   [a] palettegen [p]; \
   [b][p] paletteuse" \
  -loop 0 OUTPUT.gif
```

---

## Chaining Edits

Multiple edits can be chained. Use intermediate temp files:
```bash
# Trim, then speed up, then add text
gifsicle INPUT.gif '#10-#50' -O3 -o /tmp/claude-gif/step1.gif
gifsicle --delay 3 /tmp/claude-gif/step1.gif -O3 -o /tmp/claude-gif/step2.gif
# Then text overlay via FFmpeg on step2.gif
rm /tmp/claude-gif/step1.gif /tmp/claude-gif/step2.gif
```

## Safety Rules

1. **Never overwrite input**: Output MUST be a different path than input.
2. **Preflight first**: Run preflight.sh before writing.
3. **Preserve original**: Do not delete or modify the source GIF.
4. **Temp files**: Use `/tmp/claude-gif/` for intermediates, clean up after.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `gifsicle: no frame #N` | Frame index out of range | Check frame count first with `--info` |
| Text not visible | Font color matches background | Use contrasting color with border |
| Quality degraded | Multiple FFmpeg re-encodes | Minimize re-encode passes, use gifsicle when possible |
| File size increased | Re-encoding overhead | Apply gifsicle -O3 after FFmpeg operations |
| Aspect ratio broken | Used `--resize` not `--resize-fit` | Use `--resize-fit` or `--resize-width` |
