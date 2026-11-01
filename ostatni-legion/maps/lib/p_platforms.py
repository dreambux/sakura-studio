"""Platformy pod jednostki: duze skaly z plaskim wierzchem (jak w tower defense), w greckim stylu.

Budowa: obrys 2D (wygladzony, z szumem) -> klif z fasetowanej skaly (kilka pierscieni, plaskie cieniowanie)
-> gruba warstwa wierzchu (ziemia/trawa/piasek/marmur) z widocznym brzegiem -> glazy u podstawy i na krawedzi,
opcjonalnie kamienne schody, kepki trawy, ruiny. Marker 'Stand' = wysokosc i promien pola do stawiania.
"""
import math
import random

import bmesh
from mathutils import Vector

from .props import prop, begin, add, marker, T, F, GOLD, BRONZE, rock_bm, blob_bm, box, cyl, tube, C
from .p_arch import MARBLE, BLOCKS, column


# ------------------------------------------------------------------ obrysy
def chaikin(pts, it=2):
    for _ in range(it):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25))
            out.append((a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75))
        pts = out
    return pts


def resample(pts, step):
    n = len(pts)
    seg = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]
    L = sum(seg)
    m = max(12, int(L / step))
    out = []
    i, acc = 0, 0.0
    for k in range(m):
        t = k * L / m
        while acc + seg[i] < t:
            acc += seg[i]
            i += 1
        f = (t - acc) / max(seg[i], 1e-6)
        a, b = pts[i], pts[(i + 1) % n]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def area_sign(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def normals2d(pts):
    n = len(pts)
    ccw = area_sign(pts) > 0
    out = []
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        nx, ny = (ty / l, -tx / l) if ccw else (-ty / l, tx / l)
        out.append((nx, ny))
    return out


def shape(kind, sx, sy, seed=0, wob=0.08):
    rnd = random.Random(seed)
    if kind == 'round':
        base = [(math.cos(a) * sx, math.sin(a) * sy) for a in [2 * math.pi * k / 14 for k in range(14)]]
    elif kind == 'bean':
        base = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            r = 1 - 0.32 * max(0, math.cos(a - math.pi / 2)) ** 2
            base.append((math.cos(a) * sx * r, math.sin(a) * sy * r))
    elif kind == 'long':
        base = [(-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)]
        base = chaikin(base, 1)
    elif kind == 'L':
        base = [(-sx, -sy), (sx, -sy), (sx, -sy * 0.15), (-sx * 0.15, -sy * 0.15), (-sx * 0.15, sy), (-sx, sy)]
    elif kind == 'crescent':
        base = []
        for k in range(12):
            a = math.pi * k / 11
            base.append((math.cos(a) * sx, math.sin(a) * sy))
        for k in range(12):
            a = math.pi * (11 - k) / 11
            base.append((math.cos(a) * sx * 0.55, math.sin(a) * sy * 0.45))
    elif kind == 'tri':
        base = [(math.cos(a) * sx, math.sin(a) * sy) for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6)]
        base = chaikin(base, 1)
    else:
        raise ValueError(kind)
    pts = chaikin(base, 3)
    pts = resample(pts, 0.6)
    out = []
    ph = rnd.uniform(0, 6)
    for i, (x, y) in enumerate(pts):
        t = 2 * math.pi * i / len(pts)
        f = 1 + wob * (math.sin(t * 3 + ph) * 0.6 + math.sin(t * 7 + ph * 2) * 0.4)
        out.append((x * f, y * f))
    if area_sign(out) < 0:
        out.reverse()
    return out


