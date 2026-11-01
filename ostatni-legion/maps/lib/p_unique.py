"""Unikaty i easter eggi z mitologii - do chowania na mapach."""
import math
import random

from mathutils import Vector

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, C)
from .p_arch import column, statue_fig, MARBLE, BLOCKS


def trident_parts(loc, s=1.0, mat=None, tilt=(0, 0, 0)):
    x, y, z = loc
    mat = mat or GOLD()
    add(cyl(0.12 * s, 7.0 * s, 10), mat, loc=(x, y, z + 3.5 * s), rot=tilt, uv='none', name='shaft')
    add(box(1.8 * s, 0.25 * s, 0.25 * s, 0.05), mat, loc=(x, y, z + 7.0 * s), rot=tilt, name='cross')
    for k, dx in enumerate((-0.8, 0.0, 0.8)):
        h = 1.6 if k == 1 else 1.2
        add(cyl(0.1 * s, h * s, 8), mat, loc=(x + dx * s, y, z + (7.0 + h / 2) * s), rot=tilt, uv='none', name='prong')
        add(cyl(0.22 * s, 0.6 * s, 4, r2=0.0), mat, loc=(x + dx * s, y, z + (7.0 + h + 0.3) * s), rot=tilt,
            uv='none', name='tip')


@prop('trojzab_posejdona', 'Unikaty', 'Trojzab Posejdona wbity w skale (swieci)')
def trident_rock():
    begin('trojzab_posejdona')
    add(rock_bm(2.6, 31, 2, 0.3), T('rock_mossy'), loc=(0, 0, 0.8), uv='box', smooth=False, name='rock')
    trident_parts((0.2, 0, 0.6), 1.0, GOLD(), (8, 6, 0))
    add(C.bm_torus(1.2, 0.08, 24, 6), GLOW('sea', (90, 220, 255), 3), loc=(0.3, 0, 7.6), rot=(90, 0, 0), name='aura')
    marker('Light', (0.3, 0, 7.0), range=16, brightness=2, color=[90, 220, 255])
    marker('Sparkles', (0.3, 0, 7.0), color=[90, 220, 255])


@prop('fontanna_posejdona', 'Unikaty', 'Wielka fontanna z posagiem Posejdona i konmi morskimi')
def poseidon_fountain():
    begin('fontanna_posejdona')
    add(lathe([(0, 0), (8.5, 0), (8.6, 1.2), (8.0, 1.2), (8.0, 0.4), (0, 0.4)], 48), MARBLE(), uv='box', tile=3,
        name='basin')
    add(cyl(7.95, 0.1, 48), F('fountain_water', (60, 150, 175), 0.05), loc=(0, 0, 1.0), uv='none', name='water')
    add(cyl(2.2, 3.0, 24), BLOCKS(), loc=(0, 0, 2.0), uv='cyl', name='plinth')
    statue_fig((0, 0, 3.5), 1.1, BRONZE(), 'still')
    trident_parts((-1.8, 0, 3.5), 0.9, GOLD())
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        p = Vector((math.cos(a) * 4.8, math.sin(a) * 4.8, 1.0))
        pts = [p, p + Vector((0, 0, 1.6)), p + Vector((math.cos(a) * 0.8, math.sin(a) * 0.8, 2.6)),
               p + Vector((math.cos(a) * 1.4, math.sin(a) * 1.4, 2.4))]
        add(tube([tuple(q) for q in pts], 0.5, radii=[1.2, 1.0, 0.8, 0.5], res=6), BRONZE(), uv='box',
            name='seahorse')
        add(tube([tuple(p + Vector((0, 0, 0.2))), tuple(p + Vector((-math.cos(a) * 1.2, -math.sin(a) * 1.2, -0.6)))],
                 0.25, radii=[1, 0.3]), BRONZE(), uv='box', name='tail')
        marker('Water', tuple(p + Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, 2.4))))


