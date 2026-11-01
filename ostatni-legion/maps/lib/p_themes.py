"""Paczki tematyczne: wulkan/kuznia Hefajstosa, Knossos (Kreta), Olimp, nekropolia (nieumarli), tla."""
import math
import random

import bmesh
from mathutils import Vector, noise

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, C)
from .p_arch import column, statue_fig, MARBLE, BLOCKS


# ------------------------------------------------------------------ WULKAN / KUZNIA
@prop('kowadlo', 'Wulkan', 'Kowadlo na pniu')
def anvil():
    begin('kowadlo')
    add(cyl(0.9, 1.4, 14), T('wood_dark'), loc=(0, 0, 0.7), uv='cyl', name='stump')
    add(box(2.2, 0.8, 0.6, 0.06), F('iron', (60, 58, 56), 0.45, 0.85), loc=(0, 0, 1.8), name='top')
    add(box(1.0, 0.7, 0.4, 0.05), F('iron', (60, 58, 56), 0.45, 0.85), loc=(0, 0, 1.4), name='waist')
    add(cyl(0.3, 1.0, 8, r2=0.0), F('iron', (60, 58, 56), 0.45, 0.85), loc=(-1.5, 0, 1.85), rot=(0, 90, 0), name='horn')
    add(box(0.3, 0.3, 1.2, 0.02), T('wood'), loc=(0.6, 0.3, 2.6), rot=(0, 60, 0), name='hammer_h')
    add(box(0.5, 0.4, 0.35, 0.03), F('iron', (60, 58, 56), 0.45, 0.85), loc=(1.05, 0.3, 2.95), rot=(0, 60, 0),
        name='hammer')


@prop('kuznia', 'Wulkan', 'Kuznia Hefajstosa: piec z zarem, miech, kowadlo')
def forge():
    begin('kuznia')
    add(box(6, 5, 4, 0.15), T('blocks_grey'), loc=(0, 0, 2), uv='box', tile=4, name='furnace')
    add(cyl(1.3, 6, 8, r2=0.9), T('blocks_grey'), loc=(1.5, 1.2, 7), uv='box', tile=4, name='chimney')
    add(box(3, 0.3, 2.2, 0.05), T('lava', 0.6), loc=(0, -2.55, 1.6), uv='box', tile=2, name='mouth')
    add(box(3.6, 1.6, 0.5, 0.05), T('blocks_grey'), loc=(0, -2.6, 0.25), name='lip')
    add(C.bm_sphere(1.0, 14, 8), FIRE(), loc=(0, -2.0, 1.4), scale=(1.2, 0.6, 0.8), name='glow')
    marker('Fire', (0, -2.4, 1.6), size=5, heat=9)
    marker('Light', (0, -3.0, 1.8), range=24, brightness=3, color=[255, 120, 40])
    marker('Smoke', (1.5, 1.2, 10.2), size=4, opacity=0.4)
    add(blob_bm(1.2, 3, 2, 0.08, (1.2, 0.6, 0.6)), T('leather_dark') if False else F('leather', (90, 52, 30), 0.7),
        loc=(-3.6, -0.5, 1.2), name='bellows')
    add(box(2.0, 0.4, 0.3, 0.02), T('wood'), loc=(-3.6, -1.7, 1.4), name='bellows_handle')
    for k in range(3):
        add(C.bm_tube([(2.8 + k * 0.3, -2.6, 3.8), (2.9 + k * 0.3, -2.7, 1.2)], 0.06, smooth=False, bevel_res=1),
            F('iron', (60, 58, 56), 0.45, 0.85), uv='none', name='tool')


