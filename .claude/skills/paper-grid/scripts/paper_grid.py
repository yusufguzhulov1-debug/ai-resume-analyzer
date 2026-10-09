"""Paper-grid reel builder: white grid pane above the speaker, one animated artifact per spoken beat.

Import from a run's build script (see example_build.py). Everything is frame-based at the reel fps and lands on one
paused GSAP timeline registered as window.__timelines.main. The output is a silent HyperFrames composition; captions
and sound stay separate tracks in your editor.

    reel = Reel(out_dir, camera='assets/camera-clean.mp4', total=1314, split_video_top=-580)
    reel.layouts([('split', 0, 562), ('face', 562, 597), ...])
    with reel.scene('sPost', 0, 152):
        reel.post_card('post', at=0, drop=True, autopilot_at=86)
    reel.compile()
"""
from pathlib import Path
from contextlib import contextmanager
import json, math, os, shutil, subprocess

HERE = Path(__file__).resolve().parent

def find_gsap(start=None):
    """GSAP comes from the workspace runtime that edit-video's `init-workspace.mjs --install` prepares.
    FAVSTASH_GSAP=<path to gsap.min.js> overrides the search."""
    env = os.environ.get('FAVSTASH_GSAP')
    if env and Path(env).is_file():
        return Path(env)
    for base in [Path(start).resolve()] if start else []:
        for p in [base, *base.parents]:
            c = p / '.favstash-studio/runtime/node_modules/gsap/dist/gsap.min.js'
            if c.is_file():
                return c
    for p in [Path.cwd(), *Path.cwd().parents]:
        c = p / '.favstash-studio/runtime/node_modules/gsap/dist/gsap.min.js'
        if c.is_file():
            return c
    raise SystemExit("GSAP not found. Run edit-video's scripts/init-workspace.mjs --workspace <project> --install, "
                     "or set FAVSTASH_GSAP to a local gsap.min.js.")


# ---------------------------------------------------------------- icons (24px grid, stroke)
ICONS = {
    'pen': '<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/><path d="M14.5 5.5l3 3"/>',
    'comment': '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z"/>',
    'reply': '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 6 6v4"/>',
    'check': '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.8 2.8L16.5 9.5"/>',
    'sparkle': '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z"/><path d="M19 16l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7Z"/>',
    'hook': '<path d="M12 3v11a4 4 0 1 1-8 0"/><circle cx="12" cy="3" r="0.5"/><path d="M16 10l4-4M20 10V6h-4"/>',
    'calendar': '<rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    'pulse': '<path d="M3 12h4l2.5-6 5 12 2.5-6H21"/>',
    'user': '<circle cx="12" cy="8.5" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
    'megaphone': '<path d="M4 10v4a1 1 0 0 0 1 1h3l8 4V5L8 9H5a1 1 0 0 0-1 1Z"/><path d="M19.5 9.5a3.5 3.5 0 0 1 0 5"/>',
    'repeat': '<path d="M17 3l3 3-3 3"/><path d="M4 11V9a3 3 0 0 1 3-3h13"/><path d="M7 21l-3-3 3-3"/><path d="M20 13v2a3 3 0 0 1-3 3H4"/>',
    'mic': '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
    'github': '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    'star': '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z"/>',
    'send': '<path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4Z"/>',
    'thumb': '<path d="M7 11v9H4v-9Z"/><path d="M7 11l4-8a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.3 20H7"/>',
    'eye': '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    'lock': '<rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    'note': '<path d="M14 3H6.5A2.5 2.5 0 0 0 4 5.5v13A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V9Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    'bolt': '<path d="M13 2 4 14h7l-1 8 9-12h-7Z"/>',
    'folder': '<path d="M3.5 7a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2Z"/>',
    'code': '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
}


def icon(name, size=40, color='currentColor', width=2):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def claude_mark(size=34):
    rays = ''.join(f'<path d="M12 12 L{12 + 9 * math.cos(a * math.pi / 6):.2f} {12 + 9 * math.sin(a * math.pi / 6):.2f}"/>' for a in range(12))
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24"><g stroke="#D97757" stroke-width="2.6" stroke-linecap="round">{rays}</g></svg>'


# ---------------------------------------------------------------- tokens + base CSS
TOKENS = {
    'paper': '#fbfbfd', 'ink': '#0f172a', 'ink2': '#334155', 'muted': '#64748b', 'faint': '#e7eaf0',
    'line': 'rgba(15,23,42,.055)', 'line2': 'rgba(15,23,42,.10)', 'accent': '#1e40af', 'accent2': '#5b9eff',
    'wash': '#eef3ff', 'rim': 'rgba(15,23,42,.09)', 'red': '#e11d48', 'green': '#16a34a', 'amber': '#d97706',
    'li': '#0a66c2', 'room': '#0b0a1a',
}
CSS = (HERE.parent / 'assets/paper-grid.css').read_text()


