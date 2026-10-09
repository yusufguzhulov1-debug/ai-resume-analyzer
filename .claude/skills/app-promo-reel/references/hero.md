# 16:9 hero loop

A web hero is a silent video that plays by itself, on repeat, behind or beside a headline.
`--format 16:9` makes one: 1920x1080, 8 s by default (4 s minimum), no music, no sound effect, no
beat grid, no `cues.json`.

## What changes from the 9:16 reel

- **No sound.** `build.py` stops (exit 2) on cues, on an `<audio>` or `<video>` tag, and on a beat
  token (`D`, `E`, `BEATS` …). `finish.py` strips audio with `-an` and fails if the final file has an
  audio stream. There is no loudness, A/V or sync check.
- **Its own template** (`template/hero.html.tmpl`): one section at t=0, a phone, a headline card,
  and all motion as GSAP tweens timed with `{{calc DURATION*x}}`. Fill `CONFIG` as for a reel.
- The AI-generated label stays on screen, as in every video this skill makes.

## The loop contract

Every animated property returns to its value at t=0. The last 5 % of the loop (at most 0.4 s) is a
rest window with no motion: the phone, the card and the glow are back at their start pose.

- A `fromTo` whose from-pose differs from the t=0 pose needs `immediateRender: false`, or the
  start pose shows at t=0 and the loop opens on the wrong frame.
- An element that waits off the page stays at `opacity: 0` (see `hyperframes-gotchas.md`).
- Do not use a CSS `transform` on an element whose x is tweened by GSAP: the linter forbids it.
- The template does not hard-code a duration: slides are placed at 36 % and 64 % of it.

## Check and finish

```bash
$PY $S/build.py $P
cd $P && npx --yes hyperframes@0.8.78 check
npx --yes hyperframes@0.8.78 render -o renders/raw.mp4 -q delivery --quiet
$PY $S/finish.py $P renders/raw.mp4
```

`finish.py` decodes the whole clip (gray, 480 px wide) and measures the step from the last frame to
the first, the **seam**, against the 3 steps before it and the 3 after it (the rest window):

| Term | Meaning | Fails when |
| --- | --- | --- |
| `mad` | mean change, in gray levels | above `max(0.6, 3 x` the largest rest step`)` |
| `moved` | share of pixels that change by more than 16 levels | above `max(0.002, 3 x` the largest rest step`)` |

`moved` sees shapes (a phone shifted by 1 px, a 1.5 degree tilt: both measured). `mad` sees soft light
(a glow that ends 15 % larger and 60 px away is caught; 8 % and 30 px was not caught).

A bad seam, a clip with fewer than 8 frames, a decode that fails, or a frame count
that is not `duration x fps` (one frame more or less is a hitch at the seam) all go into the report
`problems` and the exit code is 1. The report has a `seam` block with the numbers.

A loop that passes can still be dull. Play the clip twice in a row (a doubled strip of frames
around the seam) and look at it before you deliver.

## On a web page

```html
<video autoplay loop muted playsinline src="hero.mp4"></video>
```

`muted` and `playsinline` are what let browsers start it by themselves. Nothing is uploaded by this
skill: hosting the file is yours to do.
