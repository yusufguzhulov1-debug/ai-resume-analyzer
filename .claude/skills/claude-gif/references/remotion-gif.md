# Remotion GIF Patterns Reference

Code patterns and templates for creating GIF-optimized Remotion compositions.
Load this before writing any React component for GIF output.

## GIF-Optimized Composition Settings

### Dimensions
| Target | Width | Height | Aspect Ratio | Use Case |
|--------|-------|--------|-------------|----------|
| Square | 480 | 480 | 1:1 | Social media, chat, icons |
| Landscape | 480 | 270 | 16:9 | Web, GitHub README, email |
| Wide | 640 | 360 | 16:9 | High-quality display |
| Portrait | 270 | 480 | 9:16 | Mobile, stories |
| Banner | 480 | 160 | 3:1 | Email headers, banners |

### Frame Rate
| FPS | durationInFrames (for 3s) | Best For | File Size |
|-----|--------------------------|----------|-----------|
| 10 | 30 | Discord, tiny GIFs | Smallest |
| 12 | 36 | Slack, text animations | Small |
| 15 | 45 | General purpose (recommended) | Medium |
| 20 | 60 | Smooth motion, HQ | Large |

### Duration Formula
```
durationInFrames = fps * seconds
```
- 2 seconds at 15fps = 30 frames
- 3 seconds at 15fps = 45 frames (sweet spot)
- 5 seconds at 15fps = 75 frames (maximum recommended)

## Key Remotion APIs for GIF

```tsx
import {
  useCurrentFrame,    // Current frame number (0-indexed)
  useVideoConfig,     // { fps, width, height, durationInFrames }
  spring,             // Physics-based easing
  interpolate,        // Linear interpolation between values
  Sequence,           // Time-offset child rendering
  Img,                // Image component (static assets)
  AbsoluteFill,       // Full-frame container
} from "remotion";
```

### useCurrentFrame()
Returns the current frame number (0 to durationInFrames - 1).
```tsx
const frame = useCurrentFrame(); // 0, 1, 2, ... 44
```

### spring()
Physics-based animation with bounce, damping, and stiffness.
```tsx
const scale = spring({
  frame,
  fps,
  config: {
    damping: 10,      // Lower = more bouncy (default: 10)
    stiffness: 100,   // Higher = faster (default: 100)
    mass: 1,          // Higher = heavier/slower (default: 1)
  },
});
// Returns 0 to ~1, with overshoot if damping is low
```

### interpolate()
Maps a value from one range to another.
```tsx
const opacity = interpolate(frame, [0, 30], [0, 1], {
  extrapolateRight: "clamp",  // Don't go above 1
});

const x = interpolate(frame, [0, 45], [-200, 0], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});
```

### Sequence
Delays child rendering to start at a specific frame.
```tsx
<Sequence from={15} durationInFrames={30}>
  <SecondElement />
</Sequence>
```

## Template Code Snippets

### 1. Text Bounce

```tsx
import { useCurrentFrame, useVideoConfig, spring, AbsoluteFill } from "remotion";

export const TextBounce: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 200 },
  });

  const translateY = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#1a1a2e",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          fontSize: 64,
          fontWeight: "bold",
          color: "#e94560",
          fontFamily: "Arial, sans-serif",
          transform: `scale(${scale}) translateY(${(1 - translateY) * -50}px)`,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
```

