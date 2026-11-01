"""Port i morze: triremy, lodzie, pomosty, kotwice, sieci, dzwig portowy."""
import math
import random

import bmesh
from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, GLOW, rock_bm, blob_bm, box, cyl, tube,
                    lathe, recalc, C)


def hull_bm(L=40.0, W=7.0, H=4.0, nx=24, nz=6, ram=True):
    """Kadlub: przekroje w ksztalcie U, zwezenie do dziobu (-Y) i rufy (+Y), podniesiona rufa."""
    bm = bmesh.new()
    rings = []
    for i in range(nx + 1):
        t = i / nx                     # 0 = dziob (-Y), 1 = rufa (+Y)
        y = -L / 2 + L * t
        width = W / 2 * math.sin(math.pi * (0.08 + 0.92 * t)) ** 0.55
        sheer = 0.6 * (1 - t) ** 3 * H * 0.5 + 2.2 * t ** 4 * H * 0.6
        ring = []
        for k in range(nz + 1):
            a = math.pi * k / nz        # 0 = lewa burta, pi = prawa
            x = -math.cos(a) * width
            z = -math.sin(a) * H * (0.9 if 0.05 < t < 0.95 else 0.6)
            ring.append(bm.verts.new((x, y, z + H + sheer)))
        rings.append(ring)
    for i in range(nx):
        for k in range(nz):
            bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][k + 1], rings[i][k + 1]))
    # poklad
    bm.faces.new([r[0] for r in rings] + [r[-1] for r in reversed(rings)])
    recalc(bm)
    return bm


@prop('trirema', 'Port', 'Grecka trirema bojowa (40 st.): taran z brazu, oko, 3 rzedy wiosel, zagiel')
def trireme(name='trirema', sail='sail_red', shields=(170, 40, 30), seed=1, L=40.0, sail_up=True):
    begin(name)
    W, H = 7.0, 3.6
    add(hull_bm(L, W, H), T('wood_ship', 0.75), uv='box', tile=3, smooth=True, name='hull')
    # pas malowany i oko na dziobie
    add(box(W * 0.98, L * 0.8, 0.5, 0.05), F('hull_paint', (40, 40, 44), 0.6), loc=(0, 0.5, H + 0.3), name='wale')
    for sx in (-1, 1):
        add(C.bm_sphere(0.6, 16, 8), F('eye_white', (236, 232, 220)), loc=(sx * 1.5, -L / 2 + 3.2, H + 1.4),
            scale=(0.3, 1.3, 0.8), name='eye')
        add(C.bm_sphere(0.3, 12, 6), F('eye_black', (16, 16, 20)), loc=(sx * 1.62, -L / 2 + 3.0, H + 1.4),
            scale=(0.3, 1, 1), name='pupil')
    # taran
    add(cyl(0.9, 4.5, 4, r2=0.15), BRONZE(), loc=(0, -L / 2 - 1.2, 1.2), rot=(90, 0, 45), uv='box', name='ram')
    # rufa zakrzywiona (aplustre)
    pts = [(0, L / 2 - 1, H + 2.5), (0, L / 2 + 1.5, H + 4.5), (0, L / 2 + 1.0, H + 7.5), (0, L / 2 - 0.6, H + 8.5)]
    add(tube(pts, 0.55, radii=[1.2, 1.0, 0.7, 0.4]), T('wood_ship'), uv='cyl', name='stern')
    pts = [(0, -L / 2 + 1, H + 1.5), (0, -L / 2 - 0.5, H + 3.0), (0, -L / 2 - 0.2, H + 4.2)]
    add(tube(pts, 0.4, radii=[1, 0.8, 0.5]), T('wood_ship'), uv='cyl', name='bow')
    # poklad
    add(box(W * 0.7, L * 0.8, 0.3, 0.02), T('wood'), loc=(0, 0, H + 0.9), uv='box', tile=3, name='deck')
    # wiosla (3 rzedy) i tarcze
    rnd = random.Random(seed)
    for sx in (-1, 1):
        for row in range(3):
            for k in range(13):
                y = -L / 2 + 7 + k * (L - 13) / 12
                z = H - 0.4 - row * 0.8
                pts = [(sx * (W / 2 - 0.2), y, z), (sx * (W / 2 + 4.5 + row * 0.8), y + 1.0, z - 2.6 - row * 0.4)]
                add(tube(pts, 0.08, smooth=False) if False else C.bm_tube(pts, 0.08, smooth=False, bevel_res=1),
                    T('wood'), uv='none', name='oar')
        for k in range(10):
            y = -L / 2 + 9 + k * (L - 17) / 9
            add(cyl(0.75, 0.15, 16), F('shield' + str(shields), shields, 0.5), loc=(sx * (W / 2 + 0.15), y, H + 1.4),
                rot=(0, 90, 0), uv='none', name='shield')
            add(cyl(0.25, 0.2, 10), BRONZE(), loc=(sx * (W / 2 + 0.25), y, H + 1.4), rot=(0, 90, 0), name='boss')
    # maszt i zagiel
    add(cyl(0.35, 16, 12), T('wood_dark'), loc=(0, -2, H + 8.5), uv='cyl', name='mast')
    add(cyl(0.22, 15, 10), T('wood_dark'), loc=(0, -2.3, H + 15.0), rot=(0, 90, 0), uv='cyl', name='yard')
    if sail_up:
        bm = C.bm_grid(10, 8, 14, 9)
        C.bm_map(bm, lambda co: (co.x, 0.9 * math.sin(math.pi * (co.x / 14 + 0.5)) * (0.4 + 0.6 * -co.z / 9) - 0.3,
                                 co.z))
        C.bm_solidify(bm, 0.06)
        add(bm, T(sail, 0.9), loc=(0, -2.6, H + 15.0), uv='box', tile=14, name='sail')
        # emblemat (oko/sowa) na zaglu
        add(cyl(1.8, 0.1, 24), GOLD() if sail != 'sail_white' else F('emb_blue', (40, 60, 120)),
            loc=(0, -3.35, H + 10.8), rot=(90, 0, 0), name='emblem')
    for sx in (-1, 1):
        add(C.bm_tube([(0, -2, H + 16.3), (sx * 3.4, L / 2 - 2, H + 2.0)], 0.04, smooth=False, bevel_res=1),
            F('rope', (160, 130, 80)), uv='none', name='rope')
    add(C.bm_tube([(0, -2, H + 16.3), (0, -L / 2 - 0.2, H + 4.2)], 0.04, smooth=False, bevel_res=1),
        F('rope', (160, 130, 80)), uv='none', name='rope')
    add(box(1.4, 3.0, 2.0, 0.08), T('wood'), loc=(0, L / 2 - 4, H + 2.0), name='helm_house')
    for sx in (-1, 1):
        add(box(0.3, 3.5, 0.3, 0.02), T('wood_dark'), loc=(sx * 1.6, L / 2 - 2.5, H - 0.8), rot=(25, 0, 0),
            name='steer_oar')


