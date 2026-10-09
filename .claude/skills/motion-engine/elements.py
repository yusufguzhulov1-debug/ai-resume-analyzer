"""Drawable elements for the motion engine.

Each element knows how to draw itself onto a PIL Image given current properties.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .color import Color, parse_color, ColorLike, lerp_color


class Element:
    """Base class for drawable elements."""

    def __init__(
        self,
        pos: Tuple[float, float] = (0, 0),
        anchor: Tuple[float, float] = (0.5, 0.5),
        opacity: float = 1.0,
        scale: float = 1.0,
        rotation: float = 0.0,
    ):
        self.x, self.y = pos
        self.anchor_x, self.anchor_y = anchor
        self.opacity = opacity
        self.scale = scale
        self.rotation = rotation

    def get_bounds(self) -> Tuple[float, float]:
        """Return (width, height) of the element before transforms."""
        return (0, 0)

    def draw_content(self, img: Image.Image) -> Image.Image:
        """Draw the element content onto an RGBA image sized to bounds. Override this."""
        return img

    def render(self, canvas: Image.Image) -> Image.Image:
        """Render this element onto the canvas with transforms applied."""
        if self.opacity <= 0:
            return canvas

        w, h = self.get_bounds()
        if w <= 0 or h <= 0:
            return canvas

        sw = max(1, int(w * self.scale))
        sh = max(1, int(h * self.scale))

        # Draw content at native size
        content = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
        content = self.draw_content(content)

        # Scale
        if self.scale != 1.0:
            content = content.resize((sw, sh), Image.Resampling.LANCZOS)

        # Rotate
        if self.rotation != 0:
            content = content.rotate(
                -self.rotation, resample=Image.Resampling.BICUBIC, expand=True
            )

        # Apply opacity
        if self.opacity < 1.0:
            alpha = content.getchannel("A")
            alpha = alpha.point(lambda a: int(a * self.opacity))
            content.putalpha(alpha)

        # Position (anchor-adjusted)
        cw, ch = content.size
        px = int(self.x - cw * self.anchor_x)
        py = int(self.y - ch * self.anchor_y)

        canvas.paste(content, (px, py), content)
        return canvas


class Text(Element):
    """Text element with font support."""

    def __init__(
        self,
        text: str,
        font_size: int = 48,
        color: ColorLike = "#ffffff",
        font: Optional[str] = None,
        bold: bool = False,
        align: str = "center",
        max_width: Optional[int] = None,
        line_height: float = 1.3,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = font_size
        self.color = parse_color(color)
        self.font_path = font
        self.bold = bold
        self.align = align
        self.max_width = max_width
        self.line_height = line_height
        self._font_obj: Optional[ImageFont.FreeTypeFont] = None

    def _get_font(self) -> ImageFont.FreeTypeFont:
        if self._font_obj is None:
            if self.font_path:
                self._font_obj = ImageFont.truetype(self.font_path, self.font_size)
            else:
                # Try common system fonts
                for name in [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/SFNSText.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                ]:
                    try:
                        self._font_obj = ImageFont.truetype(name, self.font_size)
                        break
                    except (OSError, IOError):
                        continue
                if self._font_obj is None:
                    self._font_obj = ImageFont.load_default(size=self.font_size)
        return self._font_obj

    def _wrap_text(self, font: ImageFont.FreeTypeFont) -> list[str]:
        """Wrap text to max_width if set."""
        if not self.max_width or not self.text:
            return self.text.split("\n")

        lines = []
        for paragraph in self.text.split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                test = f"{current} {word}"
                bbox = font.getbbox(test)
                if bbox[2] - bbox[0] <= self.max_width:
                    current = test
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def get_bounds(self) -> Tuple[float, float]:
        font = self._get_font()
        lines = self._wrap_text(font)
        max_w = 0
        total_h = 0
        lh = int(self.font_size * self.line_height)
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            max_w = max(max_w, w)
            total_h = lh * (i + 1) if i < len(lines) - 1 else lh * i + (bbox[3] - bbox[1])
        return (max_w + 4, total_h + 4)

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        font = self._get_font()
        lines = self._wrap_text(font)
        lh = int(self.font_size * self.line_height)
        img_w = img.width

        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            if self.align == "center":
                x = (img_w - tw) / 2
            elif self.align == "right":
                x = img_w - tw - 2
            else:
                x = 2
            y = i * lh
            draw.text((x, y), line, fill=self.color.rgba, font=font)
        return img


class Rect(Element):
    """Rectangle element with optional rounded corners and gradient."""

    def __init__(
        self,
        width: float,
        height: float,
        color: ColorLike = "#ffffff",
        border_radius: int = 0,
        border_color: Optional[ColorLike] = None,
        border_width: int = 0,
        gradient_end: Optional[ColorLike] = None,
        gradient_angle: float = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.width = width
        self.height = height
        self.color = parse_color(color)
        self.border_radius = border_radius
        self.border_color = parse_color(border_color) if border_color else None
        self.border_width = border_width
        self.gradient_end = parse_color(gradient_end) if gradient_end else None
        self.gradient_angle = gradient_angle

    def get_bounds(self) -> Tuple[float, float]:
        return (self.width, self.height)

    def draw_content(self, img: Image.Image) -> Image.Image:
        if self.gradient_end:
            img = self._draw_gradient(img)
        else:
            draw = ImageDraw.Draw(img)
            if self.border_radius > 0:
                draw.rounded_rectangle(
                    [0, 0, int(self.width) - 1, int(self.height) - 1],
                    radius=self.border_radius,
                    fill=self.color.rgba,
                )
            else:
                draw.rectangle(
                    [0, 0, int(self.width) - 1, int(self.height) - 1],
                    fill=self.color.rgba,
                )

        if self.border_color and self.border_width > 0:
            draw = ImageDraw.Draw(img)
            if self.border_radius > 0:
                draw.rounded_rectangle(
                    [0, 0, int(self.width) - 1, int(self.height) - 1],
                    radius=self.border_radius,
                    outline=self.border_color.rgba,
                    width=self.border_width,
                )
            else:
                draw.rectangle(
                    [0, 0, int(self.width) - 1, int(self.height) - 1],
                    outline=self.border_color.rgba,
                    width=self.border_width,
                )
        return img

    def _draw_gradient(self, img: Image.Image) -> Image.Image:
        w, h = int(self.width), int(self.height)
        angle_rad = math.radians(self.gradient_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Vectorized gradient using numpy
        xs = np.linspace(0, 1, w, dtype=np.float32)
        ys = np.linspace(0, 1, h, dtype=np.float32)
        xg, yg = np.meshgrid(xs, ys)
        t = xg * cos_a + yg * sin_a
        t = np.clip(t, 0, 1)

        c1 = self.color
        c2 = self.gradient_end
        arr = np.zeros((h, w, 4), dtype=np.uint8)
        arr[:, :, 0] = (c1.r + (c2.r - c1.r) * t).astype(np.uint8)
        arr[:, :, 1] = (c1.g + (c2.g - c1.g) * t).astype(np.uint8)
        arr[:, :, 2] = (c1.b + (c2.b - c1.b) * t).astype(np.uint8)
        arr[:, :, 3] = (c1.a + (c2.a - c1.a) * t).astype(np.uint8)

        grad = Image.fromarray(arr, "RGBA")

        # Apply rounded corners mask
        if self.border_radius > 0:
            mask = Image.new("L", (w, h), 0)
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle([0, 0, w - 1, h - 1], radius=self.border_radius, fill=255)
            grad.putalpha(mask)

        img.paste(grad, (0, 0), grad)
        return img


class GradientRect(Rect):
    """Convenience alias: Rect with gradient always enabled."""

    def __init__(self, width: float, height: float, start_color: ColorLike,
                 end_color: ColorLike, angle: float = 0, **kwargs):
        super().__init__(
            width=width, height=height, color=start_color,
            gradient_end=end_color, gradient_angle=angle, **kwargs
        )


class Circle(Element):
    """Circle element."""

    def __init__(
        self,
        radius: float,
        color: ColorLike = "#ffffff",
        border_color: Optional[ColorLike] = None,
        border_width: int = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.radius = radius
        self.color = parse_color(color)
        self.border_color = parse_color(border_color) if border_color else None
        self.border_width = border_width

    def get_bounds(self) -> Tuple[float, float]:
        d = self.radius * 2
        return (d, d)

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        d = int(self.radius * 2) - 1
        draw.ellipse([0, 0, d, d], fill=self.color.rgba)
        if self.border_color and self.border_width > 0:
            draw.ellipse(
                [0, 0, d, d],
                outline=self.border_color.rgba,
                width=self.border_width,
            )
        return img


class Line(Element):
    """Line element between two points."""

    def __init__(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        color: ColorLike = "#ffffff",
        width: int = 2,
        **kwargs,
    ):
        # Position at top-left of bounding box
        min_x = min(start[0], end[0])
        min_y = min(start[1], end[1])
        super().__init__(pos=(min_x, min_y), anchor=(0, 0), **kwargs)
        self.start = start
        self.end = end
        self.color = parse_color(color)
        self.line_width = width

    def get_bounds(self) -> Tuple[float, float]:
        w = abs(self.end[0] - self.start[0]) + self.line_width * 2
        h = abs(self.end[1] - self.start[1]) + self.line_width * 2
        return (max(w, 1), max(h, 1))

    def draw_content(self, img: Image.Image) -> Image.Image:
        draw = ImageDraw.Draw(img)
        ox = -min(self.start[0], self.end[0]) + self.line_width
        oy = -min(self.start[1], self.end[1]) + self.line_width
        draw.line(
            [
                (self.start[0] + ox, self.start[1] + oy),
                (self.end[0] + ox, self.end[1] + oy),
            ],
            fill=self.color.rgba,
            width=self.line_width,
        )
        return img


class ImageElement(Element):
    """Image element from file path or PIL Image."""

    def __init__(
        self,
        source,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if isinstance(source, str):
            self._img = Image.open(source).convert("RGBA")
        elif isinstance(source, Image.Image):
            self._img = source.convert("RGBA")
        else:
            raise ValueError("source must be a file path or PIL Image")

        if width and height:
            self._img = self._img.resize((width, height), Image.Resampling.LANCZOS)
        elif width:
            ratio = width / self._img.width
            self._img = self._img.resize(
                (width, int(self._img.height * ratio)), Image.Resampling.LANCZOS
            )
        elif height:
            ratio = height / self._img.height
            self._img = self._img.resize(
                (int(self._img.width * ratio), height), Image.Resampling.LANCZOS
            )

    def get_bounds(self) -> Tuple[float, float]:
        return (self._img.width, self._img.height)

    def draw_content(self, img: Image.Image) -> Image.Image:
        img.paste(self._img, (0, 0), self._img)
        return img
