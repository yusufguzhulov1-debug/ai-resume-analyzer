# The orchestrator layer

What the frame workers cannot do, because it spans two frames or the whole film, is added by the orchestrator on top of
the `index.html` that HeyGen's assembler rebuilds. `templates/assemble.sh` does it all, idempotently: the assembler
rewrites `index.html` from scratch on every run, and the patch is applied again.

## Why by hand

HeyGen's transition injector knows five CSS transitions (crossfade, blur-crossfade, push-slide, zoom-through, squeeze)
plus the hard cut. Its shader transitions require handing every scene to its own engine. For the two or three key
moments of a film, a hand-made layer is simpler and looks better: a light flash and an iris.

## The four pieces

1. **Audio at the root.** `<audio id="mix" data-start="0" data-duration="TOTAL" data-track-index="11">` pointing to the
   mix built by `build-audio.sh`. Frames never carry audio.
2. **Paper bed.** The video's root ground is the dark canvas. A crossfade between two light frames would pass through
   grey. A full-bleed `class="clip"` in the paper color, on track 12, lies under the whole light world (default span:
   from the flash at full white to the end of the iris).
3. **Light flash (dark world to light world, at the pivot).** A clip of 0.9 s on track 30, z-index 60: a white-hot core
   grows from the pivot object (`LEAK_X`, `LEAK_Y`), a horizontal streak and a warm sweep cross the frame, then a
   paper-colored flash covers the screen from LEAK_AT+0.15 to LEAK_AT+0.30 and fades out over 0.5 s. The cut between
   the last dark frame and the first light frame hides under it: put it at LEAK_AT+0.25, with `transition_in: cut`.
   The last dark frame should end on a bright point at the same position (a caret turning into light, a word).
4. **Iris (light world to the dark end card).** A clip of 0.95 s on track 31, z-index 61: the end card opens with
   `clip-path: circle(0% → 160%)` from the object the viewer is looking at (`IRIS_X`, `IRIS_Y`: the zero, the first
   station of a path, the button), in 0.75 s `power2.inOut`, while an accent ring with a glow grows from the same point.
   The end card starts at IRIS_AT+0.05 with `transition_in: cut`. The frame under the iris is extended to IRIS_AT+0.80
   so the light world stays visible outside the growing circle.

## Settings to decide from the storyboard

| Setting | How to pick it |
|---|---|
| `LEAK_AT` | cut between the last dark frame and the first light frame, minus 0.25 s |
| `LEAK_X`, `LEAK_Y` | where the pivot object sits at the end of the last dark frame (px, 1920 x 1080) |
| `IRIS_AT` | start of the end card minus 0.05 s |
| `IRIS_X`, `IRIS_Y` | the object the last light frame ends on |
| `PAPER` | `paper` of frame.md (empty if the film has no light world) |
| `ACCENT`, `ACCENT_LIGHT`, `ACCENT_GLOW` | the same keys in frame.md |

Leave `LEAK_AT` or `IRIS_AT` empty to skip one of them (a film on a single light ground needs neither, only the audio).

## Checks

- Snapshot at LEAK_AT+0.05, +0.2, +0.35, +0.6 and at IRIS_AT+0.1, +0.4, +0.7, +0.9: no black, no grey, the circle
  grows from the intended object.
- Black frames right after the iris: the frame under the iris has internal clips that end at its original duration.
  Extend them too (see `pitfalls.md`).
- A second, stronger transition is rarely better: 2 or 3 spectacular transitions per film at most.
