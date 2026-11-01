"""Wspolne akcesoria (sandaly, owijki, pasy, helmy, grzebienie, peleryny, tarcze...)."""
import math
import random
from mathutils import Vector

from . import core as C
from . import materials as M

D2R = math.pi / 180


def mk(rig, bm, name, mat, joint, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), angle=40, smooth=True):
    return C.make(bm, name, M.get(mat) if isinstance(mat, str) else mat, loc=loc, rot=rot,
                  scale=scale, parent=joint, rig=rig, angle=angle, smooth=smooth)


def leg_x(rig, side):
    return (-1 if side == 'Right' else 1) * rig.B['lw'] / 2


def arm_x(rig, side):
    return (-1 if side == 'Right' else 1) * rig.B['ax']


# ------------------------------------------------------------------ nogi
def sandals(rig, side, mat='leather', strap='leather_dark', bands=(0.32, 0.62), lace=True):
    B = rig.B
    x = leg_x(rig, side)
    j = f'{side} Leg'
    w = B['lw'] + 0.08
    mk(rig, C.bm_box(w, B['ld'] + 0.14, 0.14, 0.05), f'{j}.sole', 'leather_dark', j, (x, -0.04, 0.07))
    mk(rig, C.bm_box(w - 0.02, B['ld'] + 0.06, 0.10, 0.04), f'{j}.sandal', mat, j, (x, -0.02, 0.18))
    for i, z in enumerate(bands):
        mk(rig, C.bm_box(w, B['ld'] + 0.06, 0.09, 0.035), f'{j}.strap{i}', strap, j, (x, 0, z))
    if lace:
        for i in range(3):
            z = 0.25 + i * 0.16
            mk(rig, C.bm_box(0.09, 0.05, 0.22, 0.02), f'{j}.lace{i}', strap, j,
               (x, -B['ld'] / 2 - 0.03, z), rot=(0, 35 if i % 2 else -35, 0))


def wraps(rig, side, z0=0.25, z1=1.15, n=5, mat='bandage'):
    B = rig.B
    x = leg_x(rig, side)
    j = f'{side} Leg'
    for i in range(n):
        z = z0 + (z1 - z0) * i / max(1, n - 1)
        mk(rig, C.bm_box(B['lw'] + 0.07, B['ld'] + 0.07, 0.11, 0.035), f'{j}.wrap{i}', mat, j,
           (x, 0, z), rot=(0, 7 if i % 2 else -7, 0))


def greave(rig, side, mat='bronze', trim='gold', z0=0.22, z1=1.22):
    """Nagolennik: wygiety brazowy pancerz z przodu i po bokach + nakolannik."""
    B = rig.B
    x = leg_x(rig, side)
    j = f'{side} Leg'
    h = z1 - z0
    r = B['lw'] * 0.62
    prof = [(r * 0.92, 0), (r, h * 0.3), (r * 1.04, h * 0.65), (r * 0.98, h)]
    bm = C.bm_lathe(prof, segs=24, arc=200, a0=-190)
    C.bm_solidify(bm, 0.06)
    mk(rig, bm, f'{j}.greave', mat, j, (x, 0.06, z0), scale=(1.0, 0.92, 1))
    mk(rig, C.bm_sphere(0.27, 16, 10), f'{j}.knee', mat, j, (x, -0.47, z1 + 0.08), scale=(1.1, 0.55, 1))
    for z in (z0 + 0.03, z1):
        bm = C.bm_lathe([(r + 0.04, -0.03), (r + 0.06, 0), (r + 0.04, 0.03)], segs=24, arc=200, a0=-190)
        mk(rig, bm, f'{j}.greave_trim{z:.2f}', trim, j, (x, 0.06, z), scale=(1, 0.92, 1))


def leg_skirt(rig, side, mat, z0, z1, extra=0.06):
    """Spodenki/tunika na udzie (dzielona miedzy nogi jak w R6)."""
    B = rig.B
    x = leg_x(rig, side)
    j = f'{side} Leg'
    mk(rig, C.bm_box(B['lw'] + extra, B['ld'] + extra, z1 - z0, 0.05), f'{j}.skirt', mat, j,
       (x, 0, (z0 + z1) / 2))


