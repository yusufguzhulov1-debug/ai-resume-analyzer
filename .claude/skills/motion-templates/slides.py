"""Full slide deck builder — compose multi-slide presentations with auto-transitions."""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from motion_engine.scene import Scene
from motion_engine.elements import Text, Rect, Circle, GradientRect
from motion_engine.color import ColorLike, parse_color, lerp_color

from .transitions import dissolve_transition


# --- Theme definitions ---
THEMES: Dict[str, dict] = {
    "dark_purple": {
        "bg": "#0a0a12",
        "accent": "#7c6aff",
        "accent2": "#ff6ab0",
        "text": "#ffffff",
        "text_secondary": "#aaaacc",
        "card_bg": "#16162a",
        "card_border": "#2a2a4a",
    },
    "dark_blue": {
        "bg": "#0a1628",
        "accent": "#4a9eff",
        "accent2": "#00d4aa",
        "text": "#ffffff",
        "text_secondary": "#8899bb",
        "card_bg": "#122240",
        "card_border": "#1e3a60",
    },
    "dark_green": {
        "bg": "#0a1a0f",
        "accent": "#4ade80",
        "accent2": "#22d3ee",
        "text": "#ffffff",
        "text_secondary": "#88bb99",
        "card_bg": "#132a1a",
        "card_border": "#1e4a2a",
    },
    "light": {
        "bg": "#f8f9fa",
        "accent": "#6366f1",
        "accent2": "#ec4899",
        "text": "#1a1a2e",
        "text_secondary": "#64748b",
        "card_bg": "#ffffff",
        "card_border": "#e2e8f0",
    },
}


class Slide:
    """Base class for slide types."""

    def __init__(self, duration: float = 5.0):
        self.duration = duration

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        """Add this slide's elements to the scene.

        Returns the end time.
        """
        raise NotImplementedError


