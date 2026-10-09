"""Breakout-card reel builder: white grid page, the speaker in a card at the bottom with their head breaking out, dark pills and
cards that blur in and out, one-to-two-word Montserrat captions. Everything is frame-based on one paused GSAP timeline
(window.__timelines.main). Output is a silent HyperFrames composition; dialogue and SFX stay separate.

    reel = Reel(out_dir, page_plate='<plates>/page-plate.mp4', cam_plate='<plates>/cam-plate.mp4', total=1363)
    reel.layouts([('page', 0, 190), ('cam', 190, 254), ..., ('camz', 622, 707, 1.2, 1.27), ...])
    reel.captions([("there's a", 0.0), ('single file', .38), ..., (None, 7.44, 8.45), ...])
    with reel.scene('s1', 0, 190):
        reel.shot('about', 'proof.png', top=214, at=0, drop=True)
        reel.counter_pill('stars', 215697, top=838, at=46, count=(50, 87))
    reel.compile()
"""
from pathlib import Path
from contextlib import contextmanager
import json, math, os, shutil, subprocess

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / 'assets'

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


TOKENS = {'paper': '#fcfcfd', 'ink': '#121214', 'dark': '#1c1c1f', 'mute': '#b4b4be', 'accent': '#1e40af', 'accent2': '#5b9eff',
          'green': '#16a34a', 'red': '#ef4444', 'capPage': '1074px', 'capCam': '540px'}

ICONS = {
    'star': '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9Z"/>',
    'check': '<path d="m6 12.5 4 4L18 8"/>',
    'x': '<path d="M7 7l10 10M17 7 7 17"/>',
    'folder': '<path d="M3.5 7a2 2 0 0 1 2-2h4l2 2.5h7a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2Z"/>',
    'doc': '<path d="M14 3H6.5A2.5 2.5 0 0 0 4 5.5v13A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V9Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    'loop': '<path d="M17 3l3 3-3 3"/><path d="M4 11V9a3 3 0 0 1 3-3h13"/><path d="M7 21l-3-3 3-3"/><path d="M20 13v2a3 3 0 0 1-3 3H4"/>',
    'lock': '<rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    'flame': '<path d="M12 21c-4 0-6.5-2.6-6.5-6 0-3.6 3-5.6 3.6-9 2.4 1.6 3.6 3.6 3.9 5.6 1-.8 1.6-2 1.7-3.2 2 1.6 3.8 4 3.8 6.6 0 3.4-2.5 6-6.5 6Z"/>',
    'github': '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    'heart': '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10Z"/>',
    'send': '<path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4Z"/>',
    'sparkle': '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z"/>',
    'bolt': '<path d="M13 2 4 14h7l-1 8 9-12h-7Z"/>',
    'code': '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
}


def icon(name, size=36, color='currentColor', width=2.2, fill='none'):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def claude_mark(size=44):
    rays = ''.join(f'<path d="M12 12 L{12 + 9 * math.cos(a * math.pi / 6):.2f} {12 + 9 * math.sin(a * math.pi / 6):.2f}"/>' for a in range(12))
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24"><g stroke="#D97757" stroke-width="2.6" stroke-linecap="round">{rays}</g></svg>'


CURSOR = ('<svg width="76" height="76" viewBox="0 0 32 32"><path d="M11 3.5c1.1 0 2 .9 2 2v8.2l.9-.3c1-.3 2 .2 2.4 1.1l.2.4.7-.2c1-.3 2.1.2 2.5 1.2l.1.3.6-.1c1.1-.2 2.2.5 2.4 1.6l1.1 5.6'
          'c.4 2-.2 4-1.6 5.5L21 30.5H12.5L7 23.6c-.7-.9-.6-2.2.3-2.9.8-.7 2-.7 2.8 0L9 19.8V5.5c0-1.1.9-2 2-2Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>')


