---
name: text-over-footage
description: "Style for edit-video: one short, readable line of text over B-roll that matches it, for jokes, observations and setup/payoff reels. Use for POV and relatable text reels, recreations of a text-over-video format, or when there is no talking head."
---

# Text over footage

A style on top of `edit-video`. The text carries the idea; the footage supplies the
personality, the situation or the payoff. Prefer one clean full-screen shot and one
readable text block, visible from the first frame.

## Copy

- One premise, meaningful line breaks and a short payoff. Borrow the mechanism of a
  proven format (a relatable setup, a quick reversal, contrast between text and
  footage), then write a line that's true for this creator.
- When recreating a reference, read its overlay from the actual frames. A saved
  post's caption field often holds a different line from the one on screen.
- No unrequested CTA, explanatory paragraph or slogan.

## Footage

- **The creator's own footage by default**, matched to the joke's situation, not
  just "person at a desk": a date joke at a café, a late-night grind at a dark desk,
  a long day as a night-to-day timelapse.
- Avoid a stretch where they're visibly talking to someone unless the line is about
  talking. Slow, idle typing doesn't read as busy.
- Use another creator's clip only for a shot the creator explicitly names. Then
  soften its burned-in text, punch in about 10% and change the grade.
- A clip that has already been posted needs a punch-in and a new grade, or the
  platform's duplicate check may hold the reel (see `publish-and-analyze`).

## Type (tested defaults)

| Setting | Value |
|---|---|
| Font | One bold geometric sans, for example Sora Bold (OFL), white |
| Edge | No outline; a soft drop shadow (black, about 70% opacity, small blur, slight y offset) |
| Size | About 42px glyph height at 1080 wide, so a 32-character line spans about 700px |
| Wrapping | The fewest lines that fit about 700px, balanced, no single-word last line |
| Position | Centered, upper third by default (block center around y .23). Move it where the face or the joke needs space |
| Long copy | Same style, smaller |

Contrast comes from choosing clear space and from the shadow, not from a stroke.
Keep the whole block inside `edit-video`'s safe area.

## Timing and sound

Static text visible from the opening is the default; use a second reveal only when
it improves the joke or matches a visible action. Hold it long enough to read twice
at phone size: about 6–10 seconds for short copy. Longer copy needs more time or
fewer words, not smaller type.

A trending or original sound often carries this format. Use audio the creator may
reuse; a sound being available in the app doesn't make the file reusable elsewhere.
Static text changes don't each need a sound effect.