class TitleSlide(Slide):
    """Full-screen title slide with optional subtitle."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        duration: float = 5.0,
        title_size: int = 80,
        subtitle_size: int = 36,
    ):
        super().__init__(duration)
        self.title = title
        self.subtitle = subtitle
        self.title_size = title_size
        self.subtitle_size = subtitle_size

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        cx, cy = scene.width // 2, scene.height // 2
        font = kwargs.get("font")

        # Accent glow circle (background)
        glow = Circle(radius=250, color=theme["accent"],
                      pos=(cx, cy - 100))
        glow.opacity = 0.08
        scene.add(glow, enter=start, dur=self.duration, exit=start + self.duration,
                  enter_anim="scale_in", exit_anim="fade_out",
                  enter_dur=0.8, exit_dur=0.4, enter_easing="ease_out_cubic")

        # Title
        title = Text(self.title, font_size=self.title_size, color=theme["text"],
                     font=font, pos=(cx, cy - 40 if self.subtitle else cy),
                     max_width=int(scene.width * 0.85))
        scene.add(title, enter=start + 0.2, dur=self.duration - 0.5, exit=start + self.duration - 0.3,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.5, exit_dur=0.3, enter_easing="ease_out_cubic")

        # Accent line
        line = Rect(60, 4, color=theme["accent"], pos=(cx, cy + 20 if self.subtitle else cy + 50))
        scene.add(line, enter=start + 0.4, dur=self.duration - 0.8, exit=start + self.duration - 0.4,
                  enter_anim="scale_in", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.2, enter_easing="ease_out_back")

        # Subtitle
        if self.subtitle:
            sub = Text(self.subtitle, font_size=self.subtitle_size, color=theme["text_secondary"],
                       font=font, pos=(cx, cy + 60), max_width=int(scene.width * 0.8))
            scene.add(sub, enter=start + 0.5, dur=self.duration - 0.9, exit=start + self.duration - 0.4,
                      enter_anim="fade_up", exit_anim="fade_out",
                      enter_dur=0.4, exit_dur=0.3)

        return start + self.duration


class StepSlide(Slide):
    """Numbered step slide — shows a large step number, title, and description."""

    def __init__(
        self,
        number: str,
        title: str,
        desc: str = "",
        duration: float = 6.0,
        number_size: int = 160,
        title_size: int = 52,
        desc_size: int = 32,
    ):
        super().__init__(duration)
        self.number = number
        self.title = title
        self.desc = desc
        self.number_size = number_size
        self.title_size = title_size
        self.desc_size = desc_size

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        cx = scene.width // 2
        font = kwargs.get("font")

        # Large step number
        num = Text(self.number, font_size=self.number_size, color=theme["accent"],
                   font=font, pos=(cx, scene.height * 0.3))
        num.opacity = 0.3
        scene.add(num, enter=start, dur=self.duration - 0.3, exit=start + self.duration - 0.3,
                  enter_anim="scale_in", exit_anim="fade_out",
                  enter_dur=0.5, exit_dur=0.3, enter_easing="ease_out_back")

        # Card background
        card = Rect(scene.width * 0.85, 250, color=theme["card_bg"],
                    border_radius=20, border_color=theme["card_border"], border_width=1,
                    pos=(cx, scene.height * 0.52))
        scene.add(card, enter=start + 0.15, dur=self.duration - 0.5, exit=start + self.duration - 0.35,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.3, enter_easing="ease_out_cubic")

        # Title
        title = Text(self.title, font_size=self.title_size, color=theme["text"],
                     font=font, pos=(cx, scene.height * 0.48),
                     max_width=int(scene.width * 0.75))
        scene.add(title, enter=start + 0.3, dur=self.duration - 0.7, exit=start + self.duration - 0.4,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.3)

        # Description
        if self.desc:
            desc = Text(self.desc, font_size=self.desc_size, color=theme["text_secondary"],
                        font=font, pos=(cx, scene.height * 0.56),
                        max_width=int(scene.width * 0.7))
            scene.add(desc, enter=start + 0.45, dur=self.duration - 0.85, exit=start + self.duration - 0.4,
                      enter_anim="fade_up", exit_anim="fade_out",
                      enter_dur=0.4, exit_dur=0.3)

        return start + self.duration


class BulletSlide(Slide):
    """Slide with a title and bullet point items."""

    def __init__(
        self,
        title: str,
        items: List[str],
        duration: float = 7.0,
        title_size: int = 52,
        item_size: int = 32,
        bullet_char: str = "\u2022",
    ):
        super().__init__(duration)
        self.title = title
        self.items = items
        self.title_size = title_size
        self.item_size = item_size
        self.bullet_char = bullet_char

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        cx = scene.width // 2
        font = kwargs.get("font")

        # Title
        title = Text(self.title, font_size=self.title_size, color=theme["text"],
                     font=font, pos=(cx, scene.height * 0.2),
                     max_width=int(scene.width * 0.85))
        scene.add(title, enter=start + 0.1, dur=self.duration - 0.5, exit=start + self.duration - 0.4,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.3)

        # Accent line under title
        line = Rect(60, 3, color=theme["accent"],
                    pos=(cx, scene.height * 0.2 + self.title_size // 2 + 15))
        scene.add(line, enter=start + 0.2, dur=self.duration - 0.6, exit=start + self.duration - 0.4,
                  enter_anim="scale_in", exit_anim="fade_out",
                  enter_dur=0.3, exit_dur=0.2)

        # Bullet items
        stagger = 0.2
        item_start_y = scene.height * 0.32
        for i, item in enumerate(self.items):
            y = item_start_y + i * (self.item_size * 2)
            bullet_text = f"{self.bullet_char}  {item}"
            el = Text(bullet_text, font_size=self.item_size, color=theme["text"],
                      font=font, pos=(scene.width * 0.15, y), anchor=(0, 0.5),
                      max_width=int(scene.width * 0.7))
            enter_t = start + 0.3 + i * stagger
            scene.add(el, enter=enter_t,
                      dur=self.duration - 0.5 - i * stagger,
                      exit=start + self.duration - 0.4,
                      enter_anim="fade_left", exit_anim="fade_out",
                      enter_dur=0.3, exit_dur=0.3, enter_easing="ease_out_cubic")

        return start + self.duration


class SummarySlide(Slide):
    """Summary/recap slide showing key items in cards."""

    def __init__(
        self,
        items: List[str],
        title: str = "Summary",
        duration: float = 7.0,
        title_size: int = 52,
        item_size: int = 28,
    ):
        super().__init__(duration)
        self.items = items
        self.title = title
        self.title_size = title_size
        self.item_size = item_size

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        cx = scene.width // 2
        font = kwargs.get("font")

        # Title
        title = Text(self.title, font_size=self.title_size, color=theme["text"],
                     font=font, pos=(cx, scene.height * 0.15))
        scene.add(title, enter=start + 0.1, dur=self.duration - 0.5, exit=start + self.duration - 0.4,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.3)

        # Item cards
        card_w = scene.width * 0.8
        card_h = 70
        stagger = 0.2
        start_y = scene.height * 0.28

        for i, item in enumerate(self.items):
            y = start_y + i * (card_h + 15)
            accent = lerp_color(theme["accent"], theme["accent2"],
                                i / max(1, len(self.items) - 1))

            # Card bg
            card = Rect(card_w, card_h, color=theme["card_bg"],
                        border_radius=12, border_color=accent.hex, border_width=1,
                        pos=(cx, y))
            enter_t = start + 0.3 + i * stagger
            scene.add(card, enter=enter_t, dur=self.duration - 0.5 - i * stagger,
                      exit=start + self.duration - 0.4,
                      enter_anim="fade_up", exit_anim="fade_out",
                      enter_dur=0.3, exit_dur=0.3, enter_easing="ease_out_cubic")

            # Number badge
            badge = Circle(radius=18, color=accent.hex,
                           pos=(cx - card_w / 2 + 30, y))
            scene.add(badge, enter=enter_t + 0.1, dur=self.duration - 0.6 - i * stagger,
                      exit=start + self.duration - 0.4,
                      enter_anim="scale_in", exit_anim="fade_out",
                      enter_dur=0.3, exit_dur=0.2, enter_easing="ease_out_back")

            num_text = Text(str(i + 1), font_size=18, color="#ffffff",
                            font=font, pos=(cx - card_w / 2 + 30, y))
            scene.add(num_text, enter=enter_t + 0.15, dur=self.duration - 0.65 - i * stagger,
                      exit=start + self.duration - 0.4,
                      enter_anim="fade_in", exit_anim="fade_out",
                      enter_dur=0.2, exit_dur=0.2)

            # Item text
            text = Text(item, font_size=self.item_size, color=theme["text"],
                        font=font, pos=(cx + 10, y),
                        max_width=int(card_w - 80))
            scene.add(text, enter=enter_t + 0.15, dur=self.duration - 0.65 - i * stagger,
                      exit=start + self.duration - 0.4,
                      enter_anim="fade_left", exit_anim="fade_out",
                      enter_dur=0.3, exit_dur=0.3)

        return start + self.duration


class ImageSlide(Slide):
    """Slide with a centered image and optional caption."""

    def __init__(
        self,
        image_path: str,
        caption: str = "",
        duration: float = 5.0,
        image_width: Optional[int] = None,
    ):
        super().__init__(duration)
        self.image_path = image_path
        self.caption = caption
        self.image_width = image_width

    def build(self, scene: Scene, start: float, theme: dict, **kwargs) -> float:
        from motion_engine.elements import ImageElement

        cx, cy = scene.width // 2, scene.height // 2
        font = kwargs.get("font")

        img_w = self.image_width or int(scene.width * 0.8)
        img = ImageElement(self.image_path, width=img_w,
                           pos=(cx, cy - 30 if self.caption else cy))
        scene.add(img, enter=start + 0.1, dur=self.duration - 0.4, exit=start + self.duration - 0.3,
                  enter_anim="scale_up", exit_anim="fade_out",
                  enter_dur=0.5, exit_dur=0.3)

        if self.caption:
            cap = Text(self.caption, font_size=28, color=theme["text_secondary"],
                       font=font, pos=(cx, cy + img.get_bounds()[1] // 2 + 30))
            scene.add(cap, enter=start + 0.4, dur=self.duration - 0.7, exit=start + self.duration - 0.3,
                      enter_anim="fade_up", exit_anim="fade_out",
                      enter_dur=0.3, exit_dur=0.3)

        return start + self.duration


class SlideDeck:
    """Compose multiple slides into a presentation with transitions.

    Usage:
        deck = SlideDeck(theme="dark_purple")
        deck.add(TitleSlide("Hello", subtitle="World"))
        deck.add(StepSlide(number="01", title="Step One", desc="Do stuff"))
        deck.add(SummarySlide(items=["Step 1", "Step 2"]))
        deck.render("output.mp4")
    """

    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
        theme: str = "dark_purple",
        transition_dur: float = 0.6,
        font: Optional[str] = None,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.theme_name = theme
        self.theme = THEMES.get(theme, THEMES["dark_purple"])
        self.transition_dur = transition_dur
        self.font = font
        self.slides: List[Slide] = []

    def add(self, slide: Slide) -> "SlideDeck":
        """Add a slide to the deck."""
        self.slides.append(slide)
        return self

    def render(self, output_path: str, show_progress: bool = True) -> str:
        """Render the full deck to MP4."""
        scene = Scene(self.width, self.height, fps=self.fps, bg=self.theme["bg"])

        t = 0.0
        for i, slide in enumerate(self.slides):
            t = slide.build(scene, start=t, theme=self.theme, font=self.font)

            # Add transition between slides (not after last)
            if i < len(self.slides) - 1:
                dissolve_transition(scene, start=t - 0.3, dur=self.transition_dur)

        scene.duration = t + 0.5
        scene.render(output_path, show_progress=show_progress)
        return output_path