@prop('puszka_pandory', 'Unikaty', 'Puszka Pandory (uchylona, fioletowy dym)')
def pandora():
    begin('puszka_pandory')
    add(box(3, 3, 1.4, 0.06), BLOCKS(), loc=(0, 0, 0.7), name='ped')
    add(box(1.8, 1.3, 1.1, 0.06), GOLD(), loc=(0, 0, 1.95), name='box')
    add(box(1.9, 1.4, 0.25, 0.04), GOLD(), loc=(0, 0.3, 2.75), rot=(-28, 0, 0), name='lid')
    for k, x in enumerate((-0.5, 0.5)):
        add(C.bm_sphere(0.12, 10, 6), F('ruby', (180, 20, 40), 0.1), loc=(x, -0.66, 2.0), name='gem')
    add(blob_bm(0.6, 5, 1, 0.3), GLOW('evil', (150, 60, 220), 3), loc=(0, 0, 3.2), scale=(1, 1, 1.6), name='smoke')
    marker('Smoke', (0, 0, 3.0), size=2, opacity=0.5, color=[150, 60, 220])


@prop('zlote_runo', 'Unikaty', 'Zlote runo na swietym debie (Argonauci)')
def golden_fleece():
    begin('zlote_runo')
    add(tube([(0, 0, 0), (0.3, 0, 3), (0, 0.2, 5.5)], 0.7, radii=[1.3, 1.0, 0.8]), T('bark'), uv='cyl', tile=3,
        name='trunk')
    add(tube([(0, 0.1, 4.2), (2.2, 0.2, 5.0), (3.2, 0.2, 5.2)], 0.25), T('bark'), uv='cyl', name='branch')
    for k in range(5):
        a = k * 1.3
        add(blob_bm(2.2, 50 + k, 2, 0.25), T('leaf_lush'), loc=(math.cos(a) * 1.8, math.sin(a) * 1.8, 7.0),
            uv='box', name='leaf')
    add(blob_bm(0.9, 9, 2, 0.35, (1.0, 0.4, 1.3)), GOLD(), loc=(2.8, 0.2, 4.1), uv='none', name='fleece')
    marker('Sparkles', (2.8, 0.2, 4.1), color=[255, 210, 90])
    # smok-straznik spi u stop (ogon)
    add(tube([(-1.5, -1.5, 0.4), (-3, -2.5, 0.5), (-4.5, -1.5, 0.4), (-5.2, 0.5, 0.3)], 0.45,
             radii=[1.0, 0.9, 0.6, 0.2]), T('leaf_dark'), uv='box', name='dragon_tail')


@prop('kon_trojanski', 'Unikaty', 'Kon trojanski (drewniany, na kolkach)')
def trojan_horse():
    begin('kon_trojanski')
    w = T('wood')
    add(box(3.0, 1.6, 0.4, 0.04), w, loc=(0, 0, 0.8), name='platform')
    for sx in (-1.1, 1.1):
        for sy in (-0.9, 0.9):
            add(cyl(0.45, 0.25, 14), T('wood_dark'), loc=(sx, sy, 0.45), rot=(90, 0, 0), name='wheel')
    for sx in (-0.9, 0.9):
        for sy in (-0.45, 0.45):
            add(box(0.35, 0.35, 2.2, 0.05), w, loc=(sx, sy, 2.1), name='leg')
    add(box(3.0, 1.4, 1.4, 0.2), w, loc=(0, 0, 3.8), name='body')
    add(box(0.8, 0.8, 2.0, 0.15), w, loc=(-1.4, 0, 5.0), rot=(0, 25, 0), name='neck')
    add(box(1.4, 0.7, 0.7, 0.15), w, loc=(-2.0, 0, 6.0), name='head')
    add(box(0.15, 0.6, 1.4, 0.03), T('wood_dark'), loc=(-1.2, 0, 5.6), rot=(0, 25, 0), name='mane')
    add(box(0.5, 0.2, 0.6, 0.02), F('void', (14, 10, 10)), loc=(0.6, -0.72, 3.8), name='hatch')


