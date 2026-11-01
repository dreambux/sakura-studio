"""Trzecia paczka: ruiny, teatr, wybrzeze, targ, budowa, posagi, ozdoby."""
import math
import random

import bmesh
from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, fluted_column_bm, C)
from .p_arch import column, statue_fig, MARBLE, BLOCKS, LIME, steps


@prop('glowa_posagu', 'Ruiny', 'Gigantyczna marmurowa glowa posagu w trawie')
def giant_head():
    begin('glowa_posagu')
    add(cyl(2.6, 5.0, 32, bev=0.9), MARBLE(), loc=(0, 0, 2.2), rot=(80, 0, 20), uv='cyl', tile=3, name='head')
    add(box(2.6, 1.4, 1.6, 0.5), MARBLE(), loc=(-0.6, -2.6, 1.2), rot=(80, 0, 20), name='beard')
    add(C.bm_torus(2.7, 0.35, 32, 8), GOLD(), loc=(0.4, 0.8, 2.6), rot=(80, 0, 20), name='laurel')
    for k in range(5):
        add(rock_bm(0.6, 70 + k, 1, 0.4), MARBLE(), loc=(random.Random(k).uniform(-4, 4), random.Random(k + 9).uniform(-4, 4), 0.1),
            uv='box', smooth=False, name='chip')


@prop('dlon_posagu', 'Ruiny', 'Gigantyczna dlon posagu wystajaca z ziemi')
def giant_hand():
    begin('dlon_posagu')
    add(box(2.4, 1.4, 3.2, 0.4), MARBLE(), loc=(0, 0, 1.4), rot=(10, 0, 0), name='palm')
    for k in range(4):
        L = (2.6, 2.9, 2.7, 2.2)[k]
        add(box(0.55, 0.55, L, 0.22), MARBLE(), loc=(-0.85 + k * 0.57, 0.2, 3.0 + L / 2 - 0.4), rot=(10 + k * 3, 0, 0), name='finger')
    add(box(0.6, 0.6, 1.8, 0.22), MARBLE(), loc=(1.4, -0.3, 2.2), rot=(20, 40, 0), name='thumb')
    add(blob_bm(2.4, 3, 1, 0.3, (1.3, 1.2, 0.3)), T('ground_scattered'), loc=(0, 0, 0.1), name='mound')


@prop('kolumnada_ruin', 'Ruiny', 'Rzad kolumn z resztka architrawu (ruiny 20 st.)')
def colonnade_ruin():
    begin('kolumnada_ruin')
    add(box(22, 4, 0.8, 0.05), BLOCKS(), loc=(0, 0, 0.4), uv='box', tile=4, name='stylobate')
    rnd = random.Random(4)
    for k in range(6):
        br = 0 if k in (1, 2) else rnd.uniform(0.3, 0.8)
        column((-10 + k * 4, 0, 0.8), 9, 0.7, 'doric', segs=24, broken=br, seed=k, name=f'c{k}')
    add(box(9.5, 2.2, 1.0, 0.04), MARBLE(), loc=(-4, 0, 10.8), name='architrave')
    add(box(4, 2, 1, 0.04), MARBLE(), loc=(5, 2.6, 0.5), rot=(0, 10, 30), name='fallen')


@prop('naiskos', 'Ruiny', 'Naiskos - mala kapliczka z posazkiem')
def naiskos():
    begin('naiskos')
    add(box(4, 3, 0.6, 0.05), BLOCKS(), loc=(0, 0, 0.3), name='base')
    for x in (-1.4, 1.4):
        column((x, -1.0, 0.6), 3.6, 0.3, 'ionic', segs=20)
    add(box(3.8, 2.8, 3.2, 0.05), LIME(), loc=(0, 0.6, 2.2), name='back')
    add(box(4.2, 3.2, 0.5, 0.04), MARBLE(), loc=(0, 0, 4.7), name='lintel')
    tri = C.bm_extrude([(-2.1, 0), (2.1, 0), (0, 1.0)], 3.2)
    C.bm_transform(tri, rot=(90, 0, 0))
    add(tri, MARBLE(), loc=(0, 0, 4.95), name='ped')
    statue_fig((0, 0.2, 0.6), 0.45, GOLD(), 'still')


