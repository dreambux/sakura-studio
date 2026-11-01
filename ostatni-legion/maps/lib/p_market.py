"""Targ, oboz i drobiazgi: stragany, skrzynie, amfory, beczki, worki, kosze, wozy, bron, namioty."""
import math
import random

from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, C)


def amphora_bm(h=2.0, kind=0):
    if kind == 0:   # klasyczna amfora z nozka
        prof = [(0, 0), (0.12, 0), (0.18, 0.1), (0.3, 0.35), (0.55, 0.9), (0.6, 1.25), (0.45, 1.55), (0.2, 1.75),
                (0.18, 1.95), (0.25, 2.0), (0.22, 2.05), (0, 2.05)]
    elif kind == 1:  # pithos (duzy dzban)
        prof = [(0, 0), (0.6, 0), (0.95, 0.5), (1.1, 1.2), (1.0, 1.9), (0.7, 2.2), (0.75, 2.35), (0, 2.35)]
    else:            # hydria / dzbanek
        prof = [(0, 0), (0.35, 0), (0.5, 0.4), (0.62, 0.9), (0.5, 1.3), (0.28, 1.5), (0.34, 1.65), (0, 1.65)]
    s = h / prof[-1][1]
    return lathe([(r * s, z * s) for r, z in prof], 28)


def amphora(loc, h=2.0, kind=0, mat='terracotta_painted', rot=(0, 0, 0), name='amph'):
    add(amphora_bm(h, kind), T(mat, 0.6), loc=loc, rot=rot, uv='cyl', tile=h * 1.6, name=name)
    if kind == 0:
        x, y, z = loc
        for sx in (-1, 1):
            add(C.bm_tube([(x + sx * 0.18 * h / 2, y, z + 1.85 * h / 2.05), (x + sx * 0.5 * h / 2, y, z + 1.75 * h / 2.05),
                           (x + sx * 0.45 * h / 2, y, z + 1.4 * h / 2.05)], 0.05 * h / 2, smooth=True), T(mat, 0.6),
                uv='none', name=name + '_handle')


@prop('amfora', 'Targ', 'Amfora malowana (czarny pas)')
def p_amphora():
    begin('amfora')
    amphora((0, 0, 0), 2.2)


@prop('amfory_grupa', 'Targ', 'Grupa amfor i dzbanow')
def amphora_group():
    begin('amfory_grupa')
    amphora((0, 0, 0), 2.2, 0)
    amphora((1.3, 0.4, 0), 1.8, 0, 'terracotta')
    amphora((-1.2, 0.6, 0), 2.6, 1, 'terracotta')
    amphora((0.6, -1.1, 0), 1.3, 2, 'terracotta_painted')
    amphora((-0.6, -1.0, 0.45), 1.8, 0, 'terracotta', rot=(0, 75, 30))


@prop('pithos', 'Targ', 'Wielki pithos na oliwe/zboze')
def pithos():
    begin('pithos')
    amphora((0, 0, 0), 3.4, 1, 'terracotta')
    for z in (1.2, 2.1):
        add(C.bm_torus(1.08 if z < 2 else 0.95, 0.06, 24, 6), T('terracotta', 0.6), loc=(0, 0, z), name='rope_band')


@prop('amfory_stojak', 'Targ', 'Drewniany stojak z amforami (port)')
def amphora_rack():
    begin('amfory_stojak')
    for x in (-2.4, 0, 2.4):
        add(box(0.3, 1.8, 2.4, 0.02), T('wood'), loc=(x, 0, 1.2), name='side')
    add(box(5.2, 1.8, 0.2, 0.02), T('wood'), loc=(0, 0, 1.3), name='shelf')
    for k in range(4):
        amphora((-1.8 + k * 1.2, 0, 1.4), 1.6, 0, 'terracotta' if k % 2 else 'terracotta_painted')
    for k in range(3):
        amphora((-1.4 + k * 1.4, 0, -0.1 + 0.6), 1.6, 0, 'terracotta', rot=(90, 0, 0))


@prop('skrzynia', 'Targ', 'Drewniana skrzynia')
def crate(name='skrzynia', s=1.6):
    begin(name)
    add(box(s, s, s, 0.05), T('wood'), loc=(0, 0, s / 2), tile=2, name='box')
    for sx in (-1, 1):
        add(box(s + 0.08, 0.15, 0.2, 0.02), T('wood_dark'), loc=(0, sx * (s / 2), s - 0.2), name='band')
        add(box(s + 0.08, 0.15, 0.2, 0.02), T('wood_dark'), loc=(0, sx * (s / 2), 0.2), name='band')


