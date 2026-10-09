#!/usr/bin/env python3
"""Pre-publish duplicate check: does a reel look like something the account already shared?

Approximates Instagram's "looks like something you shared before" hold with Meta's open-source
PDQ frame hash plus an audio landmark fingerprint. Calibrate thresholds against real outcomes
(see ../references/duplicate-check.md); this is a local predictor, not Meta's matcher.

  dupe_check.py hash  <file-or-https-url> [...]            cache fingerprints
  dupe_check.py compare <candidate> <reference> [...]      score one file against earlier posts
  dupe_check.py batch <manifest.json> [--out report.json]  score a whole calendar

Manifest: {"posts": [{"key": "W1-B", "media": "<path|url>", "at": "<ISO time>",
           "group": "W1", "outcome": "held|passed|null"}]}. Each post is compared with every
post that published (or is queued) before it.

Requires ffmpeg, numpy, scipy, pdqhash (pip install pdqhash).
"""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

import numpy as np

FPS = 3                  # sampled video frames per second
W, H = 180, 320          # PDQ input size (hash is size-invariant)
PDQ_MATCH = 31           # Meta's recommended PDQ same-image distance
MIN_QUALITY = 50         # skip flat/black frames PDQ can't hash reliably
SR = 8000                # audio sample rate for the fingerprint
CACHE = Path(os.environ.get("DUPE_CHECK_CACHE", Path.home() / ".cache" / "dupe-check"))

# Verdict bands on the video match fraction (references/duplicate-check.md has the calibration).
# Held variants scored 0.78-0.97; a whole-frame 8% punch-in + grade scored 0.00 and passed.
# Audio alone did not cause a hold, so it is reported but does not set the verdict.
HOLD_AT = 0.55
CLEAR_BELOW = 0.10       # the 0.10-0.55 band is untested: treat BORDERLINE as "fix before posting"


def _key(src):
    # A local file re-encoded in place must not reuse its old fingerprint, so size and mtime are in the key.
    tag = src
    if os.path.exists(src):
        st = os.stat(src)
        tag = f"{src}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.sha1(tag.encode()).hexdigest()[:16]


def _frames(src):
    import pdqhash
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={FPS},scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    hashes, keep = [], []
    for i, f in enumerate(frames):
        h, q = pdqhash.compute(np.ascontiguousarray(f))
        if q >= MIN_QUALITY:
            hashes.append(np.packbits(h.astype(np.uint8)))
            keep.append(i / FPS)
    return np.array(hashes, np.uint8).reshape(-1, 32), np.array(keep)


