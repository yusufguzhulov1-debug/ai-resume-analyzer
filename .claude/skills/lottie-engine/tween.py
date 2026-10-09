"""Keyframe interpolation engine."""

from __future__ import annotations
import bisect
from typing import List, Tuple

from motion_engine.easing import get_easing, EasingFn


class Keyframe:
    """A single keyframe: time, value, easing to next keyframe."""

    __slots__ = ("time", "value", "easing")

    def __init__(self, time: float, value: float, easing: str = "linear"):
        self.time = time
        self.value = value
        self.easing = easing

    def __repr__(self):
        return f"KF(t={self.time}, v={self.value}, e={self.easing})"


class KeyframeTrack:
    """Ordered list of keyframes with interpolation.

    Handles:
    - Before first keyframe: hold first value
    - After last keyframe: hold last value
    - Between keyframes: interpolate using the starting keyframe's easing
    """

    def __init__(self):
        self._keyframes: List[Keyframe] = []
        self._times: List[float] = []  # kept in sync for bisect

    def add(self, time: float, value: float, easing: str = "linear"):
        """Add a keyframe. If time already exists, update it."""
        # Check for existing keyframe at this time
        for i, kf in enumerate(self._keyframes):
            if abs(kf.time - time) < 1e-6:
                self._keyframes[i] = Keyframe(time, value, easing)
                return

        kf = Keyframe(time, value, easing)
        idx = bisect.bisect_left(self._times, time)
        self._keyframes.insert(idx, kf)
        self._times.insert(idx, time)

    def get_value(self, t: float) -> float:
        """Get interpolated value at time t."""
        n = len(self._keyframes)
        if n == 0:
            return 0.0
        if n == 1:
            return self._keyframes[0].value

        # Before first keyframe
        if t <= self._keyframes[0].time:
            return self._keyframes[0].value

        # After last keyframe
        if t >= self._keyframes[-1].time:
            return self._keyframes[-1].value

        # Find surrounding keyframes
        idx = bisect.bisect_right(self._times, t) - 1
        idx = max(0, min(idx, n - 2))

        kf_a = self._keyframes[idx]
        kf_b = self._keyframes[idx + 1]

        # Calculate progress
        dt = kf_b.time - kf_a.time
        if dt <= 0:
            return kf_b.value

        raw_t = (t - kf_a.time) / dt
        easing_fn = get_easing(kf_a.easing)
        eased_t = easing_fn(raw_t)

        # Linear interpolation with eased progress
        return kf_a.value + (kf_b.value - kf_a.value) * eased_t

    @property
    def keyframes(self) -> List[Keyframe]:
        return self._keyframes

    def to_dict(self) -> list:
        return [
            {"time": kf.time, "value": kf.value, "easing": kf.easing}
            for kf in self._keyframes
        ]

    @classmethod
    def from_dict(cls, data: list) -> "KeyframeTrack":
        track = cls()
        for kf_data in data:
            track.add(kf_data["time"], kf_data["value"], kf_data.get("easing", "linear"))
        return track
