---
name: adaptive-glass
description: "Style for edit-video: the real speaker with moving proof in footage-matched glass panels, centered captions and event-matched sound. Use for talking-head product, tool and explainer reels with real screen proof, or when the creator asks for the glass look."
---

# Adaptive glass

A style on top of `edit-video`, which owns the cut, captions, sound and review. The finish for talking-head product, tool and explainer reels:
the real speaker, moving proof, a palette taken from the footage, centered
captions, selective modern glass and sound that follows visible events. Use it
when the creator chooses it or has no established look. Their own fonts, colors
and references take priority. Full camera, split screen and full proof are
layouts within the style, not separate styles.

Skip it for material that needs no panels: a personal reflection, a joke over
footage or a long screen demo that needs the whole canvas.

## Layouts follow the material

| Layout | Use | Starting geometry at 1080×1920 |
| --- | --- | --- |
| Full camera | A direct statement, reaction or turn with no useful asset | Camera fills the canvas; captions in the headroom |
| Half split | Proof or a diagram reads clearly above the speaker | Content above y=960; camera pane y=960–1920 |
| Third split | Proof needs more height and the face stays complete | Camera pane from about y=1120 |
| Full proof | Close UI detail, dense text, a result or an animation | Camera hidden; enlarge or reframe the useful detail |

Start proof-heavy reels with the half split when the proof stays readable. Full
screen has to earn its area; small proof over a large empty background means the
face should come back. Screen recordings fill their pane edge to edge
(`media-bleed`), without a nested card or heading. Change layout on spoken beats
or reveals. Open on the hook's subject: frame 1 should already show the product
or proof, not an empty panel.

## Face treatment

Use the actual camera plate, keep its aspect ratio and set the crop from real
frames of each take. The split pane blends through spare headroom: transparent
at the top edge, about 12% opaque at 65 px, 55% at 160 px and solid at 270 px,
with a 75 px side feather. Keep eyes and mouth sharp, keep the whole face in the
pane and check the blurred fill for a second ghost face. Full and split camera
layers are never visible together outside a deliberate transition. A tension
hook can use a fast, obvious push; compare first and peak frames, because a
speaker leaning back can cancel a digital zoom.

## Palette from the footage

Inspect the shirt, room, skin and proof separately. A dark shirt suits a lighter
related field; a light shirt may need a deeper one. The
[starting palettes](assets/palettes.json) are `soft-violet`,
`deep-violet` and `charcoal`; choose one per reel with `palette` and override
individual tokens with a `paletteFile`. Keep one color family, use dark heading ink
on a light field and light text on deep glass, and use red or green only when they
mean something. Polish the camera plate from the take (exposure, white balance,
natural skin) before judging colors.

## Material

- `glassMaterial: "optical"` for main panels, `"soft"` for supporting
  information; `glassTone: "dark"` or `"light"`. Set them for the whole plan or
  per scene.
- One quiet 1 px perimeter and 28–36 px corners. No stacked corner strokes. Nested
  media corners are concentric: inner radius ≈ outer radius minus the inset.
- Keep a glass surface at full opacity while it enters and move it instead,
  about 18 px over .42 s with an ease-out. Fading an ancestor changes what the
  backdrop samples and makes the blur pop. Fade text separately if needed.
- At most one low sweep after an optical panel settles, and only when the shot is
  long enough. Never a perpetual shimmer. Keep the blur stable.
- The CSS is optical styling, not refraction. For liquid-glass lensing, morphs or
  a named effect, search the HyperFrames registry (`hyperframes catalog`),
  inspect the item and render-test it in the project. If true fluid merging does
  not render reliably, use an honest shared-shape expansion and say so.
- Proof footage stays unobscured. Full proof is content, not a frosted panel.

## Motion

