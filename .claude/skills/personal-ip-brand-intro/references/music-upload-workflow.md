# User-Uploaded Music Workflow

Read this file only when the user provides audio or a video containing audio.

## Source Policy

The user owns the music choice. Accept the provided media and never replace it with searched, stock, demonstration, remembered, or generated music.

## File Layout

```text
assets/
  source/
    user-upload.<original-extension>
  bgm.mp3
audiomap-source.json
audiomap.json
```

Preserve `assets/source/user-upload.*` byte-for-byte. Never overwrite it.

## Duration Decisions

1. If the source duration matches the requested intro within 0.15 seconds, use the full source.
2. If longer, analyze the full source and select a coherent phrase with a clear entry and resolution.
3. Record the selected source start and duration in `brand-spec.json`.
4. Create `assets/bgm.mp3`, analyze it, and use only its `audiomap.json` for animation.
5. If shorter, ask whether to shorten the video or upload another track.

Do not loop, stretch, or pitch-shift music without explicit approval.

## Editing Rules

- Major section change: change hierarchy, scene, or dominant motif.
- Medium onset: reveal a service, illustration, image treatment, or secondary word.
- Weak beat: micro-motion only.
- Silence or decay: hold, simplify, or resolve.
- Final hit: settle the brand lockup rather than start new information.

Report the chosen time range when a long source was trimmed. Do not redistribute the user's source as a standalone deliverable.
