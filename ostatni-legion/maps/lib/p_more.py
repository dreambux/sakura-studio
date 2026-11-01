"""Druga duza paczka modeli: wies, ogrody, zima, podwodne, podziemia, oblezenie, stadion, Delfy, Hesperydy."""
import math
import random

import bmesh
from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, fluted_column_bm, C)
from .p_arch import column, statue_fig, MARBLE, BLOCKS, LIME, steps, frieze, pediment
from .p_nature import _trunk, _canopy


def fruit_tree(name, leaf, fruit_col, seed, s=1.0, fruits=14):
    begin(name)
    rnd = random.Random(seed)
    _trunk([(0, 0, 0), (0.3 * s, 0, 2.5 * s), (0, 0.2, 4.5 * s)], 0.5 * s, 'bark', radii=[1.2, 0.9, 0.7])
    cs = [((0, 0, 6.0 * s), 2.8 * s, (1, 1, 0.85))]
    for k in range(5):
        a = k * 1.25 + rnd.random()
        cs.append(((math.cos(a) * 2.2 * s, math.sin(a) * 2.2 * s, rnd.uniform(4.8, 6.0) * s), rnd.uniform(1.6, 2.2) * s,
                   (1, 1, 0.85)))
    _canopy(cs, leaf, seed)
    for k in range(fruits):
        a, el = rnd.uniform(0, 6.28), rnd.uniform(-0.3, 0.7)
        r = 3.1 * s
        add(C.bm_sphere(0.22 * s, 10, 6), F('fruit_' + name, fruit_col, 0.35),
            loc=(math.cos(a) * r * math.cos(el), math.sin(a) * r * math.cos(el), 5.6 * s + r * 0.6 * math.sin(el)),
            name='fruit')


# ------------------------------------------------------------------ ogrody i wies
prop('drzewo_cytrynowe', 'Rosliny', 'Drzewo cytrynowe z owocami')(lambda: fruit_tree('drzewo_cytrynowe', 'leaf_lush', (240, 210, 60), 3))
prop('granatowiec', 'Rosliny', 'Granatowiec z czerwonymi owocami')(lambda: fruit_tree('granatowiec', 'leaf_dark', (190, 40, 40), 4))
prop('drzewo_figowe', 'Rosliny', 'Drzewo figowe')(lambda: fruit_tree('drzewo_figowe', 'leaf_vine', (90, 50, 100), 5, 1.1, 10))
prop('zlota_jablon', 'Unikaty', 'Zlota jablon Hesperyd (zlote jablka)')(
    lambda: (fruit_tree('zlota_jablon', 'leaf_lush', (240, 190, 60), 6, 1.3, 20), marker('Sparkles', (0, 0, 8), color=[255, 210, 90])))


@prop('bukszpan_kula', 'Rosliny', 'Strzyzony bukszpan - kula w donicy')
def topiary_ball():
    begin('bukszpan_kula')
    add(lathe([(0, 0), (1.1, 0), (1.3, 1.2), (1.2, 1.3), (0, 1.1)], 20), T('terracotta'), uv='cyl', name='pot')
    add(C.bm_sphere(1.6, 20, 12), T('leaf_dark'), loc=(0, 0, 2.7), uv='box', tile=2, name='ball')


@prop('bukszpan_stozek', 'Rosliny', 'Strzyzony bukszpan - stozek')
def topiary_cone():
    begin('bukszpan_stozek')
    add(box(2.2, 2.2, 1.0, 0.1), T('blocks_marble'), loc=(0, 0, 0.5), name='planter')
    add(cyl(1.5, 5.0, 20, r2=0.15), T('leaf_dark'), loc=(0, 0, 3.5), uv='cyl', tile=2, name='cone')


@prop('zywoplot', 'Rosliny', 'Prosty zywoplot (8 st.)')
def hedge():
    begin('zywoplot')
    add(box(8, 2, 3.2, 0.5), T('leaf_dark'), loc=(0, 0, 1.6), uv='box', tile=3, name='hedge')


@prop('lilie_wodne', 'Rosliny', 'Lilie wodne (na wode)')
def lilies():
    begin('lilie_wodne')
    rnd = random.Random(7)
    for k in range(8):
        x, y = rnd.uniform(-3, 3), rnd.uniform(-3, 3)
        add(cyl(rnd.uniform(0.5, 0.9), 0.06, 16), T('leaf_lush'), loc=(x, y, 0.05), uv='box', tile=2, name='pad')
        if k % 3 == 0:
            add(C.bm_sphere(0.25, 10, 6), F('lily', (240, 200, 220), 0.5), loc=(x, y, 0.25), scale=(1, 1, 0.7), name='flower')


@prop('asfodele', 'Rosliny', 'Blade asfodele (laki Hadesu)')
def asphodel():
    begin('asfodele')
    rnd = random.Random(8)
    stem = F('asph_stem', (110, 130, 100), 0.7)
    for k in range(16):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 1.6)
        x, y = math.cos(a) * r, math.sin(a) * r
        h = rnd.uniform(1.0, 2.0)
        add(cyl(0.04, h, 5), stem, loc=(x, y, h / 2), uv='none', name='stem')
        for j in range(3):
            add(C.bm_sphere(0.12, 8, 5), GLOW('asph', (220, 230, 255), 0.8), loc=(x, y, h - j * 0.18), name='bloom')


@prop('grzyby', 'Rosliny', 'Grzyby (cien, las)')
def mushrooms():
    begin('grzyby')
    rnd = random.Random(9)
    for k in range(6):
        x, y, s = rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.6, 1.3)
        add(cyl(0.12 * s, 0.6 * s, 8), F('mush_stem', (230, 220, 200)), loc=(x, y, 0.3 * s), uv='none', name='stem')
        add(lathe([(0, 0), (0.45 * s, 0), (0.35 * s, 0.25 * s), (0, 0.32 * s)], 16), F('mush_cap', (170, 60, 40)),
            loc=(x, y, 0.55 * s), uv='none', name='cap')


@prop('pniak', 'Rosliny', 'Pniak z siekiera')
def stump():
    begin('pniak')
    add(cyl(1.0, 1.2, 16, r2=0.9), T('bark'), loc=(0, 0, 0.6), uv='cyl', name='stump')
    add(cyl(0.9, 0.05, 16), T('wood_pale'), loc=(0, 0, 1.22), uv='box', name='rings')
    add(box(0.15, 0.15, 1.6, 0.02), T('wood'), loc=(0.3, 0, 1.8), rot=(0, 25, 0), name='axe_h')
    add(box(0.6, 0.12, 0.4, 0.02), T('iron'), loc=(0.0, 0, 1.3), rot=(0, 25, 0), name='axe')


@prop('klody', 'Rosliny', 'Stos klod drewna')
def logs():
    begin('klody')
    for row, n in enumerate((4, 3, 2)):
        for k in range(n):
            add(cyl(0.45, 4.0, 12), T('bark'), loc=(-(n - 1) * 0.47 + k * 0.94, 0, 0.45 + row * 0.8), rot=(90, 0, 0),
                uv='cyl', name='log')


