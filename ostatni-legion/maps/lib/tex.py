"""Biblioteka bezszwowych tekstur (Blender).

Blender wypieka proceduralne pola (Noise / Voronoi 4D zmapowane na torus -> idealnie
powtarzalne), a nastepnie skladamy z nich kolor (sRGB) i mape normalnych (OpenGL, jak glTF).
Wyniki: maps/textures/<nazwa>_col.png, <nazwa>_nrm.png
"""
import math
import os
import random

import bpy
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TAU = 2 * math.pi
_FIELDS = {}
_STATE = {}


# ------------------------------------------------------------------ wypiekanie pol w Blenderze
def _setup(size):
    if _STATE.get('size') == size and _STATE.get('ob') and _STATE['ob'].name in bpy.data.objects:
        return
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 1
    sc.cycles.bake_type = 'EMIT'
    me = bpy.data.meshes.new('bakeplane')
    me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    ob = bpy.data.objects.new('BAKEPLANE', me)
    sc.collection.objects.link(ob)
    mat = bpy.data.materials.new('bakemat')
    try:
        mat.use_nodes = True
    except Exception:
        pass
    me.materials.append(mat)
    img = bpy.data.images.new('bakeimg', size, size, float_buffer=True, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    _STATE.update(size=size, ob=ob, mat=mat, img=img)


def _torus(nt, uvsep, su, sv, off):
    """(Vector, W) na torusie: X=Ru cos(2pi u), Y=Ru sin, Z=Rv cos(2pi v), W=Rv sin."""
    def m(op, a, b=None):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                nt.links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]
    au = m('MULTIPLY', uvsep.outputs['X'], TAU)
    av = m('MULTIPLY', uvsep.outputs['Y'], TAU)
    ru, rv = su / TAU, sv / TAU
    x = m('ADD', m('MULTIPLY', m('COSINE', au), ru), off[0])
    y = m('ADD', m('MULTIPLY', m('SINE', au), ru), off[1])
    z = m('ADD', m('MULTIPLY', m('COSINE', av), rv), off[2])
    w = m('ADD', m('MULTIPLY', m('SINE', av), rv), off[3])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(x, comb.inputs[0])
    nt.links.new(y, comb.inputs[1])
    nt.links.new(z, comb.inputs[2])
    return comb.outputs[0], w


def field(kind, size=1024, scale=4.0, aniso=1.0, seed=0, detail=4.0, rough=0.5, distortion=0.0,
          feature='F1', out='Distance', randomness=1.0):
    """Wypiekane bezszwowe pole (numpy float32, wiersz 0 = v=0). Cache po parametrach."""
    key = (kind, size, scale, aniso, seed, detail, rough, distortion, feature, out, randomness)
    if key in _FIELDS:
        return _FIELDS[key]
    _setup(size)
    st = _STATE
    nt = st['mat'].node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['UV'], sep.inputs[0])
    rnd = random.Random(seed * 7919 + 17)
    off = [rnd.uniform(-50, 50) for _ in range(4)]
    vec, w = _torus(nt, sep, scale, scale * aniso, off)
    if kind == 'noise':
        t = nt.nodes.new('ShaderNodeTexNoise')
        t.noise_dimensions = '4D'
        t.inputs['Scale'].default_value = 1.0
        t.inputs['Detail'].default_value = detail
        t.inputs['Roughness'].default_value = rough
        t.inputs['Distortion'].default_value = distortion
        sock = t.outputs['Fac']
    else:
        t = nt.nodes.new('ShaderNodeTexVoronoi')
        t.voronoi_dimensions = '4D'
        t.feature = feature
        t.inputs['Scale'].default_value = 1.0
        t.inputs['Randomness'].default_value = randomness
        sock = t.outputs[out]
    nt.links.new(vec, t.inputs['Vector'])
    nt.links.new(w, t.inputs['W'])
    em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(sock, em.inputs['Color'])
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], o.inputs['Surface'])
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = st['img']
    nt.nodes.active = img
    ob = st['ob']
    for o2 in bpy.context.scene.objects:
        o2.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type='EMIT', margin=0)
    a = np.array(st['img'].pixels[:], dtype=np.float32).reshape(size, size, 4)[:, :, 0].copy()
    _FIELDS[key] = a
    return a


# ------------------------------------------------------------------ pomocnicze numpy
def norm(a):
    lo, hi = np.percentile(a, 1), np.percentile(a, 99)
    return np.clip((a - lo) / max(1e-6, hi - lo), 0, 1)


