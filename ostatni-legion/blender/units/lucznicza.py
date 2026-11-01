"""Luczniczka Kretenska: minojska luczniczka - lniany chiton z turkusowym szlakiem, zlota opaska,
dlugi czarny warkocz, kolczan na plecach, krotki refleksyjny luk z rogiem.
Paleta: len + turkus + zloto + czern wlosow."""
import math
import bpy
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Luczniczka', display='Łuczniczka Kreteńska',
    subtitle='Militarna · zasięg, ukryci od poz. 3 · łuk: strzał, potrójna salwa, deszcz strzał',
    cam=dict(target=(0.0, -0.9, 2.7), dist=14.5, dir=(1.0, -0.62, 0.36)), ped_r=2.6,
)
SKIN = (0.74, 0.43, 0.27)
BOW_L = 1.6


def arrow_parts(L=2.1, r=0.035, fletch='red_cloth'):
    """Strzala wzdluz -Y: nasadka w y=0, grot w y=-L."""
    parts = []
    b = C.bm_cyl(r, L - 0.2, 8)
    C.bm_transform(b, loc=(0, -(L - 0.2) / 2, 0), rot=(90, 0, 0))
    parts.append((b, 'wood_light'))
    b = C.bm_cyl(0.08, 0.26, 4, r2=0.0)
    C.bm_transform(b, loc=(0, -(L - 0.08), 0), rot=(90, 0, 45))
    parts.append((b, 'steel'))
    for k in range(3):
        b = C.bm_extrude([(0, 0), (0.1, 0.06), (0.1, 0.36), (0, 0.42)], 0.012)
        C.bm_transform(b, rot=(0, 90, 0))
        C.bm_transform(b, loc=(0, -0.48, 0), rot=(0, 0, 0))
        C.bm_transform(b, rot=(0, 120 * k, 0))
        parts.append((b, fletch))
    b = C.bm_sphere(0.05, 8, 6)
    parts.append((b, 'gold'))
    return parts


def place_parts(rig, joint, prefix, parts, loc, rot):
    for i, (bm, mat) in enumerate(parts):
        C.bm_transform(bm, rot=rot)
        K.mk(rig, bm, f'{prefix}{i}', mat, joint, loc)


