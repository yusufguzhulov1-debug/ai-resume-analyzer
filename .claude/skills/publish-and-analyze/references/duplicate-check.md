# Duplicate check before scheduling

Instagram holds a reel that "looks like something you shared before". It compares
the picture against everything the account has posted, not only a reel's siblings,
and not the caption, timing or upload route. Hook variants that share one body are
the usual victims. Check every video before it is scheduled, and again after a re-edit.

## Run it

```bash
python3 scripts/dupe_check.py compare <candidate.mp4> <earlier-post.mp4|https-url> [...]
python3 scripts/dupe_check.py batch manifest.json --out report.json
```

- **References:** every earlier post on each destination account, published or
  queued, including reels posted natively in the app, which a scheduler may not list.
  At minimum, the siblings and the last few weeks. Post media URLs work directly;
  fingerprints are cached in `~/.cache/dupe-check`.
- **Batch manifest:** `{"posts": [{"key", "media", "at", "group", "outcome"}]}`; each
  post is scored against every post before it.
- **Needs:** Python 3, FFmpeg, `numpy`, `scipy` and `pdqhash` (Meta's open-source PDQ hash).

## Read the result

| Verdict | Video match | Action |
|---|---|---|
| LIKELY CLEAR | < 0.10 | Schedule |
| BORDERLINE | 0.10–0.55 | Barely tested; fix it before posting |
| LIKELY HELD | ≥ 0.55 | Don't schedule. Re-edit, then check again |

Video match is the share of the candidate's frames with a near-identical frame (PDQ
distance ≤ 31) anywhere in a reference. Audio is reported but doesn't set the
verdict: audio-only changes didn't prevent a hold, and a reel with a changed picture
passed with the same audio. The checker errs toward caution; it predicts, it isn't
the platform's matcher.

## Fix a flagged variant

The treatment that cleared and scored 0.00 transforms the **whole composited frame**:
a punch-in of about 8%, anchored slightly high so faces and captions stay in frame;
a changed grade (warmer or cooler, saturation and contrast a few percent); and a new
cover. A punch-in on the camera layer alone leaves captions and graphics identical
and still scored borderline. Give each variant a different amount, anchor and grade
so they also clear each other. Speed or pitch changes alone are not a fix. Work from
the master, rerun the delivery checks and this check, and record the recipe.