# ------------------------------------------------------------------ bryly
def cliff_bm(pts, h, seed=0, seg=1.7, bulge=1.0, facet=0.35):
    """Fasetowana sciana skalna pod obrysem pts (gora na z=h)."""
    rnd = random.Random(seed)
    P = resample(pts, seg)
    N = normals2d(P)
    # (z wzgledny, wysuniecie) - lekki nawis pod krawedzia, potem skos do podstawy
    rings = [(1.0, 0.05), (0.82, 0.45), (0.55, 0.25), (0.3, 0.7), (0.08, 1.1), (-0.12, 1.5)]
    bm = bmesh.new()
    grid = []
    for j, (zf, off) in enumerate(rings):
        row = []
        for (x, y), (nx, ny) in zip(P, N):
            o = (off + (rnd.uniform(-facet, facet) if 0 < j else 0.0)) * bulge
            z = h * zf + (rnd.uniform(-0.25, 0.25) * h * 0.15 if 0 < j < len(rings) - 1 else 0)
            row.append(bm.verts.new((x + nx * o, y + ny * o, z)))
        grid.append(row)
    n = len(P)
    for j in range(len(rings) - 1):
        for i in range(n):
            i2 = (i + 1) % n
            bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i2], grid[j][i2]))
    bm.faces.new(grid[0])          # wierzch skaly (pod warstwa ziemi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # trojkatowanie czesci quadow -> ostrzejsze fasety
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) == 4 and rnd.random() < 0.55])
    return bm


def cap_bm(pts, h, thick=0.35, inset=0.12, dome=0.0):
    """Warstwa wierzchu: plaska plyta z widocznym brzegiem (lekko zaokraglonym)."""
    N = normals2d(pts)
    bm = bmesh.new()
    top = [bm.verts.new((x - nx * inset, y - ny * inset, h + thick)) for (x, y), (nx, ny) in zip(pts, N)]
    mid = [bm.verts.new((x + nx * 0.06, y + ny * 0.06, h + thick * 0.45)) for (x, y), (nx, ny) in zip(pts, N)]
    bot = [bm.verts.new((x + nx * 0.02, y + ny * 0.02, h - 0.05)) for (x, y), (nx, ny) in zip(pts, N)]
    n = len(pts)
    for A, B in ((top, mid), (mid, bot)):
        for i in range(n):
            i2 = (i + 1) % n
            bm.faces.new((A[i], B[i], B[i2], A[i2]))
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def inside(pts, x, y):
    c = False
    n = len(pts)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c


def edge_dist(pts, x, y):
    best = 1e9
    n = len(pts)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy + 1e-9)))
        best = min(best, math.hypot(x - x1 - dx * t, y - y1 - dy * t))
    return best


def stairs(p, n, h, mat, width=3.0, rise=0.5, run=0.62, name='stairs'):
    """Kamienne schody od ziemi do krawedzi (p = punkt krawedzi, n = normalna na zewnatrz)."""
    k = max(2, int(math.ceil(h / rise)))
    ang = math.degrees(math.atan2(n[1], n[0]))
    for i in range(k):
        top = h - i * rise
        d = 0.4 + i * run
        cx, cy = p[0] + n[0] * d, p[1] + n[1] * d
        add(box(run + 0.05, width, top + 0.4, 0.04), mat, loc=(cx, cy, (top - 0.4) / 2), rot=(0, 0, ang),
            uv='box', tile=3, name=name)
    # boczne murki (policzki schodow)
    for side in (-1, 1):
        L = k * run + 0.4
        ox, oy = -n[1] * side * (width / 2 + 0.3), n[0] * side * (width / 2 + 0.3)
        bm = C.bm_extrude([(0, 0), (L, 0), (L, 0.5), (0.2, h + 0.5), (0, h + 0.5)], 0.6, 0.05, 1)
        C.bm_transform(bm, rot=(90, 0, 0))
        add(bm, mat, loc=(p[0] + ox, p[1] + oy, -0.3), rot=(0, 0, ang), uv='box', tile=3, name=name + '_cheek')


