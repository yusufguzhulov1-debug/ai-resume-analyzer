# Scaffolding a Remotion project

Use this when the target folder has no Remotion project yet. The result should be a
clean, neutral, working starting point — **not** a finished style. The user will take
the visual direction themselves; your job is to remove every obstacle between them and
that work, and to leave nothing broken or half-wired.

## 1. Initialize

Create a Remotion + TypeScript project in the target folder using the latest Remotion,
then install and verify it actually runs before moving on. A scaffold that was never
executed usually has one wrong path in it.

If the folder is empty, the fastest route is the official template:

```bash
npx create-video@latest . --template blank
npm install
```

Then add what the project needs beyond the bare template: `zod` and `@remotion/zod-types`
(schemas + color pickers in the Studio), `@remotion/google-fonts` or `@remotion/fonts`,
and `@remotion/transitions` if scenes will cut between each other. Keep every
`@remotion/*` package on the same version as `remotion` itself — mismatched versions
produce confusing runtime errors.

## 2. Structure

```
src/
  Root.tsx           registers every composition
  config.ts          shared canvas settings (size, fps) + helpers
  tokens.ts          brand: colors, radii, spacing (if the user has a brand)
  fonts.ts           font loading, exports FONT_FAMILY
  compositions/      one file per graphic
public/              fonts, images, audio (reached via staticFile())
out/                 renders (gitignore this)
```

`out/` and `node_modules/` belong in `.gitignore`. Renders are large and regenerable.

## 3. Canvas config in one place

Resolution and fps live in a single module so the user can switch to 4K or 60fps without
touching any composition. Default to 1920×1080 at 30fps unless the user's format says
otherwise (vertical/Reels/TikTok → 1080×1920).

```ts
// src/config.ts
export const CANVAS = {
  width: 1920,
  height: 1080,
  fps: 30,
} as const;

/** Convert seconds to frames at the project frame rate. */
export const sec = (seconds: number): number => Math.round(seconds * CANVAS.fps);

/** Title-safe margin (5% each side). Keep text inside this so crops don't eat it. */
export const SAFE_MARGIN = 0.05;
```

This only pays off if compositions actually use it: size content relative to the canvas
via `useVideoConfig()`, and express timings in seconds via `sec()`. A composition with
`fontSize: 72` and `durationInFrames: 150` hardcoded breaks the moment the canvas
changes, which defeats the point of having the config.

## 4. Four starter compositions

Keep them minimal — the user is going to design their own look, and elaborate starter
styling is something they have to delete first. Each one demonstrates a technique and
each one has a clean enter **and** exit so nothing pops or gets cut mid-animation:

| Composition | Demonstrates |
|---|---|
| `TitleCard` | Full-frame text, staggered entrance, eased exit |
| `LowerThird` | Name + role, slide from edge, title-safe placement |
| `KineticText` | Per-word/per-character animation with springs and stagger |
| `BadgeOverlay` | **Transparent background** — real alpha channel for editors |

Every one gets a zod schema + `defaultProps` so the user can edit values live in the
Studio without touching code. Use `zColor()` from `@remotion/zod-types` for colors —
it renders a real color picker in the Studio instead of a text field.

`BadgeOverlay` is the one that's easy to get wrong: it must paint **no** background at
all. Its `<AbsoluteFill>` carries no `backgroundColor`. In the Studio you should see a
checkerboard behind it — that's the proof the alpha channel is intact. See
`patterns.md` for the full working component.

## 5. Register everything in Root.tsx

```tsx
import {Composition} from 'remotion';
import {CANVAS, sec} from './config';

export const Root: React.FC = () => (
  <>
    <Composition
      id="TitleCard"
      component={TitleCard}
      durationInFrames={sec(5)}
      fps={CANVAS.fps}
      width={CANVAS.width}
      height={CANVAS.height}
      schema={titleCardSchema}
      defaultProps={titleCardDefaultProps}
    />
    {/* ...one per graphic */}
  </>
);
```

## 6. Scripts

```json
{
  "scripts": {
    "studio": "remotion studio",
    "render": "remotion render",
    "typecheck": "tsc --noEmit",
    "upgrade": "remotion upgrade"
  }
}
```

## 7. README

The README is what the user reads at 11pm three weeks from now, so write it for that
moment. It covers:

- **Preview**: `npm run studio`
- **Adding a graphic**: create the component in `src/compositions/`, register it in
  `Root.tsx` with a unique id, fps/size, zod schema and defaultProps
- **Render commands**: the four from SKILL.md (MP4, transparent ProRes, PNG sequence,
  still) — spelled out and copy-pasteable
- **Tips**: keep text in the title-safe area; give every animation a full enter and exit;
  trim leading silence from sound effects so hits land on frame; check a still before
  committing to a full render

## 8. Finish the job

Launch the Studio, then summarize what you built and the two or three commands the user
will actually use most. Don't recite the file tree back at them — they can see it. Tell
them what to do next.
