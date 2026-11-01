"""Meduza: gorgona o bladozielonej skorze i zoltych wezowych oczach, wlosy z zywych wezy (3 grupy
jointow), szmaragdowa luskowa suknia, zloty diadem, zlote bransolety-weze.
Paleta: zielenie + zloto + zolty blask."""
import math
import random
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Meduza', display='Meduza',
    subtitle='Magiczna · petryfikacja (ogłuszenie) · kamienne spojrzenie, ukąszenie węży, klątwa Gorgony',
    cam=dict(target=(0.2, -0.8, 2.9), dist=15.0, dir=(0.62, -1.0, 0.4)), ped_r=2.7,
)
SKIN = (0.30, 0.46, 0.25)


def snake(rig, joint, name, pts, r=0.085, mats=('snake', 'snake_dark')):
    radii = [1.0 - 0.35 * i / (len(pts) - 1) for i in range(len(pts))]
    K.mk(rig, C.bm_tube(pts, r, radii=radii, res=5), f'{name}.body', mats[0], joint, (0, 0, 0))
    a, b = Vector(pts[-2]), Vector(pts[-1])
    d = (b - a).normalized()
    hp = b + d * 0.08
    rot = C.look_rot(d)
    K.mk(rig, C.bm_sphere(0.13, 14, 8), f'{name}.head', mats[1], joint, tuple(hp), rot=rot, scale=(0.8, 1.35, 0.6))
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    for sx in (-1, 1):
        K.mk(rig, C.bm_sphere(0.032, 8, 6), f'{name}.eye{sx}', 'glow_yellow', joint,
             tuple(hp + side * sx * 0.085 + d * 0.06 + Vector((0, 0, 0.04))))
    tip = hp + d * 0.18
    K.mk(rig, C.bm_tube([tuple(tip), tuple(tip + d * 0.14)], 0.012, smooth=False, bevel_res=1), f'{name}.tongue',
         'glow_red', joint, (0, 0, 0))


