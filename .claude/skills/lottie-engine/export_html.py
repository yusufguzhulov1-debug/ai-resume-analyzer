"""Export Animation to self-contained interactive HTML."""

from __future__ import annotations
import json
import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Animation


def export_animation_html(anim: "Animation", output_path: str) -> str:
    """Export animation to a self-contained HTML file with CSS animations.

    Generates a standalone HTML file that plays the animation using
    CSS keyframes and JavaScript timing. No external dependencies.
    """
    anim_data = anim.to_dict()

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Animation</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #000; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
.stage {{
  width: {anim.width}px;
  height: {anim.height}px;
  background: {anim.bg};
  position: relative;
  overflow: hidden;
  max-width: 100vw;
  max-height: 100vh;
}}
.layer {{
  position: absolute;
  will-change: transform, opacity;
}}
.controls {{
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  gap: 10px;
}}
.controls button {{
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}}
.controls button:hover {{ background: rgba(255,255,255,0.3); }}
.timeline {{
  position: fixed;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  max-width: 600px;
}}
.timeline input {{
  width: 100%;
  accent-color: #7c6aff;
}}
</style>
</head>
<body>
<div class="stage" id="stage"></div>
<div class="timeline">
  <input type="range" id="scrubber" min="0" max="1000" value="0">
</div>
<div class="controls">
  <button id="playBtn" onclick="togglePlay()">Play</button>
  <button onclick="restart()">Restart</button>
</div>

<script>
const ANIM_DATA = {json.dumps(anim_data)};
const DURATION = ANIM_DATA.duration * 1000; // ms
const FPS = ANIM_DATA.fps;

// Easing functions
const easings = {{
  linear: t => t,
  ease_in_sine: t => 1 - Math.cos(t * Math.PI / 2),
  ease_out_sine: t => Math.sin(t * Math.PI / 2),
  ease_in_out_sine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  ease_in_quad: t => t * t,
  ease_out_quad: t => 1 - (1 - t) ** 2,
  ease_in_out_quad: t => t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2,
  ease_in_cubic: t => t ** 3,
  ease_out_cubic: t => 1 - (1 - t) ** 3,
  ease_in_out_cubic: t => t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2,
  ease_in_back: t => {{ const c = 1.70158; return (c + 1) * t ** 3 - c * t * t; }},
  ease_out_back: t => {{ const c = 1.70158; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2; }},
  ease_in_out_back: t => {{
    const c = 1.70158 * 1.525;
    return t < 0.5
      ? ((2 * t) ** 2 * ((c + 1) * 2 * t - c)) / 2
      : ((2 * t - 2) ** 2 * ((c + 1) * (t * 2 - 2) + c) + 2) / 2;
  }},
  ease_out_elastic: t => {{
    if (t === 0 || t === 1) return t;
    return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1;
  }},
  ease_out_bounce: t => {{
    const n1 = 7.5625, d1 = 2.75;
    if (t < 1 / d1) return n1 * t * t;
    else if (t < 2 / d1) return n1 * (t -= 1.5 / d1) * t + 0.75;
    else if (t < 2.5 / d1) return n1 * (t -= 2.25 / d1) * t + 0.9375;
    else return n1 * (t -= 2.625 / d1) * t + 0.984375;
  }},
}};

function getEasing(name) {{
  return easings[name] || easings.linear;
}}

function interpolateKeyframes(keyframes, time) {{
  if (!keyframes || keyframes.length === 0) return 0;
  if (keyframes.length === 1) return keyframes[0].value;
  if (time <= keyframes[0].time) return keyframes[0].value;
  if (time >= keyframes[keyframes.length - 1].time) return keyframes[keyframes.length - 1].value;

  for (let i = 0; i < keyframes.length - 1; i++) {{
    const a = keyframes[i], b = keyframes[i + 1];
    if (time >= a.time && time <= b.time) {{
      const dt = b.time - a.time;
      if (dt <= 0) return b.value;
      const rawT = (time - a.time) / dt;
      const easedT = getEasing(a.easing)(rawT);
      return a.value + (b.value - a.value) * easedT;
    }}
  }}
  return keyframes[keyframes.length - 1].value;
}}

// Create layer DOM elements
const stage = document.getElementById('stage');
const layerEls = [];

ANIM_DATA.layers.forEach((layer, i) => {{
  const el = document.createElement('div');
  el.className = 'layer';
  el.id = 'layer-' + i;
  el.style.fontSize = '48px';
  el.style.color = 'white';
  el.style.fontFamily = 'Helvetica, Arial, sans-serif';
  el.textContent = layer.name;
  stage.appendChild(el);
  layerEls.push(el);
}});

let playing = false;
let startTime = 0;
let currentTime = 0;
const scrubber = document.getElementById('scrubber');

function updateFrame(time) {{
  const t = time / 1000; // to seconds

  ANIM_DATA.layers.forEach((layer, i) => {{
    const el = layerEls[i];
    const props = layer.properties;

    const opacity = props.opacity ? interpolateKeyframes(props.opacity.keyframes, t) : 1;
    const x = props.x ? interpolateKeyframes(props.x.keyframes, t) : 0;
    const y = props.y ? interpolateKeyframes(props.y.keyframes, t) : 0;
    const scale = props.scale ? interpolateKeyframes(props.scale.keyframes, t) : 1;
    const rotation = props.rotation ? interpolateKeyframes(props.rotation.keyframes, t) : 0;

    el.style.opacity = opacity;
    el.style.transform = `translate(${{x}}px, ${{y}}px) scale(${{scale}}) rotate(${{rotation}}deg)`;
  }});

  scrubber.value = (time / DURATION) * 1000;
}}

function animate(timestamp) {{
  if (!playing) return;
  currentTime = timestamp - startTime;
  if (currentTime >= DURATION) {{
    currentTime = DURATION;
    playing = false;
    document.getElementById('playBtn').textContent = 'Play';
  }}
  updateFrame(currentTime);
  if (playing) requestAnimationFrame(animate);
}}

function togglePlay() {{
  if (playing) {{
    playing = false;
    document.getElementById('playBtn').textContent = 'Play';
  }} else {{
    playing = true;
    startTime = performance.now() - currentTime;
    document.getElementById('playBtn').textContent = 'Pause';
    requestAnimationFrame(animate);
  }}
}}

function restart() {{
  currentTime = 0;
  startTime = performance.now();
  updateFrame(0);
  if (!playing) {{
    playing = true;
    document.getElementById('playBtn').textContent = 'Pause';
    requestAnimationFrame(animate);
  }}
}}

scrubber.addEventListener('input', (e) => {{
  playing = false;
  document.getElementById('playBtn').textContent = 'Play';
  currentTime = (e.target.value / 1000) * DURATION;
  updateFrame(currentTime);
}});

// Initial frame
updateFrame(0);
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html_content)

    return output_path