class Reel:
    def __init__(self, out, camera, total, fps=30, split_video_top=-580, split_origin='50% 62%', tokens=None, grid_drift=45):
        self.out, self.camera, self.total, self.fps = Path(out), Path(camera), total, fps
        self.split_top, self.split_origin, self.drift = split_video_top, split_origin, grid_drift
        self.tokens = {**TOKENS, **(tokens or {})}
        self.H, self.J, self.media, self.scenes, self.lay = [], [], [], {}, []
        self.extra_css = []
        self.init = []  # gsap.set lines applied before the timeline (frame-0 state)
        self._stack = []

    # ---- time helpers
    def T(self, f):
        return round(f / self.fps, 4)

    def s(self, sel, props, f):
        self.J.append(f"tl.set({json.dumps(sel)},{json.dumps(props)},{self.T(f)});")

    def ft(self, sel, a, b, f, dur, ease='power2.out'):
        self.J.append(f"tl.fromTo({json.dumps(sel)},{json.dumps(a)},{json.dumps({**b, 'duration': dur, 'ease': ease, 'immediateRender': False})},{self.T(f)});")

    def to(self, sel, b, f, dur, ease='power2.out'):
        self.J.append(f"tl.to({json.dumps(sel)},{json.dumps({**b, 'duration': dur, 'ease': ease})},{self.T(f)});")

    def pop(self, sel, f, dur=.35, y=20, scale=.7, ease='back.out(2)'):
        self.ft(sel, {'opacity': 0, 'y': y, 'scale': scale}, {'opacity': 1, 'y': 0, 'scale': 1}, f, dur, ease)

    def rise(self, sel, f, dur=.42, y=50):
        self.ft(sel, {'opacity': 0, 'y': y, 'scale': .96}, {'opacity': 1, 'y': 0, 'scale': 1}, f, dur, 'power3.out')

    def leave(self, sel, f, dur=.2, y=-30):
        self.to(sel, {'opacity': 0, 'y': y}, f, dur, 'power2.in')

    def typed(self, sel, text, f0, f1):
        n = max(1, len(text))
        self.s(sel, {'textContent': ''}, 0)
        for k in range(n + 1):
            self.s(sel, {'textContent': text[:k]}, f0 + (f1 - f0) * k / n)

    def count(self, sel, a, b, f0, f1, suffix=''):
        self.J.append(f"(()=>{{const o={{v:{a}}};tl.fromTo(o,{{v:{a}}},{{v:{b},duration:{self.T(f1 - f0)},ease:'power2.out',immediateRender:false,"
                      f"onUpdate:()=>{{document.querySelector({json.dumps(sel)}).textContent=Math.round(o.v)+{json.dumps(suffix)}}}}},{self.T(f0)});}})();")
        self.s(sel, {'textContent': f'{a}{suffix}'}, max(0, f0 - 1)); self.s(sel, {'textContent': f'{b}{suffix}'}, f1 + 1)

    def blink(self, sel, f0, f1, period=14):
        for f in range(f0, f1, period):
            self.s(sel, {'opacity': 1}, f); self.s(sel, {'opacity': 0}, f + period // 2)

    def add(self, html):
        (self._stack[-1] if self._stack else self.H).append(html)

    def css(self, text):
        self.extra_css.append(text)

    # ---- structure
    def layouts(self, spans):
        """[(layout, start, end)] with layout in {'split','face'}; must cover [0,total)."""
        self.lay = spans
        assert spans[0][1] == 0 and spans[-1][2] == self.total, 'layouts must cover the whole reel'

    @contextmanager
    def scene(self, sid, a, b):
        self.scenes[sid] = (a, b)
        buf = []
        self._stack.append(buf)
        try:
            yield
        finally:
            self._stack.pop()
            self.H.append(f'<section id="{sid}" class="scene">' + ''.join(buf) + '</section>')

    def image(self, src):
        src = Path(src)
        self.media.append(src)
        return f'assets/{src.name}'

    # ---------------------------------------------------------------- components
    def chip(self, cid, text, ic=None, at=None, out=None, top=282, logo=None, glow_at=None, hidden=True):
        lead = logo or (f'<div class="ic">{icon(ic, 26)}</div>' if ic else '')
        op = 'opacity:0;' if hidden and at is not None else ''
        self.add(f'<div class="chip cchip" id="{cid}" style="top:{top}px;{op}">{lead}<span>{text}</span></div>')
        if at is not None:
            self.ft(f'#{cid}', {'opacity': 0, 'x': 60}, {'opacity': 1, 'x': 0}, at, .35, 'power3.out')
        if glow_at is not None:
            self.ft(f'#{cid}', {'boxShadow': '0 12px 26px -10px rgba(15,23,42,.25)'}, {'boxShadow': '0 0 70px 10px rgba(91,158,255,.5)'}, glow_at, .35, 'power1.inOut')
        if out is not None:
            self.to(f'#{cid}', {'opacity': 0, 'x': -60}, out, .2, 'power2.in')

    def live_chip(self, cid, text, until, top=282):
        """Visible from the scene's first frame with a pulsing red dot ("Just dropped", "New"). Use on frame 1."""
        self.add(f'<div class="chip cchip" id="{cid}" style="top:{top}px"><i class="livedot" id="{cid}Dot"></i><span>{text}</span></div>')
        for f in range(0, until, 14):
            self.ft(f'#{cid}Dot', {'scale': 1, 'opacity': 1}, {'scale': .5, 'opacity': .35}, f, .23, 'sine.inOut')
        self.to(f'#{cid}', {'opacity': 0, 'y': -12}, until, .15, 'power2.in')

    def post_card(self, pid, at, drop=False, top=360, stack_at=None, autopilot_at=None, counts=None, bubbles=(), badge=True):
        """Skeleton social post. drop=True: already on screen at `at` and settling (safe for frame 1).
        counts=((likes, comments, reposts), f0, f1); bubbles=[(text, frame, left, top)]."""
        if stack_at is not None:
            self.add(f'<div class="card ghost" id="{pid}G1" style="top:{top}px"></div><div class="card ghost" id="{pid}G2" style="top:{top}px"></div>')
        auto = (f'<div class="autoPill" id="{pid}Auto"><span>Autopilot</span><div class="autoTrack" id="{pid}Trk"><div class="autoKnob" id="{pid}Knob"></div></div></div>'
                if autopilot_at is not None else '')
        lines = ''.join(f'<div class="bar" id="{pid}L{i}" style="left:34px;top:{134 + i * 34}px;width:{w}px"></div>' for i, w in enumerate([660, 620, 672, 420]))
        acts = (f'<div class="act" style="left:34px">{icon("thumb", 30, "#0a66c2", 2.2)}<span id="{pid}N0">0</span></div>'
                f'<div class="act" style="left:210px">{icon("comment", 30, "#334155", 2.2)}<span id="{pid}N1">0</span></div>'
                f'<div class="act" style="left:380px">{icon("repeat", 30, "#334155", 2.2)}<span id="{pid}N2">0</span></div>'
                f'<div class="act" style="left:560px">{icon("send", 30, "#334155", 2.2)}</div>')
        bdg = '<div style="position:absolute;right:30px;bottom:30px"><div class="inbadge">in</div></div>' if badge else ''
        vis = '' if drop else 'opacity:0;'
        self.add(f'<div class="card postcard" id="{pid}" style="top:{top}px;{vis}"><div class="av" style="left:34px;top:30px;width:70px;height:70px"></div>'
                 '<div class="bar" style="left:122px;top:40px;width:190px;height:18px;background:#cbd5e1"></div>'
                 f'<div class="bar" style="left:122px;top:72px;width:120px;height:12px"></div>{auto}{lines}'
                 f'<div class="pmedia" id="{pid}M"></div>{acts}{bdg}</div>')
        for k, (txt, f, left, btop) in enumerate(bubbles):
            self.add(f'<div class="bub" id="{pid}B{k}" style="left:{left}px;top:{btop}px">{txt}</div>')
            self.pop(f'#{pid}B{k}', f)
        if drop:
            self.ft(f'#{pid}', {'y': -70, 'opacity': 1, 'scale': 1.03}, {'y': 0, 'opacity': 1, 'scale': 1}, at, .55, 'back.out(1.4)')
            for i in range(4):
                self.ft(f'#{pid}L{i}', {'scaleX': .35 if i < 2 else 0}, {'scaleX': 1}, at + i * 5, .35)
        else:
            self.ft(f'#{pid}', {'y': 60, 'opacity': 0, 'scale': .94}, {'y': 0, 'opacity': 1, 'scale': 1}, at, .45, 'power3.out')
            for i in range(4):
                self.ft(f'#{pid}L{i}', {'scaleX': 0}, {'scaleX': 1}, at + 4 + i * 4, .3)
        self.ft(f'#{pid}M', {'opacity': 0, 'y': 10}, {'opacity': 1, 'y': 0}, at + 18, .3)
        if stack_at is not None:
            self.ft(f'#{pid}G1', {'x': 0, 'rotation': 0, 'opacity': 0}, {'x': -34, 'y': 18, 'rotation': -5, 'opacity': 1}, stack_at, .4, 'back.out(1.6)')
            self.ft(f'#{pid}G2', {'x': 0, 'rotation': 0, 'opacity': 0}, {'x': 34, 'y': 10, 'rotation': 4, 'opacity': 1}, stack_at + 2, .4, 'back.out(1.6)')
        if autopilot_at is not None:
            self.to(f'#{pid}Trk', {'backgroundColor': self.tokens['green']}, autopilot_at, .2)
            self.to(f'#{pid}Knob', {'x': 28}, autopilot_at, .22)
            self.to(f'#{pid}Auto', {'color': self.tokens['green']}, autopilot_at, .2)
        if counts:
            (a, b, c), f0, f1 = counts
            for k, v in enumerate((a, b, c)):
                self.count(f'#{pid}N{k}', 0, v, f0 + k * 4, f1)

    def big_number(self, bid, text, at, chips=(), burst=True):
        """Hero figure ("$0", "12x") with a row of chips and an optional dot burst. `text` may hold a <span> accent."""
        self.add(f'<div class="bigno" id="{bid}">{text}</div><div class="chiprow" style="top:690px">'
                 + ''.join(f'<div class="chip rel" id="{bid}C{k}"><div class="ic">{icon(ic, 26)}</div>{t}</div>' for k, (ic, t) in enumerate(chips)) + '</div>')
        self.ft(f'#{bid}', {'scale': .55, 'opacity': 0}, {'scale': 1, 'opacity': 1}, at, .42, 'back.out(1.8)')
        for k in range(len(chips)):
            self.ft(f'#{bid}C{k}', {'opacity': 0, 'y': 24}, {'opacity': 1, 'y': 0}, at + 8 + k * 4, .3, 'power3.out')
        if burst:
            for k in range(12):
                col = ['#5b9eff', '#1e40af', '#93c5fd', '#0a66c2'][k % 4]
                self.add(f'<div class="dot" id="{bid}D{k}" style="background:{col}"></div>')
                ang = k / 12 * 2 * math.pi + .3; dist = 300 + (k % 3) * 60
                self.ft(f'#{bid}D{k}', {'x': 0, 'y': 0, 'opacity': 1, 'scale': 1}, {'x': dist * math.cos(ang), 'y': dist * .72 * math.sin(ang), 'opacity': 0, 'scale': .4}, at + 12, .7)

    def proof_list(self, lid, img, img_w, n_rows, row_px, first_row_center, at, expand_at, focus_row=0, scale=1.18,
                   label=None, counter=('SKILL', 'SKILLS'), top=300):
        """Real list screenshot (e.g. a repo folder): one focused row, then the whole list with a 1->n counter.
        img_w/row_px/first_row_center are in the screenshot's CSS pixels (1x)."""
        disp_w = img_w * scale; row = row_px * scale
        h_img = (first_row_center + row_px * (n_rows - 1) + row_px / 2 + 8) * scale
        src = self.image(img)
        self.add(f'<div class="cntWrap" id="{lid}W"><div class="cnt" id="{lid}N">1</div><div class="cntLbl" id="{lid}Lb">{counter[0]}</div></div>'
                 f'<div class="card rowsCard" id="{lid}" style="top:{top}px;width:{disp_w + 28:.0f}px;height:{h_img + 28:.0f}px">'
                 f'<img src="{src}" style="width:{disp_w:.0f}px"><div class="rowHi" id="{lid}H" style="top:14px;width:{disp_w:.0f}px;height:{row - 2:.0f}px"></div></div>')
        if label:
            self.add(f'<div class="lbl" id="{lid}T" style="top:250px">{label}</div>')
            self.ft(f'#{lid}T', {'opacity': 0}, {'opacity': 1}, expand_at + 5, .3)
        c = first_row_center + row_px * focus_row
        full = first_row_center + row_px * (n_rows - 1) + row_px / 2 + 8
        t0, t1 = (c - row_px / 2) / full * 100, 100 - (c + row_px / 2) / full * 100
        centre_y = top + 14 + c * scale
        self.s(f'#{lid}', {'clipPath': f'inset({t0:.1f}% 0% {t1:.1f}% 0% round 14px)', 'y': 560 - centre_y}, at)
        self.ft(f'#{lid}', {'opacity': 0, 'scale': 1.1}, {'opacity': 1, 'scale': 1.4}, at, .35, 'back.out(1.6)')
        self.ft(f'#{lid}W', {'opacity': 0, 'x': -30}, {'opacity': 1, 'x': 0}, at + 6, .3)
        self.to(f'#{lid}', {'clipPath': 'inset(0% 0% 0% 0% round 30px)', 'y': 0, 'scale': 1}, expand_at - 2, .45, 'power3.inOut')
        self.count(f'#{lid}N', 1, n_rows, expand_at, expand_at + 20)
        self.s(f'#{lid}Lb', {'textContent': counter[1]}, expand_at + 1)
        self.s(f'#{lid}H', {'opacity': 1, 'y': (first_row_center - row_px / 2) * scale}, expand_at)
        self.ft(f'#{lid}H', {'y': (first_row_center - row_px / 2) * scale}, {'y': (first_row_center - row_px / 2 + row_px * (n_rows - 1)) * scale}, expand_at, self.T(20), 'none')
        self.s(f'#{lid}H', {'opacity': 0}, expand_at + 21)
        self.ft(f'#{lid}N', {'scale': 1}, {'scale': 1.12}, expand_at + 19, .12); self.to(f'#{lid}N', {'scale': 1}, expand_at + 23, .2)

    def image_card(self, cid, img, at, top=290, width=820, height=None, kenburns=None, highlights=(), dark=False):
        """Real proof image in a rounded card. highlights=[(x, y, w, h, frame)] in card pixels. kenburns=(f0, f1)."""
        src = self.image(img)
        hs = ''.join(f'<div class="hl" id="{cid}H{k}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>' for k, (x, y, w, h, _) in enumerate(highlights))
        hh = f'height:{height}px;' if height else ''
        self.add(f'<div class="card imgCard" id="{cid}" style="left:{540 - width / 2:.0f}px;top:{top}px;width:{width}px;{hh}">'
                 f'<img id="{cid}I" src="{src}" style="width:{width}px">{hs}</div>')
        self.ft(f'#{cid}', {'y': 50, 'opacity': 0}, {'y': 0, 'opacity': 1}, at, .45, 'power3.out')
        if kenburns:
            self.ft(f'#{cid}I', {'scale': 1.0}, {'scale': 1.07}, kenburns[0], self.T(kenburns[1] - kenburns[0]), 'none')
        for k, (*_, f) in enumerate(highlights):
            self.ft(f'#{cid}H{k}', {'opacity': 0, 'scale': 1.3}, {'opacity': 1, 'scale': 1}, f, .3, 'back.out(2)')

    def skill_beat(self, kid, name, ic, at, out, kind, **kw):
        """Header chip + one artifact card, swapped per spoken item. kind in typed|comment|reply|profile|week."""
        self.chip(f'{kid}Ch', name, ic, at=at, out=out)
        getattr(self, f'_card_{kind}')(kid, at, out, **kw)
        self.rise(f'#{kid}', at + 1)
        if out is not None:
            self.leave(f'#{kid}', out)

    def _tag(self, tid, text, f, style='left:44px;bottom:36px', ic=None):
        self.add(f'<div class="tag" id="{tid}" style="{style};opacity:0">{icon(ic, 22) if ic else ""}{text}</div>')
        self.ft(f'#{tid}', {'opacity': 0, 'y': 10}, {'opacity': 1, 'y': 0}, f, .3, 'back.out(2)')

    def _card_typed(self, kid, at, out, text, type_span, tag=None):
        buf = []
        self._stack.append(buf)
        if tag:
            self._tag(f'{kid}Tg', tag[0], tag[1], ic=tag[2] if len(tag) > 2 else None)
        self._stack.pop()
        self.add(f'<div class="card skCard" id="{kid}" style="height:430px;opacity:0"><div class="av" style="left:34px;top:30px;width:62px;height:62px"></div>'
                 '<div class="bar" style="left:112px;top:40px;width:170px;height:16px;background:#cbd5e1"></div><div class="bar" style="left:112px;top:68px;width:110px;height:12px"></div>'
                 f'<div class="ptxt" style="top:118px"><span id="{kid}Tx"></span><span class="caret" id="{kid}Cr"></span></div>' + ''.join(buf) + '</div>')
        self.typed(f'#{kid}Tx', text, *type_span); self.blink(f'#{kid}Cr', at, out or at + 60, 12)

    def _card_comment(self, kid, at, out, text, type_span, tag=None):
        buf = []
        self._stack.append(buf)
        if tag:
            self._tag(f'{kid}Tg', tag[0], tag[1], style='left:104px;bottom:28px')
        self._stack.pop()
        self.add(f'<div class="card skCard" id="{kid}" style="height:480px;opacity:0"><div class="av" style="left:34px;top:28px;width:56px;height:56px;background:linear-gradient(140deg,#fde68a,#fecaca)"></div>'
                 '<div class="bar" style="left:106px;top:36px;width:150px;height:15px;background:#cbd5e1"></div><div class="bar" style="left:106px;top:62px;width:100px;height:11px"></div>'
                 '<div class="bar" style="left:34px;top:110px;width:680px"></div><div class="bar" style="left:34px;top:140px;width:600px"></div><div class="bar" style="left:34px;top:170px;width:470px"></div>'
                 '<div style="position:absolute;left:24px;right:24px;top:222px;height:1px;background:var(--rim)"></div><div class="av" style="left:34px;top:252px;width:52px;height:52px"></div>'
                 f'<div class="draftbox"><span id="{kid}Tx"></span><span class="caret" id="{kid}Cr"></span></div>' + ''.join(buf) + '</div>')
        self.typed(f'#{kid}Tx', text, *type_span); self.blink(f'#{kid}Cr', at, out or at + 70, 12)

    def _card_reply(self, kid, at, out, question, reply, type_span, second=None, tag=None):
        buf = []
        self._stack.append(buf)
        if tag:
            self._tag(f'{kid}Tg', tag[0], tag[1], style='left:104px;bottom:28px')
        self._stack.pop()
        sec = (f'<div class="av" style="left:34px;top:300px;width:52px;height:52px;background:linear-gradient(140deg,#fbcfe8,#ddd6fe)"></div>'
               f'<div class="qbub" style="top:294px">{second}</div>') if second else ''
        self.add(f'<div class="card skCard" id="{kid}" style="height:470px;opacity:0">'
                 f'<div class="av" style="left:34px;top:34px;width:52px;height:52px;background:linear-gradient(140deg,#bbf7d0,#bae6fd)"></div><div class="qbub" style="top:28px">{question}</div>'
                 f'<div id="{kid}R" style="position:absolute;left:150px;top:150px;right:34px;opacity:0"><div class="av" style="left:0;top:6px;width:46px;height:46px"></div>'
                 f'<div class="rbub"><span id="{kid}Tx"></span><span class="caret" id="{kid}Cr"></span></div></div>{sec}' + ''.join(buf) + '</div>')
        self.ft(f'#{kid}R', {'opacity': 0, 'x': 30}, {'opacity': 1, 'x': 0}, type_span[0] - 4, .3, 'power3.out')
        self.typed(f'#{kid}Tx', reply, *type_span); self.blink(f'#{kid}Cr', at, out or at + 50, 12)

    def _card_profile(self, kid, at, out, old, new, strike_at, new_at, tag=None):
        buf = []
        self._stack.append(buf)
        if tag:
            self._tag(f'{kid}Tg', tag[0], tag[1], style='left:44px;bottom:30px')
        self._stack.pop()
        self.add(f'<div class="card skCard" id="{kid}" style="height:470px;opacity:0;overflow:hidden"><div class="banner"></div>'
                 '<div class="av" style="left:40px;top:66px;width:120px;height:120px;border:6px solid #fff"></div><div class="bar" style="left:44px;top:206px;width:230px;height:22px;background:#cbd5e1"></div>'
                 f'<div class="hOld" id="{kid}O">{old}<i class="strike" id="{kid}S"></i></div><div class="hNew" id="{kid}N" style="opacity:0">{new}</div>' + ''.join(buf) + '</div>')
        self.ft(f'#{kid}S', {'scaleX': 0}, {'scaleX': 1}, strike_at, .25, 'power2.inOut')
        self.to(f'#{kid}O', {'opacity': .45}, strike_at + 8, .2)
        self.ft(f'#{kid}N', {'opacity': 0, 'y': 16}, {'opacity': 1, 'y': 0}, new_at, .32, 'power3.out')

    def _card_week(self, kid, at, out, fill_at, title='Your week', badge='7-day plan', icons=('pen', 'note', 'comment', 'pen', 'pulse', 'comment', 'star')):
        days = ''.join(f'<div class="day" style="left:{40 + d * 98}px"><b>{nm}</b><div class="pc" id="{kid}P{d}" style="top:{70 + (d % 3) * 64}px;opacity:0">{icon(icons[d], 32)}</div></div>'
                       for d, nm in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
        self.add(f'<div class="card skCard" id="{kid}" style="height:470px;opacity:0"><div class="ctitle">{title}</div>'
                 f'<div class="tag" style="right:34px;top:30px">{icon("calendar", 22)}{badge}</div>{days}</div>')
        for d in range(7):
            self.ft(f'#{kid}P{d}', {'opacity': 0, 'y': -40, 'scale': .7}, {'opacity': 1, 'y': 0, 'scale': 1}, fill_at + d * 4, .32, 'back.out(2)')

    def hero_chip(self, hid, name, ic, at):
        """Big centred reveal chip with a ring pulse (re-hook payoff, e.g. 'the best part is ...')."""
        self.add(f'<div class="hring" id="{hid}R"></div><div class="chip hero" id="{hid}"><div class="ic">{icon(ic, 46)}</div>{name}</div>')
        self.ft(f'#{hid}', {'opacity': 0, 'scale': .6}, {'opacity': 1, 'scale': 1}, at, .4, 'back.out(1.8)')
        self.ft(f'#{hid}R', {'opacity': .9, 'scale': .5}, {'opacity': 0, 'scale': 1.8}, at + 2, .7)
        self.ft(f'#{hid}', {'boxShadow': '0 12px 26px -10px rgba(15,23,42,.25)'}, {'boxShadow': '0 0 80px 10px rgba(91,158,255,.45)'}, at + 7, .4, 'power1.inOut')

    def enter(self, sel, at, how='rise'):
        """'rise' fades up from below; 'drop' is already opaque at `at` and settles from above (use on frame 1)."""
        if how == 'drop':
            if at == 0:
                self.init.append(f'gsap.set({json.dumps(sel)},{{opacity:1}});')
            self.ft(sel, {'y': -70, 'opacity': 1, 'scale': 1.03}, {'y': 0, 'opacity': 1, 'scale': 1}, at, .55, 'back.out(1.4)')
        else:
            self.rise(sel, at)

    def flag_draft(self, did, at, parts, flag_frames, scan=None, label='AI tells', dash_fix=None, shrink_at=None, title='Draft', how='rise', shrink_to=(-40, .45)):
        """Draft text whose flagged phrases turn red as a scan line passes; optional em-dash cap.
        parts=[(text, kind)] kind 0 plain / 1 flagged / 2 dash. dash_fix=(flare_at, [(dash_index, frame)])."""
        spans, fi, di = [], 0, 0
        for txt, kind in parts:
            if kind == 1:
                spans.append(f'<span class="fw" id="{did}F{fi}">{txt}</span>'); fi += 1
            elif kind == 2:
                spans.append(f'<span class="fw" id="{did}D{di}">{txt}</span>'); di += 1
            else:
                spans.append(txt)
        self.add(f'<div class="card draftCard" id="{did}"><div class="dhead">{icon("note", 30, "#334155")}{title}</div>'
                 f'<div class="meter" id="{did}M1" style="opacity:0"><span style="color:var(--red)">●</span>{label} <b id="{did}N1" style="color:var(--red)">0</b></div>'
                 f'<div class="meter" id="{did}M2" style="opacity:0"><span style="color:var(--amber)">—</span>Em dashes <b id="{did}N2" style="color:var(--amber)">{di}</b></div>'
                 f'<div class="dtxt">{"".join(spans)}</div><div class="scan" id="{did}Sc"></div></div>')
        self.enter(f'#{did}', at, how)
        self.ft(f'#{did}M1', {'opacity': 0}, {'opacity': 1}, at + 6, .2)
        if scan:
            self.s(f'#{did}Sc', {'opacity': 1}, scan[0])
            self.ft(f'#{did}Sc', {'y': 0}, {'y': 330}, scan[0], self.T(scan[1] - scan[0]), 'none')
            self.s(f'#{did}Sc', {'opacity': 0}, scan[1] + 1)
        for k, f in enumerate(flag_frames):
            self.ft(f'#{did}F{k}', {'backgroundColor': 'rgba(225,29,72,0)', 'color': '#0f172a'}, {'backgroundColor': 'rgba(225,29,72,.14)', 'color': '#e11d48'}, f, .15, 'none')
            self.s(f'#{did}N1', {'textContent': str(k + 1)}, f)
            self.ft(f'#{did}M1', {'scale': 1.15}, {'scale': 1}, f, .18)
        if dash_fix:
            flare, fixes = dash_fix
            self.to(f'#{did}M1', {'opacity': 0}, flare - 2, .15)
            self.ft(f'#{did}M2', {'opacity': 0}, {'opacity': 1}, flare, .2)
            for k in range(di):
                self.ft(f'#{did}D{k}', {'backgroundColor': 'rgba(217,119,6,0)', 'color': '#0f172a'}, {'backgroundColor': 'rgba(217,119,6,.18)', 'color': '#d97706'}, flare + 2 + k * 3, .15, 'none')
            left = di
            for k, f in fixes:
                left -= 1
                self.s(f'#{did}D{k}', {'textContent': ','}, f)
                self.to(f'#{did}D{k}', {'backgroundColor': 'rgba(22,163,74,.14)', 'color': '#16a34a'}, f, .12, 'none')
                self.s(f'#{did}N2', {'textContent': str(left)}, f)
            self.to(f'#{did}N2', {'color': self.tokens['green']}, fixes[-1][1], .15)
        if shrink_at is not None:
            self.to(f'#{did}', {'y': shrink_to[0], 'scale': shrink_to[1], 'transformOrigin': '50% 0%'}, shrink_at, .45, 'power3.inOut')
            self.to(f'#{did}M2', {'opacity': 0}, shrink_at, .2)

    def meter_rows(self, mid, rows, at, fill_at, focus_at=None, top=490, label='ILLUSTRATIVE', note=None, step=78):
        """Named rows with filling bars and no numbers (e.g. several detectors). rows=[(name, 0..1)].
        Keep `label` whenever the values are not measured. note=(icon, text, frame) chip under the rows."""
        body = ''.join(f'<div class="det" id="{mid}R{k}" style="top:{k * step}px;opacity:0"><b>{nm}</b><div class="trk"><i id="{mid}B{k}" '
                       f'style="width:{v * 100:.0f}%;background:linear-gradient(90deg,#22c55e,{"#f59e0b" if v > .3 else "#4ade80"});transform:scaleX(0)"></i></div></div>'
                       for k, (nm, v) in enumerate(rows))
        self.add(f'<div class="dets" id="{mid}" style="top:{top}px">{body}</div>')
        if label:
            self.add(f'<div class="ill" id="{mid}L" style="top:{top - 28}px">{label}</div>')
            self.ft(f'#{mid}L', {'opacity': 0}, {'opacity': 1}, fill_at + 3, .3)
        for k in range(len(rows)):
            self.ft(f'#{mid}R{k}', {'opacity': 0, 'x': (-1) ** k * 70}, {'opacity': 1, 'x': 0}, at + k * 3, .35, 'power3.out')
            self.ft(f'#{mid}B{k}', {'scaleX': 0}, {'scaleX': 1}, fill_at + k * 4, .5)
            if focus_at is not None:
                self.ft(f'#{mid}R{k}', {'borderColor': 'rgba(15,23,42,.09)'}, {'borderColor': 'rgba(91,158,255,.9)'}, focus_at + k * 2, .15, 'none')
        if note:
            ic, text, f = note
            self.add(f'<div class="chip cchip" id="{mid}N" style="top:{top + len(rows) * step + 16}px;opacity:0"><div class="ic">{icon(ic, 26)}</div>{text}</div>')
            self.ft(f'#{mid}N', {'opacity': 0, 'y': 20, 'scale': .8}, {'opacity': 1, 'y': 0, 'scale': 1}, f, .35, 'back.out(2)')

    def approval(self, aid, at, click_at, title='Ready to post?', yes='Yes, post it', done='Posted', waiting='Waiting for your OK', approved='Approved by you'):
        """Approve-before-publish card: cursor travels to the primary button, click, button turns green."""
        self.add(f'<div class="card yesCard" id="{aid}"><div class="ytitle">{icon("lock", 34, "#1e40af")}{title}</div>'
                 + ''.join(f'<div class="bar" style="left:44px;top:{128 + i * 34}px;width:{w}px"></div>' for i, w in enumerate([650, 610, 640, 380]))
                 + f'<div class="ystate" id="{aid}St">{waiting}</div><div class="btn bEdit">{icon("pen", 28)}Edit</div>'
                 f'<div class="btn bYes" id="{aid}Y"><span id="{aid}Ic" style="display:flex">{icon("send", 30, "#fff")}</span><span id="{aid}Tx">{yes}</span></div></div>'
                 f'<svg class="cursor" id="{aid}C" viewBox="0 0 24 24"><path d="M4 2.5 19 13l-6.5 1.2L16 21l-3 1.3-3.3-6.8L4 19.8Z" fill="#0f172a" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>')
        self.rise(f'#{aid}', at)
        self.ft(f'#{aid}C', {'x': 900, 'y': 900, 'opacity': 0}, {'x': 900, 'y': 900, 'opacity': 1}, click_at - 28, .05)
        self.to(f'#{aid}C', {'x': 720, 'y': 745}, click_at - 26, .7, 'power2.inOut')
        self.to(f'#{aid}Y', {'scale': .95}, click_at, .08); self.to(f'#{aid}Y', {'scale': 1}, click_at + 3, .15, 'back.out(2)')
        self.to(f'#{aid}C', {'scale': .88}, click_at, .08); self.to(f'#{aid}C', {'scale': 1}, click_at + 3, .12)
        self.to(f'#{aid}Y', {'backgroundColor': self.tokens['green']}, click_at + 6, .2, 'none')
        self.s(f'#{aid}Tx', {'textContent': done}, click_at + 10)
        self.s(f'#{aid}Ic', {'innerHTML': icon('check', 30, '#fff')}, click_at + 10)
        self.s(f'#{aid}St', {'textContent': approved, 'color': self.tokens['green']}, click_at + 10)

    def composer(self, cid, at, end, placeholder='What do you want to talk about?', how='rise'):
        """Empty post composer with a blinking caret (the 'you still need something to say' beat)."""
        self.add(f'<div class="card blankCard" id="{cid}"><div class="av" style="left:36px;top:36px;width:70px;height:70px"></div>'
                 f'<div class="ph"><span class="caret" id="{cid}Cr" style="height:44px;width:4px;margin:0 8px 0 0"></span>{placeholder}</div>'
                 f'<div class="tag" style="right:34px;top:44px;background:#f1f5f9;color:var(--muted)">{icon("pen", 22)}Post</div></div>')
        self.enter(f'#{cid}', at, how)
        self.blink(f'#{cid}Cr', at, end, 14)

    def note_to_post(self, nid, at, fields, fly_at, post_html, post_at, writer=('Post Writer', 'pen'), counts=None, ready='✓ Ready for your OK', title='Build note', tag='example'):
        """Input note types its fields, flies into a skill chip, and a finished post card rises.
        fields=[(LABEL, text, f0, f1)]; counts=((likes, comments), f0, f1)."""
        rows = ''.join(f'<div class="nk" style="top:{140 + i * 140}px">{lab}</div><div class="nv" style="top:{180 + i * 140}px"><span id="{nid}V{i}"></span>'
                       f'<span class="caret" id="{nid}C{i}" style="opacity:0"></span></div>' for i, (lab, *_r) in enumerate(fields))
        self.add(f'<div class="card noteCard" id="{nid}"><div class="ntitle">{icon("note", 34, "#1e40af")}{title}</div>'
                 f'<div class="tag" style="right:34px;top:34px;background:#f1f5f9;color:var(--muted)">{tag}</div>{rows}</div>')
        self.add(f'<div class="chip cchip" id="{nid}W" style="top:282px;opacity:0"><div class="ic">{icon(writer[1], 26)}</div>{writer[0]}</div>'
                 f'<div class="card outCard" id="{nid}P" style="opacity:0"><div class="av" style="left:34px;top:30px;width:62px;height:62px"></div>'
                 '<div class="bar" style="left:112px;top:40px;width:170px;height:16px;background:#cbd5e1"></div><div class="bar" style="left:112px;top:68px;width:110px;height:12px"></div>'
                 f'<div class="tag readyTag" id="{nid}Rd" style="opacity:0">{ready}</div><div class="ptxt" style="top:118px;font-size:31px">{post_html}</div>'
                 + ''.join(f'<div class="bar" id="{nid}B{i}" style="left:44px;top:{250 + i * 34}px;width:{w}px"></div>' for i, w in enumerate([660, 600, 420]))
                 + f'<div class="act" style="left:44px">{icon("thumb", 30, "#0a66c2", 2.2)}<span id="{nid}N0">0</span></div>'
                 f'<div class="act" style="left:220px">{icon("comment", 30, "#334155", 2.2)}<span id="{nid}N1">0</span></div></div>')
        self.rise(f'#{nid}', at)
        for i, (_, text, f0, f1) in enumerate(fields):
            self.s(f'#{nid}C{i}', {'opacity': 1}, f0 - 2); self.typed(f'#{nid}V{i}', text, f0, f1); self.s(f'#{nid}C{i}', {'opacity': 0}, f1 + 4)
        self.to(f'#{nid}', {'scale': .2, 'y': -170, 'opacity': 0, 'transformOrigin': '50% 0%'}, fly_at, .4, 'power3.in')
        self.ft(f'#{nid}W', {'opacity': 0, 'scale': .6}, {'opacity': 1, 'scale': 1}, fly_at + 4, .35, 'back.out(2)')
        self.ft(f'#{nid}W', {'boxShadow': '0 0 0 0 rgba(91,158,255,0)'}, {'boxShadow': '0 0 60px 8px rgba(91,158,255,.5)'}, fly_at + 10, .3)
        self.ft(f'#{nid}P', {'opacity': 0, 'y': 60, 'scale': .94}, {'opacity': 1, 'y': 0, 'scale': 1}, post_at, .42, 'power3.out')
        for i in range(3):
            self.ft(f'#{nid}B{i}', {'scaleX': 0}, {'scaleX': 1}, post_at + 6 + i * 3, .25)
        if counts:
            (a, b), f0, f1 = counts
            self.count(f'#{nid}N0', 0, a, f0, f1); self.count(f'#{nid}N1', 0, b, f0 + 2, f1)
        self.ft(f'#{nid}Rd', {'opacity': 0, 'scale': .7}, {'opacity': 1, 'scale': 1}, post_at + 18, .3, 'back.out(2)')

    def cta(self, cid, keyword, at, type_span, pill_at, chips=(), end=None):
        """Comment-to-DM close: comment bar types the keyword, keyword pill lands, resource chips drop in.
        chips=[(icon, text, frame)]."""
        self.add(f'<div class="kw" id="{cid}K">{keyword}</div><div class="card cmtBar" id="{cid}"><div class="av"></div><div class="cmtPh" id="{cid}Ph">Add a comment…</div>'
                 f'<div class="cmtTxt"><span id="{cid}T"></span><span class="caret" id="{cid}Cr"></span></div><div style="display:flex">{icon("send", 38, "#1e40af", 2.2)}</div></div>'
                 '<div class="chiprow" style="top:770px">' + ''.join(f'<div class="chip rel" id="{cid}C{k}" style="opacity:0"><div class="ic">{icon(ic, 26)}</div>{t}</div>' for k, (ic, t, _) in enumerate(chips)) + '</div>')
        self.ft(f'#{cid}', {'opacity': 0, 'y': 40}, {'opacity': 1, 'y': 0}, at, .38, 'power3.out')
        self.s(f'#{cid}Ph', {'opacity': 1}, at); self.s(f'#{cid}Ph', {'opacity': 0}, type_span[0])
        self.typed(f'#{cid}T', keyword, *type_span); self.blink(f'#{cid}Cr', at, type_span[1] + 8, 12); self.s(f'#{cid}Cr', {'opacity': 0}, type_span[1] + 8)
        self.ft(f'#{cid}K', {'opacity': 0, 'scale': .5, 'y': 40}, {'opacity': 1, 'scale': 1, 'y': 0}, pill_at, .45, 'back.out(1.8)')
        for k, (*_x, f) in enumerate(chips):
            self.ft(f'#{cid}C{k}', {'opacity': 0, 'y': 30}, {'opacity': 1, 'y': 0}, f, .35, 'back.out(2)')
        self.ft(f'#{cid}K', {'y': 0}, {'y': -10}, pill_at + 30, self.T((end or self.total) - pill_at - 30), 'sine.inOut')

    # ---------------------------------------------------------------- camera + compile
    def camera_moves(self, face_pushes=(), split_settles=(), split_drift=True, split_push=None):
        """face_pushes=[(f0, f1, s0, s1)]; split_settles=frames where the split re-enters (pane settles down, camera eases in);
        split_push=(f0, f1, s1) e.g. an opening push that runs on the split."""
        for f0, f1, s0, s1 in face_pushes:
            self.ft('#camFullV', {'scale': s0}, {'scale': s1}, f0, self.T(f1 - f0), 'power2.out')
        for f in split_settles:
            self.ft('#top', {'y': -24}, {'y': 0}, f, .38, 'power3.out')
            self.ft('#camSplitV', {'scale': 1.06}, {'scale': 1.0}, f, .5, 'power3.out')
        if split_push:
            f0, f1, s1 = split_push
            self.ft('#camSplitV', {'scale': 1.0}, {'scale': s1}, f0, self.T(f1 - f0), 'power2.out')
            self.to('#camSplitV', {'scale': 1.0}, f1 + 110, .5, 'power2.inOut')
        if split_drift:
            for lay, a, b in self.lay:
                if lay == 'split' and b - a > 40:
                    self.ft('#camSplitV', {'y': 0}, {'y': -14}, a + 20, self.T(b - a - 20), 'none')

    def compile(self, title='paper-grid reel'):
        out = self.out
        (out / 'assets').mkdir(parents=True, exist_ok=True)
        shutil.copy2(find_gsap(out), out / 'assets/gsap.min.js')
        shutil.copy2(self.camera, out / 'assets' / self.camera.name)
        for m in self.media:
            shutil.copy2(m, out / 'assets' / m.name)
        T, total = self.T, self.total
        cam = f'assets/{self.camera.name}'
        head = [f'<div id="root" data-composition-id="main" data-start="0" data-duration="{T(total)}" data-width="1080" data-height="1920">']
        for pid in ['camFull', 'camSplit']:
            head.append(f'<div id="{pid}" class="pane"><video id="{pid}V" class="clip" data-layout-allow-overflow src="{cam}" data-start="0" '
                        f'data-duration="{T(total)}" data-track-index="0" muted playsinline></video></div>')
        head.append('<div id="top"><div id="glow"></div><div id="grid"></div>')
        body = ''.join(head) + ''.join(self.H) + '</div><div id="seam"></div><div id="seamLine"></div></div>'
        # initial state from gsap.set (not only tl.set at 0), then per-layout toggles
        first = self.lay[0][0] == 'split'
        init = {'#camFull': 0 if first else 1, '#camSplit': int(first), '#top': int(first), '#seam': int(first), '#seamLine': int(first)}
        pre = ["const tl=gsap.timeline({paused:true});window.__timelines={main:tl};"]
        pre += [f'gsap.set({json.dumps(k)},{{opacity:{v}}});' for k, v in init.items()]
        for sid, (a, b) in self.scenes.items():
            pre.append(f'gsap.set("#{sid}",{{opacity:{1 if a == 0 else 0}}});')
        pre += self.init
        lay = []
        J0 = self.J; self.J = lay
        for kind, a, b in self.lay:
            split = kind == 'split'
            for p in ['#camSplit', '#top', '#seam', '#seamLine']:
                self.s(p, {'opacity': int(split)}, a)
            self.s('#camFull', {'opacity': 0 if split else 1}, a)
        for sid, (a, b) in self.scenes.items():
            self.s(f'#{sid}', {'opacity': 1}, a); self.s(f'#{sid}', {'opacity': 0}, b)
        self.ft('#grid', {'x': 0, 'y': 0}, {'x': -self.drift, 'y': -self.drift}, 0, T(total), 'none')
        self.J = J0
        js = '\n'.join(pre + lay + self.J + [f"tl.set({{}},{{}},{T(total)});"])
        tok = ':root{' + ''.join(f'--{k}:{v};' for k, v in self.tokens.items()) + '}'
        css = tok + CSS.replace('__SPLIT_TOP__', f'{self.split_top}px').replace('__SPLIT_ORIGIN__', self.split_origin) + '\n'.join(self.extra_css)
        html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><script src="assets/gsap.min.js"></script>'
                f'<link rel="stylesheet" href="style.css"></head><body>{body}<script>{js}</script></body></html>')
        (out / 'index.html').write_text(html)
        (out / 'style.css').write_text(css)
        (out / 'hyperframes.json').write_text('{"media": {"autoProxy": false}}')
        (out / 'timeline.js').write_text(js)
        chk = subprocess.run(['node', '--check', str(out / 'timeline.js')], capture_output=True, text=True)
        if chk.returncode:
            raise SystemExit('timeline script failed node --check:\n' + chk.stderr)
        (out / 'timeline.js').unlink()
        return out
