"""Roslinnosc i skaly."""
import math
import random

from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, rock_bm, blob_bm, box, cyl, tube, lathe, C)


# ------------------------------------------------------------------ drzewa
def _trunk(pts, r, mat='bark', radii=None):
    add(tube(pts, r, radii=radii or [1.0] + [0.75] * (len(pts) - 2) + [0.5]), T(mat), uv='cyl', tile=3, name='trunk')


def _canopy(centers, mat, seed=0, sub=2, amt=0.25):
    for i, (c, r, sq) in enumerate(centers):
        add(blob_bm(r, seed + i, sub, amt, sq), T(mat), loc=c, uv='box', tile=3, name=f'leaf{i}')


@prop('drzewo_oliwne', 'Rosliny', 'Drzewo oliwne: skrecony pien, srebrzysto-zielona korona')
def olive_tree(seed=1, s=1.0):
    begin(f'drzewo_oliwne' if seed == 1 else f'drzewo_oliwne_{seed}')
    rnd = random.Random(seed)
    _trunk([(0, 0, 0), (0.4 * s, 0.1, 2.2 * s), (-0.3 * s, 0.3, 4.0 * s), (0.2 * s, -0.2, 5.6 * s)], 0.75 * s,
           'bark_olive', radii=[1.2, 0.9, 0.75, 0.55])
    for k in range(3):
        a = k * 2.1 + rnd.random()
        _trunk([(0.1, 0, 4.0 * s), (math.cos(a) * 1.8 * s, math.sin(a) * 1.8 * s, 5.6 * s),
                (math.cos(a) * 2.8 * s, math.sin(a) * 2.8 * s, 6.4 * s)], 0.3 * s, 'bark_olive')
    cs = []
    for k in range(6):
        a = k * 1.05 + rnd.random() * 0.5
        rr = rnd.uniform(1.6, 2.8) * s
        cs.append(((math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(6.0, 7.6) * s), rnd.uniform(1.7, 2.4) * s,
                   (1.1, 1.1, 0.7)))
    cs.append(((0, 0, 8.0 * s), 2.6 * s, (1.2, 1.2, 0.7)))
    _canopy(cs, 'leaf_olive', seed)


for _i in (2, 3):
    prop(f'drzewo_oliwne_{_i}', 'Rosliny', 'Drzewo oliwne (wariant)')(lambda _i=_i: olive_tree(_i, 0.8 + 0.15 * _i))


@prop('cyprys', 'Rosliny', 'Cyprys: wysoki, smukly, ciemnozielony')
def cypress(seed=1, h=16.0):
    begin('cyprys' if seed == 1 else f'cyprys_{seed}')
    add(cyl(0.45, 2.0, 10), T('bark'), loc=(0, 0, 1.0), uv='cyl', tile=3, name='trunk')
    rnd = random.Random(seed)
    for k in range(6):
        t = k / 5
        r = (1.0 - t) * 2.0 + 0.5
        add(blob_bm(r, seed * 10 + k, 2, 0.2, (1, 1, 1.6)), T('leaf_dark'),
            loc=(rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 2.5 + t * (h - 4)), uv='box', tile=3,
            name=f'leaf{k}')


prop('cyprys_2', 'Rosliny', 'Cyprys nizszy')(lambda: cypress(2, 11.0))


@prop('sosna_parasolowa', 'Rosliny', 'Sosna pinia: wysoki pien, plaska szeroka korona')
def umbrella_pine(seed=1):
    begin('sosna_parasolowa' if seed == 1 else f'sosna_parasolowa_{seed}')
    _trunk([(0, 0, 0), (0.6, 0, 4), (1.2, 0.3, 8), (1.5, 0.4, 11)], 0.6, 'bark', radii=[1.2, 0.9, 0.7, 0.5])
    rnd = random.Random(seed)
    for k in range(4):
        a = k * 1.6
        _trunk([(1.4, 0.4, 10.5), (1.4 + math.cos(a) * 2.5, 0.4 + math.sin(a) * 2.5, 12.0)], 0.25, 'bark')
    cs = [((1.4, 0.4, 12.6), 4.2, (1.4, 1.4, 0.38))]
    for k in range(5):
        a = k * 1.25 + rnd.random()
        cs.append(((1.4 + math.cos(a) * 3.4, 0.4 + math.sin(a) * 3.4, 12.2 + rnd.uniform(-0.3, 0.5)),
                   rnd.uniform(2.0, 2.8), (1.3, 1.3, 0.45)))
    _canopy(cs, 'pine_needles', seed)


