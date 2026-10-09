---
name: composition
description: Remotion best practices the components follow, and how to extend them safely
---

# Composition

The Remotion rules this project is built on. Follow them when editing the
components or adding a new one.

## Animation

Drive everything from `useCurrentFrame()` and `interpolate()`. CSS
`transition`, CSS `animation` and Tailwind animation classes do not render:
each frame is captured independently, so there is no wall clock for the browser
to animate against.

Keep the `interpolate()` call inline in the `style` prop. Studio can then edit
the keyframes and write them back to the source; a value hoisted into a
variable cannot be edited that way.

```tsx
// Good
style={{
  opacity: interpolate(frame, [0, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  }),
}}

// Not editable in Studio, and drifts out of sync with the markup
const opacity = interpolate(frame, [0, 26], [0, 1]);
style={{ opacity }}
```

Use the `scale`, `translate` and `rotate` CSS properties rather than a
`transform` string, and pass `output: "perceptual-scale"` on scale animations
so growth reads as linear to the eye.

Always clamp: `extrapolateLeft: "clamp", extrapolateRight: "clamp"`. Without it
a value keeps running past its range and produces negative opacity or inverted
scale at the edges of a sequence.

## Interactive markup

Wrap meaningful blocks in `Interactive.Div` with a `name`, and give
`AbsoluteFill` and `Sequence` names too. Those names become the Studio timeline
and the click-to-source targets. It costs nothing at render time.

## Media

- Audio and video: `<Audio>` and `<Video>` from `@remotion/media`.
- Images: `<CanvasImage>` from `remotion`.
- Animated formats: `<AnimatedImage>`.
- Always reference `public/` files through `staticFile()`.

Sarvam returns WAV. Remotion plays it directly, so there is no MP3 conversion
step and no ffmpeg dependency anywhere in this project.

## Duration

`calculateMetadata` on the `<Composition>` fetches `story.json` and returns
`width`, `height`, `fps`, `durationInFrames`, `defaultOutName` and the parsed
story as props. The values on `<Composition>` itself are placeholders.

```tsx
const calculateMetadata: CalculateMetadataFunction<StoryVideoProps> = async ({
  props,
  abortSignal,
}) => {
  const response = await fetch(props.storyUrl, { signal: abortSignal });
  const story = storySchema.parse(await response.json());
  const { width, height } = DIMENSIONS[story.orientation];
  return {
    width,
    height,
    fps: story.fps,
    durationInFrames: totalFrames(story),
    defaultOutName: story.slug,
    props: { ...props, story },
  };
};
```

Pass the `abortSignal` through to `fetch` so stale requests are cancelled when
props change in the Studio.

Scene lengths come from the audio measurement in `story.json`, so the timeline
cannot drift. If you ever add `<TransitionSeries>`, remember the total shrinks
by the overlap of each transition and the metadata must subtract it.

## Layout

`src/lib/layout.ts` derives every size from `width / 1080`:

- Safe area: 80px sides, 100px top and bottom, scaled.
- Headline at least 84px, supporting text at least 44px, scaled.
- Subtitles sit `100 * scale` from the bottom, capped by `fitText` to the safe
  width so a long word shrinks instead of overflowing.
- Vertical frames get 4 word subtitle groups instead of 6, and the stat card
  moves from top right to top centre.

This is why one component serves both 1920x1080 and 1080x1920. When adding an
element, take its sizes from `getLayout()` rather than typing pixel constants.

## Fonts

Load fonts at module level in `src/lib/fonts.ts`, never inside a component, and
request only the weights and subsets used. A bare `loadFont()` pulls every
weight and subset, which is dozens of network requests per family on every
render. Asking for a weight a family does not ship throws at render time:
Space Grotesk stops at 700.

## Adding a composition

Nothing to register. `Root.tsx` lists `getStaticFiles()`, finds every
`<slug>/story.json` under `public/`, and creates one composition per story with
the slug in PascalCase as the id. Drop a folder in, it appears in the Studio.

## Rendering

```bash
npx remotion render <CompositionId> out/<slug>.mp4 --codec h264
```

Keep all `@remotion/*` packages on one version, with the `mediabunny` version
that matches. A mixed install fails at bundling with an error like
`export 'Logging' was not found in 'mediabunny'`. Check with
`npx remotion versions`, fix with `npx remotion upgrade`.
