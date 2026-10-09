# Remotion traps

Every bug here was found the expensive way — by someone reading code carefully, or by
staring at a wrong render. They share a nasty property: **the code looks right and
nothing throws.** You only find out when the number is wrong, the alpha is gone, or a
glow is sitting on screen from frame 0.

Check this list against any composition you write or touch. It's faster than rediscovering
them.

## interpolate defaults to 'extend', not 'clamp'

The single most damaging one, because it silently corrupts *data*.

```tsx
// A counter that should land on 12400 over 60 frames:
const value = interpolate(frame, [0, 60], [0, 12400]);
```

In a 150-frame composition this does not stop at 12400. The default
`extrapolateRight: 'extend'` keeps the line going: at frame 149 it reads **30793**. The
headline stat on your graphic is simply wrong, and it looks completely intentional.

Always clamp frame-driven interpolate:

```tsx
const value = interpolate(frame, [0, 60], [0, 12400], {
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
});
```

**But do not clamp a spring remap.** `interpolate(springProgress, [0, 1], [-100, 0])`
should stay unclamped — the spring's overshoot past 1 is exactly the elasticity you asked
for, and clamping flattens it back into robotic motion. Rule of thumb: interpolating
`frame` → clamp. Interpolating a spring's output → don't.

## extrapolateLeft: 'clamp' makes effects visible from frame 0

Subtle and very easy to ship.

```tsx
// Intent: a ring that expands at the payoff, around frame 72.
const ring = interpolate(frame, [72, 90], [0, 1], {extrapolateLeft: 'clamp'});
```

Clamping left pins frames 0–71 to the *start value of the range* — which is `0` here, fine
— but the moment your range starts at a visible value:

```tsx
const flash = interpolate(frame, [72, 80], [1, 0], {extrapolateLeft: 'clamp'});
```

…frames 0–71 all read `1`. The flash sits on screen, at full strength, from the first
frame of the clip. Gate payoff effects explicitly on their window instead of relying on
clamping:

```tsx
const inWindow = frame >= 72;
const flash = inWindow ? interpolate(frame, [72, 80], [1, 0], {extrapolateRight: 'clamp'}) : 0;
```

## A backgroundColor anywhere on the root kills the alpha channel

For overlays, the root `<AbsoluteFill>` must paint nothing. Inner shapes can be opaque —
that's the badge itself. But one `backgroundColor` on the outer fill and your ProRes 4444
export arrives in Premiere with a black box behind it, and the render gave no warning.

The Studio's checkerboard is the proof. Check it before you render, not after.

## remotion.config.ts defaults to JPEG, which has no alpha

Even with a correctly transparent composition, this silently flattens it:

```ts
// remotion.config.ts
Config.setVideoImageFormat('jpeg');  // ← destroys transparency project-wide
```

Set `'png'` for any project that produces overlays. This one is especially cruel because
the composition is right, the render command is right, and the output is still wrong.

## Hooks inside .map() break the moment props change

```tsx
{words.map((word, i) => {
  const enter = spring({frame: frame - i * 3, fps});  // ← hook inside a loop
  return <span key={word} style={{opacity: enter}}>{word}</span>;
})}
```

`spring()` is a hook. Calling it inside `.map()` means the hook count changes when the
array length changes — so the first time the user edits the text in the Studio, React
throws. Extract a child component:

```tsx
const Word: React.FC<{word: string; index: number}> = ({word, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame: frame - index * 3, fps});
  return <span style={{opacity: enter, display: 'inline-block'}}>{word}</span>;
};
```

## scaleX on a panel stretches the text inside it

Opening a lower-third plate with `transform: scaleX()` also scales its children —
the name comes out horizontally squashed during the reveal. Use `clip-path` instead,
which reveals without distorting:

```tsx
clipPath: `inset(0 ${(1 - reveal) * 100}% 0 0)`
```

Same trap with `scaleY` on anything containing text.

## Positioned elements paint over non-positioned ones, regardless of DOM order

```tsx
<AbsoluteFill>              {/* background layer — position: absolute */}
  <div>…background…</div>
</AbsoluteFill>
<div>…your title…</div>     {/* static — paints UNDER the absolute layer */}
```

The title is invisible and the DOM order says it shouldn't be. Give the content block
`position: 'relative'` (or its own `<AbsoluteFill>`) so it participates in the same
stacking context.

## transform does nothing on inline elements

`<span>` is inline by default, so `transform: translateY(...)` is silently ignored — your
staggered word entrance just fades with no movement, and nothing errors. Add
`display: 'inline-block'`.

## Mismatched @remotion/* versions

Every `@remotion/*` package must sit on the same version as `remotion` itself. Mismatches
surface as confusing runtime errors that look like your code's fault.

## fonts.ts pointing at a font that isn't there

`loadFont()` against `staticFile('fonts/Whatever.otf')` with no `public/fonts/` directory
fails at render time — or, if the module is never imported, does nothing at all while you
believe the brand font is applied. Renders come out in the fallback face and it's easy to
miss on a small preview. Confirm the file exists before trusting the type.

## Proportional digits jitter while counting

A counter animating through values visibly wobbles as digit widths change. Add
`fontVariantNumeric: 'tabular-nums'`. Costs nothing, and its absence is the kind of thing
that reads as "cheap" without the viewer being able to say why.