@prop('powalone_drzewo', 'Rosliny', 'Powalone drzewo z korzeniami')
def fallen_tree():
    begin('powalone_drzewo')
    add(cyl(0.8, 12, 14, r2=0.5), T('bark'), loc=(0, 0, 0.7), rot=(0, 90, 8), uv='cyl', name='trunk')
    for k in range(7):
        a = k * 0.9
        add(tube([(-6, 0, 0.8), (-6.8, math.cos(a) * 1.6, 0.8 + math.sin(a) * 1.6)], 0.2, radii=[1, 0.3]), T('bark'),
            uv='cyl', name='root')
    add(blob_bm(1.6, 4, 2, 0.3), T('leaf_dead'), loc=(6.5, 0.5, 1.2), uv='box', name='deadleaves')


@prop('stog_siana', 'Wies', 'Stog siana')
def haystack():
    begin('stog_siana')
    add(blob_bm(2.4, 3, 2, 0.12, (1, 1, 1.1)), T('straw'), loc=(0, 0, 1.6), uv='box', tile=2, name='hay')
    add(cyl(0.08, 5.5, 6), T('wood'), loc=(0, 0, 2.7), uv='none', name='pole')


@prop('pole_pszenicy', 'Wies', 'Pole pszenicy (10x10)')
def wheat():
    begin('pole_pszenicy')
    rnd = random.Random(10)
    m = F('wheat', (214, 184, 106), 0.8)
    for i in range(9):
        for j in range(9):
            x, y = -4 + i + rnd.uniform(-0.3, 0.3), -4 + j + rnd.uniform(-0.3, 0.3)
            h = rnd.uniform(1.3, 1.8)
            add(cyl(0.05, h, 4), m, loc=(x, y, h / 2), rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), 0), uv='none', name='s')
            add(cyl(0.11, 0.4, 5), m, loc=(x, y, h + 0.1), uv='none', name='ear')


@prop('ul_slomiany', 'Wies', 'Slomiany ul na lawce')
def beehive():
    begin('ul_slomiany')
    add(box(3.0, 1.2, 0.2, 0.02), T('wood'), loc=(0, 0, 1.2), name='bench')
    for x in (-1.2, 1.2):
        add(box(0.2, 1.0, 1.1, 0.02), T('wood'), loc=(x, 0, 0.55), name='leg')
    for x in (-0.7, 0.7):
        add(lathe([(0, 0), (0.55, 0), (0.6, 0.5), (0.4, 1.0), (0, 1.15)], 16), T('straw'), loc=(x, 0, 1.3), uv='cyl',
            name='hive')


@prop('plot_wiklinowy', 'Wies', 'Plot z wikliny (6 st.)')
def wattle():
    begin('plot_wiklinowy')
    for x in range(-3, 4):
        add(cyl(0.1, 2.4, 6), T('wood_dark'), loc=(x, 0, 1.2), uv='none', name='stake')
    for z in (0.5, 1.0, 1.5, 2.0):
        pts = [(x * 0.5, 0.12 * (1 if (x + int(z * 2)) % 2 else -1), z) for x in range(-6, 7)]
        add(tube(pts, 0.07, res=3), T('wood'), uv='none', name='weave')


@prop('plot_drewniany', 'Wies', 'Plot drewniany z deszczulek (8 st.)')
def fence():
    begin('plot_drewniany')
    for x in range(-4, 5, 2):
        add(box(0.3, 0.3, 2.4, 0.03), T('wood_dark'), loc=(x, 0, 1.2), name='post')
    for z in (0.8, 1.8):
        add(box(8.2, 0.15, 0.3, 0.02), T('wood'), loc=(0, 0, z), name='rail')


@prop('drogowskaz', 'Wies', 'Drogowskaz z tabliczkami (ATENY / SPARTA)')
def signpost():
    begin('drogowskaz')
    add(box(0.3, 0.3, 4.0, 0.03), T('wood_dark'), loc=(0, 0, 2.0), name='post')
    for k, (z, rz) in enumerate(((3.4, 20), (2.8, -30))):
        add(C.bm_extrude([(0, -0.25), (1.6, -0.25), (1.9, 0), (1.6, 0.25), (0, 0.25)], 0.08), T('wood'),
            loc=(0, 0, z), rot=(90, 0, rz), uv='box', name='board')


@prop('kamien_milowy', 'Wies', 'Kamien milowy (stela przydrozna)')
def milestone():
    begin('kamien_milowy')
    add(cyl(0.45, 2.2, 14), T('blocks'), loc=(0, 0, 1.1), uv='cyl', name='stone')
    add(cyl(0.5, 0.3, 14), T('blocks'), loc=(0, 0, 0.15), uv='cyl', name='base')


@prop('kapliczka', 'Wies', 'Przydrozna kapliczka z lampka oliwna')
def shrine():
    begin('kapliczka')
    add(box(1.6, 1.2, 2.0, 0.05), T('plaster'), loc=(0, 0, 1.0), name='body')
    tri = C.bm_extrude([(-1.0, 0), (1.0, 0), (0, 0.8)], 1.4)
    C.bm_transform(tri, rot=(90, 0, 0))
    add(tri, T('roof'), loc=(0, 0, 2.0), uv='box', name='roof')
    add(box(0.8, 0.2, 0.9, 0.0), F('void', (14, 10, 10)), loc=(0, -0.55, 1.3), name='niche')
    add(C.bm_sphere(0.12, 8, 6), FIRE(), loc=(0, -0.5, 1.0), name='flame')
    marker('Light', (0, -0.8, 1.1), range=8, brightness=1, color=[255, 170, 80])


@prop('prasa_oliwna', 'Wies', 'Kamienna prasa do oliwy z kolem')
def olive_press():
    begin('prasa_oliwna')
    add(cyl(2.4, 1.2, 28), T('blocks_grey'), loc=(0, 0, 0.6), uv='cyl', name='basin')
    add(cyl(1.0, 0.8, 24), T('blocks_grey'), loc=(0.9, 0, 2.0), rot=(90, 0, 0), uv='box', name='wheel')
    add(cyl(0.15, 3.6, 8), T('wood'), loc=(0, 0, 2.0), rot=(0, 90, 0), uv='none', name='beam')
    add(cyl(0.2, 2.4, 8), T('wood'), loc=(0, 0, 1.8), uv='none', name='axis')
    add(cyl(2.0, 0.1, 24), F('oil', (120, 110, 30), 0.1), loc=(0, 0, 1.2), uv='none', name='oil')


