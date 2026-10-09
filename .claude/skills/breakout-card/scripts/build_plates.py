#!/usr/bin/env python3
"""Camera plates for the breakout-card style.

page plate : white grid page, the speaker in a rounded card along the bottom, head (and raised hands) breaking out above it
cam plate  : the same graded camera, full frame

    build_plates.py prep   <camera.mp4> <plate-dir> [--matte <matte.mp4>]
                                                               CFR copy + person matte (Apple Vision on macOS, or your own
                                                               white-on-black matte video from any segmentation tool)
    build_plates.py still  <plate-dir> <t> [<t> ...] [--set key=json ...]   tuning stills -> <plate-dir>/stills/
    build_plates.py render <plate-dir> [--set key=json ...]    page-plate.mp4 + cam-plate.mp4

Settings live in <plate-dir>/plates.json; --set updates them (e.g. --set cutRow=890
--set 'objectKeys=[{"box":[420,600,670,760],"rgb":[52,36,48]}]'), so the render uses exactly what the stills approved.
Canvas is 1080x1920 at the camera's frame rate; the camera plate must already be the final cut (silent is fine).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
import cv2

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
DEFAULTS = {
    'fps': 30,
    'cutRow': 890,                    # source row placed on the card's top edge: just above the eyes/glasses
    'card': {'x': 60, 'w': 960, 'top': 1395, 'r': 18},
    'grade': {'sat': 0.86, 'contrast': 1.05, 'lift': 2},
    'grid': {'cell': 54, 'paper': [252, 252, 253], 'ink': [234, 234, 239]},
    'bgKey': {'on': True, 'near': 10, 'far': 22},   # remove pixels near the sampled wall colour, at the silhouette edge only
    'objectKeys': [],                 # [{"box":[x0,y0,x1,y1], "rgb":[r,g,b], "near":14, "far":26}] for wall items right behind the head
    'protect': 36,                    # px inside the silhouette that keys never touch (glasses, eyes)
}


def load(plate_dir, overrides=()):
    p = Path(plate_dir) / 'plates.json'
    cfg = {**DEFAULTS, **(json.loads(p.read_text()) if p.exists() else {})}
    for o in overrides:
        k, v = o.split('=', 1)
        cfg[k] = json.loads(v)
    p.write_text(json.dumps(cfg, indent=1))
    return cfg


# ------------------------------------------------------------------ prep: CFR plate + matte
def matte_binary():
    if sys.platform != 'darwin':
        raise SystemExit('Built-in matting uses Apple Vision (macOS). Elsewhere pass --matte <white-on-black matte video>.')
    src = HERE / 'person-matte.swift'
    out = Path.home() / 'Library/Caches/breakout-card/person-matte'
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['swiftc', '-O', str(src), '-o', str(out)], check=True, capture_output=True)
    return out


def prep(camera, plate_dir, matte=None):
    d = Path(plate_dir)
    d.mkdir(parents=True, exist_ok=True)
    cfg = load(d)
    cfr = d / 'camera-cfr.mp4'
    # cut plates often carry 1-frame timestamp gaps at cut points; the matte must stay frame-locked
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', camera, '-vf', f'fps={cfg["fps"]},scale={W}:{H}', '-an', '-c:v', 'libx264', '-crf', '12',
                    '-preset', 'slow', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', cfr], check=True)
    if matte:      # any white-on-black person matte at the camera's timing (e.g. from a background-removal tool)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', matte, '-vf', f'fps={cfg["fps"]},scale={W}:{H},format=gray', '-c:v', 'ffv1',
                        '-level', '3', d / 'matte.mkv'], check=True)
    else:          # macOS: Apple Vision person segmentation, stateful across frames
        m = subprocess.Popen([str(matte_binary()), str(cfr), str(W), str(H)], stdout=subprocess.PIPE)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', str(cfg['fps']), '-i', '-',
                        '-c:v', 'ffv1', '-level', '3', d / 'matte.mkv'], stdin=m.stdout, check=True)
        m.wait()
    frames = [subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', f],
                             capture_output=True, text=True).stdout.strip() for f in (cfr, d / 'matte.mkv')]
    cfg.update(camera=str(Path(camera).resolve()), frames=int(frames[0]))
    (d / 'plates.json').write_text(json.dumps(cfg, indent=1))
    print('camera / matte frames:', *frames)
    if frames[0] != frames[1]:
        raise SystemExit('matte is not frame-locked to the camera')


# ------------------------------------------------------------------ compositing
def grid_page(g):
    page = np.zeros((H, W, 3), np.uint8)
    page[:] = g['paper']
    for x in range(W // 2 % g['cell'], W, g['cell']):
        page[:, max(0, x - 1):x + 1] = g['ink']
    for y in range(0, H, g['cell']):
        page[max(0, y - 1):y + 1, :] = g['ink']
    return page


def grade(rgb, g):
    f = rgb.astype(np.float32)
    lum = f @ np.array([0.299, 0.587, 0.114], np.float32)
    f = lum[..., None] + (f - lum[..., None]) * g['sat']
    return np.clip((f - 128) * g['contrast'] + 128 + g['lift'], 0, 255).astype(np.uint8)


def ramp(x, near, far):
    return np.clip((x - near) / max(1e-3, far - near), 0, 1)


def refine_alpha(matte, rgb, cfg):
    """Vision matte, cleaned at the silhouette edge: wall-coloured fringe and wall objects removed, smooth cut-out line."""
    m = np.clip((matte.astype(np.float32) / 255 - 0.12) / 0.76, 0, 1)
    body = (m > 0.5).astype(np.uint8)
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    inner = cv2.erode(body, k(cfg['protect']))
    f = rgb.astype(np.float32)
    keep = np.ones(m.shape, np.float32)
    bk = cfg['bgKey']
    if bk.get('on'):
        ring = (cv2.dilate(body, k(40)) > 0) & (cv2.dilate(body, k(12)) == 0) & (m < 0.05)
        ring[cfg['cutRow'] + 40:] = False                      # sample the wall around the part that breaks out
        if ring.sum() > 400:
            bg = np.median(f[ring], axis=0)
            keep *= ramp(np.linalg.norm(f - bg, axis=2), bk['near'], bk['far'])
    for ok in cfg['objectKeys']:
        x0, y0, x1, y1 = ok['box']
        hit = np.zeros(m.shape, np.float32)
        hit[y0:y1, x0:x1] = 1 - ramp(np.linalg.norm(f[y0:y1, x0:x1] - np.float32(ok['rgb']), axis=2), ok.get('near', 14), ok.get('far', 26))
        keep *= 1 - cv2.dilate(hit, np.ones((5, 5), np.uint8))
    a = np.where(inner > 0, 1.0, m * keep).astype(np.float32)
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, k(3))
    a = np.clip((cv2.GaussianBlur(a, (0, 0), 3.0) - 0.32) / 0.36, 0, 1)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 0.05).astype(np.uint8), 8)
    if n > 2:                                                  # keep the person, drop detached wall bits
        a = np.where(lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA])), a, 0).astype(np.float32)
    return cv2.GaussianBlur(a, (0, 0), 0.9)


def card_mask(c):
    ss = 4
    m = np.zeros(((H - c['top']) * ss, W * ss), np.uint8)
    x0, x1, r = c['x'] * ss, (c['x'] + c['w']) * ss, c['r'] * ss
    cv2.rectangle(m, (x0 + r, 0), (x1 - r, m.shape[0]), 255, -1)
    cv2.rectangle(m, (x0, r), (x1, m.shape[0]), 255, -1)
    cv2.circle(m, (x0 + r, r), r, 255, -1, cv2.LINE_AA)
    cv2.circle(m, (x1 - r, r), r, 255, -1, cv2.LINE_AA)
    full = np.zeros((H, W), np.float32)
    full[c['top']:] = cv2.resize(m, (W, H - c['top']), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return full[..., None]


class Plates:
    def __init__(self, cfg):
        self.cfg, c = cfg, cfg['card']
        self.page = grid_page(cfg['grid']).astype(np.float32)
        self.card = card_mask(c)
        self.scale = c['w'] / W                                 # the camera's full width fills the card
        self.sh = int(round(H * self.scale))
        self.y0 = int(round(c['top'] - cfg['cutRow'] * self.scale))

    def frame(self, cam, matte):
        c, g = self.cfg['card'], grade(cam, self.cfg['grade'])
        scaled = cv2.resize(g, (c['w'], self.sh), interpolation=cv2.INTER_AREA)
        alpha = cv2.resize(refine_alpha(matte, cam, self.cfg), (c['w'], self.sh), interpolation=cv2.INTER_LINEAR)
        layer, a = np.zeros((H, W, 3), np.float32), np.zeros((H, W), np.float32)
        ys, ye = max(0, self.y0), min(H, self.y0 + self.sh)
        layer[ys:ye, c['x']:c['x'] + c['w']] = scaled[ys - self.y0:ye - self.y0]
        a[ys:ye, c['x']:c['x'] + c['w']] = alpha[ys - self.y0:ye - self.y0]
        a[c['top']:] = 0                                        # inside the card the box decides
        a = np.maximum(a[..., None], self.card)
        return np.clip(self.page * (1 - a) + layer * a, 0, 255).astype(np.uint8), g


def reader(path, pix, ch):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', pix, '-'], stdout=subprocess.PIPE)
    n = W * H * ch
    while len(b := p.stdout.read(n)) == n:
        yield np.frombuffer(b, np.uint8).reshape((H, W, ch) if ch > 1 else (H, W))


def writer(path, fps):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
                             '-c:v', 'libx264', '-crf', '13', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-g', '30', '-color_primaries', 'bt709',
                             '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', path], stdin=subprocess.PIPE)


def still(plate_dir, ts, cfg):
    d = Path(plate_dir)
    (d / 'stills').mkdir(exist_ok=True)
    pl = Plates(cfg)
    for t in ts:
        cam = subprocess.run(['ffmpeg', '-v', 'error', '-ss', t, '-i', d / 'camera-cfr.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True).stdout
        mat = subprocess.run(['ffmpeg', '-v', 'error', '-ss', t, '-i', d / 'matte.mkv', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                             capture_output=True, check=True).stdout
        page, _ = pl.frame(np.frombuffer(cam, np.uint8).reshape(H, W, 3), np.frombuffer(mat, np.uint8).reshape(H, W))
        out = d / 'stills' / f'page-{t}.png'
        cv2.imwrite(str(out), cv2.cvtColor(page, cv2.COLOR_RGB2BGR))
        print(out)


def render(plate_dir, cfg):
    d, pl = Path(plate_dir), Plates(cfg)
    wp, wc = writer(d / 'page-plate.mp4', cfg['fps']), writer(d / 'cam-plate.mp4', cfg['fps'])
    n = 0
    for cam, mat in zip(reader(d / 'camera-cfr.mp4', 'rgb24', 3), reader(d / 'matte.mkv', 'gray', 1)):
        page, g = pl.frame(cam, mat)
        wp.stdin.write(page.tobytes()); wc.stdin.write(g.tobytes())
        n += 1
        if n % 300 == 0:
            print('frames', n, flush=True)
    for w in (wp, wc):
        w.stdin.close(); w.wait()
    print('done', n, 'frames ->', d / 'page-plate.mp4', d / 'cam-plate.mp4')


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    sets = [a for i, a in enumerate(args) if i and args[i - 1] == '--set']
    rest = [a for i, a in enumerate(args) if a != '--set' and not (i and args[i - 1] == '--set')]
    if cmd == 'prep':
        mi = args.index('--matte') if '--matte' in args else None
        if mi is not None:
            rest = [a for a in rest if a not in ('--matte', args[mi + 1])]
        prep(rest[0], rest[1], args[mi + 1] if mi is not None else None)
    elif cmd == 'still':
        still(rest[0], rest[1:], load(rest[0], sets))
    elif cmd == 'render':
        render(rest[0], load(rest[0], sets))
    else:
        raise SystemExit(__doc__)