def smooth_path(p):
    """Catmull-Rom through points as cubic Beziers. Returns (svg d, length) for a dash-offset draw-on."""
    d, length = f'M {p[0][0]} {p[0][1]}', 0.0
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, len(p) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 4, p1[1] + (p2[1] - p0[1]) / 4)
        c2 = (p2[0] - (p3[0] - p1[0]) / 4, p2[1] - (p3[1] - p1[1]) / 4)
        d += f' C {c1[0]:.0f} {c1[1]:.0f} {c2[0]:.0f} {c2[1]:.0f} {p2[0]} {p2[1]}'
        prev = p1
        for k in range(1, 41):
            u = k / 40
            q = tuple((1 - u) ** 3 * a + 3 * (1 - u) ** 2 * u * b + 3 * (1 - u) * u * u * c + u ** 3 * e for a, b, c, e in zip(p1, c1, c2, p2))
            length += math.dist(prev, q); prev = q
    return d, math.ceil(length) + 4


class Reel:
    def __init__(self, out, page_plate, cam_plate, total, fps=30, tokens=None):
        self.out, self.total, self.fps = Path(out), total, fps
        self.plates = [Path(page_plate), Path(cam_plate)]
        self.tokens = {**TOKENS, **(tokens or {})}
        self.H, self.J, self.init, self.media, self.extra_css = [], [], [], [], []
        self.scenes, self.lay, self.caps, self._stack = {}, [], [], []

    # ---------------------------------------------------------------- time helpers
    def T(self, f):
        return round(f / self.fps, 4)

    def s(self, sel, props, f):
        self.J.append(f"tl.set({json.dumps(sel)},{json.dumps(props)},{self.T(f)});")

    def ft(self, sel, a, b, f, dur, ease='power3.out'):
        self.J.append(f"tl.fromTo({json.dumps(sel)},{json.dumps(a)},{json.dumps({**b, 'duration': dur, 'ease': ease, 'immediateRender': False})},{self.T(f)});")

    def to(self, sel, b, f, dur, ease='power2.out'):
        self.J.append(f"tl.to({json.dumps(sel)},{json.dumps({**b, 'duration': dur, 'ease': ease})},{self.T(f)});")

    def blur_in(self, sel, f, dur=.38, scale=.82, y=0):
        """The signature entrance: out of focus and small -> sharp."""
        self.ft(sel, {'opacity': 0, 'scale': scale, 'y': y, 'filter': 'blur(16px)'}, {'opacity': 1, 'scale': 1, 'y': 0, 'filter': 'blur(0px)'}, f, dur)

    def blur_out(self, sel, f, dur=.28):
        self.to(sel, {'opacity': 0, 'scale': 1.04, 'filter': 'blur(18px)'}, f, dur, 'power2.in')

    def pop(self, sel, f, dur=.32, scale=.6):
        self.ft(sel, {'opacity': 0, 'scale': scale}, {'opacity': 1, 'scale': 1}, f, dur, 'back.out(2.2)')

    def count(self, sel, a, b, f0, f1):
        self.J.append(f"(()=>{{const o={{v:{a}}},el=document.querySelector({json.dumps(sel)});tl.fromTo(o,{{v:{a}}},{{v:{b},duration:{self.T(f1 - f0)},"
                      f"ease:'power2.out',immediateRender:false,onUpdate:()=>{{el.textContent=Math.round(o.v).toLocaleString('en-US')}}}},{self.T(f0)});}})();")
        self.s(sel, {'textContent': f'{b:,}'}, f1 + 1)

    def typed(self, sel, text, f0, f1):
        n = max(1, len(text))
        self.s(sel, {'textContent': ''}, 0)
        for k in range(n + 1):
            self.s(sel, {'textContent': text[:k]}, f0 + (f1 - f0) * k / n)

    def blink(self, sel, f0, f1, period=16):
        for f in range(f0, f1, period):
            self.s(sel, {'opacity': 1}, f); self.s(sel, {'opacity': 0}, f + period // 2)

    def add(self, html):
        (self._stack[-1] if self._stack else self.H).append(html)

    def css(self, text):
        self.extra_css.append(text)

    def image(self, src):
        src = Path(src)
        self.media.append(src)
        return f'assets/{src.name}'

    def row(self, top, inner):
        """Full-width centring row. Animate the element inside it, never the row."""
        self.add(f'<div class="row" style="top:{top}px">{inner}</div>')

    # ---------------------------------------------------------------- structure
    def layouts(self, spans):
        """[(kind, a, b)] with kind 'page' | 'cam' | 'camz' (camz adds start/end scale: ('camz', a, b, 1.2, 1.27)). Must cover the reel.
        Cut between layouts on the paper edit's jump cuts where you can; they hide inside the layout change."""
        self.lay = spans
        assert spans[0][1] == 0 and spans[-1][2] == self.total, 'layouts must cover the whole reel'

    def layout_at(self, f):
        return next(sp[0] for sp in self.lay if sp[1] <= f < sp[2])

    def captions(self, chunks):
        """[(text, start_s[, end_s])]: one or two words each, lowercase as spoken, verified wording + ASR timing.
        text=None blanks the captions for a title moment. End defaults to the next chunk's start. A chunk crossing a layout
        change is split so each part takes its layout's style (ink on the page, white over the camera)."""
        for i, c in enumerate(chunks):
            a = round(c[1] * self.fps)
            b = round(c[2] * self.fps) if len(c) > 2 else round(chunks[i + 1][1] * self.fps)
            if c[0] is None:
                continue
            cuts = sorted({sp[1] for sp in self.lay if a < sp[1] < b})
            for x, y in zip([a] + cuts, cuts + [b]):
                self.caps.append((c[0], x, y, 'pg' if self.layout_at(x) == 'page' else 'cm'))

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

    # ---------------------------------------------------------------- components (all in the dark material)
    def pill(self, pid, text, top, at, ic=None, ok_at=None, strike_at=None, cls=''):
        """Dark capsule. ok_at pops a green check; strike_at draws a red line through it with a red cross."""
        lead = f'<i class="ico" id="{pid}I">{icon(ic, 40, "#fff", 2.2)}</i>' if ic else ''
        ok = f'<i class="ok" id="{pid}Ok">{icon("check", 30, "#fff", 3.2)}</i>' if ok_at is not None else ''
        st = (f'<i class="strike" id="{pid}St"></i><i class="no" id="{pid}No">{icon("x", 30, "#fff", 3.2)}</i>') if strike_at is not None else ''
        self.row(top, f'<div class="pill dk {cls}" id="{pid}">{lead}<b>{text}</b>{st}{ok}</div>')
        self.blur_in(f'#{pid}', at, .34, .7)
        if ok_at is not None:
            self.pop(f'#{pid}Ok', ok_at, .3, .3)
        if strike_at is not None:
            self.ft(f'#{pid}St', {'scaleX': 0}, {'scaleX': 1}, strike_at, .22, 'power2.out')
            self.pop(f'#{pid}No', strike_at, .3, .3)
            self.to(f'#{pid} b', {'color': '#8b8b96'}, strike_at, .2)

    def spin(self, sel, f, dur=.8):
        self.ft(sel, {'rotation': 0}, {'rotation': 360}, f, dur, 'power2.inOut')

    def counter_pill(self, pid, value, top, at, count, ic='star', label='stars'):
        """Big number that counts up on the spoken figure. Use the real value from a dated capture."""
        self.row(top, f'<div class="pill dk big" id="{pid}">{icon(ic, 46, "#fff", 2, "#fff")}<b id="{pid}N">0</b><span class="mut" id="{pid}L">{label}</span></div>')
        self.blur_in(f'#{pid}', at, .36, .7)
        self.count(f'#{pid}N', 0, value, *count)
        self.ft(f'#{pid}L', {'opacity': .35}, {'opacity': 1}, count[1], .15)

    def shot(self, pid, image, top, at, width=600, tilt=(9, -13, 2), drop=False, highlight=None):
        """Real proof as a 3D-tilted card. drop=True: already flying in on `at` (safe for frame 1).
        highlight=(left, top, w, h, frame) sweeps a soft accent bar over the line that carries the point."""
        hl = f'<i class="hl" id="{pid}Hl" style="left:{highlight[0]}px;top:{highlight[1]}px;width:{highlight[2]}px;height:{highlight[3]}px"></i>' if highlight else ''
        self.row(top, f'<div class="persp"><div class="shot" id="{pid}" style="width:{width}px"><img src="{self.image(image)}">{hl}</div></div>')
        rx, ry, rz = tilt
        self.init.append(f'gsap.set("#{pid}",{{rotationX:{rx},rotationY:{ry},rotationZ:{rz}}})')
        if drop:
            self.ft(f'#{pid}', {'y': -150, 'rotationX': rx + 23, 'rotationY': ry - 21, 'rotationZ': rz + 4, 'scale': .9, 'opacity': 1},
                    {'y': 0, 'rotationX': rx, 'rotationY': ry, 'rotationZ': rz, 'scale': 1, 'opacity': 1}, at, .75)
        else:
            self.blur_in(f'#{pid}', at, .45, .85)
        self.to(f'#{pid}', {'rotationY': ry * .45, 'rotationX': rx * .66, 'rotationZ': rz / 2}, at + 23, 2.4, 'sine.inOut')
        if highlight:
            self.ft(f'#{pid}Hl', {'scaleX': 0}, {'scaleX': 1}, highlight[4], .4, 'power2.out')

    def headline(self, pid, top, small, huge, mega, at):
        """Typographic beat: small line, then a huge and a mega word with grey-gradient ink. at=(small, huge, mega) frames."""
        self.row(top, f'<div class="hline" id="{pid}1">{small}</div>')
        self.row(top + 80, f'<div class="huge" id="{pid}2">{huge}</div>')
        self.row(top + 180, f'<div class="mega" id="{pid}3">{mega}</div>')
        self.blur_in(f'#{pid}1', at[0])
        self.ft(f'#{pid}2', {'opacity': 0, 'y': 30, 'filter': 'blur(14px)'}, {'opacity': 1, 'y': 0, 'filter': 'blur(0px)'}, at[1], .34)
        self.ft(f'#{pid}3', {'opacity': 0, 'scale': 1.6, 'filter': 'blur(20px)'}, {'opacity': 1, 'scale': 1, 'filter': 'blur(0px)'}, at[2], .3, 'power4.out')

    def headline_out(self, pid, f):
        for k in (1, 2, 3):
            self.blur_out(f'#{pid}{k}', f, .24)

    def tile_drop(self, pid, top, ic, label, file_text, at, drop_at, badge=True):
        """A small file/pill drops into an icon tile ("drop it in your project")."""
        b = f'<i class="badge" id="{pid}Ok">{icon("check", 34, "#fff", 3)}</i>' if badge else ''
        self.row(top, f'<div class="tile dk" id="{pid}">{icon(ic, 110, "#fff", 1.6)}{b}</div>')
        self.row(top + 265, f'<div class="lbl" id="{pid}L">{label}</div>')
        self.row(top, f'<div class="pill dk file" id="{pid}F">{icon("doc", 38, "#fff", 2)}<b>{file_text}</b></div>')
        self.pop(f'#{pid}', at)
        self.ft(f'#{pid}L', {'opacity': 0, 'y': 12}, {'opacity': 1, 'y': 0}, at + 3, .25)
        self.ft(f'#{pid}F', {'opacity': 0, 'y': -330}, {'opacity': 1, 'y': -250}, drop_at - 8, .2, 'power2.out')
        self.to(f'#{pid}F', {'y': 40, 'scale': .45, 'opacity': 0}, drop_at, .3, 'power2.in')
        self.ft(f'#{pid}', {'scale': 1.12}, {'scale': 1}, drop_at + 9, .35, 'back.out(3)')
        if badge:
            self.pop(f'#{pid}Ok', drop_at + 11, .3, .3)

    def checklist(self, pid, title, items, top, at, width=820):
        """Card whose items appear and tick on their spoken words. items=[(text, appear_frame, check_frame)]."""
        rows = ''.join(f'<div class="item" id="{pid}R{i}"><i class="tick" id="{pid}T{i}">{icon("check", 26, "#121214", 3.4)}</i><span>{t}</span></div>'
                       for i, (t, _, _) in enumerate(items))
        self.row(top, f'<div class="card dk" id="{pid}" style="width:{width}px"><div class="ctitle">{title}'
                      f'<span class="spark">{icon("sparkle", 30, "#8b8b96", 2)}</span></div>{rows}</div>')
        self.blur_in(f'#{pid}', at, .4, .86)
        for i, (_, a, b) in enumerate(items):
            self.ft(f'#{pid}R{i}', {'opacity': 0, 'x': -26}, {'opacity': 1, 'x': 0}, a, .3)
            self.ft(f'#{pid}T{i}', {'backgroundColor': 'rgba(255,255,255,0)', 'borderColor': '#5d5d68'}, {'backgroundColor': '#ffffff', 'borderColor': '#ffffff'}, b, .14, 'power1.out')
            self.ft(f'#{pid}T{i} svg', {'opacity': 0, 'scale': .3}, {'opacity': 1, 'scale': 1}, b, .26, 'back.out(3)')
            self.ft(f'#{pid}R{i} span', {'color': '#9a9aa6'}, {'color': '#ffffff'}, b, .2)

    def tree(self, pid, rows, top, at, head='your-project/', sub=(), meter=False, width=780, row_h=54):
        """Folder tree card. Follow with tree_wander / tree_straight. Returns the row y-centre function (card-local)."""
        pad = 96
        html = ''.join(f'<div class="trow{" sub" if i in sub else ""}" id="{pid}R{i}" style="top:{pad + i * row_h}px">'
                       f'{icon("folder", 30, "#8d8d99", 2)}<span>{n}</span></div>' for i, n in enumerate(rows))
        m = (f'<div class="meter" id="{pid}M">{icon("flame", 30, "#ef4444", 2.2)}<span>tokens</span><div class="mbar"><i id="{pid}MF"></i></div>'
             f'<em>illustrative</em></div>') if meter else ''
        h = pad + len(rows) * row_h + 26
        self.row(top, f'<div class="card dk tree" id="{pid}" style="width:{width}px;height:{h}px"><div class="thead">{icon("folder", 36, "#fff", 2)}'
                      f'<b>{head}</b>{m}</div>{html}<svg class="path" id="{pid}P" width="{width}" height="{h}"></svg></div>')
        self.blur_in(f'#{pid}', at, .4, .9)
        self._tree = dict(pad=pad, row_h=row_h, n=len(rows))
        return lambda r: pad + r * row_h + row_h // 2

    def tree_wander(self, pid, order, xs, f0, f1, start=(540, 96), meter_at=None):
        """Red trail looping through rows the agent doesn't need, drawn in the card's empty right side; rows flash as it passes."""
        y = lambda r: self._tree['pad'] + r * self._tree['row_h'] + self._tree['row_h'] // 2
        pts = [start] + [(xs[k], y(r)) for k, r in enumerate(order)]
        d, L = smooth_path(pts)
        self.init.append(f'document.getElementById("{pid}P").insertAdjacentHTML("beforeend",\'<path id="{pid}W" d="{d}" fill="none" stroke="#ef4444" '
                         f'stroke-width="5" stroke-linecap="round" stroke-dasharray="{L} {L}" stroke-dashoffset="{L}"/>\')')
        self.ft(f'#{pid}W', {'strokeDashoffset': L}, {'strokeDashoffset': 0}, f0, self.T(f1 - f0), 'none')
        acc, tot = 0, sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        for i in range(1, len(pts)):
            acc += math.dist(pts[i - 1], pts[i])
            f = f0 + (f1 - f0) * acc / tot
            self.ft(f'#{pid}R{order[i - 1]}', {'backgroundColor': 'rgba(239,68,68,0)'}, {'backgroundColor': 'rgba(239,68,68,.26)'}, f, .1)
            self.to(f'#{pid}R{order[i - 1]}', {'backgroundColor': 'rgba(239,68,68,.12)'}, f + 5, .3)
        if meter_at is not None:
            self.ft(f'#{pid}MF', {'scaleX': 0}, {'scaleX': 1}, meter_at, 1.2, 'power1.in')
            self.ft(f'#{pid}M', {'opacity': .4}, {'opacity': 1}, meter_at, .2)

    def tree_straight(self, pid, row, f, ok_at, x=390):
        """Accent line straight down from whatever sits above the card to one row; the rest dims, the row lights green."""
        ly = self._tree['pad'] + row * self._tree['row_h'] + self._tree['row_h'] // 2
        self.init.append(f'document.getElementById("{pid}P").insertAdjacentHTML("beforeend",\'<path id="{pid}S" d="M {x} -34 L {x} {ly}" fill="none" '
                         f'stroke="{self.tokens["accent2"]}" stroke-width="6" stroke-linecap="round" stroke-dasharray="1200" stroke-dashoffset="1200"/>'
                         f'<circle id="{pid}D" cx="{x}" cy="{ly}" r="13" fill="{self.tokens["accent2"]}"/>\')')
        self.init.append(f'gsap.set("#{pid}D",{{opacity:0,transformOrigin:"50% 50%"}})')
        self.ft(f'#{pid}S', {'strokeDashoffset': 1200}, {'strokeDashoffset': 1200 - (ly + 34)}, f, .45, 'power2.inOut')
        self.pop(f'#{pid}D', f + 14, .3, .2)
        for i in range(self._tree['n']):
            if i != row:
                self.to(f'#{pid}R{i}', {'opacity': .32}, f + 6, .3)
        self.ft(f'#{pid}R{row}', {'backgroundColor': 'rgba(22,163,74,0)'}, {'backgroundColor': 'rgba(22,163,74,.28)'}, ok_at, .2)
        self.ft(f'#{pid}R{row} span', {'color': '#c9c9d1'}, {'color': '#ffffff'}, ok_at, .2)

    def doc_card(self, pid, title, tag, sections, top, at, width=840):
        """File card that fills as it is described. sections (each fades in on its first frame):
        ('text', LABEL, value, (f0, f1))          typed value
        ('kv', LABEL, [(key, value, frame)], f)   rows slide in
        ('never', LABEL, text, f, cross_frame)    red lock label + red cross"""
        body, anim = '', []
        for k, sec in enumerate(sections):
            sid = f'{pid}S{k}'
            if sec[0] == 'text':
                body += f'<div class="sect" id="{sid}"><div class="cap2">{sec[1]}</div><div class="val" id="{sid}V">&nbsp;</div></div>'
                anim.append(lambda sid=sid, sec=sec: (self.ft(f'#{sid}', {'opacity': 0}, {'opacity': 1}, sec[3][0], .2), self.typed(f'#{sid}V', sec[2], *sec[3])))
            elif sec[0] == 'kv':
                body += (f'<div class="sect" id="{sid}"><div class="cap2">{sec[1]}</div>' +
                         ''.join(f'<div class="kv" id="{sid}R{i}"><span>{a}</span><code>{b}</code></div>' for i, (a, b, _) in enumerate(sec[2])) + '</div>')
                anim.append(lambda sid=sid, sec=sec: (self.ft(f'#{sid}', {'opacity': 0}, {'opacity': 1}, sec[3], .2),
                                                      [self.ft(f'#{sid}R{i}', {'opacity': 0, 'x': -24}, {'opacity': 1, 'x': 0}, f, .28) for i, (_, _, f) in enumerate(sec[2])]))
            elif sec[0] == 'never':
                body += (f'<div class="sect" id="{sid}"><div class="cap2">{icon("lock", 22, "#ef4444", 2.4)}<span style="margin-left:8px">{sec[1]}</span></div>'
                         f'<div class="kv"><span>{sec[2]}</span><i class="no small" id="{sid}X">{icon("x", 22, "#fff", 3.2)}</i></div></div>')
                anim.append(lambda sid=sid, sec=sec: (self.ft(f'#{sid}', {'opacity': 0}, {'opacity': 1}, sec[3], .25), self.pop(f'#{sid}X', sec[4], .3, .3)))
            self.init.append(f'gsap.set("#{sid}",{{opacity:0}})')
        tg = f'<span class="tag">{tag}</span>' if tag else ''
        self.row(top, f'<div class="card dk" id="{pid}" style="width:{width}px"><div class="ctitle">{icon("doc", 40, "#fff", 2)}'
                      f'<span style="margin-left:14px">{title}</span>{tg}</div>{body}</div>')
        self.blur_in(f'#{pid}', at, .4, .88)
        for a in anim:
            a()

    def chip(self, pid, text, top, at, ic='doc', tag=None):
        tg = f'<span class="tag">{tag}</span>' if tag else ''
        self.row(top, f'<div class="pill dk chip" id="{pid}">{icon(ic, 32, "#fff", 2)}<b>{text}</b>{tg}</div>')
        self.blur_in(f'#{pid}', at, .34, .7)

    def comment(self, pid, keyword, top, at, type_span, heart_at=None, chips=()):
        """CTA: a viewer's comment types the keyword; chips=[(icon, text, frame)] pop underneath for what they get."""
        self.row(top, f'<div class="card dk comment" id="{pid}"><i class="av"></i><div class="cbody"><i class="sk" style="width:190px"></i>'
                      f'<div class="ctext"><b id="{pid}T"></b><i class="caret" id="{pid}C"></i></div></div>'
                      f'<span class="heart" id="{pid}H">{icon("heart", 36, "#8b8b96", 2)}</span></div>')
        self.blur_in(f'#{pid}', at, .36, .8)
        self.typed(f'#{pid}T', keyword, *type_span)
        self.blink(f'#{pid}C', at, self.total)
        if heart_at is not None:
            self.ft(f'#{pid}H', {'scale': 1}, {'scale': 1.25}, heart_at, .15); self.to(f'#{pid}H', {'scale': 1}, heart_at + 5, .2)
            self.to(f'#{pid}H svg', {'fill': '#ef4444', 'stroke': '#ef4444'}, heart_at, .1)
        if chips:
            self.row(top + 250, ''.join(f'<div class="pill dk chip" id="{pid}K{i}" style="margin:0 11px">{icon(ic, 34, "#fff", 2)}<b>{t}</b></div>'
                                        for i, (ic, t, _) in enumerate(chips)))
            for i, (_, _, f) in enumerate(chips):
                self.pop(f'#{pid}K{i}', f)

    def cursor_click(self, pid, x, y, at, click_at):
        """Hand cursor glides in to (x, y) (its top-left; the fingertip sits ~(26, 8) inside) and clicks."""
        self.add(f'<div class="cursor" id="{pid}">{CURSOR}</div>')
        self.ft(f'#{pid}', {'opacity': 0, 'x': x + 220, 'y': y + 300}, {'opacity': 1, 'x': x, 'y': y}, at, .4)
        self.ft(f'#{pid}', {'scale': 1}, {'scale': .82}, click_at - 1, .08, 'power1.out'); self.to(f'#{pid}', {'scale': 1}, click_at + 2, .12)

    def title(self, pid, text, top, at):
        """Big white title over the camera (the name drop). Pair with a None caption so the words don't double."""
        self.row(top, f'<div class="title" id="{pid}">{text}</div>')
        self.ft(f'#{pid}', {'opacity': 0, 'scale': 1.45, 'filter': 'blur(18px)'}, {'opacity': 1, 'scale': 1, 'filter': 'blur(0px)'}, at, .32, 'power4.out')

    # ---------------------------------------------------------------- compile
    def compile(self, title='breakout-card reel'):
        out, T, total = self.out, self.T, self.total
        (out / 'assets/fonts').mkdir(parents=True, exist_ok=True)
        shutil.copy2(find_gsap(out), out / 'assets/gsap.min.js')
        for f in (ASSETS / 'fonts').glob('*'):
            shutil.copy2(f, out / 'assets/fonts' / f.name)
        for m in self.plates + self.media:
            dst = out / 'assets' / m.name
            if not dst.exists() or dst.stat().st_mtime < m.stat().st_mtime:
                shutil.copy2(m, dst)
        d = T(total)
        page, cam = (f'assets/{p.name}' for p in self.plates)
        caps = ''.join(f'<div class="cap {c}" id="cap{k}"><span>{t}</span></div>' for k, (t, a, b, c) in enumerate(self.caps))
        body = (f'<div id="root" data-composition-id="main" data-start="0" data-duration="{d}" data-width="1080" data-height="1920"><div class="bg"></div>'
                f'<div id="pagePane" class="pane"><video id="pageV" class="clip" data-layout-allow-overflow src="{page}" data-start="0" data-duration="{d}" data-track-index="0" muted playsinline></video></div>'
                f'<div id="camPane" class="pane"><video id="camV" class="clip" data-layout-allow-overflow src="{cam}" data-start="0" data-duration="{d}" data-track-index="0" muted playsinline></video></div>'
                + ''.join(self.H) + caps + '</div>')
        first_page = self.lay[0][0] == 'page'
        pre = ['const tl=gsap.timeline({paused:true});window.__timelines={main:tl};',
               f'gsap.set("#pagePane",{{opacity:{int(first_page)}}});gsap.set("#camPane",{{opacity:{int(not first_page)},scale:1}});']
        pre += [f'gsap.set("#{k}",{{opacity:{int(a == 0)}}});' for k, (a, b) in self.scenes.items()]
        pre += [x + ';' for x in self.init]
        J0, self.J = self.J, []
        for sp in self.lay:
            kind, a, b = sp[:3]
            self.s('#pagePane', {'opacity': int(kind == 'page')}, a)
            self.s('#camPane', {'opacity': int(kind != 'page')}, a)
            if kind == 'camz':
                self.ft('#camPane', {'scale': sp[3]}, {'scale': sp[4]}, a, T(b - a), 'none')
            elif kind == 'cam':
                self.s('#camPane', {'scale': 1}, a)
        for k, (a, b) in self.scenes.items():
            self.s(f'#{k}', {'opacity': 1}, a); self.s(f'#{k}', {'opacity': 0}, b)
        for k, (t, a, b, c) in enumerate(self.caps):
            self.ft(f'#cap{k}', {'opacity': 1, 'scale': .9}, {'opacity': 1, 'scale': 1}, a, .1, 'power2.out')
            self.s(f'#cap{k}', {'opacity': 0}, b)
        lay, self.J = self.J, J0
        js = '\n'.join(pre + lay + self.J + [f'tl.set({{}},{{}},{d});'])
        tok = ':root{' + ''.join(f'--{k}:{v};' for k, v in self.tokens.items()) + '}'
        css = tok + (ASSETS / 'breakout-card.css').read_text() + '\n'.join(self.extra_css)
        html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><script src="assets/gsap.min.js"></script>'
                f'<link rel="stylesheet" href="style.css"></head><body>{body}<script>{js}</script></body></html>')
        (out / 'index.html').write_text(html)
        (out / 'style.css').write_text(css)
        (out / 'hyperframes.json').write_text('{"media": {"autoProxy": false}}')
        (out / 'captions.json').write_text(json.dumps([{'text': t, 'start': a, 'end': b, 'style': c} for t, a, b, c in self.caps], indent=1))
        (out / 'timeline.js').write_text(js)
        chk = subprocess.run(['node', '--check', str(out / 'timeline.js')], capture_output=True, text=True)
        (out / 'timeline.js').unlink()
        if chk.returncode:
            raise SystemExit('timeline script failed node --check:\n' + chk.stderr)
        return out
