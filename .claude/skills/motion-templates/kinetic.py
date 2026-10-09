"""Kinetic typography templates — word-by-word reveal, scale-burst, typewriter."""

from __future__ import annotations
from typing import Optional, List, Tuple

from motion_engine.scene import Scene
from motion_engine.elements import Text, Rect
from motion_engine.color import ColorLike


def word_by_word(
    scene: Scene,
    text: str,
    pos: Tuple[float, float] = (540, 960),
    font_size: int = 72,
    color: ColorLike = "#ffffff",
    font: Optional[str] = None,
    start: float = 0.0,
    word_dur: float = 0.6,
    word_gap: float = 0.15,
    enter_anim: str = "fade_up",
    exit_anim: str = "fade_out",
    enter_easing: str = "ease_out_back",
    hold_after: float = 1.0,
) -> float:
    """Reveal text word by word with animation.

    Returns the total end time.
    """
    words = text.split()
    if not words:
        return start

    t = start
    for word in words:
        el = Text(word, font_size=font_size, color=color, font=font, pos=pos)
        exit_time = t + word_dur
        scene.add(
            el,
            enter=t,
            dur=word_dur,
            exit=exit_time,
            enter_anim=enter_anim,
            exit_anim=exit_anim,
            enter_dur=0.3,
            exit_dur=0.2,
            enter_easing=enter_easing,
        )
        t += word_gap + 0.1

    return t + hold_after


def scale_burst(
    scene: Scene,
    text: str,
    pos: Tuple[float, float] = (540, 960),
    font_size: int = 120,
    color: ColorLike = "#ffffff",
    font: Optional[str] = None,
    start: float = 0.0,
    dur: float = 0.8,
    hold: float = 1.5,
) -> float:
    """Text appears with a dramatic scale burst effect.

    Returns the end time.
    """
    el = Text(text, font_size=font_size, color=color, font=font, pos=pos)
    scene.add(
        el,
        enter=start,
        dur=hold,
        exit=start + dur + hold,
        enter_anim="bounce_in",
        exit_anim="scale_out",
        enter_dur=dur,
        exit_dur=0.3,
        enter_easing="ease_out_elastic",
    )
    return start + dur + hold + 0.3


def typewriter(
    scene: Scene,
    text: str,
    pos: Tuple[float, float] = (540, 960),
    font_size: int = 48,
    color: ColorLike = "#ffffff",
    font: Optional[str] = None,
    start: float = 0.0,
    char_delay: float = 0.05,
    cursor: bool = True,
    cursor_color: ColorLike = "#7c6aff",
    hold_after: float = 1.0,
    max_width: Optional[int] = None,
) -> float:
    """Typewriter effect — characters appear one by one.

    Implemented by showing progressively longer substrings.
    Returns the end time.
    """
    total_chars = len(text)
    typing_dur = total_chars * char_delay
    # Show the full text element, but use per-frame callback for the reveal
    full_text = Text(
        text, font_size=font_size, color=color, font=font,
        pos=pos, max_width=max_width, align="left",
    )

    # We'll show partial text by creating text elements for each step
    # Simpler approach: show a series of text snapshots
    step = max(1, total_chars // 30)  # Limit number of elements
    snapshots = []
    for i in range(0, total_chars + 1, step):
        i = min(i, total_chars)
        if i == 0:
            continue
        substring = text[:i]
        t_start = start + (i - step) * char_delay
        t_end = start + i * char_delay

        el = Text(
            substring, font_size=font_size, color=color, font=font,
            pos=pos, max_width=max_width, align="left",
        )
        # Each snapshot appears at its time and disappears when next appears
        if i < total_chars:
            scene.add(el, enter=t_start, dur=t_end - t_start, exit=t_end,
                       enter_anim="none", exit_anim="none", enter_dur=0.01, exit_dur=0.01)
        else:
            # Last snapshot stays
            scene.add(el, enter=t_start, dur=hold_after + 0.5, exit=t_start + hold_after,
                       enter_anim="none", exit_anim="fade_out", enter_dur=0.01, exit_dur=0.3)

    # Cursor blink
    if cursor:
        cursor_el = Rect(3, font_size, color=cursor_color, pos=(pos[0] + 10, pos[1]))
        scene.add(
            cursor_el,
            enter=start,
            dur=typing_dur + hold_after,
            exit=start + typing_dur + hold_after,
            enter_anim="none",
            exit_anim="fade_out",
            enter_dur=0.01,
            exit_dur=0.2,
        )

    return start + typing_dur + hold_after + 0.3


def text_stack(
    scene: Scene,
    lines: List[str],
    center: Tuple[float, float] = (540, 960),
    font_size: int = 56,
    color: ColorLike = "#ffffff",
    font: Optional[str] = None,
    start: float = 0.0,
    line_gap: float = 0.2,
    line_height: float = 1.5,
    enter_anim: str = "fade_up",
    hold: float = 2.0,
) -> float:
    """Stack multiple lines with staggered entrance.

    Returns the end time.
    """
    total_height = len(lines) * font_size * line_height
    start_y = center[1] - total_height / 2

    t = start
    end_times = []
    for i, line in enumerate(lines):
        y = start_y + i * font_size * line_height
        el = Text(line, font_size=font_size, color=color, font=font, pos=(center[0], y))
        enter_t = t + i * line_gap
        exit_t = enter_t + hold + (len(lines) - i) * line_gap
        scene.add(
            el,
            enter=enter_t,
            dur=hold,
            exit=exit_t,
            enter_anim=enter_anim,
            exit_anim="fade_out",
            enter_dur=0.4,
            exit_dur=0.3,
            enter_easing="ease_out_cubic",
        )
        end_times.append(exit_t + 0.3)

    return max(end_times) if end_times else start
