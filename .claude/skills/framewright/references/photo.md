# Photos as polygons

A photo never enters the HTML as pixels. `scripts/trace.py` turns it into posterized closed
polygons (a few thousand integer points), `scripts/inject.mjs` writes them between the
`PORTRAIT` markers, and the plate draws them as fills, outlines or both. The result reads as
a screen-printed or drawn likeness and animates like any other vector object.

## 1. Pipeline

```bash
bash scripts/portrait.sh photo.jpg --height 900 --levels 0.14,0.28,0.42,0.56,0.70,0.84 --blur 1.6 --minarea 36
```

`portrait.sh` runs the tracer, writes `portrait.js`, injects it, and points you at
`shots/portrait_preview.png` (posterization with contours overlaid, for eyes only).
Then shoot the portrait plate and look.

Steps inside `trace.py`:

1. Greyscale, resize to `--height` (800–900 px), autocontrast with a 0.2 % cutoff
   (a 1 % cutoff eats whole regions when they fall in the histogram tail; `--nocontrast`
   turns it off), Gaussian blur `--blur` (1.4–1.8; more blur, fewer specks).
2. Background removal: the bright connected region touching the top edge and the upper
   corners is set to black. `--bgthr` 0.86 by default; raise to 0.9 if a bald head or a
   white shirt gets eaten; `--nobg` keeps the background.
3. Thresholds from `--levels` (five or six). For faces, cluster them in 0.55–0.85 where
   skin lives; the shirt and hair fall out of the lower levels on their own.
4. Vectorized marching squares with interpolation, closure by zero padding, segment
   linking through shared edges, Douglas–Peucker with `--tol` 0.9 px at 800–900 px height,
   contours with area under `--minarea` (24–40 px²) dropped.
5. Output: `const PORTRAIT={w,h,levels:[{t,p:[[x,y,...],...]}]}` with integer coordinates.
   Typical size 30–70 KB.

Requirements: Python 3 with numpy, scipy, Pillow. No OpenCV. `portrait.sh` prefers
`./.venv/bin/python` when it exists (the doctor creates it when pip refuses system installs).

## 2. Drawing

- Fills: levels in ascending threshold order, each filled with its tone using the
  `evenodd` rule; holes (eyes, mouth) come out by themselves. Six tones from dark to light
  for a CRT look: `#0f151c #25313d #48606f #7a95a4 #b9d0dc #f3f9ff`. For risograph use two
  inks: the dark levels in blue, the mid levels in pink at 50 % density.
- Outlines: the same polygons stroked; draw only the first fraction of each polyline to
  reveal the drawing progressively.
- RGB split: draw the portrait into an offscreen canvas, make three copies multiplied by
  pure red, green and blue (`multiply`, then `destination-in` with the original), add them
  with `lighter` at offsets; converge the offsets to 1–2 units as the signal "locks".
- Slices: copy horizontal bands of the offscreen canvas with random horizontal offsets for
  a tracking glitch; decrease the amplitude over time.
- Placement: a square portrait sits with its bottom bleeding past the frame edge, so the
  shoulders do not float above black. Head top at 5–8 % from the top edge.

Sequence that reads as "a signal locking onto a face" (8 seconds): bar 1 outlines draw
themselves with strong RGB split and band tearing; bar 2 fills fade in under the outlines,
a scan beam passes top to bottom, the split converges; bar 3 a lower third slides in with the
name and a status; bar 4 a large caption on the free side, occasional small tears, then the
cut.

## 3. Tuning by symptom

| Symptom | Fix |
|---|---|
| face is one flat tone | move thresholds into 0.55–0.85, add a level at 0.78 |
| features lost in speckle | `--blur 1.8`, `--minarea 40` |
| head top or white clothes gone | `--bgthr 0.9`; if still gone, `--nobg` and crop tighter |
| background remains as a bright slab | `--bgthr 0.82`, or crop so the background touches the top edge |
| jagged outlines | `--height 900`, `--tol 0.8` |
| file too large | fewer levels, `--tol 1.2`, `--minarea 48` |
| person unrecognisable on the sheet | crop to head and shoulders; likeness lives in the silhouette, brows, mouth and hairline, not in detail |

## 4. Rights

Ask before the first render whether the person in the photo agreed to appear, and whether
the video will be public. A public repository or a shared link is publication. Without
confirmation, keep the placeholder and say so.
