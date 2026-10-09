# QA Checklist

## Automated

- Brand spec validator passes.
- HyperFrames layout, motion, and contrast checks have zero errors.
- Remotion composition resolves with the intended width, height, FPS, and duration.
- Final MP4 contains H.264 video.
- Uploaded-music mode contains AAC audio; designed-beat-grid mode may be silent.
- Duration is within 0.15 seconds of the brand spec.
- Aspect ratio and orientation match the request.

## Visual

Inspect rendered-MP4 frames at the hook, identity, proof, point of view, and final lockup.

- No missing, clipped, substituted, or garbled essential text.
- Supplied images, when present, remain recognizable and are not unintentionally distorted.
- Text-only work contains a meaningful category-native illustration system.
- The largest text has sufficient breathing room.
- Every major scene has a clear hierarchy.
- Decorative graphics support rather than compete with the message.
- Transitions have clean before/after states.
- Final lockup is readable without pausing.

## Audio and Rhythm

For uploaded music:

- Confirm `music.mode` is `uploaded` and `music.userUploaded` is `true`.
- Confirm source and working track are separate files.
- Confirm audio is present, correctly trimmed, and not unexpectedly silent.
- Confirm the reported source time range matches `brand-spec.json`.

For no uploaded music:

- Confirm `music.mode` is `none`.
- Confirm `timing.mode` is `designed-beat-grid`.
- Confirm the MP4 is silent unless the user separately authorized audio generation.
- Report the chosen BPM and accent cycle.

For both:

- Major visual changes land on mapped events.
- Not every element moves at once.
- Holds exist between impacts.
- The ending resolves rather than cutting accidentally.

## Originality

- Compare the seven fingerprint dimensions in `originality-rules.md`.
- Confirm at least five dimensions differ from every demonstration or recent brand.
- Confirm no demonstration copy, palette, layout, timing map, image, or visual asset is present.

## Delivery

- Include the final MP4, source project, brand spec, timing map, and proof frames.
- State checks performed and accepted warnings.
- Do not call a preview or lint result a finished render.
- Do not redistribute user-provided music or images separately from the user's project.
