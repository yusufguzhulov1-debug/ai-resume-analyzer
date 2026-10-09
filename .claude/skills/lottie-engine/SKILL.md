---
name: lottie-engine
description: Use when creating keyframe-based animations with JSON-serializable timelines. Provides layer-based keyframe animation with easing, presets, and export to both MP4 and interactive HTML.
---

# Lottie Engine — Keyframe Animation System

JSON-serializable keyframe animation system. Define animations as layers with keyframed properties, export to MP4 or interactive HTML.

## Quick Start

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills"))

from motion_engine.elements import Text, Rect
from lottie_engine.schema import Animation
from lottie_engine.presets import fade_in, slide_up, bounce_in, stagger_in

# Create animation
anim = Animation(width=1080, height=1920, duration=5.0, fps=30, bg="#0a0a12")

# Add layer with element
title = Text("Claude Code", font_size=96, color="#7c6aff", pos=(540, 400))
layer = anim.add_layer("title", element=title)

# Keyframe properties directly
layer.keyframe(0.0, opacity=0, y=1000)
layer.keyframe(0.5, opacity=1, y=400, easing="ease_out_back")
layer.keyframe(4.5, opacity=1, y=400)
layer.keyframe(5.0, opacity=0, y=380)

# Export
anim.export_mp4("output.mp4")
anim.export_html("output.html")
```

## Layer Keyframing

```python
layer = anim.add_layer("name", element=some_element, z_index=0)

# Set keyframes: time, easing, then any property=value pairs
layer.keyframe(time, easing="ease_out_cubic",
    opacity=1.0,    # 0-1
    x=540.0,        # horizontal position
    y=960.0,        # vertical position
    scale=1.0,      # uniform scale
    rotation=0.0,   # degrees
)
```

## Animation Presets

```python
from lottie_engine.presets import (
    fade_in, fade_out, slide_up, slide_down, slide_left, slide_right,
    bounce_in, bounce_out, pop_in, scale_pulse, rotate_in, stagger_in
)

# Apply to a layer
fade_in(layer, start=0.0, dur=0.5)
slide_up(layer, start=0.0, dur=0.5, from_y=200, to_y=0)
bounce_in(layer, start=0.0, dur=0.6)
pop_in(layer, start=0.0, dur=0.5)  # elastic

# Stagger multiple layers
stagger_in([layer1, layer2, layer3], start=0.5, stagger=0.15, preset="slide_up")
```

## JSON Serialization

```python
# Save/load animation definitions
anim.save_json("animation.json")
loaded = Animation.load_json("animation.json")

# Or work with dicts
data = anim.to_dict()
anim2 = Animation.from_dict(data)
```

## HTML Export

Generates a self-contained HTML file with:
- CSS-driven animation playback via requestAnimationFrame
- Play/Pause/Restart controls
- Timeline scrubber
- All easing functions implemented in JS
- No external dependencies

## MP4 Export

Uses the motion_engine renderer (PIL + OpenCV). Each frame:
1. Creates RGBA canvas at animation resolution
2. Interpolates all layer properties at current time
3. Renders elements with transform and opacity
4. Encodes frame to H.264 MP4