@prop('zarna', 'Wies', 'Zarna (kamien mlynski)')
def millstone():
    begin('zarna')
    add(cyl(1.2, 0.5, 20), T('blocks_grey'), loc=(0, 0, 0.25), uv='box', name='lower')
    add(cyl(1.1, 0.45, 20), T('blocks_grey'), loc=(0, 0, 0.75), uv='box', name='upper')
    add(cyl(0.08, 0.9, 6), T('wood'), loc=(0.8, 0, 1.3), uv='none', name='handle')


@prop('piec_chlebowy', 'Wies', 'Gliniany piec chlebowy')
def oven():
    begin('piec_chlebowy')
    add(lathe([(0, 0), (2.0, 0), (1.9, 1.0), (1.4, 1.9), (0.6, 2.4), (0, 2.5)], 24), T('clay'), uv='box', tile=3, name='dome')
    add(box(1.0, 0.4, 0.8, 0.05), F('void', (14, 10, 10)), loc=(0, -1.85, 0.6), name='mouth')
    add(C.bm_sphere(0.35, 10, 6), FIRE(), loc=(0, -1.4, 0.5), name='embers')
    marker('Smoke', (0, 0, 2.6), size=1.5, opacity=0.3)


@prop('lampa_oliwna', 'Wies', 'Lampa oliwna na wysokim stojaku (latarnia uliczna)')
def oil_lamp_post():
    begin('lampa_oliwna')
    add(cyl(0.12, 5.0, 8), BRONZE(), loc=(0, 0, 2.5), uv='none', name='pole')
    add(cyl(0.4, 0.2, 12), BRONZE(), loc=(0, 0, 0.1), uv='none', name='foot')
    add(lathe([(0, 0), (0.45, 0.05), (0.5, 0.2), (0.2, 0.25), (0, 0.15)], 16), BRONZE(), loc=(0, 0, 5.0), uv='none', name='lamp')
    add(cyl(0.12, 0.35, 6, r2=0.0), FIRE(), loc=(0.35, 0, 5.4), uv='none', name='flame')
    marker('Light', (0.3, 0, 5.4), range=14, brightness=1.4, color=[255, 170, 80])


@prop('amfora_rozbita', 'Targ', 'Rozbita amfora (skorupy)')
def broken_amphora():
    begin('amfora_rozbita')
    from .p_market import amphora_bm
    bm = amphora_bm(2.0, 0)
    kill = [f for f in bm.faces if f.calc_center_median().z > 0.9 or (f.calc_center_median().x > 0.2 and f.calc_center_median().z > 0.4)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    add(bm, T('terracotta_painted', 0.6), loc=(0, 0, 0), rot=(70, 0, 20), uv='cyl', tile=3, name='half')
    rnd = random.Random(11)
    for k in range(7):
        add(C.bm_extrude([(0, 0), (0.4, 0.1), (0.3, 0.4), (0.05, 0.3)], 0.05), T('terracotta', 0.6),
            loc=(rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), 0.03), rot=(0, 0, rnd.uniform(0, 360)), uv='box', name='shard')


@prop('zwoj_liny', 'Port', 'Zwoj liny')
def rope_coil():
    begin('zwoj_liny')
    for k in range(5):
        add(C.bm_torus(0.9 - k * 0.12, 0.09, 24, 6), T('rope'), loc=(0, 0, 0.1 + k * 0.08), uv='box', tile=1, name='coil')


@prop('muszle', 'Port', 'Muszle i rozgwiazdy na piasku')
def shells():
    begin('muszle')
    rnd = random.Random(12)
    for k in range(6):
        add(lathe([(0, 0), (0.3, 0.02), (0.25, 0.15), (0, 0.2)], 10), F('shell', (240, 220, 200), 0.5),
            loc=(rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), 0.02), scale=(1, 0.8, 1), uv='none', name='shell')
    for k in range(3):
        pts = []
        for i in range(10):
            a = 2 * math.pi * i / 10
            r = 0.45 if i % 2 == 0 else 0.18
            pts.append((math.cos(a) * r, math.sin(a) * r))
        add(C.bm_extrude(pts, 0.08, 0.02, 1), F('starfish', (220, 110, 60), 0.6),
            loc=(rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5), 0.04), rot=(0, 0, rnd.uniform(0, 72)), uv='none', name='star')


@prop('skrzynia_skarbow', 'Unikaty', 'Skrzynia ze zlotymi monetami (easter egg)')
def treasure():
    begin('skrzynia_skarbow')
    add(box(2.4, 1.5, 1.2, 0.08), T('wood_dark'), loc=(0, 0, 0.6), name='chest')
    add(cyl(0.75, 2.4, 16), T('wood_dark'), loc=(0, 0.3, 1.5), rot=(0, 90, 0), uv='box', name='lid') if False else None
    add(box(2.5, 1.6, 0.15, 0.03), GOLD(), loc=(0, 0, 1.15), name='band')
    add(box(2.4, 1.5, 0.3, 0.06), T('wood_dark'), loc=(0, 0.9, 1.8), rot=(-70, 0, 0), name='lid_open')
    add(blob_bm(0.9, 3, 1, 0.2, (1.2, 0.7, 0.4)), GOLD(), loc=(0, 0, 1.3), uv='none', name='coins')
    rnd = random.Random(13)
    for k in range(12):
        add(cyl(0.15, 0.04, 10), GOLD(), loc=(rnd.uniform(-1.8, 1.8), rnd.uniform(-1.6, -0.9), 0.03),
            rot=(rnd.uniform(-20, 20), 0, 0), uv='none', name='coin')
    marker('Sparkles', (0, 0, 1.5), color=[255, 210, 90])


# ------------------------------------------------------------------ zima (Boreasz)
@prop('sosna_osniezona', 'Zima', 'Osniezona jodla')
def snowy_pine(name='sosna_osniezona', seed=1, h=12.0):
    begin(name)
    add(cyl(0.4, 2.5, 10), T('bark_dark'), loc=(0, 0, 1.25), uv='cyl', name='trunk')
    for k in range(5):
        t = k / 4
        r = 3.6 * (1 - t) + 0.8
        z = 2.0 + t * (h - 4)
        add(cyl(r, 2.8, 14, r2=0.3), T('pine_needles'), loc=(0, 0, z + 1.4), uv='cyl', tile=3, name=f'tier{k}')
        add(cyl(r * 0.92, 0.9, 14, r2=r * 0.35), T('snow'), loc=(0, 0, z + 2.0), uv='cyl', tile=3, name=f'snow{k}')


prop('sosna_osniezona_2', 'Zima', 'Osniezona jodla (mniejsza)')(lambda: snowy_pine('sosna_osniezona_2', 2, 8.0))


@prop('krysztaly_lodu', 'Zima', 'Krysztaly lodu (swieca blado)')
def ice_crystals():
    begin('krysztaly_lodu')
    rnd = random.Random(14)
    m = F('ice', (170, 220, 245), 0.05, 0.0, 0.6)
    for k in range(8):
        h = rnd.uniform(1.5, 5.0)
        add(cyl(0.5, h, 6, r2=0.0), m, loc=(rnd.uniform(-1.2, 1.2), rnd.uniform(-1.2, 1.2), h / 2),
            rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), rnd.uniform(0, 60)), uv='none', smooth=False, name='crystal')
    marker('Light', (0, 0, 2), range=12, brightness=1, color=[170, 220, 255])