@prop('maski_teatralne', 'Teatr', 'Maski komedii i tragedii na postumencie')
def masks():
    begin('maski_teatralne')
    add(box(2.6, 1.6, 2.4, 0.06), MARBLE(), loc=(0, 0, 1.2), name='ped')
    for k, (sx, col, smile) in enumerate(((-0.6, (230, 200, 120), 1), (0.6, (200, 210, 230), -1))):
        add(C.bm_sphere(0.6, 16, 10), F('mask' + str(k), col, 0.4), loc=(sx, -0.2, 3.1), scale=(0.9, 0.35, 1.1), name='mask')
        for ex in (-0.2, 0.2):
            add(C.bm_sphere(0.1, 8, 6), F('void', (14, 10, 10)), loc=(sx + ex, -0.42, 3.3), name='eye')
        pts = [(sx - 0.25, -0.42, 2.85 - 0.1 * smile), (sx, -0.44, 2.8 + 0.0), (sx + 0.25, -0.42, 2.85 - 0.1 * smile)]
        pts = [(p[0], p[1], p[2] + (0.12 if (smile < 0 and i == 1) else (-0.12 if (smile > 0 and i == 1) else 0))) for i, p in enumerate(pts)]
        add(tube(pts, 0.05), F('void', (14, 10, 10)), uv='none', name='mouth')


@prop('ogien_sygnalowy', 'Wojsko', 'Wieza z ogniem sygnalowym (plonacy kosz)')
def beacon():
    begin('ogien_sygnalowy')
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(box(0.35, 0.35, 8, 0.02), T('wood_dark'), loc=(sx * 1.4, sy * 1.4, 4), rot=(sy * -6, sx * 6, 0), name='leg')
    add(box(3.4, 3.4, 0.3, 0.02), T('wood'), loc=(0, 0, 8.0), name='platform')
    add(lathe([(0, 0), (0.9, 0), (1.3, 0.8), (0, 0.6)], 16), T('iron'), loc=(0, 0, 8.2), uv='none', name='basket')
    add(cyl(1.0, 2.0, 8, r2=0.0), FIRE(), loc=(0, 0, 9.8), uv='none', name='flame')
    marker('Fire', (0, 0, 9.4), size=6, heat=10)
    marker('Light', (0, 0, 10), range=40, brightness=3, color=[255, 150, 60])


@prop('skaly_morskie', 'Skaly', 'Skaly morskie (wystaja z wody)')
def sea_stacks():
    begin('skaly_morskie')
    rnd = random.Random(30)
    for k in range(4):
        h = rnd.uniform(4, 12)
        add(rock_bm(2.4, 40 + k, 2, 0.25, 0.0, (0.8, 0.8, h / 2.4)), T('cliff'), loc=(rnd.uniform(-5, 5), rnd.uniform(-5, 5), h / 2 - 2),
            uv='box', tile=5, smooth=False, name='stack')


@prop('chata_rybacka', 'Port', 'Chata rybacka z suszonymi rybami')
def fishing_hut():
    begin('chata_rybacka')
    add(box(6, 5, 3.6, 0.06), T('wall_rubble'), loc=(0, 0, 1.8), uv='box', tile=3, name='walls')
    for sx in (-1, 1):
        add(box(3.6, 6.0, 0.3, 0.03), T('straw'), loc=(sx * 1.5, 0, 4.2), rot=(0, sx * 28, 0), uv='box', tile=2, name='roof')
    add(box(1.2, 0.2, 2.4, 0.02), T('wood_dark'), loc=(0, -2.55, 1.2), name='door')
    add(box(4.0, 0.1, 0.1, 0.0), T('wood'), loc=(0, -3.4, 2.6), name='line')
    for k in range(6):
        add(C.bm_sphere(0.22, 8, 6), F('fish', (150, 160, 170), 0.3, 0.5), loc=(-1.6 + k * 0.6, -3.4, 2.2), scale=(0.4, 1, 1.6), name='fish')


@prop('lodz_odwrocona', 'Port', 'Odwrocona lodz na plazy')
def boat_flipped():
    begin('lodz_odwrocona')
    from .p_harbor import hull_bm
    bm = hull_bm(8, 2.8, 1.1, 10, 5)
    add(bm, T('wood_painted_blue'), loc=(0, 0, 2.6), rot=(180, 0, 0), uv='box', tile=3, name='hull')
    for x in (-2, 2):
        add(box(0.3, 0.3, 0.6, 0.02), T('wood_dark'), loc=(0, x, 0.3), name='prop')