def _audio(src):
    from scipy.signal import stft
    from scipy.ndimage import maximum_filter
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
    if x.size < SR:
        return np.zeros((0, 2), np.int64)
    f, t, Z = stft(x, SR, nperseg=1024, noverlap=768)
    S = np.log1p(np.abs(Z))
    # fold to log-frequency bins (12/octave, 100 Hz-3.2 kHz): small pitch shifts and EQ stay in-bin
    edges = 100 * 2 ** (np.arange(0, 61) / 12)
    idx = np.digitize(f, edges) - 1
    L = np.stack([S[idx == b].max(0) if (idx == b).any() else np.zeros(S.shape[1]) for b in range(60)])
    peaks = (L == maximum_filter(L, size=(5, 9))) & (L > np.percentile(L, 90))
    fb, tb = np.nonzero(peaks)
    order = np.argsort(tb); fb, tb = fb[order], tb[order]
    dt = t[1] - t[0]
    out = []
    for i in range(len(tb)):  # pair each peak with the next few peaks: (f1, f2, gap) landmark
        for j in range(i + 1, min(i + 6, len(tb))):
            gap = tb[j] - tb[i]
            if 1 <= gap <= 40:
                out.append(((fb[i] * 60 + fb[j]) * 64 + gap // 2, round(tb[i] * dt * 2)))
    return np.array(out, np.int64).reshape(-1, 2)


def fingerprint(src):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{_key(src)}.npz"
    if p.exists():
        d = np.load(p)
        return {"v": d["v"], "vt": d["vt"], "a": d["a"], "dur": float(d["dur"])}
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", src], capture_output=True, text=True).stdout or 0)
    v, vt = _frames(src)
    a = _audio(src)
    np.savez_compressed(p, v=v, vt=vt, a=a, dur=dur)
    return {"v": v, "vt": vt, "a": a, "dur": dur}


_POP = np.array([bin(i).count("1") for i in range(256)], np.uint8)


def video_score(c, r):
    """Fraction of candidate frames with a near-identical frame anywhere in the reference."""
    if len(c["v"]) == 0 or len(r["v"]) == 0:
        return 0.0, None, 0.0
    d = _POP[c["v"][:, None, :] ^ r["v"][None, :, :]].sum(-1)  # hamming, cand x ref
    best = d.min(1)
    hit = best <= PDQ_MATCH
    run = longest = 0
    for h in hit:  # longest matched stretch in candidate time
        run = run + 1 if h else 0
        longest = max(longest, run)
    return float(hit.mean()), float(np.median(best)), longest / FPS


def audio_score(c, r):
    """Share of candidate landmarks found in the reference at one consistent time offset."""
    if len(c["a"]) == 0 or len(r["a"]) == 0:
        return 0.0
    ref = {}
    for h, t in r["a"]:
        ref.setdefault(int(h), []).append(int(t))
    offs = []
    for h, t in c["a"]:
        for rt in ref.get(int(h), ()):
            offs.append(rt - int(t))
    if not offs:
        return 0.0
    hist = np.bincount(np.array(offs) - min(offs))
    win = np.convolve(hist, np.ones(3, int), "same")  # tolerate small speed drift
    return float(win.max() / len(c["a"]))


def verdict(v):
    return "LIKELY HELD" if v >= HOLD_AT else ("BORDERLINE" if v >= CLEAR_BELOW else "LIKELY CLEAR")


def compare(cand, refs):
    c = fingerprint(cand)
    rows = []
    for ref in refs:
        r = fingerprint(ref)
        v, med, run = video_score(c, r)
        rows.append({"reference": ref, "video": round(v, 3), "medianPdq": med,
                     "longestMatchS": round(run, 1), "audio": round(audio_score(c, r), 3)})
    rows.sort(key=lambda x: (-x["video"], -x["audio"]))
    top = rows[0] if rows else {"video": 0}
    return {"candidate": cand, "verdict": verdict(top["video"]), "worst": top, "all": rows}


def batch(manifest, out):
    posts = sorted(json.load(open(manifest))["posts"], key=lambda p: p["at"])
    report = []
    for i, p in enumerate(posts):
        print(f"[{i+1}/{len(posts)}] {p['key']}", file=sys.stderr)
        fingerprint(p["media"])
    for i, p in enumerate(posts):
        earlier = posts[:i]
        res = compare(p["media"], [e["media"] for e in earlier]) if earlier else {"verdict": "FIRST", "worst": None, "all": []}
        by_media = {e["media"]: e["key"] for e in earlier}
        for row in res["all"]:
            row["reference"] = by_media[row["reference"]]
        report.append({"key": p["key"], "group": p.get("group"), "at": p["at"], "outcome": p.get("outcome"),
                       "verdict": res["verdict"], "worst": res["worst"], "top3": res["all"][:3]})
    if out:
        json.dump(report, open(out, "w"), indent=1)
    for r in report:
        w = r["worst"] or {}
        print(f"{r['key']:<34} {r['verdict']:<13} video {w.get('video', 0):.2f} audio {w.get('audio', 0):.2f} "
              f"run {w.get('longestMatchS', 0):>5}s vs {w.get('reference', '-'):<28} actual={r['outcome'] or '?'}")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hash"); h.add_argument("src", nargs="+")
    c = sub.add_parser("compare"); c.add_argument("candidate"); c.add_argument("refs", nargs="+")
    b = sub.add_parser("batch"); b.add_argument("manifest"); b.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "hash":
        for s in a.src:
            f = fingerprint(s); print(f"{s}: {len(f['v'])} frames, {len(f['a'])} landmarks")
    elif a.cmd == "compare":
        print(json.dumps(compare(a.candidate, a.refs), indent=1))
    else:
        batch(a.manifest, a.out)


if __name__ == "__main__":
    main()