@prop('zamarzniety_posag', 'Zima', 'Zamarzniety wojownik w bryle lodu')
def frozen_statue():
    begin('zamarzniety_posag')
    statue_fig((0, 0, 0), 0.9, T('rock_white'), 'spear')
    add(blob_bm(3.0, 5, 2, 0.12, (0.9, 0.7, 1.4)), F('ice_block', (190, 230, 250), 0.05), loc=(0, 0, 3.0), uv='none',
        smooth=False, name='ice')


@prop('sople_skala', 'Zima', 'Skala z soplami')
def icicles():
    begin('sople_skala')
    add(rock_bm(2.8, 15, 2, 0.3), T('rock_dark'), loc=(0, 0, 2.0), uv='box', smooth=False, name='rock')
    add(blob_bm(2.6, 6, 1, 0.2, (1.1, 1.1, 0.4)), T('snow'), loc=(0, 0, 3.6), uv='box', name='cap')
    rnd = random.Random(15)
    for k in range(10):
        a = rnd.uniform(0, 6.28)
        add(cyl(0.12, rnd.uniform(0.6, 1.4), 6, r2=0.0), F('ice', (170, 220, 245), 0.05, 0.0, 0.6),
            loc=(math.cos(a) * 2.4, math.sin(a) * 2.0, 2.6), rot=(180, 0, 0), uv='none', name='icicle')


@prop('zaspa', 'Zima', 'Zaspa sniezna')
def snowdrift():
    begin('zaspa')
    add(blob_bm(3.0, 9, 2, 0.15, (1.6, 1.0, 0.35)), T('snow'), loc=(0, 0, 0.3), uv='box', tile=4, name='drift')


# ------------------------------------------------------------------ podwodne (Atlantyda)
@prop('koral', 'Podwodne', 'Rafa koralowa (rozne kolory)')
def coral():
    begin('koral')
    rnd = random.Random(16)
    cols = [(230, 110, 100), (240, 170, 60), (180, 90, 200), (90, 180, 200)]
    for k in range(9):
        c = cols[k % 4]
        x, y = rnd.uniform(-2, 2), rnd.uniform(-2, 2)
        pts = [(x, y, 0)]
        for j in range(3):
            pts.append((pts[-1][0] + rnd.uniform(-0.5, 0.5), pts[-1][1] + rnd.uniform(-0.5, 0.5), pts[-1][2] + rnd.uniform(0.6, 1.0)))
        add(tube(pts, 0.25, radii=[1, 0.8, 0.6, 0.4]), F('coral' + str(c), c, 0.6), uv='none', name='branch')
    add(blob_bm(1.2, 4, 1, 0.4, (1.4, 1.2, 0.5)), F('coral_brain', (200, 160, 120), 0.7), loc=(1.5, -1.5, 0.4), name='brain')


@prop('wodorosty', 'Podwodne', 'Wodorosty (kepa)')
def seaweed():
    begin('wodorosty')
    rnd = random.Random(17)
    for k in range(10):
        x, y = rnd.uniform(-1.2, 1.2), rnd.uniform(-1.2, 1.2)
        h = rnd.uniform(2.5, 5.0)
        pts = [(x + 0.4 * math.sin(j * 1.3 + k), y + 0.3 * math.cos(j * 1.1), j * h / 4) for j in range(5)]
        add(tube(pts, 0.14, radii=[1, 0.9, 0.8, 0.6, 0.3]), T('leaf_ivy'), uv='box', name='weed')


@prop('zatopiony_posag', 'Podwodne', 'Zatopiony posag w wodorostach i muszlach')
def sunken_statue():
    begin('zatopiony_posag')
    statue_fig((0, 0, 0), 1.0, T('rock_mossy'), 'still', 0)
    add(blob_bm(0.8, 9, 1, 0.3), T('leaf_ivy'), loc=(0.3, -0.4, 4.6), name='weed_head')
    add(blob_bm(0.9, 10, 1, 0.3), T('leaf_ivy'), loc=(-0.6, 0.2, 1.0), name='weed_leg')


@prop('babelki', 'Podwodne', 'Zrodlo babelkow (marker efektu)')
def bubbles():
    begin('babelki')
    add(rock_bm(0.8, 18, 1, 0.3), T('rock_mossy'), loc=(0, 0, 0.3), uv='box', smooth=False, name='vent')
    for k in range(6):
        add(C.bm_sphere(0.12 + k * 0.03, 10, 6), F('bubble', (200, 240, 255), 0.05), loc=(0.1 * k, 0, 1.0 + k * 0.8), name='b')
    marker('Bubbles', (0, 0, 0.8))


# ------------------------------------------------------------------ podziemia (Hades)
@prop('pochodnia_duchow', 'Podziemia', 'Pochodnia z zielonym ogniem duchow')
def ghost_torch():
    begin('pochodnia_duchow')
    add(cyl(0.18, 4.0, 8), T('basalt'), loc=(0, 0, 2.0), uv='cyl', name='pole')
    add(lathe([(0, 0), (0.5, 0.1), (0.6, 0.5), (0, 0.3)], 16), T('iron'), loc=(0, 0, 4.0), uv='none', name='cup')
    add(cyl(0.4, 1.1, 8, r2=0.0), GLOW('ghostfire', (100, 255, 150), 8), loc=(0, 0, 4.9), uv='none', name='flame')
    marker('Fire', (0, 0, 4.7), size=2, heat=4, color=[100, 255, 150])
    marker('Light', (0, 0, 5.0), range=16, brightness=2, color=[100, 255, 150])


@prop('brama_kosci', 'Podziemia', 'Brama z kosci i czaszek (spawn w podziemiach)')
def bone_gate():
    begin('brama_kosci')
    bone = F('bone', (226, 214, 186), 0.6)
    for sx in (-1, 1):
        add(cyl(1.2, 10, 10), T('basalt'), loc=(sx * 5, 0, 5), uv='cyl', name='pillar')
        for k in range(5):
            add(C.bm_sphere(0.5, 12, 8), bone, loc=(sx * 5, -1.1, 2 + k * 1.8), scale=(1, 1, 0.95), name='skull')
    pts = [(-5, 0, 10), (-3, 0, 13), (0, 0, 14), (3, 0, 13), (5, 0, 10)]
    for k in range(3):
        add(tube([(p[0], p[1] + (k - 1) * 0.5, p[2] + k * 0.2) for p in pts], 0.3), bone, uv='none', name='rib')
    add(box(8.4, 0.3, 9.6, 0.0), GLOW('hades_portal', (90, 255, 140), 3), loc=(0, 0, 5.0), uv='none', name='portal')
    marker('Portal', (0, 0, 5), color=[90, 255, 140])


