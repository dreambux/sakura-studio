"""Rzezba organiczna: szkielet z promieniami -> modyfikator Skin + Subdivision -> gladka bryla.

Uzywane do zwierzat, posagow i postaci (Cerber, lwy, konie, ludzie), zeby nie skladac ich z pudelek.
"""
import math

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

from .props import C

D2R = math.pi / 180


def apply_mods(bm, mods):
    """bmesh -> tymczasowy obiekt z modyfikatorami -> nowy bmesh (modyfikatory zastosowane)."""
    me = bpy.data.meshes.new('tmp_mods')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('tmp_mods', me)
    for kind, kw in mods:
        m = ob.modifiers.new(kind.lower(), kind)
        for k, v in kw.items():
            setattr(m, k, v)
    out = C.tmp_eval(ob)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bm2 = bmesh.new()
    bm2.from_mesh(out)
    bpy.data.meshes.remove(out)
    return bm2


def subd(bm, levels=2, crease=False):
    return apply_mods(bm, [('SUBSURF', dict(levels=levels, render_levels=levels))])


class Skel:
    """Szkielet do modyfikatora Skin. Wezly: pozycja + promien (albo (rx, ry))."""

    def __init__(self):
        self.p = []
        self.r = []
        self.e = []

    def n(self, p, r):
        self.p.append(Vector(p))
        self.r.append(r if isinstance(r, (tuple, list)) else (r, r))
        return len(self.p) - 1

    def e_(self, a, b):
        self.e.append((a, b))

    def chain(self, pts, start=None):
        """pts = [(p, r), ...]; laczy po kolei (i z wezlem start). Zwraca liste id."""
        ids = []
        prev = start
        for p, r in pts:
            i = self.n(p, r)
            if prev is not None:
                self.e_(prev, i)
            prev = i
            ids.append(i)
        return ids

    def cap_leaves(self, ext=0.75, shrink=0.6):
        """Skin konczy galaz plasko w wezle - dodaj 'czubek', zeby konce (glowy, lapy) byly pelne i okragle."""
        deg = [0] * len(self.p)
        nb = [None] * len(self.p)
        for a, b in self.e:
            deg[a] += 1
            deg[b] += 1
            nb[a] = b
            nb[b] = a
        for i in range(len(deg)):
            if deg[i] == 1:
                d = (self.p[i] - self.p[nb[i]])
                if d.length < 1e-6:
                    continue
                r = self.r[i][0]
                j = self.n(self.p[i] + d.normalized() * r * ext, (r * shrink, r * shrink))
                self.e_(i, j)

    def build(self, sub=2, branch_smooth=0.0, smooth_iter=0, xform=None, cap=True):
        if cap and not getattr(self, '_capped', False):
            self.cap_leaves()
            self._capped = True
        bm = bmesh.new()
        lay = bm.verts.layers.skin.verify()
        vs = [bm.verts.new(p) for p in self.p]
        for a, b in self.e:
            bm.edges.new((vs[a], vs[b]))
        for v, r in zip(vs, self.r):
            v[lay].radius = r
        vs[0][lay].use_root = True
        mods = [('SKIN', dict(branch_smoothing=branch_smooth, use_smooth_shade=True))]
        if smooth_iter:
            mods.append(('SMOOTH', dict(iterations=smooth_iter, factor=0.5)))
        if sub:
            mods.append(('SUBSURF', dict(levels=sub, render_levels=sub)))
        bm = apply_mods(bm, mods)
        if xform is not None:
            bmesh.ops.transform(bm, matrix=xform, verts=bm.verts)
        return bm


def xf(loc=(0, 0, 0), rot=(0, 0, 0), s=1.0):
    sc = Vector((s, s, s)) if not isinstance(s, (tuple, list)) else Vector(s)
    return Matrix.LocRotScale(Vector(loc), Euler([r * D2R for r in rot]), sc)


def tx(m, p):
    return tuple(m @ Vector(p))


def cone(r, h, segs=8):
    """Stozek od podstawy w z=0 do czubka w z=h."""
    return C.bm_cyl(r, h, segs, r2=0.0)


def aim_rot(d):
    """Euler (stopnie) obracajacy os +Z na kierunek d."""
    q = Vector(d).normalized().to_track_quat('Z', 'Y')
    return tuple(math.degrees(a) for a in q.to_euler())


def bm_at(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), m=None):
    M = Matrix.LocRotScale(Vector(loc), Euler([r * D2R for r in rot]), Vector(scale))
    if m is not None:
        M = m @ M
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm


def merge(bms):
    return C.bm_merge(*bms)


def param_shell(fn, nu, nv, mask=None, thick=0.0, closed_u=True):
    """Powierzchnia parametryczna fn(u, v)->(x,y,z), u,v w [0,1]. mask(u,v)->False usuwa scianke.
    thick>0 -> solidify (np. helm)."""
    bm = bmesh.new()
    nu_v = nu if closed_u else nu + 1
    grid = [[bm.verts.new(fn(i / nu, j / nv)) for i in range(nu_v)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu if closed_u else i + 1
            uc, vc = (i + 0.5) / nu, (j + 0.5) / nv
            if mask is not None and not mask(uc, vc):
                continue
            bm.faces.new((grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]))
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if thick:
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return bm
