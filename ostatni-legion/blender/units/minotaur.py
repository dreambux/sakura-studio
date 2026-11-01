"""Minotaur: wiekszy i ciezszy od reszty (cialo R6 x1.2), glowa byka (pysk, nozdrza, zlote kolko,
wielkie rogi), czerwone slepia, kopyta, skorzana uprzaz z brazem, zerwane kajdany z lancuchem,
kolczasty naramiennik, labrys (podwojny topor).
Paleta: ciemne futro + zelazo + braz + skora."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Minotaur', display='Minotaur',
    subtitle='Magiczna · tank, szarża, łamie tarcze · cios labrysem, wir, szarża na rogach',
    cam=dict(target=(0.2, -1.2, 3.1), dist=17.5, dir=(0.62, -1.0, 0.4)), ped_r=3.2,
)
FUR = (0.13, 0.06, 0.028)
BODY = dict(tw=2.6, td=1.3, th=2.3, aw=1.25, ad=1.25, al=2.35, lw=1.25, ld=1.25, ll=2.1, hr=0.7, hh=1.3,
            bevel=0.14)


def build(out):
    M.LIB['muzzle'] = ((0.16, 0.11, 0.085), 0.0, 0.6, 0.15, 80, {'sheen': 0.4})
    M.LIB['fur_light'] = ((0.22, 0.12, 0.055), 0.0, 0.95, 0.35, 160, {'sheen': 0.6})
    rig = U.body('Minotaur', out, FUR, face_kw=dict(style='beast', mouth=None, brow=(10, 6, 4), brow_w=1.3),
                 B=BODY)
    B = rig.B
    hc = B['head_c']
    T = 'Torso'
    tz = B['tz']
    tw, td = B['tw'], B['td']

    # ---- tors: jasniejsza siersc na piersi, uprzaz X z brazowym pierscieniem
    K.mk(rig, C.bm_box(1.6, 0.12, 1.2, 0.1), 'Torso.chestfur', 'fur_light', T, (0, -td / 2 - 0.01, tz + 0.45))
    for s in (1, -1):
        ang = math.degrees(math.atan2(B['th'] - 0.2, tw - 0.2))
        L = math.hypot(B['th'] - 0.2, tw - 0.2) + 0.2
        for yy, nm in ((-td / 2 - 0.06, 'f'), (td / 2 + 0.06, 'b')):
            K.mk(rig, C.bm_box(0.26, 0.07, L, 0.03), f'Torso.harness{s}{nm}', 'leather_dark', T,
                 (0, yy, tz), rot=(0, s * (90 - ang), 0))
    K.mk(rig, C.bm_torus(0.24, 0.07, 24, 8), 'Torso.ring', 'bronze', T, (0, -td / 2 - 0.12, tz), rot=(90, 0, 0))
    K.mk(rig, C.bm_cyl(0.16, 0.06, 16), 'Torso.ringboss', 'bronze_dark', T, (0, -td / 2 - 0.12, tz), rot=(90, 0, 0))
    # kilt z pasow skory
    K.mk(rig, C.bm_box(tw + 0.12, td + 0.12, 0.3, 0.05), 'Torso.belt', 'leather_dark', T, (0, 0, B['ll'] + 0.15))
    K.mk(rig, C.bm_cyl(0.2, 0.08, 16, bevel=0.02), 'Torso.buckle', 'bronze', T, (0, -td / 2 - 0.1, B['ll'] + 0.15),
         rot=(90, 0, 0))
    for side in ('Right', 'Left'):
        K.pteruges(rig, side, 'leather', 'bronze', length=0.75, n=3)
    # naramiennik z kolcami (lewe ramie)
    ax = B['ax']
    sh_top = B['ll'] + B['th']
    prof = [(0.0, 0.32), (0.45, 0.28), (0.72, 0.12), (0.8, -0.1), (0.74, -0.12), (0.66, 0.08), (0.42, 0.22), (0.0, 0.26)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=24)), 'Left Arm.pauldron', 'iron', 'Left Arm', (ax, 0, sh_top - 0.05),
         scale=(1, 1.05, 1))
    for k in range(3):
        K.mk(rig, C.bm_cyl(0.1, 0.42, 8, r2=0.0), f'Left Arm.spike{k}', 'steel', 'Left Arm',
             (ax + 0.1 + (k - 1) * 0.0, -0.35 + k * 0.35, sh_top + 0.36), rot=(0, 18, 0))
    # kajdany z zerwanym lancuchem
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        K.mk(rig, C.bm_box(1.38, 1.38, 0.38, 0.06), f'{j}.shackle', 'iron', j, (x, 0, B['ll'] + B['th'] - B['al'] + 0.45))
        for k in range(3):
            K.mk(rig, C.bm_torus(0.11, 0.035, 12, 6), f'{j}.link{k}', 'iron', j,
                 (x + (0.72 if side == 'Left' else -0.72), 0.0, B['ll'] + B['th'] - B['al'] + 0.35 - k * 0.17),
                 rot=(0, 0, 90 * (k % 2)), scale=(1, 1, 1.5))
    # kopyta
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.mk(rig, C.bm_box(B['lw'] + 0.06, B['ld'] + 0.06, 0.42, 0.08), f'{j}.hoof', 'hoof', j, (x, 0, 0.21))
        K.mk(rig, C.bm_box(0.08, B['ld'] * 0.5 + 0.06, 0.36, 0.01), f'{j}.cleft', 'black', j, (x, -B['ld'] / 4 - 0.03, 0.2))
        K.mk(rig, C.bm_box(B['lw'] + 0.12, B['ld'] + 0.12, 0.2, 0.06), f'{j}.fetlock', 'fur_dark', j, (x, 0, 0.5))

    # ---- glowa byka
    H = 'Head'
    K.mk(rig, C.bm_box(1.0, 0.62, 0.62, 0.22, 3), 'Head.snout', 'muzzle', H, (0, -0.82, hc - 0.32))
    for sx in (-1, 1):
        K.mk(rig, C.bm_sphere(0.09, 10, 6), f'Head.nostril{sx}', 'black', H, (sx * 0.22, -1.12, hc - 0.28),
             scale=(1, 0.5, 1.3))
    K.mk(rig, C.bm_torus(0.17, 0.035, 20, 6), 'Head.nosering', 'gold', H, (0, -1.16, hc - 0.5), rot=(90, 0, 0))
    K.mk(rig, C.bm_box(1.25, 0.4, 0.3, 0.12), 'Head.brow', 'fur_dark', H, (0, -0.32, hc + 0.4))
    K.mk(rig, C.bm_sphere(0.35, 14, 8), 'Head.tuft', 'fur_dark', H, (0, 0.0, hc + 0.66), scale=(1.4, 1.2, 0.6))
    for sx in (-1, 1):
        ear = C.bm_sphere(0.22, 12, 8)
        K.mk(rig, ear, f'Head.ear{sx}', 'fur', H, (sx * 0.86, 0.05, hc + 0.2), scale=(1.3, 0.45, 0.6),
             rot=(0, sx * -20, 0))
        horn = [(sx * 0.6, 0.0, hc + 0.42), (sx * 1.05, -0.05, hc + 0.58), (sx * 1.45, -0.15, hc + 0.85),
                (sx * 1.6, -0.35, hc + 1.3), (sx * 1.5, -0.6, hc + 1.62)]
        K.mk(rig, C.bm_tube(horn, 0.22, radii=[1.0, 0.85, 0.65, 0.42, 0.12], res=6), f'Head.horn{sx}', 'horn', H, (0, 0, 0))
        K.mk(rig, C.bm_torus(0.2, 0.04, 16, 6), f'Head.hornring{sx}', 'bronze', H, (sx * 0.95, -0.04, hc + 0.55),
             rot=(0, 90 - sx * 25, 0))
    rig.attach('Horns', H, (0, -1.4, hc + 0.4))

    # ---- labrys
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Labrys', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Labrys', 'Labrys.haft', 'wood', 1.0, -3.0, 0.1, hx, hz)
    for y in (-0.2, 0.25, 0.7):
        K.mk(rig, C.bm_torus(0.11, 0.035, 14, 6), f'Labrys.wrap{y}', 'leather_dark', 'Labrys', (hx, y, hz), rot=(90, 0, 0))
    K.mk(rig, C.bm_cyl(0.14, 0.18, 10, bevel=0.03), 'Labrys.pommel', 'bronze', 'Labrys', (hx, 1.05, hz), rot=(90, 0, 0))
    hy = -2.55
    K.mk(rig, C.bm_box(0.3, 0.55, 0.42, 0.08), 'Labrys.socket', 'bronze_dark', 'Labrys', (hx, hy, hz))
    for sz in (-1, 1):
        poly = [(0.12, -0.22), (0.5, -0.32), (0.85, -0.6), (1.0, 0.0), (0.85, 0.6), (0.5, 0.32), (0.12, 0.22)]
        bm = C.bm_extrude(poly, 0.12, 0.03, 2)
        C.bm_map(bm, lambda co, sz=sz: (co.z * (1 - abs(co.x) * 0.55), co.y, sz * co.x))
        K.mk(rig, K.bmesh_recalc(bm), f'Labrys.blade{sz}', 'steel', 'Labrys', (hx, hy, hz))
        edge = []
        for i in range(9):
            a = math.radians(-34 + 68 * i / 8)
            edge.append((hx, hy + 0.62 * math.sin(a), hz + sz * (0.42 + 0.58 * math.cos(a))))
        K.mk(rig, C.bm_tube(edge, 0.035, res=2), f'Labrys.edge{sz}', 'bronze', 'Labrys', (0, 0, 0))
    rig.attach('AxeTop', 'Labrys', (hx, hy, hz + 1.0))
    rig.attach('AxeBot', 'Labrys', (hx, hy, hz - 1.0))
    rig.attach('AxeHead', 'Labrys', (hx, hy - 0.3, hz))
    rig.attach('AxeNeck', 'Labrys', (hx, -1.4, hz))
    return rig


def animate(rig):
    base = dict(T=(12, 0, -8), H=(-6, 0, 6), RA=(38, 14, 0), LA=(22, 20, 0), RL=(-12, 10, 0), LL=(12, -8, 6),
                Labrys={'pitch': 72})
    A = Animator(rig, base)
    P = A.P
    top, neck = rig.attachments['AxeHead'][1], rig.attachments['AxeNeck'][1]

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(18, P(T=(15, 0, -7), H=(4, 0, 4), RA=(40, 14, 0), LA=(25, 22, 0)))
    A.key(24, P(T=(14, 0, -7), H=(-12, 0, 6)))
    A.key(40, P(T=(10, 0, -9), H=(-4, 0, 8), Labrys={'pitch': 76}))
    A.key(60, P())
    A.add_fx('puffs', 22, 34, center='Horns', count=4, spread=0.4, rise=-0.2, size=0.12, col=(0.85, 0.85, 0.85),
             dir=(0, -0.6, -0.3), name='snort')

    # ---- atak 1: cios labrysem z gory
    A.clip('Attack1', 'Atak 1: Cios labrysem', 100, 46, level='poz. 0-1',
           desc='Zamach zza głowy, uderzenie w ziemię – pęknięcie i kurz.', show=[100, 108, 113, 116, 120, 132])
    A.key(0, P())
    A.key(10, P(T=(-14, 0, -14), Tp=(0, -0.2), RA=(205, 10, 0), Labrys={'pitch': 150}, LA=(160, 20, 0),
                H=(-22, 0, 10), RL=(-14, 10, 0), LL=(18, -8, 6)))
    A.key(13, P(T=(-10, 0, -10), RA=(200, 8, 0), Labrys={'pitch': 140}, LA=(150, 18, 0), H=(-20, 0, 8)))
    A.key(17, P(T=(34, 0, 4), Tp=(0, 0.9), RA=(78, 0, 10), Labrys={'pitch': -40}, LA=(60, 20, 10),
                H=(10, 0, -2), RL=(-34, 12, 0), LL=(40, -8, 4), cape=0))
    A.key(22, P(T=(36, 0, 4), Tp=(0, 0.9), RA=(70, 0, 10), Labrys={'pitch': -52}, LA=(50, 22, 10),
                H=(12, 0, -2), RL=(-34, 12, 0), LL=(40, -8, 4)))
    A.key(34, P(T=(18, 0, -4), Tp=(0, 0.4), RA=(50, 12, 4), Labrys={'pitch': 40}, LA=(30, 20, 0),
                RL=(-20, 10, 0), LL=(22, -8, 6)))
    A.key(46, P())
    A.event(17, 'Hit', area=2.5, stun=0.8)
    A.event(12, 'TrailOn', a='AxeNeck', b='AxeHead')
    A.event(18, 'TrailOff')
    A.add_fx('trail', 12, 18, joint='Labrys', a=neck, b=top, len=7)
    A.add_fx('ring', 17, 32, center=(-0.6, -3.1, 0.08), r0=0.4, r1=3.4, col=(1.0, 0.75, 0.45), th=0.08)
    A.add_fx('puffs', 17, 36, center=(-0.6, -3.1, 0.2), count=14, spread=2.4, rise=0.9, size=0.42,
             col=(0.68, 0.58, 0.45))
    A.add_fx('sparks', 17, 25, center=(-0.6, -3.1, 0.2), count=14, spread=1.8, col=(1, 0.75, 0.35))

    # ---- atak 2: wir labrysem
    A.clip('Attack2', 'Atak 2: Wir', 200, 50, level='poz. 2-3',
           desc='Szeroki zamach dookoła – trafia wszystkich wokół.', show=[200, 208, 213, 217, 222, 236])
    A.key(0, P())
    A.key(8, P(T=(8, 0, -70), RA=(90, 0, -70), Labrys={'pitch': 6}, LA=(40, 40, 0), H=(0, 0, 50),
               RL=(-14, 10, -20), LL=(18, -8, 20), Tp=(0, -0.1)))
    for f, ang in ((12, -20), (15, 50), (18, 120), (21, 190)):
        A.key(f, P(T=(16, 0, ang), RA=(92, 0, 10), Labrys={'pitch': 2}, LA=(50, 50, 0), H=(4, 0, 0),
                   RL=(-16, 12, ang), LL=(20, -10, -ang), Tp=(0, 0.3), air=0.15))
    A.key(28, P(T=(20, 0, 300), RA=(80, 0, 30), Labrys={'pitch': -10}, LA=(40, 40, 0), H=(6, 0, 0),
                RL=(-18, 12, 300), LL=(22, -10, -300), Tp=(0, 0.3)))
    A.key(38, P(T=(14, 0, 348), RA=(48, 14, 6), Labrys={'pitch': 50}, RL=(-12, 10, 350), LL=(12, -8, -346),
                Tp=(0, 0.1)))
    A.key(50, P(T=(12, 0, 352), RL=(-12, 10, 360), LL=(12, -8, -354)))
    A.event(17, 'Hit', area=True)
    A.add_fx('trail', 10, 24, joint='Labrys', a=neck, b=top, len=10, name='w')
    A.add_fx('ring', 16, 30, center=(0, 0, 0.1), r0=1.5, r1=5.0, col=(1, 0.85, 0.6), th=0.06)

    # ---- atak 3: szarza
    A.clip('Attack3', 'Atak 3: Szarża', 300, 60, level='poz. 4-5',
           desc='Pochyla łeb i szarżuje na rogach – łamie tarcze, odrzuca. Potem wraca na miejsce.',
           show=[300, 308, 314, 320, 324, 344])
    A.key(0, P())
    A.key(8, P(T=(30, 0, 0), H=(30, 0, 0), RA=(-20, 20, 0), LA=(-20, 20, 0), Labrys={'pitch': 60}, Tp=(0, -0.3),
               RL=(-30, 8, 0), LL=(20, -6, 0)))
    steps = [(12, 1.0, 1), (15, 2.0, -1), (18, 3.0, 1)]
    for f, d, s in steps:
        A.key(f, P(T=(38, 0, 0), H=(32, 0, 0), RA=(10 + 30 * s, 20, 0), LA=(10 - 30 * s, 20, 0),
                   Labrys={'pitch': 50}, Tp=(0, d), RL=(-35 * s, 8, 0), LL=(35 * s, -6, 0), air=0.15, cape=20))
    A.key(21, P(T=(44, 0, 0), H=(40, 0, 0), RA=(30, 30, 0), LA=(30, 30, 0), Labrys={'pitch': 40}, Tp=(0, 4.0),
                RL=(-40, 8, 0), LL=(38, -6, 0)))
    A.key(26, P(T=(-6, 0, 0), H=(-24, 0, 0), RA=(120, 40, 0), LA=(120, 40, 0), Labrys={'pitch': 90}, Tp=(0, 3.7),
                RL=(-10, 10, 0), LL=(10, -8, 0)))
    A.key(36, P(T=(10, 0, 0), H=(-6, 0, 0), Tp=(0, 2.6), RL=(-20, 10, 0), LL=(16, -8, 0)))
    A.key(44, P(T=(10, 0, 0), Tp=(0, 1.4), RL=(16, 10, 0), LL=(-16, -8, 0)))
    A.key(52, P(Tp=(0, 0.4), RL=(-16, 10, 0), LL=(16, -8, 6)))
    A.key(60, P())
    A.event(21, 'Hit', knockback=True, break_shield=True)
    A.add_fx('puffs', 10, 26, center=(0, -1.0, 0.2), count=12, spread=1.4, rise=0.4, size=0.35,
             col=(0.68, 0.58, 0.45), dir=(0, -3.0, 0), name='run')
    A.add_fx('sparks', 21, 30, center='Horns', count=18, spread=2.2, col=(1, 0.8, 0.4), name='imp')
    A.add_fx('ring', 21, 32, center='Horns', r0=0.4, r1=2.4, col=(1, 0.85, 0.6), th=0.07, flat=1.0, name='imp')
    A.finish()
    return A