@prop('szkielet', 'Podziemia', 'Lezacy szkielet wojownika z tarcza')
def skeleton():
    begin('szkielet')
    bone = F('bone', (226, 214, 186), 0.6)
    add(C.bm_sphere(0.35, 12, 8), bone, loc=(-1.4, 0, 0.3), name='skull')
    for k in range(5):
        add(C.bm_torus(0.35, 0.05, 12, 4), bone, loc=(-0.6 + k * 0.22, 0, 0.3), rot=(0, 90, 0), name='rib')
    for sy in (-0.3, 0.3):
        add(cyl(0.06, 1.6, 6), bone, loc=(1.2, sy, 0.1), rot=(0, 90, 0), uv='none', name='leg')
        add(cyl(0.05, 1.2, 6), bone, loc=(-0.4, sy * 2.5, 0.1), rot=(0, 90, 30 * sy), uv='none', name='arm')
    add(cyl(0.9, 0.12, 20), BRONZE(), loc=(0.2, 1.4, 0.4), rot=(70, 0, 0), name='shield')


@prop('klatka', 'Podziemia', 'Wiszaca zelazna klatka')
def cage():
    begin('klatka')
    add(box(0.4, 0.4, 7, 0.02), T('wood_dark'), loc=(0, 0, 3.5), name='post')
    add(box(3.5, 0.3, 0.3, 0.02), T('wood_dark'), loc=(1.6, 0, 7), name='arm')
    add(cyl(0.04, 1.2, 4), T('iron'), loc=(3.0, 0, 6.3), uv='none', name='chain')
    for k in range(8):
        a = 2 * math.pi * k / 8
        add(cyl(0.05, 2.4, 4), T('iron'), loc=(3.0 + math.cos(a) * 0.9, math.sin(a) * 0.9, 4.5), uv='none', name='bar')
    for z in (3.3, 5.7):
        add(C.bm_torus(0.9, 0.06, 16, 4), T('iron'), loc=(3.0, 0, z), name='ring')


@prop('lancuchy_mur', 'Podziemia', 'Mur z lancuchami i kajdanami')
def chain_wall():
    begin('lancuchy_mur')
    add(box(6, 1.2, 5, 0.08), T('blocks_dark'), loc=(0, 0, 2.5), uv='box', tile=3, name='wall')
    for x in (-1.5, 1.5):
        for k in range(6):
            add(C.bm_torus(0.15, 0.04, 10, 4), T('iron_rusty'), loc=(x, -0.65, 4.0 - k * 0.25), rot=(90 * (k % 2), 0, 0), name='link')
        add(C.bm_torus(0.22, 0.06, 12, 4), T('iron_rusty'), loc=(x, -0.65, 2.4), rot=(90, 0, 0), name='cuff')


@prop('czaszka_na_palu', 'Podziemia', 'Czaszka na palu (ostrzezenie)')
def skull_pike():
    begin('czaszka_na_palu')
    add(cyl(0.1, 4.0, 6, r2=0.03), T('wood_dark'), loc=(0, 0, 2.0), uv='none', name='pike')
    add(C.bm_sphere(0.4, 12, 8), F('bone', (226, 214, 186), 0.6), loc=(0, 0, 3.8), scale=(1, 1.1, 0.95), name='skull')
    for sx in (-1, 1):
        add(C.bm_sphere(0.1, 8, 4), GLOW('skull_eye', (100, 255, 150), 5), loc=(sx * 0.14, -0.33, 3.85), name='eye')


@prop('spalony_dom', 'Podziemia', 'Ruiny spalonego domu')
def burnt_house():
    begin('spalony_dom')
    for sx, sy, w, d, h in ((-4.5, 0, 0.8, 8, 4.5), (4.5, 0, 0.8, 8, 2.5), (0, 4, 9, 0.8, 5.0), (-2.5, -4, 4, 0.8, 3.0)):
        add(box(w, d, h, 0.06), T('wall_rubble'), loc=(sx, sy, h / 2), uv='box', tile=3, name='wall')
    rnd = random.Random(19)
    for k in range(6):
        add(box(rnd.uniform(2, 4), 0.35, 0.35, 0.02), T('wood_dark'),
            loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), 0.3 + rnd.uniform(0, 2)),
            rot=(rnd.uniform(-30, 30), rnd.uniform(-30, 30), rnd.uniform(0, 180)), name='beam')
    add(cyl(4.0, 0.1, 24), T('ash'), loc=(0, 0, 0.05), uv='box', name='ash')
    marker('Smoke', (0, 0, 2), size=3, opacity=0.3)


# ------------------------------------------------------------------ oblezenie (Troja) i wojsko
@prop('wieza_oblezenicza', 'Wojsko', 'Drewniana wieza oblezenicza na kolach')
def siege_tower():
    begin('wieza_oblezenicza')
    add(box(6, 6, 16, 0.1), T('wood'), loc=(0, 0, 9), uv='box', tile=3, name='frame')
    add(box(6.3, 6.3, 0.5, 0.05), T('wood_dark'), loc=(0, 0, 17.2), name='top')
    for sx in (-2.6, 2.6):
        for sy in (-2.6, 2.6):
            add(cyl(1.0, 0.5, 16), T('wood_dark'), loc=(sx * 1.05, sy, 1.0), rot=(0, 90, 0), name='wheel')
    for k in range(5):
        add(box(6.4, 0.4, 0.4, 0.02), T('wood_dark'), loc=(0, -3.1, 3 + k * 3), name='beam')
    add(box(4.0, 0.3, 5.0, 0.03), T('wood_dark'), loc=(0, -3.6, 15.0), rot=(-20, 0, 0), name='ramp')
    for x in (-2.4, -1.2, 0, 1.2, 2.4):
        add(box(1.0, 0.8, 1.2, 0.05), T('wood'), loc=(x, 0, 18.0), name='merlon')
    add(box(4.0, 0.15, 3.0, 0.0), T('leather'), loc=(0, -3.05, 8.0), name='hides')


@prop('palisada', 'Wojsko', 'Palisada z zaostrzonych pali (8 st.)')
def palisade():
    begin('palisada')
    rnd = random.Random(20)
    for k in range(13):
        h = rnd.uniform(4.5, 5.5)
        add(cyl(0.32, h, 8), T('bark'), loc=(-3.9 + k * 0.65, 0, h / 2), uv='cyl', name='stake')
        add(cyl(0.32, 0.8, 8, r2=0.0), T('wood_pale'), loc=(-3.9 + k * 0.65, 0, h + 0.4), uv='none', name='tip')
    add(box(8.4, 0.3, 0.3, 0.02), T('rope'), loc=(0, -0.3, 3.0), name='lash')