def build(out):
    rig = U.body('Luczniczka', out, SKIN,
                 face_kw=dict(style='fem', mouth='frown', lashes=True, lips=(150, 45, 50), brow_w=0.8),
                 mats=dict(torso='teal_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- chiton: turkusowe szlaki, pas, szarfa przez piers
    K.mk(rig, C.bm_box(2.08, 1.08, 0.14, 0.04), 'Torso.neckband', 'linen', T, (0, 0, 3.95))
    K.belt(rig, 2.2, 'leather_light', 'gold', h=0.2)
    K.chest_strap(rig, 'leather', 'gold', from_right=False, w=0.2)
    for i, x in enumerate((-0.6, -0.3, 0.0, 0.3, 0.6)):
        K.mk(rig, C.bm_box(0.12, 0.05, 0.12, 0.02), f'Torso.meander{i}', 'gold', T, (x, -0.55, 3.95), rot=(0, 45, 0))
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.leg_skirt(rig, side, 'teal_cloth', 1.25, 2.0, 0.1)
        K.mk(rig, C.bm_box(1.12, 1.12, 0.12, 0.03), f'{j}.hem', 'linen', j, (x, 0, 1.3))
        K.mk(rig, C.bm_box(1.13, 1.13, 0.04, 0.01), f'{j}.hemgold', 'gold', j, (x, 0, 1.38))
        K.sandals(rig, side, 'leather_light', 'leather', bands=(0.3, 0.55, 0.8, 1.05))
    # ramiona: karwasz na lewej, zlota bransoleta na prawej
    K.mk(rig, C.bm_box(1.08, 1.08, 0.5, 0.06), 'Left Arm.bracer', 'leather', 'Left Arm', (B['ax'], 0, 2.4))
    for z in (2.2, 2.6):
        K.mk(rig, C.bm_box(1.1, 1.1, 0.05, 0.02), f'Left Arm.lace{z}', 'gold', 'Left Arm', (B['ax'], 0, z))
    K.mk(rig, C.bm_box(1.08, 1.08, 0.12, 0.03), 'Right Arm.armlet', 'gold', 'Right Arm', (-B['ax'], 0, 3.45))
    K.mk(rig, C.bm_box(1.08, 1.08, 0.12, 0.03), 'Right Arm.wrist', 'gold', 'Right Arm', (-B['ax'], 0, 2.3))

    # ---- wlosy: czapa, tyl, warkocz, loki, zlota opaska z turkusem
    K.hair_cap(rig, 'hair_dark', hc, length=1.0)
    braid = [(0, 0.66, hc + 0.1), (0, 0.78, hc - 0.4), (0.05, 0.85, hc - 0.9), (0.0, 0.92, hc - 1.4),
             (-0.05, 0.98, hc - 1.8)]
    K.mk(rig, C.bm_tube(braid, 0.13, radii=[1, 1, 0.9, 0.8, 0.6], res=6), 'Head.braid', 'hair_dark', 'Head', (0, 0, 0))
    for k in range(5):
        p = braid[1][2] - k * 0.32
        K.mk(rig, C.bm_torus(0.12, 0.03, 16, 6), f'Head.braidring{k}', 'gold', 'Head',
             (0.02 * (k % 2), 0.82 + k * 0.035, p))
    for sx in (-1, 1):
        lock = [(sx * 0.62, -0.25, hc + 0.3), (sx * 0.68, -0.32, hc + 0.0), (sx * 0.64, -0.2, hc - 0.3),
                (sx * 0.70, -0.28, hc - 0.6)]
        K.mk(rig, C.bm_tube(lock, 0.07, radii=[1, 0.9, 0.8, 0.5], res=5), f'Head.lock{sx}', 'hair_dark', 'Head', (0, 0, 0))
    K.mk(rig, C.bm_torus(0.715, 0.045, 40, 8), 'Head.headband', 'gold', 'Head', (0, 0, hc + 0.31))
    K.mk(rig, C.bm_sphere(0.08, 12, 8), 'Head.gem', 'emerald', 'Head', (0, -0.76, hc + 0.33), scale=(1, 0.6, 1.2))
    for sx in (-1, 1):
        K.mk(rig, C.bm_sphere(0.06, 10, 6), f'Head.earring{sx}', 'gold', 'Head', (sx * 0.62, -0.05, hc - 0.2))

    # ---- kolczan na plecach (strzaly przy prawym barku)
    qc = Vector((-0.15, 0.78, 3.15))
    K.mk(rig, C.bm_cyl(0.24, 1.7, 16, bevel=0.03), 'Torso.quiver', 'leather', T, tuple(qc), rot=(-8, -25, 0))
    for k, dz in enumerate((-0.6, 0.0, 0.6)):
        d = Vector((math.sin(math.radians(-25)) * dz, 0, math.cos(math.radians(-25)) * dz))
        K.mk(rig, C.bm_torus(0.25, 0.035, 20, 6), f'Torso.quiverband{k}', 'gold', T, tuple(qc + d), rot=(-8, -25, 0))
    top = qc + Vector((math.sin(math.radians(-25)) * 0.85, 0.1, math.cos(math.radians(-25)) * 0.85))
    for k in range(5):
        off = Vector(((k - 2) * 0.07, (k % 2) * 0.06, 0))
        p0 = top + off
        p1 = p0 + Vector((-0.17, 0.05, 0.5 + 0.05 * (k % 3)))
        K.mk(rig, C.bm_tube([tuple(p0), tuple(p1)], 0.03, smooth=False, bevel_res=1), f'Torso.qarrow{k}', 'wood_light', T, (0, 0, 0))
        fl = C.bm_extrude([(0, 0), (0.09, 0.05), (0.09, 0.3), (0, 0.34)], 0.015)
        C.bm_transform(fl, rot=(90, 0, 70 * k))
        K.mk(rig, fl, f'Torso.qfletch{k}', 'red_cloth', T, tuple(p1 - Vector((0, 0, 0.32))), rot=(0, -18, 0))

    # ---- luk (refleksyjny, drewno + rog), w lewej dloni
    hand = rig.hand['Left Arm']
    rig.joint('Bow', 'Left Arm', tuple(hand))
    hx, hz = hand.x, hand.z

    def bow_z(t):
        return 0.36 * t * t - 2.6 * max(0.0, abs(t) - 0.82) ** 2
    pts, radii = [], []
    for i in range(21):
        t = -1 + 2 * i / 20
        pts.append((hx, BOW_L * t, hz + bow_z(t)))
        radii.append(1.0 - 0.5 * abs(t))
    K.mk(rig, C.bm_tube(pts, 0.12, radii=radii, res=3), 'Bow.limbs', 'wood_light', 'Bow', (0, 0, 0))
    for sgn in (-1, 1):
        tip = (hx, sgn * BOW_L, hz + bow_z(1))
        K.mk(rig, C.bm_sphere(0.09, 10, 6), f'Bow.horn{sgn}', 'gold', 'Bow', tip)
        seg = [(hx, sgn * BOW_L * t, hz + bow_z(t) - 0.0) for t in (0.45, 0.6, 0.75)]
        K.mk(rig, C.bm_tube(seg, 0.115, res=3), f'Bow.hornplate{sgn}', 'horn', 'Bow', (0, 0, 0))
        K.mk(rig, C.bm_torus(0.12, 0.03, 16, 6), f'Bow.band{sgn}', 'gold', 'Bow', (hx, sgn * 0.32, hz + bow_z(0.23)),
             rot=(90, 0, 0))
    K.mk(rig, C.bm_cyl(0.14, 0.45, 12), 'Bow.grip', 'leather_dark', 'Bow', (hx, 0, hz), rot=(90, 0, 0))
    ztip = hz + bow_z(1)
    string = K.mk(rig, C.bm_tube([(hx, -BOW_L, ztip), (hx, BOW_L, ztip)], 0.016, smooth=False, bevel_res=1),
                  'Bow.string', 'linen', 'Bow', (0, 0, 0))
    string['static_string'] = 1
    rig.attach('BowTipA', 'Bow', (hx, -BOW_L, ztip))
    rig.attach('BowTipB', 'Bow', (hx, BOW_L, ztip))
    rig.attach('BowGrip', 'Bow', (hx, 0, hz))

    # cieciwa: joint 'Nock' (srodek cieciwy), ciagniety do prawej dloni ograniczeniem
    rig.joint('Nock', 'Bow', (hx, 0, ztip))
    rh = rig.hand['Right Arm']
    rig.attach('RHand', 'Right Arm', tuple(rh))
    nock = rig.joints['Nock']
    con = nock.constraints.new('COPY_LOCATION')
    con.name = 'Draw'
    con.target = rig.att_obj('RHand')
    con.influence = 0.0

    # strzala na cieciwie (wzdluz -Z w ukladzie luku = do przodu po uniesieniu reki)
    rig.joint('Arrow', 'Nock', (hx, 0, ztip))
    place_parts(rig, 'Arrow', 'Arrow.p', arrow_parts(), (hx, 0, ztip), (90, 0, 0))
    rig.joint('Arrows3', 'Nock', (hx, 0, ztip))
    for k, yaw in enumerate((-13, 0, 13)):
        parts = arrow_parts()
        for bm, _ in parts:
            C.bm_transform(bm, rot=(0, 0, yaw))
        place_parts(rig, 'Arrows3', f'Arrows3.a{k}p', parts, (hx, 0, ztip), (90, 0, 0))
    # strzala w prawej dloni (siegniecie do kolczanu)
    rig.joint('ArrowHand', 'Right Arm', tuple(rh))
    place_parts(rig, 'ArrowHand', 'ArrowHand.p', arrow_parts(), (rh.x, 0.9, rh.z), (0, 0, 0))

    U.fx_template(arrow_parts(), 'arrow')
    return rig


def hooks(rig):
    """Render: dynamiczna cieciwa (koniec A - nock - koniec B)."""
    static = [o for o in bpy.data.objects if o.get('static_string')]
    mat = M.get('linen')
    state = {'ob': None}

    def upd(f):
        for o in static:
            o.hide_render = True
        if state['ob'] is not None:
            me = state['ob'].data
            bpy.data.objects.remove(state['ob'])
            bpy.data.meshes.remove(me)
        a = rig.att_obj('BowTipA').matrix_world.translation
        b = rig.att_obj('BowTipB').matrix_world.translation
        n = rig.joints['Nock'].matrix_world.translation
        bm = C.bm_merge(C.bm_tube([tuple(a), tuple(n)], 0.016, smooth=False, bevel_res=1),
                        C.bm_tube([tuple(n), tuple(b)], 0.016, smooth=False, bevel_res=1))
        ob = C.make(bm, 'DYN_string', mat)
        ob['noexport'] = 1
        state['ob'] = ob
    return [upd]


def animate(rig):
    nock = rig.joints['Nock']

    def draw(A, rel, v):
        nock.constraints['Draw'].influence = v
        nock.keyframe_insert('constraints["Draw"].influence', frame=A.clips[A.cur]['start'] + rel)

    base = dict(T=(4, 0, -8), H=(0, 0, 6), RA=(12, 8, 0), LA=(35, 6, 0), RL=(-10, 6, 0), LL=(12, -4, 6),
                Nock=(0, 0, 0))
    A = Animator(rig, base)
    P = A.P
    aim = dict(T=(2, 0, -55), H=(0, 0, 50), LA=(90, 0, -55), RL=(-6, 12, 0), LL=(10, -10, 0))

    def AP(**kw):
        d = dict(aim)
        d.update(kw)
        return P(**d)

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    draw(A, 0, 0.0)
    A.key(0, P())
    A.key(30, P(T=(6, 0, -6), H=(2, 2, 4), RA=(14, 9, 0), LA=(33, 6, 0)))
    A.key(60, P())
    A.hide('Arrow', 0, 61)
    A.hide('Arrows3', 0, 61)
    A.hide('ArrowHand', 0, 61)

    # ---- atak 1: strzal
    A.clip('Attack1', 'Atak 1: Strzał', 100, 40, level='poz. 0-1',
           desc='Sięgnięcie do kołczanu, naciągnięcie, strzał.', show=[100, 105, 110, 116, 121, 128])
    draw(A, 0, 0.0)
    A.key(0, P())
    A.key(5, P(T=(2, 0, -14), RA=(185, 22, 12), H=(-4, 0, 8), LA=(50, 6, -10)))
    draw(A, 10, 0.0)
    A.key(10, AP(RA=(96, 0, 28), T=(2, 0, -45), H=(0, 0, 40), LA=(88, 0, -45)))
    draw(A, 13, 1.0)
    A.key(16, AP(RA=(92, 0, 62)))
    draw(A, 20, 1.0)
    A.key(20, AP(RA=(92, 0, 64), T=(1, 0, -56)))
    draw(A, 21, 0.0)
    A.key(22, AP(RA=(80, 42, 70), T=(-2, 0, -50), Tp=(0, -0.15)))
    A.key(30, P(T=(4, 0, -20), RA=(30, 20, 20), LA=(60, 6, -20), H=(0, 0, 18), Tp=(0, -0.1)))
    A.key(40, P())
    A.hide('Arrows3', 0, 41)
    A.hide('ArrowHand', 0, 5)
    A.hide('ArrowHand', 11, 41)
    A.hide('Arrow', 0, 11)
    A.hide('Arrow', 21, 41)
    A.event(21, 'Hit', projectile='arrow', speed=60, attachment='BowGrip')
    A.add_fx('projectile', 21, 30, model='arrow', **{'from': 'BowGrip'}, dir=(0, -1, 0.04), speed=1.6)

    # ---- atak 2: potrojna salwa
    A.clip('Attack2', 'Atak 2: Potrójna salwa', 200, 46, level='poz. 2-3',
           desc='Trzy strzały naraz w wachlarz, łuk przechylony.', show=[200, 206, 212, 219, 224, 232])
    draw(A, 0, 0.0)
    A.key(0, P())
    A.key(6, P(T=(2, 0, -16), RA=(188, 24, 14), H=(-4, 0, 10), LA=(50, 6, -10)))
    draw(A, 12, 0.0)
    A.key(12, AP(RA=(96, 0, 28), LA=(88, 40, -45), T=(2, 0, -45), H=(0, 0, 40)))
    draw(A, 15, 1.0)
    A.key(19, AP(RA=(92, 0, 62), LA=(90, 45, -55)))
    draw(A, 23, 1.0)
    A.key(23, AP(RA=(92, 0, 64), LA=(90, 45, -56), T=(1, 0, -57)))
    draw(A, 24, 0.0)
    A.key(26, AP(RA=(80, 42, 70), LA=(88, 40, -50), T=(-4, 0, -48), Tp=(0, -0.35)))
    A.key(34, P(T=(4, 0, -20), RA=(30, 20, 20), LA=(60, 6, -20), H=(0, 0, 18), Tp=(0, -0.25)))
    A.key(46, P())
    A.hide('Arrow', 0, 47)
    A.hide('ArrowHand', 0, 6)
    A.hide('ArrowHand', 13, 47)
    A.hide('Arrows3', 0, 13)
    A.hide('Arrows3', 24, 47)
    A.event(24, 'Hit', projectile='arrow', count=3, spread=13, speed=60, attachment='BowGrip')
    for k, yaw in enumerate((-13, 0, 13)):
        d = (math.sin(math.radians(yaw)) * 0.9, -math.cos(math.radians(yaw)), 0.04)
        A.add_fx('projectile', 24, 32, model='arrow', **{'from': 'BowGrip'}, dir=d, speed=1.5, name=f'a{k}')

    # ---- atak 3: deszcz strzal
    A.clip('Attack3', 'Atak 3: Deszcz strzał', 300, 66, level='poz. 4-5',
           desc='Przyklęk, strzał w niebo – po chwili na cel spada grad strzał (obszar).',
           show=[300, 308, 318, 323, 346, 352])
    draw(A, 0, 0.0)
    kneel = dict(RL=(-78, 10, 0), LL=(38, -8, 0))
    A.key(0, P())
    A.key(6, P(T=(2, 0, -16), RA=(188, 24, 14), H=(-4, 0, 10), LA=(60, 6, -10), **kneel))
    draw(A, 12, 0.0)
    A.key(12, AP(RA=(150, 0, 30), LA=(140, 0, -55), T=(-14, 0, -48), H=(-10, 0, 42), **kneel))
    draw(A, 15, 1.0)
    A.key(18, AP(RA=(140, 0, 62), LA=(142, 0, -56), T=(-16, 0, -55), H=(-12, 0, 48), **kneel))
    draw(A, 22, 1.0)
    A.key(22, AP(RA=(141, 0, 64), LA=(143, 0, -56), T=(-17, 0, -56), H=(-12, 0, 48), **kneel))
    draw(A, 23, 0.0)
    A.key(25, AP(RA=(130, 40, 70), LA=(140, 0, -52), T=(-18, 0, -52), H=(-12, 0, 46), **kneel))
    A.key(40, P(T=(6, 0, -14), RA=(20, 14, 10), LA=(45, 6, -10), H=(-6, 0, 8), **kneel))
    A.key(54, P(T=(6, 0, -12), RA=(20, 14, 10), LA=(40, 6, -6), H=(-6, 0, 8), RL=(-30, 8, 0), LL=(24, -6, 4)))
    A.key(66, P())
    A.hide('Arrows3', 0, 67)
    A.hide('ArrowHand', 0, 6)
    A.hide('ArrowHand', 13, 67)
    A.hide('Arrow', 0, 13)
    A.hide('Arrow', 23, 67)
    A.event(23, 'Shoot', projectile='arrow', attachment='BowGrip', direction='up')
    A.event(48, 'Hit', area=4)
    A.add_fx('projectile', 23, 34, model='arrow', **{'from': 'BowGrip'}, dir=(0, -0.55, 1.0), speed=1.4)
    tgt = Vector((0, -5.5, 0))
    for k in range(7):
        sx = (k - 3) * 0.55
        sy = ((k * 37) % 5 - 2) * 0.4
        st = tgt + Vector((sx + 1.2, sy + 1.6, 9.0))
        A.add_fx('projectile', 40 + (k % 3), 49 + (k % 3), model='arrow', **{'from': tuple(st)},
                 dir=(-0.13, -0.18, -1.0), speed=1.0, name=f'r{k}')
    A.add_fx('ring', 48, 60, center=tuple(tgt + Vector((0, 0, 0.1))), r0=0.5, r1=3.0, col=(1, 0.85, 0.6), th=0.06)
    A.add_fx('puffs', 48, 62, center=tuple(tgt + Vector((0, 0, 0.2))), count=12, spread=2.4, rise=0.6,
             col=(0.75, 0.68, 0.55))
    A.finish()
    return A
