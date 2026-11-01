"""Balista Skorpion: rzymski scorpio na trojnogu (sprezyny skretne z liny, ramiona z brazem,
przednia tarcza z zlotym skorpionem, korba) + obslugujacy inzynier (brazowy helm Montefortino,
oliwkowa tunika, skorzany fartuch z narzedziami).
Paleta: drewno + braz + lina + ochra."""
import math
import bpy
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

INFO = dict(
    name='Balista', display='Balista Skorpion',
    subtitle='Militarna · snajper, przebija pancerz · strzał, bełt przebijający, salwa',
    cam=dict(target=(0.0, -2.3, 2.4), dist=19.5, dir=(1.0, -0.42, 0.5)), ped_r=4.6, ped_c=(0, -2.0, 0),
)
SKIN = (0.62, 0.32, 0.18)
SC = 1.45                        # skala machiny wzgledem inzyniera
P0 = Vector((0, -3.3, 2.25))     # os obrotu machiny (przed skalowaniem)
Y_FIRED = P0.y - 0.55            # pazur w pozycji po strzale
Y_COCK = 1.45 * SC               # ile do tylu po naciagnieciu


def bolt_parts(L=2.0, glow=False):
    parts = []
    b = C.bm_cyl(0.055, L - 0.25, 8)
    C.bm_transform(b, loc=(0, -(L - 0.25) / 2, 0), rot=(90, 0, 0))
    parts.append((b, 'wood_light'))
    b = C.bm_cyl(0.1, 0.36, 4, r2=0.0)
    C.bm_transform(b, loc=(0, -(L - 0.12), 0), rot=(90, 0, 45))
    parts.append((b, 'glow_violet' if glow else 'iron'))
    for k in range(3):
        b = C.bm_extrude([(0, 0), (0.12, 0.08), (0.12, 0.4), (0, 0.46)], 0.016)
        C.bm_transform(b, rot=(0, 90, 0))
        C.bm_transform(b, loc=(0, -0.5, 0))
        C.bm_transform(b, rot=(0, 120 * k, 0))
        parts.append((b, 'leather_light'))
    return parts


def scorpion_emblem(rig, joint, c, s=0.32):
    """Zloty skorpion na przedniej tarczy (patrzy w -Y)."""
    def flat(poly, name, at, rot=0.0, depth=0.04):
        bm = C.bm_extrude([(x * s, y * s) for x, y in poly], depth, 0.006, 1)
        C.bm_transform(bm, rot=(0, 0, rot))
        C.bm_transform(bm, rot=(90, 0, 0))
        K.mk(rig, bm, name, 'gold', joint, tuple(Vector(c) + Vector(at)))
    ell = [(0.28 * math.cos(a), 0.42 * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]]
    flat(ell, f'{joint}.sc_body', (0, -0.02, -0.05 * s))
    tail = []
    for i in range(9):
        a = math.radians(-90 + 200 * i / 8)
        tail.append((0.38 * s * math.cos(a) * 1.0, 0, 0.42 * s + 0.38 * s * (1 + math.sin(a)) * 0.9))
    tail = [(x + 0.0, -0.03, z) for x, _, z in tail]
    K.mk(rig, C.bm_tube([tuple(Vector(c) + Vector(p)) for p in tail], 0.045 * s * 2, radii=[1, 1, .9, .9, .8, .8, .7, .6, .5]),
         f'{joint}.sc_tail', 'gold', joint, (0, 0, 0))
    K.mk(rig, C.bm_cyl(0.07, 0.18, 8, r2=0.0), f'{joint}.sc_sting', 'gold', joint,
         tuple(Vector(c) + Vector(tail[-1]) + Vector((-0.05, 0, -0.06))), rot=(0, -120, 0))
    for sx in (-1, 1):
        claw = [(sx * 0.2 * s, -0.03, -0.35 * s), (sx * 0.55 * s, -0.03, -0.55 * s), (sx * 0.5 * s, -0.03, -0.95 * s),
                (sx * 0.28 * s, -0.03, -1.05 * s)]
        K.mk(rig, C.bm_tube([tuple(Vector(c) + Vector(p)) for p in claw], 0.05 * s * 2), f'{joint}.sc_claw{sx}',
             'gold', joint, (0, 0, 0))
        for k in range(3):
            z = (-0.1 + 0.2 * k) * s
            leg = [(sx * 0.25 * s, -0.03, z), (sx * 0.62 * s, -0.03, z + 0.08 * s), (sx * 0.75 * s, -0.03, z - 0.12 * s)]
            K.mk(rig, C.bm_tube([tuple(Vector(c) + Vector(p)) for p in leg], 0.025 * s * 2, smooth=False, bevel_res=1),
                 f'{joint}.sc_leg{sx}{k}', 'gold', joint, (0, 0, 0))


