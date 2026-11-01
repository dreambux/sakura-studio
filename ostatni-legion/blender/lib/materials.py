"""Wspolna biblioteka materialow PBR dla wszystkich jednostek (jeden styl).

Kolor bazowy, metalicznosc i chropowatosc sa zwyklymi wartosciami (eksportuja sie do GLB).
Do renderow dochodzi delikatny bump z szumu (eksporter go pomija).
"""
import bpy

# name: (kolor liniowy RGB, metallic, roughness, bump, skala szumu, extra)
LIB = {
    'gold':          ((1.00, 0.66, 0.24), 1.0, 0.24, 0.05, 60, {}),
    'gold_dark':     ((0.62, 0.38, 0.12), 1.0, 0.34, 0.08, 60, {}),
    'bronze':        ((0.74, 0.42, 0.18), 1.0, 0.32, 0.10, 40, {}),
    'bronze_dark':   ((0.40, 0.22, 0.09), 1.0, 0.42, 0.12, 40, {}),
    'silver':        ((0.88, 0.89, 0.92), 1.0, 0.16, 0.03, 60, {}),
    'brass':         ((0.60, 0.44, 0.17), 1.0, 0.40, 0.10, 50, {}),
    'blue_paint':    ((0.012, 0.035, 0.15), 0.0, 0.40, 0.04, 40, {'coat': 0.35}),
    'steel':         ((0.70, 0.71, 0.74), 1.0, 0.26, 0.06, 60, {}),
    'steel_dark':    ((0.28, 0.29, 0.31), 1.0, 0.38, 0.10, 60, {}),
    'iron':          ((0.20, 0.20, 0.21), 1.0, 0.55, 0.15, 30, {}),
    'red_cloth':     ((0.42, 0.025, 0.025), 0.0, 0.82, 0.15, 90, {'sheen': 0.6}),
    'red_dark':      ((0.22, 0.015, 0.015), 0.0, 0.85, 0.15, 90, {'sheen': 0.5}),
    'red_paint':     ((0.55, 0.035, 0.03), 0.0, 0.42, 0.04, 40, {'coat': 0.3}),
    'crest':         ((0.50, 0.012, 0.012), 0.0, 0.62, 0.30, 200, {'sheen': 0.15}),
    'crest_dark':    ((0.26, 0.006, 0.008), 0.0, 0.72, 0.30, 200, {'sheen': 0.15}),
    'leather':       ((0.26, 0.12, 0.05), 0.0, 0.55, 0.20, 50, {}),
    'leather_dark':  ((0.10, 0.05, 0.025), 0.0, 0.60, 0.20, 50, {}),
    'leather_light': ((0.48, 0.27, 0.11), 0.0, 0.58, 0.20, 50, {}),
    'bandage':       ((0.85, 0.80, 0.68), 0.0, 0.90, 0.20, 120, {}),
    'linen':         ((0.86, 0.83, 0.74), 0.0, 0.85, 0.12, 120, {'sheen': 0.4}),
    'white_cloth':   ((0.90, 0.89, 0.85), 0.0, 0.82, 0.10, 120, {'sheen': 0.4}),
    'wood':          ((0.30, 0.16, 0.07), 0.0, 0.62, 0.25, 25, {}),
    'bark':          ((0.16, 0.10, 0.06), 0.0, 0.85, 0.40, 30, {}),
    'wood_dark':     ((0.14, 0.08, 0.04), 0.0, 0.65, 0.25, 25, {}),
    'wood_light':    ((0.52, 0.32, 0.15), 0.0, 0.60, 0.25, 25, {}),
    'rope':          ((0.55, 0.43, 0.24), 0.0, 0.92, 0.35, 150, {}),
    'black':         ((0.015, 0.015, 0.015), 0.0, 0.50, 0.0, 10, {}),
    'pedestal':      ((0.86, 0.86, 0.87), 0.0, 0.50, 0.0, 10, {}),
    'purple_cloth':  ((0.17, 0.035, 0.26), 0.0, 0.80, 0.12, 90, {'sheen': 0.7}),
    'violet_cloth':  ((0.42, 0.20, 0.62), 0.0, 0.78, 0.12, 90, {'sheen': 0.7}),
    'blue_cloth':    ((0.03, 0.12, 0.38), 0.0, 0.80, 0.12, 90, {'sheen': 0.6}),
    'teal_cloth':    ((0.02, 0.26, 0.30), 0.0, 0.80, 0.12, 90, {'sheen': 0.6}),
    'sky_cloth':     ((0.25, 0.55, 0.80), 0.0, 0.80, 0.12, 90, {'sheen': 0.6}),
    'scale_green':   ((0.05, 0.22, 0.10), 0.3, 0.35, 0.35, 70, {}),
    'emerald':       ((0.02, 0.38, 0.16), 0.0, 0.25, 0.0, 10, {'coat': 0.8}),
    'snake':         ((0.11, 0.33, 0.08), 0.0, 0.40, 0.30, 90, {}),
    'snake_dark':    ((0.03, 0.12, 0.04), 0.0, 0.45, 0.30, 90, {}),
    'snake_belly':   ((0.70, 0.60, 0.28), 0.0, 0.50, 0.20, 90, {}),
    'fur':           ((0.24, 0.12, 0.055), 0.0, 0.95, 0.35, 160, {'sheen': 0.6}),
    'fur_dark':      ((0.09, 0.045, 0.025), 0.0, 0.95, 0.35, 160, {'sheen': 0.6}),
    'horn':          ((0.82, 0.74, 0.55), 0.0, 0.40, 0.10, 30, {}),
    'hoof':          ((0.05, 0.04, 0.035), 0.0, 0.45, 0.05, 30, {}),
    'hair_dark':     ((0.03, 0.018, 0.012), 0.0, 0.55, 0.30, 160, {'sheen': 0.6}),
    'hair_white':    ((0.80, 0.80, 0.78), 0.0, 0.65, 0.30, 160, {'sheen': 0.6}),
    'marble':        ((0.82, 0.80, 0.76), 0.0, 0.35, 0.05, 20, {}),
    'laurel':        ((0.10, 0.28, 0.05), 0.0, 0.55, 0.10, 40, {}),
    'pink':          ((0.65, 0.20, 0.22), 0.0, 0.5, 0.0, 10, {}),
}

