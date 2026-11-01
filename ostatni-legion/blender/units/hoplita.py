"""Hoplita Spartanski: helm koryncki z czarnym grzebieniem, brazowy pancerz miesniowy,
lniane pteryges, nagolenniki, karmazynowy plaszcz, okragla aspis z lambda, dlugi dory.
Paleta: braz + karmazyn + czern (inaczej niz Gladiator/Legionista)."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Hoplita', display='Hoplita Spartański',
    subtitle='Militarna · tarcza, odpycha, falanga · dory: pchnięcie, odepchnięcie tarczą, potrójne pchnięcie',
    cam=dict(target=(0.0, -0.8, 2.7), dist=14.5, dir=(0.72, -1.0, 0.42)), ped_r=2.8,
)
SKIN = (0.55, 0.27, 0.14)


def corinthian(rig, hc):
    """Helm koryncki: skorupa z otworem w ksztalcie T (oczy i usta widoczne) + nosal."""
    outer = [(0.63, -0.56), (0.67, -0.35), (0.69, -0.1), (0.69, 0.12), (0.67, 0.33), (0.60, 0.50),
             (0.47, 0.63), (0.27, 0.71), (0.0, 0.74)]
    inner = [(0.0, 0.69), (0.25, 0.66), (0.44, 0.58), (0.56, 0.46), (0.62, 0.31), (0.64, 0.12),
             (0.64, -0.1), (0.625, -0.35), (0.60, -0.56)]

    def densify(pts, n=3):
        out = []
        for a, b in zip(pts, pts[1:]):
            for i in range(n):
                t = i / n
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        out.append(pts[-1])
        return out
    prof = densify(outer) + densify(inner) + [outer[0]]
    bm = C.bm_lathe(prof, segs=56)
    import bmesh
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > -0.2:
            continue
        x, z = abs(c.x), c.z
        eyes = x < 0.40 and -0.10 < z < 0.30
        mouth = x < 0.27 and z <= -0.10
        nasal = x < 0.05 and z > 0.0
        if (eyes or mouth) and not nasal:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    K.mk(rig, bm, 'Head.helmet', 'bronze', 'Head', (0, 0, hc), angle=None)
    # obwodka otworu i brwi helmu
    bm = C.bm_box(0.86, 0.08, 0.07, 0.03)
    C.bm_map(bm, lambda co: (co.x, co.y + co.x * co.x * 0.5, co.z))
    K.mk(rig, bm, 'Head.browline', 'bronze_dark', 'Head', (0, -0.70, hc + 0.33))
    K.ring(rig, 'Head', 'Head.helmbase', 'bronze_dark', (0, 0, hc - 0.55), 0.645, 0.04, scale=(1, 1, 1))
    for sx in (-1, 1):
        pts = [(sx * 0.15, -0.69, hc + 0.43), (sx * 0.42, -0.58, hc + 0.47), (sx * 0.62, -0.25, hc + 0.42)]
        K.mk(rig, C.bm_tube(pts, 0.025, res=3), f'Head.swirl{sx}', 'gold', 'Head', (0, 0, 0))
    # grzebien na wsporniku
    K.mk(rig, C.bm_cyl(0.06, 0.24, 10), 'Head.stilt', 'bronze_dark', 'Head', (0, 0.05, hc + 0.82))
    K.mk(rig, C.bm_box(0.16, 1.3, 0.1, 0.04), 'Head.crestholder', 'bronze_dark', 'Head', (0, 0.05, hc + 0.94))
    K.crest(rig, 'Head', (0, 0.05, hc + 0.94), length=1.75, height=0.85, width=0.24, n=23,
            mats=('crest_black', 'crest_grey'), base_mat='bronze_dark', arc=176)


def build(out):
    M.LIB['crest_black'] = ((0.012, 0.011, 0.011), 0.0, 0.6, 0.35, 200, {'sheen': 0.3})
    M.LIB['crest_grey'] = ((0.05, 0.045, 0.045), 0.0, 0.62, 0.35, 200, {'sheen': 0.3})
    rig = U.body('Hoplita', out, SKIN, face_kw=dict(style='angry', mouth='teeth', scar=True),
                 mats=dict(torso='bronze'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- pancerz miesniowy
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.86, 0.16, 0.56, 0.12, 3), f'Torso.pec{sx}', 'bronze', T, (sx * 0.45, -0.5, 3.52))
        for r in range(3):
            K.mk(rig, C.bm_box(0.36, 0.1, 0.22, 0.06, 2), f'Torso.ab{sx}{r}', 'bronze', T,
                 (sx * 0.2, -0.52, 3.05 - r * 0.25))
        K.mk(rig, C.bm_sphere(0.05, 10, 6), f'Torso.nip{sx}', 'bronze_dark', T, (sx * 0.45, -0.6, 3.48))
    K.mk(rig, C.bm_torus(0.47, 0.06, 32, 8), 'Torso.collar', 'bronze_dark', T, (0, 0, 4.0), scale=(1.15, 0.95, 1))
    K.mk(rig, C.bm_box(2.12, 1.12, 0.12, 0.04), 'Torso.hemtop', 'bronze_dark', T, (0, 0, 2.22))
    K.belt(rig, 2.1, 'leather_dark', 'bronze_dark', studs=False)
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.6, 1.16, 0.14, 0.05), f'Torso.flap{sx}', 'linen', T, (sx * 0.7, 0, 4.0))
        K.mk(rig, C.bm_cyl(0.07, 0.04, 12), f'Torso.flappin{sx}', 'gold', T, (sx * 0.62, -0.6, 3.92),
             rot=(90, 0, 0))

    # plaszcz (karmazyn, bez zlotej obwodki)
    K.cape(rig, 'red_dark', 'red_cloth', length=2.7, top_w=1.9, bot_w=2.6, clasp='bronze')

    # ---- nogi
    for side in ('Right', 'Left'):
        K.leg_skirt(rig, side, 'linen', 1.55, 2.0, 0.07)
        K.pteruges(rig, side, 'linen', 'bronze_dark', length=0.62, n=3)
        K.greave(rig, side, 'bronze', 'bronze_dark', z0=0.24, z1=1.2)
        K.sandals(rig, side, 'leather', 'leather_dark', bands=(0.3,), lace=False)

    # ---- ramiona
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        K.mk(rig, C.bm_box(1.08, 1.08, 0.42, 0.05), f'{j}.bracer', 'leather_dark', j, (x, 0, 2.4))
        K.mk(rig, C.bm_box(1.1, 1.1, 0.06, 0.02), f'{j}.bracerband', 'bronze', j, (x, 0, 2.58))

    corinthian(rig, hc)

    # ---- aspis
    ax = B['ax']
    hz = B['hand_z']
    sp = Vector((ax, -0.82, hz + 0.1))
    rig.joint('Shield', 'Left Arm', tuple(sp), follow='Left Arm')
    R_ = 1.38

    def dome_z(r):
        return 0.30 * (1 - (r / R_) ** 2) + 0.06
    prof = [(0.0, 0.0), (R_, 0.0), (R_ + 0.05, 0.05)]
    for i in range(12, -1, -1):
        r = R_ * i / 12
        prof.append((r, dome_z(r)))
    bm = K.bmesh_recalc(C.bm_lathe(prof, segs=64))
    C.bm_transform(bm, rot=(90, 0, 0))
    K.mk(rig, bm, 'Shield.aspis', 'bronze', 'Shield', tuple(sp), angle=None)
    K.mk(rig, C.bm_torus(R_, 0.085, 64, 10), 'Shield.rim', 'bronze_dark', 'Shield',
         tuple(sp + Vector((0, -0.05, 0))), rot=(90, 0, 0))
    for i in range(24):
        a = 2 * math.pi * i / 24
        K.mk(rig, C.bm_sphere(0.045, 8, 6), f'Shield.rivet{i}', 'gold', 'Shield',
             tuple(sp + Vector((math.cos(a) * (R_ - 0.12), -0.13, math.sin(a) * (R_ - 0.12)))))
    lam = [(-0.68, -0.70), (-0.34, -0.70), (0.0, 0.26), (0.34, -0.70), (0.68, -0.70), (0.17, 0.74),
           (-0.17, 0.74)]
    bm = C.bm_extrude(lam, 0.06)
    C.bm_map(bm, lambda co: (co.x, co.y, dome_z(min(R_, math.hypot(co.x, co.y))) + co.z + 0.03))
    C.bm_transform(bm, rot=(90, 0, 0))
    K.mk(rig, bm, 'Shield.lambda', 'red_paint', 'Shield', tuple(sp), angle=None)
    rig.attach('ShieldFront', 'Shield', tuple(sp + Vector((0, -0.5, 0))))

    # ---- dory
    hand = rig.hand['Right Arm']
    hx, hzz = hand.x, hand.z
    rig.joint('Dory', 'Right Arm', tuple(hand), follow='Right Arm')
    U.shaft(rig, 'Dory', 'Dory.shaft', 'wood', 2.3, -3.0, 0.075, hx, hzz)
    U.shaft(rig, 'Dory', 'Dory.grip', 'leather_dark', 0.25, -0.25, 0.095, hx, hzz)
    K.mk(rig, C.bm_cyl(0.085, 0.3, 12, r2=0.06), 'Dory.socket', 'bronze', 'Dory', (hx, -3.1, hzz), rot=(90, 0, 0))
    leaf = [(0, 0), (0.17, 0.15), (0.18, 0.4), (0.0, 0.85), (-0.18, 0.4), (-0.17, 0.15)]
    bm = C.bm_extrude(leaf, 0.05, 0.02, 2)
    C.bm_map(bm, lambda co: (co.x, -co.y, co.z * (1 - abs(co.x) / 0.2 * 0.6)))
    C.bm_transform(bm, rot=(0, 90, 0))
    K.mk(rig, bm, 'Dory.head', 'steel', 'Dory', (hx, -3.22, hzz))
    K.mk(rig, C.bm_cyl(0.07, 0.5, 4, r2=0.0), 'Dory.sauroter', 'bronze', 'Dory', (hx, 2.55, hzz), rot=(-90, 0, 45))
    rig.attach('DoryTip', 'Dory', (hx, -4.05, hzz))
    rig.attach('DoryNeck', 'Dory', (hx, -3.1, hzz))
    return rig


def animate(rig):
    base = dict(T=(8, 0, -10), H=(-2, 0, 8), RA=(150, 10, 0), LA=(52, 4, 4), RL=(-14, 8, 0),
                LL=(18, -6, 6), Dory={'pitch': -8}, Shield={'pitch': 0})
    A = Animator(rig, base)
    P = A.P
    tip, neck = rig.attachments['DoryTip'][1], rig.attachments['DoryNeck'][1]

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(30, P(T=(10, 0, -9), H=(0, 0, 7), RA=(147, 10, 0), LA=(50, 4, 4), Dory={'pitch': -5}))
    A.key(60, P())

    # ---- atak 1: pchniecie dory
    A.clip('Attack1', 'Atak 1: Pchnięcie dory', 100, 32, level='poz. 0-1',
           desc='Pchnięcie znad tarczy z wykrokiem.', show=[100, 106, 110, 112, 118, 126])
    A.key(0, P())
    A.key(6, P(T=(2, 0, -26), Tp=(0, -0.15), RA=(168, 14, -4), Dory={'pitch': -4}, LA=(54, 4, 10),
               H=(-2, 0, 22)))
    A.key(10, P(T=(18, 0, 6), Tp=(0, 0.8), RA=(122, 2, 6), Dory={'pitch': -14}, LA=(46, 8, 0),
                H=(-6, 0, -4), LL=(36, -6, 4), RL=(-30, 8, 0), cape=18))
    A.key(13, P(T=(20, 0, 8), Tp=(0, 0.9), RA=(118, 2, 6), Dory={'pitch': -16}, LA=(44, 8, 0),
                H=(-6, 0, -6), LL=(38, -6, 4), RL=(-32, 8, 0), cape=16))
    A.key(22, P(T=(12, 0, -4), Tp=(0, 0.45), RA=(140, 8, 2), Dory={'pitch': -10}, LA=(50, 4, 4),
                H=(-3, 0, 4), LL=(26, -6, 6), RL=(-20, 8, 0)))
    A.key(32, P())
    A.event(10, 'Hit')
    A.event(7, 'TrailOn', a='DoryNeck', b='DoryTip')
    A.event(13, 'TrailOff')
    A.add_fx('trail', 7, 13, joint='Dory', a=neck, b=tip)
    A.add_fx('sparks', 10, 16, center='DoryTip', count=10, spread=1.0, col=(1, 0.85, 0.5))

    # ---- atak 2: odepchniecie tarcza
    A.clip('Attack2', 'Atak 2: Odepchnięcie tarczą', 200, 40, level='poz. 2-3',
           desc='Pchnięcie aspis całym ciałem – odrzuca wrogów do tyłu.', show=[200, 207, 211, 213, 220, 232])
    A.key(0, P())
    A.key(7, P(T=(22, 0, -32), Tp=(0, -0.2), LA=(38, 0, 18), RA=(158, 12, 0), Dory={'pitch': -2},
               H=(-8, 0, 26), LL=(14, -6, 8), RL=(-22, 8, 0)))
    A.key(11, P(T=(12, 0, -14), Tp=(0, 1.15), LA=(88, 0, 4), RA=(150, 16, -6), Dory={'pitch': 4},
                H=(-4, 0, 12), LL=(42, -6, 6), RL=(-40, 8, 0), cape=22))
    A.key(13, P(T=(10, 0, -10), Tp=(0, 1.3), LA=(92, 0, 2), RA=(150, 16, -6), Dory={'pitch': 4},
                H=(-4, 0, 8), LL=(44, -6, 6), RL=(-42, 8, 0), cape=20))
    A.key(22, P(T=(10, 0, -10), Tp=(0, 1.0), LA=(70, 2, 4), RA=(152, 12, -2), Dory={'pitch': -4},
                H=(-3, 0, 8), LL=(34, -6, 6), RL=(-30, 8, 0)))
    A.key(32, P(Tp=(0, 0.35)))
    A.key(40, P())
    A.event(12, 'Hit', knockback=True)
    A.add_fx('ring', 11, 22, center='ShieldFront', r0=0.6, r1=3.2, col=(1.0, 0.85, 0.55), th=0.07, flat=1.0)
    A.add_fx('puffs', 11, 26, center=(0, -1.6, 0.25), count=12, spread=2.2, rise=0.5, col=(0.75, 0.68, 0.55),
             size=0.32)

    # ---- atak 3: falanga - potrojne pchniecie
    A.clip('Attack3', 'Atak 3: Falanga – potrójne pchnięcie', 300, 56, level='poz. 4-5',
           desc='Trzy szybkie pchnięcia krok za krokiem, ostatnie z pełnym wykrokiem i tupnięciem.',
           show=[300, 310, 316, 320, 330, 344])
    A.key(0, P())
    A.key(5, P(T=(4, 0, -22), Tp=(0, -0.1), RA=(166, 12, -4), Dory={'pitch': -6}, H=(-2, 0, 18)))
    A.key(10, P(T=(16, 0, 4), Tp=(0, 0.5), RA=(124, 2, 6), Dory={'pitch': -12}, LL=(30, -6, 4),
                RL=(-24, 8, 0), H=(-5, 0, -2), cape=14))
    A.key(15, P(T=(8, 0, -18), Tp=(0, 0.55), RA=(164, 12, -4), Dory={'pitch': -6}, H=(-2, 0, 14),
                LL=(22, -6, 6), RL=(-18, 8, 0)))
    A.key(20, P(T=(18, 0, 8), Tp=(0, 1.0), RA=(120, 0, 8), Dory={'pitch': -18}, LL=(34, -6, 4),
                RL=(-28, 8, 0), H=(-6, 0, -6), cape=16))
    A.key(25, P(T=(6, 0, -26), Tp=(0, 0.95), RA=(172, 14, -6), Dory={'pitch': -2}, H=(-2, 0, 22),
                LL=(24, -6, 6), RL=(-20, 8, 0), LA=(56, 4, 8)))
    A.key(30, P(T=(26, 0, 12), Tp=(0, 1.75), RA=(112, 0, 8), Dory={'pitch': -20}, LA=(40, 10, 0),
                LL=(46, -6, 2), RL=(-40, 8, 0), H=(-8, 0, -10), cape=24))
    A.key(36, P(T=(24, 0, 10), Tp=(0, 1.7), RA=(116, 0, 8), Dory={'pitch': -18}, LA=(42, 10, 0),
                LL=(44, -6, 2), RL=(-38, 8, 0), H=(-8, 0, -8), cape=18))
    A.key(46, P(T=(10, 0, -6), Tp=(0, 0.6), RA=(144, 8, 2), Dory={'pitch': -10}, LL=(24, -6, 6),
                RL=(-18, 8, 0)))
    A.key(56, P())
    for h in (10, 20, 30):
        A.event(h, 'Hit')
        A.event(h - 3, 'TrailOn', a='DoryNeck', b='DoryTip')
        A.event(h + 3, 'TrailOff')
        A.add_fx('trail', h - 3, h + 3, joint='Dory', a=neck, b=tip, name=f'h{h}')
    A.add_fx('ring', 30, 42, center=(0, -1.9, 0.08), r0=0.5, r1=3.0, col=(1, 0.8, 0.5), th=0.06)
    A.add_fx('puffs', 30, 46, center=(0, -1.9, 0.2), count=12, spread=2.0, rise=0.6, col=(0.75, 0.68, 0.55))
    A.finish()
    return A
