---
name: claude-gif-create
description: >
  Programmatic GIF creation using Remotion (React-based). Generates text animations,
  loading spinners, logo reveals, meme templates, data visualizations, typewriter effects,
  and motion graphics as GIFs. Claude writes React components, Remotion renders frames,
  FFmpeg assembles with palette optimization. Use when user says "text animation gif",
  "loading spinner gif", "logo reveal gif", "meme template", "counter gif",
  "progress bar gif", "remotion gif", "programmatic gif", or "motion graphics gif".

---

# claude-gif-create -- Programmatic GIF Animation (Remotion)

Creates GIFs from React components rendered by Remotion. Best for text animations,
UI elements, geometric patterns, data-driven visuals, and anything that can be
expressed as code rather than captured from reality.

## Pipeline Overview

```
Concept --> React Component --> Remotion Render (PNG frames) --> gif_frames.py --> Optimized GIF
```

## Step-by-Step Procedure

### 1. Pre-Flight

```bash
# Verify Node.js 18+ and Remotion
node --version   # Must be >= 18
npx remotion --version
```

If Remotion project does not exist yet:
```bash
cd /tmp/claude-gif
npx create-video@latest gif-studio --template blank
cd gif-studio
npm install
```

Reuse existing project at `/tmp/claude-gif/gif-studio/` if it already exists.

### 2. Analyze Concept

Determine from the user's request:
- **Animation type**: text, spinner, counter, logo, progress bar, meme, typewriter, confetti
- **Content**: actual text, colors, sizes
- **Duration**: 1-5 seconds (shorter = smaller file)
- **Target platform**: determines dimensions and color budget
- **Loop behavior**: should it seamlessly loop? Most GIFs should.

### 3. Read Reference

Before writing any component:
```
Read ~/.claude/skills/claude-gif/references/remotion-gif.md
```
This contains template patterns, optimal settings, and code snippets.

### 4. Write React Component

Create the composition file at `/tmp/claude-gif/gif-studio/src/GifComposition.tsx`.

GIF-optimized composition settings:
- **Width**: 480-640px (wider = bigger file)
- **Height**: calculated from aspect ratio (usually 480x480, 480x270, or 640x360)
- **FPS**: 10-20 (lower = smaller file, 15 is the sweet spot)
- **Duration**: fps x seconds = durationInFrames (e.g., 15fps x 3s = 45 frames)

Key Remotion APIs:
```tsx
import { useCurrentFrame, useVideoConfig, spring, interpolate, Sequence, Img } from "remotion";
```

**Critical rules for GIF-quality output:**
- Use flat, solid colors. Gradients create more unique colors = larger palette = bigger file.
- Limit the color palette to 4-8 dominant colors when possible.
- Prefer simple backgrounds (solid color or subtle pattern).
- Avoid complex shadows or blurs (they create many intermediate colors).
- Use `spring()` for natural motion, `interpolate()` for linear control.
- Keep text large and readable at 480px width.

### 5. Register Composition

In `/tmp/claude-gif/gif-studio/src/Root.tsx`:
```tsx
import { Composition } from "remotion";
import { GifComposition } from "./GifComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="GifOutput"
      component={GifComposition}
      durationInFrames={45}
      fps={15}
      width={480}
      height={480}
    />
  );
};
```

### 6. Render to PNG Frames

```bash
mkdir -p /tmp/claude-gif/frames
npx remotion render src/index.ts GifOutput \
  --image-format png \
  --sequence \
  --output /tmp/claude-gif/frames/frame%04d.png \
  --concurrency 4
```

The `--sequence` flag outputs individual frames instead of a video.
Use `--concurrency 4` to speed up rendering on multi-core (8 cores available).

### 7. Assemble into GIF

```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_frames.py \
  --input-dir /tmp/claude-gif/frames/ \
  --fps 15 \
  --width 480 \
  --preset web \
  --output ~/Documents/gif_output/animation.gif
```

