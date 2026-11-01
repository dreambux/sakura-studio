"""Scena konceptu mapy: teren, sciezki, woda, rozstawienie dekoracji (instancje kolekcji),
rendery (z gory ortho + z boku), opis na obrazku oraz eksport ukladu do Luau."""
import json
import math
import os
import random

import bpy
import bmesh
from mathutils import Vector, Matrix, Euler, noise

from . import props as P

D2R = math.pi / 180


def to_collections():
    """Kazdy zbudowany model -> wlasna kolekcja (do instancjonowania)."""
    sc = bpy.context.scene
    for root in [o for o in sc.objects if o.get('prop')]:
        name = root['prop']
        if 'C_' + name in bpy.data.collections:
            continue
        col = bpy.data.collections.new('C_' + name)
        for o in [root] + list(root.children_recursive):
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
        root.location = (0, 0, 0)


class MapScene:
    def __init__(self, name, display, difficulty, size=(220, 170)):
        self.name = name
        self.display = display
        self.difficulty = difficulty
        self.W, self.D = size
        self.paths = []          # (punkty [(x,y)], szerokosc, tekstura, etykieta)
        self.placements = []     # (prop, x, y, z, rot, scale)
        self.labels = []         # (x, y, tekst, kolor)
        self.blocked = []        # (x, y, r) - nie stawiaj dekoracji
        self.spawns = []
        self.base = None
        self.coll = bpy.data.collections.new('MAP_' + name)
        bpy.context.scene.collection.children.link(self.coll)
        self.rnd = random.Random(hash(name) & 0xffff)

    # -------------------------------------------------------- obiekty
    def _obj(self, bm, name, mat, uv_tile=None):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        self.coll.objects.link(ob)
        if uv_tile:
            P.uv_box(ob, uv_tile)
        return ob

    def ground(self, outline, tex, z=0.0, depth=6.0, cliff_tex='cliff', bevel=2.0, name='ground'):
        """Plaski teren z wielokata (x,y) - gora z tekstura, boki jako klif."""
        bm = bmesh.new()
        top = [bm.verts.new((x, y, z)) for x, y in outline]
        bot = [bm.verts.new((x * 1.02, y * 1.02, z - depth)) for x, y in outline]
        ftop = bm.faces.new(top)
        n = len(outline)
        sides = []
        for i in range(n):
            j = (i + 1) % n
            sides.append(bm.faces.new((top[j], top[i], bot[i], bot[j])))
        bm.faces.new(list(reversed(bot)))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.triangulate(bm, faces=[ftop])
        ob = self._obj(bm, name, P.T(tex), 8.0)
        # boki inna tekstura
        ob.data.materials.append(P.T(cliff_tex))
        for p in ob.data.polygons:
            if abs(p.normal.z) < 0.5:
                p.material_index = 1
        return ob

    def plateau(self, cx, cy, rx, ry, h, tex, cliff='cliff', seed=1, name='plateau'):
        pts = []
        for k in range(28):
            a = 2 * math.pi * k / 28
            r = 1 + 0.18 * noise.noise(Vector((math.cos(a) * 2 + seed, math.sin(a) * 2, seed)))
            pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
        bm = bmesh.new()
        top = [bm.verts.new((x, y, h)) for x, y in pts]
        bot = [bm.verts.new((x + (x - cx) * 0.15, y + (y - cy) * 0.15, -1)) for x, y in pts]
        ftop = bm.faces.new(top)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((top[j], top[i], bot[i], bot[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.triangulate(bm, faces=[ftop])
        ob = self._obj(bm, name, P.T(tex), 8.0)
        ob.data.materials.append(P.T(cliff))
        for p in ob.data.polygons:
            if abs(p.normal.z) < 0.6:
                p.material_index = 1
        self.blocked.append((cx, cy, max(rx, ry) * 0.9))
        return ob

    def water(self, size=1400, z=-1.2, color=(0.08, 0.42, 0.55), name='water'):
        bm = bmesh.new()
        s = size / 2
        bm.faces.new([bm.verts.new(v) for v in ((-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z))])
        m = bpy.data.materials.get('M_water') or bpy.data.materials.new('M_water')
        try:
            m.use_nodes = True
        except Exception:
            pass
        b = [n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
        b.inputs['Base Color'].default_value = (*color, 1)
        b.inputs['Roughness'].default_value = 0.08
        b.inputs['Coat Weight'].default_value = 0.0
        nt = m.node_tree
        tx = nt.nodes.new('ShaderNodeTexNoise')
        tx.inputs['Scale'].default_value = 0.08
        tx.inputs['Detail'].default_value = 4
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = 0.15
        nt.links.new(tx.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
        ob = self._obj(bm, name, m)
        # plycizna przy brzegu
        return ob

    def path(self, pts, width=9.0, tex='cobble', z=0.12, label=None, curb='blocks', spawn=None, color=(255, 80, 60)):
        """Sciezka wrogow: wstega z tekstura + krawezniki. pts = [(x,y), ...] od spawnu do bazy."""
        bm = bmesh.new()
        pts = [Vector((x, y)) for x, y in pts]
        # wygladzenie zakretow (Chaikin)
        for _ in range(2):
            new = [pts[0]]
            for a, b in zip(pts, pts[1:]):
                new.append(a * 0.75 + b * 0.25)
                new.append(a * 0.25 + b * 0.75)
            new.append(pts[-1])
            pts = new
        left, right = [], []
        for i, p in enumerate(pts):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            d = (b - a).normalized()
            nrm = Vector((-d.y, d.x))
            left.append(p + nrm * width / 2)
            right.append(p - nrm * width / 2)
        vl = [bm.verts.new((v.x, v.y, z)) for v in left]
        vr = [bm.verts.new((v.x, v.y, z)) for v in right]
        for i in range(len(pts) - 1):
            bm.faces.new((vl[i], vr[i], vr[i + 1], vl[i + 1]))
        ob = self._obj(bm, f'path_{len(self.paths)}', P.T(tex), 6.0)
        # krawezniki
        for side, arr in (('L', left), ('R', right)):
            for i in range(0, len(arr) - 1):
                a, b = arr[i], arr[i + 1]
                L = (b - a).length
                if L < 0.2:
                    continue
                c = (a + b) / 2
                ang = math.atan2(b.y - a.y, b.x - a.x)
                bmc = P.box(L + 0.3, 0.7, 0.45, 0.08)
                o = self._obj(bmc, f'curb_{side}{i}', P.T(curb))
                o.location = (c.x, c.y, z + 0.1)
                o.rotation_euler = (0, 0, ang)
                bpy.context.view_layer.update()
                P.uv_box(o, 3)
        self.paths.append(dict(pts=[(round(p.x, 2), round(p.y, 2)) for p in pts], width=width, label=label,
                               color=color))
        return ob

    def place(self, prop, x, y, z=0.0, rot=0.0, scale=1.0):
        col = bpy.data.collections.get('C_' + prop)
        if col is None:
            raise KeyError(prop)
        e = bpy.data.objects.new(f'I_{prop}', None)
        e.instance_type = 'COLLECTION'
        e.instance_collection = col
        e.location = (x, y, z)
        e.rotation_euler = (0, 0, rot * D2R)
        e.scale = (scale, scale, scale)
        self.coll.objects.link(e)
        self.placements.append((prop, x, y, z, rot, scale))
        return e

    def near_path(self, x, y, margin):
        p = Vector((x, y))
        for pa in self.paths:
            pts = [Vector(q) for q in pa['pts']]
            for a, b in zip(pts, pts[1:]):
                ab = b - a
                t = max(0, min(1, (p - a).dot(ab) / max(1e-6, ab.length_squared)))
                if (a + ab * t - p).length < pa['width'] / 2 + margin:
                    return True
        return False

    def free(self, x, y, r, margin_path=3.0):
        if self.near_path(x, y, r + margin_path):
            return False
        for bx, by, br in self.blocked:
            if math.hypot(x - bx, y - by) < r + br:
                return False
        return True

    def scatter(self, props, n, region, r=3.0, scale=(0.8, 1.2), z=0.0, margin_path=3.0, inside=None, tries=30):
        """region = (xmin, ymin, xmax, ymax); inside(x,y)->bool dodatkowy test."""
        made = 0
        for _ in range(n * tries):
            if made >= n:
                break
            x = self.rnd.uniform(region[0], region[2])
            y = self.rnd.uniform(region[1], region[3])
            if inside and not inside(x, y):
                continue
            if not self.free(x, y, r, margin_path):
                continue
            p = props[self.rnd.randrange(len(props))]
            self.place(p, x, y, z, self.rnd.uniform(0, 360), self.rnd.uniform(*scale))
            self.blocked.append((x, y, r * 0.8))
            made += 1
        return made

    def block(self, x, y, r):
        self.blocked.append((x, y, r))

    def label(self, x, y, text, color=(255, 255, 255)):
        self.labels.append((x, y, text, color))

    # -------------------------------------------------------- swiatlo i render
    def lighting(self, sun_rot=(50, 0, 35), sun_col=(1.0, 0.95, 0.86), sun_e=4.5, sky=(0.55, 0.65, 0.85), sky_e=0.8,
                 bg=None, night=False):
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 32
        sc.cycles.use_denoising = True
        try:
            sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        except Exception:
            pass
        sc.view_settings.view_transform = 'AgX'
        sc.render.film_transparent = False
        w = bpy.data.worlds.new('W_' + self.name)
        sc.world = w
        try:
            w.use_nodes = True
        except Exception:
            pass
        bgn = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
        bgn.inputs['Color'].default_value = (*sky, 1)
        bgn.inputs['Strength'].default_value = sky_e
        ld = bpy.data.lights.new('Sun_' + self.name, 'SUN')
        ld.energy = sun_e
        ld.angle = 0.06
        ld.color = sun_col
        so = bpy.data.objects.new('Sun_' + self.name, ld)
        self.coll.objects.link(so)
        so.rotation_euler = [a * D2R for a in sun_rot]

    def _cam(self):
        sc = bpy.context.scene
        if sc.camera is None:
            cd = bpy.data.cameras.new('Cam')
            cam = bpy.data.objects.new('Cam', cd)
            sc.collection.objects.link(cam)
            sc.camera = cam
        return sc.camera

    def render_top(self, path, res=(1600, 1240)):
        sc = bpy.context.scene
        cam = self._cam()
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = max(self.W, self.D * res[0] / res[1]) * 1.08
        cam.location = (0, 0, 300)
        cam.rotation_euler = (0, 0, 0)
        cam.data.clip_end = 2000
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        self._top_scale = (cam.data.ortho_scale, res)

    def render_side(self, path, res=(1600, 900), dirv=(0.0, -1.0, 0.62), dist=None, target=(0, 0, 0), lens=35):
        sc = bpy.context.scene
        cam = self._cam()
        cam.data.type = 'PERSP'
        cam.data.lens = lens
        cam.data.clip_end = 3000
        d = Vector(dirv).normalized()
        dist = dist or max(self.W, self.D) * 1.05
        cam.location = Vector(target) + d * dist
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)

    def annotate(self, src, dst, legend):
        """Opis na widoku z gory: sciezki (strzalki), spawny, baza, poziom trudnosci, legenda, skala."""
        from PIL import Image, ImageDraw, ImageFont
        im = Image.open(src).convert('RGB')
        W, H = im.size
        scale, _ = self._top_scale
        ppu = W / scale

        def px(x, y):
            return (W / 2 + x * ppu, H / 2 - y * ppu)
        d = ImageDraw.Draw(im, 'RGBA')
        fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 19)
        for pa in self.paths:
            pts = [px(*p) for p in pa['pts']]
            col = tuple(pa['color']) + (150,)
            d.line(pts, fill=col, width=5)
            # strzalki kierunku
            acc = 0
            for a, b in zip(pts, pts[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                acc += L
                if acc > 70:
                    acc = 0
                    ang = math.atan2(b[1] - a[1], b[0] - a[0])
                    cx, cy = b
                    s = 14
                    tri = [(cx + math.cos(ang) * s, cy + math.sin(ang) * s),
                           (cx + math.cos(ang + 2.5) * s, cy + math.sin(ang + 2.5) * s),
                           (cx + math.cos(ang - 2.5) * s, cy + math.sin(ang - 2.5) * s)]
                    d.polygon(tri, fill=tuple(pa['color']) + (230,))
        for x, y, text, color in self.labels:
            X, Y = px(x, y)
            tw = d.textlength(text, font=f)
            d.rounded_rectangle([X - tw / 2 - 8, Y - 15, X + tw / 2 + 8, Y + 15], 8, fill=(20, 22, 32, 200))
            d.text((X - tw / 2, Y - 12), text, font=f, fill=color)
        d.rounded_rectangle([12, 12, 760, 64], 10, fill=(20, 22, 32, 215))
        d.text((24, 22), f'{self.display}   |   poziom: {self.difficulty}', font=fb, fill=(245, 214, 140))
        y = H - 24 - 26 * len(legend)
        d.rounded_rectangle([12, y - 14, 640, H - 12], 10, fill=(20, 22, 32, 215))
        for i, line in enumerate(legend):
            d.text((26, y + i * 26), line, font=f, fill=(232, 232, 240))
        # skala 20 st.
        L = 20 * ppu
        d.line([(W - 40 - L, H - 30), (W - 40, H - 30)], fill=(255, 255, 255, 255), width=4)
        d.text((W - 40 - L, H - 58), '20 studs', font=f, fill=(255, 255, 255))
        im.save(dst)

    # -------------------------------------------------------- eksport ukladu
    def export_luau(self, path, extra=None):
        def R(x, y, z=0.0):
            return [round(-x, 2), round(z, 2), round(y, 2)]
        data = dict(name=self.name, display=self.display, difficulty=self.difficulty,
                    paths=[dict(label=p['label'], width=p['width'], points=[R(x, y, 0.2) for x, y in p['pts']])
                           for p in self.paths],
                    props=[[p, *R(x, y, z), round(rot, 1), round(s, 3)] for p, x, y, z, rot, s in self.placements],
                    extra=extra or {})
        with open(path.replace('.lua', '.json'), 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False)
        L = ['-- Uklad mapy "%s" (%s) - wygenerowane z konceptu w Blenderze.' % (self.display, self.difficulty),
             '-- Osie Robloxa. Props: {nazwa_modelu, x, y, z, obrot_Y_stopnie, skala}.',
             '-- Paths: punkty sciezki od spawnu do bazy (Waypoints).', 'return {',
             f'\tName = "{self.name}", DisplayName = "{self.display}", Difficulty = "{self.difficulty}",',
             '\tPaths = {']
        for p in data['paths']:
            pts = ', '.join('{%s, %s, %s}' % tuple(q) for q in p['points'])
            L.append(f'\t\t{{Label = "{p["label"] or ""}", Width = {p["width"]}, Points = {{{pts}}}}},')
        L.append('\t},')
        L.append('\tProps = {')
        for pr in data['props']:
            L.append('\t\t{"%s", %s, %s, %s, %s, %s},' % tuple(pr))
        L.append('\t},')
        L.append('}')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(L) + '\n')