@prop('glowa_meduzy', 'Unikaty', 'Glowa Meduzy na tarczy (Aegis) na postumencie')
def medusa_head():
    begin('glowa_meduzy')
    add(box(2.6, 2.6, 2.4, 0.08), BLOCKS(), loc=(0, 0, 1.2), name='ped')
    add(cyl(1.6, 0.25, 32), BRONZE(), loc=(0, 0, 3.9), rot=(80, 0, 0), name='shield')
    add(C.bm_sphere(0.7, 16, 10), F('stone_face', (120, 130, 110), 0.6), loc=(0, -0.3, 3.95), scale=(1, 0.6, 1),
        name='face')
    for k in range(10):
        a = 2 * math.pi * k / 10
        p0 = Vector((math.cos(a) * 0.6, -0.4, 3.95 + math.sin(a) * 0.6))
        p1 = p0 + Vector((math.cos(a) * 0.6, -0.15, math.sin(a) * 0.6))
        add(tube([tuple(p0), tuple(p1)], 0.09, radii=[1, 0.5]), T('leaf_vine'), uv='box', name='snake')
    for sx in (-1, 1):
        add(C.bm_sphere(0.09, 8, 6), GLOW('medusa_eye', (255, 220, 60), 5), loc=(sx * 0.25, -0.72, 4.05), name='eye')


@prop('skamieniali_wojownicy', 'Unikaty', 'Skamieniale ofiary Meduzy (szare posagi w pozach ucieczki)')
def petrified():
    begin('skamieniali_wojownicy')
    m = T('rock', 0.9)
    statue_fig((0, 0, 0), 0.9, m, 'arms_up', 20, name='v1')
    statue_fig((3.5, 1.0, 0), 0.9, m, 'spear', -40, name='v2')
    statue_fig((-3.2, 1.5, 0), 0.9, m, 'still', 160, name='v3')


@prop('skrzydla_ikara', 'Unikaty', 'Polamane skrzydla Ikara z piorami na skale')
def icarus():
    begin('skrzydla_ikara')
    add(rock_bm(2.0, 41, 2, 0.3, 0.35, (1.4, 1, 0.5)), T('rock_white'), loc=(0, 0, 0.4), uv='box', smooth=False,
        name='rock')
    for sx in (-1, 1):
        for k in range(7):
            L = 2.6 - k * 0.25
            bm = C.bm_extrude([(0, 0), (L, 0.1), (L + 0.2, 0.35), (0, 0.45)], 0.04)
            add(bm, F('feather', (240, 236, 226), 0.8), loc=(sx * 0.3, -0.3 + k * 0.32, 1.25),
                rot=(0, -10 * sx, 90 - sx * 90 + sx * (k * 6)), uv='none', name='feather')
        add(cyl(0.05, 2.8, 6), T('wood'), loc=(sx * 1.5, 0.8, 1.3), rot=(0, 90, sx * 10), uv='none', name='frame')
    add(C.bm_sphere(0.35, 12, 8), F('wax', (240, 210, 120), 0.4), loc=(0.6, -1.0, 1.1), scale=(1.4, 1, 0.3),
        name='wax_drip')


@prop('skala_prometeusza', 'Unikaty', 'Skala Prometeusza: zerwane lancuchy i orzel')
def prometheus():
    begin('skala_prometeusza')
    add(rock_bm(4.0, 51, 2, 0.3, 0.3, (1, 0.8, 1.4)), T('cliff_grey'), loc=(0, 0, 2.5), uv='box', tile=5, smooth=False,
        name='rock')
    for sx in (-1, 1):
        for k in range(5):
            add(C.bm_torus(0.22, 0.06, 12, 5), F('iron', (60, 58, 56), 0.45, 0.85),
                loc=(sx * (1.2 + k * 0.32), -2.2, 4.0 - k * 0.3), rot=(0, 90 * (k % 2), 0), name='chain')
    add(blob_bm(0.6, 3, 1, 0.1, (0.8, 1.3, 1)), F('eagle_brown', (90, 60, 36), 0.7), loc=(0, -0.5, 6.4),
        name='eagle')
    for sx in (-1, 1):
        w = C.bm_extrude([(0, 0), (1.6, 0.5), (2.2, 0.2), (1.4, -0.3)], 0.08)
        add(w, F('eagle_brown', (90, 60, 36), 0.7), loc=(sx * 0.3, -0.5, 6.6), rot=(90, 0, 90 - sx * 90),
            uv='none', name='wing')
    marker('Fire', (0, -1.6, 5.4), size=1.2, heat=4)