@prop('kociol_lawy', 'Wulkan', 'Kociol z roztopionym brazem')
def cauldron():
    begin('kociol_lawy')
    add(lathe([(0, 0), (1.2, 0.2), (1.6, 0.9), (1.5, 1.8), (1.35, 1.8), (1.3, 1.0), (0, 0.4)], 28),
        F('iron', (60, 58, 56), 0.45, 0.85), loc=(0, 0, 0.6), uv='none', name='pot')
    add(cyl(1.3, 0.1, 28), T('lava', 0.4), loc=(0, 0, 2.2), uv='box', tile=2, name='molten')
    for k in range(3):
        a = 2 * math.pi * k / 3
        add(cyl(0.15, 0.9, 8), F('iron', (60, 58, 56), 0.45, 0.85), loc=(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.45),
            uv='none', name='leg')
    marker('Light', (0, 0, 2.6), range=14, brightness=2, color=[255, 120, 40])


@prop('jeziorko_lawy', 'Wulkan', 'Jeziorko lawy w bazaltowej obreczy (swieci)')
def lava_pool():
    begin('jeziorko_lawy')
    add(cyl(4.0, 0.2, 40), T('lava', 0.3), loc=(0, 0, 0.15), uv='box', tile=4, name='lava')
    rnd = random.Random(5)
    for k in range(12):
        a = 2 * math.pi * k / 12
        add(rock_bm(1.0, 90 + k, 1, 0.4), T('basalt'), loc=(math.cos(a) * 4.3, math.sin(a) * 4.3, 0.3),
            uv='box', smooth=False, name='rim')
    marker('Light', (0, 0, 1.5), range=20, brightness=3, color=[255, 110, 30])
    marker('Embers', (0, 0, 0.5), rate=6)


@prop('szczelina_lawy', 'Wulkan', 'Pekniecie w ziemi z lawa (pas 12 st.)')
def lava_crack():
    begin('szczelina_lawy')
    pts = [(-6, 0, 0.1), (-3, 0.6, 0.1), (0, -0.4, 0.1), (3, 0.5, 0.1), (6, 0, 0.1)]
    add(tube(pts, 0.6, radii=[0.3, 1.0, 0.8, 1.0, 0.3], res=8), T('lava', 0.3), scale=(1, 1, 0.25), uv='box',
        tile=3, name='lava')
    for k, p in enumerate(pts):
        for sy in (-1, 1):
            add(rock_bm(0.6, 100 + k * 2 + sy, 1, 0.4), T('basalt'), loc=(p[0], p[1] + sy * 0.9, 0.15),
                uv='box', smooth=False, name='edge')
    marker('Light', (0, 0, 1.0), range=16, brightness=2, color=[255, 110, 30])


@prop('obsydian', 'Wulkan', 'Krysztaly obsydianu')
def obsidian():
    begin('obsydian')
    rnd = random.Random(7)
    for k in range(7):
        h = rnd.uniform(1.0, 3.2)
        add(cyl(0.45, h, 5, r2=0.05), F('obsidian', (20, 16, 26), 0.08, 0.3), loc=(rnd.uniform(-1, 1), rnd.uniform(-1, 1), h / 2),
            rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), rnd.uniform(0, 90)), uv='none', smooth=False, name='shard')


@prop('dymiacy_otwor', 'Wulkan', 'Fumarola - dymiacy otwor')
def fumarole():
    begin('dymiacy_otwor')
    add(lathe([(0, 0), (2.2, 0), (1.6, 0.9), (0.8, 1.2), (0.6, 0.9), (0, 0.8)], 24), T('basalt'), uv='box', tile=3,
        name='cone')
    add(cyl(0.6, 0.05, 16), T('lava', 0.3), loc=(0, 0, 0.95), uv='box', name='glow')
    marker('Smoke', (0, 0, 1.3), size=3, opacity=0.5)


