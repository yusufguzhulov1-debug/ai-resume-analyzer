# Critique file — `reviews/critique-<N>.md`

Each critique round writes one file in the project folder, then runs
`critique_check.py <project>` before it fixes anything. Judge only the rendered frames. Do not
describe what you intended.

## Format

```
scores: hook=8 readability=7 motion=8 variety=8 composition=8 claims=9 sound=8

- t=12.4 evidence=reviews/still-12.4.jpg fix=src.html.tmpl: hold the CTA 0.4 s longer
```

- One `scores:` line with seven `name=score` pairs. A score is a whole number from 1 to 10.
  The names are `hook`, `readability`, `motion`, `variety`, `composition`, `claims`, and a seventh:
  `sound` for a 9:16 or 4:5 reel, `loop` for a silent 16:9 hero.
- Then 0 to 3 defects, the worst ones, one line each: `- t=<seconds> evidence=<path> fix=<file>: <change>`.
  - `t` is a time in the video that has a frame: from 0 to `duration - 1/fps`.
  - `evidence` is one image file in the project folder that shows the defect (not a folder).
  - `fix` is the file that controls it, then a colon and the change. The file is in the project
    folder (`src.html.tmpl`, `cues.json`) or a script of the skill (`make_bed.py`).
- No defect is valid only when every score is 8 or more. That is the "stop" exit of the critique.
  A score below 8 needs at least one defect.
- Other lines (a heading, a note) are ignored. A line that starts with `-` must be a defect.
- A path may not leave the project folder by `..` or by a symlink.

## Scores with a fixed rule

- **readability**: a text or a tap outside the feed safe box on a settled frame, or a text under the
  format's minimum size (`references/storyboard.md`, "Feed safe zones"), caps readability at 6.
  Read the 270 px contact sheet first, then the stills at full size.
- **motion**: read each `still for …` warning from finish.py, as you read the pops. The check
  measures the whole frame, so a background pulse counts as motion: also look for a foreground
  that does not move.

## Evidence stills

A still from the real render, at time `t`, picks the frame by its number (the same way finish.py
does), so it is the frame the viewer gets:

```bash
mkdir -p reviews
ffmpeg -nostdin -v error -y -i renders/<app>-<variant>-v<N>.mp4 \
  -vf "select=eq(n\,$(python3 -c 'print(round(12.4*30))'))" -fps_mode passthrough -frames:v 1 reviews/still-12.4.jpg
```

Use the project fps in place of 30. The contact sheet (`…-sheet.jpg`) and the poster
(`…-poster.jpg`) in `renders/` are also valid evidence. A snapshot from `hyperframes snapshot` is
too, but it shows the preview, not the render: prefer the MP4.

On a blurred reel (`scripts/blur.py`), take a still at each `fastest:` time it printed. The line
names the frames with the most local change, one per move, not proven copies. Separate copies of
one object in a still are a **motion** defect: slow the move (`references/motion.md`, "Motion blur"),
or render without blur.

## What the check proves

`critique_check.py` checks form: the scores exist and are whole numbers, each defect has a time with
a frame, an image that exists and a file to fix. It does not judge whether the scores are right.
The scores come from looking at the frames.
