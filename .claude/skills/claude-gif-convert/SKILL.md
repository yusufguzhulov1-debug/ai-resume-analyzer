---
name: claude-gif-convert
description: >
  Convert video files, image sequences, and animated SVGs to optimized GIFs.
  Mode A: Video to GIF (FFmpeg two-pass palette). Mode B: Image sequence to GIF.
  Mode C: AI image sequence to GIF (Gemini/FLUX.2 progressive prompts).
  Mode D: Animated SVG to transparent GIF (Playwright + FFmpeg).
  Use when user says "video to gif", "convert to gif", "screen recording gif",
  "images to gif", "photo sequence gif", "stop motion", "frames to gif",
  "svg to gif", "transparent gif", "animated svg to gif".

---

# claude-gif-convert -- Video, Image, and SVG to GIF Conversion

Four conversion modes for turning any visual source into an optimized GIF.

## Mode Detection

Determine the mode from the input:

| Input | Mode | Pipeline |
|-------|------|----------|
| `.mp4`, `.webm`, `.mov`, `.avi`, `.mkv` | A: Video to GIF | ffprobe analyze --> gif_convert.sh |
| Directory of `.png`/`.jpg`/`.webp` images | B: Image Sequence | glob + sort --> gif_frames.py |
| Text description of progressive scenes | C: AI Image Sequence | AI generate N frames --> gif_frames.py |
| `.svg` file (animated or static to animate) | D: SVG to Transparent GIF | Playwright capture --> FFmpeg palette |

---

## Mode A: Video to GIF

Convert a video file to an optimized GIF using FFmpeg two-pass palette generation.

### Procedure

1. **Analyze source video**:
```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate,codec_name -of json INPUT.mp4
```

2. **Determine segment** (if video is long, ask user which portion):
   - Full video: omit `--start` and `--duration`
   - Segment: specify `--start SS --duration SS`
   - Recommendation: GIFs should be 1-5 seconds. Warn if duration > 10s.

3. **Pre-flight check**:
```bash
bash ~/.claude/skills/claude-gif/scripts/preflight.sh INPUT.mp4 OUTPUT.gif
```

4. **Convert**:
```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.mp4 \
  --preset web \
  --output ~/Documents/gif_output/output.gif
```

5. **Report result** (gif_convert.sh outputs JSON with size, dimensions, settings).

### Preset Selection Guide

- User says "for Discord" or file must be tiny --> `--preset discord`
- User says "for Slack" --> `--preset slack`
- User says "for Twitter/X" --> `--preset twitter`
- User says "high quality" or "best quality" --> `--preset hq`
- No preference stated --> `--preset web`
- User specifies exact dimensions/fps --> omit preset, pass explicit flags

### Advanced Options

```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input INPUT.mp4 \
  --fps 12 \
  --width 320 \
  --start 5.5 \
  --duration 3 \
  --dither bayer:bayer_scale=3 \
  --stats-mode diff \
  --colors 128 \
  --loop 0 \
  --output ~/Documents/gif_output/output.gif
```

---

## Mode B: Image Sequence to GIF

Assemble a directory of images (PNG, JPG, WebP) into a GIF.

### Procedure

1. **Identify images**:
```bash
ls /path/to/frames/*.png | head -5
ls /path/to/frames/*.png | wc -l
```

2. **Verify order**: Images should be named with sequential numbering (e.g., `frame_001.png`, `frame_002.png`). If not, they will be sorted alphabetically.

3. **Pre-flight check**:
```bash
bash ~/.claude/skills/claude-gif/scripts/preflight.sh /path/to/frames/frame_001.png OUTPUT.gif
```

4. **Assemble**:
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_frames.py \
  --input-dir /path/to/frames/ \
  --pattern "*.png" \
  --fps 15 \
  --width 480 \
  --preset web \
  --output ~/Documents/gif_output/sequence.gif
```

### Options

- `--input-dir`: Directory containing frame images
- `--pattern`: Glob pattern to match frames (default: `*.png`)
- `--fps`: Playback frame rate
- `--width`: Output width (height auto-calculated)
- `--preset`: Quality preset (discord/slack/twitter/web/hq)
- `--output`: Output GIF path
- `--sort`: Sort order: `name` (default), `mtime`, `natural`

---

## Mode C: AI Image Sequence to GIF

Generate N image frames using AI (Gemini via banana MCP or FLUX.2) with progressive
prompt changes, then assemble into a stop-motion or animated GIF.

### Procedure

1. **Plan the sequence**: Determine what changes between frames.
   - Example: "sunrise over mountains" -- 8 frames from dark blue to golden yellow
   - Example: "flower blooming" -- 12 frames from bud to full bloom

2. **Generate frames** using progressive prompts:

**Option A: Gemini via banana MCP tool** (recommended for consistency):
```
For each frame i (0 to N-1):
  gemini_generate_image with prompt:
    "Frame {i+1} of {N}: [base description], [progressive change at stage i/N],
     consistent style, flat illustration, limited color palette, square format"
```

**Option B: FLUX.2 via image_generate.py** (local, no API cost):
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-video/scripts/image_generate.py \
  --prompt "Frame {i} of {N}: [description with progressive change]" \
  --width 512 \
  --height 512 \
  --output /tmp/claude-gif/frames/frame_{i:04d}.png
```

3. **Assemble frames**:
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_frames.py \
  --input-dir /tmp/claude-gif/frames/ \
  --fps 4 \
  --width 480 \
  --preset web \
  --output ~/Documents/gif_output/ai_sequence.gif