@prop('mur_z_wieza', 'Wojsko', 'Fragment murow miasta z wieza (Troja)')
def city_wall_tower():
    begin('mur_z_wieza')
    add(box(20, 5, 12, 0.15), T('wall_cyclopean'), loc=(0, 0, 6), uv='box', tile=6, name='wall')
    for x in range(-9, 10, 2):
        add(box(1.4, 5.2, 1.4, 0.05), T('blocks'), loc=(x, 0, 12.7), name='merlon')
    add(box(9, 9, 18, 0.15), T('wall_cyclopean'), loc=(12, 2, 9), uv='box', tile=6, name='tower')
    for k in range(4):
        for j in range(-3, 4, 2):
            p = [(12 + j, -2.5, 18.7), (12 + j, 6.5, 18.7), (7.5, 2 + j, 18.7), (16.5, 2 + j, 18.7)][k]
            add(box(1.3, 1.3, 1.4, 0.05), T('blocks'), loc=p, name='merlon')
    add(box(1.0, 0.3, 2.4, 0.0), F('void', (14, 10, 10)), loc=(12, -2.6, 13), name='window')
    for x in (-6, 4):
        add(box(1.4, 0.1, 4.0, 0.0), T('cloth_red'), loc=(x, -2.6, 9.0), uv='box', tile=2, name='banner')


@prop('namiot_dowodcy', 'Wojsko', 'Duzy namiot dowodcy z proporcami')
def commander_tent():
    begin('namiot_dowodcy')
    add(cyl(5.0, 4.0, 24), T('cloth_red'), loc=(0, 0, 2.0), uv='cyl', tile=4, name='wall')
    add(cyl(5.4, 3.6, 24, r2=0.3), T('cloth'), loc=(0, 0, 5.8), uv='cyl', tile=4, name='roof')
    add(cyl(0.15, 9.5, 8), T('wood'), loc=(0, 0, 4.75), uv='none', name='pole')
    add(box(2.4, 0.06, 1.2, 0.0), T('cloth_red'), loc=(1.2, 0, 8.9), name='pennant')
    add(box(2.0, 0.2, 3.0, 0.0), F('void', (30, 20, 20)), loc=(0, -4.95, 1.5), name='door')


@prop('sztandar', 'Wojsko', 'Sztandar z orlem na drzewcu')
def standard():
    begin('sztandar')
    add(cyl(0.12, 8, 8), T('wood_dark'), loc=(0, 0, 4), uv='none', name='pole')
    add(box(3.0, 0.15, 0.15, 0.0), GOLD(), loc=(0, 0, 7.0), name='bar')
    bm = C.bm_grid(6, 6, 2.6, 3.6)
    C.bm_map(bm, lambda co: (co.x, 0.15 * math.sin(co.x * 2 + co.z), co.z))
    add(bm, T('cloth_purple'), loc=(0, 0, 6.9), uv='box', tile=3, name='banner')
    add(C.bm_sphere(0.4, 12, 8), GOLD(), loc=(0, 0, 8.3), name='eagle')


@prop('trofeum', 'Wojsko', 'Tropaion - zbroja wroga na palu (pomnik zwyciestwa)')
def tropaion():
    begin('trofeum')
    add(cyl(0.18, 6, 8), T('bark'), loc=(0, 0, 3), uv='cyl', name='trunk')
    add(box(3.4, 0.3, 0.3, 0.0), T('bark'), loc=(0, 0, 4.6), name='cross')
    add(box(2.0, 1.0, 2.2, 0.2), BRONZE(), loc=(0, 0, 4.0), name='cuirass')
    add(lathe([(0, 0), (0.7, 0), (0.75, 0.6), (0.5, 1.0), (0, 1.1)], 16), BRONZE(), loc=(0, 0, 5.4), uv='none', name='helmet')
    add(cyl(1.2, 0.15, 20), F('shield_red', (170, 40, 30), 0.5), loc=(1.4, -0.2, 3.6), rot=(80, 0, 20), name='shield')
    add(cyl(0.05, 5.0, 6), T('wood'), loc=(-1.2, 0, 3.6), rot=(0, -30, 0), uv='none', name='spear')


@prop('pole_bitwy', 'Wojsko', 'Wlocznie wbite w ziemie i porzucone tarcze')
def battlefield():
    begin('pole_bitwy')
    rnd = random.Random(21)
    for k in range(8):
        add(cyl(0.05, 4.0, 6), T('wood'), loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), 1.6),
            rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), 0), uv='none', name='spear')
    for k in range(4):
        add(cyl(1.0, 0.15, 20), F('shield' + str(k), [(170, 40, 30), (40, 70, 140), (150, 110, 40), (60, 60, 64)][k], 0.5),
            loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), 0.1), rot=(rnd.uniform(-10, 10), rnd.uniform(-10, 10), 0), name='shield')
    for k in range(5):
        add(cyl(0.03, 1.6, 4), T('wood'), loc=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), 0.5),
            rot=(rnd.uniform(-50, 50), rnd.uniform(-50, 50), 0), uv='none', name='arrow')


@prop('stos_tarcz', 'Wojsko', 'Stos tarcz hoplitow')
def shield_pile():
    begin('stos_tarcz')
    for k in range(5):
        add(lathe([(0, 0), (1.3, 0), (1.35, 0.1), (0, 0.35)], 24), BRONZE(), loc=(k * 0.1, k * 0.05, 0.05 + k * 0.35),
            rot=(0, 0, k * 30), uv='box', name='shield')
    add(lathe([(0, 0), (0.7, 0), (0.75, 0.6), (0.5, 1.0), (0, 1.1)], 16), BRONZE(), loc=(0.4, 0.2, 1.9), uv='none',
        name='helmet')


@prop('katapulta', 'Wojsko', 'Katapulta (dekoracja oblezenia)')
def catapult():
    begin('katapulta')
    add(box(3.2, 6.0, 0.6, 0.05), T('wood'), loc=(0, 0, 1.0), name='base')
    for sx in (-1, 1):
        add(cyl(0.9, 0.4, 14), T('wood_dark'), loc=(sx * 1.8, -2.0, 0.9), rot=(0, 90, 0), name='wheel')
        add(cyl(0.9, 0.4, 14), T('wood_dark'), loc=(sx * 1.8, 2.0, 0.9), rot=(0, 90, 0), name='wheel')
        add(box(0.4, 0.4, 3.6, 0.02), T('wood'), loc=(sx * 1.2, 0.5, 2.8), rot=(0, sx * -8, 0), name='upright')
    add(box(3.0, 0.5, 0.5, 0.02), T('wood'), loc=(0, 0.5, 4.5), name='crossbar')
    add(box(0.4, 0.4, 5.5, 0.02), T('wood'), loc=(0, -0.8, 2.6), rot=(-60, 0, 0), name='arm')
    add(lathe([(0, 0), (0.6, 0.1), (0.7, 0.4), (0, 0.2)], 12), T('rope'), loc=(0, -3.2, 1.3), uv='none', name='bucket')
    add(C.bm_sphere(0.45, 10, 8), T('rock'), loc=(0, -3.2, 1.7), name='stone')


