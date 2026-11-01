"""Przeciwnicy - nieumarli Grecy (styl R6 jak jednostki). Jeden generator, rozne warianty.
Klipy: Idle = chod (petla), Attack1 = atak na baze, Attack2 = trafienie (drgniecie), Attack3 = smierc."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import kit as K
from lib.anim import Animator
from units import common as U

ZSKIN = (0.26, 0.40, 0.20)
SPECS = {
    'Zombie': dict(display='Zombie', skin=ZSKIN, tunic='linen', note='zwykly, podarta lniana tunika', speed=1.0),
    'Biegacz': dict(display='Biegacz', skin=(0.42, 0.20, 0.14), tunic='red_dark', note='szybki, chudy, pochylony', speed=1.8,
                    B=dict(tw=1.8, aw=0.85, ad=0.85, lw=0.85, ld=0.85)),
    'Ukryty': dict(display='Ukryty zombie', skin=(0.56, 0.62, 0.66), tunic='purple_cloth', note='blady, w kapturze (polprzezroczysty w grze)',
                   speed=1.1, hood=True),
    'PancernyLegionista': dict(display='Pancerny Legionista', skin=ZSKIN, tunic='red_dark', note='zardzewiala lorica i helm',
                               speed=0.8, armor=True),
    'Tarczownik': dict(display='Tarczownik', skin=ZSKIN, tunic='leather', note='wielka pekniety tarcza z przodu', speed=0.8,
                       shield=True),
    'Grubas': dict(display='Grubas Zarazy', skin=(0.34, 0.46, 0.20), tunic='leather', note='napuchniety, rozpada sie na male',
                   speed=0.6, B=dict(tw=3.0, td=2.0, th=2.4, aw=1.3, ad=1.3, lw=1.3, ld=1.3)),
    'Nekromanta': dict(display='Nekromanta', skin=(0.50, 0.52, 0.48), tunic='purple_cloth', note='leczy i wskrzesza, laska z czaszka',
                       speed=0.8, robe=True, staff=True),
    'Kopacz': dict(display='Kopacz', skin=ZSKIN, tunic='leather', note='kopie pod ziemia, kilof, brud', speed=1.0, pick=True),
    'Harpia': dict(display='Harpia', skin=(0.50, 0.40, 0.34), tunic='leather', note='latajaca: skrzydla, szpony', speed=1.3,
                   wings=True),
    'Zarazowiec': dict(display='Zarazowiec', skin=(0.40, 0.46, 0.16), tunic='linen', note='zielona chmura wylacza wieze', speed=0.9,
                       plague=True),
    'Berserker': dict(display='Berserker', skin=(0.40, 0.18, 0.12), tunic='leather_dark', note='dwa topory, szal', speed=1.3,
                      axes=True, B=dict(tw=2.3, aw=1.15, ad=1.15)),
    'ZombieCyklop': dict(display='Zombie Cyklop (boss)', skin=(0.36, 0.42, 0.30), tunic='leather', note='olbrzym z jednym okiem, maczuga',
                         speed=0.5, cyclops=True, B=dict(tw=3.2, td=1.8, th=3.0, aw=1.5, ad=1.5, al=3.0, lw=1.5, ld=1.5, ll=2.8,
                                                         hr=0.9, hh=1.7)),
    'KrolNekropolii': dict(display='Krol Nekropolii (boss)', skin=(0.80, 0.76, 0.66), tunic='purple_cloth',
                           note='szkielet krola w koronie, miecz i plaszcz', speed=0.6, king=True, robe=True),
}


def build_spec(key, out):
    s = SPECS[key]
    face = dict(style='beast', mouth='fangs', brow=(20, 30, 14), eye_glow=(120, 255, 120))
    if s.get('cyclops'):
        face = dict(style='beast', mouth='teeth', brow=(20, 30, 14), eye_glow=(255, 200, 60))
    if s.get('king'):
        face = dict(style='beast', mouth='teeth', brow=(40, 30, 30), eye_glow=(160, 90, 255))
    skin = tuple(c * 0.55 for c in s['skin']) if not s.get('king') else s['skin']
    rig = U.body(key, out, skin, face_kw=face, B=s.get('B'), mats=dict(torso=s['tunic']))
    B = rig.B
    hc = B['head_c']
    T = 'Torso'
    tz = B['tz']
    # porwana tunika: postrzepiony dol na nogach + latki
    for side in ('Right', 'Left'):
        j = f'{side} Leg'
        x = K.leg_x(rig, side)
        K.leg_skirt(rig, side, s['tunic'], B['ll'] * 0.7, B['ll'], 0.08)
        for k in range(3):
            K.mk(rig, C.bm_cyl(0.14, 0.32, 3, r2=0.0), f'{j}.rag{k}', s['tunic'], j,
                 (x - B['lw'] * 0.3 + k * B['lw'] * 0.3, -B['ld'] / 2 - 0.02, B['ll'] * 0.7 - 0.12), rot=(180, 0, 0))
        K.mk(rig, C.bm_box(B['lw'] + 0.06, B['ld'] + 0.06, 0.25, 0.04), f'{j}.bandage', 'bandage', j, (x, 0, B['ll'] * 0.35))
    K.mk(rig, C.bm_box(0.6, 0.06, 0.5, 0.05), 'Torso.patch', 'leather', T, (0.4, -B['td'] / 2 - 0.02, tz + 0.3), rot=(0, 15, 0))
    for k in range(3):
        K.mk(rig, C.bm_box(0.5, 0.05, 0.08, 0.02), f'Torso.rib{k}', 'bandage', T, (-0.45, -B['td'] / 2 - 0.03, tz - 0.1 - k * 0.2))
    if s.get('armor'):
        for i in range(4):
            K.mk(rig, C.bm_box(B['tw'] + 0.14, B['td'] + 0.14, 0.24, 0.05), f'Torso.band{i}', 'iron_rust' if False else 'steel_dark',
                 T, (0, 0, tz - 0.6 + i * 0.25), rot=(0, (i - 1.5) * 3, 0))
        rim = hc + 0.22
        K.dome(rig, 'Head', 'Head.helmet', 'steel_dark', (0, 0, rim), r=0.69, h=0.52)
        K.mk(rig, C.bm_box(0.1, 0.5, 0.5, 0.03), 'Head.cheek', 'steel_dark', 'Head', (0.66, 0.05, hc - 0.05))
    if s.get('hood'):
        prof = [(0.75, -0.3), (0.8, 0.2), (0.6, 0.6), (0.0, 0.75)]
        bm = C.bm_lathe(prof, segs=24, arc=220, a0=-20)
        C.bm_solidify(bm, 0.05)
        K.mk(rig, bm, 'Head.hood', s['tunic'], 'Head', (0, 0.05, hc), angle=None)
    if s.get('robe'):
        for side in ('Right', 'Left'):
            j = f'{side} Leg'
            K.mk(rig, C.bm_box(B['lw'] + 0.14, B['ld'] + 0.14, B['ll'] - 0.1, 0.06), f'{j}.robe', s['tunic'], j,
                 (K.leg_x(rig, side), 0, B['ll'] / 2 + 0.05))
    if s.get('king'):
        K.mk(rig, C.bm_cyl(0.66, 0.4, 16), 'Head.crown', 'gold', 'Head', (0, 0, hc + 0.75))
        for k in range(8):
            a = 2 * math.pi * k / 8
            K.mk(rig, C.bm_cyl(0.12, 0.4, 4, r2=0.0), f'Head.spike{k}', 'gold', 'Head',
                 (math.cos(a) * 0.6, math.sin(a) * 0.6, hc + 1.1))
        K.cape(rig, 'purple_cloth', 'gold', length=3.0, clasp='gold')
    if s.get('cyclops'):
        K.mk(rig, C.bm_box(1.6, 0.3, 0.3, 0.1), 'Head.brow', 'fur_dark', 'Head', (0, -0.82, hc + 0.35))
        K.mk(rig, C.bm_cyl(0.75, 0.4, 3, r2=0.0), 'Head.horn', 'horn', 'Head', (0, 0, hc + 1.0))
    if s.get('plague'):
        K.mk(rig, C.bm_sphere(0.9, 14, 10), 'Torso.sack', 'linen', T, (0, B['td'] / 2 + 0.6, tz + 0.2), scale=(1, 0.7, 1.2))
        for k in range(5):
            K.mk(rig, C.bm_sphere(0.14, 8, 6), f'Torso.boil{k}', 'glow_green', T,
                 (-0.6 + k * 0.3, -B['td'] / 2 - 0.05, tz - 0.4 + (k % 2) * 0.5))
    if s.get('wings'):
        for side, sx in (('Right', -1), ('Left', 1)):
            j = f'{side} Arm'
            w = C.bm_extrude([(0, 0), (1.6, 0.4), (2.6, -0.4), (2.2, -1.6), (1.4, -1.0), (0.6, -1.8), (0, -0.6)], 0.08, 0.02, 1)
            C.bm_map(w, lambda co, sx=sx: (sx * (co.x * 0.4 + 0.5), co.z + 0.2, co.y + 0.0))
            K.mk(rig, K.bmesh_recalc(w), f'{j}.wing', 'leather_dark', j, (K.arm_x(rig, side), 0, B['ll'] + B['th'] - 0.4))
        for side in ('Right', 'Left'):
            for k in range(3):
                K.mk(rig, C.bm_cyl(0.08, 0.5, 4, r2=0.0), f'{side} Leg.talon{k}', 'horn', f'{side} Leg',
                     (K.leg_x(rig, side) - 0.3 + k * 0.3, -0.6, 0.12), rot=(80, 0, 0))
    # bron
    hand = rig.hand['Right Arm']
    hx, hz = hand.x, hand.z
    if s.get('staff') or s.get('pick') or s.get('cyclops') or s.get('king'):
        rig.joint('Weapon', 'Right Arm', tuple(hand), follow='Right Arm')
        if s.get('staff'):
            U.shaft(rig, 'Weapon', 'Weapon.staff', 'wood', 1.6, -2.6, 0.08, hx, hz)
            K.mk(rig, C.bm_sphere(0.35, 14, 10), 'Weapon.skull', 'bandage', 'Weapon', (hx, -2.8, hz))
            K.mk(rig, C.bm_sphere(0.1, 8, 6), 'Weapon.eye', 'glow_violet', 'Weapon', (hx, -3.05, hz + 0.05))
        elif s.get('pick'):
            U.shaft(rig, 'Weapon', 'Weapon.haft', 'wood', 0.5, -2.2, 0.08, hx, hz)
            K.mk(rig, C.bm_tube([(hx, -2.2, hz - 0.9), (hx, -2.35, hz), (hx, -2.2, hz + 0.9)], 0.1, radii=[0.3, 1, 0.3]),
                 'Weapon.head', 'steel_dark', 'Weapon', (0, 0, 0))
        elif s.get('cyclops'):
            U.shaft(rig, 'Weapon', 'Weapon.club', 'bark', 0.6, -4.0, 0.35, hx, hz)
            K.mk(rig, C.bm_sphere(0.65, 12, 8), 'Weapon.knob', 'bark', 'Weapon', (hx, -4.1, hz))
        else:
            K.mk(rig, C.bm_box(0.12, 3.4, 0.4, 0.04), 'Weapon.blade', 'steel_dark', 'Weapon', (hx, -1.9, hz))
            K.mk(rig, C.bm_box(0.9, 0.2, 0.2, 0.04), 'Weapon.guard', 'gold', 'Weapon', (hx, -0.2, hz))
    if s.get('axes'):
        for side in ('Right', 'Left'):
            h = rig.hand[f'{side} Arm']
            jn = f'Axe{side[0]}'
            rig.joint(jn, f'{side} Arm', tuple(h), follow=f'{side} Arm')
            U.shaft(rig, jn, f'{jn}.haft', 'wood', 0.3, -1.6, 0.07, h.x, h.z)
            bm = C.bm_extrude([(0, 0), (0.7, -0.3), (0.8, 0.4), (0, 0.3)], 0.08, 0.02, 1)
            C.bm_transform(bm, rot=(0, 90, 0))
            K.mk(rig, bm, f'{jn}.blade', 'steel_dark', jn, (h.x, -1.5, h.z + 0.1))
    if s.get('shield'):
        sp = Vector((B['ax'], -0.9, rig.hand['Left Arm'].z))
        rig.joint('Shield', 'Left Arm', tuple(sp), follow='Left Arm')
        prof = [(0.0, 0.0), (1.6, 0.0), (1.65, 0.06)] + [(1.6 * (1 - i / 10), 0.25 * (1 - (i / 10) ** 2) + 0.06) for i in range(11)]
        bm = K.bmesh_recalc(C.bm_lathe(prof, segs=40))
        import bmesh
        kill = [f for f in bm.faces if f.calc_center_median().x > 0.9 and f.calc_center_median().y > 0.3]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        C.bm_transform(bm, rot=(90, 0, 0))
        K.mk(rig, bm, 'Shield.board', 'bronze_dark', 'Shield', tuple(sp), angle=None)
    rig.attach('Hands', 'Right Arm', tuple(hand))
    rig.attach('Chest', 'Torso', (0, -1.0, tz))
    return rig


def animate_spec(key, rig):
    s = SPECS[key]
    sp = s['speed']
    fly = s.get('wings')
    reach = not (s.get('staff') or s.get('axes') or s.get('shield') or fly)
    arms = (85, 6, 6) if reach else (30, 10, 0)
    lean = 14 if key == 'Biegacz' else 8
    base = dict(T=(lean, 0, 0), H=(6, 6, 0), RA=arms, LA=arms if not s.get('shield') else (50, 6, 10),
                RL=(0, 4, 0), LL=(0, -4, 0), Weapon={'pitch': 60}, Shield={'pitch': 0},
                AxeR={'pitch': 20}, AxeL={'pitch': 20}, air=1.8 if fly else 0.0)
    A = Animator(rig, base)
    P = A.P
    n = int(round(40 / sp))
    swing = 32 if not fly else 10
    A.clip('Idle', 'Chod (petla)', 0, n, loop=True, show=[0, n // 4, n // 2])
    for k, t in enumerate((0, 0.25, 0.5, 0.75, 1.0)):
        ph = math.sin(t * 2 * math.pi)
        A.key(round(n * t), P(RL=(swing * ph, 4, 0), LL=(-swing * ph, -4, 0),
                              T=(lean + 2 * abs(ph), 3 * ph, 4 * ph), H=(6 + 4 * abs(ph), 6 - 8 * ph, 0),
                              RA=(arms[0] + 8 * ph, arms[1], arms[2]), LA=(arms[0] - 8 * ph, arms[1], arms[2]) if not s.get('shield') else (50, 6, 10),
                              air=(1.8 + 0.3 * ph) if fly else 0.0))
    A.clip('Attack1', 'Atak na baze', 100, 34, level='',
           desc='Zamach/ugryzienie - zadaje obrazenia bazie.', show=[100, 106, 110, 114, 122, 130])
    A.key(0, P())
    A.key(8, P(T=(-8, 0, -20), RA=(170, 20, 0), LA=(150, 20, 0), H=(-10, 0, 0), Tp=(0, -0.2), Weapon={'pitch': 120}))
    A.key(13, P(T=(26, 0, 10), RA=(70, 0, 20), LA=(60, 0, 20), H=(16, 0, 0), Tp=(0, 0.7), LL=(30, -4, 0), RL=(-24, 4, 0),
                Weapon={'pitch': -40}))
    A.key(22, P(T=(18, 0, 4), Tp=(0, 0.4)))
    A.key(34, P())
    A.event(13, 'Hit')
    A.add_fx('sparks', 13, 20, center='Chest', count=10, spread=1.2, col=(0.6, 1.0, 0.5), name='bite')
    A.clip('Attack2', 'Trafienie (drgniecie)', 200, 12, level='', desc='Krotkie drgniecie do tylu po trafieniu.',
           show=[200, 202, 204, 206, 209, 212])
    A.key(0, P())
    A.key(3, P(T=(-14, -6, 8), H=(-14, 0, 0), Tp=(0, -0.35), RA=(arms[0] + 20, 20, 0)))
    A.key(12, P())
    A.event(0, 'HitReact')
    A.clip('Attack3', 'Smierc', 300, 30, level='', desc='Upadek do tylu (w grze potem rozpad na kawalki).',
           show=[300, 304, 308, 314, 320, 330])
    A.key(0, P())
    A.key(6, P(T=(-20, 10, 10), H=(-20, 10, 0), RA=(150, 40, 0), LA=(120, 40, 0), Tp=(0, -0.3)))
    A.key(16, P(T=(-80, 10, 20), H=(-10, 20, 0), RA=(160, 70, 0), LA=(140, 70, 0), Tp=(0, -1.6), RL=(30, 10, 0), LL=(50, -10, 0),
                ground=False, air=-2.4 if not fly else -0.5))
    A.key(30, P(T=(-90, 10, 20), H=(-6, 20, 0), RA=(170, 80, 0), LA=(150, 80, 0), Tp=(0, -1.8), RL=(20, 10, 0), LL=(40, -10, 0),
                ground=False, air=-2.5 if not fly else -0.6))
    A.event(16, 'Break')
    A.add_fx('puffs', 16, 30, center=(0, 1.6, 0.3), count=10, spread=1.6, rise=0.4, col=(0.4, 0.55, 0.3), name='dust')
    if s.get('plague'):
        A.add_fx('puffs', 0, n, center='Chest', count=8, spread=1.6, rise=1.2, size=0.5, col=(0.4, 0.9, 0.3), name='gas')
    A.finish()
    return A


def make(key):
    s = SPECS[key]
    info = dict(name=key, display=s['display'], subtitle=f'Przeciwnik · {s["note"]} · predkosc x{s["speed"]}',
                cam=dict(target=(0, -0.6, 3.0 if not s.get('B') else 3.6), dist=15.0 if not s.get('cyclops') else 20.0,
                         dir=(0.62, -1.0, 0.4)), ped_r=2.8)
    return info, (lambda out: build_spec(key, out)), (lambda rig: animate_spec(key, rig))