@prop('mewy', 'Port', 'Mewy na palach')
def gulls():
    begin('mewy')
    for k, x in enumerate((-1.5, 0, 1.5)):
        add(cyl(0.18, 2.0 + k * 0.4, 8), T('wood_dark'), loc=(x, 0, 1.0 + k * 0.2), uv='cyl', name='pile')
        z = 2.0 + k * 0.4
        add(C.bm_sphere(0.25, 10, 6), F('gull', (240, 240, 236), 0.6), loc=(x, 0, z + 0.25), scale=(0.8, 1.4, 0.8), name='body')
        add(C.bm_sphere(0.14, 8, 6), F('gull', (240, 240, 236), 0.6), loc=(x, -0.3, z + 0.5), name='head')
        add(cyl(0.04, 0.2, 4, r2=0.0), F('beak', (240, 180, 40)), loc=(x, -0.48, z + 0.5), rot=(90, 0, 0), name='beak')
        for sx in (-1, 1):
            add(box(0.08, 0.6, 0.15, 0.02), F('gull_wing', (150, 150, 156), 0.6), loc=(x + sx * 0.2, 0.05, z + 0.3), name='wing')


@prop('stragan_rybny', 'Targ', 'Stragan rybny z lodem i koszami')
def fish_stall():
    begin('stragan_rybny')
    add(box(5, 2.4, 1.0, 0.05), T('wood'), loc=(0, 0, 1.4), name='counter')
    for x in (-2.3, 2.3):
        for y in (-1.0, 1.0):
            add(box(0.25, 0.25, 4.4, 0.02), T('wood'), loc=(x, y, 2.2), name='post')
    add(box(5.4, 3.0, 0.15, 0.02), T('cloth_blue'), loc=(0, 0, 4.5), rot=(8, 0, 0), uv='box', tile=3, name='awning')
    rnd = random.Random(31)
    for k in range(9):
        add(C.bm_sphere(0.25, 8, 6), F('fish', (150, 160, 170), 0.3, 0.5),
            loc=(rnd.uniform(-2, 2), rnd.uniform(-0.8, 0.8), 2.0), scale=(1.6, 0.5, 0.4), rot=(0, 0, rnd.uniform(0, 180)), name='fish')
    add(C.bm_sphere(0.3, 8, 6), F('octopus', (180, 80, 120), 0.4), loc=(1.6, 0, 2.1), name='octopus')


@prop('kram_garncarza', 'Targ', 'Kram garncarza z kolem i amforami')
def potter():
    begin('kram_garncarza')
    add(box(6, 3, 0.2, 0.02), T('wood'), loc=(0, 0, 0.1), name='floor')
    add(cyl(0.6, 0.2, 20), T('wood_dark'), loc=(-1.5, 0, 1.2), uv='none', name='wheel')
    add(cyl(0.12, 1.0, 8), T('wood_dark'), loc=(-1.5, 0, 0.6), uv='none', name='axle')
    add(lathe([(0, 0), (0.35, 0), (0.45, 0.4), (0.25, 0.8), (0, 0.8)], 16), T('clay_pale'), loc=(-1.5, 0, 1.3), uv='box', name='pot')
    from .p_market import amphora
    for k in range(4):
        amphora((0.5 + k * 1.0, 0.6, 0.2), 1.4, k % 3, 'terracotta' if k % 2 else 'terracotta_painted')
    add(box(1.6, 1.0, 0.6, 0.04), T('wood'), loc=(1.8, -0.8, 0.5), name='bench')


@prop('girlanda', 'Ozdoby', 'Girlanda z kwiatow miedzy slupami')
def garland():
    begin('girlanda')
    for x in (-5, 5):
        add(cyl(0.18, 6, 8), T('wood_painted_red'), loc=(x, 0, 3), uv='cyl', name='pole')
        add(C.bm_sphere(0.3, 10, 6), GOLD(), loc=(x, 0, 6.1), name='finial')
    pts = [(x, 0, 5.4 - 1.4 * math.cos(math.pi * (x + 5) / 10 - math.pi / 2) ** 0 * (1 - ((x / 5) ** 2))) for x in range(-5, 6)]
    add(tube(pts, 0.18), T('leaf_lush'), uv='box', name='garland')
    rnd = random.Random(32)
    for k in range(14):
        p = pts[rnd.randrange(len(pts))]
        add(C.bm_sphere(0.14, 8, 6), F('gflower' + str(k % 3), [(230, 60, 80), (250, 220, 90), (240, 240, 240)][k % 3], 0.5),
            loc=(p[0] + rnd.uniform(-0.4, 0.4), p[1] - 0.15, p[2] + rnd.uniform(-0.1, 0.1)), name='flower')