prop('trirema_biala', 'Port', 'Trirema z bialym zaglem i niebieskimi tarczami')(
    lambda: trireme('trirema_biala', 'sail_white', (40, 70, 140), 2))
prop('trirema_czarna', 'Port', 'Trirema wroga / widmowa (czarny zagiel)')(
    lambda: trireme('trirema_czarna', 'sail_black', (60, 60, 64), 3))
prop('trirema_bez_zagla', 'Port', 'Trirema zacumowana (zagiel zwiniety)')(
    lambda: trireme('trirema_bez_zagla', 'sail_red', (170, 40, 30), 4, sail_up=False))


@prop('wrak_statku', 'Port', 'Wrak statku (przechylony, polamany)')
def wreck():
    begin('wrak_statku')
    bm = hull_bm(26, 6, 3.2, 16, 6)
    kill = [f for f in bm.faces if f.calc_center_median().y > 6 and f.calc_center_median().z > 2.5]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    add(bm, T('wood_dark', 0.85), rot=(0, 18, 8), uv='box', tile=3, name='hull')
    add(cyl(0.3, 9, 10), T('wood_dark'), loc=(1.5, -1, 5.5), rot=(0, 35, 0), uv='cyl', name='mast')
    bm = C.bm_grid(6, 5, 6, 5)
    C.bm_map(bm, lambda co: (co.x, 0.3 * math.sin(co.x * 1.3) + 0.4 * math.sin(co.z), co.z))
    add(bm, T('sail_white', 0.95), loc=(3.6, -1.5, 8.0), rot=(0, 30, 0), uv='box', tile=6, name='sailrag')
    rnd = random.Random(3)
    for k in range(6):
        add(box(rnd.uniform(1.5, 3.5), 0.4, 0.2, 0.02), T('wood_dark'),
            loc=(rnd.uniform(-5, 5), rnd.uniform(-10, 10), 0.2), rot=(0, 0, rnd.uniform(0, 180)), name='plank')


@prop('lodz_rybacka', 'Port', 'Mala lodz rybacka z wioslami')
def fishing_boat():
    begin('lodz_rybacka')
    add(hull_bm(10, 3.2, 1.3, 12, 5), T('wood', 0.8), uv='box', tile=3, name='hull')
    add(box(3.0, 9.0, 0.25, 0.02), F('boat_band', (40, 90, 150)), loc=(0, 0.3, 1.85), name='band')
    for y in (-1.5, 1.5):
        add(box(2.6, 0.4, 0.15, 0.02), T('wood'), loc=(0, y, 1.5), name='thwart')
    for sx in (-1, 1):
        add(C.bm_tube([(sx * 1.4, 0, 1.7), (sx * 3.2, 1.6, 0.6)], 0.06, smooth=False, bevel_res=1), T('wood'),
            uv='none', name='oar')
    add(box(1.6, 1.4, 0.4, 0.05), F('net', (140, 120, 90), 0.95), loc=(0, 2.5, 1.5), name='net')


