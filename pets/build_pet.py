"""Pet "Eklipsa" (Sekret) - pekata bestia w stylu pet simulatora, rozdarta na dwie polowki:
LOD (jasny blekit, pierzaste skrzydlo, krysztaly, spirale) i PUSTKA (ciemny fiolet, skrzydlo nietoperza, rogi,
swiecace oko). Kolory z jednej palety-tekstury z gradientami (jak w grach typu pet sim), swiecace czesci
osobnym materialem (w Robloxie -> Neon).

  python pets/build_pet.py            (model + GLB + rendery)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ostatni-legion', 'maps'))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)

from lib import props as P  # noqa: E402
from lib.sculpt import Skel, param_shell, merge, cone, aim_rot, apply_mods  # noqa: E402

C = P.C
NAME = 'Eklipsa'
OUT = os.path.join(HERE, 'export')
D2R = math.pi / 180

# ------------------------------------------------------------------ paleta (gradient: gora -> dol)
PAL = [
    ('void', (178, 72, 255), (42, 14, 112)),
    ('void_dark', (96, 58, 190), (16, 10, 40)),
    ('ice', (190, 200, 250), (100, 116, 230)),
    ('ice_feather', (196, 222, 255), (34, 84, 236)),
    ('ice_light', (215, 232, 255), (120, 160, 248)),
    ('neon', (215, 110, 255), (120, 36, 215)),
    ('horn', (120, 86, 210), (22, 14, 44)),
    ('white', (252, 252, 255), (210, 218, 238)),
    ('black', (36, 22, 52), (8, 6, 14)),
    ('crystal', (200, 240, 255), (90, 150, 255)),
]
KEY = {k: i for i, (k, a, b) in enumerate(PAL)}


def make_palette(path, w=640, h=256):
    import numpy as np
    from PIL import Image
    n = len(PAL)
    img = np.zeros((h, w, 3), np.float32)
    cw = w // n
    for i, (k, top, bot) in enumerate(PAL):
        t = np.linspace(0, 1, h)[:, None]
        col = np.array(top)[None, :] * (1 - t) + np.array(bot)[None, :] * t
        img[:, i * cw:(i + 1) * cw, :] = col[:, None, :]
    Image.fromarray(img.astype('uint8')).save(path)
    return n, cw / w


def pal_material(path):
    m = bpy.data.materials.new('Paleta')
    nt = m.node_tree if m.node_tree else None
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    im = nt.nodes.new('ShaderNodeTexImage')
    im.image = bpy.data.images.load(path)
    im.interpolation = 'Linear'
    nt.links.new(im.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.35
    return m


def glow_material():
    m = bpy.data.materials.new('Neon')
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    c = (0.85, 0.35, 1.0, 1)
    b.inputs['Base Color'].default_value = c
    b.inputs['Emission Color'].default_value = c
    b.inputs['Emission Strength'].default_value = 6.0
    return m


def glow_ice_material():
    m = bpy.data.materials.new('NeonLod')
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    c = (0.55, 0.85, 1.0, 1)
    b.inputs['Base Color'].default_value = c
    b.inputs['Emission Color'].default_value = c
    b.inputs['Emission Strength'].default_value = 5.0
    return m


# ------------------------------------------------------------------ malowanie gradientem
NPAL = len(PAL)


def paint(ob, key, axis=(0, 0, 1), lo=None, hi=None, gamma=1.0):
    """UV: u = kolumna palety, v = polozenie wzdluz osi (gora jasna, dol ciemny)."""
    me = ob.data
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    mw = ob.matrix_world
    ax = Vector(axis).normalized()
    ds = [(mw @ v.co).dot(ax) for v in me.vertices]
    lo = min(ds) if lo is None else lo
    hi = max(ds) if hi is None else hi
    u = (KEY[key] + 0.5) / NPAL
    for li, l in enumerate(me.loops):
        t = (ds[l.vertex_index] - lo) / max(1e-6, hi - lo)
        t = min(1.0, max(0.0, t)) ** gamma
        uv.data[li].uv = (u, 0.03 + 0.94 * t)
    return ob


def put(bm, key, mat, axis=(0, 0, 1), lo=None, hi=None, smooth=False, angle=50, name='part', gamma=1.0, **kw):
    smooth = False
    ob = P.add(bm, mat, uv='none', smooth=smooth, angle=angle, name=name, **kw)
    if key is not None:
        paint(ob, key, axis, lo, hi, gamma)
    return ob


# ------------------------------------------------------------------ geometria pomocnicza
def tube(pts, r, radii=None, res=4):
    # przekroj kwadratowy (bevel_res=0) i malo odcinkow -> kanciasty styl blokowy
    return C.bm_tube([tuple(p) for p in pts], r, radii=radii, res=max(1, min(res, 2)), bevel_res=0)


def spiral(center, axis, r0, r1, turns, h, n=60, phase=0.0):
    n = max(10, int(turns * 9))
    ax = Vector(axis).normalized()
    q = ax.to_track_quat('Z', 'Y').to_matrix()
    pts = []
    for k in range(n):
        t = k / (n - 1)
        a = phase + turns * 2 * math.pi * t
        r = r0 + (r1 - r0) * t
        pts.append(Vector(center) + q @ Vector((math.cos(a) * r, math.sin(a) * r, h * t)))
    return pts


def blade_poly(L, w, curve=0.25, n=8):
    n = min(n, 4)
    """Plomienisty, zakrzywiony kolec/pioro (2D): podstawa w (0,0), czubek w gore."""
    left, right = [], []
    for k in range(n + 1):
        t = k / n
        cx = curve * L * t * t
        hw = w * (1 - t) ** 0.8 * (0.6 + 0.4 * math.sin(math.pi * min(1, t * 1.3)))
        left.append((cx - hw, L * t))
        right.append((cx + hw * 0.8, L * t))
    return left + list(reversed(right[:-1]))


def flat_piece(poly, thick, M):
    b = C.bm_extrude(poly, thick, 0.0, 1)
    C.bm_map(b, lambda c: (c.x, c.z, c.y))      # plaszczyzna XZ, grubosc w Y
    bmesh.ops.transform(b, matrix=M, verts=b.verts)
    return b


def frame(origin, x_dir, z_dir):
    """Macierz ukladu: os X -> x_dir, os Z -> z_dir (ortogonalizowana), poczatek w origin."""
    x = Vector(x_dir).normalized()
    z = Vector(z_dir)
    z = (z - x * z.dot(x)).normalized()
    y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = Vector(origin)
    return M


def surface(bvh, origin, d):
    hit = bvh.ray_cast(Vector(origin), Vector(d).normalized())
    if hit[0] is None:
        return Vector(origin), Vector(d).normalized()
    return hit[0], hit[1]


# ------------------------------------------------------------------ budowa
def build():
    os.makedirs(OUT, exist_ok=True)
    pal_path = os.path.join(OUT, f'{NAME}_paleta.png')
    make_palette(pal_path)
    PM = pal_material(pal_path)
    GV = glow_material()
    GI = glow_ice_material()
    root = P.begin(NAME)
    rnd = random.Random(7)

    # ---------------- lezaca smocza glowa z blokow (fazowane prostopadlosciany), kazdy blok podzielony na 2 kolory
    boxes = [((0, 0.2, 1.7), (3.0, 3.2, 2.4)),        # czaszka
             ((0, -1.25, 2.6), (3.1, 0.9, 0.65)),     # luk brwiowy (daszek nad oczami)
             ((0, -1.75, 1.38), (1.9, 2.3, 1.05)),    # pysk
             ((0, -2.95, 1.5), (1.4, 0.55, 0.8)),     # nos
             ((0, -1.6, 0.42), (1.8, 2.5, 0.62)),     # zuchwa
             ((0, 2.25, 1.0), (2.4, 2.5, 1.95)),      # kark
             ((0, 3.75, 0.62), (1.8, 1.6, 1.2)),      # grzbiet
             ((0, 0.4, 3.05), (2.2, 2.2, 0.5))]       # ciemie
    for sx in (-1, 1):
        boxes.append(((sx * 1.62, -0.35, 1.3), (0.55, 1.4, 1.15)))   # policzki
    full = []
    for (c, sz) in boxes:
        b = C.bm_box(sz[0], sz[1], sz[2], 0.13, 1)
        C.bm_transform(b, loc=c)
        full.append(b.copy())
        for side, key in ((-1, 'ice'), (1, 'void')):
            if abs(c[0]) > 0.01 and (c[0] > 0) != (side > 0):
                continue
            h = b.copy()
            if abs(c[0]) <= 0.01:
                geo = h.verts[:] + h.edges[:] + h.faces[:]
                bmesh.ops.bisect_plane(h, geom=geo, plane_co=(0, 0, 0), plane_no=(-side, 0, 0), clear_outer=True)
                bmesh.ops.contextual_create(h, geom=[e for e in h.edges if e.is_boundary])
            put(h, key, PM, lo=0.0, hi=3.3, name='block_' + key)
        b.free()
    body = merge(full)
    bvh = BVHTree.FromBMesh(body)
    # ciemne wnetrze paszczy miedzy pyskiem a zuchwa
    put(C.bm_box(1.7, 2.1, 0.16, 0.0, 1), 'black', PM, loc=(0, -1.75, 0.78), name='maw')

    def zig(y):
        t = (y * 1.6) % 2.0
        return 0.16 * (abs(t - 1.0) * 2 - 1)

    seam = []
    for k in range(26):
        y = -3.2 + 7.6 * k / 25
        hit = bvh.ray_cast(Vector((zig(y), y, 6.0)), Vector((0, 0, -1)))
        if hit[0] is not None:
            seam.append(hit[0] + Vector((0, 0, 0.04)))
    put(C.bm_tube([tuple(p) for p in seam], 0.07, res=1, smooth=False, bevel_res=0), None, GV, name='seam')

    hc = Vector((0, -0.4, 1.6))
    # ---------------- strona PUSTKI: maska z ciemnych plyt, wielkie oko w pierscieniach, rogi, kolce
    p = Vector((1.15, -1.47, 1.95))
    n = Vector((0, -1, 0))
    rot = (90, 0, 0)
    put(C.bm_box(1.05, 0.12, 0.72, 0.04, 1), 'black', PM, loc=tuple(p), name='eye_void')
    for r in (0.34, 0.22):
        put(C.bm_torus(r, 0.04, 10, 4), None, GV, loc=tuple(p + n * 0.08), rot=rot, scale=(1.25, 1, 0.85), name='eye_ring')
    put(C.bm_box(0.12, 0.08, 0.12, 0.0, 1), None, GV, loc=tuple(p + n * 0.09), name='pupil')
    # plyty maski (ostre, nachodzace) wokol oka
    for k, (o, L, w) in enumerate((((0.6, -1.0, 0.9), 1.3, 0.5), ((1.1, -0.3, 1.0), 1.5, 0.55), ((1.3, -0.9, -0.2), 1.1, 0.45),
                                    ((0.5, -1.6, 0.4), 1.2, 0.4))):
        base, nb = surface(bvh, hc, o)
        up = Vector((0.3, 0.9, 0.3)) if k < 2 else Vector((0.4, 0.8, -0.3))
        M = frame(base + nb * 0.05, nb.cross(up).normalized(), (up - nb * up.dot(nb)).normalized())
        put(flat_piece(blade_poly(L, w, 0.3, 8), 0.14, M), 'void_dark', PM, axis=tuple(up), smooth=False, name='mask')
    for k, (o, d, L) in enumerate((((0.6, 0.0, 1.0), (0.35, 0.85, 0.55), 2.4), ((1.1, 0.4, 0.7), (0.8, 0.8, 0.3), 1.9),
                                    ((0.3, 0.6, 1.0), (0.1, 0.9, 0.7), 1.6))):
        base, nb = surface(bvh, hc, o)
        dd = Vector(d).normalized()
        pts = [base - nb * 0.1, base + dd * L * 0.4, base + dd * L * 0.75 + Vector((0, 0.15, 0.2)),
               base + dd * L + Vector((0.1, 0.5, 0.05))]
        put(tube(pts, 0.22 - 0.03 * k, [1.0, 0.75, 0.45, 0.04], 6), 'horn', PM, lo=base.z - 0.3, hi=base.z + L, name='horn')
    for k in range(10):   # kolce na karku (prawa strona)
        y = -0.2 + k * 0.42
        hit = bvh.ray_cast(Vector((0.55, y, 6.0)), Vector((0, 0, -1)))
        if hit[0] is None:
            continue
        base, nb = hit[0], hit[1]
        L = 0.7 + 0.5 * math.sin(k / 9 * math.pi)
        M = frame(base - nb * 0.05, Vector((1, 0, 0)), (nb + Vector((0.4, 0.5, 0))).normalized())
        put(flat_piece(blade_poly(L, 0.24, -0.45), 0.13, M), 'void_dark', PM, smooth=False, name='spike_v')
    # skrzydlo nietoperza (duze, uniesione i odchylone w bok)
    sh = Vector((1.2, 1.6, 1.7))
    elbow = Vector((2.6, 2.0, 2.9))
    wrist = Vector((3.4, 2.3, 4.1))
    tips = [Vector((3.6, 3.0, 6.6)), Vector((5.6, 2.9, 5.6)), Vector((6.4, 2.6, 3.4)), Vector((5.2, 2.3, 1.3)),
            Vector((2.8, 2.0, 0.6))]
    put(tube([sh, elbow, wrist], 0.2, [1.0, 0.75, 0.6], 6), 'horn', PM, name='wing_arm')
    for t in tips[:4]:
        mid = wrist.lerp(t, 0.55) + Vector((0, 0.15, 0.2))
        put(tube([wrist, mid, t], 0.1, [1.0, 0.7, 0.15], 5), 'horn', PM, name='wing_finger')
        put(cone(0.08, 0.5, 5), 'neon', PM, loc=tuple(t), rot=aim_rot(t - mid), smooth=False, name='wing_claw')
    edge = []
    for a, b in zip(tips, tips[1:]):
        for k in range(3):
            t = k / 3
            q = a.lerp(b, t)
            q = q + (wrist - q).normalized() * math.sin(math.pi * t) * 0.8
            edge.append(q)
    edge.append(tips[-1])
    mb = bmesh.new()
    cw = mb.verts.new(tuple(wrist))
    cs = mb.verts.new(tuple(sh + Vector((0.1, 0.1, -0.5))))
    ev = [mb.verts.new(tuple(q)) for q in edge]
    for i in range(len(ev) - 1):
        mb.faces.new((cw, ev[i], ev[i + 1]))
    mb.faces.new((cw, ev[-1], cs))
    bmesh.ops.recalc_face_normals(mb, faces=mb.faces[:])
    bmesh.ops.solidify(mb, geom=mb.faces[:], thickness=0.12)
    put(mb, 'void', PM, lo=0.5, hi=6.6, smooth=True, angle=30, name='wing_membrane')
    # ciemne petle-wstegi po prawej
    for k, (c, ax, r0, r1, tr, h) in enumerate(((Vector((1.8, -1.0, 0.3)), (0.4, 0.3, 1), 1.2, 0.8, 1.5, 3.2),
                                                 (Vector((2.6, 1.0, 3.2)), (0.6, -0.2, 0.7), 0.7, 1.3, 1.1, 1.8),
                                                 (Vector((1.2, 3.6, 0.4)), (0.3, 0.6, 1), 0.9, 0.6, 1.2, 2.2))):
        put(tube(spiral(c, ax, r0, r1, tr, h, 56, k), 0.075, None, 3), 'void_dark', PM,
            name='ribbon_v')

    # ---------------- strona LODU: gladka jasna twarz, zmruzone oko, wyszczerz z klami, pierzaste skrzydlo
    p2 = Vector((-1.15, -1.47, 1.95))
    put(C.bm_box(0.95, 0.12, 0.55, 0.04, 1), 'white', PM, loc=tuple(p2), name='eye_ice')
    put(C.bm_box(0.36, 0.1, 0.42, 0.02, 1), None, GI, loc=tuple(p2 + Vector((0.12, -0.06, 0))), name='iris_ice')
    put(C.bm_box(0.12, 0.1, 0.3, 0.0, 1), 'black', PM, loc=tuple(p2 + Vector((0.12, -0.1, 0))), name='pupil_ice')
    put(C.bm_box(1.1, 0.3, 0.16, 0.03, 1), 'ice_feather', PM, loc=tuple(p2 + Vector((0, -0.12, 0.36))), rot=(0, -8, 0),
        name='lid_ice')
    # warga i kly (wyszczerz) - kly lodowe po lewej, fioletowe po prawej
    for k, x in enumerate((-0.75, -0.42, -0.15, 0.15, 0.42, 0.75)):
        key = 'white' if x < 0 else 'neon'
        L = 0.5 if abs(x) > 0.6 else 0.3
        put(cone(0.1, L, 4), key, PM, loc=(x, -2.75, 0.88), rot=(180, 0, 45), name='fang')
    for k, x in enumerate((-0.5, 0.5)):
        put(cone(0.09, 0.3, 4), 'white' if x < 0 else 'neon', PM, loc=(x, -2.65, 0.68), rot=(0, 0, 45), name='fang_low')
    # pierzaste skrzydlo (plomieniste piora w 3 warstwach)
    root_w = Vector((-1.2, 1.6, 1.8))
    for layer, (n, L0, L1, spread, key, wd) in enumerate(((7, 2.8, 4.4, 125, 'ice_feather', 0.95),
                                                          (6, 2.0, 3.0, 110, 'ice_feather', 0.8),
                                                          (5, 1.2, 1.8, 95, 'ice_light', 0.65))):
        for k in range(n):
            t = k / (n - 1)
            ang = math.radians(-35 + spread * t + 6 * layer)
            d = Vector((-math.cos(ang), 0.35 + 0.12 * layer, math.sin(ang))).normalized()
            L = L0 + (L1 - L0) * math.sin(math.pi * (0.2 + 0.65 * t))
            base = root_w + d * (0.1 + 0.2 * layer) + Vector((0, -0.2 * layer, 0))
            M = frame(base, Vector((0, 1, 0)).cross(d).normalized(), d)
            fb = flat_piece(blade_poly(L, wd, 0.45, 10), 0.14, M)
            put(fb, key, PM, axis=tuple(-d), smooth=True, angle=40, name='feather', gamma=1.3)
    # krysztaly na lewej stronie glowy i karku
    for k in range(9):
        y = -0.6 + k * 0.45
        hit = bvh.ray_cast(Vector((-0.6 - 0.15 * (k % 2), y, 6.0)), Vector((0, 0, -1)))
        if hit[0] is None:
            continue
        base, nb = hit[0], hit[1]
        L = 0.6 + 0.5 * rnd.random()
        put(cone(0.2, L, 5), 'crystal', PM, loc=tuple(base - nb * 0.05), rot=aim_rot(nb + Vector((-0.45, 0.35, 0.1))),
            smooth=False, axis=tuple(nb), name='crystal')
    # lodowa kryza (plomieniste piora) za okiem
    cheek, nch = surface(bvh, hc, (-1, 0.3, 0.1))
    for k in range(6):
        d = (nch + Vector((-0.1, 0.5 + 0.12 * k, -0.4 + 0.25 * k))).normalized()
        M = frame(cheek, Vector((0, 0, 1)).cross(d).normalized(), d)
        put(flat_piece(blade_poly(1.1 + 0.12 * k, 0.3, 0.5), 0.08, M), 'ice_light', PM, axis=tuple(-d), name='frill')
    for k, (c, ax, r0, r1, tr, h) in enumerate(((Vector((-1.8, -1.0, 0.3)), (-0.4, 0.3, 1), 1.2, 0.8, 1.5, 3.2),
                                                 (Vector((-2.7, 1.0, 3.2)), (-0.6, -0.2, 0.7), 0.7, 1.3, 1.1, 1.8),
                                                 (Vector((-1.2, 3.6, 0.4)), (-0.3, 0.6, 1), 0.9, 0.6, 1.2, 2.2))):
        put(tube(spiral(c, ax, r0, r1, tr, h, 56, k + 2), 0.07, None, 3), 'ice_light', PM,
            name='ribbon_i')
    for sx, key in ((-1, 'ice_light'), (1, 'void_dark')):   # wasy smoka
        hit = bvh.ray_cast(Vector((sx * 0.5, -5.0, 1.15)), Vector((0, 1, 0)))
        if hit[0] is None:
            continue
        q = hit[0]
        pts = [q, q + Vector((sx * 0.9, -0.6, -0.1)), q + Vector((sx * 1.8, -0.4, 0.3)), q + Vector((sx * 2.1, 0.2, 0.9)),
               q + Vector((sx * 1.8, 0.4, 1.3))]
        put(tube(pts, 0.045, [1, 0.9, 0.7, 0.5, 0.15], 2), key, PM, name='whisker')

    # ---------------- unoszace sie ozdoby: rozdarta aureola z kolcami + krysztaly-runy na orbicie
    halo_z = 4.4
    for side, key in ((-1, 'ice_light'), (1, 'neon')):
        pts = [Vector((math.cos(a) * 1.4, math.sin(a) * 1.1 + 0.4, halo_z + 0.2 * math.sin(a * 2)))
               for a in [math.radians(90 + side * -12 - side * k * 8.0) for k in range(21)]]
        put(tube(pts, 0.1, res=4), key, PM, name='halo')
        for k in range(4):
            q = pts[3 + k * 5]
            put(cone(0.09, 0.42, 4), key, PM, loc=tuple(q), smooth=False, name='halo_spike')
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        p = Vector((math.cos(a) * 4.2, math.sin(a) * 3.6 + 0.6, 0.9 + 1.4 * (k % 3)))
        key = 'crystal' if p.x < 0 else 'neon'
        b1 = bmesh.new()
        bmesh.ops.create_cone(b1, cap_ends=True, segments=4, radius1=0.32, radius2=0.0, depth=0.6)
        b2 = bmesh.new()
        bmesh.ops.create_cone(b2, cap_ends=True, segments=4, radius1=0.32, radius2=0.0, depth=0.6)
        C.bm_transform(b1, loc=(0, 0, 0.3))
        C.bm_transform(b2, loc=(0, 0, -0.3), rot=(180, 0, 0))
        put(merge([b1, b2]), key, PM, loc=tuple(p), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), 45), smooth=False,
            name='orbit_gem')
        put(C.bm_torus(0.5, 0.06, 8, 4), key, PM, loc=tuple(p), rot=(70, 0, math.degrees(a)), name='orbit_ring')
    return root, PM, GV, GI


# ------------------------------------------------------------------ eksport i render
def export_glb(root, path):
    dg = bpy.context.evaluated_depsgraph_get()
    coll = bpy.data.collections.new('EXP')
    bpy.context.scene.collection.children.link(coll)
    top = bpy.data.objects.new(NAME, None)
    coll.objects.link(top)
    groups = {}
    for o in root.children_recursive:
        if o.type != 'MESH':
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        me.transform(o.matrix_world)
        groups.setdefault(o.data.materials[0].name, []).append(me)
    made = [top]
    rep = {}
    for mname, mes in groups.items():
        chunks, cur, ct = [], [], 0
        for me in mes:
            t = sum(len(p.vertices) - 2 for p in me.polygons)
            if cur and ct + t > 18000:
                chunks.append(cur)
                cur, ct = [], 0
            cur.append(me)
            ct += t
        chunks.append(cur)
        for ci, ch in enumerate(chunks):
            bm = bmesh.new()
            for me in ch:
                bm.from_mesh(me)
                bpy.data.meshes.remove(me)
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            out = bpy.data.meshes.new(f'{NAME}_{mname}{ci or ""}')
            bm.to_mesh(out)
            rep[out.name] = len(bm.faces)
            bm.free()
            out.materials.clear()
            out.materials.append(bpy.data.materials[mname])
            out.transform(Matrix.Rotation(math.pi, 4, 'Z'))
            ob = bpy.data.objects.new(out.name, out)
            coll.objects.link(ob)
            ob.parent = top
            made.append(ob)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in made:
        o.select_set(True)
    bpy.context.view_layer.objects.active = top
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_materials='EXPORT', export_animations=False,
                              export_image_format='AUTO')
    for o in made:
        o.hide_render = True
    return rep


def render(root, base):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
    bg.inputs['Color'].default_value = (0.75, 0.8, 1.0, 1)
    bg.inputs['Strength'].default_value = 0.7
    for rot, e, col in (((45, 0, 30), 2.6, (1.0, 0.96, 0.92)), ((60, 0, 210), 1.1, (0.7, 0.75, 1.0))):
        ld = bpy.data.lights.new('L', 'SUN')
        ld.energy = e
        ld.angle = 0.1
        ld.color = col
        lo = bpy.data.objects.new('L', ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = [a * D2R for a in rot]
    me = bpy.data.meshes.new('ground')
    me.from_pydata([(-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('G', me)
    sc.collection.objects.link(g)
    g.is_shadow_catcher = True
    cd = bpy.data.cameras.new('Cam')
    cam = bpy.data.objects.new('Cam', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cd.lens = 50
    target = Vector((0.0, 0.4, 2.0))
    from PIL import Image, ImageDraw, ImageFont
    shots = []
    for k, (az, el, dist) in enumerate(((-18, 16, 18.0), (-75, 12, 19.0), (160, 16, 19.0), (40, 24, 19.0))):
        d = Vector((math.sin(az * D2R) * math.cos(el * D2R), -math.cos(az * D2R) * math.cos(el * D2R), math.sin(el * D2R)))
        cam.location = target + d * dist
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        res = 1100 if k == 0 else 560
        sc.render.resolution_x = sc.render.resolution_y = res
        p = f'{base}_{k}.png'
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        shots.append(p)

    def backdrop(size):
        import numpy as np
        h = size[1]
        y = np.linspace(0, 1, h)[:, None, None]
        top = np.array((92, 70, 170)) * 1.0
        bot = np.array((40, 120, 190)) * 1.0
        img = top * (1 - y) + bot * y
        img = np.repeat(img, size[0], axis=1)
        return Image.fromarray(img.astype('uint8')).convert('RGBA')
    hero = Image.open(shots[0]).convert('RGBA')
    bgi = backdrop(hero.size)
    bgi.alpha_composite(hero)
    d = ImageDraw.Draw(bgi)
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 54)
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    d.text((40, 30), NAME, font=fb, fill=(255, 255, 255), stroke_width=4, stroke_fill=(40, 20, 70))
    d.text((44, 98), 'Sekret', font=fs, fill=(230, 120, 255), stroke_width=3, stroke_fill=(40, 20, 70))
    bgi.convert('RGB').save(f'{base}_hero.png')
    sheet = backdrop((560 * 3, 560))
    for i, p in enumerate(shots[1:]):
        sheet.alpha_composite(Image.open(p).convert('RGBA'), (i * 560, 0))
    sheet.convert('RGB').save(f'{base}_widoki.png')
    for p in shots:
        os.remove(p)


if __name__ == '__main__':
    root, PM, GV, GI = build()
    base = os.path.join(OUT, NAME)
    bpy.context.view_layer.update()
    render(root, base)
    rep = export_glb(root, base + '.glb')
    print('GLB czesci:', rep)
    bpy.ops.wm.save_as_mainfile(filepath=base + '.blend', compress=True)