# swiecace (emisja)
GLOW = {
    'glow_lightning': ((0.35, 0.62, 1.0), 4.0),
    'glow_gold':      ((1.0, 0.72, 0.25), 6.0),
    'glow_violet':    ((0.45, 0.12, 0.95), 3.0),
    'glow_green':     ((0.25, 0.9, 0.2), 3.0),
    'glow_yellow':    ((1.0, 0.75, 0.10), 3.5),
    'glow_red':       ((1.0, 0.15, 0.05), 6.0),
    'glow_fire':      ((1.0, 0.45, 0.08), 8.0),
}

_cache = {}


def _principled(m):
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def _setup_nodes(m):
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m.node_tree


def _bump(m, strength, scale):
    if strength <= 0:
        return
    nt = m.node_tree
    bsdf = _principled(m)
    tex = nt.nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = 6.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = 0.02
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])


def get(name):
    if name in _cache:
        return _cache[name]
    if name in GLOW:
        return glow(name)
    col, met, rough, bump, scale, extra = LIB[name]
    return pbr(name, col, met, rough, bump, scale, **extra)


def pbr(name, col, met=0.0, rough=0.5, bump=0.0, scale=40, sheen=0.0, coat=0.0):
    if name in _cache:
        return _cache[name]
    m = bpy.data.materials.new(name)
    _setup_nodes(m)
    b = _principled(m)
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Metallic'].default_value = met
    b.inputs['Roughness'].default_value = rough
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    m.diffuse_color = (*col, 1.0)
    _bump(m, bump, scale)
    _cache[name] = m
    return m


def skin(name, col):
    return pbr(name, col, 0.0, 0.48, 0.03, 80, sheen=0.2)


def glow(name, col=None, strength=None):
    if name in _cache:
        return _cache[name]
    if col is None:
        col, strength = GLOW[name]
    m = bpy.data.materials.new(name)
    _setup_nodes(m)
    b = _principled(m)
    b.inputs['Base Color'].default_value = (*col, 1.0)
    b.inputs['Emission Color'].default_value = (*col, 1.0)
    b.inputs['Emission Strength'].default_value = strength
    b.inputs['Roughness'].default_value = 0.4
    m.diffuse_color = (*col, 1.0)
    _cache[name] = m
    return m


def textured(name, image_path, rough=0.5, sheen=0.2):
    """Material z tekstura (glowa z twarza)."""
    if name in _cache:
        return _cache[name]
    m = bpy.data.materials.new(name)
    nt = _setup_nodes(m)
    b = _principled(m)
    img = bpy.data.images.load(image_path)
    img.pack()
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    _cache[name] = m
    return m


def fx(name, col, strength=4.0, alpha=1.0):
    """Material efektow (tylko render): emisja + przezroczystosc z atrybutu 'fade'."""
    key = 'fx_' + name
    if key in _cache:
        return _cache[key]
    m = bpy.data.materials.new(key)
    nt = _setup_nodes(m)
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*col, 1.0)
    em.inputs['Strength'].default_value = strength
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    attr = nt.nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'fade'
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = alpha
    nt.links.new(attr.outputs['Fac'], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m['fx'] = 1
    _cache[key] = m
    return m


def clear_cache():
    _cache.clear()