@prop('rusztowanie', 'Ozdoby', 'Drewniane rusztowanie przy budowie (z blokami)')
def scaffolding():
    begin('rusztowanie')
    for x in (-3, 0, 3):
        for y in (-1, 1):
            add(cyl(0.12, 9, 6), T('wood'), loc=(x, y, 4.5), uv='none', name='pole')
    for z in (3, 6):
        add(box(6.6, 2.4, 0.2, 0.02), T('wood'), loc=(0, 0, z), name='deck')
        add(box(6.6, 0.1, 0.1, 0.0), T('wood'), loc=(0, -1.1, z + 1.0), name='rail')
    for k in range(3):
        add(box(1.4, 1.0, 0.8, 0.06), BLOCKS(), loc=(-2 + k * 1.6, 0, 6.5), name='block')
    add(box(2.0, 1.2, 1.0, 0.08), BLOCKS(), loc=(2, -2.5, 0.5), name='ground_block')


@prop('zegar_sloneczny', 'Ozdoby', 'Zegar sloneczny na kolumnie')
def sundial():
    begin('zegar_sloneczny')
    add(cyl(0.6, 3.0, 20), MARBLE(), loc=(0, 0, 1.5), uv='cyl', name='pillar')
    add(cyl(1.3, 0.25, 32), MARBLE(), loc=(0, 0, 3.1), uv='box', name='dial')
    add(C.bm_extrude([(0, 0), (1.0, 0), (0, 0.8)], 0.06), BRONZE(), loc=(0, 0, 3.25), rot=(90, 0, 0), name='gnomon')
    for k in range(12):
        a = 2 * math.pi * k / 12
        add(box(0.06, 0.3, 0.02, 0.0), F('dial_mark', (40, 40, 40)), loc=(math.cos(a) * 1.0, math.sin(a) * 1.0, 3.24),
            rot=(0, 0, math.degrees(a) + 90), name='mark')


@prop('posag_konia', 'Architektura', 'Brazowy posag konia na postumencie')
def horse_statue():
    begin('posag_konia')
    m = BRONZE()
    add(box(5, 2.4, 2, 0.08), BLOCKS(), loc=(0, 0, 1), name='ped')
    add(blob_bm(1.0, 2, 2, 0.05, (1.9, 0.75, 0.85)), m, loc=(0, 0, 4.2), name='body')
    add(box(0.75, 0.6, 2.0, 0.2), m, loc=(-1.8, 0, 5.3), rot=(0, 30, 0), name='neck')
    add(box(1.2, 0.55, 0.55, 0.2), m, loc=(-2.5, 0, 6.2), rot=(0, 10, 0), name='head')
    add(box(0.15, 0.6, 1.6, 0.05), m, loc=(-1.5, 0, 5.8), rot=(0, 30, 0), name='mane')
    for sx, rx in ((-1.2, -40), (1.2, 0)):
        for sy in (-0.4, 0.4):
            add(box(0.32, 0.32, 2.4, 0.1), m, loc=(sx, sy, 2.6 + (0.4 if rx else 0)), rot=(0, rx, 0), name='leg')
    add(tube([(1.9, 0, 4.4), (2.6, 0, 3.6), (2.7, 0, 2.6)], 0.15, radii=[1, 0.8, 0.4]), m, uv='none', name='tail')


@prop('nike_skrzydlata', 'Architektura', 'Nike skrzydlata na dziobie okretu (pomnik)')
def nike():
    begin('nike_skrzydlata')
    from .p_harbor import hull_bm
    add(hull_bm(6, 3, 2, 8, 4), T('blocks_grey'), loc=(0, 0, 0), uv='box', tile=3, name='prow')
    statue_fig((0, -1.0, 3.0), 0.9, MARBLE(), 'arms_up')
    for sy in (-1, 1):
        w = C.bm_extrude([(0, 0), (0.8, 0.8), (1.0, 2.6), (2.0, 4.0), (0.8, 3.0), (0.0, 1.2)], 0.12, 0.03, 1)
        C.bm_map(w, lambda co, sy=sy: (sy * (co.y * 0.6 + 0.6), 0.2 + co.x * 0.4, co.z * 0 + 5.0 + co.y * 0.6))
        add(recalc(w), MARBLE(), loc=(0, -1.0, 0), uv='none', name='wing')


