"""Render podgladow: postument, swiatla, kamera 3/4, efekty (smuga, pociski, pioruny...)
i plansze z klatkami (PNG). Bez filmow - tylko klatki."""
import math
import os
import random
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

from . import core as C
from . import materials as M

BG = (40, 45, 66)


# ------------------------------------------------------------------ scena
def setup(target=(0, 0, 2.5), dist=12.0, ped_r=2.6, ped_c=(0, 0, 0), res=400, samples=40, lens=50,
          cam_dir=(0.45, -1.0, 0.42)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.transparent_max_bounces = 16
    sc.render.film_transparent = True
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'None'):
        try:
            sc.view_settings.look = look
            break
        except Exception:
            continue

    w = bpy.data.worlds.new('W')
    sc.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    bgn = [n for n in w.node_tree.nodes if n.type == 'BACKGROUND'][0]
    bgn.inputs['Color'].default_value = (0.20, 0.23, 0.33, 1)
    bgn.inputs['Strength'].default_value = 0.55

    # postument
    prof = [(0.0, -0.45), (ped_r - 0.08, -0.45), (ped_r, -0.40), (ped_r + 0.02, -0.12),
            (ped_r - 0.03, -0.02), (ped_r - 0.12, 0.0), (0.0, 0.0)]
    bm = C.bm_lathe(prof, segs=96)
    ped = C.make(bm, 'PEDESTAL', M.get('pedestal'), loc=ped_c, angle=30)
    ped['noexport'] = 1

    def light(name, kind, loc, energy, size, col, tgt=(0, 0, 2.2)):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = col
        if kind == 'AREA':
            ld.size = size
        else:
            ld.shadow_soft_size = size
        ob = bpy.data.objects.new(name, ld)
        C.link(ob)
        ob.location = loc
        d = Vector(tgt) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        ob['noexport'] = 1
        return ob

    light('Key', 'AREA', (7, -9, 11), 2600, 7, (1.0, 0.95, 0.88))
    light('Fill', 'AREA', (-9, -6, 5), 700, 8, (0.75, 0.82, 1.0))
    light('Rim', 'AREA', (-3, 9, 9), 1700, 5, (1.0, 0.92, 0.85))
    light('Rim2', 'AREA', (8, 7, 4), 600, 4, (0.85, 0.9, 1.0))

    cd = bpy.data.cameras.new('Cam')
    cd.lens = lens
    cam = bpy.data.objects.new('Cam', cd)
    C.link(cam)
    sc.camera = cam
    aim(target, dist, cam_dir)
    return cam


def aim(target, dist, cam_dir=(0.45, -1.0, 0.42)):
    cam = bpy.context.scene.camera
    d = Vector(cam_dir).normalized()
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


