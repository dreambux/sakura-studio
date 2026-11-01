"""Architektura grecka: kolumny, swiatynie, mury, bramy, posagi, domy, wiatrak, latarnia."""
import math
import random

import bmesh
from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, fluted_column_bm, recalc, C)

MARBLE = lambda: T('marble', 0.45)  # noqa: E731
BLOCKS = lambda: T('blocks_marble', 0.7)  # noqa: E731
LIME = lambda: T('blocks', 0.8)  # noqa: E731


# ------------------------------------------------------------------ elementy
def column(loc, h=10.0, r=0.85, style='doric', mat=None, segs=40, broken=0.0, seed=0, name='col'):
    x, y, z = loc
    mat = mat or MARBLE()
    hh = h * (1 - broken) if broken else h
    if style == 'minoan':
        add(cyl(r * 0.75, h, 24, r2=r * 1.05), F('minoan_red', (150, 36, 30), 0.7), loc=(x, y, z + h / 2), uv='none',
            name=name + '_shaft')
        add(lathe([(0, 0), (r * 1.2, 0), (r * 1.45, 0.35), (r * 1.3, 0.7), (0, 0.7)], 24), F('minoan_black', (30, 26, 26)),
            loc=(x, y, z + h), uv='none', name=name + '_cap')
        add(box(r * 3.0, r * 3.0, 0.4), T('plaster_ochre'), loc=(x, y, z + h + 0.9), name=name + '_abacus')
        return
    if style == 'ionic':
        add(lathe([(0, 0), (r * 1.4, 0), (r * 1.4, 0.25), (r * 1.15, 0.45), (r * 1.25, 0.6), (r * 1.0, 0.8),
                   (0, 0.8)], segs), mat, loc=(x, y, z), uv='box', tile=3, name=name + '_base')
        z0 = z + 0.8
    else:
        z0 = z
    shaft_h = hh - (0.8 if style == 'ionic' else 0) - (0 if broken else 1.0)
    add(fluted_column_bm(r, shaft_h, 16, 0.86, segs, 6), mat, loc=(x, y, z0), uv='cyl', tile=3, name=name + '_shaft')
    if broken:
        rnd = random.Random(seed)
        add(rock_bm(r * 1.0, seed, 1, 0.5, 0.0, (1, 1, 0.45)), mat, loc=(x, y, z0 + shaft_h), uv='box', tile=3,
            smooth=False, name=name + '_break')
        return
    zt = z0 + shaft_h
    if style == 'ionic':
        add(box(r * 2.7, r * 1.3, 0.45, 0.1), mat, loc=(x, y, zt + 0.25), name=name + '_cap')
        for sx in (-1, 1):
            add(C.bm_torus(0.38, 0.14, 20, 8), mat, loc=(x + sx * r * 1.25, y, zt + 0.12), rot=(90, 0, 0),
                uv='box', name=name + '_volute')
        add(box(r * 2.7, r * 2.7, 0.35, 0.05), mat, loc=(x, y, zt + 0.7), name=name + '_abacus')
    else:
        add(lathe([(0, 0), (r * 0.9, 0), (r * 1.35, 0.45), (r * 1.4, 0.55), (0, 0.55)], segs), mat, loc=(x, y, zt),
            uv='box', tile=3, name=name + '_echinus')
        add(box(r * 3.0, r * 3.0, 0.45, 0.05), mat, loc=(x, y, zt + 0.78), name=name + '_abacus')


def steps(w, d, n=3, h=0.6, inset=1.0, mat=None, z=0.0, name='step'):
    mat = mat or BLOCKS()
    for i in range(n):
        add(box(w - i * inset * 2, d - i * inset * 2, h, 0.04), mat, loc=(0, 0, z + h * (i + 0.5)), uv='box', tile=4,
            name=f'{name}{i}')
    return z + h * n


def pediment(w, d, h, z, mat, roof=True, front_y=None):
    tri = C.bm_extrude([(-w / 2, 0), (w / 2, 0), (0, h)], d)
    C.bm_transform(tri, rot=(90, 0, 0))
    add(tri, mat, loc=(0, 0, z), uv='box', tile=4, name='pediment')
    if roof:
        L = math.hypot(w / 2, h) + 0.6
        ang = math.degrees(math.atan2(h, w / 2))
        for sx in (-1, 1):
            add(box(L, d + 1.0, 0.45, 0.05), T('roof'), loc=(sx * w / 4, 0, z + h / 2 + 0.25),
                rot=(0, sx * ang, 0), uv='box', tile=3, name='roof')
        add(box(0.6, d + 1.2, 0.6, 0.1), T('roof_dark'), loc=(0, 0, z + h + 0.15), name='ridge')
        for k, sy in enumerate((-1, 1)):
            for sx in (-1, 0, 1):
                p = (sx * w / 2 * 0.98, sy * (d / 2 + 0.3), z + (h if sx == 0 else 0.1) + 0.3)
                add(C.bm_extrude([(-0.4, 0), (0.4, 0), (0.25, 0.6), (0, 0.9), (-0.25, 0.6)], 0.15), GOLD(),
                    loc=p, rot=(90, 0, 0), uv='none', name='acroterion')


