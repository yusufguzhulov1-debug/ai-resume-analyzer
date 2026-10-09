# Remotion starter

## Create a project

```bash
node <SKILL_DIR>/scripts/init-project.mjs --output ./paper-cut-remotion
cd ./paper-cut-remotion
npm install
npm run start
```

The copied project registers four 1080×1920, 30 fps compositions:

- `PaperCharacterScene` — separate people-free background plus rear, hero, and foreground character layers with staggered entrances.
- `PaperExplainer` — screen at top, functional support card in the center, circular presenter PiP at lower right.
- `PaperFlow` — a progressive paper-card process diagram.
- `PaperOutro` — identity card, CTA, paper presenter placeholder, and red stamp.

Render them with:

```bash
npm run render:character
npm run render:explainer
npm run render:flow
npm run render:outro
```

## Media props

`PaperExplainer` accepts optional `screenSrc` and `presenterSrc` paths relative to `public/`. Video extensions use `OffthreadVideo`; images use `Img`. When either source is omitted, the template renders a labeled placeholder so it can still be previewed and typechecked.

Put private project media under the generated project's `public/media/`, not inside the installed skill.

## Layered character props

`PaperCharacterScene` accepts an optional people-free `backgroundSrc` plus a `characters` array. Each character entry specifies:

- `src` — transparent image path relative to `public/`; omit only while staging placeholders.
- `label` — stable pose or role label.
- `layer` — `rear`, `hero`, or `foreground`.
- `left`, `top`, and `width` — static composition values approved before motion.
- `at` — entrance frame.
- `enterFrom` — `left`, `right`, `up`, or `down`.
- Optional `rotate` and `opacity`.

Keep foreground character entries before the subtitle rail in z-order. Treat the supplied motion as a starting point: adjust entrance frames and distances to the narration, while preserving the stronger hero landing and the slower rear/background motion.

## Extension points

- Replace the default `PaperCharacterScene` placeholders with project-specific pose PNGs and a people-free background.
- Add poses by changing the `characters` array rather than baking a cast into one image.
- Replace `supportTitle`, `supportCode`, and `supportSteps` from the composition props.
- Adjust screen height before reducing font size.
- Keep the PiP diameter between 300 and 340 px for the default layout.
- Duplicate `FlowNode` entries to match the narration, then stagger their `at` values.
- Replace the outro presenter placeholder with a project-specific transparent paper cutout.

## Determinism

All animation derives from `useCurrentFrame()`, `interpolate()`, and `spring()`. Do not use timers, live network fetches, `Date.now()`, or unseeded randomness. The same frame must render identically in preview and export.

## Retiming

Prefer changing `durationInFrames` and reveal frame offsets to match narration. If a finished animation must be stretched during assembly, calculate `setpts` from target duration/source duration and keep a readable hold after the final reveal.
