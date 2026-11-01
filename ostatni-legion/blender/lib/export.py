"""Eksport: GLB (model w pozie spoczynkowej) + dane klatek dla Robloxa (Luau + JSON).

Osie: Roblox (x, y, z) = Blender (-x, z, y). Postac w Blenderze patrzy w -Y, w Robloxie w -Z
(LookVector). GLB jest obrocony o 180 st. wokol pionu, wiec importer (glTF +Y w gore)
daje od razu dobra orientacje.
"""
import json
import math
import os
import bpy
import bmesh
from mathutils import Matrix, Vector

ROT180 = Matrix.Rotation(math.pi, 4, 'Z')


def to_rbx(v):
    return (-v[0], v[2], v[1])


def q_to_rbx(q):
    # (x, y, z, w) w osiach Robloxa
    return (-q.x, q.z, q.y, q.w)


def _r(x, n=4):
    v = round(x, n)
    if v == 0:
        v = 0.0
    return v


def export_glb(rig, path, tri_limit=19000):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    groups = {}
    for ob in bpy.context.scene.objects:
        if ob.type not in ('MESH', 'CURVE') or ob.get('noexport') or 'jnt' not in ob:
            continue
        mat = ob.active_material
        if mat is None or mat.get('fx'):
            continue
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        me.transform(ob.matrix_world)
        groups.setdefault((ob['jnt'], mat.name), []).append(me)

    coll = bpy.data.collections.new('EXPORT')
    bpy.context.scene.collection.children.link(coll)
    objs = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    report = []
    for (jn, mname), mes in sorted(groups.items()):
        bm = bmesh.new()
        for me in mes:
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        for f in bm.faces:
            f.material_index = 0
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        tris = len(bm.faces)
        for v in bm.verts:
            mn = Vector(map(min, mn, v.co))
            mx = Vector(map(max, mx, v.co))
        out = bpy.data.meshes.new(f'{jn}__{mname}')
        bm.to_mesh(out)
        bm.free()
        out.materials.clear()
        out.materials.append(bpy.data.materials[mname])
        out.transform(ROT180)
        ob = bpy.data.objects.new(f'{jn}__{mname}', out)
        coll.objects.link(ob)
        objs.append(ob)
        report.append((ob.name, tris))
        if tris > tri_limit:
            print(f'UWAGA: {ob.name} ma {tris} trojkatow (> {tri_limit})')

    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
              export_yup=True, export_materials='EXPORT', export_animations=False,
              export_extras=False)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_extras', None)
        bpy.ops.export_scene.gltf(**kw)
    for o in objs:
        me = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(me)
    bpy.data.collections.remove(coll)
    return dict(min=mn, max=mx, parts=report)


def sample_clips(rig, anim):
    sc = bpy.context.scene
    J = rig.joints
    clips = {}
    for cname in anim.clip_order:
        c = anim.clips[cname]
        tracks = {n: [] for n in rig.order if n != 'HumanoidRootPart'}
        for f in range(c['start'], c['end'] + 1):
            sc.frame_set(f)
            for n in tracks:
                par = rig.parents[n]
                pm = J[par].matrix_world if par else rig.model.matrix_world
                local = pm.inverted() @ J[n].matrix_world
                rest = rig.pivots[n] - (rig.pivots[par] if par else Vector((0, 0, 0)))
                tr = Matrix.Translation(rest).inverted() @ local
                p = to_rbx(tr.translation)
                q = q_to_rbx(tr.to_quaternion().normalized())
                if q[3] < 0:
                    q = tuple(-x for x in q)
                tracks[n].append([_r(x) for x in p] + [_r(x, 5) for x in q])
        # usun tory stale i zerowe
        clean = {}
        for n, fr in tracks.items():
            ident = all(abs(v) < 1e-4 for row in fr for v in row[:6]) and all(abs(row[6] - 1) < 1e-4 for row in fr)
            if not ident:
                clean[n] = fr
        evs = [dict((k, v) for k, v in e.items() if k != 'clip') for e in anim.events if e['clip'] == cname]
        evs.sort(key=lambda e: e['frame'])
        clips[cname] = dict(label=c['label'], loop=c['loop'], length=c['end'] - c['start'],
                            level=c['level'], desc=c['desc'], events=evs, tracks=clean)
    return clips


