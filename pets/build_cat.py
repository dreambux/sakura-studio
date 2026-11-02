"""Pet "Mruczek" (Rzadki): kot-szescian w stylu pet simulatora - rudy pregowany, zielone oczy, bialy pyszczek,
puszysty ogon. Uzywa wspolnych narzedzi z build_pet.py (paleta-gradient, eksport GLB, rendery).

  python pets/build_cat.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_pet as bp  # noqa: E402  (resetuje scene Blendera i laduje biblioteki)
from build_pet import P, C, put, tube, cone, aim_rot  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

bp.NAME = 'Mruczek'
bp.RARITY = ('Rzadki', (120, 210, 255))
bp.BG = ((120, 200, 255), (70, 120, 225))
bp.TARGET = (0.0, 0.2, 2.7)
bp.SHOTS = ((-24, 12, 15.5), (-90, 6, 15.0), (160, 12, 15.0), (30, 30, 15.0))
bp.PAL = [
    ('fur', (255, 178, 88), (214, 108, 38)),
    ('stripe', (196, 98, 36), (140, 62, 22)),
    ('cream', (255, 247, 230), (236, 214, 184)),
    ('pink', (255, 178, 196), (228, 118, 150)),
    ('iris', (34, 108, 44), (178, 236, 96)),
    ('black', (34, 24, 22), (10, 8, 8)),
    ('white', (255, 255, 255), (232, 238, 245)),
]
bp.KEY = {k: i for i, (k, a, b) in enumerate(bp.PAL)}
bp.NPAL = len(bp.PAL)


def rbox(sx, sy, sz, bev, loc, key, mat, lo=None, hi=None, rot=(0, 0, 0), name='box'):
    b = C.bm_box(sx, sy, sz, bev, 4)
    return put(b, key, mat, loc=loc, rot=rot, lo=lo, hi=hi, name=name)


def build():
    os.makedirs(bp.OUT, exist_ok=True)
    pal = os.path.join(bp.OUT, f'{bp.NAME}_paleta.png')
    bp.make_palette(pal)
    PM = bp.pal_material(pal)
    root = P.begin(bp.NAME)
    S = 4.0
    Z0 = 0.75
    D = S * 0.94
    H = S * 1.04
    cz = Z0 + H / 2
    F = -D / 2

    # cialo: szescian z mocno zaokraglonymi krawedziami
    rbox(S, D, H, 0.55, (0, 0, cz), 'fur', PM, lo=Z0, hi=Z0 + H, name='body')
    # lapki (krotkie, zaokraglone kostki) z kremowymi koncami
    for sx in (-1, 1):
        for sy in (-1, 1):
            rbox(1.05, 1.05, 1.0, 0.3, (sx * 1.2, sy * 1.1, 0.55), 'fur', PM, lo=0.05, hi=Z0 + 0.6, name='leg')
            rbox(1.08, 0.5, 0.32, 0.14, (sx * 1.2, sy * 1.1 - 0.32 if sy < 0 else sy * 1.1 - 0.0, 0.18), 'cream', PM,
                 name='toe') if sy < 0 else None
    # pregi (tabby): czolo, boki, grzbiet
    top = Z0 + H
    for k, x in enumerate((-0.55, 0.0, 0.55)):
        L = 0.95 if k == 1 else 0.7
        rbox(0.26, 0.24, L, 0.1, (x, F + 0.03, top - 0.35 - L / 2 + 0.25), 'stripe', PM, name='stripe_front')
        rbox(0.28, 1.6 - 0.2 * (k != 1), 0.22, 0.1, (x, F + 0.95, top + 0.02), 'stripe', PM, name='stripe_top')
    for sx in (-1, 1):
        for k, z in enumerate((Z0 + 2.6, Z0 + 1.9, Z0 + 1.2)):
            rbox(0.22, 1.1 - 0.15 * k, 0.26, 0.1, (sx * (S / 2 + 0.01), 0.55, z), 'stripe', PM, name='stripe_side')
    for k, y in enumerate((0.6, 1.2)):
        rbox(2.0 - 0.4 * k, 0.24, 0.26, 0.1, (0, -F + 0.01, top - 0.5 - 0.6 * k), 'stripe', PM, name='stripe_back')

    # uszy: trojkatne, lekko wygiete na zewnatrz, rozowe w srodku
    for sx in (-1, 1):
        outer = C.bm_extrude([(-0.62, 0), (0.62, 0), (0.12, 1.25), (-0.05, 1.3)], 0.32, 0.1, 2)
        C.bm_map(outer, lambda c: (c.x, c.z, c.y))
        put(outer, 'fur', PM, loc=(sx * 1.15, -0.35, top - 0.25), rot=(-8, sx * -14, 0), lo=top, hi=top + 1.3,
            name='ear')
        inner = C.bm_extrude([(-0.38, 0), (0.38, 0), (0.06, 0.9), (-0.03, 0.92)], 0.1, 0.04, 1)
        C.bm_map(inner, lambda c: (c.x, c.z, c.y))
        put(inner, 'pink', PM, loc=(sx * 1.15 + sx * 0.02, -0.53, top - 0.12), rot=(-8, sx * -14, 0), lo=top, hi=top + 1.0,
            name='ear_inner')

    # twarz: duze oczy (kopulki) z ciemna obwodka, zielona teczowka, zrenica i blyski
    ez = Z0 + H * 0.47
    for sx in (-1, 1):
        x = sx * 0.88
        put(C.bm_sphere(0.78, 32, 16), 'black', PM, loc=(x, F + 0.06, ez), scale=(1.0, 0.28, 1.06), name='eye_rim')
        put(C.bm_sphere(0.68, 32, 16), 'iris', PM, loc=(x, F - 0.0, ez), scale=(1.0, 0.33, 1.06), lo=ez - 0.7, hi=ez + 0.7,
            name='iris')
        put(C.bm_sphere(0.4, 24, 12), 'black', PM, loc=(x + sx * 0.04, F - 0.08, ez + 0.02), scale=(0.95, 0.3, 1.15),
            name='pupil')
        put(C.bm_sphere(0.2, 16, 8), 'white', PM, loc=(x - 0.2, F - 0.2, ez + 0.28), scale=(1, 0.35, 1), name='shine')
        put(C.bm_sphere(0.1, 12, 6), 'white', PM, loc=(x + 0.22, F - 0.17, ez - 0.3), scale=(1, 0.35, 1), name='shine')
    # bialy pyszczek, rozowy nosek, usta "w"
    mz = Z0 + H * 0.2
    put(C.bm_sphere(1.0, 28, 14), 'cream', PM, loc=(0, F + 0.12, mz), scale=(1.15, 0.2, 0.62), name='muzzle')
    nose = C.bm_extrude([(-0.2, 0.08), (0.2, 0.08), (0.0, -0.14)], 0.12, 0.05, 2)
    C.bm_map(nose, lambda c: (c.x, c.z, c.y))
    put(nose, 'pink', PM, loc=(0, F - 0.06, mz + 0.28), name='nose')
    for sx in (-1, 1):
        pts = [Vector((0, F - 0.05, mz + 0.13)), Vector((sx * 0.1, F - 0.05, mz - 0.03)), Vector((sx * 0.25, F - 0.05, mz - 0.02)),
               Vector((sx * 0.34, F - 0.04, mz + 0.1))]
        put(tube(pts, 0.035, None, 4), 'black', PM, name='mouth')
    for sx in (-1, 1):   # rumience
        put(C.bm_sphere(0.26, 16, 8), 'pink', PM, loc=(sx * 1.45, F + 0.03, mz + 0.35), scale=(1, 0.1, 0.6), name='blush')
    # biala piers pod pyszczkiem
    put(C.bm_sphere(0.9, 24, 12), 'cream', PM, loc=(0, F + 0.14, Z0 + 0.35), scale=(1.0, 0.18, 0.4), name='chest')

    # puszysty ogon: z tylu, wygiety w gore z zawinieciem, kremowy koniec
    pts = [Vector((0.6, -F - 0.2, Z0 + 0.9)), Vector((1.3, -F + 0.6, Z0 + 1.3)), Vector((1.7, -F + 0.8, Z0 + 2.6)),
           Vector((1.5, -F + 0.5, Z0 + 3.7)), Vector((1.0, -F + 0.15, Z0 + 4.15))]
    put(tube(pts, 0.36, [0.8, 1.0, 1.0, 0.95, 0.8], 6), 'fur', PM, lo=Z0, hi=Z0 + 4.2, name='tail')
    for k, t in enumerate((0.35, 0.6)):
        i = 1 + k
        p = pts[i].lerp(pts[i + 1], 0.5)
        put(C.bm_torus(0.33, 0.1, 20, 6), 'stripe', PM, loc=tuple(p), rot=aim_rot(pts[i + 1] - pts[i]), name='tail_stripe')
    put(C.bm_sphere(0.36, 16, 10), 'cream', PM, loc=tuple(pts[-1]), scale=(1.1, 1.1, 1.0), name='tail_tip')
    return root, PM


if __name__ == '__main__':
    root, PM = build()
    base = os.path.join(bp.OUT, bp.NAME)
    bpy.context.view_layer.update()
    bp.render(root, base)
    rep = bp.export_glb(root, base + '.glb')
    print('GLB czesci:', rep)
    bpy.ops.wm.save_as_mainfile(filepath=base + '.blend', compress=True)