prop('sosna_parasolowa_2', 'Rosliny', 'Pinia (wariant)')(lambda: umbrella_pine(2))


@prop('platan', 'Rosliny', 'Platan: bujne liscie, gruby pien (gaje, place)')
def plane_tree(seed=1, mat='leaf_lush', name='platan'):
    begin(name)
    _trunk([(0, 0, 0), (0.2, 0.1, 3.5), (0, 0, 6.5)], 0.9, 'bark', radii=[1.3, 1.0, 0.8])
    rnd = random.Random(seed)
    for k in range(4):
        a = k * 1.57 + 0.4
        _trunk([(0, 0, 5.5), (math.cos(a) * 2.2, math.sin(a) * 2.2, 8.0)], 0.35, 'bark')
    cs = [((0, 0, 10.0), 4.0, (1.0, 1.0, 0.85))]
    for k in range(7):
        a = k * 0.9 + rnd.random()
        cs.append(((math.cos(a) * 3.2, math.sin(a) * 3.2, rnd.uniform(8.0, 10.5)), rnd.uniform(2.3, 3.2),
                   (1, 1, 0.85)))
    _canopy(cs, mat, seed + 30)


prop('drzewo_jesienne', 'Rosliny', 'Drzewo w kolorach jesieni (Olimp, gaje)')(
    lambda: plane_tree(4, 'leaf_autumn', 'drzewo_jesienne'))
prop('drzewo_kwitnace', 'Rosliny', 'Kwitnace drzewo migdalowe (rozowe kwiaty)')(
    lambda: plane_tree(5, 'leaf_blossom', 'drzewo_kwitnace'))


@prop('palma', 'Rosliny', 'Palma daktylowa (port, wybrzeze)')
def palm():
    begin('palma')
    pts = [(0, 0, 0), (0.6, 0, 4), (1.6, 0, 8), (2.8, 0, 11)]
    _trunk(pts, 0.55, 'bark_olive', radii=[1.1, 0.95, 0.85, 0.8])
    for k in range(8):
        add(cyl(0.62, 0.35, 10), T('bark'), loc=(0.15 * k * 0.6 + 0.0, 0, 1.2 * k + 0.6), uv='cyl', name=f'ring{k}') if k < 0 else None
    top = Vector((2.8, 0, 11))
    for k in range(9):
        a = k * 2 * math.pi / 9
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [top, top + d * 2.0 + Vector((0, 0, 1.2)), top + d * 4.0 + Vector((0, 0, 0.6)),
               top + d * 5.5 + Vector((0, 0, -1.2))]
        add(tube([tuple(p) for p in pts], 0.5, radii=[0.4, 1.0, 0.8, 0.15], res=5), T('leaf_lush'),
            scale=(1, 1, 1), uv='box', tile=2, name=f'frond{k}')
    for k in range(5):
        a = k * 1.3
        add(C.bm_sphere(0.35, 10, 6), F('dates', (150, 80, 30), 0.5),
            loc=(2.8 + math.cos(a) * 0.5, math.sin(a) * 0.5, 10.4), name=f'date{k}')


@prop('drzewo_spalone', 'Rosliny', 'Martwe, spalone drzewo (wulkan, cmentarz)')
def dead_tree():
    begin('drzewo_spalone')
    _trunk([(0, 0, 0), (0.3, 0, 3), (-0.2, 0.2, 6), (0.4, 0, 8.5)], 0.55, 'basalt', radii=[1.2, 0.9, 0.6, 0.3])
    rnd = random.Random(9)
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        z = rnd.uniform(3.5, 7)
        L = rnd.uniform(1.5, 3.2)
        _trunk([(0, 0, z), (math.cos(a) * L * 0.6, math.sin(a) * L * 0.6, z + L * 0.5),
                (math.cos(a) * L, math.sin(a) * L, z + L * 0.6)], 0.18, 'basalt')


