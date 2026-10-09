# Remotion and FFmpeg Guide

Use this guide when implementing and rendering the demo video.

## Recommended Stack

- Remotion for scene composition, product screenshot motion, captions, and programmatic animation.
- FFmpeg for metadata inspection, contact sheets, audio conversion, compression, and final transcodes.
- Browser automation or the in-app browser for product research and screenshots.

## Project Setup

When no existing video project exists, copy the starter:

```bash
cp -r demo-video-creation-skill/assets/remotion-starter ./demo-video
cd demo-video
npm install
npm run studio
```

On Windows PowerShell:

```powershell
Copy-Item -Recurse demo-video-creation-skill\assets\remotion-starter .\demo-video
Set-Location .\demo-video
npm install
npm run studio
```

Add screenshots to `public/` or adapt the template's `src/demoConfig.ts`.

## Render Targets

Use a review render first:

```bash
npx remotion render src/index.ts ProductDemo out/product-demo-1080p.mp4 \
  --codec=h264 --audio-codec=aac --pixel-format=yuv420p
```

Use 4K for high-stakes delivery:

```bash
npx remotion render src/index.ts ProductDemo4K out/product-demo-4k.mp4 \
  --codec=h264 --audio-codec=aac --pixel-format=yuv420p
```

Prefer H.264 MP4 for broad sharing. Use ProRes or high-bitrate mezzanine files only if the user asks for editing handoff.

## FFmpeg Verification

Inspect final metadata:

```bash
ffprobe -v error -show_streams -show_format -of json out/product-demo-4k.mp4
```

Create a contact sheet:

```bash
ffmpeg -y -i out/product-demo-4k.mp4 \
  -vf "fps=1/6,scale=480:-1,tile=4x4" out/contact-sheet.jpg
```

Compress for social upload if needed:

```bash
ffmpeg -y -i out/product-demo-4k.mp4 \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow \
  -c:a aac -b:a 192k out/product-demo-upload.mp4
```

## Implementation Notes

- Keep all timings in seconds or named frame helpers.
- Keep scenes data-driven where possible: screenshot path, headline, subline, focus area, transition type.
- Use `interpolate`, `spring`, and easing curves consistently.
- Use static dimensions for browser frames, comparison panels, buttons, and callouts to prevent layout jumps.
- Render stills around transitions and dense UI moments before full render.

## Music and Licensing

Store music in `public/audio/` or another explicit asset path. Add a license note in the project output:

```text
Track: [title]
Author: [author]
Source: [URL]
License: [license]
Usage notes: instrumental background music for product demo video
```

If a license is unclear, do not use the track.