def build(out):
    M.LIB['ochre_cloth'] = ((0.06, 0.13, 0.05), 0.0, 0.82, 0.12, 90, {'sheen': 0.5})
    rig = U.body('Balista', out, SKIN, face_kw=dict(style='angry', mouth='teeth'),
                 mats=dict(torso='ochre_cloth'))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'

    # ---- inzynier: fartuch, pas z narzedziami, helm Montefortino
    K.belt(rig, 2.15, 'leather_dark', 'bronze')
    K.mk(rig, C.bm_box(1.5, 0.08, 1.7, 0.04), 'Torso.apron', 'leather', T, (0, -0.56, 2.65))
    K.mk(rig, C.bm_box(0.08, 0.06, 1.5, 0.02), 'Torso.apronstrap', 'leather_dark', T, (0.0, -0.6, 3.3), rot=(0, 30, 0))
    K.mk(rig, C.bm_box(0.42, 0.1, 0.32, 0.03), 'Torso.pouch', 'leather_light', T, (0.42, -0.62, 2.45))
    K.mk(rig, C.bm_box(0.1, 0.1, 0.55, 0.02), 'Torso.hammer', 'wood', T, (-0.5, -0.62, 2.0))
    K.mk(rig, C.bm_box(0.3, 0.14, 0.12, 0.02), 'Torso.hammerhead', 'iron', T, (-0.5, -0.62, 2.28))
    for side in ('Right', 'Left'):
        K.leg_skirt(rig, side, 'ochre_cloth', 1.5, 2.0, 0.08)
        K.wraps(rig, side, 0.3, 1.2, 5, 'bandage')
        K.sandals(rig, side, 'leather', 'leather_dark', bands=(), lace=False)
        j = f'{side} Arm'
        K.mk(rig, C.bm_box(1.08, 1.08, 0.5, 0.05), f'{j}.glove', 'leather_dark', j, (K.arm_x(rig, side), 0, 2.3))
        K.mk(rig, C.bm_box(1.06, 1.06, 0.45, 0.05), f'{j}.sleeve', 'ochre_cloth', j, (K.arm_x(rig, side), 0, 3.78))
    rim = hc + 0.22
    K.dome(rig, 'Head', 'Head.helmet', 'bronze', (0, 0, rim), r=0.68, h=0.62)
    prof = [(0.66, 0.0), (0.78, -0.04), (0.82, -0.06), (0.78, -0.08), (0.64, -0.03)]
    K.mk(rig, K.bmesh_recalc(C.bm_lathe(prof, segs=40)), 'Head.brim', 'bronze_dark', 'Head', (0, 0, rim))
    K.mk(rig, C.bm_cyl(0.07, 0.2, 12), 'Head.knobpost', 'bronze_dark', 'Head', (0, 0, rim + 0.66))
    K.mk(rig, C.bm_sphere(0.12, 14, 8), 'Head.knob', 'bronze', 'Head', (0, 0, rim + 0.78))
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.08, 0.36, 0.5, 0.03), f'Head.cheek{sx}', 'bronze', 'Head', (sx * 0.66, 0.08, hc - 0.05))
        fe = C.bm_extrude([(0, 0), (0.06, 0.2), (0.05, 0.7), (0, 0.85), (-0.05, 0.7), (-0.06, 0.2)], 0.03, 0.01, 1)
        C.bm_transform(fe, rot=(90, 0, 0))
        K.mk(rig, fe, f'Head.feather{sx}', 'white_cloth', 'Head', (sx * 0.6, 0.0, rim + 0.25), rot=(0, sx * -15, 90))

    # ---- machina
    rig.joint('Base', 'HumanoidRootPart', tuple(P0))
    rig.joint('Yaw', 'Base', tuple(P0))
    rig.joint('Frame', 'Yaw', tuple(P0))
    px, py, pz = P0
    # trojnog
    K.mk(rig, C.bm_cyl(0.16, pz - 0.5, 12, bevel=0.03), 'Base.post', 'wood', 'Base', (px, py, (pz - 0.5) / 2 + 0.3))
    for k in range(3):
        a = math.radians(90 + 120 * k)
        foot = (px + 1.25 * math.cos(a), py + 1.25 * math.sin(a), 0.08)
        top = (px, py, 1.25)
        K.mk(rig, C.bm_tube([top, foot], 0.1, smooth=False, bevel_res=2), f'Base.leg{k}', 'wood', 'Base', (0, 0, 0))
        K.mk(rig, C.bm_cyl(0.16, 0.12, 12, bevel=0.03), f'Base.foot{k}', 'bronze_dark', 'Base', foot)
    K.mk(rig, C.bm_cyl(0.24, 0.2, 16, bevel=0.04), 'Base.collar', 'bronze', 'Base', (px, py, 1.25))
    K.mk(rig, C.bm_cyl(0.3, 0.12, 20, bevel=0.03), 'Yaw.turntable', 'bronze', 'Yaw', (px, py, pz - 0.42))
    for sx in (-1, 1):
        K.mk(rig, C.bm_box(0.1, 0.3, 0.5, 0.03), f'Yaw.yoke{sx}', 'bronze', 'Yaw', (px + sx * 0.26, py, pz - 0.2))
    # loze (stock)
    yF, yR = py - 1.55, py + 1.45
    K.mk(rig, C.bm_box(0.38, yR - yF, 0.26, 0.04), 'Frame.stock', 'wood', 'Frame', (px, (yF + yR) / 2, pz - 0.05))
    K.mk(rig, C.bm_box(0.22, yR - yF - 0.2, 0.05, 0.01), 'Frame.groove', 'wood_light', 'Frame', (px, (yF + yR) / 2, pz + 0.09))
    for k in range(5):
        y = yF + 0.3 + k * 0.62
        K.mk(rig, C.bm_box(0.42, 0.08, 0.3, 0.02), f'Frame.band{k}', 'bronze', 'Frame', (px, y, pz - 0.05))
    K.mk(rig, C.bm_cyl(0.07, 0.62, 10), 'Frame.trunnion', 'iron', 'Frame', (px, py, pz - 0.1), rot=(0, 90, 0))
    # rama glowicy i sprezyny
    yS = py - 0.55
    for sz in (-1, 1):
        K.mk(rig, C.bm_box(1.9, 0.42, 0.2, 0.04), f'Frame.beam{sz}', 'wood', 'Frame', (px, yS, pz + sz * 0.62))
        for sx in (-1, 1):
            K.mk(rig, C.bm_cyl(0.27, 0.1, 18, bevel=0.03), f'Frame.washer{sx}{sz}', 'bronze', 'Frame',
                 (px + sx * 0.55, yS, pz + sz * 0.76))
            K.mk(rig, C.bm_box(0.1, 0.5, 0.08, 0.02), f'Frame.lever{sx}{sz}', 'iron', 'Frame',
                 (px + sx * 0.55, yS, pz + sz * 0.84))
    for sx in (-1, 1):
        K.mk(rig, C.bm_cyl(0.2, 1.06, 16), f'Frame.spring{sx}', 'rope', 'Frame', (px + sx * 0.55, yS, pz))
        for k in range(6):
            K.mk(rig, C.bm_torus(0.205, 0.022, 18, 5), f'Frame.springring{sx}{k}', 'rope', 'Frame',
                 (px + sx * 0.55, yS, pz - 0.45 + k * 0.18))
        K.mk(rig, C.bm_box(0.16, 0.32, 1.4, 0.03), f'Frame.post{sx}', 'wood', 'Frame', (px + sx * 0.93, yS, pz))
        K.mk(rig, C.bm_box(0.14, 0.3, 1.3, 0.03), f'Frame.stanchion{sx}', 'wood', 'Frame', (px + sx * 0.24, yS, pz))
    # przednia tarcza z okienkiem
    yP = yS - 0.32
    for nm, w, h, x, z in (('L', 0.62, 1.32, -0.5, 0.0), ('R', 0.62, 1.32, 0.5, 0.0), ('T', 0.4, 0.62, 0.0, 0.35),
                           ('B', 0.4, 0.5, 0.0, -0.41)):
        K.mk(rig, C.bm_box(w, 0.06, h, 0.02), f'Frame.shield{nm}', 'bronze', 'Frame', (px + x, yP, pz + z))
    K.mk(rig, C.bm_tube([(px - 0.82, yP - 0.04, pz + 0.66), (px + 0.82, yP - 0.04, pz + 0.66)], 0.04, smooth=False),
         'Frame.shieldtop', 'gold', 'Frame', (0, 0, 0))
    scorpion_emblem(rig, 'Frame', (px, yP - 0.05, pz + 0.37), s=0.42)
    # ramiona (pozycja po strzale), pivot w sprezynach
    for side, sx in (('R', -1), ('L', 1)):
        jn = f'Limb{side}'
        piv = (px + sx * 0.55, yS, pz)
        rig.joint(jn, 'Frame', piv)
        tip = Vector((px + sx * 2.0, yS + 0.3, pz))
        K.mk(rig, C.bm_tube([piv, tuple(tip)], 0.15, radii=[1.0, 0.65], smooth=False, bevel_res=2), f'{jn}.arm', 'wood',
             jn, (0, 0, 0))
        K.mk(rig, C.bm_cyl(0.13, 0.26, 10), f'{jn}.cap', 'bronze', jn, tuple(tip), rot=(0, 0, 0))
        mid = (Vector(piv) + tip) / 2
        K.mk(rig, C.bm_torus(0.09, 0.025, 12, 5), f'{jn}.band', 'bronze', jn, tuple(mid), rot=(0, 90, 0))
        rig.attach(f'Tip{side}', jn, tuple(tip))
    # suwak z pazurem, belt
    rig.joint('Slider', 'Frame', (px, Y_FIRED, pz + 0.15))
    K.mk(rig, C.bm_box(0.3, 0.7, 0.14, 0.03), 'Slider.carriage', 'wood_light', 'Slider', (px, Y_FIRED + 0.3, pz + 0.15))
    K.mk(rig, C.bm_box(0.12, 0.12, 0.2, 0.02), 'Slider.claw', 'iron', 'Slider', (px, Y_FIRED, pz + 0.27))
    K.mk(rig, C.bm_box(0.06, 0.06, 0.32, 0.02), 'Slider.trigger', 'iron', 'Slider', (px + 0.12, Y_FIRED + 0.55, pz + 0.05),
         rot=(30, 0, 0))
    rig.attach('Claw', 'Slider', (px, Y_FIRED, pz + 0.3))
    K.mk(rig, C.bm_tube([(px - 2.0, yS + 0.3, pz), (px + 2.0, yS + 0.3, pz)], 0.025, smooth=False), 'Frame.string',
         'rope', 'Frame', (0, 0, 0))['static_string'] = 1
    rig.joint('Bolt', 'Slider', (px, Y_FIRED, pz + 0.26))
    for i, (bm, mat) in enumerate(bolt_parts()):
        K.mk(rig, bm, f'Bolt.p{i}', mat, 'Bolt', (px, Y_FIRED, pz + 0.26))
    rig.attach('BoltTip', 'Bolt', (px, Y_FIRED - 2.0, pz + 0.26))
    rig.attach('Muzzle', 'Frame', (px, yP - 0.3, pz + 0.2))
    # korba
    yW = yR - 0.05
    rig.joint('Winch', 'Frame', (px, yW, pz - 0.05))
    K.mk(rig, C.bm_cyl(0.11, 0.66, 12), 'Winch.drum', 'wood_light', 'Winch', (px, yW, pz - 0.05), rot=(0, 90, 0))
    for sx in (-1, 1):
        K.mk(rig, C.bm_cyl(0.16, 0.06, 12), f'Winch.hub{sx}', 'bronze', 'Winch', (px + sx * 0.34, yW, pz - 0.05),
             rot=(0, 90, 0))
        for k in range(2):
            a = math.radians(90 * k + (45 if sx > 0 else 0))
            end = Vector((px + sx * 0.38, yW + 0.38 * math.cos(a), pz - 0.05 + 0.38 * math.sin(a)))
            end2 = Vector((px + sx * 0.38, yW - 0.38 * math.cos(a), pz - 0.05 - 0.38 * math.sin(a)))
            K.mk(rig, C.bm_tube([tuple(end2), tuple(end)], 0.035, smooth=False), f'Winch.spoke{sx}{k}', 'wood', 'Winch', (0, 0, 0))
    rig.attach('WinchTop', 'Winch', (px, yW, pz + 0.35))

    U.scale_subtree(rig, ['Base', 'Yaw', 'Frame', 'LimbR', 'LimbL', 'Slider', 'Bolt', 'Winch'], (P0.x, P0.y, 0), SC)
    U.fx_template(bolt_parts(), 'bolt')
    U.fx_template(bolt_parts(glow=True), 'bolt_glow')
    return rig