@prop('skrzynie_stos', 'Targ', 'Stos skrzyn')
def crates():
    begin('skrzynie_stos')
    rnd = random.Random(2)
    for p, s in (((0, 0, 0), 1.8), ((1.9, 0.2, 0), 1.6), ((0.9, 0.1, 1.8), 1.5), ((-1.6, 0.6, 0), 1.4)):
        add(box(s, s, s, 0.05), T('wood'), loc=(p[0], p[1], p[2] + s / 2), rot=(0, 0, rnd.uniform(-12, 12)), tile=2,
            name='box')


@prop('beczka', 'Targ', 'Beczka z obreczami')
def barrel(name='beczka'):
    begin(name)
    add(lathe([(0, 0), (0.7, 0), (0.85, 0.9), (0.7, 1.8), (0, 1.8)], 20), T('wood_dark'), uv='cyl', tile=2,
        name='body')
    for z in (0.35, 1.45):
        add(C.bm_torus(0.8, 0.05, 20, 5), F('iron', (60, 58, 56), 0.5, 0.8), loc=(0, 0, z), name='hoop')


@prop('beczki', 'Targ', 'Grupa beczek')
def barrels():
    begin('beczki')
    for k, (x, y, rz) in enumerate(((0, 0, 0), (1.7, 0.3, 0), (0.8, 1.4, 0))):
        add(lathe([(0, 0), (0.7, 0), (0.85, 0.9), (0.7, 1.8), (0, 1.8)], 20), T('wood_dark'), loc=(x, y, 0),
            uv='cyl', tile=2, name='body')
    add(lathe([(0, 0), (0.7, 0), (0.85, 0.9), (0.7, 1.8), (0, 1.8)], 20), T('wood_dark'), loc=(-1.0, -1.4, 0.8),
        rot=(90, 0, 30), uv='cyl', tile=2, name='lying')


@prop('worki', 'Targ', 'Worki ze zbozem')
def sacks():
    begin('worki')
    rnd = random.Random(4)
    for k in range(5):
        add(blob_bm(0.75, 70 + k, 2, 0.12, (0.9, 0.7, 0.75)), T('cloth', 0.95),
            loc=(rnd.uniform(-1.2, 1.2), rnd.uniform(-0.8, 0.8), 0.5 + (0.8 if k == 4 else 0)), rot=(0, 0, rnd.uniform(0, 90)),
            uv='box', tile=2, name='sack')


@prop('kosz_owocow', 'Targ', 'Wiklinowy kosz z owocami (oliwki, winogrona, granaty)')
def fruit_basket():
    begin('kosz_owocow')
    add(lathe([(0, 0), (0.7, 0), (0.95, 0.6), (0.9, 0.62), (0, 0.1)], 20), T('wood_ship'), uv='cyl', tile=1,
        name='basket')
    rnd = random.Random(5)
    cols = [(150, 30, 40), (90, 110, 40), (80, 40, 110), (230, 160, 40)]
    for k in range(14):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 0.6)
        add(C.bm_sphere(0.17, 8, 6), F('fruit' + str(k % 4), cols[k % 4], 0.4),
            loc=(math.cos(a) * r, math.sin(a) * r, 0.6 + rnd.uniform(0, 0.15)), name='fruit')


@prop('stragan', 'Targ', 'Stragan z pasiastym daszkiem')
def stall(name='stragan', cloth='cloth_red'):
    begin(name)
    for x in (-3, 3):
        for y in (-1.8, 1.8):
            add(box(0.3, 0.3, 4.6 if y < 0 else 5.4, 0.02), T('wood'), loc=(x, y, 2.3 if y < 0 else 2.7), name='post')
    add(box(6.2, 2.6, 1.0, 0.05), T('wood'), loc=(0, -0.8, 1.6), tile=2, name='counter')
    bm = C.bm_grid(8, 4, 7.0, 4.6)
    C.bm_map(bm, lambda co: (co.x, -co.z, 5.4 + co.z * 0.2 + 0.15 * math.sin(co.x * 2.4)))
    C.bm_solidify(bm, 0.05)
    add(bm, T(cloth, 0.9), loc=(0, 2.0, 0), uv='box', tile=4, name='awning')
    amphora((-2.0, -0.8, 2.1), 1.2, 0)
    amphora((-1.2, -0.8, 2.1), 1.0, 2, 'terracotta')
    add(lathe([(0, 0), (0.55, 0), (0.7, 0.4), (0, 0.1)], 16), T('wood_ship'), loc=(0.6, -0.8, 2.1), uv='cyl',
        tile=1, name='basket')
    rnd = random.Random(6)
    for k in range(9):
        add(C.bm_sphere(0.15, 8, 6), F('fruit' + str(k % 4), [(150, 30, 40), (90, 110, 40), (230, 160, 40), (80, 40, 110)][k % 4], 0.4),
            loc=(0.6 + rnd.uniform(-0.35, 0.35), -0.8 + rnd.uniform(-0.35, 0.35), 2.45), name='fruit')
    add(box(1.6, 1.0, 0.4, 0.04), T('cloth_purple'), loc=(2.0, -0.8, 2.3), name='cloth_roll')