def platform(name, kind='round', sx=5.0, sy=5.0, h=3.0, top='dirt', side='cliff_grey', seed=1, rocks=True,
             tufts=None, stair=None, extra=None, wob=0.08, bulge=1.0, top_rough=0.95):
    begin(name)
    pts = shape(kind, sx, sy, seed, wob)
    rnd = random.Random(seed * 7 + 1)
    add(cliff_bm(pts, h, seed, bulge=bulge), T(side, 0.9), uv='box', tile=6, smooth=False, name='cliff')
    add(cap_bm(pts, h), T(top, top_rough), uv='box', tile=8, smooth=True, angle=50, name='top')
    cx, cy = centroid(pts)
    N = normals2d(pts)
    if rocks:
        # glazy u podstawy (czesciowo zakopane) i kilka na krawedzi wierzchu
        for k in range(rnd.randint(5, 8)):
            i = rnd.randrange(len(pts))
            (x, y), (nx, ny) = pts[i], N[i]
            r = rnd.uniform(0.6, 1.4)
            d = 1.4 + r * 0.6
            add(rock_bm(r, seed * 13 + k, 1, 0.35, 0.3), T(side, 0.9), loc=(x + nx * d, y + ny * d, r * 0.25),
                rot=(0, 0, rnd.uniform(0, 360)), uv='box', tile=5, smooth=False, name='base_rock')
        for k in range(rnd.randint(2, 4)):
            i = rnd.randrange(len(pts))
            (x, y), (nx, ny) = pts[i], N[i]
            r = rnd.uniform(0.35, 0.7)
            add(rock_bm(r, seed * 31 + k, 1, 0.35, 0.3), T(side, 0.9), loc=(x - nx * 0.6, y - ny * 0.6, h + 0.3),
                rot=(0, 0, rnd.uniform(0, 360)), uv='box', tile=5, smooth=False, name='rim_rock')
        # odlamki
        for k in range(rnd.randint(6, 10)):
            i = rnd.randrange(len(pts))
            (x, y), (nx, ny) = pts[i], N[i]
            r = rnd.uniform(0.15, 0.35)
            d = rnd.uniform(2.0, 3.6)
            add(rock_bm(r, seed * 57 + k, 1, 0.4, 0.3), T(side, 0.9), loc=(x + nx * d, y + ny * d, r * 0.2),
                uv='box', smooth=False, name='pebble')
    if tufts:
        mat = T(tufts, 0.95)
        for k in range(rnd.randint(8, 14)):
            i = rnd.randrange(len(pts))
            (x, y), (nx, ny) = pts[i], N[i]
            inner = rnd.uniform(0.2, 0.9)
            for b in range(5):
                a = b * 72 + rnd.uniform(-20, 20)
                tip = (x - nx * inner + math.cos(math.radians(a)) * 0.35, y - ny * inner + math.sin(math.radians(a)) * 0.35,
                       h + 0.35 + rnd.uniform(0.5, 0.9))
                add(tube([(x - nx * inner, y - ny * inner, h + 0.3), tip], 0.07, radii=[1, 0.1], res=2), mat,
                    uv='box', smooth=False, name='tuft')
    if stair is not None:
        i = int(stair * len(pts)) % len(pts)
        stairs(pts[i], N[i], h, T('limestone', 0.85))
    if extra:
        extra(pts, h, rnd)
    # pole do stawiania jednostek (dla skryptu mapy)
    rad = max(0.5, min(edge_dist(pts, cx, cy) - 0.6, 30))
    marker('Stand', (cx, cy, h + 0.35), radius=round(rad, 2), size=[round(sx * 2, 1), round(sy * 2, 1)])
    return pts


# ------------------------------------------------------------------ katalog platform
def _flowers(pts, h, rnd, cols=((230, 70, 60), (250, 220, 90), (240, 240, 250), (170, 110, 220))):
    for k in range(18):
        i = rnd.randrange(len(pts))
        x, y = pts[i]
        cx, cy = centroid(pts)
        t = rnd.uniform(0.08, 0.2)
        px, py = x + (cx - x) * t, y + (cy - y) * t
        c = rnd.choice(cols)
        add(cyl(0.025, 0.45, 4), F('stem', (70, 110, 50)), loc=(px, py, h + 0.55), uv='none', name='stem')
        add(C.bm_sphere(0.1, 6, 4), F('flower' + str(c), c, 0.6), loc=(px, py, h + 0.8), name='flower')


