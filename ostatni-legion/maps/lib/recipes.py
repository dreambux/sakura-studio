"""Przepisy tekstur: pola szumu wypiekane w Blenderze (tex.field) + okresowy Voronoi (numpy).
Wszystko bezszwowe. Kazda tekstura: <nazwa>_col.png (sRGB) + <nazwa>_nrm.png (normal OpenGL)."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .tex import (field, norm, ramp, mix, smooth, uv_grid, cells, edge_dist, save, strokes, TAU)

C = lambda c: np.array(c, np.float32) / 255.0  # noqa: E731


# ------------------------------------------------------------------ okresowy Voronoi (ostre krawedzie)
_VOR = {}


def vor(size, n, seed=0, aniso=(1.0, 1.0), jitter=0.9):
    """Zwraca (F1 px, odleglosc do krawedzi px, losowa wartosc komorki 0-1, nr komorki).
    Punkty na siatce g x g z jitterem -> sprawdzamy tylko 5x5 sasiednich komorek."""
    key = (size, n, seed, aniso, jitter)
    if key in _VOR:
        return _VOR[key]
    rng = np.random.default_rng(seed)
    g = max(2, int(round(math.sqrt(n))))
    jx = (jitter * (rng.random((g, g)) - 0.5)).astype(np.float32)
    jy = (jitter * (rng.random((g, g)) - 0.5)).astype(np.float32)
    rnd = rng.random((g, g)).astype(np.float32)
    ax, ay = aniso
    F1 = np.zeros((size, size), np.float32)
    ED = np.zeros((size, size), np.float32)
    ID = np.zeros((size, size), np.int32)
    offs = [(dx, dy) for dy in range(-2, 3) for dx in range(-2, 3)]
    step = max(16, int(4_000_000 / (size * len(offs))))
    xs = (np.arange(size, dtype=np.float32) + 0.5) / size
    for r0 in range(0, size, step):
        ys = xs[r0:r0 + step]
        X, Y = np.meshgrid(xs, ys)
        cx = np.floor(X * g).astype(np.int32)
        cy = np.floor(Y * g).astype(np.int32)
        ds, ids, pxs, pys = [], [], [], []
        for dx, dy in offs:
            gx = (cx + dx) % g
            gy = (cy + dy) % g
            px = (cx + dx + 0.5 + jx[gy, gx]) / g
            py = (cy + dy + 0.5 + jy[gy, gx]) / g
            ddx = (X - px) * ax
            ddy = (Y - py) * ay
            ds.append(ddx * ddx + ddy * ddy)
            ids.append(gy * g + gx)
            pxs.append(px)
            pys.append(py)
        D = np.stack(ds, -1)
        I = np.stack(ids, -1)
        PX = np.stack(pxs, -1)
        PY = np.stack(pys, -1)
        o = np.argsort(D, axis=-1)[..., :2]
        d1 = np.take_along_axis(D, o[..., :1], -1)[..., 0]
        d2 = np.take_along_axis(D, o[..., 1:2], -1)[..., 0]
        p1x = np.take_along_axis(PX, o[..., :1], -1)[..., 0]
        p1y = np.take_along_axis(PY, o[..., :1], -1)[..., 0]
        p2x = np.take_along_axis(PX, o[..., 1:2], -1)[..., 0]
        p2y = np.take_along_axis(PY, o[..., 1:2], -1)[..., 0]
        sep = np.sqrt(((p1x - p2x) * ax) ** 2 + ((p1y - p2y) * ay) ** 2) + 1e-6
        F1[r0:r0 + step] = np.sqrt(d1) * size
        ED[r0:r0 + step] = (d2 - d1) / (2 * sep) * size
        ID[r0:r0 + step] = np.take_along_axis(I, o[..., :1], -1)[..., 0]
    out = (F1, ED, rnd.ravel()[ID], ID)
    _VOR[key] = out
    return out


def palette_pick(rid, cols):
    return ramp(rid, [(i / (len(cols) - 1), c) for i, c in enumerate(cols)])


# ------------------------------------------------------------------ wspolny styl (jak w TDS)
from . import tex as _tex
import zlib

# cracks = siec cienkich pekniec, pits = drobne wglebienia, mottle = miekkie plamy, desat = odbarwienie
STYLE_DEFAULT = dict(cracks=0.0, pits=0.0, mottle=0.08, desat=0.18, contrast=0.9, moss=0.0)
STYLE = {}


def style(name, **kw):
    STYLE[name] = kw


def finish(name, col, h):
    st = dict(STYLE_DEFAULT, **STYLE.get(name, {}))
    size = col.shape[0]
    sd = zlib.crc32(name.encode()) % 1000
    lum = (col * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1, keepdims=True)
    col = mix(col, np.broadcast_to(lum, col.shape), st['desat'])
    m = col.mean(axis=(0, 1), keepdims=True)
    col = m + (col - m) * st['contrast']
    if st['mottle']:
        mot = norm(field('noise', size, 2.5, seed=sd, detail=3))
        col = col * (1 - st['mottle'] + 2 * st['mottle'] * mot[..., None])
    if st['cracks']:
        _, ce, _, _ = vor(size, 26, sd + 1, jitter=1.0)
        _, ce2, _, _ = vor(size, 90, sd + 2, jitter=1.0)
        cov = smooth(0.35, 0.6, norm(field('noise', size, 3, seed=sd + 3, detail=3)))
        w = size / 1024.0
        crack = np.maximum(smooth(1.6 * w, 0.3 * w, ce), 0.6 * smooth(1.0 * w, 0.2 * w, ce2) * cov) * cov
        col = col * (1 - 0.35 * st['cracks'] * crack[..., None])
        h = h - 0.25 * st['cracks'] * crack
        if st['moss']:
            mz = smooth(5 * w, 0, np.minimum(ce, ce2)) * cov
            mn = smooth(0.55, 0.8, norm(field('noise', size, 18, seed=sd + 4, detail=4)))
            mm = np.clip(mz * 0.7 + mn * 0.6, 0, 1) * st['moss']
            col = mix(col, np.array([0.36, 0.46, 0.22], np.float32) * (0.8 + 0.4 * mn[..., None]), mm)
    if st['pits']:
        F1, _, rid, _ = vor(size, int(2200 * (size / 1024) ** 2), sd + 5, jitter=1.0)
        w = size / 1024.0
        pit = smooth(2.2 * w, 0.6 * w, F1) * (rid > 1 - 0.35 * st['pits'])
        rim = smooth(3.4 * w, 2.4 * w, F1) * (1 - smooth(2.4 * w, 2.0 * w, F1)) * (rid > 1 - 0.35 * st['pits'])
        col = col * (1 - 0.22 * pit[..., None]) * (1 + 0.08 * rim[..., None])
        h = h - 0.35 * pit + 0.1 * rim
    return np.clip(col, 0, 1), h


def save(name, col, h, strength, out, size_out=None):
    col, h = finish(name, col, h)
    return _tex.save(name, col, h, strength, out, size_out)


def earth(name, out, dark, light, size=1024, seed=63, lumps=0.5):
    """Ziemia jak w TDS: miekkie plamy, drobne grudki i wglebienia."""
    n = norm(field('noise', size, 3, seed=seed, detail=5))
    f = norm(field('noise', size, 18, seed=seed + 1, detail=4))
    col = mix(C(dark), C(light), 0.65 * n + 0.35 * f)
    F1, _, rid, _ = vor(size, int(1400 * lumps) + 50, seed + 2)
    r = 3.0 + 2.5 * rid
    lump = smooth(r, r - 1.5, F1) * (rid > 0.55)
    col = col * (1 + 0.12 * lump[..., None])
    return save(name, col, n * 0.3 + f * 0.3 + lump * 0.5, 3.0, out)


# ------------------------------------------------------------------ trawy
def grass(name, out, base_cols, stroke_cols, size=1024, seed=1, density=1.0, flowers=None):
    n1 = norm(field('noise', size, 3, seed=seed, detail=3))
    n2 = norm(field('noise', size, 12, seed=seed + 1, detail=3))
    base = ramp(n1 * 0.65 + n2 * 0.35, base_cols)
    dirf = norm(field('noise', size, 2.2, seed=seed + 2, detail=1))
    col, h = strokes(size, int(14000 * density * (size / 1024) ** 2), stroke_cols, dirf, length=(12, 30),
                     width=(3, 5), seed=seed, base=base, curl=0.8)
    col2, h2 = strokes(size, int(9000 * density * (size / 1024) ** 2), stroke_cols, dirf, length=(6, 14),
                       width=(2, 3), seed=seed + 9, base=col, curl=0.6)
    col = col2 * (0.82 + 0.3 * n1[..., None])
    h = np.maximum(h, h2)
    if flowers:
        rng = random.Random(seed + 5)
        im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for _ in range(int(500 * (size / 1024) ** 2)):
            x, y = rng.uniform(0, size), rng.uniform(0, size)
            c = flowers[rng.randrange(len(flowers))]
            r = rng.uniform(2, 4)
            for ox in (-size, 0, size):
                for oy in (-size, 0, size):
                    d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=c)
                    d.ellipse([x + ox - 1, y + oy - 1, x + ox + 1, y + oy + 1], fill=(250, 230, 120))
        col = np.asarray(im, np.float32) / 255
    return save(name, col, h * 0.7 + n2 * 0.3, 3.5, out)


# ------------------------------------------------------------------ podloza sypkie
def sand(name, out, light, dark, size=1024, seed=3, ripple=9, shells=False):
    u, v = uv_grid(size)
    n = norm(field('noise', size, 6, seed=seed, detail=4))
    big = norm(field('noise', size, 2, seed=seed + 1, detail=2))
    rip = 0.5 + 0.5 * np.sin(TAU * (v * ripple + u * 2 + n * 0.9)) if ripple else n
    grains = norm(field('noise', size, 120, seed=seed + 2, detail=1))
    t = 0.45 * big + 0.2 * rip + 0.35 * grains
    col = mix(C(dark), C(light), t)
    F1, ED, rid, _ = vor(size, 900, seed + 3)
    peb = smooth(5.0, 2.0, F1) * (rid > 0.82)
    col = mix(col, col * (0.7 + 0.5 * rid[..., None]), peb)
    return save(name, col, 0.45 * rip + 0.3 * grains + 0.5 * peb, 2.5, out)


def gravel(name, out, cols, gaps=(70, 62, 54), size=1024, seed=41, n=5000):
    """Zwir: drobne kanciaste kamyczki ciasno ulozone."""
    F1, ED, rid, _ = vor(size, n, seed, jitter=1.0)
    det = norm(field('noise', size, 80, seed=seed, detail=3))
    big = norm(field('noise', size, 3, seed=seed + 1, detail=2))
    stone = palette_pick(rid, cols) * (0.8 + 0.3 * det[..., None])
    m = smooth(0.6, 2.2, ED)
    col = mix(C(gaps), stone, m)
    col *= (0.7 + 0.3 * smooth(0, 5, ED))[..., None] * (0.9 + 0.15 * big[..., None])
    h = np.sqrt(np.clip(ED / 6.0, 0, 1)) * m
    return save(name, col, h, 7.0, out)


def pebbles(name, out, cols, ground=(120, 98, 70), size=1024, seed=43, n=420):
    """Kamyczki: okragle, gladkie otoczaki na ziemi."""
    F1, ED, rid, _ = vor(size, n, seed, jitter=0.95)
    r = size / math.sqrt(n) * (0.32 + 0.12 * rid)
    inside = smooth(r, r - 2.5, F1)
    dome = np.sqrt(np.clip(1 - (F1 / r) ** 2, 0, 1))
    det = norm(field('noise', size, 50, seed=seed, detail=3))
    gnd = C(ground) * (0.75 + 0.4 * norm(field('noise', size, 10, seed=seed + 1, detail=4)))[..., None]
    stone = palette_pick(rid, cols) * (0.65 + 0.45 * dome[..., None]) * (0.9 + 0.15 * det[..., None])
    col = mix(gnd, stone, inside)
    col *= (0.75 + 0.25 * smooth(r * 1.4, r, F1) + 0.25 * inside)[..., None]
    return save(name, col, dome * inside * 0.9 + det * 0.1, 6.0, out)


def clay(name, out, light=(184, 108, 66), dark=(132, 70, 40), size=1024, seed=45):
    """Glina / sucha ziemia z pekniecami (spekane bloki)."""
    F1, ED, rid, _ = vor(size, 60, seed, jitter=1.0)
    F1b, EDb, _, _ = vor(size, 260, seed + 1, jitter=1.0)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    big = norm(field('noise', size, 3, seed=seed + 1, detail=3))
    col = mix(C(dark), C(light), 0.5 * rid + 0.3 * det + 0.2 * big)
    crack = smooth(3.0, 0.5, ED)
    small = smooth(1.2, 0.2, EDb) * (det > 0.45)
    col *= (1 - 0.65 * crack - 0.3 * small)[..., None]
    col *= (0.85 + 0.2 * smooth(0, 25, ED))[..., None]
    h = smooth(0, 10, ED) - small * 0.3
    return save(name, col, h, 6.0, out)


def mud(name, out, size=1024, seed=47):
    n = norm(field('noise', size, 4, seed=seed, detail=6))
    f = norm(field('noise', size, 40, seed=seed + 1, detail=3))
    wet = smooth(0.55, 0.75, n)
    col = mix(C((104, 78, 54)), C((60, 44, 32)), wet)
    col *= (0.85 + 0.2 * f[..., None])
    return save(name, col, (1 - wet) * 0.6 + f * 0.3, 3.0, out)


def dirt_path(name, out, size=1024, seed=49):
    """Ubita ziemia sciezki: koleiny, kamyczki, plamy."""
    u, v = uv_grid(size)
    n = norm(field('noise', size, 5, seed=seed, detail=5))
    f = norm(field('noise', size, 50, seed=seed + 1, detail=3))
    col = mix(C((118, 90, 62)), C((168, 136, 98)), 0.6 * n + 0.4 * f)
    F1, ED, rid, _ = vor(size, 700, seed + 2)
    r = 4.5 + 3 * rid
    peb = smooth(r, r - 1.5, F1) * (rid > 0.55)
    col = mix(col, palette_pick(rid, [(120, 112, 100), (170, 160, 144), (96, 86, 76)]), peb)
    return save(name, col, n * 0.3 + f * 0.3 + peb * 0.6, 4.0, out)


# ------------------------------------------------------------------ kamien ukladany (sciezki, place)
def cobble(name, out, stone_cols, mortar, size=1024, seed=5, n=110, dirt=0.25, round_=1.0, mortar_w=4.0):
    F1, ED, rid, _ = vor(size, n, seed, jitter=0.8)
    det = norm(field('noise', size, 40, seed=seed + 1, detail=5))
    big = norm(field('noise', size, 3, seed=seed + 2, detail=3))
    speck = norm(field('noise', size, 160, seed=seed + 3, detail=1))
    stone = palette_pick(rid, stone_cols) * (0.8 + 0.25 * det + 0.1 * speck)[..., None]
    m = smooth(mortar_w * 0.5, mortar_w * 1.3, ED)
    bevel = smooth(mortar_w, mortar_w + 14 * round_, ED)
    col = mix(C(mortar) * (0.75 + 0.35 * det[..., None]), stone * (0.7 + 0.3 * bevel[..., None]), m)
    col = mix(col, col * C((210, 190, 160)), big[..., None] * dirt)
    h = bevel * m + det * 0.12
    return save(name, col, h, 7.0, out)


def flagstone(name, out, stone_cols, gap='grass', size=1024, seed=51, n=36):
    """Nieregularne plyty z trawa / ziemia w szczelinach (sciezka ogrodowa)."""
    F1, ED, rid, _ = vor(size, n, seed, jitter=1.0)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    stone = palette_pick(rid, stone_cols) * (0.8 + 0.3 * det[..., None])
    if gap == 'grass':
        gcol = ramp(norm(field('noise', size, 25, seed=seed + 1, detail=4)),
                    [(0, (46, 76, 30)), (1, (98, 130, 52))])
    else:
        gcol = ramp(norm(field('noise', size, 25, seed=seed + 1, detail=4)),
                    [(0, (90, 70, 50)), (1, (140, 110, 76))])
    w = 9 + 6 * norm(field('noise', size, 8, seed=seed + 2, detail=3))
    m = smooth(w * 0.6, w, ED)
    bevel = smooth(w, w + 16, ED)
    col = mix(gcol, stone * (0.72 + 0.28 * bevel[..., None]), m)
    return save(name, col, m * (0.6 + 0.4 * bevel) + det * 0.1, 6.0, out)


def slabs(name, out, cols_, rows_, colA, colB, grout, size=1024, seed=7, crack=0.5, offset=0.5, chip=0.4,
          grout_w=3.0):
    fx, fy, rid, cw, ch = cells(size, cols_, rows_, offset, seed)
    ed = edge_dist(fx, fy, cw, ch)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    big = norm(field('noise', size, 4, seed=seed + 1, detail=3))
    chipn = norm(field('noise', size, 20, seed=seed + 2, detail=3))
    base = mix(C(colA), C(colB), rid)
    base *= (0.85 + 0.25 * det * (0.6 + 0.4 * big))[..., None]
    gw = grout_w + chip * 5 * chipn
    m = smooth(gw * 0.6, gw * 1.4, ed)
    col = mix(C(grout), base, m)
    col *= (0.82 + 0.18 * smooth(0, 14, ed))[..., None]
    h = m * (0.7 + 0.3 * det)
    if crack > 0:
        _, ce, _, _ = vor(size, 30, seed + 3)
        cm = smooth(1.2, 0.0, ce) * (norm(field('noise', size, 3, seed=seed + 4)) > 1 - crack * 0.6)
        col = mix(col, col * 0.55, cm * 0.8)
        h = h - cm * 0.3
    return save(name, col, h, 5.0, out)


def mosaic(name, out, size=1024, seed=53):
    """Grecka mozaika: drobne kostki (tesserae) w meander + kolo."""
    u, v = uv_grid(size)
    N = 64
    fx, fy = (u * N) % 1, (v * N) % 1
    tx, ty = np.floor(u * N).astype(int), np.floor(v * N).astype(int)
    # wzor meandra (klucz grecki) na pasie i rozeta w srodku
    key = np.array([
        [1, 1, 1, 1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0, 0, 1, 0],
        [1, 0, 1, 1, 1, 0, 1, 0],
        [1, 0, 1, 0, 1, 0, 1, 0],
        [1, 0, 1, 0, 0, 0, 1, 0],
        [1, 0, 1, 1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1]], bool)
    band = ((ty % 32) < 8)
    kv = key[ty % 8, tx % 8]
    cx, cy = (tx % 32) - 15.5, (ty % 32) - 19.5
    rr = np.sqrt(cx * cx + cy * cy)
    ang = np.arctan2(cy, cx)
    rosette = (rr < 11) & ((np.cos(ang * 8) * 3 + 8) > rr)
    ring = (np.abs(rr - 11.5) < 0.8)
    rng = np.random.default_rng(seed)
    jit = rng.random((N + 1, N + 1)).astype(np.float32)[ty, tx]
    col = mix(C((226, 214, 186)), C((206, 192, 160)), jit)
    col = np.where((band & kv)[..., None], mix(C((40, 50, 70)), C((60, 70, 96)), jit), col)
    col = np.where((~band & rosette)[..., None], mix(C((168, 60, 40)), C((196, 90, 50)), jit), col)
    col = np.where((~band & ring)[..., None], mix(C((40, 50, 70)), C((60, 70, 96)), jit), col)
    e = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy)) * (size / N)
    g = smooth(0.4, 1.6, e)
    col = mix(C((120, 110, 92)), col, g)
    return save(name, col, g * 0.8, 4.0, out)


def meander(name, out, fg=(200, 150, 60), bg=(140, 40, 32), size=512, seed=55):
    """Pas z meandrem (klucz grecki) - do fryzow, obramowan, tkanin."""
    u, v = uv_grid(size)
    N = 16
    tx, ty = np.floor(u * N).astype(int), np.floor(v * N).astype(int)
    key = np.array([
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1],
        [1, 0, 1, 0, 0, 1, 0, 1],
        [1, 0, 1, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0]], bool)
    kv = key[ty % 16, tx % 8]
    det = norm(field('noise', size, 20, seed=seed, detail=4))
    col = np.where(kv[..., None], C(fg), C(bg)) * (0.85 + 0.2 * det[..., None])
    return save(name, col, kv.astype(np.float32) * 0.6 + det * 0.1, 3.0, out)


# ------------------------------------------------------------------ sciany, dachy, drewno
def plaster(name, out, base_col=(238, 232, 218), size=512, seed=11, dirt=(170, 150, 120)):
    n = norm(field('noise', size, 5, seed=seed, detail=5))
    f = norm(field('noise', size, 40, seed=seed + 1, detail=3))
    col = C(base_col) * (0.9 + 0.12 * f[..., None])
    col = mix(col, C(dirt), smooth(0.65, 1.0, n) * 0.35)
    _, ce, _, _ = vor(size, 18, seed + 2)
    cm = smooth(1.0, 0.0, ce) * (n > 0.6)
    col = mix(col, col * 0.7, cm)
    return save(name, col, f * 0.4 - cm * 0.3, 2.0, out)


def roof(name, out, colA=(176, 82, 46), colB=(140, 56, 34), size=512, seed=13, cols_=8, rows_=6):
    fx, fy, rid, cw, ch = cells(size, cols_, rows_, 0.5, seed)
    curve = np.sin(np.pi * fx)
    det = norm(field('noise', size, 25, seed=seed, detail=4))
    moss = smooth(0.7, 0.85, norm(field('noise', size, 5, seed=seed + 1, detail=4)))
    base = mix(C(colB), C(colA), rid * 0.7 + 0.3 * det)
    base = mix(base, C((96, 100, 60)), moss * 0.5)
    shade = (0.55 + 0.45 * curve) * (0.6 + 0.4 * smooth(0.0, 0.35, fy))
    return save(name, base * shade[..., None], curve * 0.7 + fy * 0.3, 6.0, out)


def wood(name, out, colA=(130, 86, 50), colB=(92, 58, 32), size=512, seed=15, planks=5):
    fx, fy, rid, cw, ch = cells(size, 1, planks, 0.0, seed)
    g = field('noise', size, 3, aniso=12, seed=seed, detail=6, distortion=0.6)
    grain = 0.5 + 0.5 * np.sin(TAU * (g * 8 + rid * 3))
    base = mix(C(colB), C(colA), 0.5 * grain + 0.5 * rid)
    gap = smooth(1.0, 3.5, np.minimum(fy, 1 - fy) * ch)
    _, ke, kid, _ = vor(size, 12, seed + 1, aniso=(0.4, 1.0))
    knot = smooth(6, 0, ke * 0 + vor(size, 12, seed + 1, aniso=(0.4, 1.0))[0]) * (kid > 0.6)
    base = mix(base, base * 0.55, knot)
    col = base * (0.35 + 0.65 * gap)[..., None]
    return save(name, col, gap * 0.8 + grain * 0.2, 4.0, out)


def bark(name, out, colA=(110, 90, 70), colB=(62, 50, 40), size=512, seed=17):
    n = norm(field('noise', size, 4, aniso=0.25, seed=seed, detail=6))
    _, e, rid, _ = vor(size, 120, seed + 1, aniso=(1.0, 0.3), jitter=1.0)
    col = mix(C(colB), C(colA), 0.6 * n + 0.4 * rid)
    cov = smooth(0.3, 0.6, norm(field('noise', size, 6, aniso=0.3, seed=seed + 3, detail=3)))
    cr = 1 - (1 - smooth(0.0, 3.0, e)) * cov
    col *= (0.4 + 0.6 * cr)[..., None]
    return save(name, col, cr * 0.8 + n * 0.2, 7.0, out)


def foliage(name, out, dark, mid, light, size=512, seed=19, n=240):
    """Liscie malowane mazniecciami (jak trawa) - ciemne kepy, jasniejsze wierzcholki."""
    big = norm(field('noise', size, 3, seed=seed + 1, detail=3))
    mid_n = norm(field('noise', size, 9, seed=seed + 2, detail=3))
    base = ramp(big * 0.6 + mid_n * 0.4, [(0, dark), (0.6, mid), (1, light)]) * 0.8
    dirf = norm(field('noise', size, 2.0, seed=seed + 3, detail=1))
    pal = [tuple(int(c * k) for c in col) for col in (dark, mid, light) for k in (0.85, 1.0, 1.1)]
    col, h = strokes(size, int(5200 * (size / 512) ** 2), pal, dirf, length=(5, 11), width=(4, 7), seed=seed,
                     base=base, curl=1.4)
    col = col * (0.7 + 0.45 * big[..., None])
    return save(name, col, h * 0.7 + big * 0.3, 4.0, out)


def pine_needles(name, out, size=512, seed=57):
    dirf = norm(field('noise', size, 2, seed=seed, detail=1))
    base = ramp(norm(field('noise', size, 6, seed=seed + 1, detail=3)), [(0, (16, 38, 22)), (1, (40, 70, 38))])
    col, h = strokes(size, 16000, [(30, 64, 34), (52, 92, 46), (22, 50, 28), (70, 110, 56)], dirf,
                     length=(10, 22), width=(1, 2), seed=seed, base=base, curl=0.2)
    return save(name, col, h, 4.0, out)


# ------------------------------------------------------------------ skaly
def rock(name, out, light=(150, 148, 142), dark=(92, 90, 88), size=512, seed=21, lichen=(120, 125, 70),
         lichen_amt=0.25, n=14):
    nn = norm(field('noise', size, 4, seed=seed, detail=6))
    f = norm(field('noise', size, 30, seed=seed + 1, detail=4))
    _, e, rid, _ = vor(size, n, seed + 2, jitter=1.0)
    _, e2, _, _ = vor(size, n * 6, seed + 5, jitter=1.0)
    col = mix(C(dark), C(light), 0.45 * nn + 0.3 * f + 0.25 * rid)
    cov = smooth(0.4, 0.65, norm(field('noise', size, 4, seed=seed + 6, detail=3)))
    cr = 1 - (1 - smooth(0.0, 2.0, e)) * cov
    cr = cr * (1 - (1 - smooth(0.0, 1.0, e2)) * cov * 0.5)
    col *= (0.55 + 0.45 * cr)[..., None]
    col *= (0.85 + 0.25 * norm(field('noise', size, 10, seed=seed + 7, detail=4)))[..., None]
    lm = smooth(0.62, 0.8, norm(field('noise', size, 6, seed=seed + 3, detail=4))) * lichen_amt * 3
    col = mix(col, C(lichen) * (0.8 + 0.4 * f[..., None]), np.clip(lm, 0, 0.8))
    return save(name, col, cr * 0.7 + f * 0.3, 6.0, out)


def strata(name, out, layers, size=512, seed=23, bands=6):
    u, v = uv_grid(size)
    nn = field('noise', size, 3, seed=seed, detail=5, distortion=0.4)
    t = (v * bands + nn * 1.6) % 1.0
    col = ramp(t, [(i / (len(layers) - 1), c) for i, c in enumerate(layers)])
    f = norm(field('noise', size, 30, seed=seed + 1, detail=4))
    _, e, _, _ = vor(size, 20, seed + 2)
    cr = smooth(0.0, 3.0, e)
    col *= ((0.75 + 0.25 * f) * (0.55 + 0.45 * cr))[..., None]
    step = smooth(0.0, 0.08, np.minimum(t, 1 - t))
    return save(name, col, step * 0.6 + cr * 0.4, 5.0, out)


def lava(name, out, size=512, seed=25):
    F1, e, rid, _ = vor(size, 40, seed, jitter=1.0)
    nn = norm(field('noise', size, 12, seed=seed + 1, detail=4))
    glow = smooth(9.0, 0.0, e)
    crust = ramp(nn, [(0, (20, 16, 16)), (1, (60, 46, 40))])
    hot = ramp(np.clip(glow + 0.2 * nn, 0, 1), [(0, (120, 20, 0)), (0.5, (255, 90, 10)), (1, (255, 230, 120))])
    return save(name, mix(crust, hot, glow), (1 - glow) * 0.8 + nn * 0.2, 5.0, out)


def snow(name, out, size=512, seed=27):
    nn = norm(field('noise', size, 4, seed=seed, detail=5))
    f = norm(field('noise', size, 60, seed=seed + 1, detail=2))
    col = mix(C((205, 215, 235)), C((250, 252, 255)), 0.7 * nn + 0.3 * f)
    return save(name, col, nn * 0.6 + f * 0.2, 2.0, out)


def marble(name, out, white=(236, 232, 224), vein=(150, 150, 160), size=512, seed=9):
    u, v = uv_grid(size)
    nn = field('noise', size, 3, seed=seed, detail=6, distortion=1.5)
    s = np.abs(np.sin(TAU * (u * 2 + v * 1 + nn * 3)))
    veins = smooth(0.12, 0.0, s)
    fine = norm(field('noise', size, 20, seed=seed + 1, detail=4))
    col = mix(C(white) * (0.93 + 0.07 * fine[..., None]), C(vein), veins * 0.75)
    return save(name, col, fine * 0.3, 1.0, out)


def bronze(name, out, size=512, seed=29):
    nn = norm(field('noise', size, 5, seed=seed, detail=5))
    f = norm(field('noise', size, 30, seed=seed + 1, detail=3))
    col = mix(C((150, 96, 44)), C((206, 146, 74)), f)
    col = mix(col, C((80, 130, 104)), smooth(0.72, 0.9, nn) * 0.45)
    return save(name, col, f * 0.3, 1.5, out)


def cloth(name, out, colA, colB=None, stripes=0, size=512, seed=31, border=None):
    u, v = uv_grid(size)
    weave = 0.5 + 0.25 * np.sin(TAU * u * 128) * np.sin(TAU * v * 128)
    nn = norm(field('noise', size, 6, seed=seed, detail=4))
    col = np.broadcast_to(C(colA), (size, size, 3)).copy()
    if stripes and colB:
        col = mix(col, C(colB), (np.floor(u * stripes) % 2))
    if border:
        bm = (np.abs(v - 0.5) > 0.42)
        col = np.where(bm[..., None], C(border), col)
    col *= (0.85 + 0.1 * weave + 0.1 * nn)[..., None]
    return save(name, col, weave * 0.4 + nn * 0.2, 1.5, out)


def terracotta(name, out, size=512, seed=59, painted=False):
    """Ceramika (amfory): glina z czarnym malowanym pasem i meandrem gdy painted."""
    u, v = uv_grid(size)
    nn = norm(field('noise', size, 8, seed=seed, detail=4))
    col = mix(C((168, 86, 44)), C((204, 120, 66)), nn)
    if painted:
        band = (np.abs(v - 0.5) < 0.16)
        col = np.where(band[..., None], C((28, 20, 18)), col)
        wave = (np.abs(v - 0.5 - 0.05 * np.sin(TAU * u * 6)) < 0.03)
        col = np.where(wave[..., None], C((214, 130, 70)), col)
        for y0 in (0.30, 0.70):
            col = np.where((np.abs(v - y0) < 0.012)[..., None], C((28, 20, 18)), col)
    return save(name, col, nn * 0.2, 1.0, out)


def water_ripple(name, out, size=512, seed=61):
    nn = norm(field('noise', size, 6, seed=seed, detail=4, distortion=0.8))
    col = mix(C((20, 90, 120)), C((70, 170, 190)), nn)
    return save(name, col, nn, 2.0, out)


# ------------------------------------------------------------------ cala biblioteka
LIBRARY = [
    # trawy
    ('grass_lush', lambda o: grass('grass_lush', o, [(0, (44, 74, 28)), (1, (84, 116, 44))],
                                   [(70, 110, 40), (98, 140, 52), (54, 88, 30), (124, 156, 62), (84, 122, 46)], seed=1)),
    ('grass_dry', lambda o: grass('grass_dry', o, [(0, (112, 108, 54)), (1, (166, 148, 80))],
                                  [(172, 156, 84), (138, 134, 64), (196, 176, 100), (116, 118, 56), (156, 140, 70)], seed=2)),
    ('grass_alpine', lambda o: grass('grass_alpine', o, [(0, (36, 70, 44)), (1, (66, 104, 66))],
                                     [(56, 98, 60), (80, 126, 78), (42, 80, 50), (100, 142, 90), (66, 108, 64)], seed=4)),
    ('grass_meadow', lambda o: grass('grass_meadow', o, [(0, (52, 84, 32)), (1, (96, 128, 50))],
                                     [(80, 122, 44), (104, 146, 56), (62, 98, 36), (130, 160, 66)], seed=5,
                                     flowers=[(230, 230, 240), (240, 200, 60), (200, 80, 160), (110, 140, 230)])),
    ('grass_ash', lambda o: grass('grass_ash', o, [(0, (48, 44, 40)), (1, (74, 66, 56))],
                                  [(70, 64, 56), (92, 82, 66), (54, 50, 46), (104, 74, 50), (62, 58, 52)], seed=6,
                                  density=0.7)),
    # sypkie
    ('sand', lambda o: sand('sand', o, (238, 216, 166), (198, 170, 120))),
    ('sand_white', lambda o: sand('sand_white', o, (246, 238, 214), (214, 200, 168), seed=9)),
    ('sand_wet', lambda o: sand('sand_wet', o, (170, 146, 106), (120, 100, 70), seed=10, ripple=14)),
    ('sand_volcanic', lambda o: sand('sand_volcanic', o, (96, 86, 80), (52, 46, 44), seed=4)),
    ('gravel', lambda o: gravel('gravel', o, [(150, 144, 134), (186, 178, 164), (118, 112, 104), (204, 196, 178)])),
    ('gravel_warm', lambda o: gravel('gravel_warm', o, [(196, 170, 130), (220, 198, 160), (160, 132, 96), (176, 150, 120)],
                                     gaps=(96, 76, 54), seed=42)),
    ('pebbles', lambda o: pebbles('pebbles', o, [(150, 144, 134), (178, 170, 156), (120, 114, 106), (168, 154, 128), (104, 100, 96)])),
    ('pebbles_beach', lambda o: pebbles('pebbles_beach', o, [(220, 214, 200), (190, 176, 150), (160, 154, 146), (236, 230, 216)],
                                        ground=(200, 176, 130), seed=44, n=300)),
    ('clay', lambda o: clay('clay', o)),
    ('clay_pale', lambda o: clay('clay_pale', o, (206, 172, 128), (164, 130, 92), seed=46)),
    ('mud', lambda o: mud('mud', o)),
    ('dirt_path', lambda o: dirt_path('dirt_path', o)),
    # sciezki z kamienia
    ('cobble', lambda o: cobble('cobble', o, [(150, 140, 126), (178, 168, 150), (128, 120, 110), (198, 188, 168)], (92, 80, 62))),
    ('cobble_warm', lambda o: cobble('cobble_warm', o, [(200, 170, 128), (176, 146, 106), (214, 190, 150), (160, 128, 92)],
                                     (110, 86, 60), seed=8)),
    ('cobble_dark', lambda o: cobble('cobble_dark', o, [(70, 64, 62), (96, 88, 82), (56, 52, 52), (110, 96, 86)],
                                     (36, 28, 26), seed=6, dirt=0.1)),
    ('cobble_small', lambda o: cobble('cobble_small', o, [(160, 154, 144), (188, 180, 166), (136, 130, 122), (174, 160, 140)],
                                      (100, 90, 74), seed=12, n=420, round_=0.5, mortar_w=2.5)),
    ('flagstone_grass', lambda o: flagstone('flagstone_grass', o, [(170, 164, 150), (196, 188, 170), (146, 140, 130), (184, 172, 150)])),
    ('flagstone_dirt', lambda o: flagstone('flagstone_dirt', o, [(196, 176, 140), (214, 196, 160), (170, 150, 116)], gap='dirt', seed=52)),
    ('paving', lambda o: slabs('paving', o, 3, 6, (232, 222, 200), (208, 196, 172), (150, 134, 108))),
    ('paving_marble', lambda o: slabs('paving_marble', o, 2, 2, (240, 236, 226), (220, 214, 202), (170, 160, 140), seed=9,
                                      offset=0.0, crack=0.35, grout_w=2.0)),
    ('paving_red', lambda o: slabs('paving_red', o, 4, 4, (196, 120, 82), (170, 98, 66), (110, 72, 50), seed=8, offset=0.0)),
    ('paving_basalt', lambda o: slabs('paving_basalt', o, 3, 5, (78, 72, 70), (56, 52, 52), (30, 24, 22), seed=10, crack=0.6)),
    ('mosaic', lambda o: mosaic('mosaic', o)),
    # sciany
    ('blocks', lambda o: slabs('blocks', o, 2, 4, (220, 204, 170), (190, 172, 138), (130, 112, 86), 512, seed=10, crack=0.3)),
    ('blocks_grey', lambda o: slabs('blocks_grey', o, 2, 4, (150, 146, 140), (118, 114, 110), (70, 66, 64), 512, seed=12, crack=0.4)),
    ('blocks_marble', lambda o: slabs('blocks_marble', o, 2, 3, (236, 232, 222), (214, 208, 196), (160, 152, 136), 512, seed=14,
                                      crack=0.2, grout_w=2.0)),
    ('plaster', lambda o: plaster('plaster', o)),
    ('plaster_ochre', lambda o: plaster('plaster_ochre', o, (214, 170, 104), seed=13)),
    ('plaster_red', lambda o: plaster('plaster_red', o, (168, 52, 40), seed=14, dirt=(110, 50, 40))),
    ('plaster_blue', lambda o: plaster('plaster_blue', o, (60, 100, 160), seed=15, dirt=(40, 60, 90))),
    ('marble', lambda o: marble('marble', o)),
    ('marble_dark', lambda o: marble('marble_dark', o, (90, 86, 84), (200, 196, 190), seed=10)),
    ('meander_gold', lambda o: meander('meander_gold', o)),
    ('meander_white', lambda o: meander('meander_white', o, (236, 230, 214), (40, 50, 80), seed=56)),
    ('roof', lambda o: roof('roof', o)),
    ('roof_dark', lambda o: roof('roof_dark', o, (120, 64, 44), (86, 44, 32), seed=14)),
    # drewno, rosliny
    ('wood', lambda o: wood('wood', o)),
    ('wood_dark', lambda o: wood('wood_dark', o, (86, 56, 36), (56, 36, 24), seed=16)),
    ('wood_ship', lambda o: wood('wood_ship', o, (110, 74, 44), (70, 46, 28), seed=18, planks=8)),
    ('bark', lambda o: bark('bark', o)),
    ('bark_olive', lambda o: bark('bark_olive', o, (130, 120, 104), (78, 70, 60), seed=18)),
    ('leaf_olive', lambda o: foliage('leaf_olive', o, (50, 64, 40), (104, 120, 76), (156, 168, 122), seed=19)),
    ('leaf_dark', lambda o: foliage('leaf_dark', o, (16, 38, 20), (32, 64, 32), (60, 96, 50), seed=20, n=400)),
    ('leaf_lush', lambda o: foliage('leaf_lush', o, (34, 72, 28), (70, 124, 44), (126, 172, 72), seed=22)),
    ('leaf_autumn', lambda o: foliage('leaf_autumn', o, (90, 40, 20), (164, 82, 30), (214, 146, 62), seed=24)),
    ('leaf_blossom', lambda o: foliage('leaf_blossom', o, (60, 90, 40), (220, 150, 180), (250, 220, 230), seed=26)),
    ('leaf_vine', lambda o: foliage('leaf_vine', o, (30, 60, 24), (60, 110, 40), (110, 150, 60), seed=28, n=160)),
    ('pine_needles', lambda o: pine_needles('pine_needles', o)),
    # skaly
    ('rock', lambda o: rock('rock', o)),
    ('rock_warm', lambda o: rock('rock_warm', o, (198, 172, 134), (132, 110, 84), seed=22, lichen=(150, 140, 80), lichen_amt=0.15)),
    ('rock_mossy', lambda o: rock('rock_mossy', o, (140, 140, 130), (84, 84, 80), seed=23, lichen=(80, 110, 50), lichen_amt=0.5)),
    ('rock_white', lambda o: rock('rock_white', o, (226, 222, 212), (170, 166, 156), seed=24, lichen=(170, 160, 120), lichen_amt=0.1)),
    ('cliff', lambda o: strata('cliff', o, [(214, 178, 128), (190, 146, 98), (226, 196, 150), (170, 124, 84), (214, 178, 128)])),
    ('cliff_grey', lambda o: strata('cliff_grey', o, [(150, 148, 146), (120, 118, 118), (172, 170, 166), (104, 102, 104), (150, 148, 146)], seed=24)),
    ('basalt', lambda o: rock('basalt', o, (70, 64, 62), (30, 28, 30), seed=26, lichen=(90, 40, 20), lichen_amt=0.1, n=40)),
    ('lava', lambda o: lava('lava', o)),
    ('snow', lambda o: snow('snow', o)),
    # metal, tkaniny, ceramika
    ('bronze', lambda o: bronze('bronze', o)),
    ('cloth', lambda o: cloth('cloth', o, (232, 222, 196))),
    ('cloth_red', lambda o: cloth('cloth_red', o, (232, 222, 196), (168, 40, 32), stripes=6, seed=32)),
    ('cloth_blue', lambda o: cloth('cloth_blue', o, (232, 222, 196), (40, 70, 140), stripes=6, seed=33)),
    ('cloth_purple', lambda o: cloth('cloth_purple', o, (110, 40, 100), seed=34, border=(200, 150, 60))),
    ('sail_red', lambda o: cloth('sail_red', o, (180, 50, 36), seed=35, border=(230, 200, 140))),
    ('sail_white', lambda o: cloth('sail_white', o, (236, 226, 200), seed=36, border=(40, 60, 120))),
    ('sail_black', lambda o: cloth('sail_black', o, (40, 34, 34), seed=37, border=(170, 40, 30))),
    ('terracotta', lambda o: terracotta('terracotta', o)),
    ('terracotta_painted', lambda o: terracotta('terracotta_painted', o, seed=60, painted=True)),
    ('water', lambda o: water_ripple('water', o)),
]


for _n in ('ground', 'ground_scattered', 'dirt_path', 'mud', 'clay', 'clay_pale', 'sand', 'sand_white',
           'sand_wet', 'sand_volcanic'):
    style(_n, cracks=0.25, pits=0.6)
for _n in ('sandstone', 'stone_moss', 'limestone', 'rock', 'rock_warm', 'rock_mossy', 'rock_white', 'cliff',
           'cliff_grey', 'basalt', 'blocks', 'blocks_grey', 'blocks_marble', 'paving', 'paving_marble', 'paving_red',
           'paving_basalt', 'plaster', 'plaster_ochre', 'plaster_red', 'plaster_blue', 'marble', 'marble_dark'):
    style(_n, cracks=0.8, pits=0.35)
for _n in ('cobble', 'cobble_warm', 'cobble_dark', 'cobble_small', 'flagstone_grass', 'flagstone_dirt', 'gravel',
           'gravel_warm', 'pebbles', 'pebbles_beach'):
    style(_n, cracks=0.3, pits=0.25)
style('stone_moss', cracks=1.0, pits=0.4, moss=0.9)
style('rock_mossy', cracks=0.9, pits=0.3, moss=0.7)
style('blocks_grey', cracks=0.8, pits=0.35, moss=0.35)
for _n in ('mosaic', 'meander_gold', 'meander_white', 'cloth', 'cloth_red', 'cloth_blue', 'cloth_purple',
           'sail_red', 'sail_white', 'sail_black', 'terracotta', 'terracotta_painted', 'lava', 'water'):
    style(_n, mottle=0.04, desat=0.12, contrast=0.95)
for _n in ('grass_lush', 'grass_dry', 'grass_alpine', 'grass_meadow', 'grass_ash', 'leaf_olive', 'leaf_dark',
           'leaf_lush', 'leaf_autumn', 'leaf_blossom', 'leaf_vine', 'pine_needles'):
    style(_n, mottle=0.1, desat=0.22, contrast=0.88)

LIBRARY += [
    ('ground', lambda o: earth('ground', o, (84, 78, 70), (122, 112, 98))),
    ('ground_scattered', lambda o: earth('ground_scattered', o, (122, 104, 86), (160, 140, 116), seed=64, lumps=1.5)),
    ('sandstone', lambda o: earth('sandstone', o, (150, 136, 112), (184, 168, 140), seed=65, lumps=0.05)),
    ('stone_moss', lambda o: earth('stone_moss', o, (128, 126, 102), (160, 156, 128), seed=66, lumps=0.05)),
    ('limestone', lambda o: earth('limestone', o, (168, 162, 148), (196, 190, 176), seed=67, lumps=0.2)),
]


def build_library(out_dir, only=None):
    res = {}
    for name, fn in LIBRARY:
        if only and name not in only:
            continue
        res[name] = fn(out_dir)
    return res
