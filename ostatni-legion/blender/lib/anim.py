"""Animacje: pozy w jezyku "semantycznym" -> klatki kluczowe na jointach.

Klucze pozy:
  T  = (pochylenie_do_przodu, przechyl_w_lewo, obrot_w_lewo)   tulow (obraca cale cialo)
  Tp = (x, do_przodu)    przesuniecie korzenia (studs); wysokosc liczona automatycznie
                          tak, zeby nizsza stopa stala na ziemi (+ 'air' = wyskok)
  H  = (kiwniecie_w_dol, przechyl, obrot_w_lewo)   glowa (wzgledem tulowia)
  RA/LA = (do_przodu, na_zewnatrz, do_srodka)       ramiona (wzgledem tulowia)
  RL/LL = (do_przodu, na_zewnatrz, do_srodka)       nogi (wzgledem SWIATA, kompensuja tulow)
  <joint> = (rx, ry, rz) surowe katy albo dict(pitch=, roll=, yaw=, r=, p=)
           pitch dziala dla jointow "follow" (bron/tarcza trzyma poziom niezaleznie od reki)
Wszystkie katy w stopniach.
"""
import math
import bpy
from mathutils import Vector, Euler, Matrix

D2R = math.pi / 180.0


def _e(rx, ry, rz):
    return Euler((rx * D2R, ry * D2R, rz * D2R), 'XYZ')


class Animator:
    def __init__(self, rig, base):
        self.rig = rig
        self.base = dict(base)
        self.clips = {}
        self.clip_order = []
        self.events = []
        self.fx = []
        self.hides = []
        self._prev = {}
        self.cur = None

    # ------------------------------------------------------------ clips
    def clip(self, name, label, start, length, loop=False, desc='', show=None, level=''):
        self.clips[name] = dict(name=name, label=label, start=start, end=start + length,
                                loop=loop, desc=desc, show=show, level=level)
        self.clip_order.append(name)
        self.cur = name
        return start

    def P(self, **kw):
        p = dict(self.base)
        p.update(kw)
        return p

    def event(self, rel, name, **data):
        c = self.clips[self.cur]
        self.events.append(dict(clip=self.cur, frame=rel, name=name, **data))
        try:
            bpy.context.scene.timeline_markers.new(f'{self.cur}:{name}', frame=c['start'] + rel)
        except Exception:
            pass

    def add_fx(self, kind, rel_start, rel_end, **params):
        c = self.clips[self.cur]
        self.fx.append(dict(kind=kind, clip=self.cur, start=c['start'] + rel_start,
                            end=c['start'] + rel_end, **params))

    def hide(self, joint, rel_start, rel_end):
        """Ukryj czesci jointu (np. wyrzucone pilum) w zakresie klatek [start, end)."""
        c = self.clips[self.cur]
        self.hides.append((joint, c['start'] + rel_start, c['start'] + rel_end))
        self.event(rel_start, 'Hide', joint=joint)
        self.event(rel_end, 'Show', joint=joint)

    # ------------------------------------------------------------ posing
    def key(self, rel, pose):
        c = self.clips[self.cur]
        f = c['start'] + rel
        self.apply(pose)
        for name in self.rig.order:
            if name == 'HumanoidRootPart':
                continue
            e = self.rig.joints[name]
            e.keyframe_insert('rotation_euler', frame=f)
            e.keyframe_insert('location', frame=f)
        for ob, path in getattr(self, '_extra_keys', []):
            ob.keyframe_insert(path, frame=f)
        return f

    def apply(self, pose):
        rig = self.rig
        B = rig.B
        J = rig.joints
        sem = {}

        T = pose.get('T', (0, 0, 0))
        eT = _e(T[0], T[1], T[2])
        sem['Torso'] = eT
        RT = eT.to_matrix()

        H = pose.get('H', (0, 0, 0))
        sem['Head'] = _e(H[0], H[1], H[2])

        arms = {'Right Arm': pose.get('RA', (0, 0, 0)), 'Left Arm': pose.get('LA', (0, 0, 0))}
        fwd = {}
        for name, a in arms.items():
            if name not in J:
                continue
            s = -1 if name.startswith('Right') else 1
            # prawe: ry=+out, rz=+in ; lewe: ry=-out, rz=-in
            sem[name] = _e(-a[0], -s * a[1], -s * a[2])
            fwd[name] = a[0]

        legs = {'Right Leg': pose.get('RL', (0, 0, 0)), 'Left Leg': pose.get('LL', (0, 0, 0))}
        legw = {}
        for name, a in legs.items():
            if name not in J:
                continue
            s = -1 if name.startswith('Right') else 1
            ew = _e(-a[0], -s * a[1], -s * a[2])
            legw[name] = ew.to_matrix()
            loc = (RT.inverted() @ legw[name])
            prev = self._prev.get(name)
            sem[name] = loc.to_euler('XYZ', prev) if prev else loc.to_euler('XYZ')

        # pozostale jointy
        offs = {}
        for name in rig.order:
            if name in sem or name in ('HumanoidRootPart', 'Torso'):
                continue
            v = pose.get(name)
            fol = rig.follow.get(name)
            if v is None:
                v = {}
            if isinstance(v, (tuple, list)):
                sem[name] = _e(*v)
                continue
            r = v.get('r', (0, 0, 0))
            if fol is not None or 'pitch' in v:
                pf = fwd.get(fol, 0.0) if fol else 0.0
                # pitch wzgledem swiata: kompensuje pochylenie tulowia
                rx = pf - v.get('pitch', 0.0) - (T[0] if fol else 0.0)
                sem[name] = _e(rx + r[0], v.get('roll', 0.0) + r[1], v.get('yaw', 0.0) + r[2])
            else:
                sem[name] = _e(*r)
            if 'p' in v:
                offs[name] = Vector(v['p'])

        # peleryna: wisi w dol niezaleznie od pochylenia
        if 'Cape' in J and 'Cape' not in pose:
            sem['Cape'] = _e(-0.8 * T[0] + pose.get('cape', 6.0), -0.4 * T[1], 0)

        # wysokosc korzenia: najnizsza stopa na ziemi
        tp = pose.get('Tp', (0, 0))
        base_loc = Vector((tp[0], -tp[1], 0.0))
        dz = 0.0
        if pose.get('ground', True) and 'Right Leg' in J:
            tpiv = rig.pivots['Torso']
            minz = 1e9
            hw, hd = B['lw'] / 2 - 0.08, B['ld'] / 2 - 0.08
            for name in ('Right Leg', 'Left Leg'):
                hip = tpiv + base_loc + RT @ (rig.pivots[name] - tpiv)
                for cx in (-hw, hw):
                    for cy in (-hd, hd):
                        p = hip + legw[name] @ Vector((cx, cy, -B['ll']))
                        minz = min(minz, p.z)
            dz = -minz
        dz += pose.get('air', 0.0)
        offs['Torso'] = base_loc + Vector((0, 0, dz))

        for name, eul in sem.items():
            e = J[name]
            e.rotation_euler = eul
            self._prev[name] = e.rotation_euler.copy()
        for name in rig.order:
            if name == 'HumanoidRootPart':
                continue
            e = J[name]
            par = rig.parents[name]
            rest = rig.pivots[name] - (rig.pivots[par] if par else Vector((0, 0, 0)))
            e.location = rest + offs.get(name, Vector((0, 0, 0)))

    def finish(self, ease='AUTO_CLAMPED'):
        sc = bpy.context.scene
        sc.frame_start = 0
        sc.frame_end = max(c['end'] for c in self.clips.values())