def _ruins(pts, h, rnd):
    cx, cy = centroid(pts)
    # fragment stylobatu i kikuty kolumn na brzegu
    i = rnd.randrange(len(pts))
    x, y = pts[i]
    t = 0.25
    px, py = x + (cx - x) * t, y + (cy - y) * t
    add(box(3.2, 1.3, 0.35, 0.04), MARBLE(), loc=(px, py, h + 0.5), rot=(0, 0, rnd.uniform(0, 90)), name='slab')
    from .props import fluted_column_bm
    add(fluted_column_bm(0.8, 2.3, 18, 0.95, 36, 2), MARBLE(), loc=(px, py, h + 0.65), uv='cyl', tile=3,
        name='stump')
    j = (i + len(pts) // 2) % len(pts)
    x, y = pts[j]
    px, py = x + (cx - x) * 0.2, y + (cy - y) * 0.2
    add(fluted_column_bm(0.7, 2.6, 18, 0.95, 36, 2), MARBLE(), loc=(px, py, h + 1.05), rot=(0, 90, 30), uv='cyl',
        tile=3, name='drum')


def _marble_paving(pts, h, rnd):
    """Bruk z marmurowych plyt (tekstura na wierzchu) + kilka obluzowanych, przekrzywionych plyt na brzegu."""
    N = normals2d(pts)
    for k in range(5):
        i = rnd.randrange(len(pts))
        (x, y), (nx, ny) = pts[i], N[i]
        add(box(1.3, 1.1, 0.22, 0.05), MARBLE(), loc=(x - nx * 0.7, y - ny * 0.7, h + 0.42),
            rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 90)), uv='box', tile=3, name='loose_slab')
    i = rnd.randrange(len(pts))
    (x, y), (nx, ny) = pts[i], N[i]
    add(box(1.3, 1.3, 0.8, 0.05), MARBLE(), loc=(x - nx * 1.2, y - ny * 1.2, h + 0.75), name='altar_block')
    add(box(1.5, 1.5, 0.2, 0.05), MARBLE(), loc=(x - nx * 1.2, y - ny * 1.2, h + 1.25), name='altar_top')


def _lava_cracks(pts, h, rnd):
    cx, cy = centroid(pts)
    for k in range(5):
        i = rnd.randrange(len(pts))
        x, y = pts[i]
        a = (x, y, h * 0.6)
        b = (x + (cx - x) * 0.05, y + (cy - y) * 0.05, h * 0.2)
        add(tube([a, b], 0.12, radii=[1, 0.4], res=2), F('lava_glow', (255, 110, 30), 0.5, 0.0, 6), uv='none',
            name='crack')


def _snow_drifts(pts, h, rnd):
    N = normals2d(pts)
    for k in range(8):
        i = rnd.randrange(len(pts))
        (x, y), (nx, ny) = pts[i], N[i]
        add(blob_bm(rnd.uniform(0.8, 1.4), k, 1, 0.15, (1.4, 1, 0.35)), T('snow', 0.8),
            loc=(x + nx * 1.6, y + ny * 1.6, 0.1), rot=(0, 0, math.degrees(math.atan2(ny, nx))), name='drift')


