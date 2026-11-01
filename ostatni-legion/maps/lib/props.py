"""Biblioteka greckich dekoracji (Blender). Jednostka = 1 stud.

Kazdy model: pusty obiekt 'P_<nazwa>' w (0,0,0) + czesci z materialami z jednej biblioteki tekstur
(maps/textures). UV liczone w skali swiata (tekstury maja ta sama gestosc na wszystkich modelach),
wiec wszystko wyglada spojnie.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler, noise

import importlib.util as _ilu
_core_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          'blender', 'lib', 'core.py')
_spec = _ilu.spec_from_file_location('ol_core', _core_path)
C = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(C)

D2R = math.pi / 180
TEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures')
TEX_DIR_JPG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures_jpg')


def tex_path(name):
    p = os.path.join(TEX_DIR, name + '.png')
    return p if os.path.exists(p) else os.path.join(TEX_DIR_JPG, name + '.jpg')

REGISTRY = {}      # nazwa -> (kategoria, funkcja, opis)
_MATS = {}
_CUR = {'root': None, 'name': None}


def prop(name, cat, desc=''):
    def deco(fn):
        REGISTRY[name] = (cat, fn, desc)
        return fn
    return deco


# ------------------------------------------------------------------ materialy
def _nodes(m):
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    return nt, b


def T(tex, rough=0.85, metal=0.0, nrm=1.0):
    """Material z tekstury biblioteki (kolor + normal)."""
    key = f'T_{tex}'
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(key)
    nt, b = _nodes(m)
    ic = nt.nodes.new('ShaderNodeTexImage')
    ic.image = bpy.data.images.load(tex_path(f'{tex}_col'), check_existing=True)
    nt.links.new(ic.outputs['Color'], b.inputs['Base Color'])
    inm = nt.nodes.new('ShaderNodeTexImage')
    inm.image = bpy.data.images.load(tex_path(f'{tex}_nrm'), check_existing=True)
    inm.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = nrm
    nt.links.new(inm.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m['tex'] = tex
    _MATS[key] = m
    return m


def F(name, rgb, rough=0.6, metal=0.0, emit=0.0):
    """Material jednolity (kolor 0-255)."""
    key = f'F_{name}'
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(key)
    nt, b = _nodes(m)
    c = tuple((x / 255.0) ** 2.2 for x in rgb) + (1.0,)
    b.inputs['Base Color'].default_value = c
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = c
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = c
    _MATS[key] = m
    return m


# wspolne kolory (jedna paleta dla wszystkiego)
def GOLD():
    return F('gold', (214, 168, 74), 0.32, 1.0)


def BRONZE():
    return T('bronze', 0.4, 0.85)


def FIRE():
    return F('fire', (255, 140, 40), 0.5, 0.0, 12.0)


def FIRE_CORE():
    return F('fire_core', (255, 220, 120), 0.5, 0.0, 20.0)


def GLOW(name, rgb, s=6.0):
    return F('glow_' + name, rgb, 0.5, 0.0, s)


# ------------------------------------------------------------------ UV w skali swiata
def uv_box(ob, tile=4.0):
    me = ob.data
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    mw = ob.matrix_world
    rot = mw.to_3x3()
    for p in me.polygons:
        n = (rot @ p.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uv.data[li].uv = (u / tile, v / tile)


def uv_cyl(ob, tile=4.0, axis='Z'):
    me = ob.data
    uv = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    mw = ob.matrix_world
    c = ob.matrix_world.translation
    for p in me.polygons:
        lis = list(p.loop_indices)
        cos = [mw @ me.vertices[me.loops[li].vertex_index].co for li in lis]
        angs = []
        for co in cos:
            d = co - c
            angs.append(math.atan2(d.y, d.x))
        # unikaj szwu: dopasuj katy do pierwszego
        a0 = angs[0]
        for i, a in enumerate(angs):
            while a - a0 > math.pi:
                a -= 2 * math.pi
            while a - a0 < -math.pi:
                a += 2 * math.pi
            angs[i] = a
        for li, co, a in zip(lis, cos, angs):
            r = max(0.3, math.hypot(co.x - c.x, co.y - c.y))
            uv.data[li].uv = (a * r / tile, co.z / tile)


# ------------------------------------------------------------------ budowanie
def begin(name):
    root = bpy.data.objects.new('P_' + name, None)
    C.link(root)
    root.empty_display_size = 1.0
    root['prop'] = name
    _CUR['root'] = root
    _CUR['name'] = name
    return root


def add(bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), uv='box', tile=4.0, smooth=True, angle=40,
        name='part'):
    ob = C.make(bm, f"{_CUR['name']}.{name}", mat, loc=loc, rot=rot, scale=scale, smooth=smooth, angle=angle)
    # matrix_world ustawione w make() - bez view_layer.update() (przy tysiacach obiektow to bylo O(n^2))
    ob.matrix_world = Matrix.LocRotScale(Vector(loc), Euler([r * D2R for r in rot]), Vector(scale))
    if uv == 'box':
        uv_box(ob, tile)
    elif uv == 'cyl':
        uv_cyl(ob, tile)
    ob.parent = _CUR['root']
    ob['pmat'] = mat.name
    return ob


def marker(kind, loc, **data):
    """Punkt efektu dla Robloxa (Fire, PointLight, ParticleEmitter...)."""
    e = bpy.data.objects.new(f"{_CUR['name']}.FX_{kind}", None)
    C.link(e)
    e.location = loc
    e.empty_display_size = 0.4
    e.parent = _CUR['root']
    e['fx'] = kind
    for k, v in data.items():
        e[k] = v
    return e


# ------------------------------------------------------------------ geometria pomocnicza
def rock_bm(r=1.0, seed=0, sub=2, rough=0.35, flat=0.35, squash=(1, 1, 0.75)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    off = Vector((seed * 13.1, seed * 7.7, seed * 3.3))
    for v in bm.verts:
        p = v.co.normalized()
        d = noise.fractal(p * 1.3 + off, 0.6, 2.0, 3) * rough + noise.noise(p * 3.1 + off) * rough * 0.4
        v.co = v.co * (1 + d)
        v.co.x *= squash[0]
        v.co.y *= squash[1]
        v.co.z *= squash[2]
        if v.co.z < -r * flat:
            v.co.z = -r * flat + (v.co.z + r * flat) * 0.15
    return bm


def blob_bm(r=1.0, seed=0, sub=2, amt=0.22, squash=(1, 1, 0.85)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    off = Vector((seed * 5.3, seed * 2.9, seed * 8.1))
    for v in bm.verts:
        p = v.co.normalized()
        d = noise.fractal(p * 2.0 + off, 0.5, 2.0, 3) * amt
        v.co = v.co * (1 + d)
        v.co.x *= squash[0]
        v.co.y *= squash[1]
        v.co.z *= squash[2]
    return bm


def fluted_column_bm(r=0.9, h=10.0, flutes=16, taper=0.85, segs=64, rings=8):
    bm = bmesh.new()
    verts = []
    for j in range(rings + 1):
        z = h * j / rings
        rr = r * (1 - (1 - taper) * j / rings)
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            fl = rr * (1 - 0.11 * abs(math.cos(a * flutes / 2)) ** 0.6)
            ring.append(bm.verts.new((fl * math.cos(a), fl * math.sin(a), z)))
        verts.append(ring)
    for j in range(rings):
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((verts[j][i], verts[j][i2], verts[j + 1][i2], verts[j + 1][i]))
    bm.faces.new(verts[-1])
    bm.faces.new(list(reversed(verts[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def recalc(bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def box(sx, sy, sz, bev=0.06):
    return C.bm_box(sx, sy, sz, bev, 2)


def cyl(r, h, segs=16, r2=None, bev=0.0):
    return C.bm_cyl(r, h, segs, r2=r2, bevel=bev)


def tube(pts, r, radii=None, res=6):
    return C.bm_tube(pts, r, radii=radii, res=res)


def lathe(prof, segs=32):
    return recalc(C.bm_lathe(prof, segs=segs))
