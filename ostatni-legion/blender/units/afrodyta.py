"""Afrodyta (wsparcie - morale): rozowo-bialy peplos, zloty pas, dlugie rude wlosy z rozami,
diadem z muszla, berlo z muszla przegrzebka, golebie na ramieniu.
Paleta: roz + biel + zloto (zadna inna jednostka jej nie ma)."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Afrodyta', display='Afrodyta',
    subtitle='Wsparcie · morale: +obrazenia i +szybkosc ataku wiez w zasiegu · blogoslawienstwo, rozany wybuch, zauroczenie',
    cam=dict(target=(0.2, -0.8, 2.9), dist=15.0, dir=(0.62, -1.0, 0.4)), ped_r=2.8,
    extra=dict(Support=dict(Buff='Morale', Stats=['Damage', 'Firerate'], PerLevel=[0.10, 0.12, 0.15, 0.18, 0.21, 0.25],
                            Range=[10, 11, 12, 13, 14, 15], Stack='strongest')),
)
SKIN = (0.80, 0.52, 0.40)


def build(out):
    M.LIB['pink_cloth'] = ((0.66, 0.14, 0.26), 0.0, 0.78, 0.12, 90, {'sheen': 0.8})
    M.LIB['rose'] = ((0.62, 0.04, 0.10), 0.0, 0.5, 0.05, 40, {})
    M.LIB['hair_auburn'] = ((0.32, 0.08, 0.03), 0.0, 0.5, 0.3, 160, {'sheen': 0.6})
    M.LIB['shell'] = ((0.95, 0.80, 0.72), 0.0, 0.35, 0.05, 40, {'coat': 0.6})
    rig = U.body('Afrodyta', out, SKIN,
                 face_kw=dict(style='fem', mouth='smirk', lashes=True, eye=(40, 90, 120), lips=(190, 60, 90), brow_w=0.7),
                 mats=dict(torso='pink_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'
    K.mk(rig, C.bm_box(2.08, 1.08, 0.14, 0.04), 'Torso.neck', 'white_cloth', T, (0, 0, 3.95))
    K.chest_strap(rig, 'white_cloth', 'gold', from_right=True, w=0.5)
    belt = []
    for i in range(25):
        a = 2 * math.pi * i / 24
        belt.append((1.08 * math.cos(a), 0.58 * math.sin(a), 2.55 + 0.05 * math.sin(2 * a)))
    K.mk(rig, C.bm_tube(belt, 0.08, res=3), 'Torso.girdle', 'gold', T, (0, 0, 0))
    K.mk(rig, C.bm_sphere(0.14, 12, 8), 'Torso.girdle_gem', 'rose', T, (0, -0.64, 2.55))
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.mk(rig, C.bm_box(1.14, 1.14, 1.95, 0.06), f'{j}.robe', 'pink_cloth', j, (x, 0, 1.06))
        K.mk(rig, C.bm_box(1.17, 1.17, 0.28, 0.04), f'{j}.hem', 'white_cloth', j, (x, 0, 0.2))
        K.mk(rig, C.bm_box(1.18, 1.18, 0.05, 0.02), f'{j}.hemgold', 'gold', j, (x, 0, 0.38))
        jj = f'{side} Arm'
        xa = K.arm_x(rig, side)
        K.mk(rig, C.bm_box(1.08, 1.08, 0.8, 0.05), f'{jj}.sleeve', 'white_cloth', jj, (xa, 0, 3.6))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.12, 0.03), f'{jj}.armlet', 'gold', jj, (xa, 0, 3.15))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.12, 0.03), f'{jj}.bracelet', 'gold', jj, (xa, 0, 2.3))
    # wlosy: czapa nisko + dlugie fale + roze
    K.hair_cap(rig, 'hair_auburn', hc, length=1.6)
    for sx in (-1, 1):
        for k in range(2):
            lock = [(sx * (0.6 + 0.05 * k), 0.1 + 0.2 * k, hc + 0.3), (sx * 0.72, 0.2 + 0.2 * k, hc - 0.4),
                    (sx * 0.62, 0.3 + 0.2 * k, hc - 1.1), (sx * 0.75, 0.35 + 0.2 * k, hc - 1.6)]
            K.mk(rig, C.bm_tube(lock, 0.12, radii=[1, 1, 0.9, 0.5], res=5), f'Head.wave{sx}{k}', 'hair_auburn', 'Head', (0, 0, 0))
    for k, (x, z) in enumerate(((-0.55, 0.42), (-0.35, 0.5), (0.5, 0.45))):
        K.mk(rig, C.bm_sphere(0.14, 10, 6), f'Head.rose{k}', 'rose', 'Head', (x, -0.45, hc + z))
    K.mk(rig, C.bm_torus(0.715, 0.04, 40, 8), 'Head.diadem', 'gold', 'Head', (0, 0, hc + 0.3))
    shell = C.bm_extrude([(0.3 * math.cos(math.radians(a)), 0.3 * math.sin(math.radians(a)) + 0.0) for a in range(0, 181, 15)] + [(0, -0.12)],
                         0.06, 0.01, 1)
    C.bm_transform(shell, rot=(90, 0, 0))
    K.mk(rig, shell, 'Head.shell', 'gold', 'Head', (0, -0.76, hc + 0.36))
    # golab na lewym ramieniu
    sh = Vector((B['ax'], 0.1, B['ll'] + B['th'] + 0.3))
    K.mk(rig, C.bm_sphere(0.3, 12, 8), 'Left Arm.dove', 'white_cloth', 'Left Arm', tuple(sh), scale=(0.8, 1.3, 0.9))
    K.mk(rig, C.bm_sphere(0.18, 10, 6), 'Left Arm.dovehead', 'white_cloth', 'Left Arm', tuple(sh + Vector((0, -0.35, 0.2))))
    # berlo z muszla
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Sceptre', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Sceptre', 'Sceptre.shaft', 'gold', 1.6, -2.6, 0.07, hx, hz)
    for y in (-0.3, 0.3, -1.6):
        K.mk(rig, C.bm_torus(0.09, 0.03, 14, 6), f'Sceptre.band{y}', 'pink_cloth', 'Sceptre', (hx, y, hz), rot=(90, 0, 0))
    pts = []
    for a in range(-90, 91, 10):
        r = 0.75 * (0.85 + 0.15 * abs(math.cos(math.radians(a * 5))))
        pts.append((r * math.sin(math.radians(a)), r * math.cos(math.radians(a))))
    sb = C.bm_extrude([(0, -0.15)] + pts, 0.12, 0.03, 2)
    C.bm_transform(sb, rot=(0, 90, 0))
    C.bm_transform(sb, rot=(90, 0, 0))
    K.mk(rig, sb, 'Sceptre.shell', 'shell', 'Sceptre', (hx, -2.75, hz))
    K.mk(rig, C.bm_sphere(0.2, 14, 8), 'Sceptre.pearl', 'white_cloth', 'Sceptre', (hx, -2.75, hz - 0.1))
    rig.attach('ShellTop', 'Sceptre', (hx, -3.3, hz))
    rig.attach('Heart', 'Torso', (0, -0.9, 3.4))
    rig.attach('Lips', 'Head', (0, -0.8, hc - 0.2))
    return rig


def animate(rig):
    base = dict(T=(2, 0, -6), H=(4, 4, 6), RA=(30, 6, 0), LA=(30, 26, 10), RL=(-6, 4, 0), LL=(6, -3, 6),
                Sceptre={'pitch': 84})
    A = Animator(rig, base)
    P = A.P
    PINK = (1.0, 0.45, 0.65)

    A.clip('Idle', 'Postoj (petla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(3, 2, -4), H=(2, -4, 4), RA=(33, 6, 0), LA=(34, 28, 12), Sceptre={'pitch': 86}))
    A.key(60, P())
    A.add_fx('orb', 0, 60, at='ShellTop', r=0.35, col=PINK, energy=40)

    A.clip('Attack1', 'Akcja 1: Blogoslawienstwo (puls morale)', 100, 44, level='poz. 0-1',
           desc='Dlonie do serca, rozowy puls wzmacnia wieze w zasiegu.', show=[100, 108, 114, 118, 126, 136])
    A.key(0, P())
    A.key(8, P(T=(6, 0, 0), RA=(80, 0, 60), LA=(80, 0, 60), H=(10, 0, 0), Sceptre={'pitch': 70}))
    A.key(14, P(T=(-8, 0, 0), RA=(150, 30, 0), LA=(150, 30, 0), H=(-18, 0, 0), Sceptre={'pitch': 90}, air=0.3))
    A.key(18, P(T=(-10, 0, 0), RA=(160, 35, 0), LA=(160, 35, 0), H=(-20, 0, 0), Sceptre={'pitch': 90}, air=0.35))
    A.key(30, P(T=(0, 0, -4), RA=(50, 10, 0), LA=(40, 24, 8), Sceptre={'pitch': 84}))
    A.key(44, P())
    A.event(16, 'Buff', kind='Morale')
    A.add_fx('orb', 8, 18, at='Heart', r=0.6, col=PINK, energy=200, name='h')
    A.add_fx('ring', 16, 34, center=(0, 0, 0.1), r0=0.6, r1=7.0, col=PINK, th=0.09, disc=True, name='m')
    A.add_fx('sparks', 16, 30, center='ShellTop', count=18, spread=2.2, col=PINK, name='m')

    A.clip('Attack2', 'Akcja 2: Rozany wybuch', 200, 50, level='poz. 2-3',
           desc='Obrot z berlem, wybuch platkow roz - buff x2 na kilka sekund.', show=[200, 208, 214, 220, 228, 240])
    A.key(0, P())
    A.key(8, P(T=(4, 0, 30), RA=(70, 30, -20), LA=(60, 50, 0), H=(4, 0, -20), RL=(-8, 6, 30), LL=(8, -4, -30)))
    for f, ang in ((12, 0), (16, -120), (20, -240), (24, -360)):
        A.key(f, P(T=(6, 0, ang), RA=(100, 40, -10), LA=(100, 50, -10), Sceptre={'pitch': 20}, H=(0, 0, 0), air=0.3,
                   RL=(-10, 6, ang), LL=(10, -4, -ang)))
    A.key(32, P(T=(-6, 0, -362), RA=(160, 40, 0), LA=(160, 40, 0), Sceptre={'pitch': 90}, H=(-16, 0, 0), air=0.2,
                RL=(-6, 4, -362), LL=(6, -3, 362)))
    A.key(42, P(T=(2, 0, -364), RL=(-6, 4, -364), LL=(6, -3, 364)))
    A.key(50, P(T=(2, 0, -366), RL=(-6, 4, -366), LL=(6, -3, 366)))
    A.event(28, 'Buff', kind='Morale', multiplier=2, duration=5)
    A.add_fx('trail', 12, 26, joint='Sceptre', a=rig.attachments['ShellTop'][1] + Vector((0, 1.5, 0)),
             b=rig.attachments['ShellTop'][1], col=PINK, len=8, name='s')
    A.add_fx('puffs', 26, 46, center=(0, 0, 1.0), count=22, spread=4.5, rise=1.6, size=0.22, col=(0.85, 0.15, 0.3),
             strength=1.5, name='petals', seed=7)
    A.add_fx('ring', 28, 44, center=(0, 0, 0.1), r0=1.0, r1=8.0, col=PINK, th=0.07, name='r2')

    A.clip('Attack3', 'Akcja 3: Zauroczenie', 300, 56, level='poz. 4-5',
           desc='Posyla pocalunek - rozowe serce leci w tlum i na chwile zatrzymuje wrogow.',
           show=[300, 310, 316, 320, 330, 344])
    A.key(0, P())
    A.key(10, P(T=(4, 0, -20), LA=(150, 10, 40), H=(6, -8, 20), RA=(40, 10, 0)))
    A.key(16, P(T=(10, 0, -10), LA=(118, 0, 50), H=(4, -6, 14), RA=(40, 10, 0), Tp=(0, 0.3)))
    A.key(20, P(T=(14, 0, 4), LA=(96, 10, 20), H=(-4, 0, -2), RA=(30, 14, 0), Tp=(0, 0.5), LL=(20, -3, 4), RL=(-14, 4, 0)))
    A.key(36, P(T=(6, 0, 0), LA=(50, 20, 10), Tp=(0, 0.3)))
    A.key(56, P())
    A.event(20, 'Hit', projectile='heart', charm=1.5, area=3)
    A.add_fx('orb', 14, 20, at='Lips', r=0.3, col=PINK, energy=60, name='kiss')
    A.add_fx('projectile', 20, 34, model='heart', **{'from': 'Lips'}, dir=(0, -1, 0.05), speed=0.7, col=PINK,
             glow=PINK, glow_e=80, streak_w=0.12)
    A.add_fx('ring', 34, 48, center=(0, -9.5, 0.2), r0=0.5, r1=4.0, col=PINK, th=0.07, name='charm')
    # wzorzec serca (pocisk)
    hb = C.bm_extrude([(0, -0.5), (0.5, 0.05), (0.45, 0.35), (0.22, 0.45), (0, 0.25), (-0.22, 0.45), (-0.45, 0.35),
                       (-0.5, 0.05)], 0.25, 0.08, 2)
    C.bm_transform(hb, rot=(90, 0, 0))
    U.fx_template([(hb, 'glow_red')], 'heart')
    A.finish()
    return A
