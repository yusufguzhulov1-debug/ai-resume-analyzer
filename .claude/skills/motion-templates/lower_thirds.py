"""Lower thirds, title cards, and name plate templates."""

from __future__ import annotations
from typing import Optional, Tuple

from motion_engine.scene import Scene
from motion_engine.elements import Text, Rect, GradientRect
from motion_engine.color import ColorLike


def lower_third(
    scene: Scene,
    name: str,
    title: str = "",
    pos: Tuple[float, float] = (100, 1600),
    start: float = 0.0,
    hold: float = 4.0,
    bar_color: ColorLike = "#7c6aff",
    bg_color: ColorLike = "#1a1a2e",
    text_color: ColorLike = "#ffffff",
    name_size: int = 36,
    title_size: int = 24,
    width: float = 500,
    font: Optional[str] = None,
) -> float:
    """Animated lower third with name and optional title.

    Returns end time.
    """
    # Accent bar
    bar = Rect(4, 70, color=bar_color, pos=(pos[0], pos[1]), anchor=(0, 0))
    scene.add(bar, enter=start, dur=hold, exit=start + hold,
              enter_anim="scale_in", exit_anim="scale_out",
              enter_dur=0.3, exit_dur=0.2, enter_easing="ease_out_back")

    # Background
    bg = Rect(width, 70, color=bg_color, border_radius=4,
              pos=(pos[0] + 10, pos[1]), anchor=(0, 0))
    bg.opacity = 0.85
    scene.add(bg, enter=start + 0.1, dur=hold - 0.2, exit=start + hold - 0.1,
              enter_anim="slide_right", exit_anim="fade_out",
              enter_dur=0.3, exit_dur=0.2, enter_easing="ease_out_cubic")

    # Name
    name_el = Text(name, font_size=name_size, color=text_color, font=font,
                   pos=(pos[0] + 25, pos[1] + 15 if title else pos[1] + 22),
                   anchor=(0, 0))
    scene.add(name_el, enter=start + 0.2, dur=hold - 0.4, exit=start + hold - 0.2,
              enter_anim="fade_right", exit_anim="fade_out",
              enter_dur=0.3, exit_dur=0.2)

    # Title (optional)
    if title:
        title_el = Text(title, font_size=title_size, color=text_color, font=font,
                        pos=(pos[0] + 25, pos[1] + 45), anchor=(0, 0))
        title_el.opacity = 0.7
        scene.add(title_el, enter=start + 0.3, dur=hold - 0.5, exit=start + hold - 0.2,
                  enter_anim="fade_right", exit_anim="fade_out",
                  enter_dur=0.3, exit_dur=0.2)

    return start + hold + 0.2


def title_card(
    scene: Scene,
    title: str,
    subtitle: str = "",
    pos: Tuple[float, float] = (540, 960),
    start: float = 0.0,
    hold: float = 3.0,
    title_size: int = 80,
    subtitle_size: int = 36,
    title_color: ColorLike = "#ffffff",
    subtitle_color: ColorLike = "#aaaacc",
    accent_color: ColorLike = "#7c6aff",
    font: Optional[str] = None,
    show_line: bool = True,
) -> float:
    """Full-screen title card with optional subtitle and accent line.

    Returns end time.
    """
    # Title
    title_el = Text(title, font_size=title_size, color=title_color, font=font,
                    pos=(pos[0], pos[1] - 30 if subtitle else pos[1]))
    scene.add(title_el, enter=start, dur=hold, exit=start + hold,
              enter_anim="fade_up", exit_anim="fade_out",
              enter_dur=0.5, exit_dur=0.3, enter_easing="ease_out_cubic")

    # Accent line
    if show_line:
        line = Rect(80, 4, color=accent_color,
                    pos=(pos[0], pos[1] + title_size // 2 - 10 if subtitle else pos[1] + title_size // 2 + 10))
        scene.add(line, enter=start + 0.2, dur=hold - 0.4, exit=start + hold - 0.2,
                  enter_anim="scale_in", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.2, enter_easing="ease_out_back")

    # Subtitle
    if subtitle:
        sub_el = Text(subtitle, font_size=subtitle_size, color=subtitle_color, font=font,
                      pos=(pos[0], pos[1] + title_size // 2 + 20))
        scene.add(sub_el, enter=start + 0.3, dur=hold - 0.5, exit=start + hold - 0.2,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.4, exit_dur=0.3)

    return start + hold + 0.3


def name_plate(
    scene: Scene,
    name: str,
    role: str = "",
    pos: Tuple[float, float] = (540, 1500),
    start: float = 0.0,
    hold: float = 3.0,
    bg_start: ColorLike = "#7c6aff",
    bg_end: ColorLike = "#5a4fcf",
    text_color: ColorLike = "#ffffff",
    name_size: int = 32,
    role_size: int = 22,
    width: float = 400,
    height: float = 70,
    font: Optional[str] = None,
) -> float:
    """Rounded name plate with gradient background.

    Returns end time.
    """
    bg = GradientRect(width, height, start_color=bg_start, end_color=bg_end,
                      border_radius=12, pos=pos)
    scene.add(bg, enter=start, dur=hold, exit=start + hold,
              enter_anim="slide_up", exit_anim="fade_out",
              enter_dur=0.4, exit_dur=0.3, enter_easing="ease_out_back")

    name_el = Text(name, font_size=name_size, color=text_color, font=font,
                   pos=(pos[0], pos[1] - 8 if role else pos[1]))
    scene.add(name_el, enter=start + 0.15, dur=hold - 0.3, exit=start + hold - 0.15,
              enter_anim="fade_up", exit_anim="fade_out",
              enter_dur=0.3, exit_dur=0.2)

    if role:
        role_el = Text(role, font_size=role_size, color=text_color, font=font,
                       pos=(pos[0], pos[1] + 16))
        role_el.opacity = 0.8
        scene.add(role_el, enter=start + 0.25, dur=hold - 0.4, exit=start + hold - 0.15,
                  enter_anim="fade_up", exit_anim="fade_out",
                  enter_dur=0.3, exit_dur=0.2)

    return start + hold + 0.3