def pteruges(rig, side, mat='leather', trim='gold', z1=None, length=0.6, n=3):
    """Paski skorzane (pteryges) na udzie."""
    B = rig.B
    x = leg_x(rig, side)
    j = f'{side} Leg'
    z1 = z1 if z1 is not None else B['ll'] - 0.02
    w = (B['lw'] + 0.1) / n
    for face_y, rot in ((-1, 0), (1, 0)):
        for i in range(n):
            px = x - (B['lw'] + 0.1) / 2 + w * (i + 0.5)
            mk(rig, C.bm_box(w - 0.04, 0.07, length, 0.025), f'{j}.pter{face_y}{i}', mat, j,
               (px, face_y * (B['ld'] / 2 + 0.05), z1 - length / 2))
            mk(rig, C.bm_box(w - 0.04, 0.08, 0.06, 0.02), f'{j}.ptert{face_y}{i}', trim, j,
               (px, face_y * (B['ld'] / 2 + 0.055), z1 - length + 0.04))
    for sx in (-1, 1):
        mk(rig, C.bm_box(0.07, B['ld'] + 0.1, length, 0.025), f'{j}.pters{sx}', mat, j,
           (x + sx * (B['lw'] / 2 + 0.05), 0, z1 - length / 2))


# ------------------------------------------------------------------ tulow
def belt(rig, z, mat='leather', buckle='gold', h=0.24, studs=True):
    B = rig.B
    mk(rig, C.bm_box(B['tw'] + 0.1, B['td'] + 0.1, h, 0.04), 'Torso.belt', mat, 'Torso', (0, 0, z))
    mk(rig, C.bm_box(0.42, 0.08, h + 0.08, 0.03), 'Torso.buckle', buckle, 'Torso',
       (0, -B['td'] / 2 - 0.07, z))
    mk(rig, C.bm_box(0.26, 0.06, h - 0.04, 0.02), 'Torso.buckle_in', 'bronze_dark', 'Torso',
       (0, -B['td'] / 2 - 0.10, z))
    if studs:
        for i, xx in enumerate((-0.75, -0.48, 0.48, 0.75)):
            mk(rig, C.bm_sphere(0.05, 10, 6), f'Torso.belt_stud{i}', buckle, 'Torso',
               (xx, -B['td'] / 2 - 0.06, z))


def chest_strap(rig, mat='leather', studs='gold', from_right=True, w=0.22):
    """Pas przez piers (z ramienia na biodro), z przodu i z tylu."""
    B = rig.B
    s = 1 if from_right else -1
    ang = math.degrees(math.atan2(B['th'] - 0.2, B['tw'] - 0.2))
    L = math.hypot(B['th'] - 0.2, B['tw'] - 0.2) + 0.2
    for yy, nm in ((-B['td'] / 2 - 0.04, 'f'), (B['td'] / 2 + 0.04, 'b')):
        mk(rig, C.bm_box(w, 0.06, L, 0.02), f'Torso.strap{nm}', mat, 'Torso',
           (0, yy, B['tz']), rot=(0, s * (90 - ang), 0))
    for i in range(3):
        t = (i - 1) * 0.55
        dx = -s * t * math.sin((90 - ang) * D2R)
        dz = t * math.cos((90 - ang) * D2R)
        mk(rig, C.bm_sphere(0.05, 10, 6), f'Torso.strapstud{i}', studs, 'Torso',
           (dx, -B['td'] / 2 - 0.08, B['tz'] + dz))