def frieze(w, d, z, mat, gold=True):
    add(box(w, d, 1.0, 0.04), mat, loc=(0, 0, z + 0.5), uv='box', tile=4, name='architrave')
    add(box(w + 0.2, d + 0.2, 1.1, 0.04), T('meander_white', 0.7) if not gold else T('meander_gold', 0.6),
        loc=(0, 0, z + 1.55), uv='box', tile=2.2, name='frieze')
    add(box(w + 0.6, d + 0.6, 0.4, 0.04), mat, loc=(0, 0, z + 2.3), uv='box', tile=4, name='cornice')
    return z + 2.5


def statue_fig(loc, s=1.0, mat=None, pose='spear', rotz=0, name='statue'):
    """Posag w stylu R6 (marmur/braz) na postumencie."""
    x, y, z = loc
    mat = mat or MARBLE()
    rz = rotz

    def P(dx, dy, dz):
        c, si = math.cos(math.radians(rz)), math.sin(math.radians(rz))
        return (x + (dx * c - dy * si) * s, y + (dx * si + dy * c) * s, z + dz * s)
    add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(-0.5, 0, 1.0), rot=(0, 0, rz), name=name + '_ll')
    add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(0.5, 0.2, 1.0), rot=(8, 0, rz), name=name + '_rl')
    add(box(2.0 * s, 1.0 * s, 2.0 * s, 0.12), mat, loc=P(0, 0, 3.0), rot=(0, 0, rz), name=name + '_t')
    add(box(2.1 * s, 1.1 * s, 1.4 * s, 0.12), mat, loc=P(0, 0, 1.8), rot=(0, 0, rz), name=name + '_tunic')
    add(cyl(0.6 * s, 1.2 * s, 24, bev=0.2 * s), mat, loc=P(0, 0, 4.6), rot=(0, 0, rz), name=name + '_h')
    if pose == 'spear':
        add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(-1.5, 0, 3.6), rot=(0, 160, rz), name=name + '_ra')
        add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(1.5, 0, 3.0), rot=(0, 0, rz), name=name + '_la')
        add(cyl(0.12 * s, 7 * s, 8), mat, loc=P(-1.6, 0, 4.4), rot=(0, 0, rz), name=name + '_spear')
        add(cyl(0.9 * s, 0.2 * s, 24), mat, loc=P(2.1, 0, 2.8), rot=(0, 90, rz), name=name + '_shield')
    elif pose == 'arms_up':
        for sx in (-1, 1):
            add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(sx * 1.7, 0, 4.4), rot=(0, sx * -150, rz),
                name=name + '_arm')
    else:
        for sx in (-1, 1):
            add(box(1.0 * s, 1.0 * s, 2.0 * s, 0.1), mat, loc=P(sx * 1.5, 0, 3.0), rot=(0, 0, rz), name=name + '_arm')
    add(C.bm_torus(0.62 * s, 0.1 * s, 20, 6), GOLD() if mat.name.startswith('T_marble') else mat,
        loc=P(0, 0, 5.1), rot=(0, 0, rz), name=name + '_laurel')


# ------------------------------------------------------------------ kolumny
prop('kolumna_dorycka', 'Architektura', 'Kolumna dorycka z zlobkowaniem (10 st.)')(
    lambda: (begin('kolumna_dorycka'), column((0, 0, 0), 10)))
prop('kolumna_jonska', 'Architektura', 'Kolumna jonska z wolutami')(
    lambda: (begin('kolumna_jonska'), column((0, 0, 0), 10, style='ionic')))
prop('kolumna_minojska', 'Architektura', 'Kolumna minojska (czerwona, zwezana w dol)')(
    lambda: (begin('kolumna_minojska'), column((0, 0, 0), 8, style='minoan')))
prop('kolumna_zlamana', 'Architektura', 'Zlamana kolumna (ruiny)')(
    lambda: (begin('kolumna_zlamana'), column((0, 0, 0), 10, broken=0.45, seed=3)))
prop('kolumna_zlamana_2', 'Architektura', 'Krotki kikut kolumny')(
    lambda: (begin('kolumna_zlamana_2'), column((0, 0, 0), 10, broken=0.75, seed=4)))


@prop('kolumna_przewrocona', 'Architektura', 'Przewrocona kolumna w kawalkach')
def fallen_column():
    begin('kolumna_przewrocona')
    rnd = random.Random(5)
    x = 0
    for k in range(4):
        L = rnd.uniform(1.8, 2.6)
        add(fluted_column_bm(0.85, L, 16, 1.0, 32, 2), MARBLE(), loc=(x, rnd.uniform(-0.3, 0.3), 0.85),
            rot=(0, 90, rnd.uniform(-12, 12)), uv='cyl', tile=3, name=f'drum{k}')
        x += L + rnd.uniform(0.1, 0.6)
    add(box(2.5, 2.5, 0.45, 0.05), MARBLE(), loc=(x + 1.0, 0.5, 0.25), rot=(0, 0, 20), name='abacus')
    for k in range(5):
        add(rock_bm(0.35, 50 + k, 1, 0.4), MARBLE(), loc=(rnd.uniform(-1, x + 2), rnd.uniform(-2, 2), 0.1),
            uv='box', smooth=False, name=f'chip{k}')


