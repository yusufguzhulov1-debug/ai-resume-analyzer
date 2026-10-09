# Rhythm Routing

Choose one timing authority and keep it canonical for the entire project.

## Uploaded Music

Use when the user supplies audio or a video containing audio.

- Preserve the source.
- Create a working copy.
- Analyze the final working segment.
- Use the resulting `audiomap.json` for every cut and motion anchor.
- Do not use a second analyzer or hand-adjust the map without recording the change.

## Designed Beat Grid

Use when no music is supplied.

Choose a tempo by brand behavior:

| Character | Starting range |
|---|---|
| calm, premium, reflective | 82–100 BPM |
| educational, editorial, conversational | 100–118 BPM |
| energetic, tech, youth-oriented | 118–136 BPM |

These are starting ranges, not genre labels. Adjust for text density and duration. Prefer 4/4 unless another meter clearly supports the concept.

Create the timing map with `scripts/create-beat-map.mjs`. The default accent cycle is `strong,weak,medium,weak`. Use strong beats for scene or hierarchy changes, medium beats for proof points, weak beats for micro-motion, and bar endings for holds or handoffs.

The video remains silent. Do not create an audio file merely to justify the beat grid. If the user later requests music, treat that as a new uploaded or explicitly generated-audio decision and rebuild the canonical timing map.

## Semantic Timing

Whether timing comes from audio or design:

- reserve the first 0.5–1.0 seconds for the hook
- leave readable holds after major text entrances
- cluster related service reveals
- simplify before the final lockup
- give the final identity a stable 0.8–1.2 second hold
