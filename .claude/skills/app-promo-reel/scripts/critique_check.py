#!/usr/bin/env python3
"""Check a critique file: reviews/critique-N.md (format in references/critique.md).

Usage: critique_check.py <project_dir> [--round N]      (default: the highest N)
Exit 0: the file is well formed. Exit 1: one line per problem on stderr (or no file for the round).
It checks form, not quality: that each defect has a time that has a frame, a file that exists as
evidence and a file to fix. Whether the scores are right is for the reader of the frames.
"""
import argparse
import re
import sys
from pathlib import Path

from common import die, is_silent, load_project

SCRIPTS = Path(__file__).resolve().parent
COMMON_SCORES = ("hook", "readability", "motion", "variety", "composition", "claims")
MAX_DEFECTS = 3
STOP_SCORE = 8  # every score at or above this ends the critique: no defect is then needed
DEFECT = re.compile(r"^-\s+t=(\S+)\s+evidence=(\S+)\s+fix=([^\s:]+):\s*(\S.*)$")


def inside(path, root):
    """True when path, with `..` and symlinks resolved, is under root."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def latest_round(reviews):
    rounds = [int(m.group(1)) for p in reviews.glob("critique-*.md") if (m := re.fullmatch(r"critique-(\d+)\.md", p.name))]
    return max(rounds, default=None)


def check(project_dir, text):
    """Problems of one critique file, as [(line number or None, message)]."""
    pdir = Path(project_dir)
    project = load_project(pdir)
    last_t = project["duration"] - 1 / project["fps"]
    seventh = "loop" if is_silent(project) else "sound"
    wanted = (*COMMON_SCORES, seventh)
    problems, scores, defects = [], None, []

    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("scores:"):
            if scores is not None:
                problems.append((n, "a second scores: line"))
                continue
            scores = {}
            for part in s[len("scores:"):].split():
                name, eq, val = part.partition("=")
                if not eq or name in scores:
                    problems.append((n, f"{part!r} is not a new name=score pair"))
                elif not re.fullmatch(r"\d+", val) or not 1 <= int(val) <= 10:
                    problems.append((n, f"{name}: the score must be a whole number from 1 to 10, got {val!r}"))
                    scores[name] = None
                else:
                    scores[name] = int(val)
        elif s.startswith("-"):
            defects.append((n, s))

    if scores is None:
        problems.append((None, "no scores: line"))
    else:
        for name in scores:
            if name not in wanted:
                hint = " (a silent 16:9 project scores loop, not sound)" if name == "sound" and seventh == "loop" else \
                       " (this project scores sound, not loop)" if name == "loop" else ""
                problems.append((None, f"unknown score {name!r}{hint}"))
        for name in wanted:
            if name not in scores:
                problems.append((None, f"missing score: {name}"))
        low = [k for k, v in scores.items() if v is not None and v < STOP_SCORE]
        if not defects and low:
            problems.append((None, f"no defects, but {', '.join(low)} below {STOP_SCORE}: name what is wrong, or raise the score"))

    if len(defects) > MAX_DEFECTS:
        problems.append((None, f"{len(defects)} defects: at most {MAX_DEFECTS}, the worst ones"))
    for n, s in defects:
        m = DEFECT.match(s)
        if not m:
            problems.append((n, "a defect reads: - t=<seconds> evidence=<path> fix=<file>: <change>"))
            continue
        t_raw, evidence, fix, _ = m.groups()
        try:
            t = float(t_raw)
        except ValueError:
            t = None
        if t is None or not 0 <= t <= last_t + 1e-9:
            problems.append((n, f"t={t_raw}: must be a time from 0 to {last_t:.3f} s (the last frame of the video)"))
        ev = pdir / evidence
        if not inside(ev, pdir):
            problems.append((n, f"evidence {evidence} leaves the project folder"))
        elif not ev.is_file():
            problems.append((n, f"evidence {evidence} is not a file in the project"))
        in_project, in_scripts = pdir / fix, SCRIPTS / fix
        if not ((inside(in_project, pdir) and in_project.is_file()) or (inside(in_scripts, SCRIPTS) and in_scripts.is_file())):
            problems.append((n, f"fix file {fix} is neither a file in the project nor a script of the skill"))
    return problems, scores, defects


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("--round", type=int, help="the round to check (default: the highest)")
    a = ap.parse_args()
    reviews = Path(a.project_dir) / "reviews"
    n = a.round if a.round is not None else latest_round(reviews)
    path = reviews / f"critique-{n}.md"
    if n is None or not path.is_file():
        print(f"error: no {path if n is not None else reviews / 'critique-N.md'}: write the critique first "
              f"(format in references/critique.md)", file=sys.stderr)
        sys.exit(1)
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        die(f"cannot read {path}: {e}")
    problems, scores, defects = check(a.project_dir, text)
    if problems:
        for line, msg in problems:
            print(f"{path.name}{f': line {line}' if line else ''}: {msg}", file=sys.stderr)
        sys.exit(1)
    print(f"ok: {path.name}: {len(scores)} scores, {len(defects)} defects")


if __name__ == "__main__":
    main()
