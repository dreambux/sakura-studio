"""Podstawowe narzedzia: scena, prymitywy (bmesh), rodzicowanie.

Jednostka = 1 stud. Postac stoi na z=0 i patrzy w -Y (przod Blendera).
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

D2R = math.pi / 180.0


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.unit_settings.system = 'NONE'
    return sc


def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tmp_eval(ob):
    """Ewaluacja (modyfikatory/krzywe) w osobnej, pustej scenie - szybko niezaleznie od liczby obiektow w glownej."""
    sc = bpy.data.scenes.get('_TMP_EVAL') or bpy.data.scenes.new('_TMP_EVAL')
    sc.collection.objects.link(ob)
    vl = sc.view_layers[0]
    vl.update()
    dg = vl.depsgraph
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    sc.collection.objects.unlink(ob)
    return me


# ---------------------------------------------------------------- bmesh makers
def bm_box(sx, sy, sz, bevel=0.0, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        b = min(bevel, sx * 0.49, sy * 0.49, sz * 0.49)
        bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=b, segments=segs,
                        affect='EDGES', profile=0.5, clamp_overlap=True)
    return bm


def bm_cyl(r, h, segs=24, r2=None, bevel=0.0, bsegs=2, caps=True):
    """Walec/stozek wzdluz Z, srodek w (0,0,0)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=h)
    if bevel > 0 and caps:
        rim = [e for e in bm.edges
               if all(abs(abs(v.co.z) - h / 2) < 1e-5 for v in e.verts)]
        bmesh.ops.bevel(bm, geom=rim, offset=bevel, segments=bsegs, affect='EDGES',
                        profile=0.5, clamp_overlap=True)
    return bm


def bm_sphere(r, u=24, v=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    return bm


def bm_torus(R, r, segs=32, rsegs=10):
    bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ring = []
        for j in range(rsegs):
            b = 2 * math.pi * j / rsegs
            rr = R + r * math.cos(b)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(segs):
        a, b2 = rings[i], rings[(i + 1) % segs]
        for j in range(rsegs):
            k = (j + 1) % rsegs
            bm.faces.new((a[j], b2[j], b2[k], a[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def bm_lathe(profile, segs=32, arc=360.0, a0=0.0):
    """Bryla obrotowa. profile = [(r, z), ...] od dolu do gory."""
    bm = bmesh.new()
    full = abs(arc - 360.0) < 1e-6
    n = segs if full else segs + 1
    rings = []
    for (r, z) in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for i in range(n):
            a = (a0 + arc * i / segs) * D2R
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        cnt = segs
        for i in range(cnt):
            i2 = (i + 1) % n if full else i + 1
            if len(A) == 1:
                bm.faces.new((A[0], B[i2], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[i2], B[0]))
            else:
                bm.faces.new((A[i], A[i2], B[i2], B[i]))
    return bm


def bm_extrude(poly, depth, bevel=0.0, segs=2):
    """Wielokat 2D (x, y) wyciagniety wzdluz Z (srodek grubosci w z=0)."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, -depth / 2)) for (x, y) in poly]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in res['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, depth), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=bevel, segments=segs,
                        affect='EDGES', profile=0.5, clamp_overlap=True)
    return bm


def bm_tube(points, radius=0.05, radii=None, res=6, bevel_res=3, smooth=True,
            cyclic=False, caps=True):
    """Rurka po krzywej (NURBS) -> bmesh. radii = mnozniki promienia w punktach."""
    cu = bpy.data.curves.new('tmp_tube', 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('NURBS' if smooth and len(points) > 2 else 'POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
        sp.points[i].radius = radii[i] if radii else 1.0
    if sp.type == 'NURBS':
        sp.use_endpoint_u = not cyclic
        sp.order_u = min(4, len(points))
        sp.resolution_u = res
    sp.use_cyclic_u = cyclic
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = caps
    ob = bpy.data.objects.new('tmp_tube', cu)
    me = tmp_eval(ob)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def bm_text(text, size=0.4, depth=0.03, bevel=0.006):
    cu = bpy.data.curves.new('tmp_txt', 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = depth
    cu.bevel_depth = bevel
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('tmp_txt', cu)
    me = tmp_eval(ob)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def bm_grid(nx, ny, sx, sy):
    """Plaszczyzna XZ (x szerokosc, z wysokosc), srodek gornej krawedzi w (0,0,0), w dol -Z."""
    bm = bmesh.new()
    rows = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            row.append(bm.verts.new(((i / nx - 0.5) * sx, 0.0, -j / ny * sy)))
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j + 1][i], rows[j + 1][i + 1], rows[j][i + 1]))
    return bm


def bm_map(bm, fn):
    for v in bm.verts:
        v.co = Vector(fn(v.co.copy()))
    return bm


def bm_transform(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    m = Matrix.LocRotScale(Vector(loc), Euler([r * D2R for r in rot]), Vector(scale))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return bm


def bm_merge(*bms):
    out = bmesh.new()
    for b in bms:
        me = bpy.data.meshes.new('tmp_merge')
        b.to_mesh(me)
        b.free()
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


def bm_solidify(bm, t):
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=t)
    return bm


# ---------------------------------------------------------------- objects
def make(bm, name, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
         parent=None, smooth=True, angle=40, rig=None):
    """bmesh -> obiekt. Wspolrzedne bm sa lokalne; loc/rot/scale ustawiaja go w swiecie
    (stan spoczynkowy). parent = nazwa jointu (gdy podano rig) albo obiekt."""
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
        if angle is not None:
            try:
                me.set_sharp_from_angle(angle=angle * D2R)
            except Exception:
                pass
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ob.matrix_world = Matrix.LocRotScale(Vector(loc), Euler([r * D2R for r in rot]), Vector(scale))
    ob.location = loc
    ob.rotation_euler = [r * D2R for r in rot]
    ob.scale = scale
    if parent is not None:
        if rig is not None and isinstance(parent, str):
            rig.add(ob, parent)
        else:
            parent_keep(ob, parent)
    return ob


def parent_keep(ob, parent, parent_world=None):
    pw = parent_world if parent_world is not None else parent.matrix_world.copy()
    ob.parent = parent
    ob.matrix_parent_inverse = pw.inverted()


def look_rot(direction, up=(0, 0, 1)):
    """Euler (stopnie) obracajacy os -Y na kierunek `direction`."""
    d = Vector(direction).normalized()
    q = (-d).to_track_quat('Y', 'Z')
    return [a / D2R for a in q.to_euler()]