def cape(rig, mat='red_cloth', trim='gold', length=2.5, top_w=1.9, bot_w=2.5, z_top=None,
         flare=0.55, clasp='gold'):
    """Peleryna na plecach (osobny joint 'Cape', wisi z gornej krawedzi tulowia)."""
    B = rig.B
    zt = z_top if z_top is not None else B['ll'] + B['th'] - 0.08
    y0 = B['td'] / 2 + 0.06
    rig.joint('Cape', 'Torso', (0, y0, zt))
    nx, ny = 14, 12
    bm = C.bm_grid(nx, ny, 1.0, length)

    def f(co):
        t = -co.z / length
        w = top_w + (bot_w - top_w) * t
        x = co.x * w
        fold = 0.06 * math.sin(co.x * 9.0 + 0.4) * (0.3 + t)
        y = flare * t * t + fold + 0.08 * (2 * co.x) ** 2 * (0.2 + t)
        return (x, y, co.z)
    C.bm_map(bm, f)
    C.bm_solidify(bm, 0.05)
    mk(rig, bm, 'Cape.cloth', mat, 'Cape', (0, y0, zt), angle=None)
    pts = []
    for i in range(13):
        u = i / 12 - 0.5
        co = f(Vector((u, 0, -length)))
        pts.append((co[0], co[1] + 0.02, co[2] + 0.03))
    mk(rig, C.bm_tube(pts, 0.035, res=4), 'Cape.trim', trim, 'Cape', (0, y0, zt))
    for sx in (-1, 1):
        mk(rig, C.bm_cyl(0.14, 0.07, 16, bevel=0.02), f'Torso.clasp{sx}', clasp, 'Torso',
           (sx * (top_w / 2 - 0.15), -B['td'] / 2 - 0.04, zt - 0.05), rot=(90, 0, 0))


# ------------------------------------------------------------------ glowa
def crest(rig, joint, center, length=1.1, height=0.75, width=0.16, transverse=False, n=21,
          mats=('crest', 'crest_dark'), base_mat='gold', arc=170):
    """Grzebien z wlosia/pior: wachlarz cienkich klinow (jak na Gladiatorze)."""
    cx, cy, cz = center
    rnd = random.Random(7)
    for i in range(n):
        t = i / (n - 1)
        a = (90 + arc / 2 - arc * t) * D2R
        r_in, r_out = 0.12, 0.5 * length + rnd.uniform(-0.04, 0.04)
        hscale = height / (0.5 * length)
        pa = Vector((math.cos(a) * r_in, math.sin(a) * r_in * hscale))
        pb = Vector((math.cos(a) * r_out, math.sin(a) * r_out * hscale))
        tw = 0.17 + 0.05 * math.sin(t * math.pi)
        side = Vector((-math.sin(a), math.cos(a) * hscale)).normalized() * tw
        poly = [(pa.x, pa.y), (pb.x + side.x * 0.6, pb.y + side.y * 0.6),
                (pb.x - side.x * 0.6, pb.y - side.y * 0.6)]
        bm = C.bm_extrude(poly, width * rnd.uniform(0.75, 1.0), bevel=0.012, segs=1)
        rot = (90, 0, 90) if transverse else (90, 0, 0)
        if not transverse:
            # klin w plaszczyznie YZ: x2d -> -y (przod), y2d -> z
            C.bm_map(bm, lambda co: (co.z, -co.x, co.y))
            rot = (0, 0, 0)
        else:
            C.bm_map(bm, lambda co: (co.x, co.z, co.y))
            rot = (0, 0, 0)
        mk(rig, bm, f'{joint}.crest{i}', mats[i % 2], joint, (cx, cy, cz), rot=rot, angle=None)
    mk(rig, C.bm_box(0.22 if not transverse else length * 0.9, length * 0.9 if not transverse else 0.22,
                     0.1, 0.04), f'{joint}.crestbase', base_mat, joint, (cx, cy, cz + 0.02))


def dome(rig, joint, name, mat, center, r=0.68, h=0.5, segs=40, thick=0.05, open_bottom=True):
    """Kopula helmu (polsfera splaszczona), srodek podstawy w center."""
    n = 10
    prof = []
    for i in range(n, -1, -1):          # wnetrze: od gory w dol
        a = (math.pi / 2) * i / n
        prof.append(((r - thick) * math.cos(a), (h - thick) * math.sin(a)))
    for i in range(n + 1):              # zewnatrz: od dolu do gory
        a = (math.pi / 2) * i / n
        prof.append((r * math.cos(a), h * math.sin(a)))
    prof[0] = (0.0, h - thick)
    prof[-1] = (0.0, h)
    bm = C.bm_lathe(prof, segs=segs)
    bmesh_recalc(bm)
    return mk(rig, bm, name, mat, joint, center, angle=None)


def bmesh_recalc(bm):
    import bmesh
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def ring(rig, joint, name, mat, center, R, r, rot=(0, 0, 0), scale=(1, 1, 1), segs=40):
    return mk(rig, C.bm_torus(R, r, segs, 8), name, mat, joint, center, rot=rot, scale=scale)


