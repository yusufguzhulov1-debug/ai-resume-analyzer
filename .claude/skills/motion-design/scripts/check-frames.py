#!/usr/bin/env python3
"""Check the frame files of a project before resuming work (after a session cut, a crash, a killed worker).

A frame is OK when its file exists, is one bare <template>...</template> fragment (a worker that died mid-write
leaves a truncated file), registers its timeline, and every inline <script> passes `node --check`.

Usage (from the repository root):
  python3 .claude/skills/motion-design/scripts/check-frames.py <project>
Prints one line per frame of STORYBOARD.md (OK, MISSING or BROKEN with the reason). Exit code 1 if any frame is not OK:
re-dispatch only those, never the frames that are OK.
"""
import os
import re
import subprocess
import sys
import tempfile


def check(path, frame_id):
    if not os.path.exists(path):
        return "MISSING", "no file"
    text = open(path, encoding="utf-8", errors="replace").read().strip()
    if not text.startswith("<template") or not text.endswith("</template>"):
        return "BROKEN", "not a complete <template>...</template> (half-written?)"
    if f'data-composition-id="{frame_id}"' not in text:
        return "BROKEN", f'no data-composition-id="{frame_id}"'
    if "__timelines[" not in text:
        return "BROKEN", "no timeline registered on window.__timelines"
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", text, re.S)
    for k, js in enumerate(scripts):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(js)
        try:
            r = subprocess.run(["node", "--check", tmp.name], capture_output=True, text=True)
        except FileNotFoundError:
            sys.exit("check-frames.py: node not found on PATH")
        finally:
            os.unlink(tmp.name)
        if r.returncode:
            lines = [l for l in r.stderr.splitlines() if "Error" in l] or r.stderr.splitlines() or ["syntax error"]
            return "BROKEN", f"script {k + 1}: {lines[0].strip()}"
    return "OK", f"{len(text) // 1024} KB, {len(scripts)} script(s)"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    project = sys.argv[1]
    board = os.path.join(project, "STORYBOARD.md")
    if not os.path.exists(board):
        sys.exit(f"check-frames.py: {board} not found")
    srcs = re.findall(r"(?m)^- src: (\S+)", open(board, encoding="utf-8").read())
    bad = 0
    for src in srcs:
        frame_id = os.path.splitext(os.path.basename(src))[0]
        state, why = check(os.path.join(project, src), frame_id)
        bad += state != "OK"
        print(f"{state:8s} {frame_id:28s} {why}")
    print(f"{len(srcs) - bad}/{len(srcs)} frames OK")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