def write_data(rig, anim, bounds, unit_name, display, out_dir, extra=None):
    clips = sample_clips(rig, anim)
    joints = []
    for n in rig.order:
        joints.append(dict(name=n, parent=rig.parents[n], pivot=[_r(x) for x in to_rbx(rig.pivots[n])]))
    atts = {}
    for a, (j, pos) in rig.attachments.items():
        off = pos - rig.pivots[j]
        atts[a] = dict(joint=j, offset=[_r(x) for x in to_rbx(off)])
    bmin = to_rbx(bounds['min'])
    bmax = to_rbx(bounds['max'])
    lo = [_r(min(a, b)) for a, b in zip(bmin, bmax)]
    hi = [_r(max(a, b)) for a, b in zip(bmin, bmax)]
    data = dict(name=unit_name, display=display, fps=30, bounds=dict(min=lo, max=hi),
                joints=joints, attachments=atts, clips=clips, extra=extra or {})
    with open(os.path.join(out_dir, f'{unit_name}.json'), 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(out_dir, f'{unit_name}_UnitData.lua'), 'w', encoding='utf-8') as fh:
        fh.write(to_luau(data))
    return data


def _lv(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, int) else ('%.5g' % v)
    if v is None:
        return 'nil'
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return '{' + ', '.join(_lv(x) for x in v) + '}'
    if isinstance(v, dict):
        return '{' + ', '.join(f'{_key(k)} = {_lv(x)}' for k, x in v.items()) + '}'
    return json.dumps(str(v))


def _key(k):
    k = str(k)
    if k.isidentifier():
        return k
    return '[' + json.dumps(k, ensure_ascii=False) + ']'


def to_luau(d):
    L = []
    L.append('--!strict')
    L.append(f'-- {d["display"]} ({d["name"]}) - wygenerowane przez ostatni-legion/blender/build_all.py')
    L.append('-- Osie Robloxa, 30 fps. Tory: na kazda klatke 7 liczb: px, py, pz, qx, qy, qz, qw')
    L.append('-- = Motor6D.Transform jointu (wzgledem pozy spoczynkowej, przesuniecie w studach przy skali 1).')
    L.append('return {')
    L.append(f'\tName = {_lv(d["name"])},')
    L.append(f'\tDisplayName = {_lv(d["display"])},')
    L.append('\tFps = 30,')
    L.append(f'\tBounds = {{Min = {_lv(d["bounds"]["min"])}, Max = {_lv(d["bounds"]["max"])}}},')
    L.append('\tJoints = {')
    for j in d['joints']:
        par = f', Parent = {_lv(j["parent"])}' if j['parent'] else ''
        L.append(f'\t\t{{Name = {_lv(j["name"])}{par}, Pivot = {_lv(j["pivot"])}}},')
    L.append('\t},')
    L.append('\tAttachments = {')
    for a, v in d['attachments'].items():
        L.append(f'\t\t{_key(a)} = {{Joint = {_lv(v["joint"])}, Offset = {_lv(v["offset"])}}},')
    L.append('\t},')
    if d.get('extra'):
        L.append(f'\tExtra = {_lv(d["extra"])},')
    L.append('\tClips = {')
    for cn, c in d['clips'].items():
        L.append(f'\t\t{_key(cn)} = {{')
        L.append(f'\t\t\tLabel = {_lv(c["label"])}, Loop = {_lv(c["loop"])}, Length = {c["length"]}, Level = {_lv(c["level"])},')
        L.append(f'\t\t\tDescription = {_lv(c["desc"])},')
        evs = []
        for e in c['events']:
            ee = {'Frame': e['frame'], 'Name': e['name']}
            for k, v in e.items():
                if k not in ('frame', 'name'):
                    ee[k[:1].upper() + k[1:]] = v
            evs.append(ee)
        L.append('\t\t\tEvents = {')
        for e in evs:
            L.append(f'\t\t\t\t{_lv(e)},')
        L.append('\t\t\t},')
        L.append('\t\t\tTracks = {')
        for tn, fr in c['tracks'].items():
            flat = ', '.join(_lv(x) for row in fr for x in row)
            L.append(f'\t\t\t\t{_key(tn)} = {{{flat}}},')
        L.append('\t\t\t},')
        L.append('\t\t},')
    L.append('\t},')
    L.append('}')
    return '\n'.join(L) + '\n'
