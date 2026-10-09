---
name: paper-grid
description: "Style for edit-video: a white paper pane with a quiet grid above the speaker and one clean animated UI artifact per spoken line (cards that type, counters, lists that expand, approvals that click). Use for tool, repo, skill or feature explainers where each sentence names something that can be drawn as UI."
---

# Paper grid

A style on top of `edit-video`, which owns the cut, captions, sound and review. The
top half is white paper with a quiet grid; the speaker stays in the bottom half.
Every spoken item gets its own small, living artifact: a card types, a counter
climbs, a row lights up, a cursor clicks.

## Fixed identity, open imagination

Keep the identity: white paper, the quiet grid, white cards with one rim, one navy
accent, Helvetica Neue, one clear idea per beat, real proof for facts. Everything
else is designed for the story in front of you.

- **The library is a vocabulary, not a template.** Use a component when it is the
  best picture of the line, and invent a new artifact when it isn't: a terminal that
  types, a diff that turns green, a flowchart that wires itself.
- **Each reel should feel designed for its topic.** Change which artifacts appear,
  how they connect, the rhythm and the one or two moments that surprise.
- **Aim for one screenshot-worthy idea per reel:** an object that transforms into
  the next beat, a satisfying click, a counter that lands on the spoken word.

Fits a talking head about a tool, repo, workflow or feature. Dark or saturated room
footage benefits most: the white pane gives contrast and a clean seam. Not for
personal reflections, jokes over footage or long screen demos that need the whole frame.

## The look (starting defaults)

| Element | Setting |
|---|---|
| Paper | `#fbfbfd` pane at y 0–960. Grid 45px minor / 180px major lines at 5.5% / 10% ink, radial fade at the edges, drifting one cell over the reel |
| Seam | Hard split at y=960 with a 1px light line and a soft shadow into the camera |
| Cards | White, 30px radius, one 1px rim, soft drop shadow, about 740–820 wide, centered on x=540 |
| Chips | 64px white capsules with a 42px icon tile, 28px bold |
| Ink | `#0f172a` text, `#64748b` muted, navy accent `#1e40af` / `#5b9eff`. Red, amber and green only where they mean something |
| Type | Helvetica Neue. Card text 30–36px, labels 21–28px, hero figures 200–270px |
| Skeletons | Grey bars and gradient avatars stand in for people and body text; only the words that carry the point are real |

Tokens live in `scripts/paper_grid.py` (`TOKENS`), component CSS in
`assets/paper-grid.css`. Override per reel with `Reel(tokens=...)`.

## Layout and motion

- **Split for almost everything.** Artifacts sit at y 270–940; captions go on the
  speaker's headroom (about y=.55). Set `split_video_top` from the actual take so the
  head starts below the caption band.
- **Full camera only for re-hooks** ("but the best part is…"): push in over the line,
  then return to the split on the reveal word.
- **Frame 1 shows the product moving:** open on the split with the first artifact
  already on screen and settling.
- **One artifact per spoken item, on its word.** It enters on the noun and acts on
  the verb. Entrances .35–.45s (cards rise 50px, chips pop), exits .2s, 6 frames
  before the next item. Carry one object through related beats.
- Keep it alive with typing, counters, a highlight sweep, a live dot; no perpetual
  shimmer, spin or bounce. Start from the [motion library](references/motion-library.md).

## Truth rules

- **Real proof for facts:** the actual repo page, list or product screen
  (`scripts/capture_page.py`), checked against the source that day. Crop to the
  content that reads at phone size and push into the words that carry the beat.
- **Mockups stay generic:** skeleton posts and counters carry no real names or
  results; unmeasured meters carry an `ILLUSTRATIVE` label and no numbers.
- Don't reuse a reference creator's graphics or identity. Borrow the mechanism only.

## Build

Needs Python 3.10+ and the workspace runtime from `edit-video`'s
`init-workspace.mjs --install` (HyperFrames and GSAP). Snapshots and page captures
also need `pip install playwright` and Google Chrome.

1. Cut the dialogue with `edit-video` and keep a word timeline; beat frames come from it.
2. Capture proof into the run's `assets/`, cropped to the fact that matters.
3. Write the run's build script: one `with reel.scene(...)` per beat
   ([example_build.py](scripts/example_build.py) shows the mechanics, not a storyboard):
   ```python
   sys.path.insert(0, '<this skill>/scripts')
   from paper_grid import Reel
   reel = Reel('<run>/work/grid-v01', camera='<run>/assets/camera.mp4', total=1314)
   ```
   `compile()` writes the HyperFrames folder and checks the timeline script.
4. Look before rendering: `python3 scripts/snap.py <comp> <out> 0,40,120` for stills.
5. Render with `.favstash-studio/runtime/node_modules/.bin/hyperframes render <comp> --fps 30 --quality high --output <raw>.mp4`,
   then `scripts/fix-frame0.sh <raw> <visual>.mp4` if frame 0 came out black.
6. Assemble dialogue, captions and sound in your editor or with FFmpeg, and review
   with `edit-video`.

## Sound map (`edit-video`'s SFX pack)

| Visible event | Cue |
|---|---|
| Frame 1 | `curated/hook-impact.wav` |
| Split ↔ full camera | `curated/camera-shutter.wav`; the light shutter for a smaller change |
| Re-hook build | `curated/metallic-riser.wav`, resolving on the reveal |
| Card, chip or pill arrival | `curated/ui-pop.wav` (merge arrivals under ~6 frames apart) |
| Toggle, highlight, button press | `curated/ui-click.wav` |
| Expand, shrink, fly-away | `curated/zoom-swish.wav` |
| Typed text | `typing-tick.wav`, one cue per ~0.9s of typing |
| Earned approval | `clean-ding.wav`, once |

## Pitfalls already paid for

- Anything that enters later must start hidden (`opacity:0`), or it shows before its cue.
- Put initial state in `gsap.set`; a `tl.set` at 0 alone can revert on seek.
- A `<video>` given only a width renders at the file's pixel height and letterboxes.
  Set an explicit height with `object-fit:cover`.
- Give every component a distinct id; the library's own layers use `root`, `top`,
  `grid`, `seam`, `camFull`, `camSplit` and their `V` videos.
- Snapshots can race on seek. Trust the encoded render when they disagree.
