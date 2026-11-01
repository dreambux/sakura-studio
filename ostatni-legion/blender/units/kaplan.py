"""Kaplan Zeusa (legendarna): starzec z dluga siwa broda, zloty wieniec z piorunem, biala szata
z krolewskim blekitem i zlotym meandrem, blekitny plaszcz ze zlota obwodka, berlo ze zlotymi
skrzydlami orla i swiecacym piorunem, zloty napiersnik z orlem.
Paleta: biel + krolewski blekit + zloto + blekitne pioruny."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Kaplan', display='Kapłan Zeusa',
    subtitle='Legendarna · pioruny łańcuchowe · piorun z nieba, łańcuch piorunów, gniew Zeusa',
    cam=dict(target=(0.2, -1.6, 3.2), dist=17.0, dir=(0.62, -1.0, 0.38)), ped_r=2.9,
)
SKIN = (0.66, 0.38, 0.24)


def build(out):
    M.LIB['royal_blue'] = ((0.012, 0.05, 0.30), 0.0, 0.75, 0.12, 90, {'sheen': 0.7})
    rig = U.body('Kaplan', out, SKIN, face_kw=dict(style='old', mouth=None, brow=(225, 225, 220), brow_w=1.2),
                 mats=dict(torso='white_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- szata
    K.chest_strap(rig, 'royal_blue', 'gold', from_right=False, w=0.6)
    K.belt(rig, 2.4, 'gold', 'gold', h=0.16, studs=False)
    for i in range(6):
        K.mk(rig, C.bm_box(0.12, 0.05, 0.12, 0.02), f'Torso.meander{i}', 'gold', T, (-0.75 + i * 0.3, -0.56, 2.25),
             rot=(0, 45, 0))
    # zloty napiersnik z orlem
    K.mk(rig, C.bm_cyl(0.36, 0.06, 32, bevel=0.02), 'Torso.pectoral', 'gold', T, (0.0, -0.57, 3.5), rot=(90, 0, 0))
    for sgn in (-1, 1):
        w = C.bm_extrude(U.wing_poly(0.5, flip=sgn < 0), 0.04, 0.008, 1)
        C.bm_transform(w, rot=(0, 0, sgn * 20))
        C.bm_transform(w, rot=(90, 0, 0))
        K.mk(rig, w, f'Torso.eaglewing{sgn}', 'gold', T, (sgn * 0.05, -0.62, 3.52))
    K.mk(rig, C.bm_sphere(0.09, 12, 8), 'Torso.pectoralgem', 'glow_lightning', T, (0, -0.64, 3.5))
    K.cape(rig, 'royal_blue', 'gold', length=3.6, top_w=2.0, bot_w=3.0, flare=0.7, clasp='gold')
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.mk(rig, C.bm_box(1.14, 1.14, 1.95, 0.06), f'{j}.robe', 'white_cloth', j, (x, 0, 1.06))
        K.mk(rig, C.bm_box(1.17, 1.17, 0.32, 0.04), f'{j}.hem', 'royal_blue', j, (x, 0, 0.22))
        for z in (0.07, 0.4):
            K.mk(rig, C.bm_box(1.19, 1.19, 0.05, 0.02), f'{j}.hemgold{z}', 'gold', j, (x, 0, z))
        for k in range(3):
            K.mk(rig, C.bm_box(0.11, 0.05, 0.11, 0.02), f'{j}.meander{k}', 'gold', j,
                 (x - 0.3 + 0.3 * k, -0.6, 0.23), rot=(0, 45, 0))
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        K.mk(rig, C.bm_box(1.1, 1.1, 1.3, 0.06), f'{j}.sleeve', 'white_cloth', j, (x, 0, 3.32))
        K.mk(rig, C.bm_box(1.12, 1.12, 0.1, 0.03), f'{j}.cuff', 'royal_blue', j, (x, 0, 2.7))
        K.mk(rig, C.bm_box(1.13, 1.13, 0.04, 0.01), f'{j}.cuffgold', 'gold', j, (x, 0, 2.63))

    # ---- glowa: siwe wlosy, broda, wasy, wieniec z piorunem
    K.hair_block(rig, 'hair_white', hc, back=0.6, length=1.25)
    beard = [(-0.5, 0.0), (0.5, 0.0), (0.46, -0.35), (0.3, -0.85), (0.12, -1.2), (0.0, -1.32), (-0.12, -1.2),
             (-0.3, -0.85), (-0.46, -0.35)]
    bm = C.bm_extrude(beard, 0.34, 0.12, 3)
    C.bm_transform(bm, rot=(90, 0, 0))
    K.mk(rig, bm, 'Head.beard', 'hair_white', 'Head', (0, -0.55, hc - 0.18))
    for k in range(4):
        x = -0.3 + 0.2 * k
        K.mk(rig, C.bm_box(0.04, 0.03, 0.7 - abs(x) * 0.6, 0.01), f'Head.beardline{k}', 'linen', 'Head',
             (x, -0.73, hc - 0.65))
    for sx in (-1, 1):
        mus = [(0.0, -0.66, hc - 0.18), (sx * 0.22, -0.68, hc - 0.16), (sx * 0.42, -0.62, hc - 0.28),
               (sx * 0.5, -0.58, hc - 0.45)]
        K.mk(rig, C.bm_tube(mus, 0.07, radii=[1, 1, 0.8, 0.4], res=4), f'Head.mustache{sx}', 'hair_white', 'Head', (0, 0, 0))
        lock = [(sx * 0.62, -0.1, hc + 0.2), (sx * 0.68, -0.15, hc - 0.3), (sx * 0.66, -0.05, hc - 0.8)]
        K.mk(rig, C.bm_tube(lock, 0.1, radii=[1, 0.9, 0.5], res=4), f'Head.lock{sx}', 'hair_white', 'Head', (0, 0, 0))
    K.laurel(rig, 'Head', (0, 0, hc + 0.38), R=0.67, n=9)
    bolt = C.bm_extrude(U.bolt_poly(0.5), 0.05, 0.01, 1)
    C.bm_transform(bolt, rot=(90, 0, 0))
    K.mk(rig, bolt, 'Head.crownbolt', 'glow_lightning', 'Head', (0, -0.7, hc + 0.5))

    # ---- berlo
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Sceptre', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Sceptre', 'Sceptre.shaft', 'gold', 2.05, -3.0, 0.08, hx, hz)
    for y in (-0.3, 0.3, -1.4, 1.2):
        K.mk(rig, C.bm_torus(0.095, 0.03, 14, 6), f'Sceptre.band{y}', 'royal_blue', 'Sceptre', (hx, y, hz), rot=(90, 0, 0))
    K.mk(rig, C.bm_sphere(0.16, 16, 10), 'Sceptre.knob', 'gold', 'Sceptre', (hx, -3.05, hz))
    for sgn in (-1, 1):
        w = C.bm_extrude(U.wing_poly(1.0, flip=sgn < 0), 0.05, 0.01, 1)
        C.bm_transform(w, rot=(0, 0, sgn * 25))
        C.bm_transform(w, rot=(0, 0, 180))
        K.mk(rig, w, f'Sceptre.wing{sgn}', 'gold', 'Sceptre', (hx, -3.15, hz))
    bolt = C.bm_extrude(U.bolt_poly(1.5), 0.08, 0.015, 1)
    C.bm_transform(bolt, rot=(0, 0, 180))
    K.mk(rig, bolt, 'Sceptre.bolt', 'glow_lightning', 'Sceptre', (hx, -3.75, hz))
    rig.attach('SceptreTop', 'Sceptre', (hx, -4.45, hz))
    rig.attach('SceptreMid', 'Sceptre', (hx, -2.6, hz))
    rig.attach('LeftHand', 'Left Arm', tuple(rig.hand['Left Arm']))
    return rig


def animate(rig):
    base = dict(T=(2, 0, -6), H=(2, 0, 5), RA=(30, 8, 0), LA=(24, 14, 4), RL=(-6, 4, 0), LL=(6, -3, 4),
                Sceptre={'pitch': 84})
    A = Animator(rig, base)
    P = A.P
    LB = (0.35, 0.6, 1.0)

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(4, 0, -4), H=(0, 0, 3), RA=(32, 8, 0), LA=(28, 16, 6), Sceptre={'pitch': 86}, cape=9))
    A.key(60, P())
    A.add_fx('sparks', 0, 30, center='SceptreTop', count=6, spread=0.6, col=LB, fixed=False, name='idle1')
    A.add_fx('glowpoint', 0, 60, at='SceptreTop', col=LB, energy=60)

    # ---- atak 1: piorun z nieba
    A.clip('Attack1', 'Atak 1: Piorun', 100, 44, level='poz. 0-1',
           desc='Berło w niebo, piorun uderza w cel.', show=[100, 108, 114, 116, 122, 134])
    tgt = (0.0, -5.2, 0.05)
    A.key(0, P())
    A.key(8, P(T=(8, 0, -8), RA=(40, 10, 0), LA=(30, 30, 0), H=(8, 0, 0), Sceptre={'pitch': 70}, Tp=(0, -0.1)))
    A.key(14, P(T=(-10, 0, 0), RA=(172, 4, 0), LA=(60, 50, 0), H=(-24, 0, 0), Sceptre={'pitch': 90}, air=0.2, cape=18))
    A.key(18, P(T=(14, 0, 0), RA=(120, 4, 6), LA=(40, 40, 0), H=(0, 0, 0), Sceptre={'pitch': 40}, Tp=(0, 0.3),
                LL=(20, -3, 4), RL=(-14, 4, 0), cape=10))
    A.key(28, P(T=(10, 0, -4), RA=(80, 6, 4), Sceptre={'pitch': 60}, Tp=(0, 0.2)))
    A.key(44, P())
    A.event(16, 'Hit', lightning=True)
    A.add_fx('lightning', 15, 21, a=(0.6, -5.6, 13.0), b=tgt, col=LB, r=0.07, amp=0.05, energy=900, seed=3)
    A.add_fx('lightning', 13, 16, a='SceptreTop', b=(0.3, -1.2, 12.0), col=LB, r=0.04, amp=0.05, energy=200, seed=8,
             branches=0, name='up')
    A.add_fx('ring', 16, 30, center=tgt, r0=0.3, r1=3.0, col=LB, th=0.08, disc=True, name='l1')
    A.add_fx('sparks', 16, 26, center=tgt, count=18, spread=2.0, col=LB, name='l1')

    # ---- atak 2: lancuch piorunow
    A.clip('Attack2', 'Atak 2: Łańcuch piorunów', 200, 48, level='poz. 2-3',
           desc='Pchnięcie berłem – piorun skacze po kolejnych wrogach (3 cele).', show=[200, 208, 214, 218, 222, 236])
    t1, t2, t3 = (-1.4, -4.6, 0.9), (1.6, -6.4, 0.9), (-0.6, -8.4, 0.9)
    A.key(0, P())
    A.key(8, P(T=(-6, 0, -30), RA=(150, 20, -20), LA=(60, 40, 0), H=(-6, 0, 24), Sceptre={'pitch': 30},
               Tp=(0, -0.2), cape=4))
    A.key(13, P(T=(20, 0, 6), RA=(96, 0, 8), LA=(50, 50, 0), H=(-4, 0, -4), Sceptre={'pitch': 0}, Tp=(0, 0.7),
                LL=(32, -3, 4), RL=(-28, 4, 0), cape=20))
    A.key(28, P(T=(18, 0, 4), RA=(94, 0, 8), LA=(48, 50, 0), H=(-4, 0, -4), Sceptre={'pitch': 0}, Tp=(0, 0.7),
                LL=(32, -3, 4), RL=(-28, 4, 0), cape=14))
    A.key(38, P(T=(8, 0, -4), RA=(50, 8, 4), Sceptre={'pitch': 60}, Tp=(0, 0.3)))
    A.key(48, P())
    A.event(14, 'Hit', chain=1)
    A.event(18, 'Hit', chain=2)
    A.event(22, 'Hit', chain=3)
    A.add_fx('lightning', 13, 28, a='SceptreTop', b=t1, col=LB, r=0.05, amp=0.06, energy=400, seed=1, name='c1')
    A.add_fx('lightning', 17, 28, a=t1, b=t2, col=LB, r=0.05, amp=0.07, energy=400, seed=2, name='c2')
    A.add_fx('lightning', 21, 28, a=t2, b=t3, col=LB, r=0.05, amp=0.07, energy=400, seed=4, name='c3')
    for k, t in enumerate((t1, t2, t3)):
        A.add_fx('sparks', 14 + 4 * k, 24 + 4 * k, center=t, count=12, spread=1.2, col=LB, name=f'c{k}')

    # ---- atak 3: gniew Zeusa
    A.clip('Attack3', 'Atak 3: Gniew Zeusa', 300, 72, level='poz. 4-5',
           desc='Lewituje wśród burzy, oba ramiona w górę – seria piorunów wali w cały obszar.',
           show=[300, 312, 324, 330, 338, 356])
    A.key(0, P())
    A.key(12, P(T=(12, 0, 0), RA=(60, 30, 0), LA=(60, 30, 0), H=(10, 0, 0), Sceptre={'pitch': 60}, air=0.3, cape=4))
    A.key(22, P(T=(-12, 0, 0), RA=(168, 20, 0), LA=(160, 40, 0), H=(-22, 0, 0), Sceptre={'pitch': 90}, air=1.3,
                RL=(-16, 6, 0), LL=(-4, -4, 0), cape=24))
    A.key(46, P(T=(-14, 0, 0), RA=(172, 22, 0), LA=(164, 44, 0), H=(-24, 0, 0), Sceptre={'pitch': 90}, air=1.45,
                RL=(-18, 6, 0), LL=(-6, -4, 0), cape=26))
    A.key(58, P(T=(8, 0, 0), RA=(60, 20, 0), LA=(50, 30, 0), H=(4, 0, 0), Sceptre={'pitch': 70}, air=0.4))
    A.key(72, P())
    strikes = [(26, (-1.8, -4.4, 0.05)), (30, (1.6, -5.2, 0.05)), (34, (-0.2, -6.4, 0.05)), (38, (2.4, -3.2, 0.05)),
               (42, (-2.6, -2.6, 0.05))]
    for k, (f, p) in enumerate(strikes):
        A.event(f, 'Hit', area=True, lightning=True)
        A.add_fx('lightning', f, f + 5, a=(p[0] + 0.5, p[1] - 0.4, 13.0), b=p, col=LB, r=0.07, amp=0.05, energy=700,
                 seed=10 + k, name=f's{k}')
        A.add_fx('ring', f, f + 12, center=p, r0=0.3, r1=2.2, col=LB, th=0.07, disc=True, name=f's{k}')
    A.add_fx('orb', 20, 50, at='SceptreTop', r=0.6, col=LB, energy=300, name='storm')
    A.add_fx('lightning', 22, 48, a='SceptreTop', b='LeftHand', col=LB, r=0.03, amp=0.12, energy=150, seed=40,
             branches=1, name='arc')
    A.finish()
    return A