### 2. Loading Spinner

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const Spinner: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const rotation = interpolate(frame, [0, durationInFrames], [0, 360]);

  const dots = Array.from({ length: 8 }, (_, i) => {
    const angle = (i * 360) / 8;
    const delay = i * 3;
    const opacity = interpolate(
      (frame + delay) % durationInFrames,
      [0, durationInFrames / 2, durationInFrames],
      [0.2, 1, 0.2]
    );
    return { angle, opacity };
  });

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#0f0f23", justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ position: "relative", width: 120, height: 120 }}>
        {dots.map((dot, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              width: 16,
              height: 16,
              borderRadius: "50%",
              backgroundColor: "#00d4ff",
              opacity: dot.opacity,
              top: 52 + Math.sin((dot.angle * Math.PI) / 180) * 50,
              left: 52 + Math.cos((dot.angle * Math.PI) / 180) * 50,
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
```

### 3. Counter / Number Roll

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const Counter: React.FC<{ target: number; label: string }> = ({ target, label }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Ease-out curve for counting
  const progress = interpolate(frame, [0, durationInFrames * 0.8], [0, 1], {
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
  const count = Math.round(eased * target);

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#16213e", justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: 96,
            fontWeight: "bold",
            color: "#e94560",
            fontFamily: "monospace",
          }}
        >
          {count.toLocaleString()}
        </div>
        <div style={{ fontSize: 24, color: "#a8a8b3", marginTop: 10 }}>{label}</div>
      </div>
    </AbsoluteFill>
  );
};
```

### 4. Logo Reveal

```tsx
import { useCurrentFrame, useVideoConfig, spring, interpolate, Sequence, AbsoluteFill } from "remotion";

export const LogoReveal: React.FC<{ iconText: string; brandName: string }> = ({
  iconText,
  brandName,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const iconScale = spring({ frame, fps, config: { damping: 8 } });
  const textOpacity = interpolate(frame, [15, 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const textX = interpolate(frame, [15, 30], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#0a0a0a", justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <div
          style={{
            fontSize: 72,
            transform: `scale(${iconScale})`,
          }}
        >
          {iconText}
        </div>
        <div
          style={{
            fontSize: 48,
            fontWeight: "bold",
            color: "#ffffff",
            opacity: textOpacity,
            transform: `translateX(${textX}px)`,
            fontFamily: "Arial, sans-serif",
          }}
        >
          {brandName}
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

### 5. Progress Bar

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const ProgressBar: React.FC<{ label: string; color: string }> = ({
  label,
  color = "#4ecca3",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = interpolate(frame, [5, durationInFrames - 10], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#1a1a2e", justifyContent: "center", alignItems: "center" }}
    >
      <div style={{ width: "80%", textAlign: "center" }}>
        <div style={{ fontSize: 20, color: "#a8a8b3", marginBottom: 16 }}>{label}</div>
        <div
          style={{
            width: "100%",
            height: 32,
            backgroundColor: "#16213e",
            borderRadius: 16,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progress}%`,
              height: "100%",
              backgroundColor: color,
              borderRadius: 16,
              transition: "none",
            }}
          />
        </div>
        <div
          style={{
            fontSize: 36,
            fontWeight: "bold",
            color: color,
            marginTop: 16,
            fontFamily: "monospace",
          }}
        >
          {Math.round(progress)}%
        </div>
      </div>
    </AbsoluteFill>
  );
};
```

### 6. Meme (Top/Bottom Text)

```tsx
import { AbsoluteFill, Img } from "remotion";

export const Meme: React.FC<{ imageSrc: string; topText: string; bottomText: string }> = ({
  imageSrc,
  topText,
  bottomText,
}) => {
  const textStyle: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    textAlign: "center",
    fontSize: 40,
    fontWeight: "bold",
    color: "white",
    fontFamily: "Impact, sans-serif",
    textTransform: "uppercase",
    WebkitTextStroke: "2px black",
    padding: "0 10px",
    lineHeight: 1.2,
  };

  return (
    <AbsoluteFill>
      <Img src={imageSrc} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      <div style={{ ...textStyle, top: 20 }}>{topText}</div>
      <div style={{ ...textStyle, bottom: 20 }}>{bottomText}</div>
    </AbsoluteFill>
  );
};
```

### 7. Typewriter Effect

```tsx
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

