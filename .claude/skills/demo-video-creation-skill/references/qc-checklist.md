# QC Checklist

Use this checklist before delivery.

## Product Accuracy

- Product name, URL, screenshots, and UI states are real.
- Claims are source-backed or clearly framed as generic benefits.
- No customer logos, numbers, detector scores, or integrations are invented.
- Any third-party website or proof shot is current enough and used with appropriate caution.

## Visual Quality

- Resolution is at least 1920x1080 unless the user explicitly asked otherwise.
- 4K render exists when requested.
- Screenshots remain sharp at the largest zoom.
- Text is readable after compression.
- No text, screenshots, buttons, cursors, or callouts overlap incorrectly.
- Before/after panels share the same visual scale.
- Scene transitions are smooth and logically motivated.
- First five seconds communicate audience and value.

## Motion Quality

- Cursor movements land on actual UI targets.
- Button highlights and click effects align with real coordinates.
- Transitions do not obscure important UI at the wrong moment.
- No long dead pauses unless the pause is deliberate.
- Pacing matches platform: faster for social, calmer for enterprise or investor demos.

## Audio Quality

- Music is instrumental and rights-safe.
- Source, author, URL, and license are documented.
- Music volume does not overpower voiceover, if present.
- SFX are subtle and tied to visible actions.
- Start and end fades are clean.

## Technical Verification

Run `scripts/qc_video.py` or equivalent ffprobe inspection.

Minimum evidence:

- File exists and is non-empty.
- Duration roughly matches brief.
- Width and height meet target.
- Video stream codec is usable for the delivery channel.
- Audio stream is present when music, SFX, or voiceover was requested.
- Contact sheet or still review was created.

## Delivery Package

For a full handoff, provide:

- Final MP4
- Contact sheet or preview stills
- Storyboard or shot list
- Screenshot manifest
- Source project, if user needs iteration
- Music license note, if music is included