# ------------------------------------------------------------------ efekty
class FX:
    def __init__(self, rig, anim):
        self.rig = rig
        self.anim = anim
        self.tmp = []
        self.templates = {}
        for ob in bpy.data.objects:
            if ob.get('fx_template'):
                self.templates[ob['fx_template']] = ob
                ob.hide_render = True

    def clear(self):
        for ob in self.tmp:
            data = ob.data
            bpy.data.objects.remove(ob)
            if data is not None:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
        self.tmp = []

    # pomocnicze
    def _mesh(self, name, verts, faces, fade, mat):
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        a = me.attributes.new('fade', 'FLOAT', 'POINT')
        for i, v in enumerate(fade):
            a.data[i].value = v
        me.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        C.link(ob)
        self.tmp.append(ob)
        return ob

    def _bm_obj(self, bm, name, mat, fade=1.0, matrix=None):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        a = me.attributes.new('fade', 'FLOAT', 'POINT')
        for i in range(len(me.vertices)):
            a.data[i].value = fade
        me.materials.append(mat)
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        C.link(ob)
        if matrix is not None:
            ob.matrix_world = matrix
        self.tmp.append(ob)
        return ob

    def _light(self, pos, col, energy, size=0.3):
        ld = bpy.data.lights.new('fxl', 'POINT')
        ld.color = col
        ld.energy = energy
        ld.shadow_soft_size = size
        ob = bpy.data.objects.new('fxl', ld)
        C.link(ob)
        ob.location = pos
        self.tmp.append(ob)

    def world_point(self, joint, rest_pos, f, sub=0.0):
        sc = bpy.context.scene
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        J = self.rig.joints[joint]
        return J.matrix_world @ (Vector(rest_pos) - self.rig.pivots[joint])

    def att(self, name, f):
        j, pos = self.rig.attachments[name]
        return self.world_point(j, pos, f)

    def point(self, spec, key, f):
        v = spec[key]
        if isinstance(v, str):
            return self.att(v, f)
        return Vector(v)

    # ------------------------------------------------------------ rodzaje
    def build(self, f):
        self.clear()
        for s in self.anim.fx:
            if s['kind'] == 'trail':
                if s['start'] <= f <= s['end'] + 3:
                    self.trail(s, f)
            elif s['start'] <= f <= s['end']:
                getattr(self, s['kind'])(s, f)
        bpy.context.scene.frame_set(f)

    def trail(self, s, f):
        n_len = s.get('len', 6)
        s0 = max(s['start'], f - n_len)
        s1 = min(f, s['end'])
        if s1 - s0 < 0.5:
            return
        fade_mul = 1.0 if f <= s['end'] else max(0.0, 1.0 - (f - s['end']) / 3.5)
        steps = max(2, int((s1 - s0) * 3))
        verts, fades, faces = [], [], []
        base = s.get('base_alpha', 0.25)
        for i in range(steps + 1):
            t = i / steps
            fr = s0 + (s1 - s0) * t
            a = self.world_point(s['joint'], s['a'], fr)
            b = self.world_point(s['joint'], s['b'], fr)
            verts += [tuple(a), tuple(b)]
            k = (t ** 1.4) * fade_mul
            fades += [k * base, k]
        for i in range(steps):
            faces.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
        mat = M.fx('trail_' + s.get('name', 'w'), s.get('col', (0.85, 0.92, 1.0)), s.get('strength', 2.2),
                   s.get('alpha', 0.85))
        self._mesh('fx_trail', verts, faces, fades, mat)

    def _proj_pos(self, s, t, p0):
        v = Vector(s['dir']).normalized() * s.get('speed', 1.2)
        g = s.get('grav', 0.0)
        return p0 + v * t + Vector((0, 0, -0.5 * g * t * t)), v + Vector((0, 0, -g * t))

    def projectile(self, s, f):
        p0 = self.point(s, 'from', s['start']) if isinstance(s['from'], str) else Vector(s['from'])
        t = f - s['start']
        pos, vel = self._proj_pos(s, t, p0)
        tpl = self.templates[s['model']]
        me = tpl.data.copy()
        ob = bpy.data.objects.new('fx_proj', me)
        C.link(ob)
        self.tmp.append(ob)
        rot = vel.normalized()
        q = (-rot).to_track_quat('Y', 'Z')
        ob.matrix_world = Matrix.LocRotScale(pos, q, Vector((1, 1, 1)) * s.get('scale', 1.0))
        # smuga za pociskiem
        if s.get('streak', True) and t > 0:
            back = [self._proj_pos(s, max(0, t - k * 0.5), p0)[0] for k in range(5)]
            side = rot.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side = side.normalized() * s.get('streak_w', 0.08)
            up = rot.cross(side).normalized() * s.get('streak_w', 0.08)
            verts, fades, faces = [], [], []
            for i, p in enumerate(back):
                k = 1.0 - i / (len(back) - 1)
                verts += [tuple(p + side), tuple(p - side), tuple(p + up), tuple(p - up)]
                fades += [k * 0.8] * 4
            for i in range(len(back) - 1):
                a = 4 * i
                faces.append((a, a + 1, a + 5, a + 4))
                faces.append((a + 2, a + 3, a + 7, a + 6))
            mat = M.fx('streak_' + s.get('name', 'w'), s.get('col', (0.9, 0.95, 1.0)), 2.0, 0.7)
            self._mesh('fx_streak', verts, faces, fades, mat)
        if s.get('glow'):
            self._light(pos, s['glow'], s.get('glow_e', 60))

    def lightning(self, s, f):
        a = self.point(s, 'a', f)
        b = self.point(s, 'b', f)
        rnd = random.Random(s.get('seed', 1) * 1000 + f)
        col = s.get('col', (0.6, 0.8, 1.0))

        def bolt(a, b, n, amp, r, depth=0):
            d = b - a
            side = d.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            up = d.cross(side).normalized()
            pts = []
            for i in range(n + 1):
                t = i / n
                off = 0 if i in (0, n) else amp * d.length
                p = a + d * t + side * rnd.uniform(-off, off) + up * rnd.uniform(-off, off) * 0.6
                pts.append(tuple(p))
            for rr, mat in ((r * 0.7, M.fx('bolt_core', (0.85, 0.93, 1.0), 9.0, 1.0)),
                            (r * 2.4, M.fx('bolt_glow_' + s.get('name', 'b'), col, 5.0, 0.35))):
                bm = C.bm_tube(pts, rr, smooth=False, bevel_res=1, res=1)
                self._bm_obj(bm, 'fx_bolt', mat)
            if depth == 0:
                for _ in range(s.get('branches', 2)):
                    i = rnd.randint(2, n - 2)
                    pa = Vector(pts[i])
                    dirb = (b - a).normalized() + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.2)))
                    bolt(pa, pa + dirb.normalized() * d.length * rnd.uniform(0.2, 0.35), 5, amp, r * 0.6, 1)
        bolt(a, b, s.get('n', 12), s.get('amp', 0.06), s.get('r', 0.05))
        self._light(b, col, s.get('energy', 400), 0.5)
        self._light(a, col, s.get('energy', 400) * 0.4, 0.5)

    def ring(self, s, f):
        t = (f - s['start']) / max(1, s['end'] - s['start'])
        c = self.point(s, 'center', s['start'] if s.get('fixed', True) else f)
        r = s.get('r0', 0.5) + (s.get('r1', 4.0) - s.get('r0', 0.5)) * (1 - (1 - t) ** 2)
        th = s.get('th', 0.12)
        bm = C.bm_torus(r, th, 64, 8)
        C.bm_transform(bm, scale=(1, 1, s.get('flat', 0.35)))
        mat = M.fx('ring_' + s.get('name', 'r'), s.get('col', (1, 0.9, 0.6)), s.get('strength', 4.0), 0.9)
        self._bm_obj(bm, 'fx_ring', mat, fade=(1 - t) ** 1.3, matrix=Matrix.Translation(c))
        if s.get('disc'):
            bm = C.bm_cyl(r, 0.02, 64)
            self._bm_obj(bm, 'fx_disc', M.fx('disc_' + s.get('name', 'r'), s.get('col', (1, 1, 1)), 2.0, 0.35),
                         fade=(1 - t) * 0.6, matrix=Matrix.Translation(c + Vector((0, 0, 0.03))))

    def beam(self, s, f):
        a = self.point(s, 'from', f)
        d = Vector(s['dir']).normalized()
        L = s.get('length', 6.0)
        t = (f - s['start']) / max(1, s['end'] - s['start'])
        grow = min(1.0, t * 3.0)
        bm = C.bm_cyl(s.get('r0', 0.1), L * grow, 24, r2=s.get('r1', 0.6), caps=True)
        C.bm_transform(bm, loc=(0, 0, L * grow / 2))
        q = d.to_track_quat('Z', 'Y')
        fade = (1 - max(0, t - 0.7) / 0.3) * (0.85 + 0.15 * math.sin(f * 2.3))
        self._bm_obj(bm, 'fx_beam', M.fx('beam_' + s.get('name', 'b'), s.get('col', (1, 0.9, 0.3)), 5.0, 0.55),
                     fade=fade, matrix=Matrix.LocRotScale(a, q, Vector((1, 1, 1))))
        bm = C.bm_cyl(s.get('r0', 0.1) * 0.35, L * grow, 12, r2=s.get('r1', 0.6) * 0.3)
        C.bm_transform(bm, loc=(0, 0, L * grow / 2))
        self._bm_obj(bm, 'fx_beamc', M.fx('beamcore', (1, 1, 0.9), 10.0, 0.8),
                     fade=fade, matrix=Matrix.LocRotScale(a, q, Vector((1, 1, 1))))
        self._light(a + d * 0.3, s.get('col', (1, 0.9, 0.3)), 150)

    def orb(self, s, f):
        c = self.point(s, 'at', f)  # 'at' moze byc nazwa attachmentu albo (x, y, z)
        t = (f - s['start']) / max(1, s['end'] - s['start'])
        k = math.sin(t * math.pi)
        r = s.get('r', 0.35) * (0.6 + 0.6 * k)
        for rr, mat, fd in ((r * 0.45, M.fx('orbcore', (1, 0.95, 1), 6.0, 1.0), 1.0),
                            (r, M.fx('orb_' + s.get('name', 'o'), s.get('col', (1, 0.8, 0.3)), 3.0, 0.45), k)):
            self._bm_obj(C.bm_sphere(rr, 20, 12), 'fx_orb', mat, fade=fd, matrix=Matrix.Translation(c))
        self._light(c, s.get('col', (1, 0.8, 0.3)), s.get('energy', 120) * k)

    def puffs(self, s, f):
        c = self.point(s, 'center', s['start'])
        t = (f - s['start']) / max(1, s['end'] - s['start'])
        rnd = random.Random(s.get('seed', 3))
        mat = M.fx('puff_' + s.get('name', 'p'), s.get('col', (0.8, 0.75, 0.65)), s.get('strength', 0.8), 0.55)
        d = Vector(s.get('dir', (0, 0, 0)))
        for i in range(s.get('count', 10)):
            ang = rnd.uniform(0, 2 * math.pi)
            sp = rnd.uniform(0.5, 1.0) * s.get('spread', 2.0)
            p = c + Vector((math.cos(ang) * sp * t, math.sin(ang) * sp * t, s.get('rise', 0.6) * t * rnd.uniform(0.5, 1.2))) + d * t
            r = s.get('size', 0.35) * (0.5 + t) * rnd.uniform(0.7, 1.3)
            self._bm_obj(C.bm_sphere(r, 12, 8), 'fx_puff', mat, fade=(1 - t) ** 1.2, matrix=Matrix.Translation(p))

    def sparks(self, s, f):
        c = self.point(s, 'center', s['start'] if s.get('fixed', True) else f)
        t = (f - s['start']) / max(1, s['end'] - s['start'])
        rnd = random.Random(s.get('seed', 5))
        mat = M.fx('spark_' + s.get('name', 's'), s.get('col', (1, 0.8, 0.3)), 8.0, 1.0)
        for i in range(s.get('count', 14)):
            v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.2, 1.4))).normalized()
            p = c + v * s.get('spread', 1.5) * t + Vector((0, 0, -1.0 * t * t)) + Vector(s.get('drift', (0, 0, 0))) * t
            self._bm_obj(C.bm_sphere(0.05 * (1 - t) + 0.015, 8, 4), 'fx_spark', mat, fade=1 - t,
                         matrix=Matrix.Translation(p))

    def glowpoint(self, s, f):
        c = self.point(s, 'at', f)
        self._light(c, s.get('col', (1, 0.8, 0.3)), s.get('energy', 80))