@prop('gruz_marmurowy', 'Architektura', 'Gruz: bloki i odlamki marmuru')
def rubble():
    begin('gruz_marmurowy')
    rnd = random.Random(6)
    for k in range(8):
        sx, sy, sz = rnd.uniform(1, 2.5), rnd.uniform(1, 2), rnd.uniform(0.6, 1.2)
        add(box(sx, sy, sz, 0.08), BLOCKS(), loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), sz / 2),
            rot=(rnd.uniform(-10, 10), rnd.uniform(-10, 10), rnd.uniform(0, 90)), name=f'b{k}')
    for k in range(10):
        add(rock_bm(0.4, 60 + k, 1, 0.4), MARBLE(), loc=(rnd.uniform(-4, 4), rnd.uniform(-4, 4), 0.1), uv='box',
            smooth=False, name=f'c{k}')


# ------------------------------------------------------------------ swiatynie
def temple(name, nx=6, ny=8, sp=5.0, h=10.0, style='doric', ruined=False, statue=True, seed=0, segs=32):
    begin(name)
    w, d = (nx - 1) * sp + 5, (ny - 1) * sp + 5
    z = steps(w + 3, d + 3, 3, 0.6, 0.7)
    add(box(w, d, 0.3, 0.02), T('paving_marble', 0.6), loc=(0, 0, z + 0.15), uv='box', tile=6, name='floor')
    z += 0.3
    rnd = random.Random(seed)
    k = 0
    for i in range(nx):
        for j in range(ny):
            if 0 < i < nx - 1 and 0 < j < ny - 1:
                continue
            x, y = -w / 2 + 2.5 + i * sp, -d / 2 + 2.5 + j * sp
            br = 0.0
            if ruined and rnd.random() < 0.45:
                br = rnd.uniform(0.3, 0.85)
            column((x, y, z), h, 0.85, style, segs=segs, broken=br, seed=seed * 50 + k, name=f'c{k}')
            k += 1
    # cella
    cw, cd = w - 2 * sp, d - 2 * sp
    if cw > 2 and cd > 2:
        wall_h = h * (0.45 if ruined else 1.0)
        for sx in (-1, 1):
            add(box(1.0, cd, wall_h, 0.05), LIME(), loc=(sx * cw / 2, 0, z + wall_h / 2), uv='box', tile=4,
                name='cellawall')
        add(box(cw, 1.0, wall_h, 0.05), LIME(), loc=(0, cd / 2, z + wall_h / 2), uv='box', tile=4, name='cellaback')
        for sx in (-1, 1):
            add(box(cw / 2 - 2, 1.0, wall_h, 0.05), LIME(), loc=(sx * (cw / 4 + 1), -cd / 2, z + wall_h / 2), uv='box',
                tile=4, name='cellafront')
        if statue:
            add(box(3, 3, 1.6, 0.1), BLOCKS(), loc=(0, cd / 2 - 3, z + 0.8), name='pedestal')
            statue_fig((0, cd / 2 - 3, z + 1.6), 1.25, GOLD() if not ruined else MARBLE(), 'spear', 180)
    if not ruined:
        zt = frieze(w, d, z + h, MARBLE())
        pediment(w + 0.6, d + 0.6, 3.2, zt, MARBLE())
    else:
        add(box(sp * 2.2, 1.6, 1.0, 0.04), MARBLE(), loc=(-w / 2 + 2.5 + sp, -d / 2 + 2.5, z + h + 0.5),
            name='architrave_piece')
    for sx in (-1, 1):
        add(cyl(0.9, 1.6, 16), BRONZE(), loc=(sx * (w / 2 + 1.0), -d / 2 - 2.0, 0.8), uv='cyl', name='brazier')
        add(lathe([(0, 0), (1.0, 0.2), (1.2, 0.7), (0.9, 0.7), (0, 0.4)], 24), BRONZE(),
            loc=(sx * (w / 2 + 1.0), -d / 2 - 2.0, 1.6), uv='box', name='brazierbowl')
        add(cyl(0.6, 1.2, 8, r2=0.0), FIRE(), loc=(sx * (w / 2 + 1.0), -d / 2 - 2.0, 2.6), uv='none', name='flame')
        marker('Fire', (sx * (w / 2 + 1.0), -d / 2 - 2.0, 2.5), size=4, heat=8)


prop('swiatynia_dorycka', 'Architektura', 'Swiatynia dorycka (baza / centrum mapy)')(
    lambda: temple('swiatynia_dorycka', 6, 8, 5.0, 10.0, 'doric'))
prop('swiatynia_jonska', 'Architektura', 'Mala swiatynia jonska')(
    lambda: temple('swiatynia_jonska', 4, 5, 5.0, 9.0, 'ionic', seed=2, segs=20))
prop('swiatynia_ruiny', 'Architektura', 'Ruiny swiatyni (kolumny zlamane)')(
    lambda: temple('swiatynia_ruiny', 6, 7, 5.0, 10.0, 'doric', ruined=True, statue=True, seed=3))


