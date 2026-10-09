"""Animation JSON schema — layers, keyframes, properties."""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from .properties import AnimatableProperty


class Layer:
    """A single animation layer with animatable properties."""

    def __init__(self, name: str, element=None, z_index: int = 0):
        self.name = name
        self.element = element
        self.z_index = z_index
        self.properties: Dict[str, AnimatableProperty] = {}
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Ensure standard properties exist."""
        defaults = {
            "opacity": 1.0,
            "x": 0.0,
            "y": 0.0,
            "scale": 1.0,
            "rotation": 0.0,
        }
        for name, default in defaults.items():
            if name not in self.properties:
                self.properties[name] = AnimatableProperty(name, default)

    def keyframe(self, time: float, easing: str = "linear", **kwargs):
        """Add keyframe(s) at the given time.

        Usage:
            layer.keyframe(0.0, opacity=0, y=1000)
            layer.keyframe(0.5, opacity=1, y=960, easing="ease_out_back")
        """
        for prop_name, value in kwargs.items():
            if prop_name not in self.properties:
                self.properties[prop_name] = AnimatableProperty(prop_name, value)
            self.properties[prop_name].add_keyframe(time, value, easing)
        return self

    def get_value(self, prop_name: str, time: float) -> float:
        """Get interpolated property value at time."""
        if prop_name in self.properties:
            return self.properties[prop_name].get_value(time)
        return 0.0

    def apply_to_element(self, time: float):
        """Apply current property values to the associated element."""
        if self.element is None:
            return

        for prop_name, prop in self.properties.items():
            val = prop.get_value(time)
            if prop_name == "x":
                self.element.x = val
            elif prop_name == "y":
                self.element.y = val
            elif prop_name == "opacity":
                self.element.opacity = val
            elif prop_name == "scale":
                self.element.scale = val
            elif prop_name == "rotation":
                self.element.rotation = val

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "z_index": self.z_index,
            "properties": {
                name: prop.to_dict() for name, prop in self.properties.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layer":
        """Deserialize from dictionary."""
        layer = cls(name=data["name"], z_index=data.get("z_index", 0))
        for name, prop_data in data.get("properties", {}).items():
            layer.properties[name] = AnimatableProperty.from_dict(prop_data)
        return layer


class Animation:
    """Top-level animation container.

    Usage:
        anim = Animation(width=1080, height=1920, duration=5.0, fps=30)
        layer = anim.add_layer("title", element=Text("Hello", size=96))
        layer.keyframe(0.0, opacity=0, y=1000)
        layer.keyframe(0.5, opacity=1, y=960, easing="ease_out_back")
        anim.export_mp4("output.mp4")
    """

    def __init__(
        self,
        width: int = 1080,
        height: int = 1920,
        duration: float = 5.0,
        fps: int = 30,
        bg: str = "#000000",
    ):
        self.width = width
        self.height = height
        self.duration = duration
        self.fps = fps
        self.bg = bg
        self.layers: List[Layer] = []

    def add_layer(self, name: str, element=None, z_index: int = 0) -> Layer:
        """Add a new layer to the animation."""
        layer = Layer(name=name, element=element, z_index=z_index)
        self.layers.append(layer)
        return layer

    def get_layer(self, name: str) -> Optional[Layer]:
        """Find layer by name."""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None

    def export_mp4(self, output_path: str, show_progress: bool = True) -> str:
        """Export animation to MP4 using motion_engine renderer."""
        from .export_mp4 import export_animation_mp4
        return export_animation_mp4(self, output_path, show_progress)

    def export_html(self, output_path: str) -> str:
        """Export animation to self-contained HTML."""
        from .export_html import export_animation_html
        return export_animation_html(self, output_path)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize animation to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "fps": self.fps,
            "bg": self.bg,
            "layers": [layer.to_dict() for layer in self.layers],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_json(self, path: str):
        """Save animation definition to JSON file."""
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Animation":
        """Deserialize from dictionary."""
        anim = cls(
            width=data["width"],
            height=data["height"],
            duration=data["duration"],
            fps=data.get("fps", 30),
            bg=data.get("bg", "#000000"),
        )
        for layer_data in data.get("layers", []):
            layer = Layer.from_dict(layer_data)
            anim.layers.append(layer)
        return anim

    @classmethod
    def load_json(cls, path: str) -> "Animation":
        """Load animation from JSON file."""
        with open(path) as f:
            return cls.from_dict(json.loads(f.read()))