# ------------------------------------------------------------------ krzewy, kwiaty, trawy
@prop('krzew', 'Rosliny', 'Okragly krzew')
def bush(seed=1, mat='leaf_lush', name='krzew', flowers=None, s=1.0):
    begin(name)
    rnd = random.Random(seed)
    for k in range(4):
        a = k * 1.7 + rnd.random()
        add(blob_bm(rnd.uniform(1.0, 1.5) * s, seed * 7 + k, 2, 0.25, (1, 1, 0.8)), T(mat),
            loc=(math.cos(a) * 0.9 * s, math.sin(a) * 0.9 * s, rnd.uniform(0.7, 1.2) * s), uv='box', tile=2,
            name=f'b{k}')
    if flowers:
        for k in range(18):
            a = rnd.uniform(0, 6.28)
            el = rnd.uniform(0.1, 1.1)
            r = 1.6 * s
            p = (math.cos(a) * r * math.cos(el), math.sin(a) * r * math.cos(el), 0.8 * s + r * 0.8 * math.sin(el))
            add(C.bm_sphere(0.16 * s, 8, 6), F('flower_' + str(flowers), flowers, 0.6), loc=p, name=f'f{k}')


prop('krzew_oleander', 'Rosliny', 'Oleander z rozowymi kwiatami')(
    lambda: bush(2, 'leaf_lush', 'krzew_oleander', (232, 110, 160)))
prop('krzew_ciemny', 'Rosliny', 'Ciemny krzew (bukszpan)')(lambda: bush(3, 'leaf_dark', 'krzew_ciemny'))
prop('krzew_oliwny', 'Rosliny', 'Niski krzew srebrzysty')(lambda: bush(4, 'leaf_olive', 'krzew_oliwny', s=0.8))
prop('lawenda', 'Rosliny', 'Kepa lawendy')(lambda: bush(5, 'leaf_vine', 'lawenda', (150, 110, 210), s=0.6))


@prop('kepa_trawy', 'Rosliny', 'Kepa wysokiej trawy (zdzbla)')
def grass_tuft(seed=1, name='kepa_trawy', col=(110, 140, 56), h=1.6):
    begin(name)
    rnd = random.Random(seed)
    m = F('blade_' + name, col, 0.7)
    for k in range(22):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0, 0.6)
        x, y = math.cos(a) * r, math.sin(a) * r
        lean = rnd.uniform(0.2, 0.7)
        hh = rnd.uniform(0.6, 1.0) * h
        bm = C.bm_extrude([(-0.06, 0), (0.06, 0), (0.0, hh)], 0.02)
        C.bm_transform(bm, rot=(90, 0, 0))
        add(bm, m, loc=(x, y, 0), rot=(lean * 30 * math.cos(a), lean * 30 * math.sin(a), math.degrees(a)),
            uv='none', name=f'blade{k}')


prop('kepa_trawy_sucha', 'Rosliny', 'Kepa suchej trawy')(lambda: grass_tuft(2, 'kepa_trawy_sucha', (190, 170, 96)))
prop('trzcina', 'Rosliny', 'Trzcina (brzeg wody)')(lambda: grass_tuft(3, 'trzcina', (120, 140, 70), 3.5))


@prop('kwiaty', 'Rosliny', 'Klomb kwiatow (maki, rumianki)')
def flowers():
    begin('kwiaty')
    rnd = random.Random(4)
    cols = [(220, 40, 40), (240, 240, 230), (250, 200, 60), (170, 90, 200)]
    stem = F('stem', (80, 120, 50), 0.7)
    for k in range(26):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 1.4)
        x, y = math.cos(a) * r, math.sin(a) * r
        h = rnd.uniform(0.5, 1.0)
        add(cyl(0.03, h, 5), stem, loc=(x, y, h / 2), uv='none', name=f's{k}')
        c = cols[rnd.randrange(len(cols))]
        add(C.bm_sphere(0.13, 8, 5), F('petal' + str(c), c, 0.6), loc=(x, y, h), scale=(1, 1, 0.5), name=f'p{k}')


