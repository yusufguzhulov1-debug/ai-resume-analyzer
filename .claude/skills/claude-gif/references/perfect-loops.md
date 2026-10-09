# Perfect Loop Creation Techniques

Reference for creating seamless, perfectly looping GIFs. Load this when working
with any GIF that needs to loop smoothly without visible seams.

## Loop Quality Assessment

Before applying any technique, measure how close the GIF already is to a perfect loop.

### Mean Absolute Error (MAE) Between First and Last Frame

Extract frames and compare:
```bash
# Extract first and last frames
ffmpeg -i INPUT.gif -vf "select=eq(n\,0)" -vframes 1 /tmp/claude-gif/first.png
LAST=$(($(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 INPUT.gif) - 1))
ffmpeg -i INPUT.gif -vf "select=eq(n\,$LAST)" -vframes 1 /tmp/claude-gif/last.png

# Compare with ImageMagick
compare -metric MAE /tmp/claude-gif/first.png /tmp/claude-gif/last.png /tmp/claude-gif/diff.png 2>&1
```

### MAE Score Interpretation

| MAE Score | Quality | Action |
|-----------|---------|--------|
| < 5 | Perfect loop | No processing needed |
| 5 - 15 | Good loop | Subtle seam visible; optional crossfade with 3 frames |
| 15 - 30 | Fair loop | Noticeable jump; crossfade with 5-8 frames recommended |
| 30 - 60 | Poor loop | Significant jump; crossfade with 8-12 frames or ping-pong |
| > 60 | Not loopable | Content doesn't cycle; use ping-pong or regenerate |

## Technique 1: Crossfade Blending

The primary technique for creating seamless loops. Alpha-blends the last N frames
into the first N frames using a smooth transition curve.

### How It Works

```
Original frames:  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]

With 3-frame crossfade (blend zone = frames 8,9,10 blended into 1,2,3):

Frame 8: 75% original_frame_8 + 25% original_frame_1
Frame 9: 50% original_frame_9 + 50% original_frame_2
Frame 10: 25% original_frame_10 + 75% original_frame_3

Result:  [1] [2] [3] [4] [5] [6] [7] [8'] [9'] [10']
                                          ^ blended zone

When the GIF loops from frame 10' back to frame 1, the transition is seamless
because frame 10' is already 75% frame 3 (which follows frame 2 which follows frame 1).
```

### Blending Curve

Use a sine curve for smooth transitions (avoids linear-ramp artifacts):
```python
alpha = 0.5 * (1 - math.cos(math.pi * i / num_blend_frames))
blended = frame_end * (1 - alpha) + frame_start * alpha
```

The sine curve produces a gradual acceleration and deceleration at the blend boundaries,
making the transition invisible to the eye.

### Script Usage

```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_loop.py \
  --input INPUT.gif \
  --method crossfade \
  --frames 5 \
  --output OUTPUT.gif
```

### Frame Count Selection

| GIF Duration | FPS | Recommended Blend Frames | Blend Duration |
|-------------|-----|-------------------------|----------------|
| 2 seconds | 10 | 3 | 0.3s |
| 2 seconds | 15 | 4 | 0.27s |
| 3 seconds | 15 | 5 | 0.33s |
| 4 seconds | 15 | 6 | 0.40s |
| 5 seconds | 15 | 8 | 0.53s |
| 4 seconds | 20 | 8 | 0.40s |

**Rule of thumb**: Blend 10-15% of total frames. More blend frames = smoother transition
but shorter effective content.

### Crossfade Limitations

- Reduces effective content length (blend zone replaces content at the end)
- Can create ghosting with fast-moving subjects
- Doesn't work well when first and last frames are very different (MAE > 60)
- Subjects may appear transparent during blend zone

## Technique 2: Ping-Pong (Boomerang)

Plays the GIF forward then backward. Guaranteed to loop perfectly because
the reverse naturally returns to the first frame.

### How It Works

```
Original:    [1] [2] [3] [4] [5]
Ping-pong:   [1] [2] [3] [4] [5] [4] [3] [2]
              forward -->          <-- reverse (skip first and last to avoid double-frame)
```

### Script Usage

```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_loop.py \
  --input INPUT.gif \
  --method pingpong \
  --output OUTPUT.gif
```

### Manual Implementation

```bash
FRAMES=$(gifsicle --info INPUT.gif | grep -oP '\d+ images' | grep -oP '\d+')
FORWARD=$(seq 0 $((FRAMES-1)) | sed 's/^/#/')
REVERSE=$(seq $((FRAMES-2)) -1 1 | sed 's/^/#/')
gifsicle INPUT.gif $FORWARD $REVERSE -O3 --loop -o OUTPUT.gif
```

### When to Use Ping-Pong

- **Best for**: Pendulum motion, oscillating movement, gestures, nods, waves
- **Good for**: Any content where forward-reverse looks natural
- **Avoid for**: Rotation (looks unnatural going backward), water flow, fire
- **Caveat**: Doubles the number of frames (doubles file size). May need optimization after.

### Ping-Pong Variants

**Symmetrical ping-pong** (default): Forward then reverse, skipping duplicate frames at endpoints.

**Asymmetrical ping-pong**: Forward at normal speed, reverse at faster speed (or vice versa).
Useful for "snap back" effects:
```bash
# Forward at normal speed, reverse at 2x speed
# Extract frames, then reassemble with different delays
```

## Technique 3: Freeze-Frame Blend