@prop('talos', 'Wulkan', 'Talos - olbrzymi brazowy automat (pomnik, 24 st.)')
def talos():
    begin('talos')
    add(box(8, 8, 2, 0.1), T('basalt'), loc=(0, 0, 1), uv='box', tile=4, name='base')
    s = 4.0
    statue_fig((0, 0, 2.0), s, BRONZE(), 'spear')
    add(C.bm_sphere(0.35 * s, 14, 8), GLOW('talos_eye', (255, 120, 30), 6), loc=(0, -0.62 * s, 2.0 + 4.65 * s),
        scale=(1.6, 0.3, 0.35), name='eyes')
    for k in range(8):
        add(cyl(0.12 * s, 0.2 * s, 10), F('rivet', (110, 70, 30), 0.4, 1.0), loc=(-0.8 * s + k * 0.23 * s, -0.52 * s, 2.0 + 3.6 * s),
            rot=(90, 0, 0), name='rivet')
    marker('Light', (0, -3, 2.0 + 4.6 * s), range=30, brightness=2, color=[255, 120, 40])


@prop('wulkan_tlo', 'Tla', 'Wulkan na tlo (z kraterem i lawa)')
def volcano_bg():
    begin('wulkan_tlo')
    prof = [(0, 0), (90, 0), (70, 15), (45, 40), (22, 70), (16, 78), (12, 74), (0, 70)]
    bm = lathe(prof, 48)
    for v in bm.verts:
        p = v.co * 0.05
        v.co.x += noise.noise(p) * 6
        v.co.y += noise.noise(p + Vector((5, 5, 5))) * 6
        v.co.z += noise.noise(p + Vector((9, 1, 3))) * 3 * (v.co.z > 2)
    add(bm, T('basalt'), uv='box', tile=16, smooth=False, name='mountain')
    add(cyl(12, 0.5, 32), T('lava', 0.3), loc=(0, 0, 72), uv='box', tile=6, name='crater')
    for k in range(5):
        a = k * 1.25
        pts = [(math.cos(a) * 14, math.sin(a) * 14, 74), (math.cos(a) * 35, math.sin(a) * 35, 45 + k),
               (math.cos(a) * 70, math.sin(a) * 70, 12)]
        add(tube(pts, 2.0, radii=[1.0, 0.8, 0.5], res=8), T('lava', 0.3), uv='box', tile=6, name='flow')
    marker('Smoke', (0, 0, 80), size=40, opacity=0.6)
    marker('Light', (0, 0, 76), range=120, brightness=5, color=[255, 100, 30])


# ------------------------------------------------------------------ KNOSSOS / KRETA
@prop('rogi_konsekracji', 'Knossos', 'Rogi konsekracji (symbol minojski)')
def horns():
    begin('rogi_konsekracji')
    add(box(4.4, 1.6, 0.8, 0.06), T('plaster'), loc=(0, 0, 0.4), name='base')
    for sx in (-1, 1):
        pts = [(sx * 0.6, 0, 0.8), (sx * 1.6, 0, 1.4), (sx * 2.0, 0, 3.0), (sx * 1.7, 0, 4.0)]
        add(tube(pts, 0.55, radii=[1.0, 0.9, 0.7, 0.3]), T('plaster'), uv='box', name='horn')


@prop('labrys_stojak', 'Knossos', 'Swiety labrys na stojaku')
def labrys_stand():
    begin('labrys_stojak')
    add(box(1.6, 1.6, 0.6, 0.05), T('plaster_red'), loc=(0, 0, 0.3), name='base')
    add(cyl(0.12, 5.0, 8), T('wood_dark'), loc=(0, 0, 3.0), uv='none', name='pole')
    for sz in (-1, 1):
        bm = C.bm_extrude([(0.1, -0.3), (0.6, -0.5), (1.0, -0.9), (1.1, 0), (1.0, 0.9), (0.6, 0.5), (0.1, 0.3)], 0.1, 0.02, 1)
        C.bm_map(bm, lambda co, sz=sz: (sz * co.x, co.z, co.y))
        add(recalc(bm), GOLD(), loc=(0, 0, 5.0), uv='none', name='blade')


