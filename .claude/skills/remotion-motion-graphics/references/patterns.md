# Working patterns

Copy from here rather than reconstructing the API from memory. These are the shapes that
work; the Remotion API has edges that fail quietly (a `spring` without `fps`, an
`interpolate` without clamping, an `AbsoluteFill` that kills your alpha channel) and the
damage usually isn't visible until the render is in the editor.

## Contents

- [Composition skeleton](#composition-skeleton) — schema, defaultProps, registration
- [Enter, hold, exit](#enter-hold-exit) — the core timing pattern
- [Spring](#spring) — non-robotic motion
- [Stagger](#stagger) — cascading entrances
- [Transparent overlay](#transparent-overlay) — real alpha channel
- [Animated number](#animated-number) — counters and stat reveals
- [Auto-fit text](#auto-fit-text) — long strings that don't overflow
- [Audio](#audio) — sound effects on frame
- [Fonts](#fonts) — Google and local
- [Scenes](#scenes) — sequencing a longer piece

## Composition skeleton

Every graphic exports three things: the component, its schema, its defaults. The schema is
what gives the user live-editable controls in the Studio.

```tsx
import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {zColor} from '@remotion/zod-types';
import {z} from 'zod';
import {SAFE_MARGIN} from '../config';
import {FONT_FAMILY} from '../fonts';

export const titleCardSchema = z.object({
  title: z.string(),
  subtitle: z.string(),
  accent: zColor(),
});

export const titleCardDefaultProps: z.infer<typeof titleCardSchema> = {
  title: 'Your title here',
  subtitle: 'Supporting line',
  accent: '#22C55E',
};

export const TitleCard: React.FC<z.infer<typeof titleCardSchema>> = ({
  title,
  subtitle,
  accent,
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();
  // ...
};
```

`zColor()` renders a real color picker in the Studio instead of a text field. Size against
`width`/`height` from `useVideoConfig()` — `fontSize: height * 0.06` survives a switch to
4K or vertical; `fontSize: 72` does not.

Register in `Root.tsx`:

```tsx
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
```

## Enter, hold, exit

The pattern behind the most important craft rule. `enter` ramps 0→1 at the start, `exit`
ramps 0→1 at the end, and everything visual is driven by the pair.

```tsx
const frame = useCurrentFrame();
const {fps, durationInFrames} = useVideoConfig();

// Enter: spring from 0 to 1 over the first beat.
const enter = spring({frame, fps, config: {damping: 14, stiffness: 120}});

// Exit: 0 → 1 across the last 0.5s, eased in so it accelerates away.
const exit = interpolate(
  frame,
  [durationInFrames - Math.round(0.5 * fps), durationInFrames - 1],
  [0, 1],
  {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.quad),
  },
);

const opacity = enter * (1 - exit);
const scale = enter * (1 - 0.3 * exit);
const y = (1 - enter) * 40 + exit * -30;
```

Both `extrapolateLeft` and `extrapolateRight` must be `'clamp'`. Without them
`interpolate` keeps extrapolating past the range and your opacity goes negative or past 1
— which sometimes looks fine and sometimes produces an invisible element you'll spend
twenty minutes debugging.

Reserve the exit window *inside* the duration. If the clip is 5s and the exit takes 0.5s,
the exit starts at 4.5s.

## Spring

```tsx
const enter = spring({
  frame,           // required
  fps,             // required — from useVideoConfig(), never hardcoded
  config: {damping: 14, stiffness: 120},
  durationInFrames: 20,  // optional: force it to settle in a set time
  delay: 5,              // optional: wait N frames before starting
});
```

Tuning by feel: **damping** low (8–12) = bouncy overshoot, high (20+) = smooth, no bounce.
**stiffness** high = snappier. `damping: 200` is effectively a smooth ease with no
overshoot at all — useful when bounce would be undignified.

For anticipation, run a small negative move before the main one:

```tsx
const windup = interpolate(frame, [0, 4], [0, -8], {
  extrapolateRight: 'clamp',
  easing: Easing.out(Easing.quad),
});
const x = windup + spring({frame: frame - 4, fps, config: {damping: 12}}) * 8;
```

## Stagger

Delay each item by its index. `frame - delay` fed to a spring is all it takes.

```tsx
{items.map((item, i) => {
  const delay = i * 4;  // 4 frames apart at 30fps
  const enter = spring({frame: frame - delay, fps, config: {damping: 14}});
  const exit = interpolate(
    frame,
    [durationInFrames - 15 + i * 2, durationInFrames - 5 + i * 2],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  return (
    <span
      key={item}
      style={{
        opacity: enter * (1 - exit),
        transform: `translateY(${(1 - enter) * 30}px)`,
        display: 'inline-block',
      }}
    >
      {item}
    </span>
  );
})}
```

`display: inline-block` matters — `transform` does nothing on an inline element, and this
is a common silent failure.

Stagger the exit too, in the same order. Staggered in, chorus out feels unfinished.

## Transparent overlay

The composition paints **no** background. That's the whole trick, and it's fragile: a
single `backgroundColor` anywhere in the tree destroys the alpha channel, and you won't
see it until the .mov is in the editor.

```tsx
export const BadgeOverlay: React.FC<Props> = ({label, badgeColor, textColor}) => {
  const frame = useCurrentFrame();
  const {fps, width, height, durationInFrames} = useVideoConfig();

  const enter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const pulse = 0.6 + 0.4 * Math.abs(Math.sin((frame / fps) * Math.PI));
  const exit = interpolate(
    frame,
    [durationInFrames - Math.round(0.5 * fps), durationInFrames - 1],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad)},
  );

  // No backgroundColor on this AbsoluteFill — that is what preserves alpha.
  return (
    <AbsoluteFill style={{fontFamily: FONT_FAMILY}}>
      <div
        style={{
          position: 'absolute',
          top: height * SAFE_MARGIN,
          left: width * SAFE_MARGIN,
          display: 'flex',
          alignItems: 'center',
          gap: height * 0.014,
          padding: `${height * 0.014}px ${height * 0.028}px`,
          backgroundColor: badgeColor,   // the badge itself is opaque — fine
          borderRadius: height * 0.06,
          opacity: enter * (1 - exit),
          transform: `scale(${enter * (1 - 0.3 * exit)})`,
          transformOrigin: 'left center',
        }}
      >
        {/* pulsing dot gives the badge idle life while it holds */}
        <div
          style={{
            width: height * 0.018,
            height: height * 0.018,
            borderRadius: '50%',
            backgroundColor: '#e0525c',
            opacity: pulse,
          }}
        />
        <span style={{color: textColor, fontSize: height * 0.028, fontWeight: 700}}>
          {label}
        </span>
      </div>
    </AbsoluteFill>
  );
};
```

Verify in the Studio: a checkerboard behind the badge means alpha is intact. Then render
with `--codec=prores --prores-profile=4444 --pixel-format=yuva444p10le --image-format=png`.

## Animated number

For counters and stat reveals. Drive the value from a spring so it decelerates into the
final number instead of ticking at constant speed, and give it a payoff pop when it lands.

```tsx
const progress = spring({frame, fps, config: {damping: 200}, durationInFrames: sec(1.2)});
const value = Math.round(interpolate(progress, [0, 1], [from, to]));

// Payoff: a brief scale pop right as it settles.
const landed = sec(1.2);
const pop = spring({frame: frame - landed, fps, config: {damping: 10, stiffness: 200}});
const scale = 1 + 0.08 * pop * (1 - pop);
```

Use `fontVariantNumeric: 'tabular-nums'` so digits don't jitter horizontally as they
change — proportional digits make a counter visibly wobble.

Pair with one continuous soft sound over the count, never a tick per digit.

## Audio

```tsx
import {Audio, Sequence, staticFile} from 'remotion';

<Sequence from={sec(0.5)}>
  <Audio src={staticFile('audio/whoosh.mp3')} volume={0.6} />
</Sequence>
```

The `<Sequence from={...}>` is what places the hit on a specific frame. Trim leading
silence from the source file itself — if the file has 80ms of dead air, the sound lands
80ms late no matter where you place the Sequence, and this is the usual cause of audio
that feels subtly wrong against animation that looks right.

`volume` also accepts a function of frame for fades:

```tsx
<Audio
  src={staticFile('audio/music.mp3')}
  volume={(f) => interpolate(f, [0, sec(1)], [0, 0.4], {extrapolateRight: 'clamp'})}
/>
```

## Fonts

Google font:

```ts
// src/fonts.ts
import {loadFont} from '@remotion/google-fonts/Inter';
const {fontFamily} = loadFont();
export const FONT_FAMILY = fontFamily;
```

Local font file in `public/fonts/`:

```ts
import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

loadFont({
  family: 'NeueMontreal',
  url: staticFile('fonts/NeueMontreal-Medium.otf'),
  weight: '500',
});

export const FONT_FAMILY = 'NeueMontreal';
```

Load once in a shared module and import `FONT_FAMILY` everywhere. Loading per-composition
causes flashes of fallback font in the render.

## Auto-fit text

Long strings must shrink rather than overflow. Measure and scale down when needed:

```tsx
import {fitText} from '@remotion/layout-utils';

const {fontSize} = fitText({
  text: title,
  withinWidth: width * (1 - 2 * SAFE_MARGIN),
  fontFamily: FONT_FAMILY,
  fontWeight: 700,
});

// Cap it so short strings don't blow up to absurd sizes.
const size = Math.min(fontSize, height * 0.12);
```

Requires `@remotion/layout-utils`. Worth it the first time a real prop is three words
longer than your default.

## Scenes

For a longer piece, compose scenes with `<Series>` — each scene gets its own frame
counter starting at 0, which means each one can use the enter/hold/exit pattern
unmodified.

```tsx
import {Series} from 'remotion';

<Series>
  <Series.Sequence durationInFrames={sec(4)}>
    <SceneIntro />
  </Series.Sequence>
  <Series.Sequence durationInFrames={sec(6)}>
    <SceneProof />
  </Series.Sequence>
  <Series.Sequence durationInFrames={sec(3)}>
    <SceneBrand />
  </Series.Sequence>
</Series>
```

Overlap scenes with `offset={-sec(0.3)}` on a `Series.Sequence` for a cross-fade, or use
`@remotion/transitions` (`<TransitionSeries>` with `fade()`, `slide()`, `wipe()`) when you
want a real transition rather than a cut.

A persistent background element belongs outside the `<Series>`, in the parent
`<AbsoluteFill>`, so it doesn't restart on every scene.
