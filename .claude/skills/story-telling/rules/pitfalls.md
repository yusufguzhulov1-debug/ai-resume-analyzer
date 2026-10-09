---
name: pitfalls
description: Common mistakes, and the checklist to run before generating and before shipping
---

# Pitfalls

Ordered by how often they actually bite.

## 1. Generating before the script is approved

Voices and images cost money and take minutes. A wrong figure caught in the
`story.json` review is free; caught after the render it costs the whole run.
Always show the narration to the user before running `generate`.

## 2. Editing durationInFrames by hand

`durationInFrames` and `audioDurationInSeconds` are outputs, not inputs. The
generator measures the real audio and writes them back. Hand editing them
desynchronises the subtitles immediately, because subtitle groups are spread
across the scene duration. If a scene feels too short, change the words.

## 3. Padding a scene to reach a round duration

Same failure. To make a 55 second story reach 60, raise
`outro.durationInFrames`, which is silent and has no subtitles. Never stretch a
narrated scene beyond its audio.

## 4. Digits in narration

"Rs 34,387 cr" is read unpredictably. Spell it: "thirty four thousand three
hundred eighty seven crore". Digits belong on the stat card, which is exactly
why the card exists.

## 5. Naming a real person in an image prompt

Either it is refused, or worse, it succeeds and produces a fabricated likeness.
Use a reference photo the user owns with the edit model, or describe the person
generically. This is a hard rule, not a style preference.

## 6. Burying the likeness clause

In an edit prompt, "keep his face, spectacles and features clearly
recognisable" must come first, before the scene description. Put it last and
the model drifts to a generic face.

## 7. Changing orientation after generating

Images are generated at the composition size. Flip `orientation` and every jpg
is the wrong shape, and `objectFit: cover` crops through the subject. Delete
the jpgs and rerun. Voices are unaffected, so pass nothing and let the skip
logic keep them.

## 8. Mixed Remotion versions

The classic symptom is a bundling failure:
`export 'Logging' was not found in 'mediabunny'`. Every `@remotion/*` package
must be on one version, with the `mediabunny` version that release expects.
`npx remotion versions` to check, `npx remotion upgrade` to fix.

## 9. Loading fonts wrong

`loadFont()` with no options pulls every weight and subset, dozens of requests
per family on every render. Requesting a weight a family does not ship throws
at render time: Space Grotesk stops at 700. Load at module level, never inside
a component, and always pass `weights` and `subsets`.

## 10. CSS animation

`transition`, `animation` and Tailwind animation classes render as a still
frame. Every frame is captured independently, so there is no wall clock. Drive
motion from `useCurrentFrame()` and `interpolate()`.

## 11. Forgetting to clamp interpolate

Without `extrapolateLeft: "clamp", extrapolateRight: "clamp"` values keep going
past their range: negative opacity, inverted scale, text sliding off frame at
the edges of a sequence.

## 12. Text in the platform-unsafe zone

Vertical videos lose the bottom of the frame to platform UI. Keep everything
meaningful above the bottom 260px, and inside the safe area from `getLayout()`
rather than typed pixel constants.

## 13. Reusing an image id

Ids are global across the story, not per scene. Two images sharing id 4 means
one silently overwrites the other. The zod schema does not catch this; the
symptom is a repeated frame.

## 14. Committing generated media or keys

`public/**/*.wav|mp3|jpg|png` is gitignored on purpose: `story.json`
regenerates all of it. Never commit `.env`, and never paste a key into
`.claude/settings.local.json` permission rules where it is stored in plain text.

## 15. Editing story.json while a generate run is in flight

An image run can take half an hour. `generate` used to write its whole
in-memory copy back at the end, so any edit made meanwhile was silently
discarded: stat cards added during the run simply vanished from the file and
from the render. It now re-reads the file and merges back only
`durationInFrames` and `audioDurationInSeconds`. Still, prefer to finish
editing before starting a long run, and verify a change landed by reading the
file back rather than trusting that you wrote it.

## 16. Cross fades that dip through black

If the outgoing image finishes fading out at the exact frame the next one
starts fading in, both sit at zero opacity and the transition flashes black.
The two ramps have to overlap: fade the outgoing image out over the same window
the incoming one fades in over, not over its own final frames. `ImageLayer`
does this, but the same trap applies to any transition added later.

## Checklist before generating

- [ ] Every figure in the narration traces to the given context
- [ ] Numbers spelled as words in narration, digits only on stat cards
- [ ] No hyphens, ampersands, brackets or emoji in any narration string
- [ ] 24 to 32 words per scene
- [ ] No real person named in any image prompt
- [ ] Image ids unique across the whole story
- [ ] `outro.imageId` points at an image that exists
- [ ] `orientation` matches the target platform
- [ ] `style.artPrompt` names the medium, the line, the palette and the people
- [ ] Font in `style` covers the narration's script

## Checklist before shipping

- [ ] `npm run typecheck` clean
- [ ] `npx remotion versions` reports all packages correct
- [ ] Watched end to end with sound, not just scrubbed
- [ ] Checked a frame in the middle of an image transition, not only mid scene
- [ ] Re-read story.json after any long generate run, to confirm edits survived
- [ ] Subtitles land with the voice on the last scene, where drift shows first
- [ ] No garbled text visible in any frame
- [ ] Faces consistent across every scene that uses the same reference
- [ ] Sources and dates in the narration match the context
- [ ] Output duration and file size reported to the user accurately
