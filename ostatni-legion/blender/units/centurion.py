"""Centurion (wsparcie - dowodzenie): kolczuga, falery (zlote medale), poprzeczny BIALY grzebien,
karmazynowy plaszcz, posrebrzane nagolenniki, laska winna (vitis). +zasieg wiez w zasiegu.
Paleta: srebro + bordo + biel (inna niz Gladiator i Legionista)."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Centurion', display='Centurion',
    subtitle='Wsparcie · dowodzenie: +zasieg wiez w zasiegu · rozkaz, okrzyk bojowy, Testudo!',
    cam=dict(target=(0.2, -0.8, 2.9), dist=15.0, dir=(0.62, -1.0, 0.4)), ped_r=2.8,
    extra=dict(Support=dict(Buff='Command', Stats=['Range'], PerLevel=[0.10, 0.12, 0.15, 0.18, 0.22, 0.25],
                            Range=[10, 11, 12, 13, 14, 15], Stack='strongest', Ability='Testudo')),
)
SKIN = (0.60, 0.31, 0.18)


def build(out):
    M.LIB['chainmail'] = ((0.36, 0.37, 0.40), 1.0, 0.45, 0.6, 260, {})
    M.LIB['crest_white'] = ((0.85, 0.84, 0.80), 0.0, 0.7, 0.35, 200, {'sheen': 0.2})
    M.LIB['crest_white2'] = ((0.62, 0.60, 0.58), 0.0, 0.7, 0.35, 200, {'sheen': 0.2})
    rig = U.body('Centurion', out, SKIN, face_kw=dict(style='angry', mouth='teeth', scar=True), mats=dict(torso='chainmail'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'
    K.mk(rig, C.bm_box(2.16, 1.16, 0.5, 0.05), 'Torso.shoulders', 'chainmail', T, (0, 0, 3.8))
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.12, 0.06, 1.6, 0.02), f'Torso.harness{sx}', 'leather_dark', T, (sx * 0.45, -0.58, 3.2))
    for k, (x, z) in enumerate(((-0.45, 3.6), (0.45, 3.6), (-0.45, 3.1), (0.45, 3.1), (-0.45, 2.6), (0.45, 2.6), (0, 3.35), (0, 2.85))):
        K.mk(rig, C.bm_cyl(0.17, 0.06, 18, bevel=0.02), f'Torso.phalera{k}', 'gold' if k % 3 else 'silver', T,
             (x, -0.64, z), rot=(90, 0, 0))
    K.belt(rig, 2.15, 'leather_dark', 'silver')
    for i, x in enumerate((-0.27, -0.09, 0.09, 0.27)):
        K.mk(rig, C.bm_box(0.11, 0.05, 0.66, 0.02), f'Torso.apron{i}', 'leather_dark', T, (x, -0.62, 1.72))
    K.cape(rig, 'red_dark', 'silver', length=2.8, clasp='silver')
    for side in ('Right', 'Left'):
        K.leg_skirt(rig, side, 'red_dark', 1.45, 2.0, 0.09)
        K.greave(rig, side, 'silver', 'gold', z0=0.24, z1=1.2)
        K.sandals(rig, side, 'leather_dark', 'leather_dark', bands=(0.3,), lace=False)
        j = f'{side} Arm'
        K.mk(rig, C.bm_box(1.1, 1.1, 0.6, 0.05), f'{j}.sleeve', 'chainmail', j, (K.arm_x(rig, side), 0, 3.7))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.4, 0.05), f'{j}.bracer', 'leather_dark', j, (K.arm_x(rig, side), 0, 2.4))
    # galea z poprzecznym bialym grzebieniem
    rim = hc + 0.22
    K.dome(rig, 'Head', 'Head.helmet', 'silver', (0, 0, rim), r=0.69, h=0.52)
    K.ring(rig, 'Head', 'Head.rim', 'gold', (0, 0, rim + 0.01), 0.69, 0.045)
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.07, 0.46, 0.58, 0.03), f'Head.cheek{sx}', 'silver', 'Head', (sx * 0.66, 0.03, hc - 0.07))
    K.crest(rig, 'Head', (0, 0, rim + 0.5), length=1.9, height=0.7, width=0.26, transverse=True, n=23,
            mats=('crest_white', 'crest_white2'), base_mat='gold')
    # laska winna (vitis) + gladius przy lewym boku
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Vitis', 'Right Arm', tuple(hand), follow='Right Arm')
    pts = [(hx, 0.5, hz), (hx + 0.05, -0.4, hz + 0.03), (hx - 0.03, -1.3, hz - 0.02), (hx + 0.04, -2.1, hz)]
    K.mk(rig, C.bm_tube(pts, 0.08, radii=[1, 0.9, 0.85, 0.7], res=5), 'Vitis.staff', 'wood', 'Vitis', (0, 0, 0))
    K.mk(rig, C.bm_sphere(0.14, 12, 8), 'Vitis.knob', 'silver', 'Vitis', (hx + 0.04, -2.2, hz))
    rig.attach('VitisTip', 'Vitis', (hx + 0.04, -2.25, hz))
    K.mk(rig, C.bm_box(0.2, 0.1, 1.0, 0.03), 'Torso.scabbard', 'leather_dark', T, (1.08, 0.58, 1.75), rot=(-12, 0, 0))
    K.mk(rig, C.bm_sphere(0.1, 12, 8), 'Torso.pommel', 'silver', T, (1.08, 0.5, 2.6))
    return rig


def animate(rig):
    base = dict(T=(4, 0, -6), H=(0, 0, 6), RA=(34, 8, 4), LA=(10, 20, -6), RL=(-10, 6, 0), LL=(10, -4, 6),
                Vitis={'pitch': 50})
    A = Animator(rig, base)
    P = A.P
    COL = (1.0, 0.85, 0.45)
    A.clip('Idle', 'Postoj (petla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(5, 0, -4), H=(2, 0, 10), RA=(36, 8, 4), Vitis={'pitch': 54}))
    A.key(60, P())

    A.clip('Attack1', 'Akcja 1: Rozkaz (wskazanie celu)', 100, 40, level='poz. 0-1',
           desc='Wskazuje laska cel - wieze w zasiegu dostaja +zasieg.', show=[100, 106, 112, 116, 124, 134])
    A.key(0, P())
    A.key(6, P(T=(-4, 0, -20), RA=(140, 10, 0), Vitis={'pitch': 60}, H=(-6, 0, 20), Tp=(0, -0.1)))
    A.key(12, P(T=(14, 0, 4), RA=(96, 0, 6), Vitis={'pitch': 0}, H=(-2, 0, -4), Tp=(0, 0.4), LL=(22, -4, 4), RL=(-16, 6, 0)))
    A.key(22, P(T=(12, 0, 4), RA=(94, 0, 6), Vitis={'pitch': 0}, H=(-2, 0, -4), Tp=(0, 0.4), LL=(22, -4, 4), RL=(-16, 6, 0)))
    A.key(40, P())
    A.event(12, 'Buff', kind='Command')
    A.add_fx('ring', 12, 30, center=(0, 0, 0.1), r0=0.8, r1=7.0, col=COL, th=0.08, disc=True, name='cmd')
    A.add_fx('orb', 10, 20, at='VitisTip', r=0.35, col=COL, energy=80, name='tip')

    A.clip('Attack2', 'Akcja 2: Okrzyk bojowy', 200, 46, level='poz. 2-3',
           desc='Unosi laske i krzyczy - fala dzwieku, chwilowy mocniejszy buff.', show=[200, 208, 214, 218, 228, 238])
    A.key(0, P())
    A.key(8, P(T=(16, 0, 0), H=(14, 0, 0), RA=(60, 20, 10), LA=(40, 30, 0), Tp=(0, -0.15)))
    A.key(14, P(T=(-12, 0, 0), H=(-22, 0, 0), RA=(170, 10, 0), Vitis={'pitch': 90}, LA=(80, 60, 0), air=0.15))
    A.key(26, P(T=(-10, 0, 0), H=(-20, 0, 0), RA=(168, 10, 0), Vitis={'pitch': 90}, LA=(80, 60, 0)))
    A.key(46, P())
    A.event(14, 'Buff', kind='Command', multiplier=1.5, duration=5)
    for k in range(3):
        A.add_fx('ring', 14 + k * 4, 30 + k * 4, center=(0, 0, 3.0 + k * 0.3), r0=0.6, r1=6.0, col=COL, th=0.06, flat=1.0,
                 name=f'shout{k}')

    A.clip('Attack3', 'Akcja 3: Testudo!', 300, 54, level='poz. 4-5',
           desc='Uderza laska o ziemie - zlote tarcze chronia sasiednie wieze (blokuja efekty Zarazowca).',
           show=[300, 308, 314, 318, 330, 344])
    A.key(0, P())
    A.key(8, P(T=(-8, 0, 0), RA=(160, 10, 0), Vitis={'pitch': 100}, H=(-10, 0, 0), air=0.4, LL=(20, -4, 0), RL=(-6, 6, 0)))
    A.key(14, P(T=(24, 0, 0), RA=(60, 0, 10), Vitis={'pitch': -70}, H=(10, 0, 0), RL=(-28, 8, 0), LL=(30, -6, 0)))
    A.key(18, P(T=(26, 0, 0), RA=(56, 0, 10), Vitis={'pitch': -76}, H=(12, 0, 0), RL=(-30, 8, 0), LL=(32, -6, 0)))
    A.key(36, P(T=(10, 0, 0), RA=(40, 8, 4), Vitis={'pitch': 30}))
    A.key(54, P())
    A.event(15, 'Ability', kind='Testudo', duration=6)
    A.add_fx('ring', 15, 30, center=(0, -1.5, 0.1), r0=0.5, r1=5.0, col=COL, th=0.1, name='slam')
    A.add_fx('sparks', 15, 24, center='VitisTip', count=20, spread=2.0, col=COL, name='slam')
    for k in range(6):
        a = 2 * math.pi * k / 6
        A.add_fx('orb', 18 + k, 40, at=(math.cos(a) * 4.5, math.sin(a) * 4.5, 1.6), r=0.7, col=COL, energy=40,
                 name=f'shield{k}')
    A.finish()
    return A