def rivets(rig, joint, name, mat, pts, r=0.045):
    for i, p in enumerate(pts):
        mk(rig, C.bm_sphere(r, 10, 6), f'{name}{i}', mat, joint, p)


def hair_block(rig, mat, hc, back=0.62, top=0.66, length=1.1, width=1.32):
    """Wlosy w stylu Roblox: czapa + tyl."""
    mk(rig, C.bm_box(width, back, 0.36, 0.14), 'Head.hair_top', mat, 'Head', (0, 0.06, hc + 0.47))
    mk(rig, C.bm_box(width, 0.42, length, 0.15), 'Head.hair_back', mat, 'Head',
       (0, 0.42, hc + 0.55 - length / 2))


def hair_cap(rig, mat, hc, rim=0.26, length=1.1, part=True):
    """Wlosy kobiece: zaokraglona czapa schodzaca nisko na czolo (linia wlosow tuz nad brwiami),
    grzywka z przedzialkiem i tyl. Twarz zostaje odslonieta, czolo male."""
    n = 10
    prof = []
    for i in range(n + 1):
        a = (math.pi / 2) * i / n
        prof.append((0.70 * math.cos(a), 0.48 * math.sin(a)))
    prof[-1] = (0.0, 0.48)
    prof = [(0.0, -0.02), (0.70, -0.02)] + prof
    bm = C.bm_lathe(prof, segs=40)
    bmesh_recalc(bm)
    mk(rig, bm, 'Head.hair_cap', mat, 'Head', (0, 0, hc + rim), angle=None)
    # grzywka: dwa luki od przedzialka w dol na skronie
    for sx in (-1, 1):
        pts = [(sx * 0.04, -0.66, hc + rim + 0.16), (sx * 0.25, -0.69, hc + rim + 0.05),
               (sx * 0.48, -0.60, hc + rim - 0.02), (sx * 0.64, -0.36, hc + rim - 0.12)]
        mk(rig, C.bm_tube(pts, 0.085, radii=[0.7, 1.0, 1.0, 0.8], res=5), f'Head.fringe{sx}', mat, 'Head', (0, 0, 0))
    if part:
        mk(rig, C.bm_tube([(0, -0.62, hc + rim + 0.2), (0, -0.3, hc + rim + 0.46), (0, 0.1, hc + rim + 0.5)],
                          0.03, res=4), 'Head.parting', mat, 'Head', (0, 0, 0))
    mk(rig, C.bm_box(1.34, 0.44, length, 0.16), 'Head.hair_back', mat, 'Head',
       (0, 0.42, hc + rim + 0.25 - length / 2))


def laurel(rig, joint, center, R=0.64, mat='gold', leaf_mat=None, n=11, gap=60, tilt=0, scale_y=1.0):
    """Wieniec laurowy (zloty): listki wokol glowy, przerwa z przodu."""
    cx, cy, cz = center
    leaf_mat = leaf_mat or mat
    pts = []
    for i in range(25):
        a = (-90 + gap / 2 + (360 - gap) * i / 24) * D2R
        pts.append((cx + R * math.cos(a), cy + R * math.sin(a) * scale_y, cz))
    mk(rig, C.bm_tube(pts, 0.025, res=3), f'{joint}.laurel_band', mat, joint, (0, 0, 0))
    for k in range(n * 2):
        side = 1 if k % 2 else -1
        i = k // 2
        a = (-90 + gap / 2 + 8 + (360 - gap - 16) * i / (n - 1)) * D2R
        p = (cx + R * math.cos(a), cy + R * math.sin(a) * scale_y, cz + side * 0.06)
        ang = math.degrees(a)
        leaf = C.bm_extrude([(0, -0.05), (0.09, -0.03), (0.17, 0), (0.09, 0.03), (0, 0.05), (-0.02, 0)],
                            0.025, 0.006, 1)
        C.bm_transform(leaf, rot=(90, 0, 0))
        mk(rig, leaf, f'{joint}.leaf{k}', leaf_mat, joint, p, rot=(side * 30, 0, ang + 90 + side * 25))
