# Veo Prompt Engineering for GIF-Optimized Video

MANDATORY reading before constructing any Veo prompt for GIF output.
GIF-optimized prompts differ from general video prompts in critical ways.

## Core Principles

### 1. Loop-Friendly Motion

GIFs loop infinitely. The video should either:
- **Naturally cycle** (motion returns to its starting position)
- **Be crossfade-compatible** (first and last frames can blend smoothly)
- **Contain continuous motion** (no start/end, just ongoing movement)

### 2. Static Background Strategy

GIF encoding only stores pixels that change between frames (via `diff_mode=rectangle`).
A static background means only the moving subject is encoded, dramatically reducing file size.

**Size impact**: A subject moving on a static background can be 50-70% smaller than the same
subject with a moving camera or changing background.

### 3. Simple Scenes

Complex scenes with many moving elements, colors, and textures produce larger GIFs.
Simpler scenes = fewer colors = better palette utilization = smaller files.

## Loop-Friendly Prompt Patterns

### Circular Camera Motion
The camera orbits around the subject, returning to the starting position.
```
"Camera slowly orbits 360 degrees around a [subject] on a [surface],
studio lighting, smooth continuous rotation, the view returns to the starting angle"
```

### Cyclical Natural Motion
Elements that inherently repeat: fire, water, breathing, pendulums.
```
"[Natural element] in continuous motion, [lighting], static camera angle,
the movement naturally and seamlessly repeats"
```

Good cyclical subjects:
- Fire: "flickering flame", "crackling campfire", "candle flame dancing"
- Water: "ocean waves rolling", "waterfall cascading", "rain falling"
- Air: "smoke swirling", "clouds drifting", "leaves rustling in wind"
- Mechanical: "gears turning", "clock pendulum swinging", "windmill rotating"
- Organic: "chest breathing", "heart beating", "wings flapping"

### Rotating Objects (Turntable)
```
"A [object] slowly rotating 360 degrees on a [color] surface,
[lighting], product photography style, one complete rotation"
```

### Oscillating Motion (Pendulum)
```
"A [subject] gently [oscillating verb] back and forth,
[setting], smooth continuous motion, hypnotic rhythm"
```
Oscillating verbs: swinging, rocking, bobbing, swaying, pulsing, breathing

### Particle Systems
```
"[Particles] continuously [motion verb] in [direction],
against a [solid color] background, mesmerizing endless flow"
```
Particles: sparks, snowflakes, bubbles, dust motes, stars, fireflies, confetti

## What to AVOID in GIF Prompts

These create videos that loop poorly and/or produce large GIFs:

| Avoid | Why | Alternative |
|-------|-----|------------|
| "walks across the room" | Linear motion, doesn't return | "walks in place" or "stands swaying" |
| "picks up the cup" | One-time action | "holds the cup, steam rising" |
| "enters through the door" | Narrative progression | "stands in the doorway, light behind" |
| Camera pans (left, right, up) | Camera doesn't return to start | Static camera or 360-degree orbit |
| Scene transitions | Cut = impossible to loop | Single continuous shot |
| "begins to..." | Implies start, not cycle | "continuously...", "in a loop" |
| Multiple subjects interacting | Complex, many colors, large file | Single isolated subject |
| Complex backgrounds | Many colors, all changing | Solid color or very simple backdrop |
| "zoom in" / "zoom out" | Doesn't return | Static framing or "breathing zoom" |

## Static Background Templates

### Isolated Subject on Solid Color
```
"A [subject] [action] against a solid [color] background,
[lighting], isolated, clean minimalist backdrop, studio photography"
```
Colors that compress well: black, dark navy, white, solid mid-tones.

### Cinemagraph (Partial Motion)
```
"A [scene] where only the [specific element] moves gently,
everything else perfectly still, cinematic quality, subtle continuous motion,
static camera, the [element] moves in a seamless loop"
```

### Silhouette on Gradient
```
"Silhouette of a [subject] [action] against a [color] gradient sky,
dramatic backlighting, simple composition, continuous motion"
```

