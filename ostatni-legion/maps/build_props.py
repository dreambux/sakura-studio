"""Buduje biblioteke dekoracji: katalog (miniatury), GLB per kategoria do Robloxa, .blend.

  python maps/build_props.py               (wszystko)
  python maps/build_props.py --no-render   (tylko eksport)
  python maps/build_props.py -- glaz palma (wybrane, tylko podglad)
"""
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)

from lib import props as P  # noqa: E402
from lib import p_nature  # noqa: E402,F401
for _m in ('p_arch', 'p_harbor', 'p_market', 'p_themes', 'p_unique', 'p_more', 'p_extra'):
    try:
        __import__('lib.' + _m)
    except ImportError:
        pass

OUT = os.path.join(HERE, 'modele')
CAT = os.path.join(HERE, 'katalog')
ROT180 = Matrix.Rotation(math.pi, 4, 'Z')


def bbox(root):
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in root.children_recursive:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('W')
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bg = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
    bg.inputs['Color'].default_value = (0.55, 0.65, 0.85, 1)
    bg.inputs['Strength'].default_value = 0.7
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 4.5
    sun.angle = 0.08
    sun.color = (1.0, 0.95, 0.86)
    so = bpy.data.objects.new('Sun', sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(35))
    cd = bpy.data.cameras.new('Cam')
    cam = bpy.data.objects.new('Cam', cd)
    bpy.context.scene.collection.objects.link(cam)
    sc.camera = cam
    # podloze pod miniatury
    me = bpy.data.meshes.new('ground')
    me.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new('GROUND', me)
    bpy.context.scene.collection.objects.link(g)
    me.materials.append(P.T('ground'))
    P.uv_box(g, 8)
    g.is_shadow_catcher = True
    return cam


def thumb(root, path, res=320):
    sc = bpy.context.scene
    for r in roots:
        vis = r is root
        for o in [r] + list(r.children_recursive):
            o.hide_render = not vis
    mn, mx = bbox(root)
    c = (mn + mx) / 2
    size = max((mx - mn).length, 1.0)
    cam = sc.camera
    cam.data.lens = 50
    d = Vector((0.75, -1.0, 0.62)).normalized()
    cam.location = c + d * size * 1.55
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def export_category(cat, names, path):
    dg = bpy.context.evaluated_depsgraph_get()
    coll = bpy.data.collections.new('EXP_' + cat)
    bpy.context.scene.collection.children.link(coll)
    made = []
    report = {}
    for n in names:
        root = bpy.data.objects['P_' + n]
        inv = root.matrix_world.inverted()
        top = bpy.data.objects.new(n, None)
        coll.objects.link(top)
        made.append(top)
        groups = {}
        for o in root.children_recursive:
            if o.type != 'MESH' or not o.data.materials:
                continue
            me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
            me.transform(inv @ o.matrix_world)
            groups.setdefault(o.data.materials[0].name, []).append(me)
        fx = []
        for o in root.children_recursive:
            if o.get('fx'):
                p = inv @ o.matrix_world.translation
                fx.append(dict(kind=o['fx'], pos=[round(-p.x, 3), round(p.z, 3), round(p.y, 3)],
                               **{k: (o[k].to_list() if hasattr(o[k], 'to_list') else o[k]) for k in o.keys()
                                  if k not in ('fx',) and not k.startswith('_')}))
        tris = 0
        for mname, mes in groups.items():
            bm = bmesh.new()
            for me in mes:
                bm.from_mesh(me)
                bpy.data.meshes.remove(me)
            for f in bm.faces:
                f.material_index = 0
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            t = len(bm.faces)
            tris = max(tris, t)
            out = bpy.data.meshes.new(f'{n}__{mname}')
            bm.to_mesh(out)
            bm.free()
            out.materials.clear()
            out.materials.append(bpy.data.materials[mname])
            out.transform(ROT180)
            ob = bpy.data.objects.new(f'{n}__{mname[2:]}', out)
            coll.objects.link(ob)
            ob.parent = top
            made.append(ob)
            if t > 19000:
                print('UWAGA:', n, mname, t, 'trojkatow')
        report[n] = dict(max_tris=tris, fx=fx)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in made:
        o.select_set(True)
    bpy.context.view_layer.objects.active = made[0]
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_materials='EXPORT', export_animations=False, export_image_format='JPEG',
              export_jpeg_quality=88)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop('export_jpeg_quality', None)
        bpy.ops.export_scene.gltf(**kw)
    for o in made:
        d = o.data
        bpy.data.objects.remove(o)
        if d is not None:
            bpy.data.meshes.remove(d)
    bpy.data.collections.remove(coll)
    return report


def sheet(cat, names, out_png, cell=320, cols=6):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
    rows = (len(names) + cols - 1) // cols
    W = cols * (cell + 8) + 8
    im = Image.new('RGB', (W, rows * (cell + 30) + 60), (40, 45, 66))
    d = ImageDraw.Draw(im)
    d.text((10, 14), f'Ostatni Legion - dekoracje: {cat}', font=fb, fill=(245, 214, 140))
    for i, n in enumerate(names):
        t = Image.open(os.path.join(CAT, '_tmp', f'{n}.png')).convert('RGBA')
        bg = Image.new('RGBA', t.size, (52, 58, 82, 255))
        bg.alpha_composite(t)
        x, y = 8 + (i % cols) * (cell + 8), 56 + (i // cols) * (cell + 30)
        im.paste(bg.convert('RGB'), (x, y))
        d.text((x + 4, y + cell + 6), n, font=font, fill=(230, 230, 240))
    im.save(out_png)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    flags = {a for a in sys.argv if a.startswith('--') and a != '--'}
    sel = [a for a in argv if not a.startswith('--')]
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(CAT, '_tmp'), exist_ok=True)
    t0 = time.time()
    names = sel or list(P.REGISTRY)
    roots = []
    for n in names:
        P.REGISTRY[n][1]()
        roots.append(bpy.data.objects['P_' + n])
    print('modele:', len(roots), f'{time.time() - t0:.0f} s')
    bycat = {}
    for n in names:
        bycat.setdefault(P.REGISTRY[n][0], []).append(n)
    if not sel:
        manifest = {}
        for cat, ns in bycat.items():
            rep = export_category(cat, ns, os.path.join(OUT, f'{cat}.glb'))
            for n in ns:
                manifest[n] = dict(kategoria=cat, opis=P.REGISTRY[n][2], plik=f'{cat}.glb', **rep[n])
        with open(os.path.join(OUT, 'katalog.json'), 'w', encoding='utf-8') as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
        print('eksport GLB:', list(bycat), f'{time.time() - t0:.0f} s')
    if '--no-render' not in flags:
        setup_render()
        for n, r in zip(names, roots):
            thumb(r, os.path.join(CAT, '_tmp', f'{n}.png'))
        for cat, ns in bycat.items():
            sheet(cat, ns, os.path.join(CAT, f'{cat}.png' if not sel else f'_podglad_{cat}.png'))
        print('katalog gotowy', f'{time.time() - t0:.0f} s')
    if not sel:
        for r in roots:
            for o in [r] + list(r.children_recursive):
                o.hide_render = False
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'dekoracje.blend'), compress=True)