PLATFORMS = [
    # nazwa, opis, parametry
    ('platforma_okragla', 'Okragla skala z ubita ziemia (1-2 jednostki)',
     dict(kind='round', sx=4.5, sy=4.5, h=3.0, top='dirt', side='cliff_grey', seed=1)),
    ('platforma_mala', 'Mala skala na 1 jednostke', dict(kind='round', sx=2.8, sy=2.6, h=2.4, top='dirt_path',
                                                          side='cliff_grey', seed=2)),
    ('platforma_owalna', 'Owalna skala z trawa i kwiatami', dict(kind='round', sx=8, sy=5, h=3.2, top='grass_meadow',
                                                                  side='cliff_white', seed=3, tufts='grass_lush',
                                                                  extra=_flowers)),
    ('platforma_fasolka', 'Skala w ksztalcie fasolki (obok zakretu sciezki)',
     dict(kind='bean', sx=7, sy=5, h=3.0, top='earth_red', side='rock_warm', seed=4)),
    ('platforma_dluga', 'Dluga polka skalna wzdluz sciezki', dict(kind='long', sx=11, sy=3.2, h=2.8, top='dirt',
                                                                   side='cliff', seed=5)),
    ('platforma_l', 'Skala w ksztalcie L (narozna)', dict(kind='L', sx=7, sy=7, h=3.0, top='ground_scattered',
                                                           side='cliff_grey', seed=6)),
    ('platforma_polksiezyc', 'Polksiezyc obejmujacy luk sciezki', dict(kind='crescent', sx=9, sy=8, h=3.0,
                                                                         top='grass_dry', side='cliff_white', seed=7,
                                                                         tufts='grass_dry')),
    ('platforma_trojkatna', 'Trojkatna skala (rozwidlenie sciezek)', dict(kind='tri', sx=6, sy=6, h=3.0,
                                                                            top='gravel_warm', side='rock', seed=8)),
    ('platforma_wysoka', 'Wysoka iglica skalna ze schodami (snajperzy)',
     dict(kind='round', sx=4.2, sy=4.0, h=7.0, top='flagstone_dirt', side='cliff_grey', seed=9, stair=0.75)),
    ('platforma_schody', 'Skala ze schodami z kamienia', dict(kind='round', sx=6, sy=5, h=4.0, top='dirt',
                                                               side='cliff_white', seed=10, stair=0.8)),
    ('platforma_ruiny', 'Skala z ruinami (kikut kolumny, plyta stylobatu)',
     dict(kind='round', sx=6.5, sy=5.5, h=3.2, top='grass_dry', side='limestone', seed=11, tufts='grass_dry',
          extra=_ruins)),
    ('platforma_marmurowa', 'Skala z bruku marmurowych plyt (swiatynna)',
     dict(kind='round', sx=7, sy=6, h=3.4, top='paving_marble', side='cliff_white', seed=12, extra=_marble_paving)),
    ('platforma_piaszczysta', 'Nadmorska skala z piaskiem', dict(kind='bean', sx=7, sy=4.5, h=2.4, top='sand',
                                                                  side='sandstone', seed=13, tufts='grass_sandy')),
    ('platforma_trawiasta', 'Zielona skala (gaj oliwny)', dict(kind='round', sx=6, sy=6, h=3.0, top='grass_lush',
                                                                side='rock_mossy', seed=14, tufts='grass_lush',
                                                                extra=_flowers)),
    ('platforma_wulkaniczna', 'Bazaltowa skala z zarem w szczelinach',
     dict(kind='round', sx=6, sy=5, h=3.2, top='ash', side='basalt', seed=15, extra=_lava_cracks)),
    ('platforma_sniezna', 'Osniezona skala (Boreasz)', dict(kind='round', sx=6, sy=5, h=3.0, top='snow',
                                                             side='cliff_grey', seed=16, extra=_snow_drifts)),
    ('platforma_czerwona', 'Czerwona skala (Kreta, Knossos)', dict(kind='bean', sx=6.5, sy=5, h=3.0,
                                                                     top='dirt_red', side='cliff_red', seed=17)),
    ('platforma_podziemna', 'Ciemna skala z Hadesu', dict(kind='round', sx=6, sy=5, h=3.0, top='cobble_ash',
                                                           side='rock_dark', seed=18)),
]


def _reg(n, d, kw):
    prop(n, 'Platformy', d)(lambda: platform(n, **kw))


for _n, _d, _kw in PLATFORMS:
    _reg(_n, _d, _kw)


@prop('platforma_pietrowa', 'Platformy', 'Dwupoziomowa skala ze schodami miedzy poziomami')
def tiered():
    pts = platform('platforma_pietrowa', 'bean', 9, 7, 2.6, 'dirt', 'cliff_grey', 21, stair=0.78)
    # gorny poziom
    up = [(x * 0.62, y * 0.62) for x, y in shape('round', 7, 6, 22)]
    up = [(x + 2.0, y + 1.0) for x, y in up]
    h2 = 2.6
    add(C.bm_transform(cliff_bm(up, h2, 22, bulge=0.6), loc=(0, 0, 2.95)), T('cliff_grey', 0.9), uv='box', tile=6,
        smooth=False, name='cliff2')
    add(C.bm_transform(cap_bm(up, h2), loc=(0, 0, 2.95)), T('grass_dry', 0.95), uv='box', tile=8, name='top2')
    N = normals2d(up)
    i = int(0.62 * len(up))
    p = up[i]
    k = 6
    ang = math.degrees(math.atan2(N[i][1], N[i][0]))
    for s in range(k):
        top = 2.95 + h2 - s * 0.45
        d = 0.4 + s * 0.8
        hh = top - 2.85
        add(box(0.85, 2.6, hh, 0.04), T('limestone', 0.85), loc=(p[0] + N[i][0] * d, p[1] + N[i][1] * d,
                                                                2.85 + hh / 2), rot=(0, 0, ang), name='step2')
    cx, cy = centroid(up)
    marker('Stand', (cx, cy, 2.95 + h2 + 0.35), radius=2.6, size=[8.7, 7.4])