def ramp(a, stops):
    """stops = [(pozycja, (r,g,b) 0-255)] -> HxWx3 float 0-1."""
    xs = np.array([s[0] for s in stops])
    cs = np.array([s[1] for s in stops], dtype=np.float32) / 255.0
    out = np.zeros(a.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(a, xs, cs[:, c])
    return out


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    t = t[..., None] if t.ndim == 2 else t
    return a * (1 - t) + b * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def uv_grid(size):
    v, u = np.mgrid[0:size, 0:size].astype(np.float32) / size
    return u, v


def cells(size, cols, rows, offset=0.5, seed=0):
    """Prostokatne komorki (bezszwowe): zwraca (fx, fy, id_rand, cw, ch) - pozycja w komorce 0-1,
    losowa wartosc komorki, rozmiar komorki w px."""
    u, v = uv_grid(size)
    cv = v * rows
    ry = np.floor(cv)
    cu = u * cols + (ry % 2) * offset
    rx = np.floor(cu) % cols
    fx, fy = cu - np.floor(cu), cv - ry
    rng = np.random.default_rng(seed)
    table = rng.random((rows + 1, cols + 1)).astype(np.float32)
    rid = table[ry.astype(int) % rows, rx.astype(int)]
    return fx, fy, rid, size / cols, size / rows


def edge_dist(fx, fy, cw, ch):
    return np.minimum(np.minimum(fx, 1 - fx) * cw, np.minimum(fy, 1 - fy) * ch)


def normal_from_height(h, strength=4.0):
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * strength
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * strength
    n = np.stack([-dx, -dy, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, col, height, strength, out_dir, size_out=None):
    os.makedirs(out_dir, exist_ok=True)
    col = np.clip(col, 0, 1)
    im = Image.fromarray((np.flipud(col) * 255).astype(np.uint8), 'RGB')
    nrm = normal_from_height(height.astype(np.float32), strength)
    nm = Image.fromarray((np.flipud(nrm) * 255).astype(np.uint8), 'RGB')
    if size_out and size_out != col.shape[0]:
        im = im.resize((size_out, size_out), Image.LANCZOS)
        nm = nm.resize((size_out, size_out), Image.LANCZOS)
    pc = os.path.join(out_dir, f'{name}_col.png')
    pn = os.path.join(out_dir, f'{name}_nrm.png')
    im.save(pc)
    nm.save(pn)
    return pc, pn


def strokes(size, n, palette, dirfield, length=(6, 14), width=(2, 4), seed=1, base=None, curl=0.6):
    """Pociagniecia pedzla (trawa w stylu recznie malowanym) - bezszwowe (rysowane z zawinieciem).
    Zwraca (kolor HxWx3 0-1, wysokosc HxW)."""
    rng = random.Random(seed)
    img = Image.fromarray(((base if base is not None else np.zeros((size, size, 3))) * 255).astype(np.uint8), 'RGB')
    hgt = Image.new('L', (size, size), 0)
    dc = ImageDraw.Draw(img)
    dh = ImageDraw.Draw(hgt)
    for _ in range(n):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        ang = dirfield[int(y) % size, int(x) % size] * TAU * 1.5 + rng.uniform(-0.5, 0.5)
        L = rng.uniform(*length)
        wdt = rng.randint(*width)
        col = palette[rng.randrange(len(palette))]
        jit = rng.uniform(-18, 18)
        col = tuple(int(max(0, min(255, c + jit))) for c in col)
        pts = []
        a = ang
        px, py = x, y
        for k in range(4):
            pts.append((px, py))
            a += rng.uniform(-curl, curl) * 0.4
            px += math.cos(a) * L / 3
            py += math.sin(a) * L / 3
        hv = rng.randint(140, 255)
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                p2 = [(p[0] + ox, p[1] + oy) for p in pts]
                if max(p[0] for p in p2) < -2 or min(p[0] for p in p2) > size + 2:
                    continue
                if max(p[1] for p in p2) < -2 or min(p[1] for p in p2) > size + 2:
                    continue
                dc.line(p2, fill=col, width=wdt, joint='curve')
                dh.line(p2, fill=hv, width=max(1, wdt - 1), joint='curve')
    c = np.asarray(img, np.float32) / 255.0
    h = np.asarray(hgt.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255.0
    return c, h


