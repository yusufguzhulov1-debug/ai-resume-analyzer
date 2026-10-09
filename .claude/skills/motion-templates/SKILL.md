---
name: motion-templates
description: Use when building presentation videos, kinetic typography, animated data visualizations, lower thirds, or slide decks. Provides ready-made templates that compose motion_engine and lottie_engine into polished motion graphics.
---

# Motion Templates — Ready-Made Animation Templates

High-level templates for common motion design patterns. Built on top of `motion_engine` and `lottie_engine`.

## Quick Start — Slide Deck

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills"))

from motion_templates.slides import SlideDeck, TitleSlide, StepSlide, BulletSlide, SummarySlide

deck = SlideDeck(theme="dark_purple")
deck.add(TitleSlide("Mastering Claude Code", subtitle="Pro Workflow Tips"))
deck.add(StepSlide(number="01", title="Technical Interview", desc="Make Claude ask questions first"))
deck.add(BulletSlide("Key Concepts", items=["Context management", "Modular assembly", "Quality gates"]))
deck.add(SummarySlide(items=["Interview first", "Build in modules", "Control context"]))
deck.render("presentation.mp4")
```

## Slide Types

### TitleSlide
```python
TitleSlide(title, subtitle="", duration=5.0, title_size=80, subtitle_size=36)
```

### StepSlide
```python
StepSlide(number="01", title="Step Name", desc="Details", duration=6.0)
```

### BulletSlide
```python
BulletSlide(title, items=["Item 1", "Item 2"], duration=7.0, bullet_char="•")
```

### SummarySlide
```python
SummarySlide(items=["Point 1", "Point 2"], title="Summary", duration=7.0)
```

### ImageSlide
```python
ImageSlide(image_path="photo.png", caption="Description", duration=5.0)
```

## Themes

`dark_purple` (default), `dark_blue`, `dark_green`, `light`

Each theme defines: `bg`, `accent`, `accent2`, `text`, `text_secondary`, `card_bg`, `card_border`.

## Kinetic Typography

```python
from motion_templates.kinetic import word_by_word, scale_burst, typewriter, text_stack

scene = Scene(1080, 1920, fps=30, bg="#0a0a12")

# Word-by-word reveal
end = word_by_word(scene, "Hello World Welcome", pos=(540, 960), start=0.0)

# Scale burst (dramatic emphasis)
end = scale_burst(scene, "WOW!", pos=(540, 960), start=end, font_size=120)

# Typewriter effect
end = typewriter(scene, "Loading systems...", pos=(540, 960), start=end)

# Stacked lines with staggered entrance
end = text_stack(scene, ["Line 1", "Line 2", "Line 3"], center=(540, 960), start=end)

scene.render("kinetic.mp4")
```

## Data Visualization

```python
from motion_templates.data_viz import animated_bar_chart, animated_counter, animated_pie_chart

scene = Scene(1080, 1920, fps=30, bg="#0a0a12")

# Animated bar chart
end = animated_bar_chart(scene,
    data=[("Python", 85), ("JavaScript", 72), ("Rust", 45)],
    pos=(540, 500), start=0.0, build_dur=2.0, hold=3.0)

# Counting number
end = animated_counter(scene, target=10000, pos=(540, 1000),
    start=end, prefix="$", suffix="+", font_size=96)

# Pie chart
end = animated_pie_chart(scene,
    data=[("A", 40, "#7c6aff"), ("B", 30, "#ff6ab0"), ("C", 30, "#4ade80")],
    pos=(540, 1400), start=end, donut=True)

scene.render("data_viz.mp4")
```

## Lower Thirds & Title Cards

```python
from motion_templates.lower_thirds import lower_third, title_card, name_plate

scene = Scene(1080, 1920, fps=30, bg="#0a0a12")

# Lower third (name + role)
end = lower_third(scene, name="John Doe", title="Senior Engineer", start=0.0)

# Full-screen title card
end = title_card(scene, title="Chapter 1", subtitle="Getting Started", start=end)

# Gradient name plate
end = name_plate(scene, name="Jane Smith", role="CEO", start=end)

scene.render("lower_thirds.mp4")
```

## Transitions

```python
from motion_templates.transitions import wipe_transition, dissolve_transition, zoom_transition

# Between slide content:
wipe_transition(scene, start=5.0, dur=0.6, direction="left")
dissolve_transition(scene, start=5.0, dur=0.8)
zoom_transition(scene, start=5.0, dur=0.6)
```

## Custom Themes

```python
deck = SlideDeck(theme="dark_purple")
# Override individual colors:
deck.theme["accent"] = "#ff6b6b"
deck.theme["bg"] = "#1a0a0a"
```
