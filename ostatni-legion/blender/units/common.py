"""Wspolne elementy jednostek: twarz, cialo, tarcze, drzewce."""
import math
from mathutils import Vector

from lib import core as C
from lib import materials as M
from lib import rig as R
from lib import kit as K
from lib.face import make_face

D2R = math.pi / 180


def body(name, out_dir, skin_col, face_kw=None, B=None, mats=None, head_mat_col=None):
    """Rig + cialo R6 + glowa z twarza. Zwraca rig."""
    rig = R.Rig(name)
    face_path = f'{out_dir}/{name}_face.png'
    make_face(face_path, head_mat_col or skin_col, **(face_kw or {}))
    skin = M.skin('skin_' + name, skin_col)
    face_mat = M.textured('face_' + name, face_path)
    R.build_r6(rig, skin, face_mat, B=B, mats={k: (M.get(v) if isinstance(v, str) else v)
                                                for k, v in (mats or {}).items()})
    rig.skin = skin
    return rig


def shaft(rig, joint, name, mat, y0, y1, r, x, z, segs=12, bevel=0.0):
    """Drzewce wzdluz osi Y (od y0 do y1) w punkcie (x, z)."""
    L = abs(y1 - y0)
    return K.mk(rig, C.bm_cyl(r, L, segs, bevel=bevel), name, mat, joint,
                (x, (y0 + y1) / 2, z), rot=(90, 0, 0))


def curved_shield_surface(R_):
    def S(x, z, off=0.0):
        return Vector((x, R_ - math.sqrt(max(1e-6, R_ * R_ - x * x)) - off, z))

    def tilt(x):
        return math.degrees(math.atan2(x, math.sqrt(max(1e-6, R_ * R_ - x * x))))
    return S, tilt


def rounded_rect(w, h, r, n=4):
    pts = []
    corners = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
               (w / 2 - r, -h / 2 + r, 270)]
    for cx, cz, a0 in corners:
        for i in range(n + 1):
            a = (a0 + 90 * i / n) * D2R
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def flat_on_shield(rig, joint, center, S, tilt, bm, name, mat, x, z, off=0.07, extra_rot=0.0):
    """Plaski element (bm w plaszczyznie XY, grubosc wzdluz Z) polozony na wygietej tarczy."""
    C.bm_transform(bm, rot=(0, 0, extra_rot))
    C.bm_transform(bm, rot=(90, 0, 0))
    p = Vector(center) + S(x, z, off)
    return K.mk(rig, bm, name, mat, joint, tuple(p), rot=(0, 0, tilt(x)))


def bolt_poly(scale=1.0):
    pts = [(0.00, 0.50), (0.10, 0.50), (0.02, 0.12), (0.12, 0.14), (-0.04, -0.50), (0.00, -0.06),
           (-0.10, -0.08)]
    return [(x * scale, y * scale) for x, y in pts]


def wing_poly(scale=1.0, flip=False):
    pts = [(0.00, 0.10), (0.20, 0.24), (0.42, 0.32), (0.62, 0.30), (0.52, 0.20), (0.66, 0.16),
           (0.54, 0.07), (0.64, 0.00), (0.50, -0.05), (0.56, -0.13), (0.38, -0.12), (0.18, -0.08),
           (0.00, -0.06)]
    s = -1 if flip else 1
    out = [(s * x * scale, y * scale) for x, y in pts]
    return out[::-1] if flip else out


def fx_template(parts, key):
    """parts = [(bm, material), ...] -> jeden obiekt-wzorzec pocisku (os -Y = lot)."""
    mats = []
    for i, (bm, mat) in enumerate(parts):
        for f in bm.faces:
            f.material_index = i
        mats.append(M.get(mat) if isinstance(mat, str) else mat)
    bm = C.bm_merge(*[p[0] for p in parts])
    ob = C.make(bm, 'FXT_' + key, None)
    for m in mats:
        ob.data.materials.append(m)
    ob['noexport'] = 1
    ob['fx_template'] = key
    ob.hide_render = True
    return ob


def scale_subtree(rig, joints, G, s):
    """Skaluje czesci i pivoty podanych jointow wzgledem punktu G (stan spoczynkowy, przed animacja)."""
    import bpy
    from mathutils import Matrix
    bpy.context.view_layer.update()
    Gv = Vector(G)
    Mx = Matrix.Translation(Gv) @ Matrix.Scale(s, 4) @ Matrix.Translation(-Gv)
    obs = [o for o in bpy.data.objects if o.get('jnt') in joints]
    atts = [o for o in bpy.data.objects if o.get('att') and rig.attachments[o['att']][0] in joints]
    new_world = {o.name: Mx @ o.matrix_world.copy() for o in obs + atts}
    for j in joints:
        rig.pivots[j] = Gv + (rig.pivots[j] - Gv) * s
    for j in joints:
        par = rig.parents[j]
        rig.joints[j].location = rig.pivots[j] - (rig.pivots[par] if par else Vector((0, 0, 0)))
    for o in obs + atts:
        j = o['jnt'] if o.get('jnt') else rig.attachments[o['att']][0]
        o.matrix_parent_inverse = Matrix.Translation(rig.pivots[j]).inverted()
        o.matrix_basis = new_world[o.name]
    for a, (j, p) in list(rig.attachments.items()):
        if j in joints:
            rig.attachments[a] = (j, Gv + (p - Gv) * s)
    bpy.context.view_layer.update()
