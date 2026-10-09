"""Animated data visualization templates — bar charts, counters, pie, gauge."""

from __future__ import annotations
import math
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from motion_engine.scene import Scene
from motion_engine.elements import Text, Rect, Element
from motion_engine.color import ColorLike, parse_color, lerp_color, gradient_colors
from motion_engine.easing import get_easing


class AnimatedBarChart(Element):
    """Animated horizontal bar chart that builds up over time."""

    def __init__(
        self,
        data: List[Tuple[str, float]],
        width: float = 800,
        height: float = 600,
        bar_color: ColorLike = "#7c6aff",
        bar_color_end: Optional[ColorLike] = "#ff6ab0",
        bg_color: ColorLike = "#1a1a2e",
        text_color: ColorLike = "#ffffff",
        label_size: int = 28,
        value_size: int = 24,
        bar_height: int = 40,
        bar_gap: int = 20,
        bar_radius: int = 8,
        font: Optional[str] = None,
        anim_duration: float = 1.5,
        anim_stagger: float = 0.15,
        anim_easing: str = "ease_out_cubic",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.data = data
        self.width = width
        self.height = height
        self.bar_color = parse_color(bar_color)
        self.bar_color_end = parse_color(bar_color_end) if bar_color_end else None
        self.bg_color = parse_color(bg_color)
        self.text_color = parse_color(text_color)
        self.label_size = label_size
        self.value_size = value_size
        self.bar_height = bar_height
        self.bar_gap = bar_gap
        self.bar_radius = bar_radius
        self.font_path = font
        self.anim_duration = anim_duration
        self.anim_stagger = anim_stagger
        self.anim_easing = anim_easing
        self._progress = 0.0  # 0 to 1, set externally

    def get_bounds(self) -> Tuple[float, float]:
        return (self.width, self.height)

    def _get_font(self, size):
        if self.font_path:
            return ImageFont.truetype(self.font_path, size)
        for name in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]:
            try:
                return ImageFont.truetype(name, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default(size=size)

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        w, h = int(self.width), int(self.height)

        max_val = max(v for _, v in self.data) if self.data else 1
        label_font = self._get_font(self.label_size)
        value_font = self._get_font(self.value_size)

        # Calculate label width
        label_w = 0
        for label, _ in self.data:
            bbox = label_font.getbbox(label)
            label_w = max(label_w, bbox[2] - bbox[0])
        label_w += 20

        bar_area_w = w - label_w - 80
        easing_fn = get_easing(self.anim_easing)

        for i, (label, value) in enumerate(self.data):
            y = 20 + i * (self.bar_height + self.bar_gap)

            # Staggered animation progress
            item_start = i * self.anim_stagger
            item_end = item_start + self.anim_duration
            total_dur = len(self.data) * self.anim_stagger + self.anim_duration
            t = self._progress * total_dur
            raw_t = max(0, min(1, (t - item_start) / self.anim_duration)) if self.anim_duration > 0 else 1
            progress = easing_fn(raw_t)

            # Label
            draw.text((0, y + 5), label, fill=self.text_color.rgba, font=label_font)

            # Bar
            bar_w = max(1, int(bar_area_w * (value / max_val) * progress))
            bar_x = label_w

            color = self.bar_color
            if self.bar_color_end:
                color = lerp_color(self.bar_color, self.bar_color_end, i / max(1, len(self.data) - 1))

            if self.bar_radius > 0:
                draw.rounded_rectangle(
                    [bar_x, y, bar_x + bar_w, y + self.bar_height],
                    radius=self.bar_radius,
                    fill=color.rgba,
                )
            else:
                draw.rectangle(
                    [bar_x, y, bar_x + bar_w, y + self.bar_height],
                    fill=color.rgba,
                )

            # Value text
            val_text = f"{int(value * progress)}"
            draw.text(
                (bar_x + bar_w + 10, y + 5),
                val_text,
                fill=self.text_color.rgba,
                font=value_font,
            )

        return img


def animated_bar_chart(
    scene: Scene,
    data: List[Tuple[str, float]],
    pos: Tuple[float, float] = (540, 960),
    start: float = 0.0,
    build_dur: float = 2.0,
    hold: float = 3.0,
    **chart_kwargs,
) -> float:
    """Add an animated bar chart to a scene.

    Returns the end time.
    """
    chart = AnimatedBarChart(data=data, pos=pos, **chart_kwargs)

    total_dur = build_dur + hold
    scene.add(
        chart,
        enter=start,
        dur=total_dur,
        exit=start + total_dur,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.3,
        exit_dur=0.3,
    )

    def update_chart(canvas, t, frame_num):
        if start <= t < start + total_dur:
            chart._progress = min(1.0, (t - start) / build_dur)
        return canvas

    scene.on_frame(update_chart)
    return start + total_dur + 0.3


class AnimatedCounter(Element):
    """Animated counting number display."""

    def __init__(
        self,
        target: float,
        prefix: str = "",
        suffix: str = "",
        font_size: int = 96,
        color: ColorLike = "#ffffff",
        font: Optional[str] = None,
        decimals: int = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.target = target
        self.prefix = prefix
        self.suffix = suffix
        self.font_size = font_size
        self.color = parse_color(color)
        self.font_path = font
        self.decimals = decimals
        self._progress = 0.0

    def get_bounds(self) -> Tuple[float, float]:
        return (self.font_size * (len(str(int(self.target))) + len(self.prefix) + len(self.suffix) + self.decimals + 1), self.font_size * 1.3)

    def _get_font(self):
        if self.font_path:
            return ImageFont.truetype(self.font_path, self.font_size)
        for name in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]:
            try:
                return ImageFont.truetype(name, self.font_size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default(size=self.font_size)

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        font = self._get_font()
        value = self.target * self._progress
        if self.decimals > 0:
            text = f"{self.prefix}{value:.{self.decimals}f}{self.suffix}"
        else:
            text = f"{self.prefix}{int(value)}{self.suffix}"
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        x = (img.width - tw) / 2
        draw.text((x, 0), text, fill=self.color.rgba, font=font)
        return img


def animated_counter(
    scene: Scene,
    target: float,
    pos: Tuple[float, float] = (540, 960),
    start: float = 0.0,
    count_dur: float = 2.0,
    hold: float = 2.0,
    easing: str = "ease_out_expo",
    **counter_kwargs,
) -> float:
    """Add an animated counter to a scene.

    Returns the end time.
    """
    counter = AnimatedCounter(target=target, pos=pos, **counter_kwargs)
    total_dur = count_dur + hold

    scene.add(
        counter,
        enter=start,
        dur=total_dur,
        exit=start + total_dur,
        enter_anim="fade_in",
        exit_anim="fade_out",
        enter_dur=0.3,
        exit_dur=0.3,
    )

    easing_fn = get_easing(easing)

    def update_counter(canvas, t, frame_num):
        if start <= t < start + total_dur:
            raw = min(1.0, (t - start) / count_dur)
            counter._progress = easing_fn(raw)
        return canvas

    scene.on_frame(update_counter)
    return start + total_dur + 0.3


class AnimatedPieChart(Element):
    """Animated pie/donut chart with reveal animation."""

    def __init__(
        self,
        data: List[Tuple[str, float, ColorLike]],
        radius: float = 200,
        inner_radius: float = 0,
        font_size: int = 20,
        text_color: ColorLike = "#ffffff",
        font: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.data = [(label, val, parse_color(c)) for label, val, c in data]
        self.radius = radius
        self.inner_radius = inner_radius
        self.font_size = font_size
        self.text_color = parse_color(text_color)
        self.font_path = font
        self._progress = 0.0

    def get_bounds(self) -> Tuple[float, float]:
        d = self.radius * 2 + 40
        return (d, d + 30)

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        cx, cy = img.width / 2, self.radius + 10
        total = sum(v for _, v, _ in self.data)
        if total == 0:
            return img

        angle_start = -90
        revealed = 360 * self._progress

        for label, value, color in self.data:
            sweep = (value / total) * 360
            actual_sweep = min(sweep, max(0, revealed - (angle_start + 90)))
            if actual_sweep <= 0:
                angle_start += sweep
                continue

            r = self.radius
            bbox = [cx - r, cy - r, cx + r, cy + r]
            draw.pieslice(bbox, angle_start, angle_start + actual_sweep, fill=color.rgba)

            if self.inner_radius > 0:
                ir = self.inner_radius
                ibbox = [cx - ir, cy - ir, cx + ir, cy + ir]
                draw.ellipse(ibbox, fill=(0, 0, 0, 0))

            angle_start += sweep

        return img


def animated_pie_chart(
    scene: Scene,
    data: List[Tuple[str, float, ColorLike]],
    pos: Tuple[float, float] = (540, 960),
    start: float = 0.0,
    reveal_dur: float = 1.5,
    hold: float = 3.0,
    donut: bool = False,
    **pie_kwargs,
) -> float:
    """Add an animated pie chart to a scene."""
    inner_r = pie_kwargs.pop("radius", 200) * 0.5 if donut else 0
    pie = AnimatedPieChart(data=data, inner_radius=inner_r, pos=pos, **pie_kwargs)
    total_dur = reveal_dur + hold

    scene.add(
        pie,
        enter=start,
        dur=total_dur,
        exit=start + total_dur,
        enter_anim="scale_in",
        exit_anim="scale_out",
        enter_dur=0.3,
        exit_dur=0.3,
    )

    easing_fn = get_easing("ease_out_cubic")

    def update_pie(canvas, t, frame_num):
        if start <= t < start + total_dur:
            raw = min(1.0, (t - start) / reveal_dur)
            pie._progress = easing_fn(raw)
        return canvas

    scene.on_frame(update_pie)
    return start + total_dur + 0.3
