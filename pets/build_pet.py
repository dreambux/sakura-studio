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
    c = (0.1, 0.45, 1.0, 1)
    b.inputs['Base Color'].default_value = c
    b.inputs['Emission Color'].default_value = c
    b.inputs['Emission Strength'].default_value = 1.6
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


def put(bm, key, mat, axis=(0, 0, 1), lo=None, hi=None, smooth=True, angle=35, name='part', gamma=1.0, **kw):
    ob = P.add(bm, mat, uv='none', smooth=smooth, angle=angle, name=name, **kw)
    if key is not None:
        paint(ob, key, axis, lo, hi, gamma)
    return ob


# ------------------------------------------------------------------ geometria pomocnicza
def tube(pts, r, radii=None, res=4):
    return C.bm_tube([tuple(p) for p in pts], r, radii=radii, res=res, bevel_res=2)


def spiral(center, axis, r0, r1, turns, h, n=60, phase=0.0):
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
    S = 4.0                      # bok szescianu
    Z0 = 0.6                     # pet unosi sie nad ziemia
    cz = Z0 + S / 2
    F = -S / 2                   # przednia sciana (y)

    # ---------------- CIALO: szescian z lekko zaokraglonymi krawedziami, polowa lod / polowa pustka
    for side, key in ((-1, 'ice'), (1, 'void')):
        h = C.bm_box(S, S, S, 0.32, 3)
        geo = h.verts[:] + h.edges[:] + h.faces[:]
        bmesh.ops.bisect_plane(h, geom=geo, plane_co=(0, 0, 0), plane_no=(-side, 0, 0), clear_outer=True)
        bmesh.ops.contextual_create(h, geom=[e for e in h.edges if e.is_boundary])
        C.bm_transform(h, loc=(0, 0, cz))
        ob = put(h, key, PM, lo=Z0, hi=Z0 + S, smooth=True, angle=35, name='body_' + key)
    full = C.bm_box(S, S, S, 0.32, 3)
    C.bm_transform(full, loc=(0, 0, cz))
    bvh = BVHTree.FromBMesh(full)

    # swiecacy szew-piorun: przod -> gora -> tyl (zygzak)
    def zz(t):
        return 0.22 * (1 if int(t) % 2 else -1)
    seam = []
    n = 9
    for k in range(n + 1):                                    # przod, od dolu w gore
        seam.append(Vector((zz(k) if 0 < k < n else 0, F - 0.04, Z0 + 0.25 + (S - 0.5) * k / n)))
    for k in range(1, n):                                     # gora, od przodu do tylu
        seam.append(Vector((zz(k + 1), F + 0.25 + (S - 0.5) * k / n, Z0 + S + 0.04)))
    for k in range(n, -1, -1):                                # tyl, w dol
        seam.append(Vector((zz(k) if 0 < k < n else 0, -F + 0.04, Z0 + 0.25 + (S - 0.5) * k / n)))
    put(C.bm_tube([tuple(p) for p in seam], 0.08, res=1, smooth=False, bevel_res=0), None, GV, smooth=False, name='seam')

    # ---------------- TWARZ na przedniej scianie
    ez = Z0 + S * 0.62
    # oko pustki: czarny owal + swiecace pierscienie + blysk
    put(C.bm_sphere(0.62, 28, 14), 'black', PM, loc=(0.95, F, ez), scale=(1.0, 0.18, 0.85), name='eye_void')
    for r in (0.48, 0.32, 0.16):
        put(C.bm_torus(r, 0.04, 32, 6), None, GV, loc=(0.95, F - 0.1, ez), rot=(90, 0, 0), scale=(1.0, 1.0, 0.85),
            name='eye_ring')
    put(C.bm_sphere(0.1, 10, 6), 'white', PM, loc=(1.2, F - 0.13, ez + 0.3), scale=(1, 0.4, 1), name='shine')
    # zla brew (ciemna, skosna) nad okiem pustki
    put(C.bm_box(1.25, 0.18, 0.22, 0.06, 2), 'void_dark', PM, loc=(0.95, F - 0.05, ez + 0.75), rot=(0, 16, 0), name='brow')
    # oko lodu: biale, duza blekitna teczowka, zrenica, dwa blyski
    put(C.bm_sphere(0.6, 28, 14), 'white', PM, loc=(-0.95, F, ez), scale=(1.0, 0.18, 0.88), name='eye_ice')
    put(C.bm_sphere(0.36, 24, 12), None, GI, loc=(-0.88, F - 0.08, ez - 0.05), scale=(1, 0.2, 1.1), name='iris_ice')
    put(C.bm_sphere(0.17, 16, 8), 'black', PM, loc=(-0.86, F - 0.13, ez - 0.05), scale=(1, 0.2, 1.25), name='pupil_ice')
    put(C.bm_sphere(0.09, 10, 6), 'white', PM, loc=(-0.72, F - 0.17, ez + 0.18), scale=(1, 0.4, 1), name='shine')
    put(C.bm_sphere(0.05, 8, 4), 'white', PM, loc=(-1.0, F - 0.17, ez - 0.22), scale=(1, 0.4, 1), name='shine')
    put(C.bm_box(1.2, 0.18, 0.2, 0.06, 2), 'ice_feather', PM, loc=(-0.95, F - 0.05, ez + 0.75), rot=(0, 8, 0), name='brow')
    # usmiech-wyszczerz z klami
    mz = Z0 + S * 0.3
    mouth = [Vector((-0.75 + 1.5 * k / 10, F - 0.03, mz + 0.18 * math.cos(math.pi * (k / 10 - 0.5)) - 0.18))
             for k in range(11)]
    mouth = [Vector((q.x, q.y, mz - 0.2 * math.sin(math.pi * k / 10))) for k, q in enumerate(mouth)]
    put(tube(mouth, 0.08, res=3), 'black', PM, name='mouth')
    for x, key, L in ((-0.42, 'white', 0.32), (0.42, 'neon', 0.32)):
        z = mz - 0.2 * math.sin(math.pi * (x + 0.75) / 1.5)
        put(cone(0.1, L, 6), key, PM, loc=(x, F - 0.08, z), rot=(180, 0, 0), name='fang')
    # rumience
    put(C.bm_sphere(0.28, 16, 8), 'neon', PM, loc=(1.55, F - 0.01, mz + 0.35), scale=(1, 0.1, 0.55), name='blush')
    put(C.bm_sphere(0.28, 16, 8), 'ice_feather', PM, loc=(-1.55, F - 0.01, mz + 0.35), scale=(1, 0.1, 0.55), name='blush')

    # ---------------- lapki (male kostki pod spodem) i ogon
    for sx in (-1, 1):
        for sy in (-1, 1):
            put(C.bm_box(0.8, 0.8, 0.55, 0.14, 2), 'ice' if sx < 0 else 'void', PM, loc=(sx * 1.2, sy * 1.2, Z0 - 0.15),
                lo=Z0 - 0.5, hi=Z0 + S, name='paw')
    tail = [Vector((0.9, -F, Z0 + 1.0)), Vector((1.6, -F + 1.2, Z0 + 0.9)), Vector((2.5, -F + 1.5, Z0 + 1.6)),
            Vector((3.0, -F + 1.0, Z0 + 2.5))]
    put(tube(tail, 0.26, [1.0, 0.75, 0.5, 0.3], 6), 'void', PM, lo=Z0, hi=Z0 + 3, name='tail')
    M = frame(tail[-1], tail[-1] - tail[-2], Vector((0, 0, 1)))
    put(flat_piece([(0, -0.55), (1.0, 0), (0, 0.55), (0.28, 0)], 0.12, M @ Matrix.Rotation(-math.pi / 2, 4, 'Y')), 'neon', PM,
        smooth=False, name='tail_tip')

    # ---------------- PUSTKA (prawa): rogi, kolce, skrzydlo nietoperza, wstegi
    top = Z0 + S
    for k, (o, d, L, r) in enumerate((((1.2, -0.6), (0.35, 0.3, 1.0), 2.2, 0.3), ((1.7, 0.6), (0.8, 0.5, 0.7), 1.6, 0.24))):
        base = Vector((o[0], o[1], top - 0.1))
        dd = Vector(d).normalized()
        pts = [base, base + dd * L * 0.45, base + dd * L * 0.8 + Vector((0.1, 0.35, 0.0)),
               base + dd * L + Vector((0.2, 0.7, -0.4))]
        put(tube(pts, r, [1.0, 0.8, 0.5, 0.05], 8), 'horn', PM, lo=top, hi=top + L, name='horn')
    for k in range(5):   # kolce na prawej krawedzi grzbietu
        y = -1.4 + k * 0.7
        M = frame(Vector((S / 2 - 0.05, y, top - 0.15)), Vector((0, 1, 0)), Vector((0.8, 0.3, 0.7)))
        put(flat_piece(blade_poly(0.9 + 0.2 * math.sin(k), 0.28, -0.4), 0.14, M), 'void_dark', PM, smooth=False, name='spike_v')
    sh = Vector((S / 2, 0.9, Z0 + S * 0.7))
    elbow = Vector((3.4, 1.3, Z0 + 3.6))
    wrist = Vector((4.2, 1.6, Z0 + 4.8))
    tips = [Vector((4.4, 2.3, Z0 + 7.6)), Vector((6.5, 2.3, Z0 + 6.6)), Vector((7.3, 2.0, Z0 + 4.2)), Vector((6.0, 1.7, Z0 + 2.0)),
            Vector((3.6, 1.4, Z0 + 1.4))]
    put(tube([sh, elbow, wrist], 0.2, [1.0, 0.75, 0.6], 6), 'horn', PM, name='wing_arm')
    for t in tips[:4]:
        mid = wrist.lerp(t, 0.55) + Vector((0, 0.15, 0.2))
        put(tube([wrist, mid, t], 0.11, [1.0, 0.7, 0.15], 5), 'horn', PM, name='wing_finger')
        put(cone(0.09, 0.55, 6), 'neon', PM, loc=tuple(t), rot=aim_rot(t - mid), name='wing_claw')
    edge = []
    for a_, b_ in zip(tips, tips[1:]):
        for k in range(6):
            t = k / 6
            q = a_.lerp(b_, t)
            edge.append(q + (wrist - q).normalized() * math.sin(math.pi * t) * 0.8)
    edge.append(tips[-1])
    mb = bmesh.new()
    cw = mb.verts.new(tuple(wrist))
    cs = mb.verts.new(tuple(sh + Vector((0.0, 0.1, -0.6))))
    ev = [mb.verts.new(tuple(q)) for q in edge]
    for i in range(len(ev) - 1):
        mb.faces.new((cw, ev[i], ev[i + 1]))
    mb.faces.new((cw, ev[-1], cs))
    bmesh.ops.recalc_face_normals(mb, faces=mb.faces[:])
    bmesh.ops.solidify(mb, geom=mb.faces[:], thickness=0.1)
    put(mb, 'void', PM, lo=Z0 + 1, hi=Z0 + 7.6, smooth=False, name='wing_membrane')
    for k, (c, ax, r0, r1, tr, h) in enumerate(((Vector((2.6, -1.4, Z0)), (0.4, 0.2, 1), 1.0, 0.7, 1.5, 4.0),
                                                 (Vector((3.4, 0.4, Z0 + 4.6)), (0.6, -0.2, 0.7), 0.6, 1.1, 1.1, 1.8))):
        put(tube(spiral(c, ax, r0, r1, tr, h, 60, k), 0.08, None, 3), 'void_dark', PM, name='ribbon_v')

    # ---------------- LOD (lewa): krysztaly, pierzaste skrzydlo, kryza, spirale
    for k, (x, y, L, tilt) in enumerate(((-1.2, -0.5, 1.6, (-0.3, 0.1)), (-0.6, 0.6, 1.1, (-0.1, 0.4)),
                                         (-1.6, 0.9, 1.2, (-0.6, 0.4)), (-1.0, 1.5, 0.8, (-0.3, 0.7)))):
        put(cone(0.32, L, 5), 'crystal', PM, loc=(x, y, top - 0.1), rot=aim_rot((tilt[0], tilt[1], 1)), smooth=False,
            axis=(0, 0, 1), lo=top, hi=top + L, name='crystal')
    root_w = Vector((-S / 2, 0.9, Z0 + S * 0.7))
    for layer, (n, L0, L1, spread, key, wd) in enumerate(((7, 2.8, 4.4, 125, 'ice_feather', 0.95),
                                                          (6, 2.0, 3.0, 110, 'ice_feather', 0.8),
                                                          (5, 1.2, 1.8, 95, 'ice_light', 0.65))):
        for k in range(n):
            t = k / (n - 1)
            ang = math.radians(-30 + spread * t + 6 * layer)
            d = Vector((-math.cos(ang), 0.3 + 0.12 * layer, math.sin(ang))).normalized()
            L = L0 + (L1 - L0) * math.sin(math.pi * (0.2 + 0.65 * t))
            base = root_w + d * (0.1 + 0.2 * layer) + Vector((0, -0.2 * layer, 0))
            M = frame(base, Vector((0, 1, 0)).cross(d).normalized(), d)
            fb = flat_piece(blade_poly(L, wd, 0.45, 10), 0.12, M)
            C.bm_map(fb, lambda c, base=base, d=d: tuple(Vector(c) + Vector((0, 0.35, 0)) * ((Vector(c) - base).dot(d) / 3.0) ** 2))
            put(fb, key, PM, axis=tuple(-d), smooth=True, angle=40, name='feather', gamma=1.3)
    for k in range(5):   # kryza z plomienistych pior na lewym boku glowy
        d = Vector((-0.5, 0.2 + 0.25 * k, 0.9 - 0.15 * k)).normalized()
        base = Vector((-S / 2 + 0.05, -1.3 + 0.55 * k, top - 0.3))
        M = frame(base, Vector((0, 0, 1)).cross(d).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0)), d)
        put(flat_piece(blade_poly(1.2 + 0.1 * k, 0.32, 0.5), 0.09, M), 'ice_light', PM, axis=tuple(-d), name='frill')
    for k, (c, ax, r0, r1, tr, h) in enumerate(((Vector((-2.6, -1.4, Z0)), (-0.4, 0.2, 1), 1.0, 0.7, 1.5, 4.0),
                                                 (Vector((-3.4, 0.4, Z0 + 4.6)), (-0.6, -0.2, 0.7), 0.6, 1.1, 1.1, 1.8))):
        put(tube(spiral(c, ax, r0, r1, tr, h, 60, k + 2), 0.075, None, 3), 'ice_light', PM, name='ribbon_i')

    # ---------------- aureola i krysztaly na orbicie
    halo_z = top + 1.6
    for side, key in ((-1, 'ice_light'), (1, 'neon')):
        pts = [Vector((math.cos(a) * 1.6, math.sin(a) * 1.3 + 0.2, halo_z + 0.2 * math.sin(a * 2)))
               for a in [math.radians(90 + side * -12 - side * k * 8.0) for k in range(21)]]
        put(tube(pts, 0.11, res=4), key, PM, name='halo')
        for k in range(4):
            put(cone(0.1, 0.45, 5), key, PM, loc=tuple(pts[3 + k * 5]), smooth=False, name='halo_spike')
    for k, a in enumerate((-0.25, 0.55, 1.3, 1.85, 2.6, 3.4)):    # tylko po bokach i z tylu - nie zaslaniaja twarzy
        p = Vector((math.cos(a) * 4.8, math.sin(a) * 3.8 + 0.6, Z0 + 0.8 + 1.5 * (k % 3)))
        key = 'crystal' if p.x < 0 else 'neon'
        b1 = bmesh.new()
        bmesh.ops.create_cone(b1, cap_ends=True, segments=4, radius1=0.34, radius2=0.0, depth=0.65)
        b2 = bmesh.new()
        bmesh.ops.create_cone(b2, cap_ends=True, segments=4, radius1=0.34, radius2=0.0, depth=0.65)
        C.bm_transform(b1, loc=(0, 0, 0.32))
        C.bm_transform(b2, loc=(0, 0, -0.32), rot=(180, 0, 0))
        put(merge([b1, b2]), key, PM, loc=tuple(p), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), 45), smooth=False,
            name='orbit_gem')
        put(C.bm_torus(0.55, 0.05, 24, 5), key, PM, loc=tuple(p), rot=(70, 0, math.degrees(a)), name='orbit_ring')
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
    target = Vector((0.0, 0.6, 3.4))
    from PIL import Image, ImageDraw, ImageFont
    shots = []
    for k, (az, el, dist) in enumerate(((-18, 10, 21.0), (-70, 8, 23.0), (165, 12, 23.0), (40, 14, 23.0))):
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