@prop('pomost', 'Port', 'Drewniany pomost (12 st.) na palach')
def pier(name='pomost', L=12.0):
    begin(name)
    for k in range(int(L / 1.0)):
        add(box(6.0, 0.95, 0.3, 0.02), T('wood'), loc=(0, -L / 2 + 0.5 + k, 2.0), rot=(0, 0, random.Random(k).uniform(-1, 1)),
            uv='box', tile=3, name='plank')
    for y in range(-int(L / 2), int(L / 2) + 1, 4):
        for sx in (-1, 1):
            add(cyl(0.35, 5.0, 10), T('wood_dark'), loc=(sx * 2.8, y, 0.0), uv='cyl', name='pile')
            add(C.bm_torus(0.4, 0.07, 12, 5), F('rope', (160, 130, 80)), loc=(sx * 2.8, y, 1.6), uv='none',
                name='ropering')
    for sx in (-1, 1):
        add(box(0.4, L, 0.4, 0.02), T('wood_dark'), loc=(sx * 3.0, 0, 1.75), name='beam')


@prop('pacholek', 'Port', 'Kamienny pacholek cumowniczy z lina')
def bollard():
    begin('pacholek')
    add(lathe([(0, 0), (0.6, 0), (0.5, 0.9), (0.7, 1.1), (0.7, 1.3), (0, 1.3)], 20), T('blocks_grey'), uv='box',
        name='post')
    add(C.bm_torus(0.55, 0.1, 20, 6), F('rope', (160, 130, 80)), loc=(0, 0, 0.8), uv='none', name='rope')
    add(C.bm_tube([(0.5, 0, 0.8), (1.5, -0.5, 0.3), (3.0, -1.0, 0.1)], 0.1), F('rope', (160, 130, 80)), uv='none',
        name='ropeend')


@prop('kotwica', 'Port', 'Kamienno-brazowa kotwica')
def anchor():
    begin('kotwica')
    add(cyl(0.18, 4.0, 10), BRONZE(), loc=(0, 0, 2.2), uv='box', name='shank')
    add(C.bm_torus(0.4, 0.1, 16, 6), BRONZE(), loc=(0, 0, 4.4), rot=(90, 0, 0), name='ring')
    pts = [(-1.6, 0, 1.2), (-1.3, 0, 0.5), (0, 0, 0.2), (1.3, 0, 0.5), (1.6, 0, 1.2)]
    add(tube(pts, 0.2, res=6), BRONZE(), uv='box', name='arms')
    add(box(2.6, 0.5, 0.5, 0.06), T('blocks_grey'), loc=(0, 0, 3.8), name='stock')
    for sx in (-1, 1):
        add(cyl(0.3, 0.6, 3, r2=0.0), BRONZE(), loc=(sx * 1.65, 0, 1.4), rot=(0, sx * -20, 0), name='fluke')


@prop('sieci_rybackie', 'Port', 'Sieci rozwieszone na palach')
def nets():
    begin('sieci_rybackie')
    for x in (-3, 0, 3):
        add(cyl(0.15, 4.0, 8), T('wood_dark'), loc=(x, 0, 2.0), uv='cyl', name='pole')
    bm = C.bm_grid(12, 6, 6, 2.8)
    C.bm_map(bm, lambda co: (co.x, 0.3 * math.sin(co.x * 1.1) ** 2, co.z - 0.5 * math.cos(co.x * 0.5)))
    add(bm, F('net', (140, 120, 90), 0.95), loc=(0, 0, 3.9), uv='none', name='net')
    for k in range(5):
        add(C.bm_sphere(0.18, 8, 6), F('float', (200, 160, 80)), loc=(-2.5 + k * 1.25, 0.2, 3.9), name='float')


@prop('dzwig_portowy', 'Port', 'Drewniany dzwig portowy z kolem bieznym')
def crane():
    begin('dzwig_portowy')
    for sx in (-1, 1):
        add(box(0.5, 0.5, 9, 0.03), T('wood_dark'), loc=(sx * 1.5, 0, 4.5), rot=(0, sx * -8, 0), name='leg')
    add(box(0.5, 9, 0.5, 0.03), T('wood_dark'), loc=(0, -3.5, 9.2), rot=(25, 0, 0), name='boom')
    add(C.bm_torus(2.2, 0.2, 24, 6), T('wood'), loc=(0, 1.2, 2.4), rot=(90, 0, 0), name='wheel')
    for k in range(8):
        add(box(0.15, 0.15, 4.3, 0.0), T('wood'), loc=(0, 1.2, 2.4), rot=(0, k * 22.5, 0), name='spoke')
    add(C.bm_tube([(0, -7.4, 11.0), (0, -7.4, 4.0)], 0.05, smooth=False, bevel_res=1), F('rope', (160, 130, 80)),
        uv='none', name='rope')
    add(box(1.4, 1.4, 1.2, 0.06), T('wood'), loc=(0, -7.4, 3.4), name='load')