Or use gif_convert.sh if frames were rendered as a video:
```bash
bash ~/.claude/skills/claude-gif/scripts/gif_convert.sh \
  --input /tmp/claude-gif/frames/video.mp4 \
  --preset web \
  --output ~/Documents/gif_output/animation.gif
```

### 8. Optional Optimization

If the GIF is too large for the target platform:
```bash
~/.video-skill/bin/python3 ~/.claude/skills/claude-gif/scripts/gif_optimize.py \
  --input ~/Documents/gif_output/animation.gif \
  --target-size 256 \
  --output ~/Documents/gif_output/animation_discord.gif
```

### 9. Cleanup

```bash
rm -rf /tmp/claude-gif/frames/
```

Keep `/tmp/claude-gif/gif-studio/` for reuse.

## Template Patterns

### 1. Text Bounce
Animated text that bounces into view with spring physics.
- Use `spring({ frame, fps, config: { damping: 10 } })` for bounce
- Scale or translateY the text
- Best for: titles, announcements, greetings

### 2. Loading Spinner
Rotating dots, arcs, or bars.
- Use `interpolate(frame, [0, durationInFrames], [0, 360])` for rotation
- CSS `transform: rotate(${angle}deg)`
- Best for: loading indicators, status animations

### 3. Counter / Number Roll
Counting from 0 to N with easing.
- `Math.round(interpolate(frame, [0, durationInFrames], [0, targetNumber]))`
- Best for: stats, milestones, scoreboards

### 4. Logo Reveal
Logo fades/scales/slides into view.
- Combine opacity and scale interpolations
- Use `Sequence` for staggered reveals (icon first, then text)
- Best for: brand animations, watermarks

### 5. Progress Bar
Animated progress fill with percentage label.
- `interpolate(frame, [0, durationInFrames], [0, 100])`
- Best for: achievement unlocks, loading states

### 6. Meme (Top/Bottom Text)
Image with Impact font text overlaid.
- Use `Img` component for background, absolute positioned text
- Text stroke: `WebkitTextStroke: "2px black"`
- Best for: classic meme format

### 7. Typewriter Effect
Text appearing character by character.
- `text.substring(0, Math.floor(interpolate(frame, [0, dur], [0, text.length])))`
- Add blinking cursor with modulo frame check
- Best for: code reveals, dramatic text, terminal aesthetics

### 8. Confetti / Particle Burst
Colorful particles exploding outward.
- Pre-generate particle array with random angles and velocities
- Use `spring()` for gravity-like deceleration
- Keep particle count low (20-40) for GIF palette friendliness
- Best for: celebrations, congratulations

## Key Rules

1. **Always render as PNG frame sequence** (not video). This gives the most control over GIF assembly.
2. **Keep durations short**: 1-5 seconds. A 3-second GIF at 15fps = 45 frames = reasonable file size.
3. **Flat colors dominate**: Avoid CSS gradients, complex shadows, transparency blending.
4. **Test locally first**: `npx remotion preview` opens a browser for live preview.
5. **Reuse the project**: Don't recreate `/tmp/claude-gif/gif-studio/` if it already exists.
6. **Width dictates file size**: 480px is the sweet spot. Only go 640px for `hq` preset.
7. **FPS matters**: 10fps for tiny Discord GIFs, 15fps for normal use, 20fps max for smooth motion.

## Color Strategy

For the smallest GIFs with the best quality:
- Design with 4-8 primary colors
- Use a solid background color (not white -- a distinctive color compresses better)
- Avoid anti-aliasing where possible (crisp edges = fewer colors)
- If the design has gradients, switch dither to `bayer:3` (ordered dithering looks intentional)

## Error Recovery

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find module` | Missing Remotion deps | `cd /tmp/claude-gif/gif-studio && npm install` |
| `Composition not found` | ID mismatch | Check Root.tsx `id` matches render command |
| Blank frames | Component returns null | Check conditional rendering logic |
| Huge GIF file | Too many colors/frames | Reduce duration, colors, or width |
| Pixelated text | Width too small | Increase to 480px minimum |