# ------------------------------------------------------------------ render
def apply_hides(rig, anim, f):
    hidden = set()
    for (j, a, b) in anim.hides:
        if a <= f < b:
            hidden.add(j)
    for name, J in rig.joints.items():
        for ob in J.children_recursive:
            if ob.type in ('MESH', 'CURVE') and ob.get('jnt') == name:
                ob.hide_render = name in hidden
    for ob in bpy.data.objects:
        if ob.get('show_frames') is not None:
            ob.hide_render = True
            for (a, b) in ob['show_frames']:
                if a <= f < b:
                    ob.hide_render = False


def render_frame(rig, anim, fx, f, path, hooks=()):
    sc = bpy.context.scene
    sc.frame_set(f)
    apply_hides(rig, anim, f)
    for h in hooks:
        h(f)
    fx.build(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    fx.clear()


def compose(img_path, bg=BG):
    from PIL import Image
    im = Image.open(img_path).convert('RGBA')
    base = Image.new('RGBA', im.size, bg + (255,))
    # delikatna winieta
    base.alpha_composite(im)
    return base.convert('RGB')


def default_show(c, n):
    s, e = c['start'], c['end']
    return [round(s + (e - s) * i / (n - 1)) for i in range(n)]


def render_sheets(rig, anim, out_dir, unit, display, subtitle, hooks=(), cell=360, cols=6,
                  hero_res=900):
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, '_tmp')
    os.makedirs(tmp, exist_ok=True)
    sc = bpy.context.scene
    fx = FX(rig, anim)
    font_b = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    font_s = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)

    # hero
    sc.render.resolution_x = sc.render.resolution_y = hero_res
    hp = os.path.join(tmp, 'hero.png')
    lens0 = sc.camera.data.lens
    sc.camera.data.lens = lens0 * 1.3
    render_frame(rig, anim, fx, anim.clips['Idle']['start'], hp, hooks)
    sc.camera.data.lens = lens0
    hero = compose(hp)
    hero.save(os.path.join(out_dir, f'{unit}_hero.png'))

    sc.render.resolution_x = sc.render.resolution_y = cell
    rows = []
    for cn in anim.clip_order:
        c = anim.clips[cn]
        frames = c['show'] or default_show(c, cols if cn != 'Idle' else 3)
        imgs = []
        for f in frames:
            p = os.path.join(tmp, f'{cn}_{f:04d}.png')
            render_frame(rig, anim, fx, f, p, hooks)
            imgs.append((f - c['start'], compose(p)))
        rows.append((c, imgs))

    pad = 18
    head_h = 96
    row_h = cell + 46
    W = pad * 2 + cols * cell + (cols - 1) * 8
    H = head_h + len(rows) * (row_h + 10) + pad
    sheet = Image.new('RGB', (W, H), (24, 26, 38))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), display, font=font_b, fill=(245, 214, 140))
    d.text((pad, 58), subtitle, font=font, fill=(200, 205, 220))
    y = head_h
    for c, imgs in rows:
        lab = c['label'] + (f'   ({c["level"]})' if c['level'] else '') + f'   [{c["end"] - c["start"]} kl.]'
        d.text((pad, y + 8), lab, font=font, fill=(235, 235, 245))
        for i, (rf, im) in enumerate(imgs):
            x = pad + i * (cell + 8)
            sheet.paste(im, (x, y + 40))
            d.text((x + 8, y + 44), f'kl. {rf}', font=font_s, fill=(170, 175, 195))
        y += row_h + 10
    sp = os.path.join(out_dir, f'{unit}_animacje.png')
    sheet.save(sp, optimize=True)
    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)
    return sp
