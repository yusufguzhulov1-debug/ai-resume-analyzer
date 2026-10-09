---
name: remotion-motion-graphics
description: Build animated motion graphics as real video with Remotion (React-based programmatic video) — title cards, lower thirds, logo stings, badges, stat reveals, countdowns, end screens, captions, animated charts, social reels — and export them as MP4 or as transparent ProRes/PNG sequences for Premiere, Final Cut, CapCut, DaVinci or After Effects. Use this skill whenever the user wants to create, animate, restyle, polish or render any video graphic, overlay, intro, reel or animation from code, or mentions Remotion, motion graphics, video overlays, alpha/transparency export, or asks to make an existing graphic feel smoother, less flat, less robotic or more premium — even when they never say "Remotion" out loud.
---

# Remotion Motion Graphics

Remotion renders React components into video. `useCurrentFrame()` tells a component which
frame it's drawing; everything animated is a pure function of that number. No timeline, no
keyframe UI — which is why graphics can be data-driven, reusable, and rendered with a real
alpha channel.

You already know how to write decent motion code. This skill exists for the three things
that are easy to skip and expensive to get wrong: **finding the actual bug before
polishing**, **verifying what you built**, and **the traps that fail silently**.

## Diagnose before you decorate

When a graphic "feels flat" or "looks like a PowerPoint," look for a defect before you
start adding springs. Complaints about *feel* are often a real bug the user can see but
can't name.

A real case: a stat callout counted up and "just sat there." The actual problem was
`interpolate(frame, [0, 60], [0, 12400])` with no clamp — Remotion extrapolates by
default, so the number never landed on 12.400, it climbed to 30.793 by the final frame.
The stat was *wrong*. Adding a bouncy entrance would have shipped a beautiful graphic
displaying a false number.

So: read the existing code, check what it actually computes at frame 0, mid, and
`durationInFrames - 1`, and fix what's broken. Then make it beautiful. `references/traps.md`
is the list of failures that look fine in the source — read it before touching animation
code, and check your own work against it when you're done.

## Verify what you built

Rendering the whole clip to find out it's wrong is the slow way. Check a still first:

```bash
npx remotion still <CompId> out/check.png --frame=45
```

Seconds instead of minutes. Check the key frames — mid-entrance, the payoff, mid-hold,
mid-exit — and **read the image**, don't just confirm the file exists. This is the step
most likely to get skipped and the one that catches the embarrassing stuff: the element
that never enters, the glow stuck on from frame 0, the text clipped by its container.

For alpha, the Studio's checkerboard is the proof. Confirm it there before rendering a
ProRes the editor will reject.

If the toolchain genuinely can't run, say so plainly in your summary — "this has never
been executed" is important information, not a footnote.

## Craft checklist

Apply by default; the reasoning is in `references/polish.md` if a case isn't obvious.

- **Complete enter → hold → exit.** Nothing on screen at frame 0, nothing still moving at
  the last frame. Reserve the exit *inside* the duration. Biggest single tell of amateur work.
- **Never linear.** `spring()` first (anticipation, overshoot, settle); `Easing` when you
  need `interpolate`.
- **Stagger**, 3–5 frames apart at 30fps — entrances *and* exits, same order.
- **Idle life** during the hold: gentle float, slow glow pulse, shine sweep. Felt, not noticed.
- **Payoff** on the key moment: scale pop, glow, ring, sound.
- **Geometric light, not clip-art.** Flash, expanding ring, thin streaks, bloom. Emoji and
  particle clip-art read as cheap instantly. One accent, not three.
- **Readability.** Title-safe 5–10% margins; scrim/shadow behind text over footage; one
  bold focal element; long strings shrink and wrap rather than overflow.
- **Timing follows content.** ~1s per short line to read; respect the length asked for.
- **Data-driven.** Text, colors, numbers, images as props with a zod schema +
  `defaultProps`, so it's restyleable from the Studio without touching code.
- **Canvas-relative sizing** (`useVideoConfig()`) and `sec()` for timings, so 4K or a
  vertical crop doesn't break the layout.

## Sound

Silent graphics are the most common gap — sound is roughly half of perceived polish, and
it's the thing that never gets added unless someone insists. A soft whoosh on entrance, a
click on key actions, a chime on success, a swish on exit.

```tsx
<Sequence from={sec(0.5)}>
  <Audio src={staticFile('audio/whoosh.mp3')} volume={0.6} />
</Sequence>
```

Trim leading silence from the source file — a file with 80ms of dead air lands 80ms late
no matter where the Sequence sits, and this is the usual reason audio "feels off" against
animation that looks right. For typing or counting, one continuous soft sound across the
duration; the same effect per character or per digit is grating.

If there's no `public/audio/`, don't invent it silently — tell the user sound is the next
biggest upgrade and offer to wire it when they drop files in.

## Modes

**No Remotion project** (no `remotion` dep) → scaffold: `references/scaffold.md`.

**Project exists, new graphic** → write the composition in `src/compositions/`, export
component + schema + defaultProps, register in `Root.tsx` with a unique id. Working code
for every pattern: `references/patterns.md`.

**"It feels flat"** → diagnose first (above), then `references/polish.md` for the upgrade
passes in priority order.

When the direction is open, 2–3 quick style variations beat guessing — polishing the wrong
direction is the most expensive mistake here.

## Render and export

```bash
# Full scene → MP4
npx remotion render <CompId> out/<name>.mp4 --codec=h264 --crf=18

# Overlay with real alpha → Premiere / FCP / DaVinci / AE
npx remotion render <CompId> out/<name>.mov --codec=prores \
  --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png

# Overlay → PNG sequence (CapCut and friends)
npx remotion render <CompId> out/<name>/frame-%04d.png --image-format=png

# Live preview
npm run studio
```

## References

- `references/traps.md` — silent failures. Read before writing animation code.
- `references/patterns.md` — working code: enter/exit, spring, stagger, alpha, audio,
  fonts, auto-fit, scenes.
- `references/polish.md` — upgrade passes for a flat graphic, by leverage.
- `references/scaffold.md` — new project from scratch.