@prop('mur_fresk', 'Knossos', 'Sciana z freskiem (czerwony tynk, pas z rozetami)')
def fresco_wall():
    begin('mur_fresk')
    add(box(10, 1.2, 6, 0.08), T('plaster_red'), loc=(0, 0, 3), uv='box', tile=4, name='wall')
    add(box(10.2, 1.3, 0.9, 0.05), T('plaster'), loc=(0, 0, 4.2), uv='box', tile=4, name='band')
    for k in range(6):
        add(cyl(0.38, 0.1, 16), F('fresco_blue', (40, 80, 150)), loc=(-4.2 + k * 1.7, -0.66, 4.2), rot=(90, 0, 0),
            name='rosette')
        add(cyl(0.16, 0.12, 12), F('fresco_yellow', (220, 170, 60)), loc=(-4.2 + k * 1.7, -0.7, 4.2), rot=(90, 0, 0),
            name='rosette_c')
    add(box(10.2, 1.4, 0.4, 0.04), T('plaster_ochre'), loc=(0, 0, 6.2), name='cap')
    add(box(10.2, 1.4, 0.8, 0.04), T('plaster_ochre'), loc=(0, 0, 0.4), name='dado')
    # stylizowany byk na fresku
    add(box(2.6, 0.08, 1.2, 0.05), F('fresco_bull', (40, 30, 26)), loc=(-1.0, -0.62, 2.4), name='bull_body')
    add(box(0.8, 0.08, 0.8, 0.05), F('fresco_bull', (40, 30, 26)), loc=(0.6, -0.62, 2.8), name='bull_head')
    for sx in (-1, 1):
        add(box(0.12, 0.08, 1.0, 0.0), F('fresco_bull', (40, 30, 26)), loc=(-1.0 + sx * 0.9, -0.62, 1.4), name='leg')


@prop('posag_byka', 'Knossos', 'Posag byka z brazu na postumencie')
def bull_statue():
    begin('posag_byka')
    add(box(6, 3, 1.6, 0.08), T('blocks_marble'), loc=(0, 0, 0.8), name='ped')
    add(box(4.4, 1.8, 2.0, 0.4), BRONZE(), loc=(0, 0, 3.4), name='body')
    for sx in (-1.6, 1.6):
        for sy in (-0.6, 0.6):
            add(box(0.5, 0.5, 1.5, 0.12), BRONZE(), loc=(sx, sy, 2.0), name='leg')
    add(box(1.4, 1.3, 1.3, 0.3), BRONZE(), loc=(-2.8, 0, 4.0), name='head')
    for sy in (-1, 1):
        add(tube([(-2.9, sy * 0.5, 4.6), (-3.1, sy * 1.2, 5.0), (-3.5, sy * 1.3, 5.6)], 0.15, radii=[1, 0.7, 0.2]),
            GOLD(), uv='none', name='horn')
    add(tube([(2.2, 0, 4.0), (2.8, 0, 3.0), (2.7, 0, 1.8)], 0.08), BRONZE(), uv='none', name='tail')


@prop('labirynt_sciana', 'Knossos', 'Segment murow labiryntu (zywoplot w kamiennej ramie)')
def maze_wall():
    begin('labirynt_sciana')
    add(box(8, 2.0, 1.0, 0.06), T('blocks'), loc=(0, 0, 0.5), uv='box', tile=4, name='base')
    add(box(7.6, 1.8, 3.4, 0.4), T('leaf_dark'), loc=(0, 0, 2.7), uv='box', tile=3, name='hedge')
    for x in (-4, 4):
        add(box(1.2, 2.2, 5.0, 0.06), T('blocks'), loc=(x, 0, 2.5), uv='box', tile=4, name='pillar')
        add(C.bm_sphere(0.55, 12, 8), T('blocks_marble'), loc=(x, 0, 5.4), name='ball')


