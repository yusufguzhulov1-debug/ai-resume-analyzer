"""Animatable properties: opacity, position, scale, rotation, color."""

from __future__ import annotations
from typing import Any, Dict

from .tween import KeyframeTrack


class AnimatableProperty:
    """A named property with keyframe animation support."""

    def __init__(self, name: str, default: float = 0.0):
        self.name = name
        self.default = default
        self.track = KeyframeTrack()

    def add_keyframe(self, time: float, value: float, easing: str = "linear"):
        """Add a keyframe to this property."""
        self.track.add(time, value, easing)

    def get_value(self, time: float) -> float:
        """Get interpolated value at time. Returns default if no keyframes."""
        if not self.track.keyframes:
            return self.default
        return self.track.get_value(time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "default": self.default,
            "keyframes": self.track.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimatableProperty":
        prop = cls(name=data["name"], default=data.get("default", 0.0))
        prop.track = KeyframeTrack.from_dict(data.get("keyframes", []))
        return prop