```

Low FPS (2-6) works best for AI image sequences since each frame is a distinct "scene".

### Tips for AI Image Sequences

- **Consistency is hard**: AI models may vary style between frames. Mitigate by:
  - Including strong style anchors in every prompt ("pixel art style", "watercolor style")
  - Using the same seed if the tool supports it
  - Keeping the composition simple and consistent
- **Frame count**: 6-12 frames is the sweet spot (more = more variation = less consistent)
- **Low FPS**: 2-6 fps gives a charming stop-motion look and hides inter-frame inconsistency

---

## Mode D: Animated SVG to Transparent GIF

Convert an animated SVG (CSS animations, SMIL, or JavaScript) to a GIF with
transparency support. Uses Playwright headless Chromium to capture frames.

### When to Use

- Converting SVG animations from the `svg-animate` skill to shareable GIFs
- Creating transparent logo animations for embedding
- Making animated icons, stickers, or UI elements with transparency
- Any SVG with `<animate>`, `@keyframes`, or GSAP animations

### Procedure

1. **Analyze the SVG**: Check for animation type and duration.
```bash
grep -E '<animate|@keyframes|animation:|requestAnimationFrame' input.svg | head -5
```

2. **Determine animation duration**: Parse from CSS `animation-duration` or SMIL `dur` attribute.

3. **Create Playwright capture script**:
```bash
cat > /tmp/claude-gif/capture_svg.js << 'SCRIPT'
const { chromium } = require('playwright');

(async () => {
  const svgPath = process.argv[2];
  const outputDir = process.argv[3];
  const fps = parseInt(process.argv[4] || '15');
  const durationMs = parseInt(process.argv[5] || '3000');
  const width = parseInt(process.argv[6] || '480');
  const height = parseInt(process.argv[7] || '480');

  const totalFrames = Math.ceil((durationMs / 1000) * fps);
  const frameInterval = durationMs / totalFrames;

  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width, height });

  // Load SVG with transparent background
  const svgUrl = `file://${svgPath}`;
  await page.goto(svgUrl, { waitUntil: 'networkidle' });

  // Inject transparent background
  await page.evaluate(() => {
    document.body.style.background = 'transparent';
    document.documentElement.style.background = 'transparent';
  });

  // Capture frames
  for (let i = 0; i < totalFrames; i++) {
    const frameNum = String(i).padStart(4, '0');
    await page.screenshot({
      path: `${outputDir}/frame_${frameNum}.png`,
      omitBackground: true,  // Transparency support
    });
    await page.waitForTimeout(frameInterval);
  }

  await browser.close();
  console.log(JSON.stringify({ frames: totalFrames, fps, duration_ms: durationMs }));
})();
SCRIPT
```

4. **Capture frames**:
```bash
mkdir -p /tmp/claude-gif/svg_frames
node /tmp/claude-gif/capture_svg.js \
  "$(realpath input.svg)" \
  /tmp/claude-gif/svg_frames \
  15 \
  3000 \
  480 \
  480
```

5. **Assemble with transparency** using FFmpeg two-pass with `reserve_transparent=1`:
```bash
# Pass 1: Generate palette with transparency reserved
ffmpeg -y -framerate 15 -i /tmp/claude-gif/svg_frames/frame_%04d.png \
  -vf "palettegen=reserve_transparent=1:stats_mode=diff:max_colors=255" \
  /tmp/claude-gif/palette.png

# Pass 2: Apply palette with transparency
ffmpeg -n -framerate 15 -i /tmp/claude-gif/svg_frames/frame_%04d.png \
  -i /tmp/claude-gif/palette.png \
  -lavfi "paletteuse=dither=bayer:bayer_scale=3:alpha_threshold=128" \
  -loop 0 \
  ~/Documents/gif_output/transparent.gif
```

Key FFmpeg flags for transparent GIFs:
- `reserve_transparent=1`: Reserves one palette slot for transparency
- `max_colors=255`: 255 colors + 1 transparent = 256 total
- `stats_mode=diff`: Only analyze changing pixels (optimal for animations)
- `alpha_threshold=128`: Pixels with alpha < 128 become transparent (adjust 0-255)
- `dither=bayer:bayer_scale=3`: Ordered dithering works best with transparency

6. **Cleanup**:
```bash
rm -rf /tmp/claude-gif/svg_frames /tmp/claude-gif/capture_svg.js /tmp/claude-gif/palette.png
```

### SVG Preparation Tips

- SVGs should have explicit `width` and `height` attributes (not just `viewBox`)
- If the SVG uses percentage-based sizing, wrap it in an HTML file:
```html
<!DOCTYPE html>
<html><head><style>
  body { margin: 0; background: transparent; overflow: hidden; }
  svg { width: 480px; height: 480px; }
</style></head>
<body>
  <!-- SVG content here -->
</body></html>
```
- CSS animations: ensure `animation-iteration-count: infinite` for seamless capture
- SMIL animations: set `repeatCount="indefinite"`

---

## Output Conventions

- Default output directory: `~/Documents/gif_output/`
- Naming: descriptive, lowercase, underscores: `campfire_loop.gif`, `logo_transparent.gif`
- Always report final file size, dimensions, frame count, and duration
- If result exceeds target platform size, suggest running through `claude-gif-optimize`

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| `No such file or directory` | Input path wrong | Verify with `ls`, use absolute paths |
| Huge GIF (>20MB) | Long video, high res | Trim duration, reduce width, use preset |
| No transparency in output | SVG has opaque background | Add `omitBackground: true`, check SVG has no `<rect>` background |
| Playwright not installed | Missing dependency | `npx playwright install chromium` |
| Frames out of order | Non-sequential naming | Use `--sort natural` in gif_frames.py |
| Choppy animation | Too few frames or low FPS | Increase FPS or capture more frames |
