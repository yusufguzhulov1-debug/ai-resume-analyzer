---
name: breakout-card
description: "Style for edit-video: a white grid page with the speaker in a rounded card along the bottom and their head breaking out above it, dark pills and cards that blur in and out, and one-to-two-word Montserrat captions, cut against full-camera beats. Use for talking-head explainers that alternate graphics with personal lines, or when the creator asks for the head pop-out card."
---

# Breakout card

A style on top of `edit-video`, which owns the cut, sound and review. The speaker
sits in a rounded card along the bottom of a white grid page, and their head (and
raised hands) break out above the card's top edge. Above them, one dark pill or
card at a time explains the line, and one or two words of caption sit between the
graphic and the head. Full-camera beats cut in for personal lines.

## The look (tested defaults)

| Element | Setting |
|---|---|
| Page | `#fcfcfd` with a static 54px grid in `#eaeaef` |
| Card | x 60–1020, top 1395, 18px radius, bleeding off the bottom; the camera's full width fills it |
| Breakout | The card's top edge cuts just above the eyes or glasses, so hair or a cap rise about 150–180px above it |
| Graphics | Dark material `#1c1c1f`, white text, one soft shadow, a faint inner rim. Pills 96px tall, cards 34–36px radius, at y 200–1000 |
| Type | Montserrat (OFL, bundled in `assets/fonts`). Pills 38px Bold, card text 32–37px SemiBold, headline 112px ExtraBold + 150px Black with grey-gradient ink |
| Captions | One or two words, lowercase as spoken, Montserrat Bold 60px. Page: dark ink between the graphic and the head. Camera: white, above the head |
| Accent | Navy for tags, lines and badges. Green and red only for a real check or a real strike |

Tokens sit in `scripts/breakout.py` (`TOKENS`); component CSS in `assets/breakout-card.css`.

## Layouts and rhythm

- **Page** for every informational beat. **Cam** (full frame) for personal lines and
  the name drop. **Camz** adds a slow push (1.2→1.27) for a re-hook like "here's the catch".
- Alternate every 4–10s with hard cuts, placed on the cut's jump cuts where possible
  so the jump hides inside the layout change.
- **Frame 1 is the page with real proof already moving**, such as a tilted capture flying in.
- On a camera beat, a big white title can replace the caption for the name drop.

## Captions

Write the chunks from the verified transcript with ASR timing: one or two words,
about 0.3–0.7s each, breaking on punctuation, lowercase except file names and the
CTA keyword. They are baked into the render because the font and word rhythm are the
look; the compiler writes `captions.json` so a wording fix is a quick re-render.
A chunk crossing a layout change splits and restyles automatically. Check the
longest chunk in both layouts against `edit-video`'s safe area.

## Graphics vocabulary

| Component | Use |
|---|---|
| `shot` | Real capture as a 3D-tilted card, optional highlight sweep. `drop=True` for frame 1 |
| `counter_pill` | A spoken figure counting up to the real value |
| `headline` | Small line, then a huge and a mega word |
| `tile_drop` | A file drops into a folder tile |
| `checklist` | Card whose items appear and tick on their words |
| `pill` | One idea in a capsule; `ok_at` adds a check, `strike_at` a red strike and cross |
| `cursor_click` | Hand cursor clicks a pill |
| `tree` + `tree_wander` / `tree_straight` | An agent wandering through folders vs. going straight to the right one |
| `doc_card`, `chip` | A file that fills as it is described, then shrinks to a chip |
| `comment` | CTA: a viewer comment types the keyword, chips pop for what they get |
| `title` | Big white name drop over the camera |

Everything **blurs into focus** (opacity 0, scale .7–.86, blur 16px → sharp in about
.35s) and **blurs away** (.25s). One graphic group at a time; it enters on the noun
and acts on the verb. Real captures for facts; mockups stay generic and unmeasured
meters say `illustrative`.

## Head breakout plates

`scripts/build_plates.py` turns the cut camera plate (1080×1920, silent is fine)
into a page plate and a full-camera plate. Needs Python 3.10+, `numpy` and `opencv-python`.

1. `prep <camera.mp4> <plate-dir>` converts to a constant frame rate and makes the
   person matte: Apple Vision on macOS (compiled from `person-matte.swift`, needs the
   Xcode command line tools). Elsewhere, pass `--matte <video>` with a white-on-black
   person matte from any segmentation tool.
2. `still <plate-dir> 3 12 22 30 40` and inspect the head edge in each still. Tune
   with `--set` (saved to `plates.json`): `cutRow` (source row on the card's top edge),
   `bgKey` (removes wall-coloured fringe at the silhouette edge), `objectKeys` (a wall
   item right behind the head that the matte grabs) and `protect` (keeps keys away
   from the face and glasses).
3. `render <plate-dir>` writes `page-plate.mp4` and `cam-plate.mp4`.

## Build

Needs the workspace runtime from `edit-video`'s `init-workspace.mjs --install`.

1. Cut the dialogue with `edit-video`; keep the word timeline.
2. Make the plates (above) and capture proof.
3. Write the run's build script with `layouts`, `captions` and one `scene` per page
   section ([example_build.py](scripts/example_build.py) shows mechanics only):
   ```python
   sys.path.insert(0, '<this skill>/scripts')
   from breakout import Reel
   reel = Reel('<run>/work/breakout-v01', page_plate='<plates>/page-plate.mp4', cam_plate='<plates>/cam-plate.mp4', total=1363)
   ```
4. Check and render with `.favstash-studio/runtime/node_modules/.bin/hyperframes`.
   If frame 0 renders black, clone frame 1 over it before assembly.
5. Mix dialogue and SFX in your editor, or `scripts/preview_mix.py <cues.json> <dialogue.wav> <out.wav>`
   for a quick review mix. Review with `edit-video`.

## Sound map (`edit-video`'s SFX pack)

| Visible event | Cue |
|---|---|
| Frame 1 | `curated/hook-impact.wav` |
| Page ↔ camera | `curated/camera-shutter.wav` 4 frames early; the light shutter into a page |
| Re-hook push | `curated/metallic-riser.wav`, resolving on the cut back to the page |
| Graphic arrives | `curated/ui-pop.wav` (rows and chips quieter) |
| Tick, click, count landing | `curated/ui-click.wav` |
| Blur-away, line draws, file drops | `curated/zoom-swish.wav`; `sub-impact.wav` where something lands |
| Earned yes | `clean-ding.wav`, once |

## Pitfalls already paid for

- Matte the constant-frame-rate copy that `prep` makes; a matte from a variable-rate
  cut drifts a frame at every gap.
- A coloured light on hair or a cap can make it as tinted as the wall behind it, only
  darker. The sampled-wall key with the default thresholds keeps it; a hue-only key eats it.
- Keys inside the silhouette punch holes in reflective glasses; `protect` stops that.
- Measure long headline words: 196px overflowed a 1080 canvas; the mega line is 150px.
- Draw-on paths need their measured length (`smooth_path` returns it).
- Animate the element inside a `.row`, never the row itself (it is the centring wrapper).
