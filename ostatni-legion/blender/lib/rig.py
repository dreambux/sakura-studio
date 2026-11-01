"""Rig z pustych obiektow (empties) = 1:1 z Motor6D w Robloxie.

Kazdy joint ma osie rownolegle do osi postaci w pozycji spoczynkowej, wiec jego lokalny
obrot/przesuniecie to dokladnie Motor6D.Transform (C0 = przesuniecie od rodzica, C1 = 0).
Hierarchia R6: HumanoidRootPart -> Torso (RootJoint) -> Head / Left Arm / Right Arm /
Left Leg / Right Leg, plus dodatkowe jointy (bron, tarcza, peleryna, maszyny...).
"""
import math
import bpy
from mathutils import Vector, Matrix

from . import core
from . import materials as M
from .face import HEAD_UV_W


class Rig:
    def __init__(self, name):
        self.name = name
        self.joints = {}
        self.pivots = {}
        self.parents = {}
        self.order = []
        self.follow = {}       # joint -> joint ramienia, za ktorym "trzyma poziom" (pitch)
        self.attachments = {}  # name -> (joint, world pos)
        self.B = None
        self.model = bpy.data.objects.new('MODEL_' + name, None)
        core.link(self.model)

    def joint(self, name, parent, pivot, follow=None):
        e = bpy.data.objects.new(name, None)
        core.link(e)
        e.empty_display_size = 0.2
        e.empty_display_type = 'PLAIN_AXES'
        e.rotation_mode = 'XYZ'
        pv = Vector(pivot)
        pp = self.pivots[parent] if parent else Vector((0, 0, 0))
        e.parent = self.joints[parent] if parent else self.model
        e.location = pv - pp
        e['joint'] = 1
        self.joints[name] = e
        self.pivots[name] = pv
        self.parents[name] = parent
        self.order.append(name)
        if follow:
            self.follow[name] = follow
        return e

    def rest_world(self, name):
        return Matrix.Translation(self.pivots[name])

    def add(self, ob, joint):
        core.parent_keep(ob, self.joints[joint], self.rest_world(joint))
        ob['jnt'] = joint
        return ob

    def attach(self, name, joint, pos):
        self.attachments[name] = (joint, Vector(pos))
        e = bpy.data.objects.new('ATT_' + name, None)
        core.link(e)
        e.empty_display_size = 0.08
        e.location = pos
        core.parent_keep(e, self.joints[joint], self.rest_world(joint))
        e['noexport'] = 1
        e['att'] = name
        return e

    def att_obj(self, name):
        return bpy.data.objects['ATT_' + name]

    def meshes_of(self, joint):
        return [o for o in self.joints[joint].children if o.type == 'MESH']


# ------------------------------------------------------------------ R6 body
R6 = dict(tw=2.0, th=2.0, td=1.0, aw=1.0, al=2.0, ad=1.0, lw=1.0, ll=2.0, ld=1.0,
          hr=0.6, hh=1.2, bevel=0.1)


def head_mesh(r=0.6, h=1.2, fillet=0.24, segs=40):
    prof = [(0.0, -h / 2)]
    n = 6
    for i in range(n + 1):
        a = -math.pi / 2 + (math.pi / 2) * i / n
        prof.append((r - fillet + fillet * math.cos(a), -h / 2 + fillet + fillet * math.sin(a)))
    for i in range(n + 1):
        a = (math.pi / 2) * i / n
        prof.append((r - fillet + fillet * math.cos(a), h / 2 - fillet + fillet * math.sin(a)))
    prof.append((0.0, h / 2))
    return core.bm_lathe(prof, segs=segs)


def uv_face(ob, zc_local=0.0, w=HEAD_UV_W):
    """UV: przod glowy rzutowany planarnie, reszta w rog tekstury (sam kolor skory)."""
    me = ob.data
    uv = me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        front = p.normal.y < -0.15
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            if front:
                uv.data[li].uv = (0.5 + v.x / w, 0.5 + (v.z - zc_local) / w)
            else:
                uv.data[li].uv = (0.02, 0.02)


def build_r6(rig, skin_mat, face_mat, B=None, mats=None, head_bm=None):
    """Buduje cialo R6 i jointy. mats: torso/larm/rarm/lleg/rleg -> material (domyslnie skora)."""
    B = dict(R6, **(B or {}))
    rig.B = B
    mats = mats or {}
    tw, th, td = B['tw'], B['th'], B['td']
    aw, al, ad = B['aw'], B['al'], B['ad']
    lw, ll, ld = B['lw'], B['ll'], B['ld']
    bev = B['bevel']
    tz = ll + th / 2
    rig.joint('HumanoidRootPart', None, (0, 0, tz))
    rig.joint('Torso', 'HumanoidRootPart', (0, 0, tz))
    rig.joint('Head', 'Torso', (0, 0, ll + th))
    ax = tw / 2 + aw / 2
    sh = ll + th - 0.5
    rig.joint('Right Arm', 'Torso', (-ax, 0, sh))
    rig.joint('Left Arm', 'Torso', (ax, 0, sh))
    rig.joint('Right Leg', 'Torso', (-lw / 2, 0, ll))
    rig.joint('Left Leg', 'Torso', (lw / 2, 0, ll))
    B['tz'] = tz
    B['ax'] = ax
    B['sh'] = sh
    B['hand_z'] = sh - (al - 0.65)   # punkt chwytu (dol ramienia)
    B['head_c'] = ll + th + B['hh'] / 2

    core.make(core.bm_box(tw, td, th, bev, 3), 'Torso.body', mats.get('torso', skin_mat),
              loc=(0, 0, tz), parent='Torso', rig=rig)
    for side, sx, key in (('Right', -1, 'rarm'), ('Left', 1, 'larm')):
        core.make(core.bm_box(aw, ad, al, bev, 3), f'{side} Arm.body', mats.get(key, skin_mat),
                  loc=(sx * ax, 0, ll + th - al / 2), parent=f'{side} Arm', rig=rig)
    for side, sx, key in (('Right', -1, 'rleg'), ('Left', 1, 'lleg')):
        core.make(core.bm_box(lw, ld, ll, bev, 3), f'{side} Leg.body', mats.get(key, skin_mat),
                  loc=(sx * lw / 2, 0, ll / 2), parent=f'{side} Leg', rig=rig)
    hb = head_bm or head_mesh(B['hr'], B['hh'])
    head = core.make(hb, 'Head.body', face_mat, loc=(0, 0, B['head_c']), parent='Head', rig=rig,
                     angle=50)
    uv_face(head, 0.0)
    rig.hand = {
        'Right Arm': Vector((-ax, 0, B['hand_z'])),
        'Left Arm': Vector((ax, 0, B['hand_z'])),
    }
    return B