## Duration Guidance

| Veo Duration | GIF Duration | Loop Friendliness | Cost |
|-------------|-------------|-------------------|------|
| 4 seconds | 4 seconds | Best (short = easier to loop) | ~$0.60 |
| 8 seconds | 8 seconds or trimmed | Good (more content, trim to best segment) | ~$1.20 |

**Recommendation**: Always generate 4 seconds. It's cheaper and shorter clips loop better.
If the user needs variety, generate multiple 4-second clips rather than one 8-second clip.

## Aspect Ratio for GIF

| Aspect Ratio | Veo Flag | Best For |
|-------------|----------|----------|
| 16:9 | `--aspect-ratio 16:9` | Landscape GIFs, web banners, GitHub README |
| 1:1 | `--aspect-ratio 1:1` | Social media, Discord, chat, icons |
| 9:16 | `--aspect-ratio 9:16` | Mobile, vertical stickers |

**Default recommendation**: 16:9 for general use, 1:1 for social/chat platforms.

## Example Prompts by GIF Type

### Cozy Campfire Loop
```
"A small campfire crackling and flickering on a dark night, close-up shot,
warm orange flames dancing continuously against a solid black background,
sparks rising gently, static camera, the flames move in a natural seamless cycle,
cinematic quality, shallow depth of field"
```

### Ocean Waves Loop
```
"Gentle ocean waves rolling onto a sandy beach and receding, overhead drone shot,
turquoise water, white foam, the waves repeat in a continuous natural cycle,
bright daylight, static camera position, calm rhythm"
```

### Product Turntable
```
"A sleek wireless headphone rotating slowly 360 degrees on a clean white surface,
soft studio lighting, product photography, shadow beneath, one complete smooth rotation,
minimalist background, high-end commercial quality"
```

### Abstract Art Loop
```
"Abstract liquid chrome flowing and morphing in continuous motion,
iridescent purple and blue metallic surface, solid black background,
mesmerizing seamless loop, the forms cycle back to their starting shape,
macro photography style"
```

### Neon Sign Flicker
```
"A neon sign reading 'OPEN' flickering with a warm glow against a dark brick wall,
the sign buzzes and pulses continuously, pink and blue neon light,
static camera, nighttime atmosphere, the flicker repeats naturally"
```

### Coffee Steam (Cinemagraph)
```
"A ceramic coffee mug on a wooden table, perfectly still,
only the steam rising from the cup moves gently upward in a continuous wisp,
warm morning light, shallow depth of field, everything static except the steam,
cozy cafe atmosphere"
```

### Geometric Pattern
```
"A kaleidoscopic geometric pattern rotating and morphing continuously,
sacred geometry, vibrant jewel tones on black background,
the pattern completes one full transformation cycle and returns to start,
perfectly symmetrical, mathematical precision"
```

### Rain on Window
```
"Close-up of raindrops streaming down a window pane continuously,
blurred city lights in the background, the drops flow endlessly,
moody blue-gray tones, static camera, ASMR aesthetic, nighttime"
```

## Post-Generation Loop Assessment

After generating the video, assess loop quality before converting:
1. Watch the first and last second -- do they look similar?
2. If yes: direct conversion will loop well
3. If close but not perfect: apply crossfade (5-8 frames)
4. If very different: apply ping-pong loop (plays forward then reverse)
5. If unsuitable for looping: consider regenerating with a more loop-friendly prompt

## Prompt Enhancement Checklist

Before sending any prompt to Veo for GIF output, verify:

- [ ] Contains loop-friendly motion description ("continuous", "repeating", "cycling")
- [ ] Specifies static camera OR 360-degree camera orbit
- [ ] Describes simple/solid background (or cinemagraph with static scene)
- [ ] No narrative progression (no "begins", "starts", "walks to")
- [ ] No scene cuts or transitions
- [ ] Includes lighting description (affects color palette)
- [ ] Mentions quality ("cinematic", "4K", "professional")
- [ ] Single subject or simple composition (fewer moving elements = smaller GIF)
