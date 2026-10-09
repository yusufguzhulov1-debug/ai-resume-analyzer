# GIF Optimization Reference

Comprehensive technical reference for GIF optimization. Load this before any
optimization task or when choosing palette/dither settings during conversion.

## Palette Generation Strategies (FFmpeg palettegen)

FFmpeg's `palettegen` filter creates a 256-color palette from the source frames.
The `stats_mode` parameter controls HOW colors are sampled:

| stats_mode | Method | Best For | File Size Impact |
|------------|--------|----------|-----------------|
| `full` | Sample all pixels from all frames equally | General purpose, evenly animated content | Baseline |
| `diff` | Weight pixels that change between frames | Animations with static backgrounds | **Smaller** (static areas get fewer palette slots) |
| `single` | Generate a new palette per frame | Content with dramatic color changes | **Larger** (more complex encoding) |

### When to Use Each

- **`full`** (default): Safe choice for most content. Every frame contributes equally to the palette.
- **`diff`**: Best for GIFs where a subject moves against a static background. The background gets fewer palette slots, so the moving subject gets higher color fidelity. Also produces smaller files because unchanged pixels compress better.
- **`single`**: Only use when colors vary drastically between frames (e.g., rainbow transitions, scene cuts). Produces larger files but prevents color banding in individual frames.

**Recommendation**: Start with `diff` for most GIFs. Fall back to `full` if you see color banding in static areas.

## Dithering Algorithms (FFmpeg paletteuse)

Dithering distributes quantization error to simulate more colors than the palette contains.

| Algorithm | Quality | File Size | Speed | Visual Style |
|-----------|---------|-----------|-------|-------------|
| `floyd_steinberg` | Highest | Largest | Fast | Natural, film-like grain |
| `sierra2` | High | Large | Fast | Slightly less grain than Floyd-Steinberg |
| `sierra2_4a` | Medium-High | Medium | Fast | Simplified Sierra, good balance |
| `bayer:bayer_scale=N` | Medium | **Smallest** | Fastest | Ordered/crosshatch pattern, retro look |
| `none` | Lowest | Smallest | Fastest | Hard color boundaries, posterized |

### bayer_scale Parameter

The `bayer_scale` parameter (0-5) controls the dithering matrix size for bayer dithering:
- `bayer_scale=0`: 2x2 matrix (very visible pattern, smallest files)
- `bayer_scale=1`: 4x4 matrix
- `bayer_scale=2`: 8x8 matrix
- `bayer_scale=3`: 16x16 matrix (recommended balance)
- `bayer_scale=4`: 32x32 matrix
- `bayer_scale=5`: 64x64 matrix (subtlest pattern, largest files)

### Choosing Dithering

| Content Type | Recommended Dither | Reason |
|-------------|-------------------|--------|
| Photography/video | `floyd_steinberg` | Natural error diffusion hides banding |
| Flat illustrations | `bayer:3` or `none` | Fewer colors = less error to diffuse |
| Text animations | `none` or `bayer:3` | Crisp edges, no grain on text |
| Pixel art / retro | `bayer:2` | Matches aesthetic, intentional pattern |
| Size-critical (Discord) | `bayer:3` | Smallest files with acceptable quality |
| Quality-critical | `floyd_steinberg` | Best perceived quality |
| Transparent GIFs | `bayer:3` | Handles transparency edges cleanly |

## Color Quantization

### Global Palette vs Per-Frame Palette

- **Global palette** (default): One 256-color palette shared across all frames. Smaller files, but colors are a compromise across all frames.
- **Per-frame palette** (`stats_mode=single`): Each frame gets its own palette. Better color accuracy per frame, but larger files and potential flickering at frame boundaries.

### Color Count Impact

| Colors | Quality | Size Reduction vs 256 |
|--------|---------|----------------------|
| 256 | Best | Baseline |
| 192 | Very Good | ~10-15% smaller |
| 128 | Good | ~20-30% smaller |
| 64 | Acceptable | ~40-50% smaller |
| 32 | Noticeable loss | ~55-65% smaller |
| 16 | Significant loss | ~65-75% smaller |

### Color Reduction Strategy

1. Start with 256 colors
2. If file is too large, try 128 first (barely noticeable for most content)
3. Only go below 64 for extreme size constraints (Discord)
4. Pair fewer colors with `bayer` dithering (makes reduction less visible)

