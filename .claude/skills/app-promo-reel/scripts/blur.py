#!/usr/bin/env python3
"""Motion blur: turn a 240 fps render into a blurred video at the project fps.

Optional step between the render and finish.py, for reels with fast moves. Render the project with
`--fps 240`, run this script, then run finish.py on its output (renders/raw.mp4 by default). finish.py
does not know or care that the video was blurred.

1. Inputs (each failure exits 2 and writes no file): a 9:16 or 4:5 project (a 16:9 loop's seam would
   need samples that wrap around); an input rate that is a whole multiple K >= 4 of the project fps;
   a constant-rate video that starts at 0; a frame count N that is a multiple of K; the size of the
   project's format; an audio stream (finish.py needs one).
2. Samples: output frame n averages the input frames within a third of an output frame of its time,
   c-R .. c+R with c = K*n and R = K // 3 (5 of 8 frames at K 8, about 225 degrees of shutter). The
   windows of two neighbour frames never touch, so an input frame half-way between two frame times
   is in no window.
3. Cuts: a step (mean absolute Y difference of two neighbour input frames, every 4th pixel) above
   CUT_FLOOR and above CUT_RATIO x the median of the two steps on each side is a cut. A window keeps
   only the run of frames around c that crosses no cut, so a cut, a slam or a one-frame flash is never
   blended with the picture before it.
4. Average: the Y, U and V planes summed in float32 and rounded once. No RGB round trip.
5. Encode: libx264 slow, CRF 15 (the hyperframes `-q delivery` preset). The colour tags of the input
   go on the raw frames AND on the output: with tags on the output only, ffmpeg 7 converts the colour
   matrix and the picture changes. Audio is copied. The output is written as <out stem>.partial.mp4
   and renamed only when the encoder succeeded and the result has N / K frames and an audio stream;
   on any failure (also Ctrl-C) the partial file is removed and an old output stays as it was.

Report (stdout): the sample count, `cuts:` (the times of the windows a cut made shorter) and
`fastest:` (up to 6 times, one per move, of the frames with the largest local change inside their
window: 64 x 64 px cells, so a small fast object counts). Very fast moves show separate copies, one
input frame apart; the critique looks at these times in the MP4. A fade or a flash ranks high too.

Usage: blur.py <project_dir> <render_240fps.mp4> [-o renders/raw.mp4]
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import die, is_silent, load_project  # noqa: E402

MIN_K = 4            # fewer input frames per output frame cannot blur and still leave a gap
CUT_FLOOR = 1.0      # gray levels
CUT_RATIO = 2.5      # measured 2026-10-07 on a 30 s reel: smooth motion up to 1.7 x its neighbours, a move that
                     # starts or stops at rest 2 x (by construction), cuts 2.7-56 x (2.7 and 3.0 over a moving
                     # background). A missed cut leaves a ghost of the old scene; an extra cut only less blur.
STRIDE = 4           # steps and scores read every 4th pixel of Y in each direction
CELL = 16            # fastest: cells of 16 x 16 sampled pixels (64 x 64 px); only full cells count
FAST_MIN = 2.0       # gray levels: a frame below this did not move
FAST_MAX, FAST_GAP = 6, 0.5
RATE_TOL = 1e-4      # 240000/1001 over a project fps of 29.97 is 8.0000027
START_TOL = 0.001
X264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "15", "-profile:v", "high", "-pix_fmt", "yuv420p"]
# ffprobe field -> ffmpeg option, for the four colour tags
TAGS = {"color_range": "-color_range", "color_space": "-colorspace", "color_primaries": "-color_primaries",
        "color_transfer": "-color_trc"}


def factor(rate, fps):
    """K, the input frames per output frame, or None when it is not a whole number of at least
    MIN_K. `rate` and `fps` may be Fractions, ints or floats."""
    k = Fraction(rate) / Fraction(fps)
    whole = round(k)
    return whole if abs(k - whole) < RATE_TOL and whole >= MIN_K else None


def reach(k):
    """R: the window is c-R .. c+R, a third of an output frame each side."""
    return k // 3


def is_cut(steps, i):
    """True when step i (input frame i to i+1) is a cut; `steps` maps an index to its step."""
    if i not in steps:
        return False
    near = [steps[j] for j in (i - 2, i - 1, i + 1, i + 2) if j in steps]
    return steps[i] > CUT_FLOOR and steps[i] > CUT_RATIO * (float(np.median(near)) if near else 0.0)


def window(c, n_frames, r, cut):
    """(lo, hi), inclusive: the frames of c-R .. c+R inside the clip, cut back to the run around c
    that crosses no cut. `cut(i)` tells whether step i -> i+1 is a cut."""
    lo = c
    while lo - 1 >= max(0, c - r) and not cut(lo - 1):
        lo -= 1
    hi = c
    while hi + 1 <= min(n_frames - 1, c + r) and not cut(hi):
        hi += 1
    return lo, hi


def average(frames):
    """The mean of equal-sized uint8 frames, summed in float32 and rounded once."""
    acc = np.zeros(frames[0].shape, np.float32)
    for f in frames:
        acc += f
    return np.rint(acc / len(frames)).astype(np.uint8)


def step_scores(a, b):
    """(whole-frame step, largest cell step) of two sampled Y planes (float32)."""
    d = np.abs(b - a)
    h, w = (d.shape[0] // CELL) * CELL, (d.shape[1] // CELL) * CELL
    local = d[:h, :w].reshape(h // CELL, CELL, w // CELL, CELL).mean(axis=(1, 3)).max() if h and w else 0.0
    return float(d.mean()), float(local)


def pick_fastest(scores, rate):
    """Output frame indices for the `fastest:` line: best score first, then each next best that is
    FAST_GAP s from every frame taken, at most FAST_MAX, only scores >= FAST_MIN; in time order."""
    taken = []
    for n in sorted((n for n, s in enumerate(scores) if s >= FAST_MIN), key=lambda n: (-scores[n], n)):
        if len(taken) == FAST_MAX:
            break
        if all(abs(n - m) / rate >= FAST_GAP for m in taken):
            taken.append(n)
    return sorted(taken)


def probe(path):
    """The video stream of `path` (rate, timing, size, packets, colour tags) and whether it has audio."""
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-show_entries",
                        "stream=codec_type,r_frame_rate,avg_frame_rate,start_time,duration,width,height,"
                        "nb_read_packets," + ",".join(TAGS), "-of", "json", str(path)],
                       capture_output=True, text=True)
    if r.returncode:
        die(f"ffprobe cannot read {path}:\n{r.stderr[-800:]}")
    streams = json.loads(r.stdout).get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        die(f"{path} has no video stream")

    def number(key):
        try:
            v = float(video.get(key))
        except (TypeError, ValueError):
            return None
        return v if math.isfinite(v) else None

    def ratio(key):
        try:
            v = Fraction(video.get(key, ""))
        except (ValueError, ZeroDivisionError):
            return None
        return v if v > 0 else None

    return {"rate": ratio("r_frame_rate"), "avg_rate": ratio("avg_frame_rate"), "start": number("start_time"),
            "duration": number("duration"), "width": video.get("width"), "height": video.get("height"),
            "frames": int(video.get("nb_read_packets") or 0),
            "tags": {k: video[k] for k in TAGS if video.get(k) not in (None, "", "unknown")},
            "audio": any(s.get("codec_type") == "audio" for s in streams)}


def decoder_cmd(src):
    return ["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"]


def encoder_cmd(src, dst, width, height, rate, tags):
    tag_args = [a for k, v in tags.items() for a in (TAGS[k], v)]
    return ["ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{width}x{height}", "-framerate", str(rate), *tag_args,
            "-i", "-", "-i", str(src), "-map", "0:v:0", "-map", "1:a:0", *X264, *tag_args,
            "-c:a", "copy", "-movflags", "+faststart", str(dst)]


def check_input(project, src):
    """K and the probe of `src`, or exit 2 with the rule that failed."""
    fmt = project["format"]
    if is_silent(fmt):
        die(f"blur is for 9:16 and 4:5 reels; a {fmt} loop would need samples that wrap around its seam")
    if not Path(src).is_file():
        die(f"{src} not found")
    info = probe(src)
    fps = project["fps"]
    k = factor(info["rate"], fps) if info["rate"] else None
    if k is None:
        die(f"{src} runs at {info['rate']} fps: the input rate must be a whole multiple (4 or more) of the "
            f"project fps ({fps:g}); render with --fps 240 for 30 fps, or with the largest multiple of the "
            f"project fps up to 240 (200 for 25 fps, 240000/1001 for 29.97)")
    n = info["frames"]
    if (info["avg_rate"] != info["rate"] or info["start"] is None or abs(info["start"]) > START_TOL
            or info["duration"] is None or abs(info["duration"] - n / info["rate"]) > 1 / info["rate"]):
        die(f"{src} is not a constant-rate video that starts at 0 (rate {info['rate']}, average "
            f"{info['avg_rate']}, start {info['start']}, duration {info['duration']}, {n} frames): the "
            f"copied audio would drift; use the HyperFrames render as it is")
    if n == 0 or n % k:
        die(f"{src} has {n} frames, which is not a whole number of output frames ({k} input frames each): "
            f"the project duration x fps is not a whole number of frames, or the render has a frame more "
            f"or less than that")
    if (info["width"], info["height"]) != (project["width"], project["height"]):
        die(f"{src} is {info['width']}x{info['height']}, but a {fmt} project is "
            f"{project['width']}x{project['height']}")
    if not info["audio"]:
        die(f"{src} has no audio stream; finish.py needs the sound of a {fmt} reel")
    return k, info


def read_frame(stream, size):
    data = stream.read(size)
    return np.frombuffer(data, np.uint8) if len(data) == size else None


def blur(project_dir, src, out=None):
    project = load_project(project_dir)
    k, info = check_input(project, src)
    w, h, n_in = project["width"], project["height"], info["frames"]
    r, n_out, rate = reach(k), n_in // k, info["rate"] / k
    size = w * h * 3 // 2
    out = Path(out) if out else Path(project_dir) / "renders" / "raw.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.stem + ".partial.mp4")
    dec = enc = None
    with tempfile.TemporaryDirectory() as tmp:
        dec_log, enc_log = open(Path(tmp) / "dec.log", "w+"), open(Path(tmp) / "enc.log", "w+")

        def tail(log):
            log.flush()
            log.seek(0)
            return log.read()[-800:]
        try:
            dec = subprocess.Popen(decoder_cmd(src), stdout=subprocess.PIPE, stderr=dec_log)
            enc = subprocess.Popen(encoder_cmd(src, partial, w, h, rate, info["tags"]), stdin=subprocess.PIPE,
                                   stderr=enc_log)
            frames, small, steps, local = {}, None, {}, {}
            loaded = 0

            def load_to(last):
                nonlocal loaded, small
                while loaded <= last:
                    f = read_frame(dec.stdout, size)
                    if f is None:
                        die(f"the decoder stopped after {loaded} of {n_in} frames:\n{tail(dec_log)}")
                    y = f[:w * h].reshape(h, w)[::STRIDE, ::STRIDE].astype(np.float32)
                    if small is not None:
                        steps[loaded - 1], local[loaded - 1] = step_scores(small, y)
                    frames[loaded], small = f, y
                    loaded += 1

            scores, cut_short = [], []
            for n in range(n_out):
                c = k * n
                load_to(min(c + r + 2, n_in - 1))
                lo, hi = window(c, n_in, r, lambda i: is_cut(steps, i))
                if hi - lo < min(n_in - 1, c + r) - max(0, c - r):
                    cut_short.append(n)
                scores.append(max((local[i] for i in range(lo, hi)), default=0.0))
                try:
                    enc.stdin.write(average([frames[i] for i in range(lo, hi + 1)]).tobytes())
                except BrokenPipeError:
                    die(f"the encoder stopped at frame {n}:\n{tail(enc_log)}")
                for i in [i for i in frames if i < c + k - r]:
                    del frames[i]
            # the last window ends before the last input frame: read the rest so the decoder can exit
            while (f := read_frame(dec.stdout, size)) is not None:
                loaded += 1
            if loaded != n_in or dec.wait() != 0:
                die(f"the decoder gave {loaded} of {n_in} frames (exit {dec.returncode}):\n{tail(dec_log)}")
            enc.stdin.close()
            if enc.wait() != 0:
                die(f"the encoder failed:\n{tail(enc_log)}")
            got = probe(partial)
            if got["frames"] != n_out or got["rate"] != rate or not got["audio"]:
                die(f"the blurred video has {got['frames']} frames at {got['rate']} fps (audio: {got['audio']}), "
                    f"expected {n_out} at {rate}")
            os.replace(partial, out)
        finally:
            for p in (dec, enc):
                if p is not None and p.poll() is None:
                    p.kill()
                    p.wait()
            for f in (dec_log, enc_log):
                f.close()
            partial.unlink(missing_ok=True)

    times = lambda ns: " ".join(f"{float(i / rate):.3f}" for i in ns) or "none"  # noqa: E731
    print(f"blur: K={k}, {2 * r + 1} of {k} input frames per output frame "
          f"(about {round(360 * (2 * r + 1) / k)} degrees), {n_out} frames, {len(cut_short)} windows cut short")
    print(f"cuts: {times(cut_short)}")
    print(f"fastest: {times(pick_fastest(scores, rate))}")
    print(f"wrote {out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("render", help="the project rendered with --fps 240")
    ap.add_argument("-o", "--out", help="output video (default: <project>/renders/raw.mp4)")
    a = ap.parse_args(argv)
    sys.exit(blur(a.project_dir, a.render, a.out))


if __name__ == "__main__":
    main()