@prop('glaz_syzyfa', 'Unikaty', 'Glaz Syzyfa na zboczu (nigdy nie dotarl na szczyt)')
def sisyphus():
    begin('glaz_syzyfa')
    bm = C.bm_extrude([(-7, 0), (7, 0), (7, 5), (-7, 0.4)], 6, 0.1, 1)
    C.bm_transform(bm, rot=(90, 0, 0))
    add(bm, T('grass_dry'), loc=(0, 0, 0), uv='box', tile=6, name='slope')
    add(rock_bm(2.2, 61, 3, 0.12, 0.0, (1, 1, 1)), T('rock'), loc=(2.0, 0, 4.4), uv='box', smooth=False,
        name='boulder')
    for k in range(5):
        add(box(0.4, 0.6, 0.05, 0.0), F('footprint', (90, 70, 50)), loc=(-4 + k * 1.3, (k % 2) * 0.6 - 0.3,
                                                                          0.35 + k * 0.62), rot=(0, -20, 0),
            name='step')


@prop('helm_hadesa', 'Unikaty', 'Helm niewidzialnosci Hadesa na czarnym oltarzu')
def hades_helm():
    begin('helm_hadesa')
    add(box(2.6, 2.6, 2.0, 0.08), T('basalt'), loc=(0, 0, 1.0), name='altar')
    add(lathe([(0.0, 0.0), (0.75, 0.0), (0.8, 0.6), (0.6, 1.1), (0, 1.25)], 24), F('dark_bronze', (40, 34, 40), 0.3, 1.0),
        loc=(0, 0, 2.05), uv='none', name='helm')
    add(C.bm_extrude([(-0.1, 0), (0.1, 0), (0.05, 1.4), (-0.05, 1.4)], 0.15), F('dark_bronze', (40, 34, 40), 0.3, 1.0),
        loc=(0, 0, 3.1), rot=(90, 0, 90), uv='none', name='crest')
    add(blob_bm(0.9, 7, 1, 0.3), GLOW('soul', (120, 255, 160), 2.5), loc=(0, 0, 2.6), scale=(1, 1, 0.6),
        name='soulmist')
    marker('Mist', (0, 0, 2.2), color=[120, 255, 160])


@prop('zlote_jablko', 'Unikaty', 'Zlote jablko Eris z napisem "Dla najpiekniejszej"')
def golden_apple():
    begin('zlote_jablko')
    add(cyl(0.7, 3.0, 20), MARBLE(), loc=(0, 0, 1.5), uv='cyl', name='pillar')
    add(box(1.8, 1.8, 0.3, 0.04), MARBLE(), loc=(0, 0, 3.15), name='cap')
    add(C.bm_sphere(0.55, 20, 12), GOLD(), loc=(0, 0, 3.85), scale=(1, 1, 0.9), name='apple')
    add(cyl(0.05, 0.4, 6), T('wood_dark'), loc=(0, 0, 4.5), uv='none', name='stem')
    add(C.bm_extrude([(0, 0), (0.5, 0.2), (0.6, 0.5), (0.1, 0.3)], 0.03), T('leaf_lush'), loc=(0.05, 0, 4.6),
        rot=(90, 0, 0), uv='none', name='leaf')
    marker('Sparkles', (0, 0, 3.9), color=[255, 220, 100])


@prop('posag_cerbera', 'Unikaty', 'Posag Cerbera - trzyglowy pies (straznik bramy)')
def cerberus():
    begin('posag_cerbera')
    m = T('basalt', 0.6)
    add(box(5, 3, 1.2, 0.06), T('blocks_grey'), loc=(0, 0, 0.6), name='ped')
    add(blob_bm(1.3, 2, 2, 0.1, (1.8, 1.0, 0.9)), m, loc=(0, 0, 2.8), name='body')
    for sx in (-1.2, 1.2):
        for sy in (-0.6, 0.6):
            add(box(0.5, 0.5, 1.6, 0.15), m, loc=(sx, sy, 1.9), name='leg')
    for k, (dx, dy) in enumerate(((-2.0, -0.7), (-2.3, 0.0), (-2.0, 0.7))):
        add(box(1.0, 0.8, 0.8, 0.25), m, loc=(dx, dy, 4.0), rot=(0, 0, (k - 1) * 25), name='head')
        add(box(0.6, 0.5, 0.4, 0.12), m, loc=(dx - 0.6, dy, 3.85), rot=(0, 0, (k - 1) * 25), name='snout')
        for ex in (-0.15, 0.15):
            add(C.bm_sphere(0.08, 8, 4), GLOW('cerb', (255, 60, 30), 6), loc=(dx - 0.5, dy + ex, 4.2), name='eye')
    add(tube([(2.2, 0, 3.0), (3.0, 0, 3.6), (3.2, 0, 4.5)], 0.18, radii=[1, 0.8, 0.4]), m, uv='box', name='tail')