@prop('tholos', 'Architektura', 'Tholos - okragla swiatynia (Delfy)')
def tholos():
    begin('tholos')
    z = 0
    for i in range(3):
        add(cyl(9.0 - i * 0.8, 0.6, 48), BLOCKS(), loc=(0, 0, 0.3 + i * 0.6), uv='box', tile=4, name=f'step{i}')
    z = 1.8
    for k in range(12):
        a = 2 * math.pi * k / 12
        column((math.cos(a) * 6.5, math.sin(a) * 6.5, z), 8.0, 0.65, 'doric', segs=28, name=f'c{k}')
    add(cyl(4.6, 8.0, 40), LIME(), loc=(0, 0, z + 4.0), uv='cyl', tile=4, name='cella')
    add(cyl(7.6, 1.0, 48), MARBLE(), loc=(0, 0, z + 9.0), uv='cyl', tile=3, name='ring')
    add(cyl(7.7, 1.0, 48), T('meander_gold', 0.6), loc=(0, 0, z + 10.0), uv='cyl', tile=2.2, name='frieze')
    add(cyl(7.9, 4.0, 48, r2=0.8), T('roof'), loc=(0, 0, z + 12.5), uv='cyl', tile=3, name='roof')
    add(C.bm_sphere(0.8, 16, 8), GOLD(), loc=(0, 0, z + 14.7), name='finial')


# ------------------------------------------------------------------ mury, schody, bramy, mosty
@prop('mur', 'Architektura', 'Mur z ciosow (8 st.)')
def wall(name='mur', ruined=False, mat='blocks', seed=7):
    begin(name)
    rnd = random.Random(seed)
    for row in range(4):
        x = -4 + (0.0 if row % 2 == 0 else -1.0)
        while x < 4:
            L = rnd.uniform(1.6, 2.4)
            L = min(L, 4 - x)
            if L > 0.3 and not (ruined and row >= 2 and rnd.random() < 0.55):
                add(box(L - 0.06, 1.4, 0.9, 0.08), T(mat), loc=(x + L / 2, 0, 0.45 + row * 0.92),
                    rot=(0, 0, rnd.uniform(-1, 1)), tile=3, name=f'b{row}')
            x += L
    if not ruined:
        add(box(8.2, 1.6, 0.3, 0.05), T(mat), loc=(0, 0, 3.85), name='cap')
    else:
        for k in range(4):
            add(box(1.6, 1.3, 0.8, 0.08), T(mat), loc=(rnd.uniform(-4, 4), rnd.uniform(-2.5, 2.5), 0.4),
                rot=(rnd.uniform(-15, 15), rnd.uniform(-15, 15), rnd.uniform(0, 90)), name=f'fall{k}')


prop('mur_zniszczony', 'Architektura', 'Zniszczony mur z lezacymi blokami')(lambda: wall('mur_zniszczony', True, seed=8))
prop('mur_szary', 'Architektura', 'Mur z szarego kamienia z mchem')(lambda: wall('mur_szary', False, 'blocks_grey', 9))


@prop('schody', 'Architektura', 'Szerokie kamienne schody (6 st. wys.)')
def stairs():
    begin('schody')
    for i in range(8):
        add(box(10, 1.6, 0.75, 0.04), BLOCKS(), loc=(0, i * 1.5, 0.375 + i * 0.75), uv='box', tile=4, name=f's{i}')
    for sx in (-1, 1):
        add(box(1.4, 12.5, 6.4, 0.06), LIME(), loc=(sx * 5.6, 5.3, 3.0), rot=(0, 0, 0), name='side')


@prop('brama_luk', 'Architektura', 'Kamienny luk / brama miejska')
def arch_gate(name='brama_luk', portal=None):
    begin(name)
    for sx in (-1, 1):
        add(box(3, 3, 10, 0.08), T('blocks'), loc=(sx * 6, 0, 5), uv='box', tile=4, name='pier')
        add(box(3.6, 3.6, 0.8, 0.06), MARBLE(), loc=(sx * 6, 0, 0.4), name='plinth')
        add(box(3.6, 3.6, 0.6, 0.06), MARBLE(), loc=(sx * 6, 0, 10.3), name='impost')
    pts = []
    for i in range(13):
        a = math.pi * i / 12
        pts.append((-math.cos(a) * 6, 0, 10.6 + math.sin(a) * 4.2))
    add(tube(pts, 1.5, res=12), T('blocks'), uv='box', tile=4, name='arch')
    add(box(16, 3.4, 1.4, 0.06), MARBLE(), loc=(0, 0, 15.6), name='attic')
    add(box(16.4, 3.6, 1.0, 0.06), T('meander_gold', 0.6), loc=(0, 0, 16.8), uv='box', tile=2.2, name='frieze')
    add(C.bm_extrude([(-1.5, 0), (1.5, 0), (0, 1.8)], 0.4), GOLD(), loc=(0, -1.8, 13.8), rot=(90, 0, 0),
        uv='none', name='keystone')
    if portal:
        add(box(9, 0.3, 10.5, 0.0), GLOW('portal_' + str(portal), portal, 4.0), loc=(0, 0, 5.4), uv='none',
            name='portal')
        marker('Portal', (0, 0, 5.4), color=list(portal))


prop('brama_portal_zielony', 'Architektura', 'Brama spawnu z zielonym portalem')(
    lambda: arch_gate('brama_portal_zielony', (60, 255, 120)))
prop('brama_portal_czerwony', 'Architektura', 'Brama spawnu z czerwonym portalem')(
    lambda: arch_gate('brama_portal_czerwony', (255, 60, 50)))