export const Typewriter: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const charCount = Math.floor(
    interpolate(frame, [0, durationInFrames * 0.8], [0, text.length], {
      extrapolateRight: "clamp",
    })
  );

  const showCursor = frame % 15 < 10; // Blink every 15 frames

  return (
    <AbsoluteFill
      style={{ backgroundColor: "#0d1117", justifyContent: "center", alignItems: "center" }}
    >
      <div
        style={{
          fontSize: 32,
          color: "#c9d1d9",
          fontFamily: "'Courier New', monospace",
          padding: 40,
          maxWidth: "90%",
        }}
      >
        <span style={{ color: "#7ee787" }}>$ </span>
        {text.substring(0, charCount)}
        <span
          style={{
            display: "inline-block",
            width: 12,
            height: 32,
            backgroundColor: showCursor ? "#c9d1d9" : "transparent",
            marginLeft: 2,
            verticalAlign: "bottom",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
```

### 8. Confetti Burst

```tsx
import { useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill } from "remotion";

const COLORS = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#ff6eb4"];

interface Particle {
  x: number;
  angle: number;
  speed: number;
  color: string;
  size: number;
  rotation: number;
}

// Deterministic random from seed
const seededRandom = (seed: number) => {
  const x = Math.sin(seed * 9301 + 49297) * 49297;
  return x - Math.floor(x);
};

const particles: Particle[] = Array.from({ length: 30 }, (_, i) => ({
  x: seededRandom(i) * 480,
  angle: seededRandom(i + 100) * Math.PI * 2,
  speed: 200 + seededRandom(i + 200) * 300,
  color: COLORS[i % COLORS.length],
  size: 8 + seededRandom(i + 300) * 12,
  rotation: seededRandom(i + 400) * 360,
}));

export const Confetti: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const burst = spring({ frame, fps, config: { damping: 20, stiffness: 80 } });
  const gravity = interpolate(frame, [0, 45], [0, 200], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e", overflow: "hidden" }}>
      {particles.map((p, i) => {
        const px = 240 + Math.cos(p.angle) * p.speed * burst;
        const py = 240 + Math.sin(p.angle) * p.speed * burst + gravity;
        const rot = p.rotation + frame * (i % 2 === 0 ? 8 : -8);
        const opacity = interpolate(frame, [30, 45], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: px,
              top: py,
              width: p.size,
              height: p.size * 0.6,
              backgroundColor: p.color,
              transform: `rotate(${rot}deg)`,
              opacity,
              borderRadius: 2,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
```

## Color Palette Considerations

### GIF-Friendly Colors (Flat, Limited Palette)

```tsx
// Dark themes compress best
const DARK_BG = "#0a0a0a";   // Near-black (common in all frames = 1 palette slot)
const DARK_SURFACE = "#1a1a2e";

// High-contrast accent colors
const ACCENT_RED = "#e94560";
const ACCENT_BLUE = "#00d4ff";
const ACCENT_GREEN = "#4ecca3";
const ACCENT_YELLOW = "#ffd93d";

// Text colors
const TEXT_PRIMARY = "#ffffff";
const TEXT_SECONDARY = "#a8a8b3";
```

### Colors That Waste Palette Slots

Avoid these in GIF-targeted compositions:
- CSS `linear-gradient()` or `radial-gradient()` -- creates hundreds of intermediate colors
- `box-shadow` with blur -- generates many semi-transparent colors
- `text-shadow` with blur
- `filter: blur()` on any element
- Semi-transparent overlays (`rgba` with alpha between 0.1 and 0.9)
- Photographic backgrounds (use solid colors or simple patterns)

### Looping Compositions

For compositions that should seamlessly loop:
- Ensure frame 0 and the last frame are visually identical
- Use modulo operations for cyclic animations:
  ```tsx
  const rotation = (frame / durationInFrames) * 360; // Completes exactly one rotation
  const pulse = Math.sin((frame / durationInFrames) * Math.PI * 2); // Sine wave loop
  ```
- Test by watching the GIF loop several times -- the seam should be invisible

## Root.tsx Registration Template

```tsx
import { Composition } from "remotion";
import { GifComposition } from "./GifComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="GifOutput"
      component={GifComposition}
      durationInFrames={45}    // 3 seconds at 15fps
      fps={15}
      width={480}
      height={480}
      defaultProps={{
        text: "Hello World",  // Override with --props flag
      }}
    />
  );
};
```

## Render Commands

```bash
# Render as PNG frame sequence (recommended for GIF)
npx remotion render src/index.ts GifOutput \
  --image-format png \
  --sequence \
  --output /tmp/claude-gif/frames/frame%04d.png \
  --concurrency 4

# Render with custom props
npx remotion render src/index.ts GifOutput \
  --image-format png \
  --sequence \
  --output /tmp/claude-gif/frames/frame%04d.png \
  --props '{"text": "Custom Text"}'

# Preview in browser
npx remotion preview src/index.ts
```