@prop('sowa_ateny', 'Unikaty', 'Sowa Ateny na galazce oliwnej (z brazu)')
def owl():
    begin('sowa_ateny')
    add(cyl(0.5, 3.4, 16), MARBLE(), loc=(0, 0, 1.7), uv='cyl', name='pillar')
    add(blob_bm(0.7, 4, 2, 0.06, (0.9, 0.8, 1.3)), BRONZE(), loc=(0, 0, 4.2), name='body')
    add(C.bm_sphere(0.5, 14, 10), BRONZE(), loc=(0, 0, 5.2), scale=(1.1, 0.9, 0.9), name='head')
    for sx in (-1, 1):
        add(C.bm_sphere(0.17, 12, 8), GOLD(), loc=(sx * 0.22, -0.42, 5.25), name='eye')
        add(cyl(0.08, 0.3, 4, r2=0.0), BRONZE(), loc=(sx * 0.32, 0, 5.65), rot=(0, sx * 20, 0), name='ear')
    add(cyl(0.06, 0.2, 4, r2=0.0), GOLD(), loc=(0, -0.48, 5.05), rot=(-100, 0, 0), name='beak')
    add(tube([(-0.8, -0.2, 3.5), (0.9, -0.2, 3.6)], 0.07), T('bark_olive'), uv='none', name='twig')


@prop('sandaly_hermesa', 'Unikaty', 'Skrzydlate sandaly Hermesa na poduszce')
def hermes_sandals():
    begin('sandaly_hermesa')
    add(box(1.8, 1.8, 2.6, 0.06), MARBLE(), loc=(0, 0, 1.3), name='ped')
    add(box(1.4, 1.2, 0.3, 0.2), T('cloth_purple'), loc=(0, 0, 2.75), name='cushion')
    for sx in (-0.35, 0.35):
        add(box(0.35, 0.9, 0.12, 0.05), T('wood'), loc=(sx, 0, 2.97), name='sole')
        for k in range(2):
            add(box(0.4, 0.06, 0.1, 0.02), GOLD(), loc=(sx, -0.25 + k * 0.4, 3.05), name='strap')
        for side in (-1, 1):
            w = C.bm_extrude([(0, 0), (0.6, 0.2), (0.8, 0.5), (0.3, 0.3)], 0.03)
            add(w, F('feather', (240, 236, 226), 0.8), loc=(sx + side * 0.2, 0.3, 3.05), rot=(90, 0, 90 - side * 90),
                uv='none', name='wing')


@prop('lodz_charona', 'Unikaty', 'Lodz Charona z latarnia (mglista woda)')
def charon():
    begin('lodz_charona')
    from .p_harbor import hull_bm
    add(hull_bm(9, 2.6, 1.0, 12, 5), T('wood_dark', 0.85), uv='box', tile=3, name='hull')
    statue_fig((0, 2.0, 1.4), 0.6, F('cloak', (24, 22, 28), 0.9), 'still', 180, name='charon')
    add(cyl(0.05, 4.5, 6), T('wood_dark'), loc=(0.8, 2.0, 2.8), rot=(10, 0, 0), uv='none', name='pole')
    add(cyl(0.2, 0.4, 8), GLOW('ghostlamp', (120, 255, 160), 5), loc=(0, -4.6, 2.6), name='lamp')
    add(cyl(0.04, 1.4, 4), T('wood_dark'), loc=(0, -4.2, 2.8), rot=(60, 0, 0), uv='none', name='lamp_pole')
    marker('Light', (0, -4.6, 2.6), range=14, brightness=1.5, color=[120, 255, 160])
    marker('Mist', (0, 0, 0.6), color=[120, 255, 160])