@prop('most_kamienny', 'Architektura', 'Kamienny most lukowy (12 st.)')
def bridge():
    begin('most_kamienny')
    add(box(9, 16, 1.2, 0.06), T('paving'), loc=(0, 0, 4.6), uv='box', tile=6, name='deck')
    for sx in (-1, 1):
        add(box(0.8, 16, 1.2, 0.06), T('blocks'), loc=(sx * 4.2, 0, 5.8), name='parapet')
        for y in (-8, 8):
            add(box(1.6, 1.6, 2.4, 0.06), T('blocks'), loc=(sx * 4.2, y, 6.4), name='post')
    pts = [(0, -8, 0), (0, -6, 3.0), (0, 0, 4.2), (0, 6, 3.0), (0, 8, 0)]
    for sx in (-3.2, 0, 3.2):
        add(tube([(sx, p[1], p[2]) for p in pts], 1.4, res=8), T('blocks'), uv='box', tile=4, name='arch')
    for y in (-8.5, 8.5):
        add(box(9, 3, 4.6, 0.06), T('blocks'), loc=(0, y, 2.3), name='abut')


@prop('studnia', 'Architektura', 'Studnia z daszkiem')
def well():
    begin('studnia')
    add(cyl(1.8, 2.0, 24, bev=0.1), T('blocks_grey'), loc=(0, 0, 1.0), uv='cyl', tile=3, name='ring')
    add(cyl(1.4, 0.1, 24), F('well_water', (30, 60, 80), 0.1), loc=(0, 0, 1.6), uv='none', name='water')
    for sx in (-1, 1):
        add(box(0.35, 0.35, 4.5, 0.04), T('wood'), loc=(sx * 1.6, 0, 2.25), name='post')
    add(cyl(0.25, 3.4, 10), T('wood'), loc=(0, 0, 3.6), rot=(0, 90, 0), uv='cyl', name='axle')
    add(cyl(0.02, 2.0, 4), F('rope', (160, 130, 80)), loc=(0, 0, 2.6), uv='none', name='rope')
    add(cyl(0.3, 0.5, 12), T('wood'), loc=(0, 0, 1.8), uv='cyl', name='bucket')
    for sx in (-1, 1):
        add(box(2.3, 4.6, 0.25, 0.04), T('roof'), loc=(sx * 1.0, 0, 5.0), rot=(0, sx * 30, 0), tile=3, name='roof')


@prop('fontanna', 'Architektura', 'Fontanna z delfinem (marmur)')
def fountain():
    begin('fontanna')
    add(lathe([(0, 0), (4.2, 0), (4.3, 1.0), (3.9, 1.0), (3.9, 0.3), (0, 0.3)], 40), MARBLE(), uv='box', tile=3,
        name='basin')
    add(cyl(3.85, 0.1, 40), F('fountain_water', (60, 140, 170), 0.05), loc=(0, 0, 0.8), uv='none', name='water')
    add(cyl(0.6, 3.0, 20), MARBLE(), loc=(0, 0, 1.5), uv='cyl', name='pillar')
    add(lathe([(0, 0), (1.8, 0.1), (2.0, 0.5), (0, 0.3)], 32), MARBLE(), loc=(0, 0, 3.0), uv='box', name='bowl')
    pts = [(0, 0, 3.4), (0.4, 0, 4.4), (0.2, 0, 5.2), (-0.5, 0, 5.4), (-0.9, 0, 4.8)]
    add(tube(pts, 0.45, radii=[1, 1, 0.9, 0.6, 0.3], res=6), BRONZE(), uv='box', name='dolphin')
    marker('Water', (0, 0, 5.0))


@prop('oltarz', 'Architektura', 'Oltarz ofiarny z ogniem')
def altar():
    begin('oltarz')
    add(box(4, 2.5, 0.5, 0.04), BLOCKS(), loc=(0, 0, 0.25), name='base')
    add(box(3.4, 2.0, 1.8, 0.06), MARBLE(), loc=(0, 0, 1.4), uv='box', tile=3, name='body')
    add(box(3.6, 2.2, 0.15, 0.02), T('meander_gold', 0.6), loc=(0, 0, 2.0), uv='box', tile=2.2, name='band')
    for sx in (-1, 1):
        add(cyl(0.3, 2.2, 16), MARBLE(), loc=(sx * 1.8, 0, 2.4), rot=(90, 0, 0), uv='cyl', name='scroll')
    add(cyl(0.7, 1.0, 8, r2=0.0), FIRE(), loc=(0, 0, 2.9), uv='none', name='flame')
    marker('Fire', (0, 0, 2.7), size=3, heat=6)


@prop('postument', 'Architektura', 'Pusty postument (pod posag/jednostke)')
def pedestal():
    begin('postument')
    add(box(3.2, 3.2, 0.5, 0.05), BLOCKS(), loc=(0, 0, 0.25), name='base')
    add(box(2.6, 2.6, 2.4, 0.08), MARBLE(), loc=(0, 0, 1.7), uv='box', tile=3, name='body')
    add(box(3.0, 3.0, 0.4, 0.05), MARBLE(), loc=(0, 0, 3.1), name='top')


@prop('posag_wojownika', 'Architektura', 'Marmurowy posag hoplity z wlocznia')
def statue_warrior():
    begin('posag_wojownika')
    add(box(3.4, 3.4, 2.4, 0.08), BLOCKS(), loc=(0, 0, 1.2), name='ped')
    statue_fig((0, 0, 2.4), 1.0, MARBLE(), 'spear')


