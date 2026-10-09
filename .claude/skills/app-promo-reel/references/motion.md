# Motion language

A reel feels precise when each kind of object always moves the same way. If every element
overshoots, nothing feels precise. The classes live in `<project>/motion.js` (copied from
`template/motion.js` by `new_project.py`, built into the page by the `{{MOTION}}` token). Edit
the values there, not in the timeline.

| Class | Used for | Ease | Duration |
|---|---|---|---|
| `micro` | small in-place responses (a button squash, a toggle) | spring, 6% overshoot | 0.18 s |
| `panel` | big surfaces: the phone, the hero chip, a card | spring, 7% overshoot | 0.55 s |
| `headline` | captions and taglines | spring, 13% overshoot | 0.35 s, then hold 1.0 s |
| `icon` | small objects that appear: icon, pop, CTA, chips, rows | spring, 10% overshoot | 0.32 s |
| `camera` | drift and push-in of a whole scene | `sine.inOut` (drift), `power2.inOut` (move) | set by the scene |

Why these values: a big object that bounces a lot looks cheap, so `panel` is nearly flat. A
small object can bounce a little more (`icon`). A headline needs a clear landing, then
a hold so it can be read: the words stay put while something else moves
(`references/storyboard.md`, "Density"). The camera never uses a spring: a spring on the camera reads as a
shake.

## Rules
- Use the class ease: `ease: MOTION.panel.ease`. A tween keeps its own `duration` and start
  time; the template overrides some class durations on purpose (`#phone` is 0.7 s). The class
  fixes the feel, the scene fixes the timing.
- An object that **enters** uses its entrance class (`icon` for a pop, `panel` for a screen).
  An object that **responds in place** uses `micro`.
- `shake` and `flash` are the loudest effects: at most 2 shakes and 2 flashes per reel, best on the
  drop and the end card (the template has one of each in s3 and in s6). Give the other beats a
  `punch`. `build.py` prints a warning when the page calls either more than 2 times.
- At most one class overshoots hard at a time. When a `headline` and an `icon` land on the
  same beat, give the beat to one and delay or soften the other.
- Do not use `back.out(...)` in a scene. If an element truly needs it, put a
  `// motion-exception: <reason>` comment on that line.
- A spring is trimmed so it starts at 0 and ends at exactly 1: the tween always lands on its
  target. The overshoot argument must be between 0 and 0.35; `spring(0)` is a critically
  damped ease with no overshoot.
- The 16:9 hero loop uses no spring. It must start and end at rest (`references/hero.md`).

## Seekable frames
A frame must depend only on the time `t`: `frame = render(t)`. Then a seek, a re-render and a
snapshot all show the same picture. `build.py` fails (exit 2) when an inline script of the page
uses a hidden clock or a random value: `Math.random`, `Date.now`, `Date(` / `new Date`,
`performance.now`, `setTimeout`, `setInterval`, `requestAnimationFrame`,
`crypto.getRandomValues`, `crypto.randomUUID`. Comments, strings and template text are not
read. Scripts with a `src` and inline event-handler attributes are not read.

If you need variation, write it as a constant (a seeded list in the file), or derive it from
`t` with `Math.sin`. Check a built page again with `build.py <project>`.

## Motion blur
Optional, for 9:16 and 4:5 reels with fast moves: render at 240 fps and let `scripts/blur.py` make
the project-fps video (commands in `references/pipeline.md`, step 5). It costs about 2.5 minutes for
a 30 s reel instead of about 25 s.
- Each output frame averages the input frames within a third of a frame of its time: 5 of 8 at
  30 fps (about 225° of shutter), 3 of 4 at 60 fps. The window is centred on the frame time.
- No blur across a cut. A step between two input frames 2.5 times the steps around it (or more) is
  a cut, and the frame keeps only the side of its own time. That catches hard cuts, slams on a frame
  time, and the in and out steps of a one-frame flash (that frame gets less blur). An instant change
  in the gap between two windows (more than a third of a frame from both frame times) is in no
  window and needs no cut. A change inside a window that is too small for the cut rule blends on
  that one frame. A cut under a fast move can be too small too: the frame shows a ghost of the old
  scene, and blur.py names that frame on its `fastest:` line.
- Copies: the samples of a frame sit one input frame apart. A move faster than about 10 × K px per
  output frame (K input frames per output frame: 80 px at 30 fps, 40 px at 60 fps) shows separate
  copies instead of a smear. The stock s2 exit whip moves about 210 px per frame and shows 5 copies.
  The `fastest:` line of blur.py names the frames to look at: the frames with the most local change,
  one per move. A fade or a flash ranks high too.
- Counters and typed text: a change at a frame time falls inside that frame's window, and the frame
  blends the old and the new glyphs (a digit change is too small for the cut rule). With blur, put
  each change of a counter or typed text at a half-frame time, `(n + 0.5) / fps`: no window holds
  those input frames. Beat times are not frame times: move each change to the nearest half-frame
  time.
- Motion blur is not CSS `filter: blur()` and does not replace one: the entrance blurs of the
  template stay.
