"""Hermes (wsparcie - szybkosc): skrzydlaty kapelusz petasos, kaduceusz z dwoma wezami i skrzydlami,
skrzydlate sandaly, blekitna chlamida, torba poslanca. Szybsze odnowienie wiez + tansze ulepszenia.
Paleta: blekit nieba + biel + zloto + braz skory."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Hermes', display='Hermes',
    subtitle='Wsparcie · szybkosc: krotsze odnowienie wiez, tansze ulepszenia · pospiech, skrzydlate kroki, kaduceusz',
    cam=dict(target=(0.2, -0.8, 2.9), dist=15.0, dir=(0.62, -1.0, 0.4)), ped_r=2.8,
    extra=dict(Support=dict(Buff='Haste', Stats=['Cooldown', 'UpgradeCost'], PerLevel=[0.08, 0.10, 0.12, 0.15, 0.18, 0.22],
                            Range=[10, 11, 12, 13, 14, 15], Stack='strongest')),
)
SKIN = (0.70, 0.40, 0.25)


def build(out):
    M.LIB['sky_cloth'] = ((0.10, 0.35, 0.70), 0.0, 0.78, 0.12, 90, {'sheen': 0.6})
    M.LIB['feather'] = ((0.92, 0.92, 0.90), 0.0, 0.7, 0.1, 80, {'sheen': 0.4})
    M.LIB['hair_brown'] = ((0.12, 0.06, 0.03), 0.0, 0.55, 0.3, 160, {'sheen': 0.6})
    rig = U.body('Hermes', out, SKIN, face_kw=dict(style='fem', mouth='smirk', lips=(150, 70, 60), brow_w=1.0),
                 mats=dict(torso='white_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'
    K.chest_strap(rig, 'leather', 'gold', from_right=False, w=0.2)
    K.mk(rig, C.bm_box(0.7, 0.4, 0.6, 0.08), 'Torso.bag', 'leather', T, (0.95, -0.35, 2.4))
    K.belt(rig, 2.2, 'leather', 'gold', h=0.16)
    K.cape(rig, 'sky_cloth', 'gold', length=2.2, top_w=1.4, bot_w=2.2, flare=0.9, clasp='gold')
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.leg_skirt(rig, side, 'white_cloth', 1.4, 2.0, 0.08)
        K.mk(rig, C.bm_box(1.1, 1.1, 0.08, 0.02), f'{j}.hem', 'sky_cloth', j, (x, 0, 1.42))
        K.sandals(rig, side, 'leather', 'gold', bands=(0.32, 0.62, 0.92))
        for sy in (-1, 1):
            w = C.bm_extrude([(0, 0), (0.5, 0.15), (0.75, 0.5), (0.3, 0.35)], 0.04, 0.01, 1)
            C.bm_transform(w, rot=(90, 0, 0))
            K.mk(rig, w, f'{j}.wing{sy}', 'feather', j, (x + (0.55 if side == 'Left' else -0.55), 0.2, 0.55),
                 rot=(0, 0, 90 + (0 if side == 'Left' else 180) + sy * 10))
    K.hair_block(rig, 'hair_brown', hc, back=0.6, length=0.8)
    # petasos ze skrzydlami
    prof = [(0.0, 0.0), (1.1, 0.0), (1.15, 0.05), (0.66, 0.12), (0.62, 0.45), (0.3, 0.6), (0.0, 0.62)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=40)), 'Head.petasos', 'leather_light', 'Head', (0, 0, hc + 0.28))
    K.mk(rig, C.bm_torus(0.64, 0.04, 32, 6), 'Head.band', 'gold', 'Head', (0, 0, hc + 0.42))
    for sx in (-1, 1):
        for k in range(3):
            w = C.bm_extrude([(0, 0), (0.6 - k * 0.1, 0.15), (0.9 - k * 0.15, 0.5), (0.35, 0.3)], 0.04, 0.01, 1)
            C.bm_map(w, lambda co, sx=sx: (sx * co.x, co.z, co.y))
            K.mk(rig, K.bmesh_recalc(w), f'Head.wing{sx}{k}', 'feather', 'Head', (sx * 0.62, 0.1 + k * 0.1, hc + 0.5 + k * 0.05),
                 rot=(0, sx * -25, 0))
    # kaduceusz
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    rig.joint('Caduceus', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Caduceus', 'Caduceus.rod', 'gold', 1.0, -2.6, 0.07, hx, hz)
    for sgn in (-1, 1):
        pts = [(hx + sgn * 0.25 * math.sin(t * 2.4), -0.4 - t * 0.7, hz + sgn * 0.25 * math.cos(t * 2.4)) for t in
               [i / 3 for i in range(10)]]
        K.mk(rig, C.bm_tube(pts, 0.07, res=4), f'Caduceus.snake{sgn}', 'snake', 'Caduceus', (0, 0, 0))
        w = C.bm_extrude([(0, 0), (0.6, 0.2), (0.9, 0.6), (0.4, 0.4)], 0.05, 0.01, 1)
        C.bm_map(w, lambda co, sgn=sgn: (sgn * co.x, -co.y, co.z))
        K.mk(rig, K.bmesh_recalc(w), f'Caduceus.wing{sgn}', 'feather', 'Caduceus', (hx, -2.6, hz), rot=(90, 0, 0))
    K.mk(rig, C.bm_sphere(0.18, 12, 8), 'Caduceus.orb', 'gold', 'Caduceus', (hx, -2.75, hz))
    rig.attach('CaduceusTop', 'Caduceus', (hx, -2.9, hz))
    return rig


def animate(rig):
    base = dict(T=(4, 0, -8), H=(0, 0, 8), RA=(40, 10, 0), LA=(20, 20, 0), RL=(-14, 6, 0), LL=(14, -4, 6),
                Caduceus={'pitch': 70})
    A = Animator(rig, base)
    P = A.P
    SKY = (0.45, 0.75, 1.0)
    A.clip('Idle', 'Postoj (petla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(15, P(air=0.12, RL=(-16, 6, 0), LL=(16, -4, 6)))
    A.key(30, P(T=(6, 0, -6), H=(2, 0, 4), air=0.0, Caduceus={'pitch': 74}))
    A.key(45, P(air=0.12))
    A.key(60, P())

    A.clip('Attack1', 'Akcja 1: Pospiech', 100, 36, level='poz. 0-1',
           desc='Blyskawiczny obrot - niebieski puls skraca odnowienie wiez w zasiegu.', show=[100, 104, 108, 112, 120, 130])
    A.key(0, P())
    for f, ang in ((4, -90), (8, -180), (12, -270), (16, -360)):
        A.key(f, P(T=(6, 0, ang - 8), RA=(90, 20, 0), Caduceus={'pitch': 0}, LA=(70, 50, 0), air=0.4,
                   RL=(-20, 6, ang), LL=(10, -4, -ang)))
    A.key(24, P(T=(4, 0, -368), RL=(-14, 6, -360), LL=(14, -4, 366)))
    A.key(36, P(T=(4, 0, -368), RL=(-14, 6, -360), LL=(14, -4, 366)))
    A.event(14, 'Buff', kind='Haste')
    A.add_fx('trail', 3, 17, joint='Caduceus', a=rig.attachments['CaduceusTop'][1] + Vector((0, 1.5, 0)),
             b=rig.attachments['CaduceusTop'][1], col=SKY, len=8, name='spin')
    A.add_fx('ring', 14, 30, center=(0, 0, 0.1), r0=0.8, r1=7.0, col=SKY, th=0.08, disc=True, name='haste')

    A.clip('Attack2', 'Akcja 2: Skrzydlate kroki', 200, 44, level='poz. 2-3',
           desc='Wyskok i zawis na skrzydlatych sandalach - mocniejszy buff szybkosci.', show=[200, 206, 212, 218, 228, 238])
    A.key(0, P())
    A.key(6, P(T=(14, 0, 0), RA=(20, 20, 0), LA=(20, 20, 0), RL=(-30, 6, 0), LL=(30, -4, 0)))
    A.key(12, P(T=(-10, 0, 0), RA=(150, 40, 0), LA=(150, 40, 0), Caduceus={'pitch': 90}, air=2.2, RL=(-20, 6, 0), LL=(10, -4, 0)))
    A.key(26, P(T=(-8, 0, 0), RA=(155, 40, 0), LA=(150, 40, 0), Caduceus={'pitch': 90}, air=2.5, RL=(-24, 6, 0), LL=(8, -4, 0)))
    A.key(36, P(air=0.3))
    A.key(44, P())
    A.event(14, 'Buff', kind='Haste', multiplier=1.6, duration=5)
    A.add_fx('sparks', 10, 30, center=(0, 0, 0.6), count=20, spread=1.8, col=SKY, fixed=True, name='lift')
    A.add_fx('ring', 14, 32, center=(0, 0, 0.1), r0=1.0, r1=7.5, col=SKY, th=0.07, name='r2')

    A.clip('Attack3', 'Akcja 3: Kaduceusz', 300, 50, level='poz. 4-5',
           desc='Rzut energia kaduceusza - fala usypia wrogow (spowolnienie), wieze dostaja buff.',
           show=[300, 308, 314, 318, 328, 340])
    A.key(0, P())
    A.key(8, P(T=(-6, 0, -30), RA=(190, 20, 0), Caduceus={'pitch': 30}, H=(-6, 0, 30), Tp=(0, -0.2)))
    A.key(14, P(T=(18, 0, 10), RA=(100, 0, 10), Caduceus={'pitch': -10}, H=(-4, 0, -8), Tp=(0, 0.6), LL=(28, -4, 4), RL=(-24, 6, 0)))
    A.key(26, P(T=(12, 0, 4), RA=(80, 0, 10), Caduceus={'pitch': 0}, Tp=(0, 0.5)))
    A.key(50, P())
    A.event(15, 'Hit', slow=0.5, duration=3, area=4)
    A.add_fx('beam', 14, 26, **{'from': 'CaduceusTop'}, dir=(0, -1, -0.1), length=7, r0=0.2, r1=1.4, col=SKY, name='wave')
    A.add_fx('ring', 18, 34, center=(0, -7.5, 0.2), r0=0.6, r1=4.0, col=SKY, th=0.08, name='sleep')
    A.finish()
    return A
