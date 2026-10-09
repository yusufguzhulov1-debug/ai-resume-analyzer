# HyperFrames 0.8.78 — lessons from real runs

Pin the version: `npx --yes hyperframes@0.8.78 …` (the project's package.json uses the same).

## Timeline
- The page registers `window.__timelines["main"] = tl` on a paused GSAP timeline; the root has
  `data-composition-id="main"`, `data-start="0"` and `data-duration` = project duration.
- Every scene is a `<section class="clip" data-start data-duration data-track-index>`. Its
  times come from beat tokens. Overlap neighbours by ~0.1-0.3 s for the transition.
- **Every `fromTo` whose from-state is visible needs `immediateRender: false`** — shakes,
  punches, flashes, glow pulses, button squashes and **tap rings**. Without it the from-state
  is painted at t=0 (a tap ring showed in frame one).
- A property in the from-vars but not in the to-vars animates BACK to its CSS value. Put it in
  both (a slide-in screen with `opacity: 1` only in the from-state stayed invisible).
- A tween `ease` can be a plain function of progress. HyperFrames 0.8.78 accepts it: `check`
  reports 0 errors, snapshots repeat exactly and two draft renders gave identical frame hashes.
  The springs in `motion.js` rely on this (`references/motion.md`).
- `build.py` fails when an inline script uses `Math.random`, `Date.now`, a timer or
  `requestAnimationFrame`: a frame must depend only on `t`, or two renders differ.
- Hide an element after it leaves with a short `tl.to(…, {opacity: 0, duration: 0.02})`, not
  `tl.set`; the earlier reels used this pattern for every visibility change.

## Look
- Between two phone screens use a **slide, not a crossfade**: a crossfade shows both screens
  at half opacity (double exposure).
- Fade out screens that slide away, or their edge shows at the next scene start.
- Full-screen **linear** gradients band in the H.264 output: use radial gradients.
- Contrast: `check` measures text on its real background. Bright radial centres and flash
  peaks fail it — darken chip text, darken the centre colour, lower the flash peak (≤ 0.6).
- Images on a flat coloured background need real alpha. A flood-fill to cut out an icon leaks
  into light areas of the icon: put the full icon on a rounded tile instead.

## Files
- The source is `src.html.tmpl`, never a `.html` file: HyperFrames opens every `.html` in the
  folder. build.py writes `index.html`.
- Fonts: a local `.woff2` in `assets/fonts/` with an `@font-face`. No web font CDNs.
- Audio: `<audio>` with `data-start`, `data-duration`, `data-track-index` (music 20, SFX 21+),
  `data-volume`. build.py allocates SFX tracks so two sounds never share a track at once.

## Check, snapshot, render
- `check` must end with 0 errors. Expected and safe to keep: 7 lint warnings
  (`composition_file_too_large`, `nested_structure_needs_subcomposition` for each scene — the
  single-file template is deliberate) and "info" items at transition times (overlap, overflow
  of an element that is sliding out).
- `snapshot --at t1,t2,… --describe false --no-end -o snapshots/rN` — always a new folder per
  round (the shell may refuse a recursive delete of old snapshots).
- Verify on frames from the **final MP4** (finish.py contact sheet), not only on snapshots.
- `render -o renders/raw.mp4 -q delivery --quiet`. Then finish.py.
- Motion blur: `render -o renders/sub240.mp4 -q delivery --fps 240 --quiet`, then `scripts/blur.py`
  writes `renders/raw.mp4` (`references/pipeline.md`, step 5).

## Off-page text and the contrast check
`hyperframes check` measures the text of a clipped, off-page element (a screen parked at
`x: 760` inside an `overflow: hidden` frame) against the page behind it, and the contrast gate
fails. Keep an element that waits off the page at `opacity: 0` (`gsap.set(el, {x: 760, opacity: 0})`),
and fade it to 0 again right after it slides out (`tl.to(el, {opacity: 0, duration: 0.02}, t)`).
Keep backup copies of `index.html` outside the project folder: a second root composition makes
`check` report `multiple_root_compositions` and a bogus "0/0" contrast result.