# ------------------------------------------------------------------ OLIMP
@prop('chmura', 'Olimp', 'Puszysta chmura (morze chmur pod Olimpem)')
def cloud(name='chmura', seed=1, s=1.0):
    begin(name)
    rnd = random.Random(seed)
    m = F('cloud', (246, 248, 255), 0.95)
    for k in range(7):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0, 5) * s
        add(blob_bm(rnd.uniform(2.5, 4.5) * s, seed * 10 + k, 2, 0.15, (1.2, 1.0, 0.7)), m,
            loc=(math.cos(a) * r, math.sin(a) * r, rnd.uniform(0, 1.5) * s), uv='none', name='puff')


prop('chmura_duza', 'Olimp', 'Duza chmura')(lambda: cloud('chmura_duza', 2, 2.0))


@prop('szczyt_osniezony', 'Tla', 'Osniezony szczyt (tlo Olimpu)')
def snow_peak():
    begin('szczyt_osniezony')
    prof = [(0, 0), (60, 0), (40, 30), (20, 60), (6, 85), (0, 90)]
    bm = lathe(prof, 40)
    for v in bm.verts:
        p = v.co * 0.06
        v.co.x += noise.noise(p) * 8
        v.co.y += noise.noise(p + Vector((5, 5, 5))) * 8
    add(bm, T('cliff_grey'), uv='box', tile=16, smooth=False, name='rock')
    prof = [(0, 50), (26, 50), (20, 60), (6, 86), (0, 91)]
    bm = lathe(prof, 40)
    for v in bm.verts:
        p = v.co * 0.06
        v.co.x += noise.noise(p) * 8 * 1.06
        v.co.y += noise.noise(p + Vector((5, 5, 5))) * 8 * 1.06
        v.co.x *= 1.04
        v.co.y *= 1.04
    add(bm, T('snow'), uv='box', tile=10, smooth=False, name='snowcap')


@prop('orzel_zeusa', 'Olimp', 'Zloty orzel Zeusa na kolumnie')
def eagle():
    begin('orzel_zeusa')
    column((0, 0, 0), 7.0, 0.7, 'doric', segs=28)
    z = 8.0
    add(blob_bm(0.9, 4, 2, 0.05, (0.8, 1.3, 1.0)), GOLD(), loc=(0, 0, z + 0.9), uv='none', name='body')
    add(C.bm_sphere(0.45, 12, 8), GOLD(), loc=(0, -0.9, z + 1.9), name='head')
    add(cyl(0.18, 0.5, 6, r2=0.0), F('beak', (230, 180, 60), 0.4, 0.8), loc=(0, -1.3, z + 1.85), rot=(90, 0, 0), name='beak')
    for sx in (-1, 1):
        w = C.bm_extrude([(0, 0), (1.2, 0.8), (2.6, 1.8), (3.4, 1.4), (2.8, 0.6), (3.2, 0.2), (2.2, -0.2), (1.0, -0.4)],
                         0.12, 0.03, 1)
        C.bm_map(w, lambda co, sx=sx: (sx * co.x, co.z, co.y))
        add(recalc(w), GOLD(), loc=(sx * 0.5, 0.2, z + 1.4), rot=(0, sx * -20, 0), uv='none', name='wing')


@prop('piorun_pomnik', 'Olimp', 'Swiecacy piorun Zeusa wbity w skale')
def bolt_monument():
    begin('piorun_pomnik')
    add(rock_bm(2.4, 9, 2, 0.3), T('rock_white'), loc=(0, 0, 0.8), uv='box', smooth=False, name='rock')
    pts = [(0, 0), (0.6, 1.2), (0.1, 1.3), (0.9, 3.2), (0.4, 3.3), (1.2, 5.8), (-0.4, 2.8), (0.1, 2.7), (-0.6, 1.0),
           (-0.1, 0.9), (-0.4, 0)]
    bm = C.bm_extrude([(x * 1.4, y * 1.4) for x, y in pts], 0.4, 0.05, 1)
    C.bm_transform(bm, rot=(90, 0, 15))
    add(bm, GLOW('bolt', (150, 200, 255), 8), loc=(0, 0, 1.6), uv='none', name='bolt')
    marker('Light', (0, 0, 5), range=22, brightness=3, color=[160, 200, 255])
    marker('Sparkles', (0, 0, 5), color=[160, 200, 255])