Carry one surface through connected states: a chip becomes a panel, a panel
slides into a new position, related shapes join or split when the explanation
calls for it. Tie each move to a spoken beat or visible action. Small arrivals
take about .3–.5 s and larger shared-shape transitions .45–.8 s, followed by a
readable hold. Use continuous velocity and a restrained settle; avoid a
universal bounce, robotic linear slides and repeated identical pop-ins. Words
stay stable while their surface moves. Every rendered state comes from timeline
time.

## Type and captions

Helvetica Neue Bold is the default, with Helvetica and Arial as fallbacks. Use an
installed font and confirm the renderer used it; never commit system font binaries.
Captions are usually one or two lines at about 54 px on a 1080-wide export;
panel headings 52–76 px with few words; source labels 24–30 px. Headings,
eyebrows and footers are optional. Alongside captions, allow at most one short
extra emphasis.

Starting caption anchors (fraction of height): full camera .235, half split .55,
third split .595, full proof .60–.615. Two-line captions overflow easily, so
measure the rendered box, backing and shadow against `edit-video`'s safe area. The scaffold writes these anchors
and a starting caption style to `captions.json` for the captioning tool.

## Sound map

Use `edit-video`'s curated sounds (`assets/sfx/`) and the gains in its manifest
as starting points:

| Visible event | Sound | Timing |
| --- | --- | --- |
| Frame 1 of the hook | `curated/hook-impact.wav` | On the opening frame |
| Large layout or camera change | `curated/camera-shutter.wav` | About 4 frames before the cut |
| Small framing or take change | `curated/camera-shutter-light.wav` | About 2 frames before |
| Panel or element arrival | `curated/ui-pop.wav` | On the arrival frame |
| Visible click or selection | `curated/ui-click.wav` | On the click |
| Motivated zoom, crop or pan | `curated/zoom-swish.wav` | Its rise follows the move |
| Build into a reveal | `curated/metallic-riser.wav` | Trim or stretch it to resolve on the reveal |
| Earned completion | `clean-ding.wav` | Sparingly |

Keep speech dominant and make demonstrated clicks and reveals audible. Put each
cue family on its own track so overlapping cues are not replaced, merge cues
fewer than about 6 frames apart and keep ordinary caption changes silent.

## Build the visual layer

1. Prepare the camera plate and proof clips in the run's `assets/`: trim, and crop
   from the original high-resolution source rather than enlarging a small copy.
2. Write a scene plan. Start from the
   [example](assets/composition.example.json): frame ranges at
   30 fps, `layout` (`face`, `split-half`, `split-third`, `full-proof`), `type`
   (`none`, `media-bleed`, `media-card`, `media-wide`, `proof`, `diagram`), media
   ranges, optional `label`, `title`, `footer` or `captionY`.
3. Generate a new composition:

   ```bash
   node <skill>/scripts/scaffold-glass.mjs <run>/work/scenes.json --output <run>/work/glass-v01
   ```

   It validates the whole plan before writing, refuses to overwrite a revision,
   copies media by hash and copies GSAP from the workspace runtime prepared by
   `init-workspace.mjs --install`.
4. Check, inspect key frames, then render with the workspace's HyperFrames
   (prepared by `edit-video`'s `init-workspace.mjs --install`):

   ```bash
   .favstash-studio/runtime/node_modules/.bin/hyperframes check <run>/work/glass-v01
   .favstash-studio/runtime/node_modules/.bin/hyperframes render <run>/work/glass-v01 --fps 30 --quality high --output <run>/previews/glass-v01.mp4
   ```

    The composition is silent: assemble dialogue, captions and sound
   in the editor or with FFmpeg, keeping them editable. The checker's
   `duplicate_media_discovery_risk` warning is expected, because the full-camera,
   split and blurred-fill layers share one camera plate.
5. Treat the output as a starter, not an art director. Adjust face placement and
   proof crops from the footage, and add purpose-built motion where proof is
   missing.

The material CSS is an original implementation informed by the six-layer optical
model in [liquid-glass-css](https://github.com/turtiesocks/agent-skills/tree/main/liquid-glass-css);
no third-party code is included.
