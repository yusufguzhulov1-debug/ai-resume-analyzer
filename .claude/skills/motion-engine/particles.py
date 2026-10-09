"""Particle system engine using numpy vectorized operations."""

from __future__ import annotations
import math
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from .color import Color, parse_color, lerp_color, ColorLike


class ParticleSystem:
    """GPU-friendly (numpy vectorized) particle emitter.

    Usage:
        ps = ParticleSystem(max_particles=500, emit_rate=50)
        ps.emit_pos = (540, 960)
        ps.color_start = "#7c6aff"
        ps.color_end = "#ff6ab0"
        # Each frame:
        ps.update(dt)
        ps.draw(canvas)
    """

    def __init__(
        self,
        max_particles: int = 500,
        emit_rate: float = 50,
        lifetime: float = 2.0,
        lifetime_var: float = 0.5,
        speed: float = 100,
        speed_var: float = 30,
        direction: float = -90,  # degrees, -90 = upward
        spread: float = 360,  # degrees
        gravity: float = 0,
        size_start: float = 4,
        size_end: float = 0,
        color_start: ColorLike = "#ffffff",
        color_end: Optional[ColorLike] = None,
        fade_out: bool = True,
    ):
        self.max_particles = max_particles
        self.emit_rate = emit_rate
        self.lifetime_base = lifetime
        self.lifetime_var = lifetime_var
        self.speed = speed
        self.speed_var = speed_var
        self.direction = direction
        self.spread = spread
        self.gravity = gravity
        self.size_start = size_start
        self.size_end = size_end
        self.color_start = parse_color(color_start)
        self.color_end = parse_color(color_end) if color_end else None
        self.fade_out = fade_out

        self.emit_pos: Tuple[float, float] = (0, 0)
        self.emit_size: Tuple[float, float] = (0, 0)  # area randomization
        self.active = True

        # Particle arrays
        self._pos = np.zeros((max_particles, 2), dtype=np.float32)
        self._vel = np.zeros((max_particles, 2), dtype=np.float32)
        self._life = np.zeros(max_particles, dtype=np.float32)  # remaining
        self._max_life = np.zeros(max_particles, dtype=np.float32)  # total
        self._alive = np.zeros(max_particles, dtype=bool)
        self._emit_accum = 0.0

    @property
    def alive_count(self) -> int:
        return int(np.sum(self._alive))

    def update(self, dt: float):
        """Advance simulation by dt seconds."""
        # Update alive particles
        alive = self._alive
        if np.any(alive):
            self._life[alive] -= dt
            self._vel[alive, 1] += self.gravity * dt
            self._pos[alive] += self._vel[alive] * dt
            # Kill expired
            expired = alive & (self._life <= 0)
            self._alive[expired] = False

        # Emit new particles
        if self.active and self.emit_rate > 0:
            self._emit_accum += self.emit_rate * dt
            to_emit = int(self._emit_accum)
            self._emit_accum -= to_emit
            if to_emit > 0:
                self._emit(to_emit)

    def _emit(self, count: int):
        """Spawn new particles."""
        dead = np.where(~self._alive)[0]
        count = min(count, len(dead))
        if count == 0:
            return

        idx = dead[:count]
        self._alive[idx] = True

        # Lifetime
        lf = self.lifetime_base + (np.random.random(count) - 0.5) * 2 * self.lifetime_var
        self._life[idx] = np.maximum(lf, 0.1)
        self._max_life[idx] = self._life[idx]

        # Position
        self._pos[idx, 0] = self.emit_pos[0] + (np.random.random(count) - 0.5) * self.emit_size[0]
        self._pos[idx, 1] = self.emit_pos[1] + (np.random.random(count) - 0.5) * self.emit_size[1]

        # Velocity
        dir_rad = math.radians(self.direction)
        spread_rad = math.radians(self.spread)
        angles = dir_rad + (np.random.random(count) - 0.5) * spread_rad
        speeds = self.speed + (np.random.random(count) - 0.5) * 2 * self.speed_var
        self._vel[idx, 0] = np.cos(angles) * speeds
        self._vel[idx, 1] = np.sin(angles) * speeds

    def burst(self, count: int, pos: Optional[Tuple[float, float]] = None):
        """Emit a burst of particles at once."""
        if pos:
            old_pos = self.emit_pos
            self.emit_pos = pos
        self._emit(count)
        if pos:
            self.emit_pos = old_pos

    def draw(self, canvas: Image.Image) -> Image.Image:
        """Draw alive particles onto canvas."""
        alive_idx = np.where(self._alive)[0]
        if len(alive_idx) == 0:
            return canvas

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for i in alive_idx:
            t = 1.0 - (self._life[i] / self._max_life[i])  # 0=birth, 1=death
            t = max(0, min(1, t))

            # Size interpolation
            size = self.size_start + (self.size_end - self.size_start) * t
            if size <= 0:
                continue

            # Color
            if self.color_end:
                c = lerp_color(self.color_start, self.color_end, t)
            else:
                c = self.color_start

            # Fade out alpha
            alpha = c.a
            if self.fade_out:
                alpha = int(alpha * (1 - t))
            color = (c.r, c.g, c.b, alpha)

            x, y = self._pos[i]
            half = size / 2
            draw.ellipse(
                [x - half, y - half, x + half, y + half],
                fill=color,
            )

        canvas = Image.alpha_composite(canvas, overlay)
        return canvas
