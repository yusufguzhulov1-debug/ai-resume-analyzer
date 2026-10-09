# Polish passes

Use this when a graphic exists but feels flat, cheap, or "off" in a way that's hard to
name. The passes are ordered by leverage — the first one fixes more perceived quality
than the rest combined, so work top-down rather than picking the one that sounds most
interesting.

Diagnose before you edit. Render a still at a few key frames, or watch it in the Studio,
and find *what* is wrong. "Make it better" applied blindly tends to add effects on top of
a timing problem, which makes it worse and busier.

## 1. Complete enter and exit

**Symptom:** things appear already on screen, or the clip ends while something is still
moving. Elements feel like they blink in and out.

**Fix:** every element animates in (from off-screen or opacity 0), holds, then animates
fully out before the clip ends. Nothing at frame 0, nothing at the last frame.

This is first for a reason: it's the clearest signal of amateur work and the cheapest to
fix. If you only do one pass, do this one.

## 2. Non-robotic motion

**Symptom:** movement is technically correct but lifeless. Constant velocity, no weight.

**Fix:** anticipation (a small wind-up in the opposite direction), overshoot (pass the
target), settle (come back). `spring()` gives you this for free — a lower `damping` means
more bounce. Where you need `interpolate()`, always pass an `Easing`.

## 3. Stagger

**Symptom:** several elements arrive at once, and it reads as an accident.

**Fix:** offset entrances 3–5 frames apart (at 30fps). The eye follows a cascade; it
can't follow a chorus.

## 4. Idle life

**Symptom:** the graphic freezes during its hold and looks like a static image with an
animated entrance bolted on.

**Fix:** something subtle during the hold — a gentle float, a slow glow pulse, a shine
sweep. The bar is that the viewer should feel it, not notice it.

## 5. Payoff

**Symptom:** the graphic builds to a number or a result and then just... sits there.

**Fix:** give the key moment a beat — a scale pop, a glow bloom, a few light particles, a
sound. This is what makes a reveal *land* instead of merely happening.

## 6. Effects and accent

**Symptom:** either nothing distinguishes it, or it's cluttered with decoration.

**Fix:** prefer geometric light — a flash, an expanding ring, thin streaks, soft glints, a
bloom. Emoji and clip-art particles read as cheap and no amount of good animation
recovers from them. Add *one* tasteful animated accent (light traveling a border, a slow
gradient shift) for a premium feel. One. A second one starts costing you.

## 7. Readability and layout

**Symptom:** text overflows, gets clipped, disappears over bright footage, or everything
competes for attention.

**Fix:** title-safe area (5–10% margins). A shadow, scrim, or backing shape behind text
that sits over footage. Auto-fit long strings — shrink and wrap rather than overflow,
because real content is messier than your defaults. One bold focal element, supporting
text smaller and lower-contrast.

## 8. Sound

**Symptom:** it's silent, or the sounds feel slightly late.

**Fix:** soft whoosh on entrance, click/pop on key actions, chime on success, swish on
exit. Trim leading silence from every file so the hit lands exactly on its frame — this
is almost always the cause of "the audio feels off" when the animation looks right. Keep
levels balanced, no clipping. For typing or counting, one continuous soft sound across
the whole duration; the same effect per character or per digit is grating.

## 9. Reusable and on-brand

**Symptom:** values are hardcoded; restyling means editing code; graphics in the set don't
look related.

**Fix:** expose text, colors, numbers and images as props with a zod schema so the user
can restyle from the Studio. Define brand once (accent colors, font, corner radius) in a
tokens module and apply it everywhere. Support real images via a prop with a clean
placeholder fallback, so it looks right both before and after the user's assets arrive.

## Workflow habits that make polish cheap

**Check a still first.** `npx remotion still <CompId> out/check.png --frame=45` — seconds
instead of minutes. Review the key frames before committing to a full render.

**Offer variations before polishing.** When the direction is open, 2–3 rough style options
let the user pick before you invest in refining one. Polishing the wrong direction is the
most expensive mistake available here.

**Match timing to content.** About a second per short line to read, and stay within the
length the user asked for.