@prop('posag_zloty', 'Architektura', 'Zloty posag bohatera (Olimp)')
def statue_gold():
    begin('posag_zloty')
    add(box(3.4, 3.4, 2.4, 0.08), MARBLE(), loc=(0, 0, 1.2), name='ped')
    statue_fig((0, 0, 2.4), 1.0, GOLD(), 'arms_up')


@prop('posag_bogini', 'Architektura', 'Posag bogini (Atena) w spokojnej pozie')
def statue_goddess():
    begin('posag_bogini')
    add(box(3.4, 3.4, 2.4, 0.08), BLOCKS(), loc=(0, 0, 1.2), name='ped')
    statue_fig((0, 0, 2.4), 1.1, MARBLE(), 'still')
    add(cyl(1.4, 4.2, 24, r2=1.1), MARBLE(), loc=(0, 0, 4.4), uv='cyl', name='robe')


@prop('popiersie', 'Architektura', 'Popiersie filozofa na kolumnie')
def bust():
    begin('popiersie')
    add(cyl(0.6, 3.5, 20), MARBLE(), loc=(0, 0, 1.75), uv='cyl', name='pillar')
    add(box(1.6, 1.6, 0.3, 0.04), MARBLE(), loc=(0, 0, 3.6), name='cap')
    add(box(1.6, 0.9, 0.9, 0.2), MARBLE(), loc=(0, 0, 4.2), name='shoulders')
    add(cyl(0.5, 1.0, 20, bev=0.15), MARBLE(), loc=(0, 0, 5.1), name='head')
    add(box(0.8, 0.4, 0.6, 0.2), MARBLE(), loc=(0, -0.35, 4.8), name='beard')


@prop('herma', 'Architektura', 'Herma (filar z glowa Hermesa)')
def herm():
    begin('herma')
    add(box(1.0, 1.0, 4.0, 0.05), MARBLE(), loc=(0, 0, 2.0), uv='box', tile=3, name='pillar')
    add(cyl(0.55, 1.0, 20, bev=0.15), MARBLE(), loc=(0, 0, 4.5), name='head')
    add(box(0.7, 0.35, 0.6, 0.15), MARBLE(), loc=(0, -0.4, 4.2), name='beard')
    add(C.bm_torus(0.56, 0.08, 20, 6), GOLD(), loc=(0, 0, 4.9), name='laurel')