@prop('zloty_tron_zeusa', 'Olimp', 'Zloty tron Zeusa na schodach')
def zeus_throne():
    begin('zloty_tron_zeusa')
    for i in range(3):
        add(box(8 - i * 1.5, 6 - i * 1.2, 0.6, 0.04), MARBLE(), loc=(0, 0, 0.3 + i * 0.6), name='step')
    add(box(3.0, 2.6, 2.0, 0.08), GOLD(), loc=(0, 0.3, 2.8), name='seat')
    add(box(3.2, 0.6, 5.0, 0.08), GOLD(), loc=(0, 1.4, 4.4), name='back')
    for sx in (-1, 1):
        add(box(0.5, 2.6, 1.2, 0.08), GOLD(), loc=(sx * 1.6, 0.3, 4.0), name='arm')
        add(C.bm_sphere(0.4, 12, 8), F('sapphire', (40, 80, 200), 0.1), loc=(sx * 1.6, -1.0, 4.7), name='gem')
    add(cyl(1.2, 0.3, 24), F('sapphire', (40, 80, 200), 0.1), loc=(0, 1.1, 6.4), rot=(90, 0, 0), name='disc')


# ------------------------------------------------------------------ NEKROPOLIA (nieumarli)
@prop('nagrobek', 'Nekropolia', 'Nagrobek (przekrzywiony)')
def tombstone(name='nagrobek', seed=1):
    begin(name)
    rnd = random.Random(seed)
    add(box(1.6, 0.4, 2.2, 0.08), T('blocks_grey'), loc=(0, 0, 1.0), rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), 0),
        uv='box', tile=2, name='stone')
    add(cyl(0.8, 0.4, 20), T('blocks_grey'), loc=(0, 0, 2.1), rot=(90, 0, 0), uv='box', tile=2, name='round')
    add(blob_bm(1.2, seed, 1, 0.2, (1, 1.4, 0.2)), T('dirt_path'), loc=(0, -1.3, 0.05), name='mound')


prop('nagrobek_2', 'Nekropolia', 'Nagrobek (wariant)')(lambda: tombstone('nagrobek_2', 2))


@prop('otwarty_grob', 'Nekropolia', 'Rozkopany grob (stad wychodza zombie)')
def open_grave():
    begin('otwarty_grob')
    add(box(4.0, 2.4, 0.2, 0.05), F('void', (14, 10, 10)), loc=(0, 0, 0.05), name='hole')
    rnd = random.Random(3)
    for k in range(10):
        a = 2 * math.pi * k / 10
        add(blob_bm(0.7, 30 + k, 1, 0.3, (1, 1, 0.5)), T('ground_scattered'),
            loc=(math.cos(a) * 2.4, math.sin(a) * 1.6, 0.2), uv='box', name='dirt')
    add(box(1.6, 0.4, 2.0, 0.08), T('blocks_grey'), loc=(0, 1.6, 1.0), rot=(-20, 0, 5), name='stone')
    marker('Mist', (0, 0, 0.5), color=[120, 255, 140])


@prop('kosci', 'Nekropolia', 'Stos kosci i czaszek')
def bones():
    begin('kosci')
    rnd = random.Random(4)
    bone = F('bone', (226, 214, 186), 0.6)
    for k in range(10):
        add(cyl(0.08, rnd.uniform(0.8, 1.4), 6), bone, loc=(rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.15),
            rot=(90, 0, rnd.uniform(0, 180)), uv='none', name='bone')
    for k in range(3):
        p = (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), 0.35)
        add(C.bm_sphere(0.35, 12, 8), bone, loc=p, scale=(1, 1.1, 0.95), name='skull')
        for sx in (-1, 1):
            add(C.bm_sphere(0.09, 8, 4), F('void', (14, 10, 10)), loc=(p[0] + sx * 0.13, p[1] - 0.3, p[2] + 0.05),
                name='eye')


