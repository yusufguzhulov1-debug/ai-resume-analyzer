#!/usr/bin/env python3
"""Trace a photo into posterized closed polygons. No pixels in the output, only coordinates.
Output: a JS snippet `const PORTRAIT={w,h,levels:[{t,p:[[x,y,...],...]}]}` (brightness levels -> polygons).

  python3 trace.py photo.jpg --out portrait.js --preview preview.png
  options: --height 800 --blur 1.4 --levels 0.16,0.30,0.46,0.62,0.80 --tol 0.9 --minarea 24
           --crop x0,y0,x1,y1 --bgthr 0.86 --nobg --nocontrast
Needs numpy, scipy, Pillow. No OpenCV required (pure numpy marching squares).
"""
import argparse, json, sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageDraw
from scipy import ndimage

def load(path, crop, height, blur, contrast=True):
    im = Image.open(path).convert('L')
    if crop: im = im.crop(crop)
    w, h = im.size
    im = im.resize((round(w*height/h), height), Image.LANCZOS)
    if contrast: im = ImageOps.autocontrast(im, cutoff=0.2)
    if blur > 0: im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, dtype=np.float32)/255.0

def remove_background(a, thr):
    """Background = bright region connected to the top edge and upper corners."""
    H, W = a.shape
    lab, n = ndimage.label(a > thr)
    seeds = set(int(v) for v in np.concatenate([lab[0,:], lab[:H//3,0], lab[:H//3,W-1]]) if v > 0)
    mask = np.isin(lab, list(seeds)) if seeds else np.zeros_like(a, dtype=bool)
    mask = ndimage.binary_dilation(mask, iterations=2)
    out = a.copy(); out[mask] = 0.0
    return out, mask

# --- vectorized marching squares ---
# bits: tl=8 tr=4 br=2 bl=1; edges: 0=top 1=right 2=bottom 3=left
TABLE = {1:[(3,2)],14:[(3,2)],2:[(2,1)],13:[(2,1)],3:[(3,1)],12:[(3,1)],4:[(0,1)],11:[(0,1)],
         6:[(0,2)],9:[(0,2)],7:[(0,3)],8:[(0,3)]}

def edge_ids(js, is_, e, W):
    # top=h(i,j) bottom=h(i,j+1) left=v(i,j) right=v(i+1,j); h -> even ids, v -> odd ids
    if e == 0: return 2*(js*W+is_)
    if e == 2: return 2*((js+1)*W+is_)
    if e == 3: return 2*(js*W+is_)+1
    return 2*(js*W+is_+1)+1

def isolines(a, T):
    a = np.pad(a, 1, constant_values=0.0)
    H, W = a.shape
    b = a >= T
    case = (b[:-1,:-1].astype(np.uint8)<<3)|(b[:-1,1:].astype(np.uint8)<<2)|(b[1:,1:].astype(np.uint8)<<1)|b[1:,:-1].astype(np.uint8)
    A, B = [], []
    for c, segs in TABLE.items():
        js, is_ = np.nonzero(case == c)
        if js.size == 0: continue
        for (e1, e2) in segs:
            A.append(edge_ids(js, is_, e1, W)); B.append(edge_ids(js, is_, e2, W))
    for c in (5, 10):
        js, is_ = np.nonzero(case == c)
        if js.size == 0: continue
        center = (a[js,is_]+a[js,is_+1]+a[js+1,is_]+a[js+1,is_+1])/4 >= T
        if c == 5:   # tr+bl inside
            segs_in, segs_out = [(0,3),(1,2)], [(0,1),(3,2)]
        else:        # tl+br inside
            segs_in, segs_out = [(0,1),(3,2)], [(0,3),(1,2)]
        for m, segs in ((center, segs_in), (~center, segs_out)):
            if not m.any(): continue
            for (e1, e2) in segs:
                A.append(edge_ids(js[m], is_[m], e1, W)); B.append(edge_ids(js[m], is_[m], e2, W))
    if not A: return []
    A = np.concatenate(A); B = np.concatenate(B); N = A.size
    ends = np.concatenate([A, B])
    order = np.argsort(ends, kind='stable')
    se = ends[order]
    if N and not np.array_equal(se[0::2], se[1::2]):
        raise RuntimeError('open contours: check padding')
    pos = np.empty_like(order); pos[order] = np.arange(order.size)
    partner = order[pos ^ 1]          # for each endpoint entry: the partner entry sharing the same edge
    partner = partner.tolist()
    visited = np.zeros(N, dtype=bool)
    loops = []
    for s0 in range(N):
        if visited[s0]: continue
        loop = []; s = s0; side = 0     # enter through endpoint A
        while True:
            visited[s] = True
            exit_entry = s + N if side == 0 else s
            loop.append(int(A[s]) if side == 0 else int(B[s]))
            p = partner[exit_entry]
            s = p % N; side = 0 if p < N else 1
            if s == s0: break
        loops.append(np.array(loop, dtype=np.int64))
    # point coordinates from edge ids (unpadded coordinates)
    out = []
    for ids in loops:
        i = (ids//2) % W; j = (ids//2)//W; horiz = (ids % 2 == 0)
        x = np.empty(ids.size, np.float32); y = np.empty(ids.size, np.float32)
        h = horiz
        v0 = a[j[h], i[h]]; v1 = a[j[h], i[h]+1]; t = np.clip((T-v0)/np.where(v1-v0==0, 1e-6, v1-v0), 0, 1)
        x[h] = i[h]+t; y[h] = j[h]
        v = ~horiz
        v0 = a[j[v], i[v]]; v1 = a[j[v]+1, i[v]]; t = np.clip((T-v0)/np.where(v1-v0==0, 1e-6, v1-v0), 0, 1)
        x[v] = i[v]; y[v] = j[v]+t
        out.append(np.stack([x-1, y-1], axis=1))
    return out

def simplify(P, tol):
    """Douglas-Peucker for a closed contour."""
    n = len(P)
    if n < 4: return P
    keep = np.zeros(n, dtype=bool); keep[0] = True
    # split the closed contour at the two farthest points
    far = int(np.argmax(((P - P[0])**2).sum(1))); keep[far] = True
    stack = [(0, far), (far, n-1)]
    keep[n-1] = True
    while stack:
        i0, i1 = stack.pop()
        if i1 - i0 < 2: continue
        seg = P[i0:i1+1]; a = seg[0]; b = seg[-1]; d = b - a; L = np.hypot(*d)
        if L < 1e-9: dist = np.hypot(*(seg - a).T)
        else: dist = np.abs(d[0]*(seg[:,1]-a[1]) - d[1]*(seg[:,0]-a[0]))/L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            keep[i0+k] = True; stack.append((i0, i0+k)); stack.append((i0+k, i1))
    return P[keep]

def area(P):
    x, y = P[:,0], P[:,1]
    return 0.5*abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('photo'); ap.add_argument('--out', default='portrait.js')
    ap.add_argument('--height', type=int, default=800); ap.add_argument('--blur', type=float, default=1.4)
    ap.add_argument('--levels', default='0.16,0.30,0.46,0.62,0.80'); ap.add_argument('--tol', type=float, default=0.9)
    ap.add_argument('--minarea', type=float, default=24); ap.add_argument('--crop', default=None)
    ap.add_argument('--bgthr', type=float, default=0.86); ap.add_argument('--nobg', action='store_true')
    ap.add_argument('--preview', default=None); ap.add_argument('--nocontrast', action='store_true')
    A = ap.parse_args()
    crop = tuple(int(v) for v in A.crop.split(',')) if A.crop else None
    a = load(A.photo, crop, A.height, A.blur, not A.nocontrast)
    if not A.nobg: a, bgmask = remove_background(a, A.bgthr)
    H, W = a.shape
    levels = [float(v) for v in A.levels.split(',')]
    result = []; total_pts = 0
    for T in levels:
        polys = []
        for P in isolines(a, T):
            if len(P) < 4 or area(P) < A.minarea: continue
            Sm = simplify(P, A.tol)
            if len(Sm) < 3: continue
            polys.append([int(round(v)) for v in Sm.ravel()])
            total_pts += len(Sm)
        result.append({'t': T, 'p': polys})
        print(f'level {T:.2f}: {len(polys)} contours', file=sys.stderr)
    js = 'const PORTRAIT=' + json.dumps({'w': W, 'h': H, 'levels': result}, separators=(',', ':')) + ';\n'
    open(A.out, 'w').write(js)
    print(f'{A.out}: {W}x{H}, {total_pts} points, {len(js)//1024} KB', file=sys.stderr)
    if A.preview:
        # raster preview of the posterization + contours, for eyes only
        q = np.zeros_like(a)
        for k, T in enumerate(levels): q[a >= T] = (k+1)/len(levels)
        im = Image.fromarray((q*255).astype(np.uint8)).convert('RGB')
        d = ImageDraw.Draw(im)
        for lv in result:
            for poly in lv['p']:
                pts = list(zip(poly[0::2], poly[1::2]))
                d.line(pts + [pts[0]], fill=(255, 80, 80), width=1)
        im.save(A.preview)

if __name__ == '__main__':
    main()