@prop('opuncja', 'Rosliny', 'Opuncja (kaktus wysp greckich)')
def prickly_pear():
    begin('opuncja')
    rnd = random.Random(5)
    pads = [((0, 0, 0.8), 0, 0), ((0.5, 0, 1.8), 25, 20), ((-0.5, 0.1, 1.9), -30, -15), ((0.7, 0.2, 2.8), 40, 50),
            ((-0.2, -0.2, 2.9), -10, 100)]
    for i, (p, ry, rz) in enumerate(pads):
        add(C.bm_sphere(0.6, 12, 8), T('leaf_vine'), loc=p, rot=(0, ry, rz), scale=(1, 0.28, 1.25), uv='box', tile=2,
            name=f'pad{i}')
        add(C.bm_sphere(0.1, 8, 6), F('pear_fruit', (190, 60, 80), 0.5),
            loc=(p[0] + 0.2, p[1], p[2] + 0.7), name=f'fr{i}')


@prop('winorosl', 'Rosliny', 'Pergola z winorosla i winogronami')
def vine_trellis():
    begin('winorosl')
    w = T('wood')
    for x in (-3, 3):
        for y in (-1.5, 1.5):
            add(box(0.4, 0.4, 5), w, loc=(x, y, 2.5), name='post')
    for y in (-1.5, 1.5):
        add(box(6.8, 0.35, 0.35), w, loc=(0, y, 5.1), name='beam')
    for x in range(-3, 4):
        add(box(0.25, 3.8, 0.25), w, loc=(x, 0, 5.35), name='slat')
    rnd = random.Random(6)
    for k in range(10):
        add(blob_bm(rnd.uniform(0.8, 1.2), k, 2, 0.3, (1.3, 1, 0.5)), T('leaf_vine'),
            loc=(rnd.uniform(-3, 3), rnd.uniform(-1.5, 1.5), 5.7), uv='box', tile=2, name=f'v{k}')
    for k in range(6):
        x, y = rnd.uniform(-2.8, 2.8), rnd.uniform(-1.3, 1.3)
        for j in range(6):
            add(C.bm_sphere(0.12, 8, 6), F('grape', (90, 40, 110), 0.3),
                loc=(x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15), 4.9 - j * 0.12), name=f'g{k}{j}')


# ------------------------------------------------------------------ skaly
def _rock(name, mat, r, seed, sq=(1, 1, 0.75), n=1, spread=1.2, sub=2, rough=0.35):
    begin(name)
    rnd = random.Random(seed)
    for k in range(n):
        rr = r * (1 if k == 0 else rnd.uniform(0.35, 0.7))
        a = rnd.uniform(0, 6.28)
        d = 0 if k == 0 else r * spread * rnd.uniform(0.6, 1.0)
        add(rock_bm(rr, seed * 10 + k, sub, rough, 0.35, sq), T(mat), loc=(math.cos(a) * d, math.sin(a) * d, rr * 0.3),
            rot=(0, 0, rnd.uniform(0, 360)), uv='box', tile=4, smooth=False, name=f'r{k}')