@prop('trumna_zlamana', 'Nekropolia', 'Rozbita drewniana trumna')
def coffin():
    begin('trumna_zlamana')
    add(box(1.8, 4.2, 0.9, 0.05), T('wood_dark'), loc=(0, 0, 0.45), uv='box', tile=2, name='box')
    add(box(1.6, 3.9, 0.1, 0.0), F('void', (14, 10, 10)), loc=(0, 0, 0.88), name='inside')
    add(box(1.9, 4.3, 0.2, 0.03), T('wood_dark'), loc=(1.6, 0.6, 0.3), rot=(0, 25, 30), name='lid')


@prop('mauzoleum', 'Nekropolia', 'Grecki grobowiec z kolumnami (wejscie)')
def mausoleum():
    begin('mauzoleum')
    add(box(10, 8, 0.8, 0.06), T('blocks_grey'), loc=(0, 0, 0.4), name='base')
    add(box(8, 6, 6, 0.08), T('blocks_grey'), loc=(0, 0.6, 3.8), uv='box', tile=4, name='body')
    for x in (-3, 3):
        column((x, -3.2, 0.8), 5.6, 0.5, 'doric', mat=T('blocks_grey'), segs=24)
    add(box(9, 7.6, 0.8, 0.06), T('blocks_grey'), loc=(0, 0, 7.2), name='lintel')
    tri = C.bm_extrude([(-4.6, 0), (4.6, 0), (0, 2.4)], 7.6)
    C.bm_transform(tri, rot=(90, 0, 0))
    add(tri, T('blocks_grey'), loc=(0, 0, 7.6), uv='box', tile=4, name='pediment')
    add(box(2.6, 0.3, 4.0, 0.03), F('void', (14, 10, 10)), loc=(0, -2.45, 2.8), name='door')
    marker('Mist', (0, -3, 0.8), color=[120, 255, 140])


# ------------------------------------------------------------------ TLA
@prop('wyspa_tlo', 'Tla', 'Odlegla skalista wyspa z drzewami (tlo morza)')
def island_bg():
    begin('wyspa_tlo')
    bm = rock_bm(30, 7, 3, 0.25, 0.2, (1.4, 1.0, 0.45))
    add(bm, T('cliff'), uv='box', tile=12, smooth=False, name='rock')
    add(blob_bm(26, 8, 2, 0.12, (1.3, 0.95, 0.18)), T('grass_dry'), loc=(0, 0, 11), uv='box', tile=12, name='top')
    rnd = random.Random(8)
    for k in range(10):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 20)
        add(blob_bm(3.0, 40 + k, 1, 0.2, (1, 1, 1.6)), T('leaf_dark'), loc=(math.cos(a) * r * 1.3, math.sin(a) * r, 16),
            uv='box', name='tree')
    column((10, 4, 12), 8, 0.7, 'doric', segs=20, name='ruin1')
    column((15, 4, 12), 8, 0.7, 'doric', segs=20, broken=0.4, name='ruin2')


@prop('gory_tlo', 'Tla', 'Pasmo gor na tlo (Kreta / Olimp)')
def mountains_bg():
    begin('gory_tlo')
    bm = C.bm_grid(40, 10, 400, 80)
    C.bm_map(bm, lambda co: (co.x, -co.z * 1.2, max(0.0, 60 * (1 + co.z / 80) * (0.5 + 0.5 * noise.fractal(
        Vector((co.x * 0.012, 0.3, 0)), 0.5, 2.0, 4))) * (1 + co.z / 80) ** 0.6))
    add(bm, T('cliff_grey'), uv='box', tile=20, smooth=False, name='range')
