"""Legionista: lorica segmentata, stalowa galea z krzyzowymi okuciami (bez grzebienia),
plocienna tunika, granatowe scutum z srebrnym orlem (aquila) i SPQR, pilum.
Celowo inna paleta niz Gladiator (stal / granat / len / mosiadz zamiast czerwieni i zlota)."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Legionista', display='Legionista',
    subtitle='Militarna · tani start · pilum: pchnięcie, rzut, tarcza + pchnięcie',
    cam=dict(target=(0.0, -0.6, 2.55), dist=13.5, dir=(0.72, -1.0, 0.45)), ped_r=2.7,
)
SKIN = (0.66, 0.33, 0.18)


def build(out):
    rig = U.body('Legionista', out, SKIN, face_kw=dict(style='angry', mouth='teeth'),
                 mats=dict(torso='linen'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- lorica segmentata
    for i in range(5):
        z = 2.30 + i * 0.215
        K.mk(rig, C.bm_box(2.14, 1.14, 0.25, 0.05), f'Torso.band{i}', 'steel', T, (0, 0, z))
        for sx in (-0.16, 0.16):
            K.mk(rig, C.bm_box(0.13, 0.06, 0.1, 0.02), f'Torso.hinge{i}{sx}', 'brass', T,
                 (sx, -0.6, z + 0.02))
    K.mk(rig, C.bm_box(2.1, 1.12, 0.62, 0.06), 'Torso.chest', 'steel', T, (0, 0, 3.62))
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.62, 1.18, 0.16, 0.05), f'Torso.shoulderplate{sx}', 'steel', T,
             (sx * 0.72, 0, 3.98))
        K.mk(rig, C.bm_box(0.16, 0.06, 0.16, 0.02), f'Torso.buckle{sx}', 'brass', T, (sx * 0.5, -0.6, 3.72))
        K.mk(rig, C.bm_box(0.6, 0.07, 0.07, 0.02), f'Torso.chesttrim{sx}', 'brass', T, (sx * 0.62, -0.58, 3.4))
    K.mk(rig, C.bm_box(0.5, 0.07, 0.3, 0.03), 'Torso.chestplate', 'brass', T, (0, -0.6, 3.6))
    K.mk(rig, C.bm_sphere(0.09, 12, 8), 'Torso.chestboss', 'steel', T, (0, -0.66, 3.6))
    # chusta (focale)
    K.mk(rig, C.bm_torus(0.46, 0.12, 32, 8), 'Torso.focale', 'blue_cloth', T, (0, -0.02, 4.02),
         scale=(1.05, 0.95, 1))
    K.mk(rig, C.bm_sphere(0.13, 12, 8), 'Torso.knot', 'blue_cloth', T, (0, -0.52, 3.9))
    # pas + fartuch
    K.belt(rig, 2.13, 'leather_dark', 'brass')
    for i, x in enumerate((-0.27, -0.09, 0.09, 0.27)):
        K.mk(rig, C.bm_box(0.11, 0.05, 0.66, 0.02), f'Torso.apron{i}', 'leather', T, (x, -0.62, 1.72))
        for k in range(3):
            K.mk(rig, C.bm_cyl(0.045, 0.03, 12), f'Torso.apronstud{i}{k}', 'brass', T,
                 (x, -0.655, 1.95 - k * 0.2), rot=(90, 0, 0))
        K.mk(rig, C.bm_box(0.13, 0.06, 0.06, 0.02), f'Torso.aprontip{i}', 'brass', T, (x, -0.63, 1.38))
    # miecz w pochwie (prawy bok, za reka)
    K.mk(rig, C.bm_box(0.2, 0.09, 1.0, 0.03), 'Torso.scabbard', 'leather_dark', T, (-1.08, 0.58, 1.75),
         rot=(-12, 0, 0))
    for z in (2.15, 1.32):
        K.mk(rig, C.bm_box(0.23, 0.11, 0.08, 0.02), f'Torso.scabbardring{z}', 'brass', T,
             (-1.08, 0.58 - (2.15 - z) * 0.2 + 0.0, z), rot=(-12, 0, 0))
    K.mk(rig, C.bm_cyl(0.06, 0.32, 12), 'Torso.hilt', 'wood', T, (-1.08, 0.53, 2.42), rot=(-12, 0, 0))
    K.mk(rig, C.bm_sphere(0.1, 12, 8), 'Torso.pommel', 'brass', T, (-1.08, 0.5, 2.6))

    # ---- nogi: tunika + caligae
    for side in ('Right', 'Left'):
        K.leg_skirt(rig, side, 'linen', 1.42, 2.0, 0.09)
        K.mk(rig, C.bm_box(1.1, 1.1, 0.06, 0.02), f'{side} Leg.hem', 'blue_cloth', f'{side} Leg',
             (K.leg_x(rig, side), 0, 1.44))
        K.sandals(rig, side, 'leather', 'leather_dark', bands=(0.34, 0.62, 0.9))

    # ---- ramiona: naramienniki segmentowe + karwasz
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        sx = -1 if side == 'Right' else 1
        for i in range(3):
            K.mk(rig, C.bm_box(1.12, 1.14, 0.24, 0.05), f'{j}.pauldron{i}', 'steel', j,
                 (x + sx * 0.02, 0, 3.86 - i * 0.2), rot=(0, sx * (6 + i * 3), 0))
            K.mk(rig, C.bm_sphere(0.045, 8, 6), f'{j}.prv{i}', 'brass', j, (x + sx * 0.58, 0, 3.86 - i * 0.2))
        K.mk(rig, C.bm_box(1.06, 1.06, 0.4, 0.05), f'{j}.bracer', 'leather', j, (x, 0, 2.38))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.06, 0.02), f'{j}.bracertrim', 'brass', j, (x, 0, 2.56))

    # ---- helm (galea)
    H = 'Head'
    rim = hc + 0.22
    K.dome(rig, H, 'Head.helmet', 'steel', (0, 0, rim), r=0.69, h=0.52)
    K.ring(rig, H, 'Head.helmrim', 'brass', (0, 0, rim + 0.01), 0.69, 0.045)
    bm = C.bm_box(0.95, 0.09, 0.1, 0.03)
    C.bm_map(bm, lambda co: (co.x, co.y + co.x * co.x * 0.42, co.z))
    K.mk(rig, bm, 'Head.browridge', 'brass', H, (0, -0.70, rim + 0.08))
    prof = [(0.66, 0.0), (0.74, -0.12), (0.86, -0.24), (0.88, -0.28), (0.82, -0.27), (0.70, -0.14),
            (0.62, 0.0)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=20, arc=150, a0=15)), 'Head.neckguard', 'steel', H,
         (0, 0.0, rim))
    for sx in (-1, 1):
        bm = C.bm_box(0.07, 0.46, 0.58, 0.03)
        K.mk(rig, bm, f'Head.cheek{sx}', 'steel', H, (sx * 0.66, 0.03, hc - 0.07), rot=(0, sx * -8, 0))
        K.mk(rig, C.bm_box(0.08, 0.48, 0.06, 0.02), f'Head.cheektrim{sx}', 'brass', H,
             (sx * 0.665, 0.03, hc + 0.2), rot=(0, sx * -8, 0))
        K.mk(rig, C.bm_sphere(0.05, 10, 6), f'Head.cheekrivet{sx}', 'brass', H, (sx * 0.71, 0.03, hc - 0.07))
    # krzyzowe okucia kopuly + galka (bez grzebienia - to cecha Gladiatora)
    for axis in ('y', 'x'):
        pts = []
        for i in range(17):
            a = math.pi * i / 16
            c, z = 0.705 * math.cos(a), rim + 0.535 * math.sin(a)
            pts.append((0, c, z) if axis == 'y' else (c, 0, z))
        K.mk(rig, C.bm_tube(pts, 0.04, res=3), f'Head.cross{axis}', 'brass', H, (0, 0, 0))
    K.mk(rig, C.bm_cyl(0.06, 0.14, 12), 'Head.knobpost', 'brass', H, (0, 0, rim + 0.58))
    K.mk(rig, C.bm_sphere(0.1, 14, 8), 'Head.knob', 'brass', H, (0, 0, rim + 0.68))

    # ---- tarcza (scutum)
    ax = B['ax']
    sp = Vector((ax, -0.78, 2.2))
    rig.joint('Shield', 'Left Arm', tuple(sp), follow='Left Arm')
    W, Hh, Rr = 1.8, 2.45, 1.5
    S, tilt = U.curved_shield_surface(Rr)
    bm = C.bm_grid(16, 20, W, Hh)
    C.bm_transform(bm, loc=(0, 0, Hh / 2))
    C.bm_map(bm, lambda co: tuple(S(co.x, co.z)))
    C.bm_solidify(bm, 0.09)
    K.mk(rig, bm, 'Shield.board', 'blue_paint', 'Shield', tuple(sp), angle=None)
    for nm, w, h, r, th, mat in (('rim', W, Hh, 0.12, 0.055, 'steel'), ('inner', W - 0.36, Hh - 0.36, 0.1, 0.028, 'silver')):
        pts = [tuple(S(x, z, 0.0 if nm == 'rim' else 0.03)) for (x, z) in U.rounded_rect(w, h, r)]
        pts.append(pts[0])
        K.mk(rig, C.bm_tube(pts, th, smooth=False, bevel_res=2), f'Shield.{nm}', mat, 'Shield', tuple(sp))
    # umbo
    prof = [(0.0, 0.0), (0.42, 0.0), (0.42, 0.04), (0.30, 0.08), (0.27, 0.16), (0.18, 0.25), (0.0, 0.29)]
    um = C.bm_lathe(prof, segs=32)
    C.bm_transform(um, rot=(90, 0, 0))
    K.mk(rig, um, 'Shield.umbo', 'steel', 'Shield', tuple(sp + Vector((0, -0.06, 0))))
    K.mk(rig, C.bm_torus(0.42, 0.03, 32, 6), 'Shield.umboring', 'brass', 'Shield',
         tuple(sp + Vector((0, -0.07, 0))), rot=(90, 0, 0))
    # srebrny orzel legionu (aquila) nad umbo + wieniec wokol umbo
    ez = 0.66
    body = [(0.0, 0.30), (0.06, 0.26), (0.05, 0.18), (0.10, 0.08), (0.09, -0.10), (0.16, -0.26),
            (0.0, -0.20), (-0.16, -0.26), (-0.09, -0.10), (-0.10, 0.08), (-0.05, 0.18), (-0.06, 0.26)]
    U.flat_on_shield(rig, 'Shield', sp, S, tilt, C.bm_extrude(body, 0.04, 0.008, 1), 'Shield.eagle', 'silver', 0.0, ez)
    U.flat_on_shield(rig, 'Shield', sp, S, tilt, C.bm_extrude([(0.0, 0.0), (0.09, 0.03), (0.0, 0.07), (-0.03, 0.03)], 0.045, 0.006, 1),
                     'Shield.beak', 'brass', 0.06, ez + 0.25)
    for sgn in (-1, 1):
        U.flat_on_shield(rig, 'Shield', sp, S, tilt, C.bm_extrude(U.wing_poly(0.62, flip=sgn < 0), 0.035, 0.008, 1),
                         f'Shield.ewing{sgn}', 'silver', sgn * 0.08, ez + 0.02, extra_rot=sgn * 38)
        lr = []
        for k in range(9):
            a = math.radians(-80 + 160 * k / 8)
            lr.append(tuple(S(sgn * 0.52 * math.cos(a), 0.52 * math.sin(a), 0.035)))
        K.mk(rig, C.bm_tube(lr, 0.025, res=3), f'Shield.wreath{sgn}', 'silver', 'Shield', tuple(sp))
        for k in range(7):
            a = math.radians(-65 + 130 * k / 6)
            x, z = sgn * 0.52 * math.cos(a), 0.52 * math.sin(a)
            leaf = C.bm_extrude([(0, -0.035), (0.07, 0), (0, 0.035), (-0.02, 0)], 0.02, 0.005, 1)
            U.flat_on_shield(rig, 'Shield', sp, S, tilt, leaf, f'Shield.leaf{sgn}{k}', 'silver', x, z,
                             extra_rot=math.degrees(a) + (90 if sgn > 0 else -90) + sgn * 40)
    txt = C.bm_text('SPQR', size=0.3, depth=0.025, bevel=0.004)
    U.flat_on_shield(rig, 'Shield', sp, S, tilt, txt, 'Shield.spqr', 'silver', 0.0, -0.72, off=0.06)

    # ---- pilum
    hand = rig.hand['Right Arm']
    rig.joint('Pilum', 'Right Arm', tuple(hand), follow='Right Arm')
    hx, hz = hand.x, hand.z
    U.shaft(rig, 'Pilum', 'Pilum.shaft', 'wood_light', 1.0, -1.3, 0.085, hx, hz)
    U.shaft(rig, 'Pilum', 'Pilum.grip', 'leather_dark', 0.2, -0.2, 0.105, hx, hz)
    K.mk(rig, C.bm_cyl(0.07, 0.18, 8, r2=0.0), 'Pilum.butt', 'iron', 'Pilum', (hx, 1.08, hz), rot=(-90, 0, 0))
    K.mk(rig, C.bm_box(0.17, 0.26, 0.17, 0.03), 'Pilum.weight', 'bronze', 'Pilum', (hx, -1.32, hz))
    U.shaft(rig, 'Pilum', 'Pilum.shank', 'steel', -1.4, -2.55, 0.045, hx, hz, segs=8)
    K.mk(rig, C.bm_cyl(0.1, 0.34, 4, r2=0.0), 'Pilum.tip', 'steel', 'Pilum', (hx, -2.68, hz), rot=(90, 0, 45))
    rig.attach('PilumTip', 'Pilum', (hx, -2.8, hz))
    rig.attach('PilumMid', 'Pilum', (hx, -1.2, hz))
    rig.attach('PilumGrip', 'Pilum', (hx, 0.0, hz))
    rig.attach('ShieldFront', 'Shield', tuple(sp + Vector((0, -0.4, 0))))

    # wzorzec pocisku (pilum w locie, os -Y)
    parts = []
    b = C.bm_cyl(0.085, 2.3, 10)
    C.bm_transform(b, loc=(0, -0.15 + 1.15 - 1.15, 0), rot=(90, 0, 0))
    C.bm_transform(b, loc=(0, 1.0, 0))
    parts.append((b, 'wood_light'))
    b = C.bm_box(0.17, 0.26, 0.17, 0.03)
    C.bm_transform(b, loc=(0, -0.3, 0))
    parts.append((b, 'bronze'))
    b = C.bm_cyl(0.045, 1.15, 8)
    C.bm_transform(b, loc=(0, -0.95, 0), rot=(90, 0, 0))
    parts.append((b, 'steel'))
    b = C.bm_cyl(0.1, 0.34, 4, r2=0.0)
    C.bm_transform(b, loc=(0, -1.66, 0), rot=(90, 0, 45))
    parts.append((b, 'steel'))
    U.fx_template(parts, 'pilum')
    return rig


def animate(rig):
    base = dict(T=(6, 0, -10), H=(0, 0, 8), RA=(28, 8, 0), LA=(32, 8, -8), RL=(-12, 5, 0),
                LL=(16, -2, 10), Pilum={'pitch': 10}, Shield={'pitch': 0})
    A = Animator(rig, base)
    P = A.P

    # ---------------- postoj
    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(8, 0, -9), H=(3, 0, 7), RA=(31, 8, 0), LA=(30, 8, -8), Pilum={'pitch': 13}))
    A.key(60, P())

    # ---------------- atak 1: pchniecie pilum
    A.clip('Attack1', 'Atak 1: Pchnięcie pilum', 100, 36, level='poz. 0-1',
           desc='Szybkie pchnięcie zza tarczy z wykrokiem.', show=[100, 106, 110, 112, 118, 127])
    A.key(0, P())
    A.key(6, P(T=(0, 0, -30), Tp=(0, -0.15), RA=(8, 18, -12), Pilum={'pitch': 4}, LA=(42, 4, 16),
               H=(-2, 0, 24), LL=(10, -2, 10), RL=(-14, 5, 0)))
    A.key(10, P(T=(14, 0, -4), Tp=(0, 0.5), RA=(72, 0, 2), Pilum={'pitch': -1}, LA=(36, 6, 10),
                H=(0, 0, 6), LL=(30, -2, 6), RL=(-26, 5, 0), cape=12))
    A.key(12, P(T=(20, 0, 8), Tp=(0, 0.85), RA=(90, 0, 2), Pilum={'pitch': -2}, LA=(30, 10, 4),
                H=(-6, 0, -6), LL=(38, -2, 4), RL=(-32, 5, 0), cape=16))
    A.key(18, P(T=(16, 0, 4), Tp=(0, 0.75), RA=(82, 0, 2), Pilum={'pitch': -1}, LA=(32, 8, 6),
                H=(-4, 0, -2), LL=(34, -2, 4), RL=(-28, 5, 0), cape=12))
    A.key(27, P(T=(9, 0, -9), Tp=(0, 0.25), RA=(40, 8, 4), Pilum={'pitch': 6}, LA=(38, 4, 8),
                H=(0, 0, 8), LL=(20, -2, 8), RL=(-16, 5, 0)))
    A.key(36, P())
    A.event(12, 'Hit')
    A.event(8, 'TrailOn', a='PilumMid', b='PilumTip')
    A.event(15, 'TrailOff')
    tip, mid = rig.attachments['PilumTip'][1], rig.attachments['PilumMid'][1]
    A.add_fx('trail', 8, 15, joint='Pilum', a=mid, b=tip)
    A.add_fx('sparks', 12, 18, center='PilumTip', count=10, spread=1.0, col=(1, 0.85, 0.5))

    # ---------------- atak 2: rzut pilum
    A.clip('Attack2', 'Atak 2: Rzut pilum', 200, 46, level='poz. 2-3',
           desc='Zamach zza głowy, rzut z wykrokiem; pilum leci łukiem, nowe pojawia się w dłoni.',
           show=[200, 208, 212, 215, 219, 238])
    A.key(0, P())
    A.key(8, P(T=(-8, 10, -42), Tp=(0, -0.25), RA=(205, 18, 0), Pilum={'pitch': 25}, LA=(70, 25, -5),
               H=(-6, -6, 40), LL=(22, -4, 8), RL=(-18, 6, -10)))
    A.key(12, P(T=(4, 6, -28), Tp=(0, 0.0), RA=(200, 14, 0), Pilum={'pitch': 15}, LA=(75, 25, -5),
                H=(-4, -4, 28), LL=(28, -4, 8), RL=(-22, 6, -6)))
    A.key(15, P(T=(18, -4, 12), Tp=(0, 0.6), RA=(118, 4, 10), Pilum={'pitch': 6}, LA=(40, 20, 0),
                H=(-4, 2, -6), LL=(36, -4, 4), RL=(-30, 6, 0), cape=16))
    A.key(19, P(T=(26, -6, 24), Tp=(0, 0.8), RA=(70, 0, 40), Pilum={'pitch': -20}, LA=(25, 22, 0),
                H=(-8, 0, -16), LL=(40, -4, 4), RL=(-34, 6, 0), cape=18))
    A.key(30, P(T=(12, 0, -6), Tp=(0, 0.4), RA=(30, 10, 10), Pilum={'pitch': 0}, LA=(34, 6, 20),
                H=(0, 0, 6), LL=(22, -2, 6), RL=(-16, 5, 0)))
    A.key(46, P())
    A.event(15, 'Hit', projectile='pilum', speed=42, attachment='PilumMid')
    A.hide('Pilum', 16, 38)
    A.event(11, 'TrailOn', a='PilumMid', b='PilumTip')
    A.event(16, 'TrailOff')
    A.add_fx('trail', 11, 16, joint='Pilum', a=mid, b=tip)
    A.add_fx('projectile', 16, 30, model='pilum', **{'from': 'PilumMid'}, dir=(0.05, -1, 0.1), speed=1.4,
             grav=0.01)
    A.add_fx('orb', 36, 41, at='PilumGrip', r=0.45, col=(1, 0.8, 0.35))

    # ---------------- atak 3: tarcza + pchniecie
    A.clip('Attack3', 'Atak 3: Uderzenie tarczą + pchnięcie', 300, 52, level='poz. 4-5',
           desc='Taran tarczą (ogłusza), potem mocne pchnięcie pilum.', show=[300, 306, 310, 321, 325, 340])
    A.key(0, P())
    A.key(6, P(T=(12, 0, -40), Tp=(0, -0.1), LA=(55, 0, 30), RA=(10, 14, -14), Pilum={'pitch': 10},
               H=(0, 0, 34), LL=(16, -2, 10), RL=(-18, 6, 0)))
    A.key(10, P(T=(16, 0, -42), Tp=(0, 1.0), LA=(80, 0, 40), RA=(14, 16, -10), Pilum={'pitch': 10},
                H=(-4, 0, 36), LL=(40, -2, 10), RL=(-36, 6, 0), cape=18))
    A.key(16, P(T=(14, 0, -38), Tp=(0, 1.0), LA=(74, 0, 36), RA=(6, 20, -18), Pilum={'pitch': 8},
                H=(-2, 0, 32), LL=(36, -2, 10), RL=(-32, 6, 0)))
    A.key(21, P(T=(10, 0, -30), Tp=(0, 0.95), LA=(60, 6, 28), RA=(4, 24, -22), Pilum={'pitch': 4},
                H=(0, 0, 28), LL=(32, -2, 8), RL=(-30, 6, 0)))
    A.key(25, P(T=(22, 0, 10), Tp=(0, 1.45), RA=(92, 0, 2), Pilum={'pitch': -2}, LA=(48, 16, 10),
                H=(-6, 0, -6), LL=(42, -2, 4), RL=(-36, 6, 0), cape=16))
    A.key(33, P(T=(16, 0, 4), Tp=(0, 1.3), RA=(78, 0, 2), Pilum={'pitch': -1}, LA=(42, 10, 10),
                H=(-4, 0, 0), LL=(38, -2, 4), RL=(-32, 6, 0)))
    A.key(43, P(T=(8, 0, -12), Tp=(0, 0.5), RA=(36, 8, 4), Pilum={'pitch': 8}, LA=(40, 4, 8),
                H=(0, 0, 12), LL=(20, -2, 8), RL=(-16, 5, 0)))
    A.key(52, P())
    A.event(10, 'Hit', stun=True)
    A.event(25, 'Hit')
    A.event(22, 'TrailOn', a='PilumMid', b='PilumTip')
    A.event(28, 'TrailOff')
    A.add_fx('sparks', 10, 17, center='ShieldFront', count=16, spread=1.6, col=(1, 0.85, 0.45))
    A.add_fx('ring', 10, 18, center='ShieldFront', r0=0.3, r1=1.8, col=(1, 0.9, 0.7), th=0.06, flat=1.0)
    A.add_fx('trail', 22, 28, joint='Pilum', a=mid, b=tip)
    A.finish()
    return A
