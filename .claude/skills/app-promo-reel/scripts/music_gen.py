#!/usr/bin/env python3
"""Generate music beds with facebook/musicgen-small (fp16, CUDA), one seed at a time.

The model weights are published under CC-BY-NC 4.0. Read that licence before you publish a
video that uses the output. This script makes no claim about what it permits.

Every hard failure (no torch/CUDA, CUDA out of memory, a model that cannot load or generate, a
file that cannot be written, a duration the model cannot make) stops the run with exit 2. A
seed whose output is shorter than asked gets no file; the other seeds still run, and the run
exits 2 at the end naming it. No broken seed can ever be ranked. Only one music_gen.py runs at
a time (GPU memory): a second one exits 2.

Usage: music_gen.py --prompt "..." --duration 30 --seeds 5,17,23 --out work/
Writes <out>/bgm_<seed>.wav for each seed.
"""
import argparse
import fcntl
import os
import sys
import tempfile
from pathlib import Path

MODEL = "facebook/musicgen-small"
FRAME_RATE = 50          # musicgen audio tokens per second
HEADROOM = 1.2           # extra seconds generated past the video length
MAX_TOKENS = 1560        # the longest generation this script accepts (31.2 s)
LOCK = Path(tempfile.gettempdir()) / f"app-promo-reel-music-gen-{os.getuid()}.lock"


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def partial_path(out, seed):
    """Where a seed is written before its final rename: outside the bgm_*.wav pattern that
    music_rank.py is given, so an interrupted write can never be ranked."""
    return Path(out) / f".partial-{seed}.wav"


def tokens_for(duration):
    n = int(round((duration + HEADROOM) * FRAME_RATE))
    if duration <= 0 or n > MAX_TOKENS:
        fail(f"duration {duration:g}s is not possible: musicgen-small here makes at most "
             f"{MAX_TOKENS / FRAME_RATE - HEADROOM:g}s")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--seeds", required=True, help="comma-separated integers")
    ap.add_argument("--out", required=True)
    ap.add_argument("--guidance", type=float, default=3.5)
    a = ap.parse_args(argv)
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
        fail(f"another music_gen.py is running (lock {LOCK}); run one at a time")
    except OSError as e:
        fail(f"cannot use the lock file {LOCK}: {e}")
    # an old bgm_<seed>.wav from an earlier run must not survive a failure and get ranked
    for seed in seeds:
        (out / f"bgm_{seed}.wav").unlink(missing_ok=True)
    max_new = tokens_for(a.duration)

    try:
        import soundfile as sf
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except ImportError as e:
        fail(f"{e.name} is not installed: pip install -r requirements-gen.txt and a CUDA build "
             f"of torch (see README)")
    if not torch.cuda.is_available():
        fail("CUDA is not available; musicgen generation needs an NVIDIA GPU")

    try:
        proc = AutoProcessor.from_pretrained(MODEL)
        model = MusicgenForConditionalGeneration.from_pretrained(MODEL, torch_dtype=torch.float16).to("cuda")
    except torch.cuda.OutOfMemoryError:
        fail("CUDA out of memory while loading the model")
    except Exception as e:  # download, cache, auth: whatever the hub raises
        fail(f"cannot load {MODEL} ({type(e).__name__}: {e}); check the network and the Hugging Face cache")
    sr = model.config.audio_encoder.sampling_rate
    short = []
    for seed in seeds:
        try:
            torch.manual_seed(seed)  # seeds CUDA too: a broken CUDA setup can fail here
            inp = proc(text=[a.prompt], padding=True, return_tensors="pt").to("cuda")
            audio = model.generate(**inp, do_sample=True, guidance_scale=a.guidance, max_new_tokens=max_new)
            y = audio[0, 0].float().cpu().numpy()
        except torch.cuda.OutOfMemoryError:
            fail(f"CUDA out of memory on seed {seed}")
        except Exception as e:
            fail(f"generation failed on seed {seed} ({type(e).__name__}: {e})")
        length = len(y) / sr
        if length < a.duration:
            print(f"error: seed {seed} came out {length:.2f}s, shorter than {a.duration:g}s; no file written",
                  file=sys.stderr)
            short.append(seed)
            continue
        dest = out / f"bgm_{seed}.wav"
        tmp = partial_path(out, seed)
        try:
            sf.write(tmp, y, sr)
            os.replace(tmp, dest)
        except Exception as e:
            tmp.unlink(missing_ok=True)
            fail(f"cannot write {dest} ({type(e).__name__}: {e})")
        print(f"seed {seed}: {dest} ({length:.2f}s)", flush=True)
    if short:
        fail(f"seed(s) {', '.join(map(str, short))} came out shorter than {a.duration:g}s and have no file")


if __name__ == "__main__":
    main()