def build(out):
    rig = U.body('Meduza', out, SKIN,
                 face_kw=dict(style='snake', mouth='fangs', lashes=False, brow=(20, 50, 20)),
                 mats=dict(torso='scale_green'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- suknia z lusek, zloty kolnierz i pas-waz
    for r in range(4):
        for c in range(5):
            x = -0.8 + c * 0.4 + (0.2 if r % 2 else 0)
            if abs(x) > 0.95:
                continue
            K.mk(rig, C.bm_sphere(0.14, 10, 6), f'Torso.scale{r}{c}', 'emerald', T, (x, -0.5, 3.6 - r * 0.32),
                 scale=(1, 0.35, 0.8))
    prof = [(0.48, 0.0), (0.95, -0.05), (1.02, -0.12), (0.95, -0.16), (0.5, -0.1)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=40)), 'Torso.collar', 'gold', T, (0, 0, 4.03), scale=(1.0, 0.62, 1))
    for k in range(9):
        a = math.radians(200 + 140 * k / 8)
        K.mk(rig, C.bm_sphere(0.06, 10, 6), f'Torso.collargem{k}', 'emerald', T,
             (0.82 * math.cos(a), 0.5 * math.sin(a), 3.93))
    belt = []
    for i in range(25):
        a = 2 * math.pi * i / 24
        belt.append((1.08 * math.cos(a), 0.58 * math.sin(a), 2.15 + 0.06 * math.sin(3 * a)))
    K.mk(rig, C.bm_tube(belt, 0.07, res=3), 'Torso.snakebelt', 'gold', T, (0, 0, 0))
    K.mk(rig, C.bm_sphere(0.13, 12, 8), 'Torso.beltsnakehead', 'gold', T, (0.15, -0.66, 2.2), scale=(1.4, 0.8, 0.8))
    for sx in (-1, 1):
        K.mk(rig, C.bm_sphere(0.03, 8, 6), f'Torso.beltsnakeeye{sx}', 'glow_red', T, (0.15 + sx * 0.08, -0.74, 2.26))
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.mk(rig, C.bm_box(1.14, 1.14, 1.9, 0.06), f'{j}.gown', 'snake_dark', j, (x, 0, 1.05))
        for r in range(4):
            K.mk(rig, C.bm_box(1.16, 1.16, 0.05, 0.02), f'{j}.scaleline{r}', 'scale_green', j, (x, 0, 0.45 + r * 0.4))
        K.mk(rig, C.bm_box(1.18, 1.18, 0.1, 0.03), f'{j}.hem', 'gold', j, (x, 0, 0.12))
        # sukienka rozcieta jak luski - zakonczenie zebami
        for k in range(4):
            K.mk(rig, C.bm_cyl(0.13, 0.22, 4, r2=0.0), f'{j}.tooth{k}', 'gold', j,
                 (x - 0.38 + 0.25 * k, -0.6, 0.28), rot=(180, 0, 45))
    # bransolety-weze
    for side in ('Right', 'Left'):
        j = f'{side} Arm'
        x = K.arm_x(rig, side)
        pts = []
        for i in range(30):
            a = 2 * math.pi * i / 10
            pts.append((x + 0.58 * math.cos(a), 0.58 * math.sin(a), 2.25 + i * 0.022))
        K.mk(rig, C.bm_tube(pts, 0.05, res=2), f'{j}.coil', 'gold', j, (0, 0, 0))
        K.mk(rig, C.bm_sphere(0.09, 10, 6), f'{j}.coilhead', 'gold', j, tuple(Vector(pts[-1]) + Vector((0, -0.05, 0.05))),
             scale=(0.8, 1.3, 0.7))
        K.mk(rig, C.bm_box(1.08, 1.08, 0.7, 0.05), f'{j}.sleeve', 'scale_green', j, (x, 0, 3.68))

    # ---- diadem
    K.mk(rig, C.bm_torus(0.64, 0.045, 40, 8), 'Head.diadem', 'gold', 'Head', (0, 0, hc + 0.36))
    tri = C.bm_extrude([(-0.16, 0), (0.16, 0), (0, 0.3)], 0.05, 0.01, 1)
    C.bm_transform(tri, rot=(90, 0, 0))
    K.mk(rig, tri, 'Head.diademtip', 'gold', 'Head', (0, -0.67, hc + 0.36))
    K.mk(rig, C.bm_sphere(0.07, 12, 8), 'Head.diademgem', 'emerald', 'Head', (0, -0.72, hc + 0.44))
    K.mk(rig, C.bm_box(1.26, 1.2, 0.3, 0.12), 'Head.scalp', 'snake_dark', 'Head', (0, 0.04, hc + 0.5))

    # ---- wlosy-weze: 3 grupy jointow (lewe, prawe, tyl) do animacji
    piv = (0, 0.05, hc + 0.35)
    for g in ('SnakesR', 'SnakesL', 'SnakesB'):
        rig.joint(g, 'Head', piv)
    rnd = random.Random(11)
    angs = [0, 25, 50, 75, 100, 125, 150, 175, 200, 215, -20, -38, 90, 60, 120]
    for i, deg in enumerate(angs):
        th = math.radians(deg)
        top = i >= 12
        zb = hc + (0.6 if top else rnd.uniform(0.3, 0.52))
        rb = 0.35 if top else 0.6
        d = Vector((math.cos(th), math.sin(th), 0))
        base = Vector((0, 0.05, zb)) + d * rb
        L = rnd.uniform(0.8, 1.15)
        fwd = Vector((0, -1, 0))
        up = Vector((0, 0, 1))
        if top:
            pts = [base, base + up * 0.35 + d * 0.1, base + up * 0.6 + d * 0.3 + fwd * 0.1,
                   base + up * 0.75 + d * 0.35 + fwd * 0.35]
        else:
            pts = [base, base + d * 0.3 * L + up * 0.18, base + d * 0.55 * L - up * 0.05 + fwd * 0.05,
                   base + d * 0.75 * L + up * 0.25 + fwd * 0.12, base + d * 0.8 * L + up * 0.5 + fwd * 0.32]
        x = pts[-1].x
        g = 'SnakesB' if (top or 60 < deg < 125) else ('SnakesL' if x > 0 else 'SnakesR')
        snake(rig, g, f'{g}.s{i}', [tuple(p) for p in pts], mats=('snake', 'snake_dark') if i % 2 else ('snake_dark', 'snake'))
    rig.attach('Eyes', 'Head', (0, -0.75, hc + 0.0))
    rig.attach('SnakeL', 'SnakesL', (0.9, -0.3, hc + 0.8))
    rig.attach('SnakeR', 'SnakesR', (-0.9, -0.3, hc + 0.8))
    return rig


