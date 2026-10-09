---
name: publish-and-analyze
description: "Take an approved cut to a scheduled post and back into the next idea: delivery export, a real-frame cover, hook variants that won't be held as duplicates, scheduling through FavStash after approval, then comparing results. Use when asked to post, schedule, upload, pick a cover, run a hook test or review how recent shorts performed."
---

# Publish and analyze

The last step of the loop: an approved cut goes out, and its results choose the next
idea. **Nothing is uploaded or scheduled until the creator approves the exact files,
caption, account, settings and time.** Prepare everything, show one summary and wait
for "go".

FavStash does the posting and the analytics: one connected channel and 10 posts a
month are free. For Codex and Claude Code, its CLI bridge uploads local files; see
[connecting FavStash](references/favstash-connection.md). The FavStash tools describe
their own current parameters, so read them instead of guessing.

## 1. Export once from the master

Export a high-quality master (ProRes or similar) from the editor, then encode the
delivery file once. A tested starting point for 1080×1920, 30 fps, SDR Rec.709:

```bash
ffmpeg -i master.mov -c:v libx264 -preset slow -crf 16 -maxrate 24M -bufsize 48M \
  -profile:v high -pix_fmt yuv420p \
  -x264-params keyint=60:min-keyint=60:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709 \
  -color_range tv -c:a aac -b:a 128k -ar 48000 -ac 2 \
  -use_editlist 0 -movflags +faststart+negative_cts_offsets delivery.mp4
```

Both streams must start at 0 (`ffprobe -show_entries stream=start_pts`), or lip
sync breaks. Fully decode the file, compare it with the master and match loudness
across hook variants so the test is fair.

## 2. The cover is a second hook

Many viewers see only the cover. Pick a real frame of each variant with a readable
promise, number, proof shot or strong reaction; never a neutral talking frame or a
transition blur. Check the 9:16, 3:4 and square crops at phone size and show the
creator each cover with its frame time. Their pick wins.

## 3. Hook variants without duplicate holds

Variants that share one body get held as "looks like something you shared before".
The platform compares the picture itself; spacing posts out, changing the upload
route or changing the audio doesn't prevent it.

- Post the strongest variant first and untouched; the first upload counts as the original.
- Give each other variant a different **whole-frame** treatment before posting:
  about an 8% punch-in anchored slightly high, a changed grade and its own cover.
  Treat the composited frame, not only the camera layer.
- A shared end card counts too; give each reel's card its own background.
- Check every file with the [duplicate check](references/duplicate-check.md) against
  the account's earlier posts and its siblings. Never re-upload a held file; only a
  treated file that checks clear may replace it.

Trial Reels let variants reach non-followers, but the connector's support flag isn't
proof: new accounts have refused them at publish time. On an account that hasn't
published one yet, let one go out before queueing more, or use regular reels.

For TikTok and YouTube Shorts, post the same final export directly. In testing,
TikTok recognized and credited a trend song baked into the video; check YouTube for
a copyright claim a few hours after posting. A comment keyword usually belongs on
the platform where the creator's DM automation runs, with the caption on the other
platforms pointing there.

## 4. Caption and approval

Line one carries the promise (or the comment keyword for a gated reel), then the
payoff with real facts, a material catch if one exists and a few hashtags. Label
AI-generated main footage or a synthetic face or voice; editing assistance, captions
and motion graphics on real footage don't make a video AI-generated.

Show the package: files, covers, caption, accounts, settings, times. Send after "go".

## 5. Upload, verify, learn

- Create one post per variant with its own stable request ID, then read each one
  back: media, cover, caption, settings and time. Once live, check its status and URL.
- Compare variants at equal ages, usually after two or three days. If viewers leave
  in the first two or three seconds, rebuild the opening before touching the body.
- Record one next test and hand it to `find-ideas`. Missing metrics are unknown,
  not zero; never promise reach from an edit alone.
- After everything is confirmed, delete regenerable scratch (test renders, frame
  dumps, unchosen covers). Keep masters, posted files, the project and reports.
