# Editing, captions, and assembly

## Speech edit

Use word timestamps as the source of truth.

- Keep about 80 ms before the first word of a retained chunk.
- Keep 120–180 ms after ordinary phrases.
- Split on pauses longer than roughly 0.75 seconds when tightening rhythm.
- Remove abandoned starts only when the corrected take follows clearly.
- Keep the final complete take when a phrase is repeated.
- Preserve 800–1000 ms after the last spoken sentence.

Review every join for consonant clipping, room-tone discontinuity, and breath pops. A visually clean cut can still sound broken.

## Caption grouping

Build captions after the cut map has changed the timeline.

- Prefer one semantic phrase per cue.
- Typical Chinese cue length: 8–26 visible characters; soft maximum 30.
- Show one or two balanced lines, not three cramped lines.
- Typical duration: 0.7–4.5 seconds.
- End on punctuation, a completed noun phrase, or a completed verb phrase.
- Merge short closers such as `吗`, `呢`, `吧`, `对吧`, and `是吧` into the previous cue.
- Do not end a cue on weak connectors such as `在`, `把`, `通过`, `如果`, `因为`, `所以`, `可以`, `就是`, or `欢迎关注我` when the sentence continues.
- Keep fixed terms together: `SKILL.md`, `Skill Creator`, `AI Hot`, file paths, and commands.

Bad:

```text
你真的知道什么是 Skill
吗
```

Good:

```text
你真的知道什么是 Skill 吗？
```

## Caption layout

Use high-contrast warm white text on a near-black rounded plate when the background changes frequently. Keep the rail above social-app controls and below the circular PiP. Verify long paths at the smallest expected phone preview size.

## Assembly

Render camera, screen, and animation scenes separately. Normalize all scene outputs to:

- 1080×1920.
- 30 fps CFR.
- BT.709 limited range.
- H.264 High, yuv420p.
- AAC stereo, 48 kHz, 160–192 kbps.

Prefer concat demuxing after normalization. Complex `xfade` chains can create timestamp errors on long videos; verify duration after any filtered concat.

## Whole-video 1.1× pacing

When requested, speed the already approved master with pitch preservation:

```bash
ffmpeg -i approved.mp4 \
  -vf "setpts=PTS/1.1" \
  -af "atempo=1.1,aresample=async=1:first_pts=0" \
  -r 30 -c:v h264_videotoolbox -profile:v high -b:v 12M \
  -pix_fmt yuv420p -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart final-1.1x.mp4
```

Recheck the final spoken sentence and outro after retiming. Expected duration is original duration divided by 1.1 within a small frame/audio tolerance.