def animate(rig):
    base = dict(T=(4, 0, -6), H=(4, 0, 6), RA=(30, 28, 10), LA=(30, 28, 10), RL=(-8, 5, 0), LL=(8, -3, 5),
                SnakesL=(0, 0, 0), SnakesR=(0, 0, 0), SnakesB=(0, 0, 0))
    A = Animator(rig, base)
    P = A.P

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(15, P(SnakesL=(6, -8, 8), SnakesR=(-4, 6, -6), SnakesB=(-6, 4, 0), H=(4, 2, 4)))
    A.key(30, P(T=(5, 1, -4), RA=(34, 30, 12), LA=(26, 26, 8), SnakesL=(-4, 6, -6), SnakesR=(6, -8, 8),
                SnakesB=(6, -4, 4), H=(2, -2, 8)))
    A.key(45, P(SnakesL=(4, -4, 6), SnakesR=(-6, 4, -4), SnakesB=(-4, 6, -4)))
    A.key(60, P())

    # ---- atak 1: kamienne spojrzenie
    A.clip('Attack1', 'Atak 1: Kamienne spojrzenie', 100, 44, level='poz. 0-1',
           desc='Pochyla się, dłonie przy twarzy, z oczu bije żółty promień – cel kamienieje (ogłuszenie).',
           show=[100, 108, 114, 118, 126, 136])
    A.key(0, P())
    A.key(8, P(T=(-6, 0, -4), RA=(120, 20, 50), LA=(120, 20, 50), H=(-10, 0, 4), SnakesL=(-10, -14, 0),
               SnakesR=(-10, 14, 0), SnakesB=(-12, 0, 0), Tp=(0, -0.1)))
    A.key(14, P(T=(18, 0, 0), RA=(100, 30, 30), LA=(100, 30, 30), H=(-4, 0, 0), SnakesL=(18, -20, 0),
                SnakesR=(18, 20, 0), SnakesB=(10, 0, 0), Tp=(0, 0.4), LL=(22, -3, 4), RL=(-16, 5, 0)))
    A.key(26, P(T=(20, 0, 0), RA=(98, 34, 28), LA=(98, 34, 28), H=(-4, 0, 0), SnakesL=(22, -24, 4),
                SnakesR=(22, 24, -4), SnakesB=(12, 0, 0), Tp=(0, 0.45), LL=(22, -3, 4), RL=(-16, 5, 0)))
    A.key(34, P(T=(8, 0, -4), RA=(50, 28, 12), LA=(50, 28, 12), Tp=(0, 0.2)))
    A.key(44, P())
    A.event(16, 'Hit', stun=1.5, petrify=True)
    A.add_fx('beam', 14, 28, **{'from': 'Eyes'}, dir=(0, -1, -0.25), length=6.0, r0=0.1, r1=0.7,
             col=(0.95, 0.8, 0.1), name='gaze')
    A.add_fx('glowpoint', 12, 28, at='Eyes', col=(1, 0.85, 0.2), energy=120)
    A.add_fx('puffs', 18, 36, center=(0, -5.0, 0.4), count=10, spread=1.4, rise=0.8, col=(0.6, 0.6, 0.58),
             size=0.38, name='stone')

    # ---- atak 2: ukaszenie wezy
    A.clip('Attack2', 'Atak 2: Ukąszenie węży', 200, 36, level='poz. 2-3',
           desc='Wypad do przodu, węże z włosów kąsają (trucizna).', show=[200, 206, 210, 212, 218, 228])
    A.key(0, P())
    A.key(6, P(T=(-8, 0, 0), H=(-14, 0, 0), RA=(20, 50, 0), LA=(20, 50, 0), SnakesL=(-30, -10, 0),
               SnakesR=(-30, 10, 0), SnakesB=(-25, 0, 0), Tp=(0, -0.2)))
    A.key(10, P(T=(26, 0, 0), H=(18, 0, 0), RA=(60, 40, 20), LA=(60, 40, 20), SnakesL=(50, 12, 10),
                SnakesR=(50, -12, -10), SnakesB=(45, 0, 0), Tp=(0, 0.9), LL=(36, -3, 4), RL=(-30, 5, 0)))
    A.key(13, P(T=(28, 0, 0), H=(20, 0, 0), RA=(62, 40, 20), LA=(62, 40, 20), SnakesL=(55, 14, 12),
                SnakesR=(55, -14, -12), SnakesB=(50, 0, 0), Tp=(0, 1.0), LL=(38, -3, 4), RL=(-32, 5, 0)))
    A.key(20, P(T=(14, 0, 0), H=(6, 0, 0), SnakesL=(10, 0, 0), SnakesR=(10, 0, 0), SnakesB=(6, 0, 0),
                Tp=(0, 0.6), LL=(24, -3, 4), RL=(-18, 5, 0)))
    A.key(28, P(Tp=(0, 0.2)))
    A.key(36, P())
    A.event(11, 'Hit', poison=True)
    for nm, att in (('l', 'SnakeL'), ('r', 'SnakeR')):
        A.add_fx('sparks', 11, 18, center=att, count=10, spread=1.0, col=(0.3, 1.0, 0.3), fixed=True, name=nm)
    A.add_fx('trail', 7, 13, joint='SnakesL', a=rig.attachments['SnakeL'][1] + Vector((0, 0.3, -0.2)),
             b=rig.attachments['SnakeL'][1], col=(0.5, 1.0, 0.5), name='sl')
    A.add_fx('trail', 7, 13, joint='SnakesR', a=rig.attachments['SnakeR'][1] + Vector((0, 0.3, -0.2)),
             b=rig.attachments['SnakeR'][1], col=(0.5, 1.0, 0.5), name='sr')

    # ---- atak 3: klatwa Gorgony
    A.clip('Attack3', 'Atak 3: Klątwa Gorgony', 300, 64, level='poz. 4-5',
           desc='Unosi się, rozkłada ręce, węże nastroszone – fala zielonej klątwy kamienieje wszystkich w zasięgu.',
           show=[300, 310, 322, 328, 338, 352])
    A.key(0, P())
    A.key(10, P(T=(16, 0, 0), H=(12, 0, 0), RA=(20, 10, 30), LA=(20, 10, 30), SnakesL=(30, 20, 0),
                SnakesR=(30, -20, 0), SnakesB=(30, 0, 0), RL=(-14, 5, 0), LL=(14, -3, 0)))
    A.key(22, P(T=(-14, 0, 0), H=(-20, 0, 0), RA=(150, 70, 0), LA=(150, 70, 0), SnakesL=(-20, -40, 0),
                SnakesR=(-20, 40, 0), SnakesB=(-35, 0, 0), air=0.8, RL=(-20, 6, 0), LL=(-5, -4, 0)))
    A.key(28, P(T=(-16, 0, 0), H=(-22, 0, 0), RA=(160, 80, 0), LA=(160, 80, 0), SnakesL=(-25, -48, 0),
                SnakesR=(-25, 48, 0), SnakesB=(-40, 0, 0), air=0.95, RL=(-22, 6, 0), LL=(-6, -4, 0)))
    A.key(40, P(T=(-8, 0, 0), H=(-10, 0, 0), RA=(120, 60, 0), LA=(120, 60, 0), SnakesL=(-10, -30, 0),
                SnakesR=(-10, 30, 0), SnakesB=(-20, 0, 0), air=0.6))
    A.key(52, P(air=0.1, RA=(40, 30, 10), LA=(40, 30, 10)))
    A.key(64, P())
    A.event(28, 'Hit', area=True, stun=2.0, petrify=True)
    A.add_fx('orb', 18, 30, at='Eyes', r=0.5, col=(0.3, 1.0, 0.3), energy=200, name='g')
    A.add_fx('ring', 28, 46, center=(0, 0, 0.12), r0=0.8, r1=6.5, col=(0.3, 1.0, 0.25), th=0.1, disc=True, name='g')
    A.add_fx('ring', 31, 48, center=(0, 0, 0.12), r0=0.5, r1=4.5, col=(0.8, 1.0, 0.5), th=0.05, name='g2')
    A.add_fx('puffs', 28, 54, center=(0, 0, 0.3), count=16, spread=4.0, rise=0.6, col=(0.55, 0.58, 0.52),
             size=0.42, name='stone3', seed=12)
    A.finish()
    return A
