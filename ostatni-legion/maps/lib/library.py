"""Pelna biblioteka tekstur Ostatniego Legionu - JEDEN styl dla wszystkiego.

Wspolne zasady (dla kazdej tekstury):
  * gestosc: 128 px na stud (podloza/sciezki 1024 px = 8 studow, modele 512 px = 4 study),
  * baza z pol szumu Blendera + ta sama warstwa "malowanych" pociagniec pedzla (kolor brany z tla),
  * ten sam filtr: odbarwienie, kontrast, miekkie plamy, cienkie pekniecia, drobne wglebienia.
"""
import math
import zlib
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import recipes as R
from . import tex as X
from .tex import field, norm, ramp, mix, smooth, uv_grid, cells, edge_dist, TAU
from .recipes import vor, palette_pick, C

# ------------------------------------------------------------------ wspolna warstwa pedzla
PAINT = {}   # nazwa -> dict(density, length, width, curl, dir, jitter)


def paint_over(col, h, seed, density=1.0, length=(10, 24), width=(3, 5), curl=0.9, dirmode='noise', jitter=0.10):
    size = col.shape[0]
    n = int(9000 * density * (size / 1024) ** 2)
    if n <= 0:
        return col, h
    rng = random.Random(seed)
    dirf = norm(field('noise', size, 2.2, seed=seed + 77, detail=1)) * TAU * 1.5
    src = (np.clip(col, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(src.copy(), 'RGB')
    hi = Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8), 'L')
    dc = ImageDraw.Draw(img)
    dh = ImageDraw.Draw(hi)
    for _ in range(n):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        xi, yi = int(x) % size, int(y) % size
        if dirmode == 'vertical':
            a = math.pi / 2 + rng.uniform(-0.25, 0.25)
        elif dirmode == 'horizontal':
            a = rng.uniform(-0.2, 0.2)
        else:
            a = dirf[yi, xi] + rng.uniform(-0.5, 0.5)
        L = rng.uniform(*length)
        w = rng.randint(*width)
        k = 1 + rng.uniform(-jitter, jitter)
        c = tuple(int(max(0, min(255, v * k + rng.uniform(-6, 6)))) for v in src[yi, xi])
        pts = []
        px, py = x, y
        for _s in range(4):
            pts.append((px, py))
            a += rng.uniform(-curl, curl) * 0.35
            px += math.cos(a) * L / 3
            py += math.sin(a) * L / 3
        hv = int(min(255, h[yi, xi] * 255 + rng.uniform(10, 40)))
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                p2 = [(p[0] + ox, p[1] + oy) for p in pts]
                if max(p[0] for p in p2) < -4 or min(p[0] for p in p2) > size + 4:
                    continue
                if max(p[1] for p in p2) < -4 or min(p[1] for p in p2) > size + 4:
                    continue
                dc.line(p2, fill=c, width=w, joint='curve')
                dh.line(p2, fill=hv, width=max(1, w - 1), joint='curve')
    out = np.asarray(img.filter(ImageFilter.GaussianBlur(0.5)), np.float32) / 255
    hh = np.asarray(hi.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    return out, hh


_orig_finish = R.finish


def finish(name, col, h):
    st = dict(R.STYLE_DEFAULT, **R.STYLE.get(name, {}))
    import zlib
    sd = zlib.crc32(name.encode()) % 1000
    p = PAINT.get(name)
    if p:
        col, h = paint_over(col, h, sd + 300, **p)
    return _orig_finish(name, col, h)


R.finish = finish


def capture(fn, *a, **kw):
    """Uruchom generator, ale zamiast zapisu zwroc (kolor, wysokosc) - do mieszania tekstur."""
    old = R.save
    R.save = lambda name, col, h, strength, out, size_out=None: (col, h)
    try:
        return fn(*a, **kw)
    finally:
        R.save = old


def blend_save(name, out, A, B, mask, strength=4.0):
    col = mix(A[0], B[0], mask)
    h = A[1] * (1 - mask) + B[1] * mask
    return R.save(name, col, h, strength, out)


# ------------------------------------------------------------------ nowe generatory
def vor_hex(size, n, seed=0):
    """Szesciokatne komorki (plytki heksagonalne)."""
    g = max(2, int(round(math.sqrt(n))))
    u, v = uv_grid(size)
    best = None
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            cy = np.floor(v * g) + dy
            off = (cy % 2) * 0.5
            cx = np.floor(u * g - off) + dx
            px = (cx + 0.5 + off) / g
            py = (cy + 0.5) / g
            d = np.sqrt(((u - px) * 1.0) ** 2 + ((v - py) * 0.866) ** 2)
            idv = ((cx % g) * 131 + (cy % g) * 17) % 997
            if best is None:
                best = [d, np.full_like(d, 9.0), idv]
            else:
                m = d < best[0]
                best[1] = np.where(m, best[0], np.minimum(best[1], d))
                best[2] = np.where(m, idv, best[2])
                best[0] = np.where(m, d, best[0])
    F1, F2, idv = best
    rnd = (np.sin(idv * 12.9898) * 43758.5453) % 1.0
    return F1 * size, (F2 - F1) * 0.5 * size, rnd.astype(np.float32)


def hex_tiles(name, out, cols, grout, size=1024, seed=71, n=100):
    F1, ED, rid = vor_hex(size, n, seed)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    stone = palette_pick(rid, cols) * (0.85 + 0.25 * det[..., None])
    m = smooth(2.0, 5.0, ED)
    col = mix(C(grout), stone * (0.8 + 0.2 * smooth(4, 16, ED))[..., None], m)
    return R.save(name, col, m * (0.8 + 0.2 * det), 5.0, out)


def checker(name, out, colA, colB, grout, size=1024, seed=73, n=8):
    fx, fy, rid, cw, ch = cells(size, n, n, 0.0, seed)
    u, v = uv_grid(size)
    par = ((np.floor(u * n) + np.floor(v * n)) % 2)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    base = mix(C(colA), C(colB), par) * (0.88 + 0.2 * det * (0.5 + rid))[..., None]
    ed = edge_dist(fx, fy, cw, ch)
    m = smooth(1.5, 3.5, ed)
    return R.save(name, mix(C(grout), base, m), m, 4.0, out)


def bricks(name, out, colA, colB, mortar, size=1024, seed=75, pattern='running'):
    u, v = uv_grid(size)
    if pattern == 'basket':
        B = 4
        bx, by = np.floor(u * B), np.floor(v * B)
        fu, fv = u * B - bx, v * B - by
        horiz = ((bx + by) % 2) == 0
        k = np.where(horiz, np.floor(fv * 3), np.floor(fu * 3))
        a = np.where(horiz, fu, fv)
        b = np.where(horiz, fv * 3 - k, fu * 3 - k)
        bp = size / B
        ed = np.minimum(np.minimum(a, 1 - a) * bp, np.minimum(b, 1 - b) * bp / 3)
        rng = np.random.default_rng(seed)
        tab = rng.random((B, B, 3)).astype(np.float32)
        rid = tab[by.astype(int) % B, bx.astype(int) % B, k.astype(int) % 3]
    else:
        fx, fy, rid, cw, ch = cells(size, 4, 12, 0.5, seed)
        ed = edge_dist(fx, fy, cw, ch)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    base = mix(C(colA), C(colB), rid) * (0.85 + 0.25 * det)[..., None]
    m = smooth(2.0, 4.5, ed)
    col = mix(C(mortar) * (0.8 + 0.3 * det[..., None]), base * (0.8 + 0.2 * smooth(3, 12, ed))[..., None], m)
    return R.save(name, col, m * (0.8 + 0.2 * det), 6.0, out)


def via(name, out, stone_cols, gap, size=1024, seed=77, ruts=True):
    """Rzymska droga: duze wielokatne kamienie, glebokie szczeliny, koleiny od wozow."""
    F1, ED, rid, _ = vor(size, 28, seed, jitter=1.0)
    det = norm(field('noise', size, 30, seed=seed, detail=5))
    stone = palette_pick(rid, stone_cols) * (0.8 + 0.3 * det[..., None])
    m = smooth(3, 7, ED)
    bevel = smooth(7, 26, ED)
    col = mix(C(gap), stone * (0.68 + 0.32 * bevel[..., None]), m)
    h = m * (0.6 + 0.4 * bevel)
    if ruts:
        u, v = uv_grid(size)
        rut = np.maximum(smooth(0.06, 0.0, np.abs(u - 0.3)), smooth(0.06, 0.0, np.abs(u - 0.7)))
        col = col * (1 - 0.18 * rut[..., None])
        h = h - 0.25 * rut
    return R.save(name, col, h, 6.0, out)


def stepping(name, out, ground_fn, stone_cols, size=1024, seed=79, n=20):
    """Duze plaskie kamienie w trawie/piasku."""
    G = capture(ground_fn)
    F1, ED, rid, _ = vor(size, n, seed, jitter=1.0)
    gap = size / math.sqrt(n) * (0.12 + 0.1 * rid) + 10 * norm(field('noise', size, 10, seed=seed, detail=3))
    inside = smooth(gap, gap + 3, ED)
    det = norm(field('noise', size, 30, seed=seed + 1, detail=5))
    stone = palette_pick(rid, stone_cols) * (0.8 + 0.3 * det[..., None]) * (0.72 + 0.28 * smooth(gap, gap + 18, ED))[..., None]
    col = mix(G[0] * (0.82 + 0.18 * smooth(gap - 10, gap, ED))[..., None], stone, inside)
    return R.save(name, col, G[1] * (1 - inside) + inside * 0.9, 5.0, out)


def boardwalk(name, out, colA=(126, 88, 54), colB=(90, 60, 36), size=1024, seed=81, weathered=False):
    fx, fy, rid, cw, ch = cells(size, 2, 8, 0.5, seed)
    g = field('noise', size, 3, aniso=10, seed=seed, detail=6, distortion=0.6)
    grain = 0.5 + 0.5 * np.sin(TAU * (g * 8 + rid * 3))
    if weathered:
        colA, colB = (150, 140, 124), (104, 96, 86)
    base = mix(C(colB), C(colA), 0.5 * grain + 0.5 * rid)
    ed = edge_dist(fx, fy, cw, ch)
    gap = smooth(1.5, 5.0, np.minimum(fy, 1 - fy) * ch) * smooth(0.5, 2.0, np.minimum(fx, 1 - fx) * cw)
    col = base * (0.25 + 0.75 * gap)[..., None]
    u, v = uv_grid(size)
    for nx in (0.06, 0.44, 0.56, 0.94):
        nail = smooth(4.5, 2.5, np.hypot((fx - nx) * cw, (fy - 0.5) * ch))
        col = mix(col, C((60, 58, 56)), nail)
    return R.save(name, col, gap * 0.8 + grain * 0.2, 5.0, out)


def ruts(name, out, base_fn, size=1024, seed=83):
    G = capture(base_fn)
    u, v = uv_grid(size)
    nn = field('noise', size, 3, seed=seed, detail=3)
    rut = np.maximum(smooth(0.07, 0.01, np.abs(u - 0.32 - 0.02 * nn)), smooth(0.07, 0.01, np.abs(u - 0.68 + 0.02 * nn)))
    col = G[0] * (1 - 0.25 * rut[..., None])
    return R.save(name, col, G[1] - 0.4 * rut, 4.0, out)


def rubble_wall(name, out, cols, mortar, size=512, seed=85, n=70, aniso=(1.0, 1.7)):
    F1, ED, rid, _ = vor(size, n, seed, aniso=aniso, jitter=1.0)
    det = norm(field('noise', size, 20, seed=seed, detail=5))
    stone = palette_pick(rid, cols) * (0.78 + 0.3 * det[..., None])
    m = smooth(1.5, 3.5, ED)
    bevel = smooth(3, 12, ED)
    col = mix(C(mortar) * (0.8 + 0.3 * det[..., None]), stone * (0.65 + 0.35 * bevel[..., None]), m)
    return R.save(name, col, m * (0.5 + 0.5 * bevel), 6.0, out)


def mixed_ground(name, out, fa, fb, scale=3.0, cover=0.5, seed=87, size=1024):
    A = capture(fa)
    B = capture(fb)
    n = norm(field('noise', size, scale, seed=seed, detail=4))
    m = smooth(cover - 0.08, cover + 0.08, n)
    return blend_save(name, out, A, B, m)


def snow_path(name, out, size=1024, seed=89):
    u, v = uv_grid(size)
    n = norm(field('noise', size, 5, seed=seed, detail=5))
    col = mix(C((190, 200, 218)), C((236, 240, 250)), n)
    rng = random.Random(seed)
    im = Image.fromarray((col * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    hgt = Image.new('L', (size, size), 200)
    dh = ImageDraw.Draw(hgt)
    for k in range(60):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                d.ellipse([x + ox - 14, y + oy - 22, x + ox + 14, y + oy + 22], fill=(176, 188, 210))
                dh.ellipse([x + ox - 14, y + oy - 22, x + ox + 14, y + oy + 22], fill=120)
    c = np.asarray(im.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    h = np.asarray(hgt.filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    return R.save(name, c, h, 3.0, out)


def mosaic_waves(name, out, size=1024, seed=91, fg=(40, 80, 140), bg=(226, 216, 190)):
    u, v = uv_grid(size)
    N = 64
    tx, ty = np.floor(u * N), np.floor(v * N)
    fx, fy = u * N - tx, v * N - ty
    cu, cv = (tx + 0.5) / N, (ty + 0.5) / N
    wave = np.sin(TAU * (cu * 4)) * 0.06
    band = ((cv * 4 + wave * 4) % 1.0) < 0.35
    rng = np.random.default_rng(seed)
    jit = rng.random((N + 1, N + 1)).astype(np.float32)[ty.astype(int), tx.astype(int)]
    col = np.where(band[..., None], mix(C(fg), C(fg) * 1.25, jit), mix(C(bg), C(bg) * 0.92, jit))
    e = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy)) * (size / N)
    g = smooth(0.4, 1.6, e)
    return R.save(name, mix(C((120, 110, 92)), col, g), g * 0.8, 4.0, out)


def mosaic_checker(name, out, size=1024, seed=93, a=(196, 170, 120), b=(110, 60, 40)):
    u, v = uv_grid(size)
    N = 48
    tx, ty = np.floor(u * N), np.floor(v * N)
    fx, fy = u * N - tx, v * N - ty
    par = ((np.floor(tx / 4) + np.floor(ty / 4)) % 2) == 0
    rng = np.random.default_rng(seed)
    jit = rng.random((N + 1, N + 1)).astype(np.float32)[ty.astype(int), tx.astype(int)]
    col = np.where(par[..., None], mix(C(a), C(a) * 0.9, jit), mix(C(b), C(b) * 1.15, jit))
    e = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy)) * (size / N)
    g = smooth(0.4, 1.6, e)
    return R.save(name, mix(C((110, 100, 84)), col, g), g * 0.8, 4.0, out)


def ice(name, out, size=1024, seed=95):
    n = norm(field('noise', size, 3, seed=seed, detail=5))
    _, e, _, _ = vor(size, 30, seed, jitter=1.0)
    col = mix(C((120, 170, 200)), C((200, 230, 245)), n)
    col = col * (1 - 0.25 * smooth(1.5, 0.3, e))[..., None]
    return R.save(name, col, n * 0.5, 2.0, out)


def straw(name, out, size=512, seed=97):
    base = ramp(norm(field('noise', size, 5, seed=seed, detail=3)), [(0, (150, 120, 60)), (1, (214, 184, 106))])
    dirf = norm(field('noise', size, 1.5, seed=seed + 1, detail=1)) * 0.3
    col, h = X.strokes(size, 7000, [(200, 170, 96), (170, 140, 70), (226, 200, 130), (140, 110, 56)], dirf,
                       length=(14, 30), width=(2, 3), seed=seed, base=base, curl=0.2)
    return R.save(name, col, h, 3.0, out)


def rope(name, out, size=512, seed=99):
    u, v = uv_grid(size)
    s = 0.5 + 0.5 * np.sin(TAU * (u * 16 + v * 16))
    n = norm(field('noise', size, 20, seed=seed, detail=3))
    col = mix(C((120, 96, 56)), C((196, 166, 110)), s * 0.7 + n * 0.3)
    return R.save(name, col, s, 4.0, out)


def leather(name, out, size=512, seed=101, col_=(110, 66, 36)):
    n = norm(field('noise', size, 8, seed=seed, detail=6))
    f = norm(field('noise', size, 60, seed=seed + 1, detail=3))
    col = C(col_) * (0.75 + 0.3 * n + 0.1 * f)[..., None]
    return R.save(name, col, f * 0.4 + n * 0.2, 2.0, out)


def iron(name, out, size=512, seed=103, rust=0.4):
    n = norm(field('noise', size, 6, seed=seed, detail=5))
    f = norm(field('noise', size, 40, seed=seed + 1, detail=3))
    col = mix(C((70, 70, 72)), C((110, 108, 106)), f)
    col = mix(col, C((140, 70, 30)) * (0.8 + 0.3 * f[..., None]), smooth(1 - rust, 1 - rust + 0.2, n))
    return R.save(name, col, f * 0.3, 2.0, out)


def gold_tex(name, out, size=512, seed=105):
    n = norm(field('noise', size, 6, seed=seed, detail=4))
    col = mix(C((190, 140, 50)), C((250, 210, 110)), n)
    return R.save(name, col, n * 0.2, 1.0, out)


# ------------------------------------------------------------------ styl (malowanie) dla grup
def paint(names, **kw):
    for n in names:
        PAINT[n] = kw


def style(names, **kw):
    for n in names:
        R.STYLE[n] = kw


NATURAL = dict(density=1.0, length=(10, 24), width=(3, 5), curl=0.9)
STONE = dict(density=0.35, length=(6, 12), width=(2, 4), curl=0.6, jitter=0.06)
WALL = dict(density=0.45, length=(6, 14), width=(2, 4), curl=0.7, jitter=0.07)
LEAF = dict(density=2.2, length=(8, 18), width=(4, 6), curl=1.6, jitter=0.16)
BARK = dict(density=1.6, length=(14, 34), width=(3, 5), curl=0.25, dirmode='vertical', jitter=0.14)
GRAIN = dict(density=0.8, length=(20, 40), width=(2, 3), curl=0.15, dirmode='horizontal', jitter=0.08)
METAL = dict(density=0.25, length=(8, 16), width=(2, 3), curl=0.8, jitter=0.05)


# ------------------------------------------------------------------ KATALOG
def _g(name, base, strokes_, seed, **kw):
    return (name, lambda o: R.grass(name, o, base, strokes_, seed=seed, **kw))


GRASS_SETS = {
    'grass_lush': ([(0, (44, 74, 28)), (1, (84, 116, 44))], [(70, 110, 40), (98, 140, 52), (54, 88, 30), (124, 156, 62)]),
    'grass_dry': ([(0, (112, 108, 54)), (1, (166, 148, 80))], [(172, 156, 84), (138, 134, 64), (196, 176, 100), (116, 118, 56)]),
    'grass_alpine': ([(0, (36, 70, 44)), (1, (66, 104, 66))], [(56, 98, 60), (80, 126, 78), (42, 80, 50), (100, 142, 90)]),
    'grass_ash': ([(0, (48, 44, 40)), (1, (74, 66, 56))], [(70, 64, 56), (92, 82, 66), (54, 50, 46), (104, 74, 50)]),
    'grass_autumn': ([(0, (110, 78, 34)), (1, (160, 116, 50))], [(170, 120, 50), (140, 96, 40), (196, 150, 70), (120, 110, 50)]),
    'grass_swamp': ([(0, (40, 52, 30)), (1, (70, 80, 44))], [(60, 74, 40), (80, 92, 50), (46, 58, 34), (96, 100, 60)]),
    'grass_burnt': ([(0, (60, 46, 30)), (1, (96, 76, 44))], [(110, 84, 46), (80, 62, 38), (130, 110, 60), (60, 50, 36)]),
    'grass_short': ([(0, (60, 96, 38)), (1, (96, 132, 54))], [(84, 124, 48), (104, 146, 58), (70, 108, 42)]),
    'grass_blue': ([(0, (40, 72, 66)), (1, (70, 106, 96))], [(60, 98, 90), (84, 124, 112), (48, 84, 78)]),
}

LIB = []   # (kategoria, nazwa, funkcja)


def add(cat, name, fn):
    LIB.append((cat, name, fn))


# --- TRAWY
for _n, (_b, _s) in GRASS_SETS.items():
    add('Trawy', _n, (lambda n=_n, b=_b, s=_s: (lambda o: R.grass(n, o, b, s, seed=zlib.crc32(n.encode()) % 97)))())
add('Trawy', 'grass_meadow', lambda o: R.grass('grass_meadow', o, *GRASS_SETS['grass_lush'], seed=5,
                                                 flowers=[(230, 230, 240), (240, 200, 60), (200, 80, 160), (110, 140, 230)]))
add('Trawy', 'grass_poppies', lambda o: R.grass('grass_poppies', o, *GRASS_SETS['grass_dry'], seed=7,
                                                  flowers=[(210, 40, 36), (230, 60, 40), (240, 230, 220)]))
add('Trawy', 'grass_clover', lambda o: R.grass('grass_clover', o, *GRASS_SETS['grass_short'], seed=8,
                                                 flowers=[(240, 240, 240), (230, 200, 230)]))
add('Trawy', 'moss', lambda o: R.earth('moss', o, (50, 80, 34), (96, 126, 52), seed=9, lumps=1.2))

# --- PODLOZA
G = 'Podloza'
add(G, 'ground', lambda o: R.earth('ground', o, (84, 78, 70), (122, 112, 98)))
add(G, 'ground_scattered', lambda o: R.earth('ground_scattered', o, (122, 104, 86), (160, 140, 116), seed=64, lumps=1.5))
add(G, 'earth_dark', lambda o: R.earth('earth_dark', o, (54, 44, 36), (88, 72, 58), seed=65))
add(G, 'earth_red', lambda o: R.earth('earth_red', o, (120, 60, 36), (168, 94, 58), seed=66, lumps=0.8))
add(G, 'dirt', lambda o: R.sand('dirt', o, (150, 116, 80), (106, 78, 52), seed=8, ripple=0))
add(G, 'sand', lambda o: R.sand('sand', o, (238, 216, 166), (198, 170, 120)))
add(G, 'sand_white', lambda o: R.sand('sand_white', o, (246, 238, 214), (214, 200, 168), seed=9))
add(G, 'sand_wet', lambda o: R.sand('sand_wet', o, (170, 146, 106), (120, 100, 70), seed=10, ripple=14))
add(G, 'sand_red', lambda o: R.sand('sand_red', o, (214, 150, 96), (170, 104, 62), seed=11, ripple=6))
add(G, 'sand_dunes', lambda o: R.sand('sand_dunes', o, (232, 200, 142), (190, 150, 98), seed=12, ripple=4))
add(G, 'sand_volcanic', lambda o: R.sand('sand_volcanic', o, (96, 86, 80), (52, 46, 44), seed=4))
add(G, 'ash', lambda o: R.earth('ash', o, (60, 58, 58), (104, 100, 98), seed=13, lumps=0.3))
add(G, 'clay', lambda o: R.clay('clay', o))
add(G, 'clay_pale', lambda o: R.clay('clay_pale', o, (206, 172, 128), (164, 130, 92), seed=46))
add(G, 'salt_flat', lambda o: R.clay('salt_flat', o, (236, 232, 222), (200, 194, 182), seed=47))
add(G, 'mud', lambda o: R.mud('mud', o))
add(G, 'swamp_mud', lambda o: R.earth('swamp_mud', o, (40, 40, 28), (70, 66, 40), seed=48, lumps=0.6))
add(G, 'rocky_ground', lambda o: R.pebbles('rocky_ground', o, [(130, 124, 116), (160, 152, 140), (104, 100, 96)],
                                           ground=(110, 96, 78), seed=49, n=900))
add(G, 'scree', lambda o: R.gravel('scree', o, [(150, 146, 140), (120, 116, 110), (176, 170, 160)], gaps=(80, 76, 72),
                                   seed=50, n=1400))
add(G, 'snow', lambda o: R.snow('snow', o, size=1024))
add(G, 'snow_dirty', lambda o: mixed_ground('snow_dirty', o, lambda: R.snow('x', o, size=1024),
                                            lambda: R.earth('x', o, (90, 84, 76), (130, 120, 108)), 4, 0.62, 51))
add(G, 'ice', lambda o: ice('ice', o))
add(G, 'grass_patchy', lambda o: mixed_ground('grass_patchy', o, lambda: R.grass('x', o, *GRASS_SETS['grass_lush'], seed=31),
                                              lambda: R.earth('x', o, (110, 92, 70), (150, 130, 100), lumps=1.0), 3, 0.62, 52))
add(G, 'grass_sandy', lambda o: mixed_ground('grass_sandy', o, lambda: R.grass('x', o, *GRASS_SETS['grass_dry'], seed=32),
                                             lambda: R.sand('x', o, (238, 216, 166), (198, 170, 120)), 3, 0.55, 53))
add(G, 'grass_rocky', lambda o: mixed_ground('grass_rocky', o, lambda: R.grass('x', o, *GRASS_SETS['grass_alpine'], seed=33),
                                             lambda: R.gravel('x', o, [(150, 146, 140), (120, 116, 110)], gaps=(80, 76, 72), n=1400),
                                             4, 0.6, 54))
add(G, 'moss_ground', lambda o: mixed_ground('moss_ground', o, lambda: R.earth('x', o, (54, 44, 36), (88, 72, 58)),
                                             lambda: R.earth('x', o, (50, 80, 34), (96, 126, 52), lumps=1.2), 3, 0.5, 55))
add(G, 'lava_crust', lambda o: mixed_ground('lava_crust', o, lambda: R.earth('x', o, (30, 26, 26), (60, 50, 46)),
                                            lambda: R.lava('x', o, size=1024), 3, 0.72, 56))

# --- SCIEZKI (najwieksza grupa - na 14 map)
S = 'Sciezki'
GREY = [(150, 140, 126), (178, 168, 150), (128, 120, 110), (198, 188, 168)]
WARM = [(200, 170, 128), (176, 146, 106), (214, 190, 150), (160, 128, 92)]
DARK = [(70, 64, 62), (96, 88, 82), (56, 52, 52), (110, 96, 86)]
WHITE = [(222, 216, 204), (240, 234, 222), (200, 194, 182), (230, 222, 206)]
RED = [(170, 98, 66), (196, 120, 82), (150, 84, 56), (184, 110, 74)]
BLUEGREY = [(120, 130, 138), (146, 154, 160), (100, 108, 116), (160, 166, 168)]
add(S, 'cobble', lambda o: R.cobble('cobble', o, GREY, (92, 80, 62)))
add(S, 'cobble_warm', lambda o: R.cobble('cobble_warm', o, WARM, (110, 86, 60), seed=8))
add(S, 'cobble_dark', lambda o: R.cobble('cobble_dark', o, DARK, (36, 28, 26), seed=6, dirt=0.1))
add(S, 'cobble_white', lambda o: R.cobble('cobble_white', o, WHITE, (150, 140, 120), seed=9))
add(S, 'cobble_red', lambda o: R.cobble('cobble_red', o, RED, (90, 60, 44), seed=10))
add(S, 'cobble_bluegrey', lambda o: R.cobble('cobble_bluegrey', o, BLUEGREY, (70, 74, 76), seed=11))
add(S, 'cobble_small', lambda o: R.cobble('cobble_small', o, GREY, (100, 90, 74), seed=12, n=420, round_=0.5, mortar_w=2.5))
add(S, 'cobble_small_warm', lambda o: R.cobble('cobble_small_warm', o, WARM, (110, 86, 60), seed=13, n=420, round_=0.5, mortar_w=2.5))
add(S, 'cobble_big', lambda o: R.cobble('cobble_big', o, GREY, (92, 80, 62), seed=14, n=50, mortar_w=5))
add(S, 'cobble_mossy', lambda o: R.cobble('cobble_mossy', o, GREY, (60, 92, 40), seed=15))
add(S, 'cobble_sandy', lambda o: R.cobble('cobble_sandy', o, WARM, (210, 186, 140), seed=16, mortar_w=6))
add(S, 'cobble_snowy', lambda o: R.cobble('cobble_snowy', o, BLUEGREY, (226, 232, 244), seed=17, mortar_w=6))
add(S, 'cobble_lava', lambda o: R.cobble('cobble_lava', o, DARK, (255, 110, 30), seed=18, dirt=0.0, mortar_w=3))
add(S, 'cobble_ash', lambda o: R.cobble('cobble_ash', o, DARK, (90, 88, 86), seed=19))
add(S, 'via_basalt', lambda o: via('via_basalt', o, DARK, (40, 34, 30)))
add(S, 'via_limestone', lambda o: via('via_limestone', o, WHITE, (120, 110, 92), seed=78))
add(S, 'via_warm', lambda o: via('via_warm', o, WARM, (96, 76, 54), seed=79, ruts=False))
add(S, 'flagstone_grass', lambda o: R.flagstone('flagstone_grass', o, GREY))
add(S, 'flagstone_dirt', lambda o: R.flagstone('flagstone_dirt', o, WARM, gap='dirt', seed=52))
add(S, 'flagstone_white', lambda o: R.flagstone('flagstone_white', o, WHITE, seed=53))
add(S, 'flagstone_dark', lambda o: R.flagstone('flagstone_dark', o, DARK, gap='dirt', seed=54))
add(S, 'paving', lambda o: R.slabs('paving', o, 3, 6, (232, 222, 200), (208, 196, 172), (150, 134, 108)))
add(S, 'paving_marble', lambda o: R.slabs('paving_marble', o, 2, 2, (240, 236, 226), (220, 214, 202), (170, 160, 140), seed=9,
                                          offset=0.0, crack=0.35, grout_w=2.0))
add(S, 'paving_large', lambda o: R.slabs('paving_large', o, 2, 3, (214, 204, 184), (190, 178, 156), (130, 116, 94), seed=20,
                                         crack=0.6))
add(S, 'paving_grey', lambda o: R.slabs('paving_grey', o, 3, 5, (160, 156, 150), (130, 126, 120), (80, 76, 72), seed=21))
add(S, 'paving_red', lambda o: R.slabs('paving_red', o, 4, 4, (196, 120, 82), (170, 98, 66), (110, 72, 50), seed=8, offset=0.0))
add(S, 'paving_basalt', lambda o: R.slabs('paving_basalt', o, 3, 5, (78, 72, 70), (56, 52, 52), (30, 24, 22), seed=10, crack=0.6))
add(S, 'paving_cracked', lambda o: R.slabs('paving_cracked', o, 3, 4, (210, 200, 180), (180, 168, 146), (70, 100, 44), seed=22,
                                           crack=1.0, grout_w=4.5))
add(S, 'paving_sandstone', lambda o: R.slabs('paving_sandstone', o, 3, 6, (214, 182, 132), (190, 156, 108), (130, 100, 70),
                                             seed=23))
add(S, 'bricks_path', lambda o: bricks('bricks_path', o, (176, 96, 62), (150, 76, 48), (120, 104, 84)))
add(S, 'bricks_basket', lambda o: bricks('bricks_basket', o, (180, 104, 66), (154, 82, 52), (120, 104, 84), seed=76,
                                         pattern='basket'))
add(S, 'bricks_pale', lambda o: bricks('bricks_pale', o, (210, 186, 146), (186, 160, 120), (130, 116, 94), seed=77))
add(S, 'tiles_hex', lambda o: hex_tiles('tiles_hex', o, GREY, (90, 80, 66)))
add(S, 'tiles_hex_terracotta', lambda o: hex_tiles('tiles_hex_terracotta', o, RED, (110, 90, 70), seed=72))
add(S, 'tiles_checker', lambda o: checker('tiles_checker', o, (232, 226, 214), (60, 58, 62), (120, 114, 104)))
add(S, 'tiles_checker_red', lambda o: checker('tiles_checker_red', o, (226, 210, 176), (150, 70, 46), (120, 104, 84), seed=74))
add(S, 'mosaic', lambda o: R.mosaic('mosaic', o))
add(S, 'mosaic_waves', lambda o: mosaic_waves('mosaic_waves', o))
add(S, 'mosaic_checker', lambda o: mosaic_checker('mosaic_checker', o))
add(S, 'dirt_path', lambda o: R.dirt_path('dirt_path', o))
add(S, 'dirt_path_dark', lambda o: ruts('dirt_path_dark', o, lambda: R.earth('x', o, (70, 58, 46), (110, 92, 70), lumps=1.2)))
add(S, 'dirt_ruts', lambda o: ruts('dirt_ruts', o, lambda: R.dirt_path('x', o), seed=84))
add(S, 'dirt_red', lambda o: ruts('dirt_red', o, lambda: R.earth('x', o, (130, 70, 44), (176, 104, 66), lumps=1.0), seed=85))
add(S, 'sand_path', lambda o: ruts('sand_path', o, lambda: R.sand('x', o, (224, 196, 146), (180, 150, 104), ripple=0), seed=86))
add(S, 'gravel', lambda o: R.gravel('gravel', o, [(150, 144, 134), (186, 178, 164), (118, 112, 104), (204, 196, 178)]))
add(S, 'gravel_warm', lambda o: R.gravel('gravel_warm', o, WARM, gaps=(96, 76, 54), seed=42))
add(S, 'gravel_dark', lambda o: R.gravel('gravel_dark', o, DARK, gaps=(30, 28, 26), seed=43))
add(S, 'gravel_white', lambda o: R.gravel('gravel_white', o, WHITE, gaps=(150, 144, 130), seed=44))
add(S, 'pebbles', lambda o: R.pebbles('pebbles', o, [(150, 144, 134), (178, 170, 156), (120, 114, 106), (168, 154, 128)]))
add(S, 'pebbles_beach', lambda o: R.pebbles('pebbles_beach', o, [(220, 214, 200), (190, 176, 150), (160, 154, 146)],
                                            ground=(200, 176, 130), seed=44, n=300))
add(S, 'stepping_grass', lambda o: stepping('stepping_grass', o, lambda: R.grass('x', o, *GRASS_SETS['grass_lush'], seed=40), GREY))
add(S, 'stepping_sand', lambda o: stepping('stepping_sand', o, lambda: R.sand('x', o, (238, 216, 166), (198, 170, 120)), WARM, seed=80))
add(S, 'stepping_moss', lambda o: stepping('stepping_moss', o, lambda: R.earth('x', o, (50, 80, 34), (96, 126, 52), lumps=1.2),
                                           BLUEGREY, seed=81))
add(S, 'stepping_snow', lambda o: stepping('stepping_snow', o, lambda: R.snow('x', o, size=1024), BLUEGREY, seed=82))
add(S, 'boardwalk', lambda o: boardwalk('boardwalk', o))
add(S, 'boardwalk_old', lambda o: boardwalk('boardwalk_old', o, seed=82, weathered=True))
add(S, 'snow_path', lambda o: snow_path('snow_path', o))
add(S, 'obsidian_path', lambda o: R.slabs('obsidian_path', o, 3, 3, (30, 26, 36), (20, 18, 26), (255, 110, 30), seed=24,
                                          crack=0.3, grout_w=2.0, offset=0.3))
add(S, 'marble_gold_path', lambda o: R.slabs('marble_gold_path', o, 2, 2, (240, 236, 226), (226, 220, 206), (210, 160, 60),
                                             seed=25, offset=0.0, crack=0.2, grout_w=3.0))

# --- SKALY
K = 'Skaly'
add(K, 'rock', lambda o: R.rock('rock', o))
add(K, 'rock_warm', lambda o: R.rock('rock_warm', o, (198, 172, 134), (132, 110, 84), seed=22, lichen=(150, 140, 80), lichen_amt=0.15))
add(K, 'rock_mossy', lambda o: R.rock('rock_mossy', o, (140, 140, 130), (84, 84, 80), seed=23, lichen=(80, 110, 50), lichen_amt=0.5))
add(K, 'rock_white', lambda o: R.rock('rock_white', o, (226, 222, 212), (170, 166, 156), seed=24, lichen=(170, 160, 120), lichen_amt=0.1))
add(K, 'rock_dark', lambda o: R.rock('rock_dark', o, (96, 92, 90), (54, 52, 52), seed=25, lichen=(90, 90, 70), lichen_amt=0.1))
add(K, 'rock_red', lambda o: R.rock('rock_red', o, (176, 106, 70), (116, 64, 42), seed=26, lichen=(150, 130, 80), lichen_amt=0.1))
add(K, 'granite', lambda o: R.gravel('granite', o, [(170, 160, 156), (120, 112, 110), (200, 190, 184), (90, 86, 88)],
                                     gaps=(140, 132, 128), seed=60, n=9000))
add(K, 'cliff', lambda o: R.strata('cliff', o, [(214, 178, 128), (190, 146, 98), (226, 196, 150), (170, 124, 84), (214, 178, 128)]))
add(K, 'cliff_grey', lambda o: R.strata('cliff_grey', o, [(150, 148, 146), (120, 118, 118), (172, 170, 166), (104, 102, 104), (150, 148, 146)], seed=24))
add(K, 'cliff_red', lambda o: R.strata('cliff_red', o, [(176, 100, 66), (150, 80, 52), (196, 126, 84), (130, 70, 46), (176, 100, 66)], seed=25))
add(K, 'cliff_white', lambda o: R.strata('cliff_white', o, [(232, 226, 212), (208, 200, 184), (240, 236, 224), (190, 182, 166), (232, 226, 212)], seed=26))
add(K, 'basalt', lambda o: R.rock('basalt', o, (70, 64, 62), (30, 28, 30), seed=26, lichen=(90, 40, 20), lichen_amt=0.1, n=40))
add(K, 'obsidian', lambda o: R.marble('obsidian', o, (26, 22, 32), (70, 60, 90), seed=27))
add(K, 'lava', lambda o: R.lava('lava', o))
add(K, 'sandstone', lambda o: R.earth('sandstone', o, (150, 136, 112), (184, 168, 140), seed=65, lumps=0.05))
add(K, 'stone_moss', lambda o: R.earth('stone_moss', o, (128, 126, 102), (160, 156, 128), seed=66, lumps=0.05))
add(K, 'limestone', lambda o: R.earth('limestone', o, (168, 162, 148), (196, 190, 176), seed=67, lumps=0.2))
add(K, 'marble', lambda o: R.marble('marble', o))
add(K, 'marble_dark', lambda o: R.marble('marble_dark', o, (90, 86, 84), (200, 196, 190), seed=10))
add(K, 'marble_green', lambda o: R.marble('marble_green', o, (70, 110, 90), (190, 210, 196), seed=11))
add(K, 'marble_pink', lambda o: R.marble('marble_pink', o, (220, 186, 180), (160, 120, 116), seed=12))

# --- SCIANY
W = 'Sciany'
add(W, 'blocks', lambda o: R.slabs('blocks', o, 2, 4, (220, 204, 170), (190, 172, 138), (130, 112, 86), 512, seed=10, crack=0.3))
add(W, 'blocks_grey', lambda o: R.slabs('blocks_grey', o, 2, 4, (150, 146, 140), (118, 114, 110), (70, 66, 64), 512, seed=12, crack=0.4))
add(W, 'blocks_marble', lambda o: R.slabs('blocks_marble', o, 2, 3, (236, 232, 222), (214, 208, 196), (160, 152, 136), 512, seed=14, crack=0.2, grout_w=2.0))
add(W, 'blocks_dark', lambda o: R.slabs('blocks_dark', o, 2, 4, (80, 74, 72), (60, 56, 56), (30, 26, 26), 512, seed=15, crack=0.4))
add(W, 'blocks_red', lambda o: R.slabs('blocks_red', o, 2, 4, (176, 106, 70), (150, 86, 56), (100, 66, 46), 512, seed=16, crack=0.3))
add(W, 'blocks_mossy', lambda o: R.slabs('blocks_mossy', o, 2, 4, (150, 146, 130), (124, 120, 106), (60, 90, 40), 512, seed=17, crack=0.5))
add(W, 'wall_rubble', lambda o: rubble_wall('wall_rubble', o, GREY, (120, 108, 90)))
add(W, 'wall_rubble_warm', lambda o: rubble_wall('wall_rubble_warm', o, WARM, (140, 116, 84), seed=86))
add(W, 'wall_cyclopean', lambda o: rubble_wall('wall_cyclopean', o, GREY, (70, 64, 58), seed=87, n=14, aniso=(1.0, 1.0)))
add(W, 'bricks_wall', lambda o: bricks('bricks_wall', o, (168, 88, 58), (140, 70, 46), (190, 176, 150), size=512, seed=88))
add(W, 'plaster', lambda o: R.plaster('plaster', o))
add(W, 'plaster_ochre', lambda o: R.plaster('plaster_ochre', o, (214, 170, 104), seed=13))
add(W, 'plaster_red', lambda o: R.plaster('plaster_red', o, (168, 52, 40), seed=14, dirt=(110, 50, 40)))
add(W, 'plaster_blue', lambda o: R.plaster('plaster_blue', o, (60, 100, 160), seed=15, dirt=(40, 60, 90)))
add(W, 'plaster_green', lambda o: R.plaster('plaster_green', o, (96, 130, 96), seed=16, dirt=(60, 80, 60)))
add(W, 'plaster_pink', lambda o: R.plaster('plaster_pink', o, (220, 170, 160), seed=17, dirt=(160, 120, 110)))
add(W, 'plaster_peeling', lambda o: mixed_ground('plaster_peeling', o, lambda: R.plaster('x', o),
                                                 lambda: R.slabs('x', o, 2, 4, (220, 204, 170), (190, 172, 138), (130, 112, 86), 512),
                                                 4, 0.66, 57, size=512))
add(W, 'meander_gold', lambda o: R.meander('meander_gold', o))
add(W, 'meander_white', lambda o: R.meander('meander_white', o, (236, 230, 214), (40, 50, 80), seed=56))
add(W, 'meander_black', lambda o: R.meander('meander_black', o, (210, 120, 60), (28, 24, 22), seed=57))
add(W, 'roof', lambda o: R.roof('roof', o))
add(W, 'roof_dark', lambda o: R.roof('roof_dark', o, (120, 64, 44), (86, 44, 32), seed=14))
add(W, 'roof_blue', lambda o: R.roof('roof_blue', o, (70, 100, 150), (50, 76, 120), seed=15))

# --- ROSLINY
P = 'Rosliny'
add(P, 'leaf_olive', lambda o: R.foliage('leaf_olive', o, (50, 64, 40), (104, 120, 76), (156, 168, 122), seed=19))
add(P, 'leaf_dark', lambda o: R.foliage('leaf_dark', o, (16, 38, 20), (32, 64, 32), (60, 96, 50), seed=20))
add(P, 'leaf_lush', lambda o: R.foliage('leaf_lush', o, (34, 72, 28), (70, 124, 44), (126, 172, 72), seed=22))
add(P, 'leaf_autumn', lambda o: R.foliage('leaf_autumn', o, (90, 40, 20), (164, 82, 30), (214, 146, 62), seed=24))
add(P, 'leaf_blossom', lambda o: R.foliage('leaf_blossom', o, (60, 90, 40), (220, 150, 180), (250, 220, 230), seed=26))
add(P, 'leaf_vine', lambda o: R.foliage('leaf_vine', o, (30, 60, 24), (60, 110, 40), (110, 150, 60), seed=28))
add(P, 'leaf_palm', lambda o: R.foliage('leaf_palm', o, (40, 80, 30), (80, 130, 50), (150, 180, 90), seed=29))
add(P, 'leaf_dead', lambda o: R.foliage('leaf_dead', o, (60, 44, 30), (110, 84, 54), (150, 120, 80), seed=30))
add(P, 'leaf_ivy', lambda o: R.foliage('leaf_ivy', o, (14, 40, 24), (30, 80, 40), (70, 120, 60), seed=31))
add(P, 'pine_needles', lambda o: R.pine_needles('pine_needles', o))
add(P, 'bark', lambda o: R.bark('bark', o))
add(P, 'bark_olive', lambda o: R.bark('bark_olive', o, (130, 120, 104), (78, 70, 60), seed=18))
add(P, 'bark_dark', lambda o: R.bark('bark_dark', o, (70, 56, 46), (36, 28, 24), seed=19))
add(P, 'bark_birch', lambda o: R.bark('bark_birch', o, (220, 214, 200), (120, 110, 100), seed=20))
add(P, 'straw', lambda o: straw('straw', o))

# --- DREWNO, METAL, TKANINY, CERAMIKA
M = 'Materialy'
add(M, 'wood', lambda o: R.wood('wood', o))
add(M, 'wood_dark', lambda o: R.wood('wood_dark', o, (86, 56, 36), (56, 36, 24), seed=16))
add(M, 'wood_ship', lambda o: R.wood('wood_ship', o, (110, 74, 44), (70, 46, 28), seed=18, planks=8))
add(M, 'wood_pale', lambda o: R.wood('wood_pale', o, (190, 160, 120), (150, 120, 86), seed=19))
add(M, 'wood_painted_blue', lambda o: R.wood('wood_painted_blue', o, (60, 100, 150), (40, 76, 120), seed=20))
add(M, 'wood_painted_red', lambda o: R.wood('wood_painted_red', o, (160, 56, 40), (120, 40, 30), seed=21))
add(M, 'bronze', lambda o: R.bronze('bronze', o))
add(M, 'gold', lambda o: gold_tex('gold', o))
add(M, 'iron', lambda o: iron('iron', o, rust=0.2))
add(M, 'iron_rusty', lambda o: iron('iron_rusty', o, rust=0.6, seed=104))
add(M, 'leather', lambda o: leather('leather', o))
add(M, 'leather_dark', lambda o: leather('leather_dark', o, col_=(60, 36, 22), seed=102))
add(M, 'rope', lambda o: rope('rope', o))
add(M, 'cloth', lambda o: R.cloth('cloth', o, (232, 222, 196)))
add(M, 'cloth_red', lambda o: R.cloth('cloth_red', o, (232, 222, 196), (168, 40, 32), stripes=6, seed=32))
add(M, 'cloth_blue', lambda o: R.cloth('cloth_blue', o, (232, 222, 196), (40, 70, 140), stripes=6, seed=33))
add(M, 'cloth_green', lambda o: R.cloth('cloth_green', o, (232, 222, 196), (60, 110, 60), stripes=6, seed=34))
add(M, 'cloth_yellow', lambda o: R.cloth('cloth_yellow', o, (232, 222, 196), (210, 160, 50), stripes=6, seed=35))
add(M, 'cloth_purple', lambda o: R.cloth('cloth_purple', o, (110, 40, 100), seed=36, border=(200, 150, 60)))
add(M, 'cloth_black', lambda o: R.cloth('cloth_black', o, (40, 36, 40), seed=37, border=(170, 130, 50)))
add(M, 'sail_red', lambda o: R.cloth('sail_red', o, (180, 50, 36), seed=38, border=(230, 200, 140)))
add(M, 'sail_white', lambda o: R.cloth('sail_white', o, (236, 226, 200), seed=39, border=(40, 60, 120)))
add(M, 'sail_black', lambda o: R.cloth('sail_black', o, (40, 34, 34), seed=40, border=(170, 40, 30)))
add(M, 'sail_purple', lambda o: R.cloth('sail_purple', o, (100, 40, 110), seed=41, border=(220, 180, 80)))
add(M, 'terracotta', lambda o: R.terracotta('terracotta', o))
add(M, 'terracotta_painted', lambda o: R.terracotta('terracotta_painted', o, seed=60, painted=True))
add(M, 'water', lambda o: R.water_ripple('water', o))

# styl malowania dla grup
paint([n for c, n, _ in LIB if c in ('Podloza',) and not n.startswith('grass')], **NATURAL)
paint(['rock', 'rock_warm', 'rock_mossy', 'rock_white', 'rock_dark', 'rock_red', 'cliff', 'cliff_grey', 'cliff_red',
       'cliff_white', 'basalt', 'sandstone', 'stone_moss', 'limestone', 'moss'], **NATURAL)
paint([n for c, n, _ in LIB if c == 'Sciezki' and not n.startswith(('mosaic', 'tiles_', 'boardwalk', 'stepping'))], **STONE)
paint([n for c, n, _ in LIB if c == 'Sciany' and not n.startswith('meander')], **WALL)
paint(['leaf_olive', 'leaf_dark', 'leaf_lush', 'leaf_autumn', 'leaf_blossom', 'leaf_vine', 'leaf_palm', 'leaf_dead',
       'leaf_ivy'], **LEAF)
paint(['bark', 'bark_olive', 'bark_dark', 'bark_birch'], **BARK)
paint(['wood', 'wood_dark', 'wood_ship', 'wood_pale', 'wood_painted_blue', 'wood_painted_red', 'boardwalk',
       'boardwalk_old'], **GRAIN)
paint(['bronze', 'gold', 'iron', 'iron_rusty', 'leather', 'leather_dark'], **METAL)

style([n for c, n, _ in LIB if c == 'Podloza'], cracks=0.25, pits=0.6)
style(['rock', 'rock_warm', 'rock_white', 'rock_dark', 'rock_red', 'cliff', 'cliff_grey', 'cliff_red', 'cliff_white',
       'basalt', 'sandstone', 'limestone', 'marble', 'marble_dark', 'marble_green', 'marble_pink'], cracks=0.8, pits=0.35)
style(['stone_moss', 'rock_mossy', 'blocks_mossy', 'cobble_mossy'], cracks=0.9, pits=0.35, moss=0.7)
style([n for c, n, _ in LIB if c == 'Sciezki' and n not in ('cobble_mossy',)], cracks=0.35, pits=0.3)
style([n for c, n, _ in LIB if c == 'Sciany' and not n.startswith('meander') and n != 'blocks_mossy'], cracks=0.7, pits=0.3)
style([n for c, n, _ in LIB if c in ('Trawy', 'Rosliny')], mottle=0.1, desat=0.22, contrast=0.88)
style(['mosaic', 'mosaic_waves', 'mosaic_checker', 'meander_gold', 'meander_white', 'meander_black', 'lava', 'water',
       'obsidian'] + [n for c, n, _ in LIB if n.startswith(('cloth', 'sail', 'terracotta'))],
      mottle=0.04, desat=0.12, contrast=0.95)
style(['moss'], cracks=0.0, pits=0.5, mottle=0.1, desat=0.22, contrast=0.88)


def build(out_dir, only=None):
    done = []
    for cat, name, fn in LIB:
        if only and name not in only:
            continue
        fn(out_dir)
        done.append(name)
    return done
