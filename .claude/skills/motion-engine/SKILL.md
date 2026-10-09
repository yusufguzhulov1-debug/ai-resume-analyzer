---
name: motion-engine
description: Use when creating programmatic motion graphics, animations, or video content in Python. Provides Scene-based timeline composition with elements, easing, particles, and shape morphing — renders directly to MP4.
---

# Motion Engine — Programmatic Motion Design

Core rendering framework for creating animations in pure Python. No browser, no Node.js — just PIL + numpy + OpenCV.

## Installation

Already installed. Modules live at `~/.claude/skills/motion_engine/`.

Add to Python path before importing:
```python
import sys
sys.path.insert(0, os.path.expanduser("~/.claude/skills"))
```

## Quick Start

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills"))

from motion_engine.scene import Scene
from motion_engine.elements import Text, Rect, Circle, GradientRect, ImageElement
from motion_engine.easing import get_easing
from motion_engine.color import parse_color, lerp_color
from motion_engine.particles import ParticleSystem
from motion_engine.morph import interpolate_shapes, circle_points, star_points

# Create scene (vertical video: 1080x1920)
scene = Scene(1080, 1920, fps=30, bg="#0a0a12")

# Add elements with timeline
title = Text("Hello World", font_size=96, color="#7c6aff", pos=(540, 960))
scene.add(title, enter=0.0, dur=3.0, exit=4.0,
          enter_anim="fade_up", exit_anim="fade_out")

# Render to MP4
scene.render("output.mp4")
```

## Elements

### Text
```python
Text(text, font_size=48, color="#fff", font=None, bold=False,
     align="center", max_width=None, line_height=1.3,
     pos=(x, y), anchor=(0.5, 0.5), opacity=1.0, scale=1.0, rotation=0.0)
```

### Rect
```python
Rect(width, height, color="#fff", border_radius=0,
     border_color=None, border_width=0,
     gradient_end=None, gradient_angle=0,
     pos=(x, y), ...)
```

### GradientRect
```python
GradientRect(width, height, start_color="#7c6aff", end_color="#ff6ab0",
             angle=45, border_radius=20, pos=(x, y))
```

### Circle
```python
Circle(radius, color="#fff", border_color=None, border_width=0, pos=(x, y))
```

### Line
```python
Line(start=(x1, y1), end=(x2, y2), color="#fff", width=2)
```

### ImageElement
```python
ImageElement(source="path.png", width=200, height=None, pos=(x, y))
```

## Scene.add() Parameters

```python
scene.add(element,
    enter=0.0,          # when element appears (seconds)
    dur=3.0,            # visible duration
    exit=None,          # when exit starts (default: enter + dur)
    enter_anim="fade_in",  # enter animation name
    exit_anim="fade_out",  # exit animation name
    enter_dur=0.4,      # enter animation duration
    exit_dur=0.4,       # exit animation duration
    enter_easing="ease_out_cubic",
    exit_easing="ease_in_cubic",
    z_index=0,          # layer ordering
)
```

### Enter Animations
`fade_in`, `fade_up`, `fade_down`, `fade_left`, `fade_right`, `scale_in`, `scale_up`, `bounce_in`, `slide_up`, `slide_down`, `slide_left`, `slide_right`, `none`

### Exit Animations
`fade_out`, `scale_out`, `slide_up`, `slide_down`, `fade_up`, `fade_down`, `none`

## Easing Functions

All standard easings: `linear`, `ease_in/out/in_out_` + `sine`, `quad`, `cubic`, `quart`, `quint`, `expo`, `circ`, `back`, `elastic`, `bounce`.

Custom: `cubic_bezier(x1, y1, x2, y2)` returns an easing function.

## Particles

```python
ps = ParticleSystem(
    max_particles=500, emit_rate=50,
    lifetime=2.0, speed=100, gravity=50,
    size_start=4, size_end=0,
    color_start="#7c6aff", color_end="#ff6ab0",
    fade_out=True
)
ps.emit_pos = (540, 960)

def on_frame(canvas, t, frame_num):
    ps.update(1/30)
    return ps.draw(canvas)

scene.on_frame(on_frame)
```

## Shape Morphing

```python
from motion_engine.morph import circle_points, star_points, interpolate_shapes, draw_shape

shape_a = circle_points(540, 960, 100)
shape_b = star_points(540, 960, 120, 50, tips=5)

# In a frame callback:
points = interpolate_shapes(shape_a, shape_b, t=0.5)
draw_shape(canvas, points, fill=(124, 106, 255, 200))
```

## Per-Frame Callbacks

```python
def custom_effect(canvas, t, frame_num):
    # t = time in seconds, frame_num = frame index
    # Modify canvas (PIL RGBA Image) and return it
    return canvas

scene.on_frame(custom_effect)
```

## Color Utilities

```python
from motion_engine.color import parse_color, lerp_color, gradient_colors, Color

c = parse_color("#7c6aff")    # Color object
c = parse_color((255, 0, 0))  # RGB tuple
c.rgba  # (124, 106, 255, 255)
c.hex   # "#7c6aff"

mid = lerp_color("#ff0000", "#0000ff", 0.5)  # purple
colors = gradient_colors("#000", "#fff", 10)  # 10-step gradient
```
