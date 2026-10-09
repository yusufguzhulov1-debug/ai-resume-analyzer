#!/usr/bin/env python3
"""Word timings of the final voice, for the storyboard (every animation lands on a word).

Runs the local openai-whisper CLI (no API key, nothing leaves the machine) with word timestamps, then writes
assets/audio/<name>-mots.json as {"duration": s, "words": [{"w", "start", "end"}]}, the format the storyboard uses.
Usage: python3 mots.py <voice.wav> [--model medium] [--lang fr]
Run it on the EDITED voice (silences already cut), never on the raw ElevenLabs file.
"""
import json
import os
import subprocess
import sys
import tempfile


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit("usage: mots.py <voice.wav> [--model medium] [--lang fr]")
    wav = os.path.abspath(args[0])
    model = args[args.index("--model") + 1] if "--model" in args else "medium"
    lang = args[args.index("--lang") + 1] if "--lang" in args else "fr"
    out_dir = tempfile.mkdtemp(prefix="mots-")
    subprocess.run(["whisper", wav, "--model", model, "--language", lang, "--word_timestamps", "True",
                    "--output_format", "json", "--output_dir", out_dir, "--verbose", "False"], check=True)
    raw = json.load(open(os.path.join(out_dir, os.path.splitext(os.path.basename(wav))[0] + ".json")))
    words = [{"w": w["word"].strip(), "start": round(w["start"], 2), "end": round(w["end"], 2)}
             for seg in raw.get("segments", []) for w in seg.get("words", []) if w["word"].strip()]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                               capture_output=True, text=True, check=True).stdout.strip())
    out = os.path.splitext(wav)[0] + "-mots.json"
    json.dump({"duration": round(dur, 2), "words": words}, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(words)} mots, {dur:.2f} s -> {out}")
    # silences over 0.4 s: each one must become a shot with its own action in the storyboard
    gaps = [(a["end"], b["start"]) for a, b in zip(words, words[1:]) if b["start"] - a["end"] > 0.4]
    print("silences > 0,4 s : " + ", ".join(f"{a:.2f} à {b:.2f}" for a, b in gaps))


if __name__ == "__main__":
    main()