prop('glaz', 'Skaly', 'Duzy glaz')(lambda: _rock('glaz', 'rock', 2.5, 1))
prop('glaz_2', 'Skaly', 'Glaz plaski')(lambda: _rock('glaz_2', 'rock', 2.2, 2, (1.3, 1, 0.5)))
prop('glaz_mech', 'Skaly', 'Glaz z mchem')(lambda: _rock('glaz_mech', 'rock_mossy', 2.4, 3))
prop('glaz_cieply', 'Skaly', 'Glaz piaskowcowy')(lambda: _rock('glaz_cieply', 'rock_warm', 2.4, 4))
prop('glaz_bialy', 'Skaly', 'Bialy wapien')(lambda: _rock('glaz_bialy', 'rock_white', 2.2, 5))
prop('skaly_grupa', 'Skaly', 'Grupa skal (jak w TDS)')(lambda: _rock('skaly_grupa', 'rock', 2.4, 6, n=5))
prop('skaly_grupa_mech', 'Skaly', 'Grupa skal z mchem')(lambda: _rock('skaly_grupa_mech', 'rock_mossy', 2.2, 7, n=4))
prop('kamyki', 'Skaly', 'Rozsypane kamyki')(lambda: _rock('kamyki', 'rock', 0.5, 8, n=9, spread=3.5, sub=1))
prop('kamyki_cieple', 'Skaly', 'Kamyki piaskowcowe')(lambda: _rock('kamyki_cieple', 'rock_warm', 0.5, 9, n=9, spread=3.5, sub=1))
prop('skala_wulkaniczna', 'Skaly', 'Skala bazaltowa')(lambda: _rock('skala_wulkaniczna', 'basalt', 2.6, 10, (1, 1, 1.0)))
prop('skala_wulkaniczna_grupa', 'Skaly', 'Grupa skal bazaltowych')(
    lambda: _rock('skala_wulkaniczna_grupa', 'basalt', 2.4, 11, (1, 1, 0.9), n=5))
prop('blok_klifu', 'Skaly', 'Wielki blok klifu (tlo, brzegi)')(
    lambda: _rock('blok_klifu', 'cliff', 8.0, 12, (1.3, 1, 1.1), sub=2, rough=0.3))
prop('blok_klifu_szary', 'Skaly', 'Wielki szary blok klifu')(
    lambda: _rock('blok_klifu_szary', 'cliff_grey', 8.0, 13, (1.2, 1, 1.2), sub=2, rough=0.3))


@prop('kolumny_bazaltowe', 'Skaly', 'Kolumny bazaltowe (heksagonalne)')
def basalt_columns():
    begin('kolumny_bazaltowe')
    rnd = random.Random(14)
    for k in range(14):
        a, r = rnd.uniform(0, 6.28), rnd.uniform(0, 2.5)
        h = rnd.uniform(2, 7)
        add(cyl(0.7, h, 6, bev=0.05), T('basalt'), loc=(math.cos(a) * r, math.sin(a) * r, h / 2),
            rot=(0, 0, rnd.uniform(0, 60)), uv='box', smooth=False, name=f'c{k}')


@prop('luk_skalny', 'Skaly', 'Skalny luk nad woda')
def rock_arch():
    begin('luk_skalny')
    pts = [(-8, 0, 0), (-7, 0, 6), (-3, 0, 10), (3, 0, 10), (7, 0, 6), (8, 0, 0)]
    add(tube(pts, 2.6, radii=[1.4, 1.1, 0.9, 0.9, 1.1, 1.4], res=8), T('cliff'), uv='box', tile=6, name='arch')
    for k, x in enumerate((-8, 8)):
        add(rock_bm(3.5, 20 + k, 2, 0.3), T('cliff'), loc=(x, 0, 1.5), uv='box', tile=6, smooth=False, name=f'foot{k}')


@prop('jaskinia', 'Skaly', 'Wejscie do jaskini (spawn wrogow)')
def cave():
    begin('jaskinia')
    for k in range(7):
        a = math.pi * k / 6
        add(rock_bm(3.2, 30 + k, 2, 0.3, 0.3, (1, 1, 1.1)), T('rock'),
            loc=(math.cos(a) * 7, 0, math.sin(a) * 7), uv='box', tile=5, smooth=False, name=f'r{k}')
    add(rock_bm(6.0, 40, 2, 0.25, 0.3, (1.6, 1.2, 0.8)), T('rock'), loc=(0, 3.5, 9), uv='box', tile=5,
        smooth=False, name='top')
    add(box(9, 0.5, 7, 0.1), F('cave_dark', (6, 6, 8), 0.9), loc=(0, 3.0, 3.5), name='dark')