@prop('stela_nagrobna', 'Architektura', 'Stela nagrobna (cmentarz, nieumarli)')
def stele():
    begin('stela_nagrobna')
    add(box(1.8, 0.5, 3.2, 0.05), MARBLE(), loc=(0, 0, 1.6), rot=(4, 0, 3), uv='box', tile=3, name='slab')
    add(C.bm_extrude([(-1.0, 0), (1.0, 0), (0, 0.6)], 0.55), MARBLE(), loc=(0.05, 0, 3.25), rot=(94, 0, 3),
        uv='box', name='top')
    add(box(2.4, 1.2, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='base')


@prop('sarkofag', 'Architektura', 'Kamienny sarkofag (uchylony)')
def sarcophagus():
    begin('sarkofag')
    add(box(5, 2.4, 2.0, 0.08), T('blocks_grey'), loc=(0, 0, 1.0), uv='box', tile=3, name='box')
    add(box(5.2, 2.6, 0.5, 0.08), T('blocks_grey'), loc=(0.6, 0.4, 2.3), rot=(0, 0, 8), name='lid')
    add(box(5.0, 0.1, 0.4, 0.02), T('meander_white', 0.7), loc=(0, -1.22, 1.5), uv='box', tile=1.5, name='band')
    add(box(4.6, 2.0, 0.1, 0.0), F('void', (10, 10, 12)), loc=(0, 0, 1.96), name='dark')


@prop('dom_grecki', 'Architektura', 'Bielony dom z dachem z dachowek')
def house(name='dom_grecki', w=10, d=8, h=6, two=False, wall='plaster', door=(40, 80, 150)):
    begin(name)
    add(box(w, d, h, 0.1), T(wall, 0.85), loc=(0, 0, h / 2), uv='box', tile=4, name='walls')
    add(box(w + 0.4, d + 0.4, 0.6, 0.06), LIME(), loc=(0, 0, 0.3), name='plinth')
    if two:
        add(box(w * 0.6, d * 0.8, h * 0.7, 0.1), T(wall, 0.85), loc=(w * 0.15, d * 0.05, h + h * 0.35), uv='box',
            tile=4, name='upper')
        add(box(w * 0.4 + 0.2, 2.2, 0.3, 0.04), T('wood'), loc=(-w * 0.15 - 0.2, -d / 2 - 0.9, h + 0.15),
            name='balcony')
        for k in range(6):
            add(box(0.12, 0.12, 1.0, 0.0), T('wood'), loc=(-w * 0.35 + k * 0.8 * w / 10, -d / 2 - 1.9, h + 0.8),
                name='rail')
    top = h * (1.7 if two else 1.0)
    rw = (w * 0.6 if two else w) + 1.0
    cx = (w * 0.15 if two else 0)
    for sx in (-1, 1):
        add(box(rw / 2 + 0.6, d + 1.2, 0.35, 0.04), T('roof'), loc=(cx + sx * rw / 4, 0, top + 0.8),
            rot=(0, sx * 18, 0), uv='box', tile=3, name='roof')
    add(box(w * 0.15, 0.25, 3.2, 0.03), F('door' + str(door), door, 0.6), loc=(-w * 0.2, -d / 2 - 0.05, 1.9),
        name='door')
    add(box(w * 0.15 + 0.5, 0.35, 0.3, 0.03), LIME(), loc=(-w * 0.2, -d / 2 - 0.1, 3.6), name='lintel')
    for k, x in enumerate((w * 0.15, w * 0.35)):
        add(box(1.2, 0.2, 1.4, 0.03), F('window', (30, 30, 36), 0.4), loc=(x, -d / 2 - 0.02, 3.6), name='win')
        add(box(0.6, 0.15, 1.5, 0.03), F('shutter' + str(door), door, 0.6), loc=(x - 0.95, -d / 2 - 0.1, 3.6),
            name='shut')
        add(box(0.6, 0.15, 1.5, 0.03), F('shutter' + str(door), door, 0.6), loc=(x + 0.95, -d / 2 - 0.1, 3.6),
            name='shut')
    add(cyl(0.45, 0.8, 12, r2=0.55), T('terracotta'), loc=(w * 0.2, -d / 2 - 1.0, 0.4), uv='cyl', name='pot')
    add(blob_bm(0.6, 3, 1, 0.3), T('leaf_lush'), loc=(w * 0.2, -d / 2 - 1.0, 1.1), name='plant')


prop('dom_grecki_pietrowy', 'Architektura', 'Pietrowy dom z balkonem')(
    lambda: house('dom_grecki_pietrowy', 12, 9, 6, True, door=(150, 60, 40)))
prop('dom_ochra', 'Architektura', 'Dom w kolorze ochry')(
    lambda: house('dom_ochra', 9, 8, 5.5, False, 'plaster_ochre', (60, 90, 60)))


@prop('dom_cykladzki', 'Architektura', 'Bialy dom z niebieska kopula (wyspy)')
def cycladic():
    begin('dom_cykladzki')
    add(box(10, 10, 7, 0.15), T('plaster', 0.85), loc=(0, 0, 3.5), uv='box', tile=4, name='walls')
    add(lathe([(0, 0), (3.6, 0)] + [(3.6 * math.cos(a * math.pi / 16), 3.6 * math.sin(a * math.pi / 16)) for a in
                                    range(1, 9)], 32), T('plaster_blue', 0.6), loc=(0, 0, 7.0), uv='box', tile=3,
        name='dome')
    add(cyl(0.12, 1.6, 8), GOLD(), loc=(0, 0, 11.2), uv='none', name='cross')
    add(box(1.6, 0.3, 3.4, 0.05), F('door_blue', (40, 80, 150)), loc=(0, -5.05, 1.7), name='door')
    for x in (-3, 3):
        add(box(1.2, 0.3, 1.6, 0.05), F('door_blue', (40, 80, 150)), loc=(x, -5.05, 4.2), name='win')
    for k in range(5):
        add(box(2.0, 1.2, 0.5, 0.04), T('plaster', 0.85), loc=(5.6, -4 + k * 1.2, 0.25 + k * 0.5), name='stair')


@prop('wiatrak', 'Architektura', 'Grecki wiatrak (Mykonos)')
def windmill():
    begin('wiatrak')
    add(cyl(3.0, 10, 32, r2=2.6), T('plaster', 0.85), loc=(0, 0, 5), uv='cyl', tile=4, name='tower')
    add(cyl(2.9, 2.6, 32, r2=0.6), T('roof_dark'), loc=(0, 0, 11.3), uv='cyl', tile=3, name='cap')
    add(cyl(0.25, 2.0, 10), T('wood_dark'), loc=(0, -3.2, 9.6), rot=(90, 0, 0), uv='cyl', name='axle')
    for k in range(8):
        a = k * 45
        add(box(0.18, 0.18, 7.5, 0.0), T('wood'), loc=(0, -4.2, 9.6), rot=(0, a, 0), name='spar')
        add(C.bm_extrude([(0, 0.6), (1.4, 1.2), (1.4, 6.8), (0, 7.4)], 0.04), T('cloth', 0.9),
            loc=(0, -4.2, 9.6), rot=(90, 0, 0), uv='box', tile=3, name='sail') if False else None
        bm = C.bm_extrude([(0.1, 0.8), (1.5, 1.4), (1.3, 7.0), (0.1, 7.2)], 0.04)
        C.bm_transform(bm, rot=(-90, 0, 0))
        C.bm_transform(bm, rot=(0, a, 0))
        add(bm, T('cloth', 0.9), loc=(0, -4.25, 9.6), uv='box', tile=3, name='sail')
    add(box(1.4, 0.3, 2.8, 0.04), T('wood'), loc=(0, -2.75, 1.4), rot=(0, 0, 0), name='door')


@prop('latarnia_morska', 'Architektura', 'Latarnia morska (faros) z ogniem')
def lighthouse():
    begin('latarnia_morska')
    add(box(12, 12, 8, 0.15), T('blocks'), loc=(0, 0, 4), uv='box', tile=4, name='base')
    add(box(9, 9, 10, 0.15), T('blocks_marble'), loc=(0, 0, 13), uv='box', tile=4, name='mid')
    add(cyl(3.5, 8, 8), T('blocks'), loc=(0, 0, 22), uv='box', tile=4, name='octagon')
    add(cyl(3.0, 4, 16), MARBLE(), loc=(0, 0, 28), uv='cyl', name='lantern_base')
    for k in range(8):
        a = 2 * math.pi * k / 8
        add(cyl(0.25, 4, 8), MARBLE(), loc=(math.cos(a) * 2.6, math.sin(a) * 2.6, 32), uv='none', name='post')
    add(cyl(3.2, 0.8, 16), MARBLE(), loc=(0, 0, 34.4), uv='none', name='roof')
    add(C.bm_sphere(1.6, 16, 8), FIRE_CORE(), loc=(0, 0, 31.5), uv='none', name='fire')
    add(cyl(0.3, 3.0, 8), GOLD(), loc=(0, 0, 36.0), name='spire')
    statue_fig((0, 0, 35), 0.6, BRONZE(), 'spear')
    marker('Light', (0, 0, 31.5), range=60, brightness=4, color=[255, 190, 110])
    marker('Fire', (0, 0, 31.5), size=8, heat=10)
    for sx in (-1, 1):
        add(box(0.6, 12.2, 0.6, 0.04), MARBLE(), loc=(sx * 6.1, 0, 8.3), name='cornice')


@prop('wieza_straznicza', 'Architektura', 'Kamienna wieza straznicza z blankami')
def watchtower():
    begin('wieza_straznicza')
    add(cyl(4.0, 14, 24, r2=3.6), T('blocks_grey'), loc=(0, 0, 7), uv='cyl', tile=4, name='tower')
    add(cyl(4.3, 1.0, 24), T('blocks_grey'), loc=(0, 0, 14.5), uv='cyl', tile=4, name='ring')
    for k in range(10):
        a = 2 * math.pi * k / 10
        add(box(1.4, 1.0, 1.4, 0.05), T('blocks_grey'), loc=(math.cos(a) * 3.9, math.sin(a) * 3.9, 15.7),
            rot=(0, 0, math.degrees(a)), name='merlon')
    add(box(0.15, 0.15, 5, 0.0), T('wood'), loc=(0, 0, 17.5), name='pole')
    add(box(2.6, 0.08, 1.6, 0.0), T('cloth_red', 0.9), loc=(1.3, 0, 19.0), uv='box', tile=2, name='flag')
    add(box(1.6, 0.3, 3.0, 0.04), T('wood_dark'), loc=(0, -3.9, 1.5), name='door')


@prop('koksownik', 'Architektura', 'Koksownik (trojnog z ogniem)')
def brazier():
    begin('koksownik')
    for k in range(3):
        a = 2 * math.pi * k / 3
        add(tube([(math.cos(a) * 0.9, math.sin(a) * 0.9, 0), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1.6),
                  (math.cos(a) * 0.7, math.sin(a) * 0.7, 2.6)], 0.09), BRONZE(), uv='box', name='leg')
    add(lathe([(0, 0), (0.5, 0), (1.0, 0.3), (1.15, 0.65), (0.95, 0.65), (0, 0.35)], 24), BRONZE(),
        loc=(0, 0, 2.5), uv='box', name='bowl')
    add(cyl(0.6, 1.1, 8, r2=0.0), FIRE(), loc=(0, 0, 3.6), uv='none', name='flame')
    add(cyl(0.3, 0.7, 8, r2=0.0), FIRE_CORE(), loc=(0, 0, 3.3), uv='none', name='core')
    marker('Fire', (0, 0, 3.4), size=3, heat=6)
    marker('Light', (0, 0, 3.8), range=18, brightness=2, color=[255, 160, 80])


