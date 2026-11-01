"""Wyrocznia Delficka (Pytia): biala suknia do ziemi, fioletowy himation i welon, zloty wieniec
laurowy, laska z laurowym kregiem i kula proroctw, obok zloty trojnog z fioletowym ogniem.
Paleta: biel + fiolet + zloto, magia fioletowa."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Wyrocznia', display='Wyrocznia Delficka',
    subtitle='Magiczna · wsparcie, aura wykrywania · wizja, proroctwo, opary Delf',
    cam=dict(target=(0.2, -1.3, 3.0), dist=16.5, dir=(0.62, -1.0, 0.4)), ped_r=3.0,
)
SKIN = (0.78, 0.50, 0.36)


def build(out):
    rig = U.body('Wyrocznia', out, SKIN,
                 face_kw=dict(style='fem', mouth='frown', lashes=True, eye=(70, 25, 110), lips=(120, 40, 80),
                              brow_w=0.8),
                 mats=dict(torso='white_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- suknia + himation
    K.chest_strap(rig, 'purple_cloth', 'gold', from_right=True, w=0.48)
    K.belt(rig, 2.55, 'gold', 'gold', h=0.12, studs=False)
    K.mk(rig, C.bm_box(2.1, 1.1, 0.12, 0.04), 'Torso.neckline', 'gold', T, (0, 0, 3.97))
    for sx in (-1, 1):
        K.mk(rig, C.bm_cyl(0.12, 0.06, 16, bevel=0.02), f'Torso.fibula{sx}', 'gold', T, (sx * 0.7, -0.56, 3.85),
             rot=(90, 0, 0))
        K.mk(rig, C.bm_sphere(0.06, 10, 6), f'Torso.fibgem{sx}', 'glow_violet', T, (sx * 0.7, -0.61, 3.85))
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.mk(rig, C.bm_box(1.14, 1.14, 1.95, 0.06), f'{j}.robe', 'white_cloth', j, (x, 0, 1.06))
        K.mk(rig, C.bm_box(1.17, 1.17, 0.3, 0.04), f'{j}.hem', 'purple_cloth', j, (x, 0, 0.22))
        K.mk(rig, C.bm_box(1.18, 1.18, 0.05, 0.02), f'{j}.hemgold', 'gold', j, (x, 0, 0.4))
        K.mk(rig, C.bm_box(1.18, 1.18, 0.05, 0.02), f'{j}.hemgold2', 'gold', j, (x, 0, 0.07))
        for k in range(3):
            K.mk(rig, C.bm_box(0.05, 0.04, 1.4, 0.015), f'{j}.fold{k}', 'linen', j,
                 (x - 0.3 + 0.3 * k, -0.585, 1.15))
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        K.mk(rig, C.bm_box(1.08, 1.08, 0.9, 0.05), f'{j}.sleeve', 'white_cloth', j, (x, 0, 3.55))
        K.mk(rig, C.bm_box(1.1, 1.1, 0.06, 0.02), f'{j}.sleevegold', 'gold', j, (x, 0, 3.1))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.14, 0.03), f'{j}.bracelet', 'gold', j, (x, 0, 2.3))

    # ---- wlosy, welon, wieniec
    K.hair_block(rig, 'hair_dark', hc, back=0.6, length=1.3)
    for sx in (-1, 1):
        lock = [(sx * 0.62, -0.2, hc + 0.3), (sx * 0.67, -0.25, hc - 0.2), (sx * 0.64, -0.15, hc - 0.7),
                (sx * 0.72, -0.1, hc - 1.0)]
        K.mk(rig, C.bm_tube(lock, 0.09, radii=[1, 0.95, 0.85, 0.5], res=5), f'Head.lock{sx}', 'hair_dark', 'Head',
             (0, 0, 0))
    prof = []
    for i in range(12):
        t = i / 11
        prof.append((0.74 + 0.5 * t ** 1.5, hc + 0.72 - 2.3 * t))
    prof = [(r, z - hc) for r, z in prof]
    bm = C.bm_lathe(prof[::-1], segs=24, arc=200, a0=-10)
    C.bm_solidify(bm, 0.05)
    K.mk(rig, bm, 'Head.veil', 'violet_cloth', 'Head', (0, 0.05, hc), angle=None)
    K.mk(rig, C.bm_box(1.5, 0.1, 0.12, 0.04), 'Head.veilband', 'gold', 'Head', (0, 0.62, hc + 0.68), rot=(20, 0, 0))
    K.laurel(rig, 'Head', (0, 0, hc + 0.36), R=0.68, n=9)
    K.mk(rig, C.bm_sphere(0.09, 12, 8), 'Head.thirdeye', 'glow_violet', 'Head', (0, -0.72, hc + 0.36),
         scale=(1, 0.6, 1.2))

    # ---- laska
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Staff', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Staff', 'Staff.shaft', 'wood', 2.05, -3.0, 0.075, hx, hz)
    for y in (-0.3, 0.3, -1.5, -2.6):
        K.mk(rig, C.bm_torus(0.085, 0.03, 14, 6), f'Staff.band{y}', 'gold', 'Staff', (hx, y, hz), rot=(90, 0, 0))
    K.mk(rig, C.bm_cyl(0.09, 0.2, 10, r2=0.04), 'Staff.foot', 'gold', 'Staff', (hx, 2.1, hz), rot=(-90, 0, 0))
    ring_c = Vector((hx, -3.45, hz))
    K.mk(rig, C.bm_torus(0.42, 0.05, 32, 8), 'Staff.ring', 'gold', 'Staff', tuple(ring_c), rot=(0, 90, 0))
    for k in range(10):
        a = 2 * math.pi * k / 10
        p = ring_c + Vector((0, math.cos(a) * 0.45, math.sin(a) * 0.45))
        leaf = C.bm_extrude([(0, -0.04), (0.09, 0), (0, 0.04), (-0.02, 0)], 0.025, 0.006, 1)
        C.bm_transform(leaf, rot=(0, 90, 0))
        K.mk(rig, leaf, f'Staff.leaf{k}', 'gold', 'Staff', tuple(p), rot=(math.degrees(a) + 60, 0, 0))
    K.mk(rig, C.bm_sphere(0.22, 24, 14), 'Staff.orb', 'glow_violet', 'Staff', tuple(ring_c))
    rig.attach('StaffTop', 'Staff', tuple(ring_c))
    rig.attach('StaffMid', 'Staff', (hx, -2.2, hz))
    rig.attach('Eye', 'Head', (0, -0.8, hc + 0.36))

    # ---- trojnog z fioletowym ogniem (stoi obok, statyczny)
    tc = Vector((2.15, -0.9, 0))
    rig.joint('Tripod', 'HumanoidRootPart', (tc.x, tc.y, 1.9))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        foot = tc + Vector((0.55 * math.cos(a), 0.55 * math.sin(a), 0.05))
        top = tc + Vector((0.35 * math.cos(a), 0.35 * math.sin(a), 1.8))
        mid = (foot + top) / 2 + Vector((0.12 * math.cos(a), 0.12 * math.sin(a), 0))
        K.mk(rig, C.bm_tube([tuple(foot), tuple(mid), tuple(top)], 0.05, res=4), f'Tripod.leg{k}', 'gold', 'Tripod', (0, 0, 0))
        K.mk(rig, C.bm_sphere(0.08, 10, 6), f'Tripod.paw{k}', 'gold', 'Tripod', tuple(foot))
    K.mk(rig, C.bm_torus(0.3, 0.025, 24, 6), 'Tripod.brace', 'gold', 'Tripod', tuple(tc + Vector((0, 0, 0.9))))
    prof = [(0.0, 0.0), (0.2, 0.0), (0.42, 0.12), (0.52, 0.3), (0.55, 0.36), (0.5, 0.36), (0.45, 0.28),
            (0.0, 0.18)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=32)), 'Tripod.bowl', 'bronze', 'Tripod', tuple(tc + Vector((0, 0, 1.72))))
    K.mk(rig, C.bm_torus(0.53, 0.035, 32, 6), 'Tripod.lip', 'gold', 'Tripod', tuple(tc + Vector((0, 0, 2.08))))
    for k in range(7):
        a = 2 * math.pi * k / 7
        r = 0.0 if k == 0 else 0.25
        h = 0.75 if k == 0 else 0.45 + 0.1 * (k % 3)
        p = tc + Vector((r * math.cos(a), r * math.sin(a), 2.0))
        K.mk(rig, C.bm_cyl(0.16 if k == 0 else 0.11, h, 8, r2=0.0), f'Tripod.flame{k}', 'glow_violet', 'Tripod',
             tuple(p + Vector((0, 0, h / 2))), rot=(0, 0, 0))
    rig.attach('Fire', 'Tripod', tuple(tc + Vector((0, 0, 2.5))))
    return rig


def animate(rig):
    base = dict(T=(2, 0, -6), H=(4, 0, 4), RA=(28, 6, 0), LA=(20, 18, -6), RL=(-6, 4, 0), LL=(6, -3, 4),
                Staff={'pitch': 84})
    A = Animator(rig, base)
    P = A.P

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(3, 1, -4), H=(0, 3, 2), RA=(30, 6, 0), LA=(24, 22, -10), Staff={'pitch': 86}))
    A.key(60, P())
    A.add_fx('orb', 0, 60, at='StaffTop', r=0.4, col=(0.55, 0.2, 1.0), energy=60)
    A.add_fx('puffs', 0, 60, center='Fire', count=6, spread=0.4, rise=1.6, size=0.25, col=(0.6, 0.35, 0.9),
             strength=1.5, name='idle')

    # ---- atak 1: wizja (puls wykrywania)
    A.clip('Attack1', 'Atak 1: Wizja', 100, 42, level='poz. 0-1',
           desc='Laska w górę, głowa odchylona, fioletowy puls wykrywa ukrytych i lekko rani.',
           show=[100, 106, 112, 116, 122, 132])
    A.key(0, P())
    A.key(6, P(T=(8, 0, -10), RA=(20, 10, 0), LA=(10, 20, 0), H=(10, 0, 0), Staff={'pitch': 80}, Tp=(0, -0.1)))
    A.key(13, P(T=(-10, 0, 0), RA=(165, 6, 0), LA=(40, 50, -20), H=(-22, 0, 0), Staff={'pitch': 90}, air=0.25))
    A.key(16, P(T=(-12, 0, 0), RA=(170, 6, 0), LA=(45, 55, -20), H=(-25, 0, 0), Staff={'pitch': 90}, air=0.3))
    A.key(24, P(T=(-6, 0, 0), RA=(150, 6, 0), LA=(40, 45, -15), H=(-15, 0, 0), Staff={'pitch': 88}, air=0.15))
    A.key(34, P(T=(1, 0, -5), RA=(40, 6, 0), LA=(24, 20, -8), H=(2, 0, 4), Staff={'pitch': 85}))
    A.key(42, P())
    A.event(16, 'Hit', area=True, reveal_hidden=True)
    A.add_fx('orb', 10, 24, at='StaffTop', r=0.6, col=(0.6, 0.25, 1.0), energy=300, name='a1')
    A.add_fx('ring', 16, 32, center=(0, 0, 0.1), r0=0.6, r1=6.5, col=(0.55, 0.2, 1.0), th=0.09, disc=True, name='a1')
    A.add_fx('ring', 18, 34, center=(0, 0, 0.1), r0=0.4, r1=4.5, col=(0.95, 0.8, 1.0), th=0.05, name='a1b')
    A.add_fx('sparks', 14, 28, center='StaffTop', count=16, spread=1.6, col=(0.85, 0.6, 1.0), name='a1')

    # ---- atak 2: proroctwo (lewitacja + promien)
    A.clip('Attack2', 'Atak 2: Proroctwo', 200, 56, level='poz. 2-3',
           desc='Lewituje, ramiona szeroko, z kuli strzela fioletowy promień w cel.',
           show=[200, 208, 216, 224, 232, 246])
    A.key(0, P())
    A.key(8, P(T=(6, 0, -4), RA=(60, 30, 0), LA=(60, 30, 0), H=(8, 0, 0), Staff={'pitch': 60}, air=0.2,
               RL=(-4, 4, 0), LL=(4, -3, 0)))
    A.key(16, P(T=(-8, 0, 0), RA=(150, 35, 0), LA=(150, 45, 0), H=(-18, 0, 0), Staff={'pitch': 40}, air=0.9,
                RL=(-14, 6, 0), LL=(-4, -4, 0)))
    A.key(22, P(T=(10, 0, -2), RA=(96, 4, 6), LA=(120, 50, 0), H=(4, 0, 0), Staff={'pitch': 2}, air=1.0,
                RL=(-18, 6, 0), LL=(-6, -4, 0)))
    A.key(34, P(T=(12, 0, -2), RA=(94, 4, 6), LA=(118, 52, 0), H=(6, 0, 0), Staff={'pitch': 0}, air=1.05,
                RL=(-18, 6, 0), LL=(-6, -4, 0)))
    A.key(44, P(T=(4, 0, -4), RA=(50, 8, 0), LA=(40, 25, 0), Staff={'pitch': 70}, air=0.4))
    A.key(56, P())
    A.event(24, 'Hit', beam=True)
    A.add_fx('orb', 12, 24, at='StaffTop', r=0.55, col=(0.6, 0.25, 1.0), energy=250, name='a2')
    A.add_fx('beam', 23, 35, **{'from': 'StaffTop'}, dir=(0, -1, -0.12), length=6.5, r0=0.12, r1=0.55,
             col=(0.55, 0.2, 1.0), name='a2')
    A.add_fx('puffs', 14, 40, center=(0, 0, 0.15), count=10, spread=1.6, rise=0.3, col=(0.6, 0.35, 0.9),
             strength=1.2, name='a2')

    # ---- atak 3: opary Delf (obrot z laska + fioletowa mgla)
    A.clip('Attack3', 'Atak 3: Opary Delf', 300, 60, level='poz. 4-5',
           desc='Obrót z laską na płasko, fioletowe opary rozlewają się i spowalniają wrogów (obszar).',
           show=[300, 310, 318, 324, 334, 348])
    A.key(0, P())
    A.key(8, P(T=(8, 0, 30), RA=(40, 30, -30), LA=(30, 30, 0), Staff={'pitch': 20}, H=(4, 0, -20),
               RL=(-8, 6, 30), LL=(8, -4, -30)))
    spin = [(14, 0), (19, -90), (24, -180), (29, -270), (34, -360)]
    for f, ang in spin:
        A.key(f, P(T=(10, 0, ang), RA=(90, 0, -20), LA=(70, 60, 0), Staff={'pitch': 0}, H=(4, 0, 0), air=0.35,
                   RL=(-10, 6, ang), LL=(10, -4, -ang)))
    A.key(42, P(T=(14, 0, -362), RA=(100, 0, 10), LA=(60, 40, 0), Staff={'pitch': -6}, air=0.0,
                RL=(-20, 8, -362), LL=(22, -6, 362)))
    A.key(52, P(T=(4, 0, -364), RA=(30, 6, 0), LA=(22, 18, -6), Staff={'pitch': 84}, RL=(-6, 4, -364),
                LL=(6, -3, 360)))
    A.key(60, P(T=(2, 0, -366), RL=(-6, 4, -366), LL=(6, -3, 366)))
    A.event(30, 'Hit', area=True, slow=0.4)
    sm = rig.attachments['StaffMid'][1]
    st = rig.attachments['StaffTop'][1]
    A.add_fx('trail', 14, 34, joint='Staff', a=sm, b=st, col=(0.8, 0.55, 1.0), len=8, name='a3')
    A.add_fx('puffs', 28, 56, center=(0, -1.2, 0.3), count=18, spread=3.6, rise=0.8, size=0.45,
             col=(0.6, 0.32, 0.9), strength=1.3, name='a3', seed=9)
    A.add_fx('ring', 30, 46, center=(0, 0, 0.1), r0=1.0, r1=5.5, col=(0.55, 0.2, 1.0), th=0.07, name='a3')
    A.finish()
    return A