prop('stragan_niebieski', 'Targ', 'Stragan z niebieskim daszkiem')(lambda: stall('stragan_niebieski', 'cloth_blue'))


@prop('woz', 'Targ', 'Drewniany woz z sianem')
def cart():
    begin('woz')
    add(box(3.2, 5.0, 0.3, 0.03), T('wood'), loc=(0, 0, 1.6), tile=3, name='bed')
    for sx in (-1, 1):
        add(box(0.2, 5.0, 0.9, 0.02), T('wood'), loc=(sx * 1.5, 0, 2.2), name='side')
        add(C.bm_torus(1.1, 0.15, 24, 6), T('wood_dark'), loc=(sx * 1.8, 0.8, 1.2), rot=(0, 90, 0), name='wheel')
        for k in range(6):
            add(box(0.1, 0.1, 2.2, 0.0), T('wood_dark'), loc=(sx * 1.8, 0.8, 1.2), rot=(k * 30, 0, 0), name='spoke')
    add(box(0.3, 3.2, 0.25, 0.02), T('wood'), loc=(0.4, -4.0, 1.3), rot=(-8, 0, 0), name='shaft')
    add(box(-0.3 + 0.6, 3.2, 0.25, 0.02), T('wood'), loc=(-0.4, -4.0, 1.3), rot=(-8, 0, 0), name='shaft2')
    add(blob_bm(1.4, 9, 2, 0.15, (1.0, 1.6, 0.5)), T('grass_dry', 0.95), loc=(0, 0, 2.4), uv='box', tile=2, name='hay')


@prop('rydwan', 'Targ', 'Rydwan bojowy (dekoracja)')
def chariot():
    begin('rydwan')
    add(box(2.6, 1.8, 0.2, 0.03), T('wood'), loc=(0, 0, 1.5), name='floor')
    bm = C.bm_extrude([(-1.3, 0), (1.3, 0), (1.3, 1.0), (0.9, 1.4), (-0.9, 1.4), (-1.3, 1.0)], 0.12, 0.03, 1)
    C.bm_transform(bm, rot=(90, 0, 0))
    add(bm, BRONZE(), loc=(0, -0.9, 1.6), name='front')
    for sx in (-1, 1):
        add(C.bm_torus(1.4, 0.12, 24, 6), T('wood_dark'), loc=(sx * 1.5, 0.2, 1.4), rot=(0, 90, 0), name='wheel')
        for k in range(4):
            add(box(0.08, 0.08, 2.7, 0.0), T('wood_dark'), loc=(sx * 1.5, 0.2, 1.4), rot=(k * 45, 0, 0), name='spoke')
    add(cyl(0.12, 3.5, 8), T('wood'), loc=(0, 0.2, 1.4), rot=(0, 90, 0), uv='none', name='axle')
    add(box(0.25, 5, 0.25, 0.02), T('wood'), loc=(0, -3.0, 1.2), rot=(-6, 0, 0), name='pole')


@prop('stojak_broni', 'Targ', 'Stojak z wloczniami i tarczami')
def weapon_rack():
    begin('stojak_broni')
    for x in (-2, 2):
        add(box(0.3, 0.3, 3.0, 0.02), T('wood'), loc=(x, 0, 1.5), name='post')
    add(box(4.4, 0.3, 0.3, 0.02), T('wood'), loc=(0, 0, 2.6), name='bar')
    for k in range(5):
        x = -1.6 + k * 0.8
        add(cyl(0.06, 4.0, 6), T('wood'), loc=(x, 0.2, 2.1), rot=(-10, 0, 0), uv='none', name='spear')
        add(cyl(0.12, 0.5, 4, r2=0.0), F('iron', (60, 58, 56), 0.4, 0.8), loc=(x, 0.55, 4.2), rot=(-10, 0, 0),
            name='tip')
    for k, c in enumerate(((170, 40, 30), (40, 70, 140))):
        add(cyl(1.0, 0.15, 24), F('shield' + str(c), c, 0.5), loc=(-1.0 + k * 2.0, -0.4, 1.2), rot=(80, 0, 0),
            uv='none', name='shield')
        add(cyl(0.3, 0.2, 12), BRONZE(), loc=(-1.0 + k * 2.0, -0.5, 1.2), rot=(80, 0, 0), name='boss')


