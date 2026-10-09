#!/usr/bin/env python3
"""Generate music beds with ACE-Step 1.5 (turbo model, no language model), one seed at a time.

Runs with ACE-Step's own Python, not this repo's venv (ACE-Step pins its own torch):
    $ACESTEP_DIR/.venv/bin/python music_gen_ace.py --prompt "..." --bpm 120 --duration 30 \\
        --seeds 5,17,23 --out work/ [--device auto|cpu|cuda]
ACESTEP_DIR is the ACE-Step 1.5 clone (github.com/ace-step/ACE-Step-1.5, MIT code and weights; its
model card says the output can be used for commercial purposes. Read it before you publish).

ACE-Step writes a whole song inside the length it is given, ending included, so each seed is made
EXTRA seconds longer than --duration and the ending falls after the reel; make_bed.py cuts it.

Every hard failure (no ACE-Step, a model that cannot load or generate, a file that cannot be
written) stops the run with exit 2. The GPU running out of memory exits 3: run the same command
again with --device cpu. A seed whose output is shorter than --duration gets no file; the other
seeds still run, and the run exits 2 at the end naming it. Only one music generator runs at a time
(the lock of music_gen.py): a second one exits 2.

Writes <out>/bgm_<seed>.wav for each seed.
"""
import argparse
import fcntl
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import media_duration  # noqa: E402

MODEL = "acestep-v15-turbo"
EXTRA = 10.0  # seconds past the reel: measured, the song's ending then falls after it
# the same path as music_gen.py's LOCK (the two scripts run in different venvs, so it is repeated
# here): one music generator at a time, whichever it is
LOCK = Path(tempfile.gettempdir()) / f"app-promo-reel-music-gen-{os.getuid()}.lock"
OOM_HINT = ("not enough GPU memory: run again with --device cpu (about 85 s per seed on a 32-thread "
            "CPU, 15 GB RAM)")


def fail(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def is_oom(err):
    """CUDA out of memory, as an exception (torch's OutOfMemoryError, or a RuntimeError that says
    so) or as the error text ACE-Step returns in a failed result."""
    return type(err).__name__ == "OutOfMemoryError" or "out of memory" in str(err).lower()


def stop(err, msg):
    """Exit 3 when `err` is the GPU running out of memory (the caller can retry on the CPU), else
    exit 2 with `msg`."""
    if is_oom(err):
        fail(OOM_HINT, 3)
    fail(msg)


def partial_path(out, seed):
    """Where a seed is written before its final rename: outside the bgm_*.wav pattern that
    music_rank.py is given, so an interrupted write can never be ranked."""
    return Path(out) / f".partial-{seed}.wav"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True, help="genre and instrument words; the tempo is --bpm")
    ap.add_argument("--bpm", type=int, required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--seeds", required=True, help="comma-separated integers")
    ap.add_argument("--out", required=True)
    ap.add_argument("--beats-per-bar", type=int, default=4, choices=(2, 3, 4, 6))
    ap.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    a = ap.parse_args(argv)
    if not 30 <= a.bpm <= 300:
        fail(f"--bpm must be from 30 to 300, got {a.bpm}")
    if not 0 < a.duration <= 600 - EXTRA:  # also NaN
        fail(f"--duration must be above 0 and at most {600 - EXTRA:g} s (ACE-Step makes up to 600 s)")
    try:
        seeds = [int(s) for s in a.seeds.split(",")]
    except ValueError:
        fail(f"--seeds must be comma-separated integers, got {a.seeds!r}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # the lock comes first: a second process must never touch the files of a running one
    try:
        lock = open(LOCK, "a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fail(f"another music generator is running (lock {LOCK}); run one at a time")
    except OSError as e:
        fail(f"cannot use the lock file {LOCK}: {e}")
    # an old bgm_<seed>.wav from an earlier run must not survive a failure and get ranked
    for seed in seeds:
        (out / f"bgm_{seed}.wav").unlink(missing_ok=True)

    ace = os.environ.get("ACESTEP_DIR")
    if not ace or not Path(ace).is_dir():
        fail("ACESTEP_DIR is not set to the ACE-Step 1.5 clone: git clone "
             "https://github.com/ace-step/ACE-Step-1.5 && cd ACE-Step-1.5 && uv sync, then export "
             "ACESTEP_DIR=<that folder> (see README)")
    sys.path.insert(0, ace)
    try:
        from acestep.handler import AceStepHandler
        from acestep.inference import GenerationConfig, GenerationParams, generate_music
    except ImportError as e:
        fail(f"cannot import ACE-Step from {ace} ({e}); run this script with $ACESTEP_DIR/.venv/bin/python")

    try:
        handler = AceStepHandler()
        msg, ok = handler.initialize_service(project_root=ace, config_path=MODEL, device=a.device)
    except Exception as e:  # download, cache, device: whatever ACE-Step raises
        stop(e, f"cannot load {MODEL} ({type(e).__name__}: {e})")
    if not ok:
        stop(msg, f"cannot load {MODEL}: {msg}")

    short = []
    for seed in seeds:
        work = Path(tempfile.mkdtemp(prefix=".ace-", dir=out))
        try:
            params = GenerationParams(
                task_type="text2music", caption=a.prompt, lyrics="[Instrumental]", instrumental=True,
                bpm=a.bpm, duration=a.duration + EXTRA, timesignature=str(a.beats_per_bar), seed=seed,
                thinking=False, use_cot_caption=False, use_cot_metas=False, use_cot_language=False)
            config = GenerationConfig(batch_size=1, audio_format="wav", use_random_seed=False, seeds=[seed])
            try:
                result = generate_music(handler, None, params, config, save_dir=str(work))
            except Exception as e:
                stop(e, f"generation failed on seed {seed} ({type(e).__name__}: {e})")
            if not result.success:
                stop(result.error, f"generation failed on seed {seed}: {result.error}")
            if not result.audios or not result.audios[0].get("path"):
                fail(f"generation on seed {seed} returned no audio file")
            src = Path(result.audios[0]["path"])
            length = media_duration(src)
            if length < a.duration:
                print(f"error: seed {seed} came out {length:.2f}s, shorter than {a.duration:g}s; no file written",
                      file=sys.stderr)
                short.append(seed)
                continue
            dest = out / f"bgm_{seed}.wav"
            tmp = partial_path(out, seed)
            try:
                shutil.copyfile(src, tmp)
                os.replace(tmp, dest)
            except OSError as e:
                tmp.unlink(missing_ok=True)
                fail(f"cannot write {dest} ({e})")
            print(f"seed {seed}: {dest} ({length:.2f}s)", flush=True)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    if short:
        fail(f"seed(s) {', '.join(map(str, short))} came out shorter than {a.duration:g}s and have no file")


if __name__ == "__main__":
    main()