## diff_mode=rectangle

The `diff_mode` parameter in `paletteuse` controls how frames are encoded:

- **`diff_mode=none`** (default): Each frame is encoded in full.
- **`diff_mode=rectangle`**: Only the rectangular region that changed between frames is encoded.

**Always use `diff_mode=rectangle`** for animations. It dramatically reduces file size for GIFs where only part of the frame changes (most GIFs). The savings compound:
- Subject moving on static background: 40-70% reduction
- Full-frame motion: 5-10% reduction (still worth enabling)
- Zero cost to quality

## Gifsicle Optimization

### Optimization Levels

| Level | Description | Speed | Savings |
|-------|-------------|-------|---------|
| `-O1` | Basic optimization | Fast | 5-10% |
| `-O2` | Moderate optimization | Medium | 10-15% |
| `-O3` | Maximum optimization | Slow | 15-20% |

Always use `-O3` -- the speed difference is negligible for typical GIFs.

### Lossy Compression (--lossy=N)

Gifsicle's `--lossy` parameter introduces controlled quality loss for size reduction.
The value is NOT a percentage -- it's an artifact tolerance scale.

| Value | Quality Impact | Typical Savings |
|-------|---------------|----------------|
| 30 | Imperceptible | 10-20% |
| 60 | Barely visible | 20-30% |
| 80 | Minor artifacts | 25-40% |
| 120 | Noticeable | 35-50% |
| 150 | Visible artifacts | 45-60% |
| 200 | Significant artifacts | 55-70% |

**Strategy**: Start at 30, increase by 30 until target size is reached. Preview after each step.

### Additional Gifsicle Flags

```bash
--no-comments      # Strip comment metadata
--no-names         # Strip frame name metadata
--no-extensions    # Strip extension blocks
--color-method=diversity  # Better color selection (default)
--color-method=blend-diversity  # Blend similar colors (slightly better quality)
```

## Transparency Handling

GIF supports binary transparency (each pixel is either fully opaque or fully transparent).
No semi-transparency / alpha blending.

### FFmpeg Transparent GIF Settings

```
palettegen:
  reserve_transparent=1    # Reserve one palette slot for transparency
  max_colors=255           # 255 colors + 1 transparent = 256

paletteuse:
  alpha_threshold=128      # Pixels with source alpha < 128 become transparent
```

### Alpha Threshold Tuning

- `alpha_threshold=0`: Only fully transparent pixels (alpha=0) become transparent
- `alpha_threshold=128`: Default; pixels with <50% opacity become transparent
- `alpha_threshold=255`: Only fully opaque pixels remain; everything else transparent

For clean edges on transparent GIFs, use `alpha_threshold=128` with `dither=bayer:bayer_scale=3`.

## File Size Estimation

Rough formula for estimating GIF file size before creation:

```
estimated_bytes = width * height * frame_count * color_factor * dither_factor * motion_factor

color_factor:
  256 colors = 0.5
  128 colors = 0.4
  64 colors  = 0.3

dither_factor:
  floyd_steinberg = 1.0
  sierra2         = 0.95
  bayer:3         = 0.7
  none            = 0.5

motion_factor (with diff_mode=rectangle):
  Full-frame motion  = 0.8
  Partial motion     = 0.3
  Mostly static      = 0.15
```

This is very approximate. Actual compression depends heavily on content complexity.

## Optimization Decision Flowchart

```
Is GIF too large?
  |
  +--> Apply gifsicle -O3 --lossy=30 (always first)
  |     |
  |     +--> Still too large?
  |           |
  |           +--> Is dither floyd_steinberg?
  |           |     +--> Yes: Switch to bayer:3 + stats_mode=diff
  |           |     +--> No: Reduce colors (256->128->64)
  |           |
  |           +--> Still too large?
  |           |     +--> Reduce dimensions (640->480->320)
  |           |
  |           +--> Still too large?
  |           |     +--> Increase lossy (60->80->120->150)
  |           |
  |           +--> Still too large?
  |           |     +--> Reduce FPS (20->15->10->8)
  |           |
  |           +--> Still too large?
  |                 +--> Content is too complex for target size
  |                 +--> Suggest: trim duration, split into parts, or use video format
```