@prop('namiot_wojskowy', 'Targ', 'Namiot wojskowy (oboz)')
def tent():
    begin('namiot_wojskowy')
    for sx in (-1, 1):
        add(box(4.4, 7.0, 0.1, 0.0), T('cloth', 0.95), loc=(sx * 1.55, 0, 1.7), rot=(0, sx * 45, 0), uv='box',
            tile=3, name='side')
    for y in (-3.5, 3.5):
        add(C.bm_extrude([(-3.1, 0), (3.1, 0), (0, 3.2)], 0.08), T('cloth', 0.95), loc=(0, y, 0.05),
            rot=(90, 0, 0), uv='box', tile=3, name='end') if y > 0 else None
    add(cyl(0.12, 4.0, 8), T('wood'), loc=(0, -3.6, 2.0), uv='none', name='pole')
    add(box(1.4, 0.06, 0.9, 0.0), T('cloth_red', 0.9), loc=(0.7, -3.6, 3.6), name='pennant')


@prop('ognisko', 'Targ', 'Ognisko z kamieni')
def campfire():
    begin('ognisko')
    for k in range(8):
        a = 2 * math.pi * k / 8
        add(rock_bm(0.35, 80 + k, 1, 0.3), T('rock'), loc=(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.15), uv='box',
            smooth=False, name='stone')
    for k in range(4):
        add(cyl(0.12, 1.6, 6), T('wood_dark'), loc=(0, 0, 0.3), rot=(70, 0, k * 45), uv='none', name='log')
    add(cyl(0.45, 1.0, 8, r2=0.0), FIRE(), loc=(0, 0, 0.8), uv='none', name='flame')
    marker('Fire', (0, 0, 0.6), size=2.5, heat=5)
    marker('Light', (0, 0, 1.2), range=14, brightness=1.5, color=[255, 150, 70])


@prop('lawka', 'Targ', 'Kamienna lawka')
def bench():
    begin('lawka')
    add(box(4.0, 1.2, 0.35, 0.05), T('blocks_marble'), loc=(0, 0, 1.1), name='seat')
    for x in (-1.5, 1.5):
        add(box(0.5, 1.0, 0.95, 0.04), T('blocks_marble'), loc=(x, 0, 0.47), name='leg')


@prop('stol_uczta', 'Targ', 'Stol z misami i dzbanem (uczta)')
def table():
    begin('stol_uczta')
    add(box(4.0, 2.0, 0.2, 0.03), T('wood'), loc=(0, 0, 1.6), tile=2, name='top')
    for sx in (-1.7, 1.7):
        for sy in (-0.8, 0.8):
            add(cyl(0.12, 1.5, 8), T('wood_dark'), loc=(sx, sy, 0.75), uv='none', name='leg')
    amphora((-1.2, 0, 1.7), 1.0, 2)
    for k in range(3):
        add(lathe([(0, 0), (0.35, 0.05), (0.45, 0.2), (0, 0.1)], 16), BRONZE(), loc=(-0.2 + k * 0.7, 0.3, 1.7),
            uv='box', name='bowl')
    add(C.bm_sphere(0.2, 8, 6), F('bread', (190, 140, 70)), loc=(1.2, -0.4, 1.8), scale=(1.3, 1, 0.6), name='bread')


@prop('lira', 'Targ', 'Lira na postumencie (dekoracja Apolla)')
def lyre():
    begin('lira')
    add(box(1.6, 1.6, 2.0, 0.05), T('blocks_marble'), loc=(0, 0, 1.0), name='ped')
    pts = [(-0.6, 0, 2.2), (-0.9, 0, 3.0), (-0.7, 0, 3.8)]
    for sx in (-1, 1):
        add(tube([(sx * abs(p[0]), p[1], p[2]) for p in pts], 0.09), GOLD(), uv='none', name='arm')
    add(box(1.6, 0.15, 0.15, 0.02), GOLD(), loc=(0, 0, 3.7), name='bar')
    for k in range(5):
        add(cyl(0.015, 1.4, 4), F('string', (230, 220, 200)), loc=(-0.4 + k * 0.2, 0, 3.0), uv='none', name='str')
    add(box(1.0, 0.4, 0.3, 0.05), GOLD(), loc=(0, 0, 2.25), name='sound')


@prop('kraterowa_waza', 'Targ', 'Wielki krater (waza) z brazu')
def krater():
    begin('kraterowa_waza')
    add(lathe([(0, 0), (0.6, 0), (0.4, 0.4), (0.5, 0.7), (1.1, 1.3), (1.4, 2.2), (1.3, 2.3), (0, 1.0)], 28), BRONZE(),
        uv='box', name='body')
    for sx in (-1, 1):
        add(C.bm_torus(0.35, 0.07, 16, 6), BRONZE(), loc=(sx * 1.25, 0, 1.6), rot=(0, 90, 0), name='handle')