# ------------------------------------------------------------------ Olimpia, Delfy, posagi
@prop('trybuny_stadionu', 'Architektura', 'Kamienne trybuny (segment teatru/stadionu)')
def stands():
    begin('trybuny_stadionu')
    for i in range(7):
        add(box(16, 1.6, 0.6, 0.04), T('blocks'), loc=(0, i * 1.5, 0.3 + i * 0.6), uv='box', tile=4, name=f'row{i}')
    for sx in (-1, 1):
        add(box(1.0, 11, 4.6, 0.05), T('blocks'), loc=(sx * 8.5, 4.5, 2.3), name='side')


@prop('kolumnada_stoa', 'Architektura', 'Stoa - kolumnada z dachem (16 st.)')
def stoa():
    begin('kolumnada_stoa')
    steps(18, 7, 2, 0.5, 0.5)
    for k in range(5):
        column((-7.2 + k * 3.6, -2.0, 1.0), 7.0, 0.55, 'doric', segs=24, name=f'c{k}')
    add(box(17, 1.0, 7.0, 0.05), LIME(), loc=(0, 2.6, 4.5), uv='box', tile=4, name='backwall')
    add(box(17.4, 6.4, 0.8, 0.05), MARBLE(), loc=(0, 0, 8.6), name='architrave')
    for sx in (-1, 1):
        add(box(9.4, 7.0, 0.35, 0.04), T('roof'), loc=(0, sx * 1.6, 9.6), rot=(sx * 14, 0, 0), uv='box', tile=3, name='roof')


@prop('akwedukt', 'Architektura', 'Fragment akweduktu (luki)')
def aqueduct():
    begin('akwedukt')
    for k in range(3):
        x = -8 + k * 8
        for sx in (-1, 1):
            add(box(1.8, 3, 12, 0.08), T('blocks'), loc=(x + sx * 3.1, 0, 6), uv='box', tile=4, name='pier')
        pts = [(x - 2.2 + 4.4 * i / 8, 0, 12 + 2.2 * math.sin(math.pi * i / 8)) for i in range(9)]
        add(tube(pts, 0.9, res=3), T('blocks'), uv='box', tile=4, name='arch')
    add(box(26, 3.2, 2.0, 0.08), T('blocks'), loc=(0, 0, 15.0), uv='box', tile=4, name='channel')
    add(box(26, 1.6, 0.2, 0.0), F('aq_water', (60, 140, 170), 0.05), loc=(0, 0, 16.05), name='water')


@prop('omfalos', 'Architektura', 'Omfalos - pepek swiata z Delf')
def omphalos():
    begin('omfalos')
    add(box(3, 3, 1.0, 0.05), T('blocks_marble'), loc=(0, 0, 0.5), name='base')
    add(lathe([(0, 0), (1.1, 0), (1.15, 0.8), (0.8, 1.7), (0, 2.0)], 24), MARBLE(), loc=(0, 0, 1.0), uv='box', name='stone')
    for k in range(6):
        add(C.bm_torus(1.0 - k * 0.05, 0.05, 20, 4), GOLD(), loc=(0, 0, 1.2 + k * 0.25), scale=(1, 1, 1), name='net')


@prop('trojnog_delficki', 'Architektura', 'Zloty trojnog Pytii nad szczelina z oparami')
def delphic_tripod():
    begin('trojnog_delficki')
    add(cyl(1.6, 0.4, 24), T('blocks_grey'), loc=(0, 0, 0.2), uv='box', name='floor')
    add(box(2.0, 0.3, 0.1, 0.0), F('void', (14, 10, 10)), loc=(0, 0, 0.41), name='chasm')
    for k in range(3):
        a = 2 * math.pi * k / 3
        add(tube([(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.4), (math.cos(a) * 0.6, math.sin(a) * 0.6, 3.0)], 0.07), GOLD(),
            uv='none', name='leg')
    add(lathe([(0, 0), (0.9, 0.1), (1.0, 0.5), (0, 0.3)], 20), GOLD(), loc=(0, 0, 3.0), uv='none', name='bowl')
    marker('Smoke', (0, 0, 0.5), size=2, opacity=0.35, color=[200, 170, 255])


@prop('skarbczyk', 'Architektura', 'Skarbczyk (maly budynek z kolumnami, Delfy)')
def treasury():
    begin('skarbczyk')
    z = steps(8, 10, 2, 0.5, 0.5)
    add(box(6.4, 7.0, 6.0, 0.06), T('blocks_marble'), loc=(0, 1.0, z + 3.0), uv='box', tile=4, name='cella')
    for x in (-1.4, 1.4):
        column((x, -3.4, z), 6.0, 0.45, 'ionic', segs=24)
    add(box(6.8, 9.0, 0.8, 0.05), MARBLE(), loc=(0, 0, z + 6.6), name='architrave')
    tri = C.bm_extrude([(-3.6, 0), (3.6, 0), (0, 1.6)], 9.0)
    C.bm_transform(tri, rot=(90, 0, 0))
    add(tri, MARBLE(), loc=(0, 0, z + 7.0), uv='box', tile=4, name='pediment')


@prop('dyskobol', 'Architektura', 'Posag dyskobola (Olimpia)')
def discobolus():
    begin('dyskobol')
    add(box(3, 3, 2.0, 0.08), BLOCKS(), loc=(0, 0, 1.0), name='ped')
    statue_fig((0, 0, 2.0), 1.0, BRONZE(), 'arms_up', 30)
    add(cyl(0.5, 0.12, 20), BRONZE(), loc=(-1.6, 0.6, 7.0), rot=(70, 0, 0), name='discus')


@prop('kora_posag', 'Architektura', 'Kora - posag dziewczyny w peplosie (malowany)')
def kore():
    begin('kora_posag')
    add(box(2.4, 2.4, 1.6, 0.08), BLOCKS(), loc=(0, 0, 0.8), name='ped')
    statue_fig((0, 0, 1.6), 0.9, MARBLE(), 'still')
    add(cyl(1.15, 3.6, 24, r2=0.95), T('plaster_red'), loc=(0, 0, 3.4), uv='cyl', name='peplos')


@prop('posag_lwa', 'Architektura', 'Marmurowy lew (Aleja Lwow, Delos)')
def lion():
    begin('posag_lwa')
    add(box(5, 2.2, 1.0, 0.08), BLOCKS(), loc=(0, 0, 0.5), name='ped')
    add(blob_bm(1.0, 3, 2, 0.08, (2.0, 0.9, 1.0)), MARBLE(), loc=(0.3, 0, 2.1), name='body')
    add(blob_bm(0.9, 4, 2, 0.15, (1, 1, 1.1)), MARBLE(), loc=(-1.8, 0, 3.0), name='mane')
    add(box(0.7, 0.6, 0.6, 0.2), MARBLE(), loc=(-2.5, 0, 2.9), name='snout')
    for sx in (-1.3, 1.6):
        for sy in (-0.5, 0.5):
            add(box(0.45, 0.45, 1.5, 0.12), MARBLE(), loc=(sx, sy, 1.5), name='leg')
    add(tube([(2.2, 0, 2.2), (2.9, 0, 1.6), (3.1, 0, 2.3)], 0.1), MARBLE(), uv='none', name='tail')