Averages the first and last frames to create a "meeting point" frame, then
blends both the start and end of the GIF toward this average.

### How It Works

```
1. Compute average_frame = (first_frame + last_frame) / 2
2. Prepend 2-3 frames that blend from average_frame to first_frame
3. Append 2-3 frames that blend from last_frame to average_frame
```

### When to Use

- Content with very slow motion (slow camera drift, subtle particle movement)
- When crossfade causes too much ghosting
- When the first and last frames are similar but not identical

### Limitations

- Adds frames (increases file size)
- The "average frame" may look blurry if first and last frames are very different
- Only effective when MAE < 30

## Naturally Looping Content Types

Content that inherently loops well without post-processing:

### Perfect Natural Loops (MAE typically < 10)
- Fire / flames (chaotic motion, any frame connects to any other)
- Flowing water (continuous motion, no start/end)
- Rain / snow falling (particles enter and exit frame)
- Smoke / steam (continuous, chaotic)
- Sparks / particles (continuous emission)
- Rotating objects (360-degree rotation returns to start)
- Spinning/orbiting camera (completes full circle)

### Good Natural Loops (MAE typically 10-30)
- Breathing (chest expands and contracts)
- Pendulum / swinging (oscillation)
- Heartbeat (rhythmic pulse)
- Blinking lights / neon signs
- Waves (periodic motion)

### Difficult to Loop (MAE typically > 30)
- Walking / running (needs precise timing to match foot positions)
- Talking / speaking (mouth shapes rarely match)
- One-time actions (jumping, throwing, catching)
- Camera movement that doesn't complete a circle

## Cinemagraph Technique

A special loop technique: a static photograph with one masked element that loops.

### Concept
```
Static layer:  [frozen frame from the middle of the clip]
Motion mask:   [defines which area moves]
Motion layer:  [only the masked area animates from the original video]
```

### Implementation via FFmpeg

```bash
# 1. Extract a "still" frame (choose the best-looking one)
ffmpeg -i INPUT.mp4 -vf "select=eq(n\,30)" -vframes 1 /tmp/claude-gif/still.png

# 2. Create motion mask (white = motion area, black = static)
# This must be done manually or with edge detection:
ffmpeg -i INPUT.mp4 -vf "
  tblend=all_mode=grainextract,
  lumakey=threshold=0.05:tolerance=0.05,
  format=gray
" -frames:v 1 /tmp/claude-gif/mask.png
# Note: The mask usually needs manual refinement in GIMP

# 3. Composite: still background + masked motion area
ffmpeg -i INPUT.mp4 -i /tmp/claude-gif/still.png -i /tmp/claude-gif/mask.png \
  -filter_complex "
    [1:v]loop=loop=-1:size=1[bg];
    [0:v][bg][2:v]maskedmerge[out]
  " -map "[out]" /tmp/claude-gif/cinemagraph.mp4

# 4. Convert to GIF with diff_mode for tiny file size
bash gif_convert.sh --input /tmp/claude-gif/cinemagraph.mp4 --preset web \
  --stats-mode diff --output OUTPUT.gif
```

### Best Cinemagraph Subjects
- Steam rising from coffee (cup static, steam loops)
- Hair blowing in wind (person static, hair moves)
- Waterfall in landscape (landscape static, water falls)
- Flickering candle in still room (room static, flame dances)
- Flag waving on building (building static, flag moves)

### Why Cinemagraphs Make Great GIFs
- `diff_mode=rectangle` encodes only the tiny moving area
- File sizes are extremely small (often < 200KB even at high quality)
- Mesmerizing visual effect that draws attention
- Naturally loops because the motion area is typically chaotic/cyclical

## Loop Quality Verification

After applying any loop technique, verify the result:

### Visual Check
1. Open the GIF in a viewer that shows loop playback
2. Watch at least 5 complete loops
3. Focus on the loop seam -- is there a visible jump, flash, or stutter?
4. Check for ghosting or transparency artifacts in the blend zone

### Automated Check
```bash
# Extract first and last frames of the processed GIF
ffmpeg -i OUTPUT.gif -vf "select=eq(n\,0)" -vframes 1 /tmp/claude-gif/loop_first.png
LAST=$(($(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 OUTPUT.gif) - 1))
ffmpeg -i OUTPUT.gif -vf "select=eq(n\,$LAST)" -vframes 1 /tmp/claude-gif/loop_last.png

# Compute MAE
compare -metric MAE /tmp/claude-gif/loop_first.png /tmp/claude-gif/loop_last.png null: 2>&1
# Target: MAE < 5 for perfect loop
```

## Decision Flowchart

```
Is the content naturally looping? (fire, water, rotation)
  |
  +--> Yes --> Convert directly, verify MAE < 15
  |             |
  |             +--> MAE < 5: Perfect, done
  |             +--> MAE 5-15: Optional light crossfade (3 frames)
  |             +--> MAE > 15: Apply crossfade (5-8 frames)
  |
  +--> No --> Is it oscillating/pendulum motion?
               |
               +--> Yes --> Ping-pong loop
               |
               +--> No --> Is first/last frame similar? (MAE < 30)
                     |
                     +--> Yes --> Crossfade (5-8 frames)
                     |
                     +--> No --> Can a static area be isolated?
                           |
                           +--> Yes --> Cinemagraph technique
                           |
                           +--> No --> Ping-pong, or regenerate with loop-friendly prompt
```