def hooks(rig):
    static = [o for o in bpy.data.objects if o.get('static_string')]
    mat = M.get('rope')
    state = {'ob': None}

    def upd(f):
        for o in static:
            o.hide_render = True
        if state['ob'] is not None:
            me = state['ob'].data
            bpy.data.objects.remove(state['ob'])
            bpy.data.meshes.remove(me)
        a = rig.att_obj('TipR').matrix_world.translation
        b = rig.att_obj('TipL').matrix_world.translation
        n = rig.att_obj('Claw').matrix_world.translation
        bm = C.bm_merge(C.bm_tube([tuple(a), tuple(n)], 0.028, smooth=False, bevel_res=1),
                        C.bm_tube([tuple(n), tuple(b)], 0.028, smooth=False, bevel_res=1))
        ob = C.make(bm, 'DYN_string', mat)
        ob['noexport'] = 1
        state['ob'] = ob
    return [upd]


COCK = dict(LimbR=(0, 0, -38), LimbL=(0, 0, 38), Slider={'p': (0, Y_COCK, 0)})
FIRED = dict(LimbR=(0, 0, 0), LimbL=(0, 0, 0), Slider={'p': (0, 0, 0)})


def animate(rig):
    hands = dict(T=(12, 0, 0), RA=(80, 4, 10), LA=(80, 4, 10), H=(-10, 0, 0), RL=(-14, 8, 0), LL=(10, -8, 0))
    base = dict(hands, **COCK, Winch=(0, 0, 0), Frame=(0, 0, 0), Yaw=(0, 0, 0))
    A = Animator(rig, base)
    P = A.P

    def crank(turns_from, turns_to, f0, f1, extra=None, step=4):
        """Krecenie korba: korba obraca sie, rece i tulow pracuja, suwak wraca do tylu."""
        n = max(1, int((f1 - f0) / step))
        for i in range(n + 1):
            t = i / n
            ang = -360 * (turns_from + (turns_to - turns_from) * t)
            ph = math.radians(-ang)
            pose = dict(extra or {})
            pose.update(T=(12 + 5 * math.sin(ph), 0, 2 * math.sin(ph)), RA=(80 + 14 * math.sin(ph), 4, 10),
                        LA=(80 - 14 * math.sin(ph), 4, 10), H=(-8, 0, 0))
            pose['Winch'] = (ang, 0, 0)
            pose['Slider'] = {'p': (0, Y_COCK * t, 0)}
            pose['LimbR'] = (0, 0, -38 * t)
            pose['LimbL'] = (0, 0, 38 * t)
            A.key(round(f0 + (f1 - f0) * t), P(**pose))

    A.clip('Idle', 'Postój (pętla)', 0, 60, loop=True, show=[0, 15, 30])
    A.key(0, P())
    A.key(20, P(Yaw=(0, 0, 4), H=(-8, 0, 4), T=(17, 0, 1)))
    A.key(40, P(Yaw=(0, 0, -4), H=(-8, 0, -4), T=(15, 0, -1)))
    A.key(60, P())

    # ---- atak 1: strzal
    A.clip('Attack1', 'Atak 1: Strzał bełtem', 100, 52, level='poz. 0-1',
           desc='Spust, cięciwa strzela do przodu, odrzut, przeładowanie korbą.', show=[100, 104, 107, 110, 122, 140])
    A.key(0, P())
    A.key(4, P(RA=(40, 14, -10), T=(14, 0, -6), H=(-6, 0, 6)))
    A.key(6, P(RA=(36, 16, -12), T=(14, 0, -6), H=(-6, 0, 6)))
    A.key(8, P(**FIRED, RA=(30, 22, -14), T=(6, 0, -8), Frame=(-7, 0, 0), Tp=(0, -0.15), H=(0, 0, 8)))
    A.key(12, P(**FIRED, RA=(40, 14, -6), T=(10, 0, -4), Frame=(2, 0, 0), Tp=(0, -0.1)))
    A.key(16, P(**FIRED))
    crank(0, 2, 16, 44)
    A.key(52, P())
    A.event(7, 'Hit', projectile='bolt', speed=80, attachment='BoltTip')
    A.hide('Bolt', 7, 46)
    A.add_fx('projectile', 7, 16, model='bolt', **{'from': 'Claw'}, dir=(0, -1, 0.02), speed=2.2)
    A.add_fx('puffs', 7, 16, center='Muzzle', count=6, spread=0.8, rise=0.3, size=0.22, col=(0.8, 0.75, 0.65))
    A.add_fx('orb', 44, 49, at='Claw', r=0.35, col=(1, 0.8, 0.35))

    # ---- atak 2: belt przebijajacy
    A.clip('Attack2', 'Atak 2: Bełt przebijający', 200, 72, level='poz. 2-3',
           desc='Celowanie, naładowanie świecącego bełtu, potężny strzał przebijający pancerz w linii.',
           show=[200, 208, 218, 222, 226, 250])
    A.key(0, P())
    A.key(8, P(Yaw=(0, 0, -6), Frame=(3, 0, 0), T=(20, 0, -4), H=(-14, 0, 6), RA=(84, 6, 12), LA=(76, 6, 8)))
    A.key(18, P(Yaw=(0, 0, 0), Frame=(1, 0, 0), T=(22, 0, 0), H=(-16, 0, 0), RA=(40, 14, -10)))
    A.key(21, P(Yaw=(0, 0, 0), Frame=(1, 0, 0), T=(22, 0, 0), H=(-16, 0, 0), RA=(36, 16, -12)))
    A.key(23, P(**FIRED, Frame=(-12, 0, 0), Yaw={'p': (0, 0.35, 0)}, T=(-4, 0, -10), Tp=(0, -0.45),
                RA=(20, 30, -10), LA=(30, 20, 0), H=(4, 0, 10), RL=(-24, 10, 0), LL=(4, -8, 0)))
    A.key(28, P(**FIRED, Frame=(3, 0, 0), Yaw={'p': (0, 0.2, 0)}, T=(6, 0, -6), Tp=(0, -0.3)))
    A.key(34, P(**FIRED))
    crank(0, 2, 34, 64)
    A.key(72, P())
    A.event(22, 'Hit', projectile='bolt_glow', speed=110, pierce=True, attachment='BoltTip')
    A.hide('Bolt', 22, 66)
    A.add_fx('orb', 6, 22, at='BoltTip', r=0.45, col=(0.75, 0.4, 1.0), energy=150)
    A.add_fx('projectile', 22, 30, model='bolt_glow', **{'from': 'Claw'}, dir=(0, -1, 0.0), speed=2.6,
             col=(0.8, 0.55, 1.0), glow=(0.7, 0.4, 1.0), glow_e=200, streak_w=0.14, name='glow')
    A.add_fx('ring', 22, 30, center='Muzzle', r0=0.2, r1=1.6, col=(0.75, 0.45, 1.0), th=0.06, flat=1.0, fixed=True)
    A.add_fx('puffs', 22, 34, center='Muzzle', count=8, spread=1.2, rise=0.4, size=0.25, col=(0.7, 0.6, 0.8))

    # ---- atak 3: salwa
    A.clip('Attack3', 'Atak 3: Salwa (3 bełty)', 300, 76, level='poz. 4-5',
           desc='Trzy strzały pod rząd z błyskawicznym przeładowaniem.', show=[300, 307, 314, 327, 347, 360])
    A.key(0, P())
    for k, f in enumerate((6, 26, 46)):
        A.key(f - 2, P(RA=(38, 14, -10), T=(14, 0, -6), Yaw=(0, 0, (k - 1) * 5)))
        A.key(f, P(RA=(36, 16, -12), T=(14, 0, -6), Yaw=(0, 0, (k - 1) * 5)))
        A.key(f + 2, P(**FIRED, RA=(30, 22, -14), T=(6, 0, -8), Frame=(-7, 0, 0), Tp=(0, -0.12),
                       Yaw=(0, 0, (k - 1) * 5)))
        A.key(f + 5, P(**FIRED, Frame=(2, 0, 0), Yaw=(0, 0, (k - 1) * 5)))
        if k < 2:
            crank(0, 1, f + 6, f + 17, extra=dict(Yaw=(0, 0, k * 5 - 2)), step=3)
        A.event(f + 1, 'Hit', projectile='bolt', speed=80, attachment='BoltTip')
        A.hide('Bolt', f + 1, f + 16)
        yaw = math.radians((k - 1) * 5)
        A.add_fx('projectile', f + 1, f + 10, model='bolt', **{'from': 'Claw'},
                 dir=(math.sin(yaw), -math.cos(yaw), 0.02), speed=2.2, name=f's{k}')
        A.add_fx('puffs', f + 1, f + 10, center='Muzzle', count=5, spread=0.7, rise=0.3, size=0.2,
                 col=(0.8, 0.75, 0.65), seed=k + 4, name=f'p{k}')
    crank(0, 2, 52, 70)
    A.key(76, P())
    A.finish()
    return A