@prop('sfinks_naksyjski', 'Architektura', 'Sfinks Naksyjczykow na jonskiej kolumnie')
def sphinx():
    begin('sfinks_naksyjski')
    column((0, 0, 0), 10, 0.7, 'ionic', segs=24)
    z = 11.2
    add(blob_bm(0.8, 6, 2, 0.08, (1.8, 0.8, 0.9)), MARBLE(), loc=(0.3, 0, z + 0.8), name='body')
    add(C.bm_sphere(0.55, 14, 10), MARBLE(), loc=(-1.0, 0, z + 1.9), name='head')
    for sx in (-1, 1):
        w = C.bm_extrude([(0, 0), (1.0, 0.6), (2.0, 1.6), (1.6, 0.4), (0.6, -0.2)], 0.12, 0.03, 1)
        C.bm_map(w, lambda co, sx=sx: (co.x, sx * (co.z + 0.5), co.y))
        add(recalc(w), MARBLE(), loc=(0.0, 0, z + 1.1), uv='none', name='wing')


@prop('atlas', 'Unikaty', 'Atlas dzwigajacy niebo (zloty globus)')
def atlas():
    begin('atlas')
    add(box(4, 4, 1.6, 0.08), BLOCKS(), loc=(0, 0, 0.8), name='ped')
    statue_fig((0, 0, 1.6), 1.1, BRONZE(), 'arms_up')
    add(C.bm_sphere(2.6, 32, 16), GOLD(), loc=(0, 0, 10.6), name='globe')
    for k in range(3):
        add(C.bm_torus(2.65, 0.06, 32, 4), F('star_band', (40, 60, 120), 0.4), loc=(0, 0, 10.6), rot=(k * 60, 30, 0), name='band')


@prop('maczuga_heraklesa', 'Unikaty', 'Maczuga i skora lwa nemejskiego Heraklesa')
def herakles_club():
    begin('maczuga_heraklesa')
    add(rock_bm(1.6, 22, 2, 0.25), T('rock_warm'), loc=(0, 0, 0.5), uv='box', smooth=False, name='rock')
    add(cyl(0.45, 4.0, 10, r2=0.18), T('bark_dark'), loc=(0.5, 0, 2.4), rot=(0, 20, 0), uv='cyl', name='club')
    for k in range(6):
        add(C.bm_sphere(0.15, 6, 4), T('bark_dark'), loc=(0.9 + 0.1 * k, 0.3 * (k % 2 - 0.5), 3.4 + 0.2 * k), name='knot')
    add(blob_bm(1.4, 6, 2, 0.2, (1.4, 1.0, 0.25)), F('lion_pelt', (190, 140, 70), 0.9), loc=(-0.6, 0.3, 1.5), rot=(0, 30, 0),
        name='pelt')


@prop('luk_teczy', 'Olimp', 'Teczowy luk Iris (portal Olimpu)')
def rainbow():
    begin('luk_teczy')
    cols = [(230, 60, 60), (240, 150, 50), (240, 220, 70), (90, 190, 90), (70, 130, 230), (150, 90, 210)]
    for k, c in enumerate(cols):
        R_ = 9 - k * 0.55
        pts = [(math.cos(math.pi * i / 16) * R_, 0, math.sin(math.pi * i / 16) * R_) for i in range(17)]
        add(tube(pts, 0.3, res=3), GLOW('rainbow' + str(k), c, 1.5), uv='none', name='band')
    for sx in (-1, 1):
        from .p_themes import cloud  # noqa
        add(blob_bm(2.4, 30 + sx, 2, 0.15, (1.3, 1, 0.8)), F('cloud', (246, 248, 255), 0.95), loc=(sx * 7.5, 0, 0.5), name='cloud')


@prop('zlote_wrota_olimpu', 'Olimp', 'Zlote wrota Olimpu (wielka brama)')
def olympus_gate():
    begin('zlote_wrota_olimpu')
    for sx in (-1, 1):
        column((sx * 7, 0, 0), 14, 1.2, 'ionic', mat=MARBLE(), segs=32)
        add(box(5.6, 0.6, 12.0, 0.08), GOLD(), loc=(sx * 3.0, 0.2, 6.2), rot=(0, 0, sx * -25), name='door')
        for k in range(4):
            add(cyl(0.3, 0.2, 12), GOLD(), loc=(sx * 3.0 + sx * 0.9 * math.cos(math.radians(25)), -0.2 - 0.9 * math.sin(math.radians(25)) * sx * 0, 2.5 + k * 2.6),
                rot=(90, 0, 0), name='stud')
    add(box(17, 2.6, 1.6, 0.08), MARBLE(), loc=(0, 0, 16.0), name='lintel')
    add(box(17.4, 2.8, 1.0, 0.05), T('meander_gold'), loc=(0, 0, 17.3), uv='box', tile=2.2, name='frieze')
    add(cyl(1.6, 0.4, 24), GOLD(), loc=(0, -1.4, 17.0), rot=(90, 0, 0), name='sun_disc')
    marker('Light', (0, -3, 12), range=30, brightness=2, color=[255, 220, 140])


@prop('posag_pegaza', 'Olimp', 'Posag Pegaza na postumencie')
def pegasus_statue():
    begin('posag_pegaza')
    m = MARBLE()
    add(box(5, 3, 2, 0.08), BLOCKS(), loc=(0, 0, 1), name='ped')
    add(blob_bm(1.0, 2, 2, 0.05, (1.9, 0.8, 0.9)), m, loc=(0, 0, 4.2), name='body')
    add(box(0.8, 0.7, 2.2, 0.2), m, loc=(-1.8, 0, 5.4), rot=(0, 30, 0), name='neck')
    add(box(1.3, 0.6, 0.6, 0.2), m, loc=(-2.6, 0, 6.4), rot=(0, 10, 0), name='head')
    for sx, rx in ((-1.2, -30), (1.2, 0)):
        for sy in (-0.45, 0.45):
            add(box(0.35, 0.35, 2.4, 0.1), m, loc=(sx, sy, 2.6), rot=(0, rx, 0), name='leg')
    for sy in (-1, 1):
        w = C.bm_extrude([(0, 0), (1.0, 1.0), (1.4, 3.0), (2.4, 4.4), (1.0, 3.2), (0.2, 1.4)], 0.12, 0.03, 1)
        C.bm_map(w, lambda co, sy=sy: (co.x * 0.8, sy * (co.y + 0.6), co.z * 0 + 4.6 + co.y * 0.5))
        add(recalc(w), GOLD(), loc=(-0.2, 0, 0.0), uv='none', name='wing')