@prop('posag_apollina', 'Architektura', 'Posag Apollina z lira (brazowy)')
def apollo():
    begin('posag_apollina')
    add(box(3, 3, 2.0, 0.08), MARBLE(), loc=(0, 0, 1.0), name='ped')
    statue_fig((0, 0, 2.0), 1.0, BRONZE(), 'still')
    for sx in (-1, 1):
        add(tube([(sx * 0.4, -1.0, 4.4), (sx * 0.7, -1.0, 5.2), (sx * 0.55, -1.0, 5.9)], 0.07), GOLD(), uv='none', name='lyre')
    add(box(1.2, 0.1, 0.1, 0.0), GOLD(), loc=(0, -1.0, 5.85), name='lyrebar')
    add(C.bm_torus(0.6, 0.12, 20, 6), GOLD(), loc=(0, 0, 7.15), name='laurel')


@prop('wiszace_lampy', 'Ozdoby', 'Rzad wiszacych lampek oliwnych na linie')
def hanging_lamps():
    begin('wiszace_lampy')
    for x in (-6, 6):
        add(cyl(0.15, 5, 8), T('wood_dark'), loc=(x, 0, 2.5), uv='cyl', name='pole')
    pts = [(x, 0, 4.8 - 0.8 * (1 - (x / 6) ** 2)) for x in range(-6, 7)]
    add(tube(pts, 0.03, res=3), T('rope'), uv='none', name='rope')
    for k, x in enumerate(range(-4, 5, 2)):
        z = 4.8 - 0.8 * (1 - (x / 6) ** 2) - 0.6
        add(lathe([(0, 0), (0.25, 0.05), (0.3, 0.2), (0, 0.3)], 12), BRONZE(), loc=(x, 0, z), uv='none', name='lamp')
        add(C.bm_sphere(0.1, 8, 6), FIRE(), loc=(x + 0.2, 0, z + 0.3), name='flame')
        marker('Light', (x, 0, z + 0.3), range=8, brightness=0.8, color=[255, 170, 80])


@prop('mur_z_bluszczem', 'Ruiny', 'Mur porosniety bluszczem')
def ivy_wall():
    begin('mur_z_bluszczem')
    add(box(8, 1.2, 4.5, 0.08), T('blocks_mossy'), loc=(0, 0, 2.25), uv='box', tile=4, name='wall')
    rnd = random.Random(33)
    for k in range(14):
        add(blob_bm(rnd.uniform(0.5, 1.0), 80 + k, 1, 0.35, (1.2, 0.35, 1.0)), T('leaf_ivy'),
            loc=(rnd.uniform(-3.8, 3.8), -0.65, rnd.uniform(0.5, 4.4)), uv='box', name='ivy')


@prop('donice_kwiatow', 'Ozdoby', 'Donice z kwiatami (grupa)')
def flower_pots():
    begin('donice_kwiatow')
    for k, (x, y, s) in enumerate(((0, 0, 1.0), (1.4, 0.4, 0.8), (-1.2, 0.5, 0.7), (0.5, -1.1, 0.6))):
        add(lathe([(0, 0), (0.5 * s, 0), (0.7 * s, 0.9 * s), (0.75 * s, 1.0 * s), (0, 0.9 * s)], 16),
            T('terracotta'), loc=(x, y, 0), uv='cyl', name='pot')
        add(blob_bm(0.6 * s, k, 1, 0.3), T('leaf_lush'), loc=(x, y, 1.2 * s), name='plant')
        for j in range(4):
            add(C.bm_sphere(0.1, 6, 4), F('pflower' + str(k % 3), [(230, 60, 90), (250, 200, 60), (180, 120, 230)][k % 3], 0.5),
                loc=(x + 0.3 * math.cos(j * 1.6), y + 0.3 * math.sin(j * 1.6), 1.55 * s), name='bloom')


@prop('urny', 'Ozdoby', 'Marmurowe urny na cokolach (para)')
def urns():
    begin('urny')
    for x in (-1.5, 1.5):
        add(box(1.2, 1.2, 1.2, 0.05), MARBLE(), loc=(x, 0, 0.6), name='plinth')
        add(lathe([(0, 0), (0.35, 0), (0.25, 0.2), (0.6, 0.7), (0.5, 1.2), (0.65, 1.35), (0, 1.3)], 24), MARBLE(),
            loc=(x, 0, 1.2), uv='box', name='urn')