@prop('pochodnia', 'Architektura', 'Pochodnia na slupie')
def torch():
    begin('pochodnia')
    add(cyl(0.18, 4.0, 8), T('wood_dark'), loc=(0, 0, 2.0), uv='cyl', name='pole')
    add(cyl(0.3, 0.6, 10, r2=0.4), BRONZE(), loc=(0, 0, 4.2), uv='cyl', name='cup')
    add(cyl(0.35, 0.9, 8, r2=0.0), FIRE(), loc=(0, 0, 4.9), uv='none', name='flame')
    marker('Fire', (0, 0, 4.7), size=1.5, heat=4)
    marker('Light', (0, 0, 5.0), range=12, brightness=1.5, color=[255, 160, 80])


@prop('tron', 'Architektura', 'Tron z gryfami (Knossos / Olimp)')
def throne():
    begin('tron')
    add(box(3, 3, 0.6, 0.05), MARBLE(), loc=(0, 0, 0.3), name='dais')
    add(box(2.0, 1.8, 1.4, 0.06), T('plaster_red'), loc=(0, 0, 1.3), name='seat')
    bm = C.bm_extrude([(-1.0, 0), (1.0, 0), (1.0, 2.4), (0.6, 3.2), (0, 3.6), (-0.6, 3.2), (-1.0, 2.4)], 0.4, 0.06, 2)
    C.bm_transform(bm, rot=(90, 0, 0))
    add(bm, T('plaster_red'), loc=(0, 0.75, 2.0), uv='box', tile=2, name='back')
    add(box(2.2, 2.0, 0.15, 0.02), GOLD(), loc=(0, 0, 2.05), name='trim')
    for sx in (-1, 1):
        add(box(0.4, 1.8, 0.9, 0.05), GOLD(), loc=(sx * 1.1, 0, 2.3), name='arm')
