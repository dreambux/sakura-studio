"""Modele wysokiej jakosci - zastepuja slabsze wersje (ta sama nazwa w REGISTRY).

Organiczne bryly (zwierzeta, posagi) sa rzezbione modyfikatorem Skin + Subdivision (lib/sculpt.py),
a przedmioty (skrzynie, bronie, domy) maja prawdziwe 3D detale: pojedyncze monety, dachowki, okucia.
Wzorowane na zabytkach: lew z Amfipolis/Cheronei, Sfinks Naksyjczykow (Delfy), helm koryncki,
dom z Olintu (kamienny cokol + cegla mulowa, dziedziniec z pastas, dach z dachowek laconskich).
"""
import math
import random
import sys

import bmesh
from mathutils import Vector, Matrix

from .props import (prop, begin, add, marker, T, F, GOLD, BRONZE, FIRE, FIRE_CORE, GLOW, rock_bm, blob_bm, box, cyl,
                    tube, lathe, recalc, C)
from .sculpt import Skel, xf, tx, cone, aim_rot, bm_at, merge, param_shell, subd, apply_mods
from . import p_arch
from .p_arch import MARBLE, BLOCKS

D2R = math.pi / 180


def IRON():
    return F('iron', (60, 58, 56), 0.45, 0.85)


def IVORY():
    return F('ivory', (226, 214, 188), 0.45)


def DARK_BRONZE():
    return F('bronze_dark', (78, 62, 46), 0.38, 0.9)


def EYE(name='red', rgb=(255, 60, 30), s=6):
    return GLOW('eye_' + name, rgb, s)


def plinth(w, d, h=1.2, mat=None, steps=2, name='ped'):
    """Postument z profilowanym cokolem i gzymsem (jak pod prawdziwymi posagami)."""
    mat = mat or MARBLE()
    z = 0.0
    for k in range(steps):
        e = (steps - k) * 0.35
        add(box(w + e * 2, d + e * 2, 0.35, 0.05), BLOCKS(), loc=(0, 0, z + 0.175), name=name + '_step')
        z += 0.35
    add(box(w + 0.3, d + 0.3, 0.25, 0.06), mat, loc=(0, 0, z + 0.125), name=name + '_base')
    z += 0.25
    add(box(w, d, h, 0.04), mat, loc=(0, 0, z + h / 2), name=name + '_die')
    z += h
    add(box(w + 0.3, d + 0.3, 0.25, 0.06), mat, loc=(0, 0, z + 0.125), name=name + '_cap')
    return z + 0.25


# =================================================================== Cerber
def dog_head(sk, base, M, jaw_open=30, s=1.0):
    """Glowa psa (molos): czaszka, stop, dluga kufa, otwarta zuchwa. M = macierz glowy (+x = przod)."""
    skull = sk.n(tx(M, (0, 0, 0)), 0.5 * s)
    sk.e_(base, skull)
    occ = sk.n(tx(M, (-0.25, 0, 0.16)), 0.4 * s)
    sk.e_(skull, occ)
    stop = sk.n(tx(M, (0.38, 0, 0.05)), 0.34 * s)
    sk.e_(skull, stop)
    muz = sk.n(tx(M, (0.75, 0, -0.02)), 0.26 * s)
    sk.e_(stop, muz)
    nose = sk.n(tx(M, (1.0, 0, -0.02)), 0.2 * s)
    sk.e_(muz, nose)
    a = jaw_open * D2R
    j0 = sk.n(tx(M, (0.2, 0, -0.3)), 0.26 * s)
    sk.e_(skull, j0)
    j1 = sk.n(tx(M, (0.2 + 0.45 * math.cos(a), 0, -0.3 - 0.45 * math.sin(a))), 0.18 * s)
    sk.e_(j0, j1)
    j2 = sk.n(tx(M, (0.2 + 0.75 * math.cos(a), 0, -0.3 - 0.75 * math.sin(a))), 0.13 * s)
    sk.e_(j1, j2)
    return a


def dog_head_details(M, a, mat, tooth, eye, tongue):
    # zeby gorne (kly + siekacze) wzdluz kufy
    for side in (-1, 1):
        for k, (x, L) in enumerate(((0.95, 0.22), (0.78, 0.12), (0.62, 0.11), (0.46, 0.1))):
            p = tx(M, (x, side * (0.13 if k else 0.11), -0.2))
            d = M.to_3x3() @ Vector((0.05, 0, -1))
            add(cone(0.045 if k == 0 else 0.035, L, 6), tooth, loc=p, rot=aim_rot(d), uv='none', name='tooth')
        # dolne kly na zuchwie
        for k, t in enumerate((0.95, 0.6)):
            x = 0.2 + 0.75 * t * math.cos(a)
            z = -0.3 - 0.75 * t * math.sin(a) + 0.1
            p = tx(M, (x, side * 0.1, z))
            d = M.to_3x3() @ Vector((math.sin(a) * 0.3, 0, 1))
            add(cone(0.04, 0.16 if k == 0 else 0.1, 6), tooth, loc=p, rot=aim_rot(d), uv='none', name='tooth')
        # oko pod lukiem brwiowym
        add(C.bm_sphere(0.075, 10, 6), eye, loc=tx(M, (0.36, side * 0.3, 0.2)), name='eye')
        # luk brwiowy
        add(tube([tx(M, (0.2, side * 0.18, 0.36)), tx(M, (0.38, side * 0.33, 0.3)), tx(M, (0.48, side * 0.36, 0.2))],
                 0.07, radii=[0.8, 1, 0.6], res=4), mat, uv='box', name='brow')
        # uszy stojace, spiczaste (jak u molosa straznika)
        base = Vector((-0.08, side * 0.3, 0.36))
        tip = Vector((-0.38, side * 0.5, 0.78))
        bm = C.bm_extrude([(-0.17, 0), (0.17, 0), (0.03, 1.0), (-0.03, 1.0)], 0.07, 0.02, 1)
        bm_at(bm, rot=(90, 0, 0), scale=(1, 1, 1))
        bm_at(bm, scale=(1, 1, (tip - base).length))
        R = (tip - base).normalized().to_track_quat('Z', 'X').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M @ Matrix.Translation(base) @ R, verts=bm.verts)
        add(bm, mat, uv='box', name='ear')
        # nozdrza
        add(C.bm_sphere(0.05, 8, 4), F('void', (14, 10, 10)), loc=tx(M, (0.98, side * 0.08, 0.06)), name='nostril')
    # jezyk
    x0, x1 = 0.3, 0.2 + 0.65 * math.cos(a)
    z1 = -0.3 - 0.65 * math.sin(a) + 0.12
    add(tube([tx(M, (x0, 0, -0.32)), tx(M, ((x0 + x1) / 2, 0, (-0.32 + z1) / 2)), tx(M, (x1, 0, z1))], 0.09,
             radii=[1, 1, 0.7], res=4), tongue, uv='box', name='tongue')
    # gardlo (ciemne wnetrze paszczy)
    add(C.bm_sphere(0.17, 10, 6), F('maw', (40, 12, 12), 0.6), loc=tx(M, (0.35, 0, -0.28)), name='maw')


def spiked_collar(center, normal, R, mat_band, mat_spike, n=10):
    q = Vector(normal).to_track_quat('Z', 'Y')
    rot = tuple(math.degrees(a) for a in q.to_euler())
    add(C.bm_torus(R, 0.09, 28, 8), mat_band, loc=center, rot=rot, scale=(1, 1, 1.6), name='collar')
    Mq = q.to_matrix()
    for k in range(n):
        a = 2 * math.pi * k / n
        d = Mq @ Vector((math.cos(a), math.sin(a), 0))
        p = Vector(center) + d * (R + 0.05)
        add(cone(0.06, 0.2, 6), mat_spike, loc=tuple(p), rot=aim_rot(d), uv='none', name='spike')


@prop('posag_cerbera', 'Unikaty', 'Posag Cerbera - trzyglowy pies (straznik bramy)')
def cerberus():
    begin('posag_cerbera')
    top = plinth(6.0, 3.6, 1.0, T('basalt', 0.7))
    skin = T('bronze', 0.42, 0.9)
    tooth = IVORY()
    eye = EYE('cerb', (255, 70, 30), 7)
    tongue = F('tongue', (150, 40, 45), 0.5)
    W = xf((0, 0, top), (0, 0, -58), 1.0)       # caly pies lekko skrecony do kamery
    sk = Skel()
    # kregoslup: zad -> grzbiet -> klatka (gleboka) -> barki
    pel = sk.n(tx(W, (-1.9, 0, 2.35)), 0.75)
    lum = sk.n(tx(W, (-1.0, 0, 2.4)), 0.7)
    sk.e_(pel, lum)
    chest = sk.n(tx(W, (0.2, 0, 2.5)), 1.0)
    sk.e_(lum, chest)
    brisket = sk.n(tx(W, (0.65, 0, 1.85)), 0.7)
    sk.e_(chest, brisket)
    wither = sk.n(tx(W, (0.75, 0, 3.0)), 0.95)
    sk.e_(chest, wither)
    # trzy szyje (rozchodza sie w wachlarz) i glowy
    heads = []
    for k, (yaw, pitch, L, jaw) in enumerate(((50, 14, 1.3, 35), (0, 38, 1.5, 45), (-50, 10, 1.3, 28))):
        y0 = (1 - k) * 0.5
        nb = sk.n(tx(W, (1.05, y0 * 1.3, 3.3)), 0.6)
        sk.e_(wither, nb)
        d = Vector((math.cos(pitch * D2R) * math.cos(yaw * D2R), math.cos(pitch * D2R) * math.sin(yaw * D2R),
                    math.sin(pitch * D2R)))
        mid = Vector((1.05, y0 * 1.3, 3.3)) + d * L * 0.55 + Vector((0, 0, 0.15))
        nm = sk.n(tx(W, tuple(mid)), 0.52)
        sk.e_(nb, nm)
        hp = Vector((1.05, y0 * 1.3, 3.3)) + d * L + Vector((0, 0, 0.3))
        hb = sk.n(tx(W, tuple(hp)), 0.5)
        sk.e_(nm, hb)
        Mh = W @ Matrix.Translation(hp + Vector((0.15 * math.cos(yaw * D2R), 0.15 * math.sin(yaw * D2R), 0.12))) @ \
            Matrix.Rotation(yaw * D2R, 4, 'Z') @ Matrix.Rotation(-(pitch - 25) * D2R * 0.5, 4, 'Y')
        a = dog_head(sk, hb, Mh, jaw, 1.25)
        heads.append((Mh, a, W @ (Vector((1.05, y0 * 1.3, 3.3)) + d * L * 0.3), W.to_3x3() @ d))
    # nogi przednie (prosto, mocno) - lokiec, nadgarstek, lapa
    for side in (-1, 1):
        y = side * 0.55
        sh = sk.n(tx(W, (0.7, y, 2.4)), 0.58)
        sk.e_(chest, sh)
        sk.chain([(tx(W, (0.55, y * 1.08, 1.45)), 0.42), (tx(W, (0.7, y, 0.7)), 0.3),
                  (tx(W, (0.8, y, 0.32)), 0.28), (tx(W, (1.05, y, 0.22)), 0.32)], sh)
        # tylne: udo (mocne), kolano do przodu, staw skokowy do tylu, lapa
        hp = sk.n(tx(W, (-1.8, y * 0.95, 2.2)), 0.7)
        sk.e_(pel, hp)
        sk.chain([(tx(W, (-1.3, y * 1.08, 1.45)), 0.52), (tx(W, (-2.0, y, 0.9)), 0.3),
                  (tx(W, (-1.95, y, 0.35)), 0.27), (tx(W, (-1.7, y, 0.22)), 0.32)], hp)
    # ogon - waz
    tail = sk.chain([(tx(W, (-2.5, 0, 2.75)), 0.3), (tx(W, (-3.2, 0.2, 3.0)), 0.26), (tx(W, (-3.6, 0.7, 3.6)), 0.22),
                     (tx(W, (-3.4, 1.2, 4.3)), 0.18), (tx(W, (-2.95, 1.35, 4.65)), 0.16),
                     (tx(W, (-2.6, 1.35, 4.6)), 0.19), (tx(W, (-2.3, 1.35, 4.55)), 0.1)], pel)
    add(sk.build(2), skin, uv='box', tile=3, name='body')
    # detale glow, obroze z kolcami
    for Mh, a, cpos, d in heads:
        dog_head_details(Mh, a, skin, tooth, eye, tongue)
        spiked_collar(tuple(cpos), tuple(d), 0.62, F('leather_dark', (60, 36, 24), 0.7), IRON(), 9)
    # pazury
    for side in (-1, 1):
        for xb in (1.05, -1.7):
            for k in (-1, 0, 1):
                p = tx(W, (xb + 0.27, side * 0.55 + k * 0.12, 0.12))
                add(cone(0.05, 0.16, 5), IVORY(), loc=p, rot=aim_rot(W.to_3x3() @ Vector((1, 0, -0.5))), uv='none',
                    name='claw')
    # oczy weza na ogonie
    for s2 in (-1, 1):
        add(C.bm_sphere(0.04, 6, 4), EYE('snake', (255, 220, 60), 6), loc=tx(W, (-2.45, 1.35 + s2 * 0.14, 4.72)),
            name='snake_eye')
    # lancuchy przy cokole
    for side in (-1, 1):
        for k in range(6):
            add(C.bm_torus(0.16, 0.045, 10, 5), IRON(), loc=(side * (2.4 - k * 0.27), -1.95, top - 0.3 - k * 0.12),
                rot=(0, 90 * (k % 2), 0), name='chain')
    marker('Fire', tx(W, (1.9, 0, 5.0)), size=0.6, heat=2)
    marker('Light', tx(W, (1.9, 0, 5.0)), range=12, brightness=1.5, color=[255, 90, 40])


# =================================================================== bron i zbroja (wspolne czesci)
def helm_bm(crest=True, crest_only=False):
    """Helm koryncki: kopula, wyciecia oczu w ksztalcie migdala, nosal, dlugie policzki ze szczelina,
    rozszerzona oslona karku. Jednostka: promien glowy = 1, przod = -Y, srodek glowy w (0,0,0)."""
    def fn(u, v):
        th = 2 * math.pi * u
        if v < 0.5:
            ph = v / 0.5 * math.pi / 2
            rad = math.sin(ph)
            z = 0.35 + math.cos(ph) * 0.95
        else:
            t = (v - 0.5) / 0.5
            z = 0.35 - t * 1.35
            f = max(0.0, math.cos(th)) ** 2
            b = max(0.0, -math.cos(th)) ** 2
            rad = 1 - 0.2 * f * t ** 1.2 + 0.28 * b * t ** 3 - 0.04 * t
        return (rad * math.sin(th) * 1.0, -rad * math.cos(th) * 1.15, z)

    def mask(u, v):
        if v < 0.5:
            return True
        t = (v - 0.5) / 0.5
        a = abs(((2 * math.pi * u + math.pi) % (2 * math.pi)) - math.pi)
        if 0.13 < a < 0.8:
            q = (a - 0.13) / 0.67
            half = 0.13 * max(0.0, 1 - q * q) ** 0.5
            if abs(t - 0.17 - 0.05 * q) < half:
                return False
        if t > 0.42 and a < 0.1 + 0.12 * (t - 0.42):
            return False
        return True
    parts = []
    if not crest_only:
        bm = param_shell(fn, 30, 15, mask, 0.0)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.08)
        parts.append(subd(bm, 1))
    for side in ((-1, 1) if not crest_only else ()):   # wytloczone brwi nad oczami
        pts = []
        for k in range(6):
            a = side * (0.15 + 0.6 * k / 5)
            pts.append((math.sin(a) * 1.07, -math.cos(a) * 1.22, 0.42 + 0.06 * math.sin(k / 5 * math.pi)))
        parts.append(C.bm_tube(pts, 0.05, res=3))
    if crest:
        poly = []
        for k in range(13):
            a = math.radians(-60 + 150 * k / 12)
            poly.append((math.sin(a) * 1.35, 0.35 + math.cos(a) * 1.15))
        for k in range(13):
            a = math.radians(90 - 150 * k / 12)
            r = 2.1 - 0.35 * (k / 12) ** 2
            poly.append((math.sin(a) * r * 1.05, 0.35 + math.cos(a) * r * 0.95 - (0.6 if k < 2 else 0)))
        cb = C.bm_extrude(poly, 0.32, 0.06, 1)
        C.bm_map(cb, lambda c: (c.z, c.x, c.y))
        parts.append(cb)
        st = C.bm_box(0.16, 0.9, 0.3, 0.03, 1)
        C.bm_transform(st, loc=(0, 0.2, 1.38))
        parts.append(st)
    return merge(parts)


def helm(loc, s=0.4, rot=(0, 0, 0), mat=None, crest_mat=None, name='helm'):
    """Helm koryncki (s = promien glowy). Grzebien osobnym materialem (kon. wlosie)."""
    mat = mat or BRONZE()
    bm = helm_bm(False)
    add(bm, mat, loc=loc, rot=rot, scale=(s, s, s), uv='box', tile=2, name=name)
    if crest_mat is not False:
        cb = helm_bm(True, True)
        add(cb, crest_mat or F('crest_red', (150, 30, 26), 0.85), loc=loc, rot=rot, scale=(s, s, s), uv='box',
            tile=2, name=name + '_crest')


def aspis_bm(blazon=None):
    """Tarcza hoplity (aspis): wypukla czasza + plaski, szeroki rant. Os +Z = przod. Promien 1."""
    prof = [(0, 0.2), (0.35, 0.195), (0.6, 0.17), (0.8, 0.12), (0.92, 0.06), (0.98, 0.02), (1.0, 0.0),
            (1.13, 0.0), (1.15, 0.03), (1.13, 0.06), (1.0, 0.05)]
    bm = lathe(prof, 40)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.035)
    return bm


BLAZONS = {
    'lambda': [(-0.5, -0.5), (-0.3, -0.5), (0, 0.22), (0.3, -0.5), (0.5, -0.5), (0.09, 0.5), (-0.09, 0.5)],
    'star': [(math.cos(math.pi / 2 + k * math.pi / 8) * (0.55 if k % 2 == 0 else 0.22),
              math.sin(math.pi / 2 + k * math.pi / 8) * (0.55 if k % 2 == 0 else 0.22)) for k in range(16)],
    'club': [(-0.08, -0.55), (0.08, -0.55), (0.16, 0.2), (0.25, 0.45), (0.12, 0.6), (-0.12, 0.6), (-0.25, 0.45),
             (-0.16, 0.2)],
    'trident': [(-0.05, -0.6), (0.05, -0.6), (0.05, 0.15), (0.3, 0.15), (0.3, 0.6), (0.22, 0.6), (0.22, 0.25),
                (0.05, 0.25), (0.05, 0.62), (-0.05, 0.62), (-0.05, 0.25), (-0.22, 0.25), (-0.22, 0.6), (-0.3, 0.6),
                (-0.3, 0.15), (-0.05, 0.15)],
}


def aspis(loc, s=1.0, rot=(0, 0, 0), face=None, rim=None, blazon='lambda', bmat=None, name='shield'):
    """Tarcza: lico (malowane) + brazowy rant + godlo. rot obraca os +Z (przod tarczy)."""
    face = face or F('shield_red', (150, 34, 28), 0.55)
    rim = rim or BRONZE()
    bm = aspis_bm()
    inner = bmesh.new()
    rimb = bmesh.new()
    # podziel na lico (r<0.97) i rant
    me_faces = [f for f in bm.faces if f.calc_center_median().xy.length > 0.97]
    rb = bm.copy()
    bmesh.ops.delete(bm, geom=me_faces, context='FACES')
    keep = [f for f in rb.faces if f.calc_center_median().xy.length <= 0.97]
    bmesh.ops.delete(rb, geom=keep, context='FACES')
    add(bm, face, loc=loc, rot=rot, scale=(s, s, s), uv='box', tile=2, name=name)
    add(rb, rim, loc=loc, rot=rot, scale=(s, s, s), uv='box', tile=2, name=name + '_rim')
    inner.free()
    rimb.free()
    if blazon:
        poly = BLAZONS[blazon]
        b = C.bm_extrude(poly, 0.04, 0.0, 1)
        prof = [(0, 0.2), (0.35, 0.195), (0.6, 0.17), (0.8, 0.12), (0.92, 0.06)]

        def surf(r):
            for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
                if r <= r1:
                    return z0 + (z1 - z0) * (r - r0) / (r1 - r0)
            return 0.06
        C.bm_map(b, lambda c: (c.x, c.y, surf(math.hypot(c.x, c.y)) + 0.045 + c.z * 0.6))
        add(b, bmat or GOLD(), loc=loc, rot=rot, scale=(s, s, s), uv='none', name=name + '_blazon')


def spear(p0, p1, r=0.07, shaft=None, metal=None, name='spear'):
    """Dory: drzewce, grot w ksztalcie liscia z zebrem, tulejka, sauroter (okucie tylne)."""
    shaft = shaft or T('wood')
    metal = metal or IRON()
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    L = d.length
    dn = d.normalized()
    rot = aim_rot(dn)
    add(cyl(r, L * 0.88, 8, r2=r * 0.85), shaft, loc=tuple(p0 + dn * L * 0.47), rot=rot, uv='none', name=name)
    # grot (lisc): lathe splaszczony
    k = r / 0.07
    blade = lathe([(0, 0), (0.08 * k, 0), (0.075 * k, 0.28 * k), (0.2 * k, 0.6 * k), (0.19 * k, 0.85 * k),
                   (0.0, 1.25 * k)], 12)
    bm_at(blade, scale=(1, 0.22, 1))
    rib = cone(0.045 * k, 1.2 * k, 4)
    blade = merge([blade, rib])
    add(blade, metal, loc=tuple(p0 + dn * L * 0.9), rot=rot, uv='none', name=name + '_tip')
    add(cone(r * 1.05, 0.55 * k, 4), metal, loc=tuple(p0 + dn * 0.55 * k), rot=aim_rot(-dn), uv='none',
        name=name + '_butt')
    add(cyl(r * 1.1, 0.4 * k, 8), metal, loc=tuple(p0 + dn * 0.6 * k), rot=rot, uv='none', name=name + '_ferrule')


def xiphos_bm(L=1.6):
    """Miecz xiphos: lisciasta glownia, jelec, rekojesc z owijka, glowica. Os +Z, rekojesc w z<0."""
    hw = [(0, 0.085), (0.3, 0.078), (0.7, 0.07), (1.1, 0.105), (1.38, 0.075), (1.55, 0.03), (1.6, 0.0)]
    poly = [(w, z * L / 1.6) for z, w in hw] + [(-w, z * L / 1.6) for z, w in reversed(hw)][1:]
    blade = C.bm_extrude(poly, 0.045, 0.012, 1)
    C.bm_map(blade, lambda c: (c.x, c.z, c.y))
    ridge = C.bm_box(0.025, 0.06, L * 0.9, 0.0, 1)
    C.bm_transform(ridge, loc=(0, 0, L * 0.45))
    guard = C.bm_box(0.42, 0.12, 0.09, 0.03, 1)
    C.bm_transform(guard, loc=(0, 0, -0.03))
    grip = C.bm_cyl(0.05, 0.42, 10, r2=0.055)
    C.bm_transform(grip, loc=(0, 0, -0.29))
    pom = C.bm_sphere(0.09, 12, 6)
    C.bm_transform(pom, loc=(0, 0, -0.52), scale=(1.3, 0.8, 0.7))
    return merge([blade, ridge]), merge([guard, pom]), grip


def sword(loc, rot=(0, 0, 0), s=1.0, blade_mat=None, fit=None, grip=None, name='sword'):
    b, f, g = xiphos_bm()
    add(b, blade_mat or IRON(), loc=loc, rot=rot, scale=(s, s, s), uv='none', name=name)
    add(f, fit or BRONZE(), loc=loc, rot=rot, scale=(s, s, s), uv='none', name=name + '_fit')
    add(g, grip or F('leather_dark', (60, 36, 24), 0.7), loc=loc, rot=rot, scale=(s, s, s), uv='none',
        name=name + '_grip')


# =================================================================== rzezbiona postac ludzka (posagi)
def _n(v):
    v = Vector(v)
    return v.normalized()


POSES = {
    # (prawe ramie: [ramie, przedramie], lewe ramie, prawa noga: [udo, golen], lewa noga, pochylenie tulowia, obrot glowy)
    'still': dict(ra=[(-0.12, 0.02, -1), (-0.05, -0.3, -1)], la=[(0.16, 0.06, -1), (0.15, -0.75, -0.6)],
                  rl=[(0.02, 0, -1), (0, 0.02, -1)], ll=[(0.1, -0.14, -1), (0.04, 0.25, -1)], lean=(0, 0), head=8),
    'spear': dict(ra=[(-0.75, -0.1, 0.25), (-0.05, -0.1, 1)], la=[(0.35, -0.25, -0.9), (0.05, -1, 0.1)],
                  rl=[(0.03, 0, -1), (0, 0.02, -1)], ll=[(0.12, -0.2, -1), (0.04, 0.22, -1)], lean=(0, 0), head=-12),
    'arms_up': dict(ra=[(-0.55, -0.05, 0.85), (-0.25, -0.05, 1)], la=[(0.55, -0.05, 0.85), (0.25, -0.05, 1)],
                    rl=[(-0.06, 0, -1), (0, 0, -1)], ll=[(0.06, 0, -1), (0, 0, -1)], lean=(0, 0), head=0),
    'discus': dict(ra=[(-0.4, 0.75, 0.1), (-0.1, 1, 0.45)], la=[(0.35, -0.6, -0.5), (0.0, -0.5, -1)],
                   rl=[(-0.05, -0.35, -1), (0.0, 0.25, -1)], ll=[(0.2, 0.45, -1), (0.0, 0.85, -0.6)],
                   lean=(28, -25), head=-30),
    'lyre': dict(ra=[(-0.12, -0.3, -1), (0.3, -1, 0.15)], la=[(0.3, -0.3, -0.9), (-0.25, -1, 0.35)],
                 rl=[(0.02, 0, -1), (0, 0.02, -1)], ll=[(0.1, -0.14, -1), (0.04, 0.25, -1)], lean=(0, 0), head=10),
    'reach': dict(ra=[(-0.4, -0.6, 0.6), (-0.2, -1, 0.4)], la=[(0.25, 0.1, -1), (0.1, -0.2, -1)],
                  rl=[(0.02, 0, -1), (0, 0.02, -1)], ll=[(0.12, -0.3, -1), (0.0, 0.3, -1)], lean=(-8, 0), head=0),
}


def figure(loc, s=1.0, mat=None, pose='still', rotz=0, name='statue', female=False, helmet=False, beard=False,
           dress=None, shield=False, spear_on=None, cloak=False, wreath=None):
    """Posag czlowieka o heroicznych proporcjach (7.5 glowy), wyrzezbiony Skin + Subsurf.
    Wysokosc ok. 5.3 * s. Przod = -Y (po obrocie rotz)."""
    mat = mat or MARBLE()
    P = POSES[pose]
    lean_x, lean_z = P['lean']
    W = xf(loc, (0, 0, rotz), s)
    T_ = W @ Matrix.Translation((0, 0, 2.62)) @ Matrix.Rotation(lean_z * D2R, 4, 'Z') @ \
        Matrix.Rotation(lean_x * D2R, 4, 'X') @ Matrix.Translation((0, 0, -2.62))
    sk = Skel()
    hipw = 0.34 if female else 0.3
    shw = 0.55 if female else 0.66
    pel = sk.n(tx(W, (0, 0, 2.75)), 0.46 if female else 0.42)
    waist = sk.n(tx(T_, (0, 0.02, 3.2)), 0.33 if female else 0.37)
    sk.e_(pel, waist)
    chest = sk.n(tx(T_, (0, 0.0, 3.72)), 0.45 if female else 0.5)
    sk.e_(waist, chest)
    up = sk.n(tx(T_, (0, 0.04, 4.08)), 0.42 if female else 0.48)
    sk.e_(chest, up)
    neck = sk.n(tx(T_, (0, 0.02, 4.45)), 0.15 if female else 0.18)
    sk.e_(up, neck)
    hr = P['head'] * D2R
    H = T_ @ Matrix.Translation((0, -0.03, 4.82)) @ Matrix.Rotation(hr, 4, 'Z')
    head = sk.n(tx(H, (0, 0.02, 0)), 0.32)
    sk.e_(neck, head)
    crown = sk.n(tx(H, (0, 0.05, 0.13)), 0.29)
    sk.e_(head, crown)
    jaw = sk.n(tx(H, (0, -0.12, -0.18)), 0.17)
    sk.e_(head, jaw)
    if not female:   # miesnie piersiowe i brzuch (rzezba anatomiczna)
        for sx in (-1, 1):
            pc = sk.n(tx(T_, (sx * 0.2, -0.2, 3.85)), 0.27)
            sk.e_(chest, pc)
    else:
        for sx in (-1, 1):
            pc = sk.n(tx(T_, (sx * 0.16, -0.22, 3.82)), 0.2)
            sk.e_(chest, pc)
    hands = {}
    for side, key in ((-1, 'ra'), (1, 'la')):
        sh0 = sk.n(tx(T_, (side * shw * 0.75, 0.04, 4.15)), 0.24 if female else 0.3)
        sk.e_(up, sh0)
        p = Vector((side * shw, 0.04, 4.08))
        a1, a2 = [Vector(d) for d in P[key]]
        a1 = Vector((a1.x, a1.y, a1.z)).normalized()
        a2 = a2.normalized()
        el = p + a1 * 0.95
        wr = el + a2 * 0.82
        hd = wr + a2 * 0.22
        f = 0.85 if female else 1.0
        ids = sk.chain([(tx(T_, tuple(p)), 0.25 * f), (tx(T_, tuple(p + a1 * 0.45)), 0.22 * f),
                        (tx(T_, tuple(el)), 0.155 * f), (tx(T_, tuple(el + a2 * 0.3)), 0.17 * f),
                        (tx(T_, tuple(wr)), 0.1 * f), (tx(T_, tuple(hd)), 0.13 * f)], sh0)
        hands[key] = (Vector(tx(T_, tuple(hd))), (T_.to_3x3() @ a2).normalized())
    feet = {}
    for side, key in ((-1, 'rl'), (1, 'll')):
        p = Vector((side * hipw, 0.0, 2.62))
        l1, l2 = [Vector(d).normalized() for d in P[key]]
        kn = p + l1 * 1.28
        an = kn + l2 * 1.2
        hp = sk.n(tx(W, (side * hipw * 0.8, 0.02, 2.7)), 0.4 if female else 0.37)
        sk.e_(pel, hp)
        sk.chain([(tx(W, tuple(p + l1 * 0.35)), 0.34), (tx(W, tuple(p + l1 * 0.85)), 0.26),
                  (tx(W, tuple(kn)), 0.19), (tx(W, tuple(kn + l2 * 0.35)), 0.22), (tx(W, tuple(an)), 0.12),
                  (tx(W, tuple(an + Vector((0, -0.38, -0.1)))), 0.13)], hp)
        feet[key] = an
    # dopasuj do ziemi: najnizsza kostka na z=0.14
    minz = min(f.z for f in feet.values())
    dz = (0.14 - minz) * s
    G = Matrix.Translation((0, 0, dz))
    body = sk.build(2 if 1.2 <= s < 2.5 else 1, xform=G)
    add(body, mat, uv='box', tile=3, name=name)
    hands = {k: (v[0] + Vector((0, 0, dz)), v[1]) for k, v in hands.items()}
    Hs = G @ H
    # nos, wlosy (loki), broda
    add(cone(0.07 * s, 0.17 * s, 4), mat, loc=tx(Hs, (0, -0.28, 0.0)), rot=aim_rot(Hs.to_3x3() @ Vector((0, -0.4, -1))),
        uv='none', name=name + '_nose')
    rnd = random.Random(int(abs(loc[0] * 7 + loc[1] * 3)) + len(name))
    if not helmet:
        add(C.bm_sphere(0.33 * s, 16, 10), mat, loc=tx(Hs, (0, 0.06, 0.1)), rot=(0, 0, rotz), scale=(1, 1.02, 0.95),
            name=name + '_hair')
        for k in range(16):
            a = math.pi * (0.1 + 0.8 * k / 15)
            add(C.bm_sphere(0.075 * s, 6, 4), mat, loc=tx(Hs, (math.cos(a) * 0.3, -math.sin(a) * 0.22 + 0.02, 0.2)),
                name=name + '_curl')
        if female:
            add(C.bm_sphere(0.17 * s, 10, 6), mat, loc=tx(Hs, (0, 0.33, 0.0)), name=name + '_bun')
            for sx in (-1, 1):
                add(C.bm_tube([tx(Hs, (sx * 0.22, 0.05, -0.1)), tx(Hs, (sx * 0.26, 0.05, -0.45)),
                               tx(Hs, (sx * 0.24, -0.05, -0.75))], 0.06 * s, res=3), mat, uv='none',
                    name=name + '_lock')
    if beard:
        add(blob_bm(0.2 * s, 4, 1, 0.15, (1.0, 0.8, 1.2)), mat, loc=tx(Hs, (0, -0.2, -0.3)), name=name + '_beard')
    if helmet:
        helm(tx(Hs, (0, 0.0, 0.08)), 0.36 * s, (0, 0, rotz + P['head']), mat, mat, name=name + '_helm')
    if wreath:
        add(C.bm_torus(0.31 * s, 0.045 * s, 20, 5), wreath, loc=tx(Hs, (0, 0.03, 0.14)), rot=(8, 0, rotz),
            name=name + '_wreath')
        for k in range(14):
            a = 2 * math.pi * k / 14
            add(C.bm_sphere(0.05 * s, 6, 3), wreath, loc=tx(Hs, (math.cos(a) * 0.31, math.sin(a) * 0.31, 0.15)),
                scale=(1, 1, 0.5), name=name + '_leaf')
    # szaty
    Ws = G @ W
    if dress == 'long' or (dress is None and female):
        def fn(u, v):
            th = 2 * math.pi * u
            z = 4.02 - v * 3.92
            r = 0.47 + 0.12 * v + 0.24 * v ** 2
            r *= 1 + 0.045 * math.sin(th * 18) * v + 0.02 * math.sin(th * 7)
            return tx(Ws, (r * math.cos(th), r * math.sin(th) * 0.85, z))
        add(param_shell(fn, 72, 14, None, 0.0), mat, uv='box', tile=3, name=name + '_peplos')
        def fn2(u, v):   # apoptygma (narzutka do pasa)
            th = 2 * math.pi * u
            z = 4.1 - v * 1.25
            r = 0.52 + 0.1 * v
            r *= 1 + 0.05 * math.sin(th * 14) * v
            return tx(Ws, (r * math.cos(th), r * math.sin(th) * 0.85, z))
        add(param_shell(fn2, 64, 6, None, 0.0), mat, uv='box', tile=3, name=name + '_apopt')
    elif dress == 'short' or (dress is None and not female):
        prof = [(4.2, 0.46), (3.95, 0.56), (3.6, 0.55), (3.3, 0.45), (3.2, 0.47), (2.6, 0.6), (2.0, 0.7)]

        def fn(u, v):
            th = 2 * math.pi * u
            t = v * (len(prof) - 1)
            i = min(int(t), len(prof) - 2)
            f = t - i
            z = prof[i][0] + (prof[i + 1][0] - prof[i][0]) * f
            r = prof[i][1] + (prof[i + 1][1] - prof[i][1]) * f
            fold = max(0.0, (3.2 - z) / 1.2)
            r *= 1 + 0.06 * math.sin(th * 16) * fold + 0.015 * math.sin(th * 9) * (1 - fold)
            return tx(Ws, (r * math.cos(th) * 1.12, r * math.sin(th) * 0.78, z))
        add(param_shell(fn, 64, 18, None, 0.0), mat, uv='box', tile=3, name=name + '_chiton')
        add(C.bm_torus(0.47, 0.06, 28, 5), mat, loc=tx(Ws, (0, 0, 3.25)), rot=(0, 0, rotz), scale=(s * 1.12, s * 0.8, s),
            name=name + '_belt')
    if cloak:
        def fnc(u, v):
            th = math.pi * (0.15 + 0.7 * u)
            z = 4.25 - v * 2.6
            r = 0.62 + 0.25 * v
            r *= 1 + 0.05 * math.sin(u * 40) * v
            return tx(Ws, (math.cos(th) * r * 1.1, math.sin(th) * r * 0.75 + 0.1, z))
        add(param_shell(fnc, 30, 10, None, 0.0, closed_u=False), mat, uv='box', tile=3, name=name + '_cloak')
    if spear_on:
        hp, d = hands[spear_on]
        base = hp - Vector((0, 0, 1)) * 2.6 * s
        base.z = max(base.z, loc[2] + 0.1 * s)
        spear(tuple(base), tuple(hp + Vector((0, 0, 2.6 * s))), 0.07 * s, mat, mat, name=name + '_spear')
    if shield:
        hp, d = hands['la']
        fwd = Vector((0, -1, 0))
        fwd.rotate(Matrix.Rotation(rotz * D2R, 3, 'Z'))
        c = hp - d * 0.35 * s + fwd * 0.15 * s
        aspis(tuple(c), 0.95 * s, aim_rot(fwd), mat, mat, 'lambda' if mat.name.startswith('T_marble') else None, mat,
              name=name + '_shield')
    return hands


def statue_fig_hq(loc, s=1.0, mat=None, pose='spear', rotz=0, name='statue'):
    """Zamiennik dawnego klockowego posagu: ta sama sygnatura, rzezbiona postac."""
    if pose == 'spear':
        return figure(loc, s, mat, 'spear', rotz, name, helmet=True, shield=True, spear_on='ra')
    if pose == 'arms_up':
        return figure(loc, s, mat, 'arms_up', rotz, name, wreath=GOLD() if mat and mat.name.startswith('T_marble') else None)
    return figure(loc, s, mat, 'still', rotz, name, cloak=True, beard=True)


# podmien statue_fig we wszystkich modulach (funkcje propsow szukaja nazwy w globalach modulu przy wywolaniu)
for _mn, _m in list(sys.modules.items()):
    if _mn.startswith(('lib.', 'maps.lib.')) and hasattr(_m, 'statue_fig'):
        _m.statue_fig = statue_fig_hq


# =================================================================== unikaty: helm Hadesa, skrzynia, puszka Pandory
@prop('helm_hadesa', 'Unikaty', 'Helm niewidzialnosci Hadesa (koryncki, czarny braz) na oltarzu z ogniem dusz')
def hades_helm():
    begin('helm_hadesa')
    top = plinth(2.6, 2.6, 1.3, T('basalt', 0.6), 1)
    add(box(2.62, 2.62, 0.22, 0.0), T('meander_gold', 0.5, 0.6), loc=(0, 0, top - 0.85), uv='box', tile=1.3,
        name='band')
    add(cyl(0.9, 0.2, 32), T('marble_dark', 0.4), loc=(0, 0, top + 0.1), uv='box', name='cushion_plate')
    add(blob_bm(0.75, 2, 2, 0.05, (1, 1, 0.35)), T('cloth_purple', 0.9), loc=(0, 0, top + 0.3), name='cushion')
    blk = F('hades_bronze', (34, 30, 34), 0.28, 1.0)
    helm((0, 0, top + 1.25), 0.8, (0, 0, -25), blk, F('hades_crest', (20, 18, 22), 0.9), name='helm')
    # srebrne zdobienia: waz wokol helmu i trupie czaszki na policzkach
    pts = [(math.sin(a) * 0.93, -math.cos(a) * 1.05, top + 1.55 + 0.08 * math.sin(a * 3)) for a in
           [math.radians(-110 + 220 * k / 14) for k in range(15)]]
    M = Matrix.Rotation(-25 * D2R, 4, 'Z')
    pts = [tuple(M @ Vector(p)) for p in pts]
    add(C.bm_tube(pts, 0.06, res=4), F('silver', (200, 205, 215), 0.25, 1.0), uv='none', name='snake')
    for sx in (-1, 1):
        add(C.bm_sphere(0.13, 10, 6), EYE('soul', (120, 255, 160), 5), loc=tuple(M @ Vector((sx * 0.38, -0.95, top + 1.55))),
            scale=(1, 0.5, 0.7), name='eye_glow')
    # dwa koksowniki z zielonym ogniem dusz
    for sx in (-1, 1):
        x = sx * 2.4
        for k in range(3):
            a = 2 * math.pi * k / 3
            add(C.bm_tube([(x + math.cos(a) * 0.5, math.sin(a) * 0.5, 0), (x + math.cos(a) * 0.3, math.sin(a) * 0.3, 1.4),
                           (x + math.cos(a) * 0.45, math.sin(a) * 0.45, 2.0)], 0.06, res=4), blk, uv='none', name='leg')
        add(lathe([(0.15, 0), (0.6, 0.2), (0.7, 0.45), (0.62, 0.45), (0.15, 0.12)], 24), blk, loc=(x, 0, 1.9),
            uv='none', name='bowl')
        flame((x, 0, 2.25), 0.7, 13 + int(sx), 'flame', GLOW('soulfire', (90, 230, 140), 4), GLOW('soulcore', (200, 255, 220), 6))
        marker('Fire', (x, 0, 2.5), size=1.2, heat=4, color=[120, 255, 160])
    marker('Mist', (0, 0, top + 0.6), color=[120, 255, 160])
    marker('Light', (0, 0, top + 1.5), range=12, brightness=1.2, color=[120, 255, 160])


def chest_body(w=2.4, d=1.5, h=1.1, wood=None, metal=None, name='chest'):
    """Skrzynia z desek: osobne deski z przerwami, okucia narozne, nity, zamek, uchwyty."""
    wood = wood or T('wood_dark', 0.8)
    metal = metal or IRON()
    gold = GOLD()
    n = 3
    ph = h / n
    for k in range(n):
        z = ph * (k + 0.5)
        for sy in (-1, 1):
            add(box(w, 0.1, ph - 0.025, 0.02), wood, loc=(0, sy * (d / 2 - 0.05), z), name=name + '_plank')
        for sx in (-1, 1):
            add(box(0.1, d - 0.2, ph - 0.025, 0.02), wood, loc=(sx * (w / 2 - 0.05), 0, z), name=name + '_plank')
    add(box(w - 0.1, d - 0.1, 0.1, 0.0), wood, loc=(0, 0, 0.05), name=name + '_bottom')
    # okucia: pionowe pasy i narozniki z nitami
    for x in (-w * 0.32, w * 0.32):
        for sy in (-1, 1):
            add(box(0.16, 0.04, h + 0.02, 0.01), metal, loc=(x, sy * (d / 2 + 0.02), h / 2), name=name + '_band')
            for z in (0.15, h / 2, h - 0.15):
                add(C.bm_sphere(0.035, 6, 4), metal, loc=(x, sy * (d / 2 + 0.05), z), name=name + '_rivet')
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.12, h - 0.12):
                add(box(0.3, 0.3, 0.24, 0.02), metal, loc=(sx * (w / 2 - 0.12), sy * (d / 2 - 0.12), z),
                    scale=(1, 1, 1), name=name + '_corner') if False else None
                bm = C.bm_extrude([(0, 0), (0.3, 0), (0.3, 0.06), (0.06, 0.06), (0.06, 0.3), (0, 0.3)], 0.25, 0.01, 1)
                add(bm, metal, loc=(sx * (w / 2 + 0.02), sy * (d / 2 + 0.02), z),
                    rot=(0, 0, {(1, 1): 180, (-1, 1): 270, (1, -1): 90, (-1, -1): 0}[(sx, sy)]), uv='none',
                    name=name + '_corner')
        add(C.bm_torus(0.15, 0.03, 14, 5), metal, loc=(sx * (w / 2 + 0.06), 0, h * 0.62), rot=(0, 90, 90),
            name=name + '_handle')
    add(box(0.32, 0.05, 0.4, 0.02), gold, loc=(0, -d / 2 - 0.03, h - 0.22), name=name + '_lock')
    add(box(0.05, 0.02, 0.12, 0.0), F('void', (14, 10, 10)), loc=(0, -d / 2 - 0.06, h - 0.26), name=name + '_key')


def barrel_lid(w, d, open_deg, wood, metal, hinge_z, name='lid'):
    """Wieko beczkowe z 7 deszczulek + boczne polokragle sciany, obrocone na zawiasie (tyl gory)."""
    R = d / 2
    parts = []
    for k in range(7):
        a0 = math.pi * k / 7
        a1 = math.pi * (k + 1) / 7
        am = (a0 + a1) / 2
        L = 2 * R * math.sin(math.pi / 14) - 0.015
        b = C.bm_box(w, L, 0.09, 0.015, 1)
        C.bm_transform(b, rot=(math.degrees(am) - 90, 0, 0))
        C.bm_transform(b, loc=(0, math.cos(am) * (R - 0.045), math.sin(am) * (R - 0.045)))
        parts.append(b)
    for sx in (-1, 1):
        poly = [(math.cos(math.pi * k / 12) * R, math.sin(math.pi * k / 12) * R) for k in range(13)]
        b = C.bm_extrude(poly, 0.1, 0.01, 1)
        C.bm_map(b, lambda c, sx=sx: (c.z + sx * (w / 2 - 0.05), c.x, c.y))
        parts.append(b)
    lid = merge(parts)
    bands = []
    for x in (-w * 0.32, w * 0.32):
        b = C.bm_tube([(x, math.cos(math.pi * k / 10) * (R + 0.01), math.sin(math.pi * k / 10) * (R + 0.01)) for k in
                       range(11)], 0.035, res=2, smooth=False)
        bands.append(b)
    band = merge(bands)
    # zawias na tylnej krawedzi (y=+R, z=0) -> obrot o -open wokol osi X
    Mh = Matrix.Translation((0, R, hinge_z)) @ Matrix.Rotation(-open_deg * D2R, 4, 'X') @ Matrix.Translation((0, -R, 0))
    bmesh.ops.transform(lid, matrix=Mh, verts=lid.verts)
    bmesh.ops.transform(band, matrix=Mh, verts=band.verts)
    add(lid, wood, uv='box', tile=2, name=name)
    add(band, metal, uv='none', name=name + '_band')


def coin_heap(cx, cy, z0, w, d, peak, n, seed, mat, spill=None):
    """Kopiec z pojedynczych monet (kazda to osobny walec) + zloty spod, zeby nie bylo przeswitow."""
    rnd = random.Random(seed)
    coins = []

    def hgt(x, y):
        fx = max(0.0, 1 - (x / (w / 2)) ** 2)
        fy = max(0.0, 1 - (y / (d / 2)) ** 2)
        return peak * (fx * fy) ** 0.7

    under = C.bm_grid(16, 10, w, d)
    C.bm_map(under, lambda c: (c.x, -c.z * 1.0 - d / 2 if False else c.x, 0))
    under = bmesh.new()
    gv = [[under.verts.new((cx + (i / 14 - 0.5) * w, cy + (j / 9 - 0.5) * d,
                            z0 + hgt((i / 14 - 0.5) * w, (j / 9 - 0.5) * d) - 0.05)) for i in range(15)] for j in range(10)]
    for j in range(9):
        for i in range(14):
            under.faces.new((gv[j][i], gv[j][i + 1], gv[j + 1][i + 1], gv[j + 1][i]))
    add(under, F('gold_deep', (170, 120, 40), 0.45, 1.0), uv='none', name='heap_base')
    for k in range(n):
        x = rnd.uniform(-w / 2, w / 2) * 0.96
        y = rnd.uniform(-d / 2, d / 2) * 0.96
        z = z0 + hgt(x, y) + rnd.uniform(-0.02, 0.03)
        c = C.bm_cyl(0.105, 0.028, 9)
        C.bm_transform(c, rot=(rnd.uniform(-35, 35), rnd.uniform(-35, 35), rnd.uniform(0, 360)),
                       loc=(cx + x, cy + y, z))
        coins.append(c)
    if spill:
        for (x, y, z, tilt) in spill:
            c = C.bm_cyl(0.105, 0.028, 9)
            C.bm_transform(c, rot=(tilt[0], tilt[1], rnd.uniform(0, 360)), loc=(x, y, z))
            coins.append(c)
    # monety laczone w paczki (szybciej)
    for i in range(0, len(coins), 60):
        add(merge(coins[i:i + 60]), mat, uv='none', smooth=True, angle=30, name='coins')


def gem(loc, r, rgb, seed=0, name='gem'):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    rnd = random.Random(seed)
    for v in bm.verts:
        v.co.z *= 0.75
    add(bm, F('gem' + str(rgb), rgb, 0.05, 0.0, 0.6), loc=loc, rot=(rnd.uniform(0, 60), rnd.uniform(0, 60), 0),
        smooth=False, uv='none', name=name)


@prop('skrzynia_skarbow', 'Unikaty', 'Otwarta skrzynia pelna zlotych monet, klejnotow i kosztownosci')
def treasure():
    begin('skrzynia_skarbow')
    w, d, h = 2.4, 1.5, 1.1
    chest_body(w, d, h)
    barrel_lid(w, d, 112, T('wood_dark', 0.8), IRON(), h)
    gold = GOLD()
    rnd = random.Random(5)
    spill = []
    for k in range(70):   # wysypane monety przed skrzynia (wachlarz)
        a = rnd.uniform(-1.1, 1.1)
        r = rnd.uniform(0.95, 2.4) ** 1.2
        spill.append((math.sin(a) * r * 1.2, -0.9 - math.cos(a) * r * 0.55, 0.015, (rnd.uniform(-6, 6), rnd.uniform(-6, 6))))
    for k in range(14):   # monety na krawedzi i splywajace po przedniej scianie
        x = rnd.uniform(-0.9, 0.9)
        z = rnd.uniform(0.2, 1.1)
        spill.append((x, -d / 2 - 0.08, z, (rnd.uniform(60, 90), rnd.uniform(-20, 20))))
    # stosy monet obok
    for (sx, sy, nn) in ((1.7, -0.6, 9), (1.95, -0.2, 6), (-1.75, -0.55, 11)):
        for k in range(nn):
            spill.append((sx + rnd.uniform(-0.02, 0.02), sy + rnd.uniform(-0.02, 0.02), 0.015 + k * 0.03,
                          (rnd.uniform(-3, 3), rnd.uniform(-3, 3))))
    coin_heap(0, 0, h - 0.05, w - 0.25, d - 0.25, 0.42, 380, 9, gold, spill)
    for k, c in enumerate(((190, 20, 40), (30, 160, 80), (40, 80, 200), (190, 20, 40), (120, 40, 170),
                           (30, 160, 80), (240, 240, 250), (40, 80, 200))):
        x = rnd.uniform(-0.9, 0.9)
        y = rnd.uniform(-0.5, 0.5)
        gem((x, y, h + 0.3 * (1 - (x / 1.2) ** 2) + 0.07), rnd.uniform(0.08, 0.13), c, k)
    # zloty puchar (kantharos) przewrocony obok i diadem z lisci na kopcu
    add(lathe([(0, 0), (0.22, 0), (0.06, 0.06), (0.05, 0.3), (0.12, 0.35), (0.3, 0.55), (0.32, 0.75), (0.28, 0.75),
               (0.26, 0.57), (0.1, 0.4), (0, 0.4)], 24), gold, loc=(-1.6, -1.2, 0.33), rot=(0, 75, 30), uv='none',
        name='cup')
    add(C.bm_torus(0.35, 0.035, 24, 5), gold, loc=(0.35, 0.05, h + 0.42), rot=(14, 8, 0), name='diadem')
    for k in range(16):
        a = 2 * math.pi * k / 16
        add(C.bm_sphere(0.06, 6, 3), gold, loc=(0.35 + math.cos(a) * 0.35, 0.05 + math.sin(a) * 0.35,
                                                h + 0.42 + math.sin(a) * 0.09), scale=(1.4, 0.7, 0.5), name='leaf')
    # sznur perel przewieszony przez krawedz
    pts = [(-0.6 + 0.05 * k, -d / 2 - 0.05 - 0.02 * math.sin(k / 3), h + 0.05 - 0.45 * math.sin(k / 18 * math.pi))
           for k in range(19)]
    for p in pts:
        add(C.bm_sphere(0.045, 8, 4), F('pearl', (238, 232, 220), 0.25), loc=p, name='pearl')
    marker('Sparkles', (0, 0, 1.6), color=[255, 210, 90])
    marker('Light', (0, -0.3, 1.8), range=8, brightness=0.8, color=[255, 200, 110])


@prop('puszka_pandory', 'Unikaty', 'Puszka Pandory: zdobiona szkatula na lwich lapach, uchylona, fioletowa mgla')
def pandora():
    begin('puszka_pandory')
    top = plinth(3.0, 2.4, 1.4, MARBLE(), 2)
    body = F('pandora_bronze', (70, 54, 44), 0.35, 0.9)
    gold = GOLD()
    w, d, h = 2.0, 1.4, 1.25
    z0 = top + 0.35
    # lwie lapy
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * (w / 2 - 0.12), sy * (d / 2 - 0.12), top)
            add(C.bm_sphere(0.2, 12, 8), gold, loc=(p[0], p[1], top + 0.12), scale=(1, 1.2, 0.7), name='paw')
            add(cyl(0.12, 0.3, 10, r2=0.17), gold, loc=(p[0], p[1], top + 0.25), name='ankle')
            for k in (-1, 0, 1):
                add(C.bm_sphere(0.06, 6, 4), gold, loc=(p[0] + k * 0.09, p[1] + sy * 0.0 - 0.18 * (1 if sy < 0 else -1) * 0 - 0.17,
                                                         top + 0.06), name='toe') if sy < 0 else None
    add(box(w, d, h, 0.04), body, loc=(0, 0, z0 + h / 2), uv='box', tile=2, name='box')
    # panele z reliefem: ramki + meander + srodkowa rozeta
    for sy in (-1, 1):
        add(box(w - 0.3, 0.04, h - 0.35, 0.01), T('meander_gold', 0.4, 0.8), loc=(0, sy * (d / 2 + 0.01), z0 + h / 2),
            uv='box', tile=0.8, name='frieze') if False else None
        for (fw, fh, zz) in ((w - 0.22, 0.08, z0 + 0.12), (w - 0.22, 0.08, z0 + h - 0.12)):
            add(box(fw, 0.06, fh, 0.01), gold, loc=(0, sy * (d / 2 + 0.02), zz), name='trim')
        add(box(w - 0.5, 0.05, h - 0.5, 0.02), T('marble_dark', 0.4), loc=(0, sy * (d / 2 + 0.01), z0 + h / 2),
            uv='box', tile=1.5, name='panel')
        add(C.bm_torus(0.26, 0.04, 24, 5), gold, loc=(0, sy * (d / 2 + 0.05), z0 + h / 2), rot=(90, 0, 0),
            name='rosette_ring')
        for k in range(8):
            a = 2 * math.pi * k / 8
            add(C.bm_sphere(0.08, 8, 4), gold, loc=(math.cos(a) * 0.15, sy * (d / 2 + 0.06), z0 + h / 2 + math.sin(a) * 0.15),
                scale=(1, 0.5, 1), name='petal')
        add(C.bm_sphere(0.09, 10, 6), F('ruby', (180, 20, 40), 0.1, 0.0, 0.8), loc=(0, sy * (d / 2 + 0.08), z0 + h / 2),
            name='gem')
    # narozne pilastry
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(cyl(0.09, h - 0.1, 12), gold, loc=(sx * (w / 2 + 0.02), sy * (d / 2 + 0.02), z0 + h / 2), name='pilaster')
    # wieko dwuspadowe (jak dach swiatyni) z akroterionami, uchylone
    lid = []
    roof = C.bm_extrude([(-d / 2 - 0.1, 0), (d / 2 + 0.1, 0), (d / 2 + 0.1, 0.12), (0, 0.45), (-d / 2 - 0.1, 0.12)],
                        w + 0.2, 0.02, 1)
    C.bm_map(roof, lambda c: (c.z, c.x, c.y))
    Ml = Matrix.Translation((0, d / 2 + 0.1, z0 + h)) @ Matrix.Rotation(-32 * D2R, 4, 'X') @ \
        Matrix.Translation((0, -(d / 2 + 0.1), 0))
    bmesh.ops.transform(roof, matrix=Ml, verts=roof.verts)
    add(roof, body, uv='box', tile=2, name='lid')
    for x in (-w / 2 - 0.1, 0, w / 2 + 0.1):
        a = C.bm_extrude([(-0.14, 0), (0.14, 0), (0, 0.3)], 0.06, 0.01, 1)
        C.bm_map(a, lambda c: (c.z, c.x, c.y))
        C.bm_transform(a, loc=(x, 0, 0.42))
        bmesh.ops.transform(a, matrix=Ml, verts=a.verts)
        add(a, gold, uv='none', name='acroterion')
    edge = C.bm_box(w + 0.24, 0.06, 0.06, 0.01, 1)
    C.bm_transform(edge, loc=(0, -d / 2 - 0.1, 0.06))
    bmesh.ops.transform(edge, matrix=Ml, verts=edge.verts)
    add(edge, gold, uv='none', name='lid_trim')
    # swiatlo i wijace sie smugi dymu ze szczeliny
    glow = GLOW('evil', (160, 70, 235), 4)
    add(box(w - 0.1, d - 0.1, 0.05, 0.0), glow, loc=(0, 0, z0 + h - 0.02), name='inner_glow')
    for k in range(5):
        x0 = -0.7 + k * 0.35
        pts = []
        for j in range(9):
            t = j / 8
            pts.append((x0 + 0.35 * math.sin(t * 7 + k), -0.6 - t * 0.6 + 0.2 * math.cos(t * 5 + k), z0 + h + t * 2.4))
        add(C.bm_tube(pts, 0.11, radii=[1.2 - 0.9 * j / 8 for j in range(9)], res=4), GLOW('evil_smoke', (130, 60, 200), 2.5),
            uv='none', name='wisp')
    # zerwane lancuchy
    for sx in (-1, 1):
        for k in range(5):
            add(C.bm_torus(0.12, 0.035, 10, 5), IRON(), loc=(sx * (w / 2 + 0.3 + k * 0.2), -0.4 + k * 0.12, top + 0.04),
                rot=(90 * (k % 2), 0, 30 * sx), name='chain')
    marker('Smoke', (0, -0.6, z0 + h + 0.5), size=2, opacity=0.5, color=[150, 60, 220])
    marker('Light', (0, -0.6, z0 + h + 0.4), range=12, brightness=1.5, color=[170, 80, 255])



# =================================================================== posagi postaci
def ped_classic(w=3.0, h=2.2, mat=None):
    """Postument z profilowana stopa i gzymsem + inskrypcja (pasek)."""
    mat = mat or MARBLE()
    add(box(w + 0.8, w + 0.8, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='ped_step')
    add(box(w + 0.35, w + 0.35, 0.3, 0.06), mat, loc=(0, 0, 0.55), name='ped_foot')
    add(lathe([(0, 0), (w * 0.62, 0), (w * 0.62, 0.08), (w * 0.57, 0.2), (0, 0.2)], 4), mat, loc=(0, 0, 0.7),
        rot=(0, 0, 45), uv='box', name='ped_mold') if False else None
    add(box(w, w, h, 0.03), mat, loc=(0, 0, 0.7 + h / 2), uv='box', tile=3, name='ped_die')
    add(box(w * 0.7, 0.04, 0.35, 0.0), F('inscription', (150, 140, 128), 0.8), loc=(0, -w / 2 - 0.01, 0.7 + h * 0.62),
        name='ped_text')
    add(box(w + 0.35, w + 0.35, 0.3, 0.06), mat, loc=(0, 0, 0.85 + h), name='ped_cap')
    return h + 1.0


@prop('posag_wojownika', 'Architektura', 'Marmurowy posag hoplity: helm koryncki, aspis, dory')
def statue_warrior():
    begin('posag_wojownika')
    z = ped_classic(3.0, 1.2)
    figure((0, 0, z), 1.35, MARBLE(), 'spear', -15, 'hoplite', helmet=True, shield=True, spear_on='ra')


@prop('posag_zloty', 'Architektura', 'Zloty posag zwyciezcy z wiencem laurowym (Olimp)')
def statue_gold():
    begin('posag_zloty')
    z = ped_classic(3.0, 1.2)
    figure((0, 0, z), 1.35, GOLD(), 'arms_up', -15, 'victor', wreath=GOLD(), cloak=True)


@prop('posag_bogini', 'Architektura', 'Posag Ateny: peplos, helm odsuniety na czolo, wlocznia i tarcza')
def statue_goddess():
    begin('posag_bogini')
    z = ped_classic(3.2, 1.2)
    hands = figure((0, 0, z), 1.4, MARBLE(), 'reach', -15, 'athena', female=True, dress='long')
    # helm koryncki odsuniety na czubek glowy (typowy dla Ateny)
    helm((0.0, 0.08, z + 7.05), 0.5, (-25, 0, -15), MARBLE(), MARBLE(), name='helm')
    hp, d = hands['ra']
    spear((hp.x, hp.y, z + 0.1), (hp.x, hp.y, hp.z + 3.6), 0.1, MARBLE(), MARBLE(), name='spear')
    aspis((1.55, 0.1, z + 1.55), 1.45, (0, -75, -15), MARBLE(), MARBLE(), None, name='shield')
    # sowa u stop
    add(blob_bm(0.32, 3, 2, 0.05, (0.9, 0.8, 1.3)), MARBLE(), loc=(-1.1, -0.9, z + 0.35), name='owl')
    add(C.bm_sphere(0.24, 12, 8), MARBLE(), loc=(-1.1, -0.92, z + 0.85), name='owl_head')


@prop('dyskobol', 'Architektura', 'Dyskobol (rzut dyskiem, wg Myrona) na postumencie')
def discobolus():
    begin('dyskobol')
    z = ped_classic(3.0, 1.0, MARBLE())
    hands = figure((0, 0, z), 1.3, BRONZE(), 'discus', 20, 'athlete', dress='none')
    hp, d = hands['ra']
    add(cyl(0.48, 0.1, 24, bev=0.03), BRONZE(), loc=tuple(hp + d * 0.1), rot=(80, 0, 20), name='discus')


@prop('kora_posag', 'Architektura', 'Kora archaiczna: malowany peplos, warkocze, usmiech')
def kore():
    begin('kora_posag')
    z = ped_classic(2.6, 1.0)
    figure((0, 0, z), 1.25, MARBLE(), 'still', -10, 'kore', female=True, dress='long')
    # malowana bordiura u dolu peplosu (polichromia jak na Korach z Akropolu)
    add(C.bm_torus(0.83, 0.05, 48, 4), F('kore_red', (170, 50, 40), 0.6), loc=(0, 0, z + 0.3),
        scale=(1.25, 1.05, 1), rot=(0, 0, -10), name='paint')


@prop('posag_apollina', 'Architektura', 'Brazowy Apollo z lira (kitharoidos) w himationie')
def apollo():
    begin('posag_apollina')
    z = ped_classic(3.0, 1.2)
    hands = figure((0, 0, z), 1.35, BRONZE(), 'lyre', -15, 'apollo', cloak=True, wreath=GOLD())
    hp, d = hands['la']
    c = hp + Vector((0.05, -0.3, 0.1))
    k_ = 1.3
    # lira: pudlo z muszli zolwia + dwa zakrzywione ramiona + jarzmo + struny
    add(C.bm_sphere(0.32, 14, 8), BRONZE(), loc=tuple(c), scale=(1, 0.45, 0.85), name='lyre_body')
    for sx in (-1, 1):
        add(C.bm_tube([tuple(c + Vector((sx * 0.2, 0, 0.1))), tuple(c + Vector((sx * 0.38, 0, 0.55))),
                       tuple(c + Vector((sx * 0.3, 0, 0.95)))], 0.04, res=4), GOLD(), uv='none', name='lyre_arm')
    add(cyl(0.035, 0.75, 6), GOLD(), loc=tuple(c + Vector((0, 0, 0.9))), rot=(0, 90, 0), uv='none', name='lyre_bar')
    for k in range(5):
        x = -0.16 + k * 0.08
        add(cyl(0.008, 0.7, 4), GOLD(), loc=tuple(c + Vector((x, -0.02, 0.55))), uv='none', name='string')


def wing_bm(span=3.0, chord=1.2, up=0.0, n=13):
    """Skrzydlo: plat (kosc + blona) pokryty zachodzacymi na siebie piorami - lotki, pokrywy duze i male.
    Rozpietosc wzdluz +X, piora zwisaja w -Z (tyl skrzydla)."""
    parts = []

    def edge_z(t):
        return up * t * t * span * 0.4

    for row, (cnt, Lf, zoff, dy) in enumerate(((n, 1.0, 0.0, 0.0), (n - 2, 0.6, 0.06, 0.03), (n - 4, 0.36, 0.1, 0.06))):
        sp = span * 0.92 / cnt
        wd = sp * 1.9
        for k in range(cnt):
            t = (k + 0.5) / cnt
            x = span * (0.04 + 0.92 * t)
            L = chord * Lf * (0.7 + 0.65 * t ** 1.6)
            poly = [(-wd * 0.5, 0.05), (wd * 0.5, 0.05), (wd * 0.52, -L * 0.7), (wd * 0.15, -L), (-wd * 0.3, -L * 0.92),
                    (-wd * 0.5, -L * 0.6)]
            b = C.bm_extrude(poly, 0.03, 0.0, 1)
            C.bm_map(b, lambda c: (c.x, c.z, c.y))
            ang = -(12 + 30 * t) * (1.0 if row == 0 else 0.7)
            C.bm_transform(b, rot=(0, ang, 0))
            C.bm_transform(b, loc=(x, dy + 0.012 * (k % 2), edge_z(t) - zoff))
            parts.append(b)
    memb = []
    for k in range(11):
        t = k / 10
        memb.append((span * (0.0 + 0.95 * t), edge_z(t) + 0.1))
    for k in range(11):
        t = 1 - k / 10
        memb.append((span * 0.95 * t - chord * 0.3 * t, edge_z(t) - chord * (0.5 + 0.2 * t)))
    mb = C.bm_extrude(memb, 0.06, 0.0, 1)
    C.bm_map(mb, lambda c: (c.x, c.z - 0.02, c.y))
    parts.append(mb)
    arm = C.bm_tube([(0, 0, 0.05), (span * 0.45, 0, edge_z(0.45) + 0.12), (span * 0.98, 0, edge_z(1.0) + 0.05)], 0.12,
                    radii=[1.4, 1.0, 0.4], res=4)
    parts.append(arm)
    return merge(parts)


def place_wing(bm, root, yaw, pitch, roll, s=1.0, mirror=False):
    if mirror:
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=bm.verts)
    M = Matrix.Translation(root) @ Matrix.Rotation(yaw * D2R, 4, 'Z') @ Matrix.Rotation(pitch * D2R, 4, 'X') @ \
        Matrix.Rotation(roll * D2R, 4, 'Y') @ Matrix.Scale(s, 4)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm


@prop('nike_skrzydlata', 'Architektura', 'Nike z Samotraki: skrzydlata bogini na dziobie okretu')
def nike():
    begin('nike_skrzydlata')
    from .p_harbor import hull_bm
    # dziob okretu z kamienia (jak oryginal)
    add(box(5.0, 3.0, 1.0, 0.05), BLOCKS(), loc=(0, 0.6, 0.5), name='base')
    bm = hull_bm(7, 2.6, 1.6, 12, 5)
    bm_at(bm, rot=(0, 0, 90))
    add(bm, MARBLE(), loc=(0, 0.6, 1.4), uv='box', tile=3, name='prow')
    add(box(2.6, 3.0, 0.3, 0.04), MARBLE(), loc=(0, 0.9, 2.95), name='deck')
    z = 3.1
    figure((0, 0.3, z), 1.1, MARBLE(), 'reach', 0, 'nike', female=True, dress='long')
    for side in (-1, 1):
        w = wing_bm(3.2, 1.5, 0.9)
        place_wing(w, (side * 0.35, 0.75, z + 4.4), 0, -18, side * -35 + (0 if side > 0 else 0), 1.0, side < 0)
        add(w, MARBLE(), uv='box', tile=3, name='wing')
    # wiatr: rozwiana szata z tylu
    add(C.bm_tube([(0, 1.0, z + 1.0), (0.3, 1.8, z + 0.8), (0.8, 2.4, z + 0.5)], 0.25, radii=[1, 0.8, 0.3]), MARBLE(),
        uv='box', name='drapery')


def bust(loc, s, mat, beard=True, female=False, name='bust'):
    sk = Skel()
    x, y, z = loc
    b = sk.n((x, y, z + 0.0), 0.5 * s)
    c = sk.n((x, y, z + 0.45 * s), 0.62 * s)
    sk.e_(b, c)
    for sx in (-1, 1):
        sh = sk.n((x + sx * 0.6 * s, y + 0.05 * s, z + 0.55 * s), 0.36 * s)
        sk.e_(c, sh)
    nk = sk.n((x, y, z + 1.0 * s), 0.22 * s)
    sk.e_(c, nk)
    hd = sk.n((x, y - 0.03 * s, z + 1.4 * s), 0.36 * s)
    sk.e_(nk, hd)
    cr = sk.n((x, y + 0.04 * s, z + 1.55 * s), 0.34 * s)
    sk.e_(hd, cr)
    jw = sk.n((x, y - 0.13 * s, z + 1.2 * s), 0.2 * s)
    sk.e_(hd, jw)
    add(sk.build(2), mat, uv='box', tile=3, name=name)
    H = Matrix.Translation((x, y - 0.03 * s, z + 1.4 * s)) @ Matrix.Scale(s * 1.1, 4)
    add(cone(0.08 * s, 0.2 * s, 4), mat, loc=tx(H, (0, -0.29, 0.0)), rot=aim_rot((0, -0.4, -1)), uv='none',
        name=name + '_nose')
    add(C.bm_sphere(0.35 * s, 16, 10), mat, loc=tx(H, (0, 0.06, 0.12)), scale=(1, 1.02, 0.92), name=name + '_hair')
    for k in range(16):
        a = math.pi * (0.1 + 0.8 * k / 15)
        add(C.bm_sphere(0.08 * s, 6, 4), mat, loc=tx(H, (math.cos(a) * 0.31, -math.sin(a) * 0.22 + 0.02, 0.22)),
            name=name + '_curl')
    if beard:
        add(blob_bm(0.26 * s, 6, 2, 0.18, (1.0, 0.75, 1.25)), mat, loc=tx(H, (0, -0.18, -0.33)), name=name + '_beard')
        for k in range(9):
            a = math.pi * (0.15 + 0.7 * k / 8)
            add(C.bm_sphere(0.07 * s, 6, 4), mat, loc=tx(H, (math.cos(a) * 0.24, -math.sin(a) * 0.2 - 0.1, -0.45)),
                name=name + '_bcurl')


@prop('popiersie', 'Architektura', 'Popiersie brodatego filozofa na kolumnie z inskrypcja')
def bust_prop():
    begin('popiersie')
    from .props import fluted_column_bm
    add(box(1.8, 1.8, 0.3, 0.04), MARBLE(), loc=(0, 0, 0.15), name='base')
    add(lathe([(0, 0), (0.75, 0), (0.75, 0.12), (0.62, 0.22), (0.62, 0.3), (0, 0.3)], 32), MARBLE(), loc=(0, 0, 0.3),
        uv='box', name='torus')
    add(fluted_column_bm(0.55, 3.0, 16, 0.95, 48, 4), MARBLE(), loc=(0, 0, 0.6), uv='cyl', tile=3, name='shaft')
    add(box(1.4, 1.4, 0.25, 0.04), MARBLE(), loc=(0, 0, 3.72), name='abacus')
    bust((0, 0, 4.35), 1.0, MARBLE(), True)
    add(box(1.0, 0.6, 0.5, 0.04), MARBLE(), loc=(0, 0, 4.05), name='socle')


@prop('herma', 'Architektura', 'Herma: czworoboczny filar z brodata glowa Hermesa')
def herm():
    begin('herma')
    add(box(1.6, 1.6, 0.4, 0.04), BLOCKS(), loc=(0, 0, 0.2), name='base')
    bm = C.bm_box(1.0, 0.85, 3.6, 0.04, 1)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.x *= 0.85
            v.co.y *= 0.85
    add(bm, MARBLE(), loc=(0, 0, 2.2), uv='box', tile=3, name='pillar')
    for sx in (-1, 1):
        add(box(0.2, 0.25, 0.3, 0.04), MARBLE(), loc=(sx * 0.6, 0, 3.6), name='stub')
    bust((0, 0, 3.7), 0.85, MARBLE(), True, name='head')
    add(C.bm_torus(0.33, 0.05, 20, 5), GOLD(), loc=(0, 0.03, 5.15), rot=(8, 0, 0), name='wreath')





# =================================================================== zwierzeta (rzezba)
def build_body(spec, W, sub=2):
    """spec: lista (nazwa, pozycja, promien, rodzic). Zwraca (bmesh, slownik pozycji w swiecie)."""
    sk = Skel()
    ids = {}
    pos = {}
    for nm, p, r, par in spec:
        ids[nm] = sk.n(tx(W, p), r)
        pos[nm] = Vector(tx(W, p))
        if par is not None:
            sk.e_(ids[par], ids[nm])
    return sk.build(sub), pos


def lion_spec(pose='sit'):
    S = []
    a = S.append
    if pose == 'sit':
        a(('rump', (-1.15, 0, 0.95), 0.85, None))
        a(('belly', (-0.5, 0, 1.65), 0.72, 'rump'))
        a(('chest', (0.3, 0, 2.3), 0.82, 'belly'))
        a(('brisk', (0.55, 0, 1.85), 0.6, 'chest'))
        a(('wither', (0.1, 0, 2.85), 0.72, 'chest'))
        a(('neck', (0.55, 0, 3.25), 0.7, 'wither'))
        a(('head', (0.95, 0, 3.55), 0.6, 'neck'))
        for sd in (-1, 1):
            y = sd * 0.5
            a((f'sh{sd}', (0.35, y, 2.3), 0.5, 'chest'))
            a((f'el{sd}', (0.3, y * 1.12, 1.4), 0.36, f'sh{sd}'))
            a((f'wr{sd}', (0.55, y, 0.45), 0.25, f'el{sd}'))
            a((f'pw{sd}', (0.85, y, 0.22), 0.3, f'wr{sd}'))
            a((f'hip{sd}', (-0.95, sd * 0.62, 1.25), 0.68, 'rump'))
            a((f'kn{sd}', (-0.2, sd * 0.8, 0.62), 0.42, f'hip{sd}'))
            a((f'hk{sd}', (-1.35, sd * 0.72, 0.32), 0.27, f'kn{sd}'))
            a((f'hp{sd}', (-0.55, sd * 0.85, 0.2), 0.27, f'hk{sd}'))
    else:   # lezacy (aleja lwow) - brzuch na cokole
        a(('rump', (-1.4, 0, 1.05), 0.8, None))
        a(('belly', (-0.5, 0, 1.05), 0.75, 'rump'))
        a(('chest', (0.4, 0, 1.25), 0.82, 'belly'))
        a(('wither', (0.35, 0, 1.75), 0.68, 'chest'))
        a(('neck', (0.8, 0, 2.15), 0.64, 'wither'))
        a(('head', (1.25, 0, 2.45), 0.55, 'neck'))
        for sd in (-1, 1):
            y = sd * 0.5
            a((f'sh{sd}', (0.5, y, 1.0), 0.48, 'chest'))
            a((f'el{sd}', (0.45, y * 1.1, 0.4), 0.33, f'sh{sd}'))
            a((f'wr{sd}', (1.3, y, 0.25), 0.24, f'el{sd}'))
            a((f'pw{sd}', (1.7, y, 0.22), 0.29, f'wr{sd}'))
            a((f'hip{sd}', (-1.3, sd * 0.6, 0.95), 0.66, 'rump'))
            a((f'kn{sd}', (-0.55, sd * 0.85, 0.45), 0.4, f'hip{sd}'))
            a((f'hk{sd}', (-1.65, sd * 0.75, 0.28), 0.26, f'kn{sd}'))
            a((f'hp{sd}', (-0.95, sd * 0.9, 0.2), 0.26, f'hk{sd}'))
    return S


def lion_head(M, mat, roar=0.4, human=False, stone=True):
    """Pysk lwa: kufa, nos, polotwarta paszcza z klami, oczy pod lukami, uszy; M = macierz glowy."""
    sk = Skel()
    h = sk.n(tx(M, (-0.1, 0, 0.02)), 0.42)
    m = sk.n(tx(M, (0.45, 0, -0.1)), 0.3)
    sk.e_(h, m)
    n = sk.n(tx(M, (0.8, 0, -0.08)), 0.22)
    sk.e_(m, n)
    j0 = sk.n(tx(M, (0.25, 0, -0.32)), 0.2)
    sk.e_(h, j0)
    j1 = sk.n(tx(M, (0.62, 0, -0.38 - roar * 0.3)), 0.13)
    sk.e_(j0, j1)
    add(C.bm_sphere(0.5, 20, 12), mat, loc=tx(M, (0.0, 0, 0.05)), scale=(1.0, 1.05, 0.95), name='cranium')
    add(sk.build(2), mat, uv='box', tile=3, name='lion_head')
    for sd in (-1, 1):
        add(C.bm_sphere(0.08, 10, 6), mat, loc=tx(M, (0.42, sd * 0.24, 0.12)), scale=(1, 1, 0.7), name='eye')
        add(C.bm_tube([tx(M, (0.3, sd * 0.1, 0.27)), tx(M, (0.44, sd * 0.25, 0.25)), tx(M, (0.5, sd * 0.36, 0.14))], 0.07,
                      res=3), mat, uv='none', name='brow')
        add(C.bm_sphere(0.14, 10, 6), mat, loc=tx(M, (-0.12, sd * 0.38, 0.4)), scale=(0.6, 1, 1), name='ear')
        add(C.bm_sphere(0.06, 8, 4), F('void', (14, 10, 10)) if not stone else mat, loc=tx(M, (0.98, sd * 0.09, -0.06)),
            scale=(0.5, 1, 0.6), name='nostril')
        for k, x in enumerate((0.78, 0.62)):
            add(cone(0.045, 0.2 if k == 0 else 0.12, 6), mat, loc=tx(M, (x, sd * 0.12, -0.25)),
                rot=aim_rot(M.to_3x3() @ Vector((0.1, 0, -1))), uv='none', name='fang')
        for k in range(3):   # wasy (bruzdy na kufie)
            add(C.bm_sphere(0.04, 6, 3), mat, loc=tx(M, (0.66 + k * 0.05, sd * (0.22 - k * 0.03), -0.12 - k * 0.04)),
                name='whisker_pad')


def mane(center, M, mat, R=0.95, n=46, seed=1, face_dir=(1, 0, 0)):
    """Grzywa: masywna kryza wokol szyi + warstwy plomienistych lokow przylegajacych i splywajacych w tyl."""
    rnd = random.Random(seed)
    R3 = M.to_3x3()
    fd = (R3 @ Vector(face_dir)).normalized()
    c = Vector(center)
    yaw = math.degrees(math.atan2(fd.y, fd.x))
    add(blob_bm(R * 0.82, seed, 3, 0.06, (1.15, 1.0, 1.05)), mat, loc=tuple(c - fd * 0.2 + Vector((0, 0, -0.12))),
        rot=(0, 0, yaw), uv='box', tile=3, name='ruff')
    golden = math.pi * (3 - math.sqrt(5))
    for k in range(n * 2):
        zz = 1 - 2 * (k + 0.5) / (n * 2)
        r = math.sqrt(max(0.0, 1 - zz * zz))
        ang = golden * k
        d = R3 @ Vector((math.cos(ang) * r, math.sin(ang) * r, zz))
        if d.dot(fd) > 0.45 or d.z < -0.7:
            continue
        p = c + d * R * 0.86
        # kierunek splywu: w tyl (od twarzy) i w dol, stycznie do powierzchni
        flow = (-fd * 0.8 + Vector((0, 0, -0.6)))
        flow = (flow - d * flow.dot(d)).normalized()
        L = rnd.uniform(0.3, 0.42)
        p1 = p + flow * L * 0.5 + d * 0.1
        p2 = p + flow * L + d * 0.05
        add(C.bm_tube([tuple(p), tuple(p1), tuple(p2)], 0.11, radii=[1.0, 0.8, 0.1], res=3), mat, uv='box', tile=3,
            name='lock')


def tail(pts, r, mat, tuft=True, name='tail'):
    add(C.bm_tube(pts, r, radii=[1.0] + [0.7] * (len(pts) - 2) + [0.5], res=4), mat, uv='box', name=name)
    if tuft:
        add(blob_bm(r * 2.2, 3, 1, 0.3, (1.3, 1, 1)), mat, loc=pts[-1], name=name + '_tuft')


def claws(pos, fwd, mat, n=4, s=1.0):
    fwd = Vector(fwd).normalized()
    side = Vector((-fwd.y, fwd.x, 0))
    for k in range(n):
        p = Vector(pos) + fwd * 0.26 * s + side * (k - (n - 1) / 2) * 0.12 * s + Vector((0, 0, -0.08 * s))
        add(C.bm_sphere(0.075 * s, 8, 4), mat, loc=tuple(p), name='toe')


@prop('posag_lwa', 'Architektura', 'Marmurowy lew siedzacy na postumencie (typ lwa z Amfipolis i Cheronei)')
def lion_statue(name='posag_lwa', mat=None, pose='sit', ped=True, yaw=-105):
    begin(name)
    mat = mat or MARBLE()
    z = 0
    if ped:
        add(box(5.2, 3.6, 0.45, 0.05), BLOCKS(), loc=(0, 0, 0.225), name='step')
        add(box(4.6, 3.0, 1.4, 0.04), mat, loc=(0, 0, 1.15), uv='box', tile=3, name='ped')
        add(box(4.9, 3.3, 0.3, 0.05), mat, loc=(0, 0, 2.0), name='cornice')
        z = 2.15
    W = xf((0.2, 0, z), (0, 0, yaw), 1.0)
    bm, P = build_body(lion_spec(pose), W)
    add(bm, mat, uv='box', tile=3, name='body')
    hd = P['head']
    Mh = Matrix.Translation(hd) @ Matrix.Rotation((yaw + (12 if pose == 'sit' else 0)) * D2R, 4, 'Z') @ \
        Matrix.Rotation(4 * D2R, 4, 'Y')
    lion_head(Mh, mat, 0.3)
    mane(tuple(Vector(hd) + Mh.to_3x3() @ Vector((-0.4, 0, -0.25))), Mh, mat, 0.95, 110, 3)
    fwd = W.to_3x3() @ Vector((1, 0, 0))
    for sd in (-1, 1):
        claws(P[f'pw{sd}'], fwd, mat)
        claws(P[f'hp{sd}'], fwd, mat)
    r = P['rump']
    t = [tuple(r + W.to_3x3() @ Vector(v)) for v in ((-0.7, 0, -0.35), (-0.55, 0.85, -0.7), (0.3, 1.15, -0.78),
                                                      (1.0, 1.05, -0.8))]
    tail(t, 0.12, mat)


@prop('sfinks_naksyjski', 'Architektura', 'Sfinks Naksyjczykow (Delfy): kobieca glowa, cialo lwicy, skrzydla, jonska kolumna')
def naxian_sphinx():
    begin('sfinks_naksyjski')
    from .props import fluted_column_bm
    m = MARBLE()
    add(box(3.2, 3.2, 0.5, 0.05), BLOCKS(), loc=(0, 0, 0.25), name='base')
    add(lathe([(0, 0), (1.25, 0), (1.25, 0.15), (1.1, 0.3), (1.15, 0.45), (1.0, 0.55), (0, 0.55)], 40), m,
        loc=(0, 0, 0.5), uv='box', name='spira')
    H = 9.0
    add(fluted_column_bm(0.85, H, 24, 0.9, 72, 6), m, loc=(0, 0, 1.05), uv='cyl', tile=3, name='shaft')
    zc = 1.05 + H
    # wczesny kapitel jonski: szeroki, z duzymi wolutami po bokach
    add(cyl(0.85, 0.3, 32), m, loc=(0, 0, zc + 0.15), name='echinus')
    add(box(3.2, 1.3, 0.45, 0.05), m, loc=(0, 0, zc + 0.5), name='canalis')
    for sx in (-1, 1):
        pts = []
        add(lathe([(0.0, -0.66), (0.62, -0.66), (0.66, -0.6), (0.5, -0.3), (0.45, 0.0), (0.5, 0.3), (0.66, 0.6),
                   (0.62, 0.66), (0.0, 0.66)], 32), m, loc=(sx * 1.25, 0, zc + 0.15), rot=(90, 0, 0), uv='box',
            name='volute_drum')
        for fy in (-1, 1):
            pts = []
            for k in range(48):
                a = k / 47 * 3.2 * math.pi
                rr = 0.58 * (1 - k / 54)
                pts.append((sx * 1.25 + math.cos(a) * rr, fy * 0.69, zc + 0.15 + math.sin(a) * rr))
            add(C.bm_tube(pts, 0.06, res=3), m, uv='none', name='volute')
            add(C.bm_sphere(0.13, 10, 6), m, loc=(sx * 1.25, fy * 0.68, zc + 0.15), scale=(1, 0.5, 1), name='eye')
    add(box(2.0, 1.6, 0.25, 0.04), m, loc=(0, 0, zc + 0.85), name='abacus')
    z = zc + 0.98
    W = xf((0.0, 0, z), (0, 0, -90), 0.85)
    spec = lion_spec('sit')
    spec = [(nm, p, r * (0.85 if nm not in ('head', 'neck') else 0.7), par) for nm, p, r, par in spec]
    spec = [(nm, (p[0], p[1], p[2] + (0.45 if nm in ('neck', 'head') else 0.0)), r, par) for nm, p, r, par in spec]
    bm, P = build_body(spec, W)
    add(bm, m, uv='box', tile=3, name='body')
    # kobieca glowa z archaicznym usmiechem, dlugie warkocze (perlowane), korona
    hd = Vector(P['head']) + Vector((0, 0, 0.2))
    Mh = Matrix.Translation(hd) @ Matrix.Rotation(-90 * D2R, 4, 'Z') @ Matrix.Scale(1.15, 4)
    sk = Skel()
    a_ = sk.n(tx(Mh, (0, 0, 0)), 0.36)
    b_ = sk.n(tx(Mh, (0.15, 0, -0.2)), 0.25)
    sk.e_(a_, b_)
    c_ = sk.n(tx(Mh, (-0.05, 0, 0.15)), 0.36)
    sk.e_(a_, c_)
    add(sk.build(2), m, uv='box', name='face')
    add(cone(0.08, 0.2, 4), m, loc=tx(Mh, (0.33, 0, -0.02)), rot=aim_rot(Mh.to_3x3() @ Vector((0.4, 0, -1))), uv='none',
        name='nose')
    add(lathe([(0, 0), (0.36, 0), (0.42, 0.25), (0, 0.25)], 24), m, loc=tx(Mh, (-0.04, 0, 0.3)), name='polos')
    for sd in (-1, 1):
        for k in range(3):
            pts = [tx(Mh, (-0.15 - k * 0.08, sd * (0.28 + k * 0.03), 0.1)), tx(Mh, (-0.22 - k * 0.1, sd * (0.38 + k * 0.03), -0.4)),
                   tx(Mh, (-0.15 - k * 0.12, sd * (0.42 + k * 0.03), -0.85))]
            for j in range(7):
                t = j / 6
                q = Vector(pts[0]).lerp(Vector(pts[1]), min(1, t * 2)) if t < 0.5 else Vector(pts[1]).lerp(Vector(pts[2]), (t - 0.5) * 2)
                add(C.bm_sphere(0.075, 8, 5), m, loc=tuple(q), name='tress_bead')
    # skrzydla: zakrzywione w gore i do przodu (typowe dla sfinksow archaicznych)
    for sd in (-1, 1):
        w = wing_bm(2.6, 1.0, 1.8, 11)
        place_wing(w, tuple(Vector(P['wither']) + Vector((sd * 0.3, 0.0, 0.2))), 0, 0, -sd * 70 - 0, 0.95, sd < 0)
        bmesh.ops.transform(w, matrix=Matrix.Translation(Vector(P['wither'])) @ Matrix.Rotation(-90 * D2R, 4, 'Z') @
                            Matrix.Rotation(0, 4, 'Z') @ Matrix.Translation(-Vector(P['wither'])), verts=w.verts) if False else None
        add(w, m, uv='box', tile=3, name='wing')
    fwd = W.to_3x3() @ Vector((1, 0, 0))
    for sd in (-1, 1):
        claws(P[f'pw{sd}'], fwd, m, 4, 0.85)
    r = P['rump']
    t = [tuple(r + W.to_3x3() @ Vector(v) * 0.85) for v in ((-0.7, 0, -0.3), (-0.9, 0.6, 0.4), (-0.6, 0.7, 1.3),
                                                          (-0.2, 0.5, 1.6))]
    tail(t, 0.1, m)


def horse_spec(raise_leg=True, rear=False):
    S = []
    a = S.append
    a(('rump', (-1.35, 0, 3.0), 0.72, None))
    a(('back', (-0.35, 0, 3.0), 0.68, 'rump'))
    a(('chest', (0.7, 0, 2.95), 0.74, 'back'))
    a(('brisk', (1.0, 0, 2.45), 0.5, 'chest'))
    a(('neck1', (1.25, 0, 3.55), 0.52, 'chest'))
    a(('neck2', (1.6, 0, 4.25), 0.4, 'neck1'))
    a(('poll', (1.85, 0, 4.7), 0.3, 'neck2'))
    a(('head', (2.15, 0, 4.5), 0.3, 'poll'))
    a(('muz', (2.6, 0, 3.95), 0.21, 'head'))
    a(('jowl', (2.0, 0, 4.25), 0.3, 'head'))
    for sd in (-1, 1):
        y = sd * 0.42
        a((f'sh{sd}', (0.85, y, 2.65), 0.42, 'chest'))
        if raise_leg and sd > 0:
            a((f'el{sd}', (1.05, y, 2.0), 0.26, f'sh{sd}'))
            a((f'kn{sd}', (1.6, y, 1.85), 0.17, f'el{sd}'))
            a((f'ft{sd}', (1.45, y, 1.15), 0.13, f'kn{sd}'))
            a((f'hf{sd}', (1.5, y, 0.95), 0.16, f'ft{sd}'))
        else:
            a((f'el{sd}', (0.82, y, 1.9), 0.26, f'sh{sd}'))
            a((f'kn{sd}', (0.88, y, 1.15), 0.17, f'el{sd}'))
            a((f'ft{sd}', (0.92, y, 0.35), 0.13, f'kn{sd}'))
            a((f'hf{sd}', (0.97, y, 0.12), 0.16, f'ft{sd}'))
        a((f'hip{sd}', (-1.45, sd * 0.45, 2.7), 0.6, 'rump'))
        a((f'st{sd}', (-0.95, sd * 0.5, 1.85), 0.4, f'hip{sd}'))
        a((f'hk{sd}', (-1.75, sd * 0.45, 1.15), 0.18, f'st{sd}'))
        a((f'hft{sd}', (-1.62, sd * 0.45, 0.35), 0.13, f'hk{sd}'))
        a((f'hhf{sd}', (-1.57, sd * 0.45, 0.12), 0.16, f'hft{sd}'))
    return S


def horse(W, mat, raise_leg=True, mane_mat=None, name='horse'):
    bm, P = build_body(horse_spec(raise_leg), W)
    add(bm, mat, uv='box', tile=3, name=name)
    R3 = W.to_3x3()
    # przycieta, stojaca grzywa (jak na rzezbach greckich) - grzebien z pasm
    for k in range(10):
        t = k / 9
        p = Vector(P['neck1']).lerp(Vector(P['poll']), t) + R3 @ Vector((-0.12, 0, 0.36 - 0.1 * t))
        add(box(0.16, 0.14, 0.42 - 0.12 * t, 0.04), mane_mat or mat, loc=tuple(p),
            rot=(0, -40 + 0 * t, math.degrees(math.atan2(R3[1][0], R3[0][0]))), name=name + '_mane')
    # uszy, oczy, nozdrza, wedzidlo
    hd = Vector(P['head'])
    for sd in (-1, 1):
        add(cone(0.09, 0.32, 6), mat, loc=tuple(Vector(P['poll']) + R3 @ Vector((0.0, sd * 0.13, 0.2))),
            rot=aim_rot(R3 @ Vector((0.15, sd * 0.25, 1))), uv='none', name=name + '_ear')
        add(C.bm_sphere(0.06, 8, 5), mat, loc=tuple(hd + R3 @ Vector((0.05, sd * 0.24, 0.05))), name=name + '_eye')
        add(C.bm_sphere(0.05, 8, 4), F('void', (14, 10, 10)), loc=tuple(Vector(P['muz']) + R3 @ Vector((0.17, sd * 0.09, 0.0))),
            name=name + '_nostril')
    add(C.bm_torus(0.24, 0.025, 20, 4), GOLD(), loc=tuple(Vector(P['muz']) + R3 @ Vector((-0.05, 0, 0.05))),
        rot=(90, 0, math.degrees(math.atan2(R3[1][0], R3[0][0]))), name=name + '_bridle')
    r = Vector(P['rump'])
    tail([tuple(r + R3 @ Vector(v)) for v in ((-0.6, 0, 0.1), (-1.0, 0, -0.5), (-1.05, 0, -1.3), (-0.9, 0, -1.9))],
         0.22, mane_mat or mat, False, name=name + '_tail')
    return P


@prop('posag_konia', 'Architektura', 'Brazowy kon z uniesiona noga (jak kon Seleny / z Artemizjonu)')
def horse_statue():
    begin('posag_konia')
    add(box(5.6, 2.6, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='step')
    add(box(5.2, 2.2, 1.5, 0.04), MARBLE(), loc=(0, 0, 1.15), uv='box', tile=3, name='ped')
    add(box(5.4, 2.4, 0.25, 0.05), MARBLE(), loc=(0, 0, 2.0), name='cornice')
    horse(xf((-0.3, 0, 2.12), (0, 0, -30), 1.0), BRONZE(), True)


@prop('posag_pegaza', 'Olimp', 'Pegaz: bialy marmurowy skrzydlaty kon na postumencie ze zlotem')
def pegasus():
    begin('posag_pegaza')
    add(box(5.6, 2.8, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='step')
    add(box(5.2, 2.4, 1.6, 0.04), MARBLE(), loc=(0, 0, 1.2), uv='box', tile=3, name='ped')
    add(box(5.4, 2.6, 0.25, 0.05), GOLD(), loc=(0, 0, 2.1), name='cornice')
    W = xf((-0.3, 0, 2.22), (0, 0, -30), 1.0)
    P = horse(W, MARBLE(), True, GOLD())
    R3 = W.to_3x3()
    for sd in (-1, 1):
        w = wing_bm(3.6, 1.5, 1.2, 13)
        if sd < 0:
            bmesh.ops.transform(w, matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=w.verts)
        # rozpietosc w bok (os Y konia), lekko w gore i do tylu
        M = Matrix.Translation(Vector(P['back']) + R3 @ Vector((0.4, sd * 0.45, 0.55))) @ W.to_3x3().to_4x4() @ \
            Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Rotation(-sd * 35 * D2R, 4, 'Y') @ Matrix.Rotation(15 * D2R, 4, 'X')
        bmesh.ops.transform(w, matrix=M, verts=w.verts)
        add(w, MARBLE(), uv='box', tile=3, name='wing')


@prop('posag_byka', 'Knossos', 'Brazowy byk minojski z rogami w ksztalcie liry')
def bull_statue():
    begin('posag_byka')
    add(box(5.4, 2.8, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='step')
    add(box(5.0, 2.4, 1.3, 0.04), T('plaster_red', 0.8), loc=(0, 0, 1.05), uv='box', tile=3, name='ped')
    add(box(5.2, 2.6, 0.25, 0.05), T('meander_black', 0.6), loc=(0, 0, 1.82), uv='box', tile=1.5, name='cornice')
    W = xf((-0.2, 0, 1.95), (0, 0, -30), 1.0)
    spec = horse_spec(False)
    big = {'rump': 0.85, 'back': 0.88, 'chest': 0.95, 'brisk': 0.75, 'neck1': 0.75, 'neck2': 0.62}
    out = []
    for nm, p, r, par in spec:
        if nm in ('neck2', 'poll'):
            p = (p[0] - 0.25, p[1], p[2] - 0.75)
        if nm in ('head', 'muz', 'jowl'):
            p = (p[0] - 0.2, p[1], p[2] - 1.05)
        if nm in ('back', 'rump', 'chest'):
            p = (p[0], p[1], p[2] - 0.15)
        r = big.get(nm, r * (1.25 if nm.startswith(('el', 'kn', 'st', 'hk', 'hip', 'sh')) else 1.1))
        if nm == 'head':
            r = 0.42
        if nm == 'muz':
            r = 0.3
        out.append((nm, p, r, par))
    bm, P = build_body(out, W)
    m = BRONZE()
    add(bm, m, uv='box', tile=3, name='body')
    R3 = W.to_3x3()
    hd = Vector(P['head'])
    for sd in (-1, 1):
        pts = [tuple(hd + R3 @ Vector(v)) for v in ((-0.05, sd * 0.3, 0.25), (0.0, sd * 0.85, 0.45), (0.25, sd * 1.05, 1.1),
                                                    (0.45, sd * 0.85, 1.55))]
        add(C.bm_tube(pts, 0.13, radii=[1.0, 0.85, 0.5, 0.12], res=4), GOLD(), uv='none', name='horn')
        add(C.bm_sphere(0.16, 10, 6), m, loc=tuple(hd + R3 @ Vector((-0.15, sd * 0.42, 0.05))), scale=(0.5, 1, 0.8),
            name='ear')
        add(C.bm_sphere(0.07, 8, 5), F('void', (14, 10, 10)), loc=tuple(hd + R3 @ Vector((0.12, sd * 0.32, 0.12))), name='eye')
    add(C.bm_torus(0.12, 0.03, 16, 4), GOLD(), loc=tuple(Vector(P['muz']) + R3 @ Vector((0.22, 0, -0.08))),
        rot=(0, 0, math.degrees(math.atan2(R3[1][0], R3[0][0]))), name='nose_ring')
    r = Vector(P['rump'])
    tail([tuple(r + R3 @ Vector(v)) for v in ((-0.8, 0, 0.0), (-0.95, 0, -0.8), (-0.9, 0, -1.6))], 0.09, m)



# =================================================================== domy (typ z Olintu, V-IV w. p.n.e.)
def roof_slope(x0, x1, ye, yr, ze, zr, slab=None, tile=None, n_seg=None, ante=True, name='roof'):
    """Polac dachu z dachowek: plaska warstwa tegul + rzedy imbreksow (polwalce, nakladane odcinkami)
    + antefiksy z palmeta na okapie. Okap na (ye, ze), kalenica na (yr, zr), od x0 do x1."""
    slab = slab or T('roof', 0.8)
    tile = tile or T('terracotta', 0.75)
    E = Vector((0, ye, ze))
    R = Vector((0, yr, zr))
    d = R - E
    L = d.length
    th = math.degrees(math.atan2(d.z, d.y))
    add(box(x1 - x0, L, 0.16, 0.02), slab, loc=((x0 + x1) / 2, (ye + yr) / 2, (ze + zr) / 2 - 0.02), rot=(th, 0, 0),
        uv='box', tile=3, name=name)
    nrm = Vector((0, -d.z, d.y)).normalized()
    if nrm.z < 0:
        nrm = -nrm
    n_seg = n_seg or max(2, int(L / 0.9))
    rows = []
    x = x0 + 0.3
    while x < x1 - 0.15:
        rows.append(x)
        x += 0.58
    cyls = []
    for x in rows:
        for k in range(n_seg):
            a = E + d * (k / n_seg) - d.normalized() * 0.06
            b = E + d * ((k + 1) / n_seg) + d.normalized() * 0.04
            c = C.bm_cyl(0.15, (b - a).length, 8, r2=0.13)
            Mx = Matrix.Translation(Vector((x, 0, 0)) + (a + b) / 2 + nrm * 0.1) @ \
                Vector((b - a)).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
            bmesh.ops.transform(c, matrix=Mx, verts=c.verts)
            cyls.append(c)
    add(merge(cyls), tile, uv='box', tile=2, name=name + '_imbrex')
    if ante:
        af = []
        for x in rows:
            poly = [(-0.17, 0), (0.17, 0), (0.2, 0.18), (0.12, 0.33), (0, 0.38), (-0.12, 0.33), (-0.2, 0.18)]
            b = C.bm_extrude(poly, 0.05, 0.0, 1)
            C.bm_map(b, lambda c: (c.x, c.z, c.y))
            sg = 1.0 if yr > ye else -1.0
            if sg < 0:
                C.bm_transform(b, rot=(0, 0, 180))
            C.bm_transform(b, loc=(x, ye - 0.03 * sg, ze + 0.02))
            af.append(b)
        add(merge(af), T('terracotta_painted', 0.75), uv='box', tile=1, name=name + '_antefix')
    return rows


def gable_roof(x0, x1, y0, y1, ze, zr, wall=None, o=0.6, name='roof'):
    ym = (y0 + y1) / 2
    for s in (-1, 1):
        ye = (y0 - o) if s < 0 else (y1 + o)
        dz = (zr - ze) * o / ((y1 - y0) / 2)
        roof_slope(x0 - o, x1 + o, ye, ym, ze - dz, zr, name=name)
    # kalenica
    segs = []
    x = x0 - o
    while x < x1 + o:
        c = C.bm_cyl(0.22, 0.95, 8, r2=0.19)
        C.bm_transform(c, rot=(0, 90, 0), loc=(x + 0.45, ym, zr + 0.16))
        segs.append(c)
        x += 0.85
    add(merge(segs), T('terracotta', 0.75), uv='box', tile=2, name=name + '_ridge')
    # szczyty (trojkatne sciany)
    if wall is not None:
        for x in (x0, x1):
            b = C.bm_extrude([(y0, 0), (y1, 0), (ym, zr - ze)], 0.5, 0.0, 1)
            C.bm_map(b, lambda c: (c.z, c.x, c.y))
            C.bm_transform(b, loc=(x + (0.25 if x == x0 else -0.25), 0, ze))
            add(b, wall, uv='box', tile=4, name=name + '_gable')


def beam_ends(x0, x1, y, z, step=0.9, name='beam'):
    bms = []
    x = x0 + 0.4
    while x < x1 - 0.2:
        b = C.bm_box(0.24, 0.5, 0.24, 0.03, 1)
        C.bm_transform(b, loc=(x, y, z))
        bms.append(b)
        x += step
    add(merge(bms), T('wood_dark', 0.85), uv='box', tile=2, name=name)


def door(x, y, z=0.0, w=1.8, h=2.7, face=-1, rotz=0, color=None, name='door'):
    """Drzwi dwuskrzydlowe z desek: oscieznice, nadproze-belka, kamienny prog, brazowe cwieki i kolatka."""
    wood = T('wood_dark', 0.8)
    leaf = color or T('wood', 0.8)
    R = Matrix.Rotation(rotz * D2R, 4, 'Z')

    def P(dx, dy, dz):
        return tuple(Vector((x, y, z)) + R.to_3x3() @ Vector((dx, dy * face, dz)))
    add(box(w + 0.6, 0.7, 0.18, 0.03), T('limestone', 0.8), loc=P(0, 0.15, 0.09), rot=(0, 0, rotz), name=name + '_sill')
    add(box(w * 0.98, 0.25, 0.1, 0.0), F('void', (18, 14, 12)), loc=P(0, -0.05, 0.25), rot=(0, 0, rotz), name=name + '_dark') if False else None
    for sx in (-1, 1):
        add(box(0.24, 0.4, h, 0.03), wood, loc=P(sx * (w / 2 + 0.12), 0.05, 0.18 + h / 2), rot=(0, 0, rotz),
            name=name + '_jamb')
    add(box(w + 1.0, 0.45, 0.3, 0.03), wood, loc=P(0, 0.05, 0.18 + h + 0.15), rot=(0, 0, rotz), name=name + '_lintel')
    for sx in (-1, 1):
        for k in range(4):
            add(box(w / 8 - 0.02, 0.12, h - 0.04, 0.015), leaf, loc=P(sx * (w / 16 + k * w / 8), 0.12, 0.18 + h / 2),
                rot=(0, 0, rotz), name=name + '_plank')
        for zz in (0.5, h - 0.4):
            add(box(w / 2 - 0.1, 0.06, 0.16, 0.01), wood, loc=P(sx * w / 4, 0.05, 0.18 + zz), rot=(0, 0, rotz),
                name=name + '_brace')
            for k in range(4):
                add(C.bm_sphere(0.035, 6, 4), BRONZE(), loc=P(sx * (0.15 + k * (w / 2 - 0.3) / 3), 0.01, 0.18 + zz),
                    name=name + '_stud')
        add(C.bm_torus(0.1, 0.02, 12, 4), BRONZE(), loc=P(sx * 0.2, 0.0, 0.18 + h * 0.5), rot=(90, 0, rotz),
            name=name + '_ring')


def window(x, y, z, w=0.9, h=0.8, face=-1, rotz=0, name='win'):
    """Male okno wysoko w scianie: ciemny otwor, drewniana rama z kratka, okiennice."""
    R = Matrix.Rotation(rotz * D2R, 4, 'Z')

    def P(dx, dy, dz):
        return tuple(Vector((x, y, z)) + R.to_3x3() @ Vector((dx, dy * face, dz)))
    add(box(w, 0.12, h, 0.0), F('void', (22, 18, 16)), loc=P(0, -0.02, 0), rot=(0, 0, rotz), name=name + '_hole')
    wood = T('wood_dark', 0.8)
    for sx in (-1, 1):
        add(box(0.1, 0.18, h + 0.2, 0.01), wood, loc=P(sx * (w / 2 + 0.05), 0.03, 0), rot=(0, 0, rotz), name=name + '_frame')
        add(box(w / 2, 0.06, h + 0.05, 0.01), T('wood', 0.8), loc=P(sx * (w * 0.75 + 0.12), 0.1, 0),
            rot=(0, 0, rotz + sx * face * 12), name=name + '_shutter')
    for dz in (-1, 1):
        add(box(w + 0.3, 0.2, 0.12, 0.01), wood, loc=P(0, 0.03, dz * (h / 2 + 0.06)), rot=(0, 0, rotz), name=name + '_frame')
    add(box(0.05, 0.08, h, 0.0), wood, loc=P(0, 0.02, 0), rot=(0, 0, rotz), name=name + '_bar')


def wing(x0, x1, y0, y1, h, wall, socle=1.0, name='wing'):
    add(box(x1 - x0 + 0.16, y1 - y0 + 0.16, socle, 0.05), T('wall_rubble', 0.9), loc=((x0 + x1) / 2, (y0 + y1) / 2, socle / 2),
        uv='box', tile=3, name=name + '_socle')
    add(box(x1 - x0, y1 - y0, h - socle, 0.03), wall, loc=((x0 + x1) / 2, (y0 + y1) / 2, socle + (h - socle) / 2),
        uv='box', tile=4, name=name + '_wall')


def court_house(name, W=16.0, D=14.0, wall_tex='plaster', upper=False, seed=1):
    """Dom z dziedzincem (pastas): skrzydlo polnocne z portykiem, skrzydlo zachodnie, mur z brama od ulicy."""
    begin(name)
    rnd = random.Random(seed)
    wall = T(wall_tex, 0.9)
    x0, x1, y0, y1 = -W / 2, W / 2, -D / 2, D / 2
    H = 4.2
    # dziedziniec (bruk z otoczakow) i odplyw
    add(box(W - 0.2, D - 0.2, 0.12, 0.0), T('cobble_small_warm', 0.9), loc=(0, 0, 0.06), uv='box', tile=4, name='court')
    # skrzydlo polnocne (glowne), dach dwuspadowy
    yn = y1 - 5.0
    wing(x0, x1, yn, y1, H, wall, name='north')
    if upper:
        add(box(W * 0.55, 5.0, 3.0, 0.03), wall, loc=(x0 + W * 0.275, (yn + y1) / 2, H + 1.5), uv='box', tile=4,
            name='upper')
        gable_roof(x0, x0 + W * 0.55, yn, y1, H + 3.0, H + 4.4, wall, name='roof_up')
        roof_slope(x0 + W * 0.55, x1 + 0.6, yn - 0.6, y1 - 1.0, H - 0.2, H + 1.1, name='roof_n')
        beam_ends(x0, x0 + W * 0.55, yn - 0.2, H + 2.75, name='beam_up')
        # drewniany balkon/loggia nad portykiem
        add(box(W * 0.55, 1.6, 0.2, 0.02), T('wood', 0.8), loc=(x0 + W * 0.275, yn - 0.8, H + 0.1), name='balcony')
        for k in range(10):
            add(box(0.1, 0.1, 1.0, 0.0), T('wood_dark', 0.8), loc=(x0 + 0.4 + k * (W * 0.55 - 0.8) / 9, yn - 1.55, H + 0.7),
                name='baluster')
        add(box(W * 0.55, 0.12, 0.12, 0.01), T('wood_dark', 0.8), loc=(x0 + W * 0.275, yn - 1.55, H + 1.2), name='rail')
        window(x0 + W * 0.15, yn - 0.02, H + 1.7, 0.9, 1.0, name='uwin')
        window(x0 + W * 0.4, yn - 0.02, H + 1.7, 0.9, 1.0, name='uwin')
    else:
        gable_roof(x0, x1, yn, y1, H, H + 1.9, wall, name='roof_n')
    beam_ends(x0, x1, yn - 0.2, H - 0.25, name='beam_n')
    # portyk (pastas): drewniane slupy na kamiennych bazach + daszek pulpitowy
    py = yn - 2.0
    for k in range(5):
        x = x0 + 4.4 + k * (W - 5.2) / 4
        add(cyl(0.32, 0.3, 12), T('limestone', 0.8), loc=(x, py, 0.27), name='post_base')
        add(cyl(0.2, H - 0.7, 10, r2=0.18), T('wood', 0.8), loc=(x, py, 0.42 + (H - 0.7) / 2), uv='cyl', name='post')
        add(box(0.6, 0.6, 0.18, 0.02), T('wood_dark', 0.8), loc=(x, py, H - 0.2), name='post_cap')
    add(box(W - 4.4, 0.35, 0.35, 0.02), T('wood_dark', 0.8), loc=(x0 + 4.2 + (W - 4.4) / 2, py, H - 0.05), name='architrave')
    if not upper:
        roof_slope(x0 + 4.0, x1 + 0.4, py - 0.5, yn, H - 0.5 + 0.2, H + 0.25, name='roof_p')
    # skrzydlo zachodnie: dach pulpitowy opadajacy do dziedzinca
    xw = x0 + 4.0
    wing(x0, xw, y0, yn, H - 0.5, wall, name='west')
    rb = C.bm_box(D - 5.0 + 0.6, 4.0 + 1.2, 0.01, 0, 1)
    rows_y = None
    # pulpitowy: okap nad dziedzincem (x = xw + 0.6), kalenica przy zewnetrznym murze (x0)
    # obroc roof_slope o 90 stopni: budujemy w lokalnym ukladzie i przenosimy
    root = begin.__globals__['_CUR']['root']
    before = set(root.children)
    roof_slope(-yn, -(y0 - 0.5), xw + 0.6, x0 - 0.3, H - 0.7, H + 0.7, name='roof_w')
    for ob in set(root.children) - before:
        ob.matrix_world = Matrix.Rotation(-math.pi / 2, 4, 'Z') @ Matrix.Scale(1, 4) @ ob.matrix_world
        ob.matrix_world = Matrix.Diagonal((1, 1, 1, 1)) @ ob.matrix_world
    # mur obwodowy (poludnie + wschod) z daszkiem z dachowek, brama
    for (ax, a0, a1, c) in (('x', xw, x1, y0), ('y', y0, yn, x1)):
        L = a1 - a0
        if ax == 'x':
            add(box(L, 0.6, 1.0, 0.04), T('wall_rubble', 0.9), loc=((a0 + a1) / 2, c, 0.5), uv='box', tile=3, name='fence_socle')
            add(box(L, 0.5, 2.2, 0.03), wall, loc=((a0 + a1) / 2, c, 2.1), uv='box', tile=4, name='fence')
            add(box(L + 0.2, 0.9, 0.16, 0.02), T('roof', 0.8), loc=((a0 + a1) / 2, c, 3.28), name='coping')
        else:
            add(box(0.6, L, 1.0, 0.04), T('wall_rubble', 0.9), loc=(c, (a0 + a1) / 2, 0.5), uv='box', tile=3, name='fence_socle')
            add(box(0.5, L, 2.2, 0.03), wall, loc=(c, (a0 + a1) / 2, 2.1), uv='box', tile=4, name='fence')
            add(box(0.9, L + 0.2, 0.16, 0.02), T('roof', 0.8), loc=(c, (a0 + a1) / 2, 3.28), name='coping')
    # brama w murze poludniowym (prothyron) z daszkiem
    gx = xw + (x1 - xw) * 0.55
    add(box(3.0, 0.62, 3.4, 0.0), F('void', (26, 20, 18)), loc=(gx, y0, 1.7), name='gate_hole') if False else None
    door(gx, y0 - 0.3, 0.0, 1.9, 2.6)
    roof_slope(gx - 1.8, gx + 1.8, y0 - 1.3, y0 + 0.3, 3.35, 3.9, n_seg=2, name='porch_roof')
    # okna w skrzydlach (male, wysoko)
    window(x0 + 2.0, y0 - 0.02, 3.0, 0.8, 0.7)
    for k in range(3):
        window(x0 + 2.5 + k * (W - 4) / 3, y1 + 0.02, 3.2, 0.8, 0.7, face=1)
    # wyposazenie dziedzinca: oltarz Zeusa Herkejosa, studnia/cysterna, amfory, krosno, donica
    add(box(1.1, 0.8, 0.9, 0.04), T('limestone', 0.8), loc=(1.5, -1.0, 0.57), name='altar')
    add(box(1.3, 1.0, 0.15, 0.03), T('limestone', 0.8), loc=(1.5, -1.0, 1.1), name='altar_top')
    add(lathe([(0.0, 0), (0.75, 0), (0.75, 0.75), (0.55, 0.85), (0.5, 0.85), (0.5, 0.12), (0, 0.12)], 24),
        T('limestone', 0.8), loc=(x1 - 2.6, y0 + 2.6, 0.1), uv='box', name='cistern')
    add(cyl(0.48, 0.05, 20), F('water_dark', (30, 50, 60), 0.1), loc=(x1 - 2.6, y0 + 2.6, 0.6), name='cistern_water')
    for k in range(3):
        add(lathe([(0, 0), (0.12, 0), (0.42, 0.45), (0.45, 0.8), (0.3, 1.25), (0.14, 1.35), (0.16, 1.5), (0.12, 1.5),
                   (0, 1.4)], 16), T('terracotta', 0.8), loc=(x1 - 1.0, yn - 1.0 - k * 0.95, 0.12),
            rot=(0, 0, rnd.uniform(0, 90)), uv='cyl', name='amphora')
    add(lathe([(0, 0), (0.5, 0), (0.62, 0.7), (0.55, 0.75), (0, 0.6)], 16), T('terracotta', 0.8), loc=(-1.0, 1.5, 0.12),
        uv='cyl', name='planter')
    add(blob_bm(0.8, 2, 2, 0.25, (1, 1, 0.8)), T('leaf_olive', 0.9), loc=(-1.0, 1.5, 1.4), name='shrub')
    add(cyl(0.4, 0.12, 12), T('wood', 0.8), loc=(-3.0, -2.5, 0.95), name='stool') if False else None
    marker('Smoke', (x0 + 2.0, y1 - 1.0, H + 2.4 if not upper else H + 5.0), size=0.6, opacity=0.3)


prop('dom_grecki', 'Architektura', 'Dom z dziedzincem (Olint): pastas na slupach, dach z dachowek, brama')(
    lambda: court_house('dom_grecki', 16, 14, 'plaster', False, 1))
prop('dom_grecki_pietrowy', 'Architektura', 'Pietrowy dom z dziedzincem, drewniana loggia na pietrze')(
    lambda: court_house('dom_grecki_pietrowy', 16, 14, 'plaster_peeling', True, 2))


@prop('dom_ochra', 'Architektura', 'Wiejski dom z cegly mulowej na kamiennym cokole, z pergola winorosli')
def farm_house():
    begin('dom_ochra')
    wall = T('plaster_ochre', 0.9)
    w, d, H = 9.0, 6.5, 3.8
    wing(-w / 2, w / 2, -d / 2, d / 2, H, wall, 1.1, name='main')
    gable_roof(-w / 2, w / 2, -d / 2, d / 2, H, H + 1.6, wall, 0.55, name='roof')
    beam_ends(-w / 2, w / 2, -d / 2 - 0.2, H - 0.22)
    beam_ends(-w / 2, w / 2, d / 2 + 0.2, H - 0.22)
    door(-1.6, -d / 2 - 0.25, 0.0, 1.5, 2.4)
    window(1.6, -d / 2 - 0.02, 2.6, 0.8, 0.7)
    window(-w / 2 - 0.02, 0.5, 2.6, 0.8, 0.7, rotz=90, face=-1)
    # pergola z winorosla przed domem
    for x in (-3.8, 0.0, 3.8):
        add(cyl(0.14, 2.8, 8), T('wood', 0.8), loc=(x, -d / 2 - 3.2, 1.4), uv='cyl', name='pergola_post')
    for x in (-3.8, 0.0, 3.8):
        add(box(0.16, 3.4, 0.16, 0.01), T('wood_dark', 0.8), loc=(x, -d / 2 - 1.6, 2.85), name='pergola_beam')
    for k in range(7):
        add(cyl(0.05, 8.2, 6), T('wood', 0.8), loc=(0, -d / 2 - 0.3 - k * 0.48, 2.98), rot=(0, 90, 0), uv='none',
            name='pergola_lath')
    rnd = random.Random(4)
    for k in range(9):
        add(blob_bm(0.75, 30 + k, 2, 0.3, (1.3, 1, 0.45)), T('leaf_ivy', 0.9),
            loc=(rnd.uniform(-3.6, 3.6), -d / 2 - rnd.uniform(0.5, 3.0), 3.15), name='vine')
    for k in range(6):
        add(C.bm_sphere(0.16, 8, 6), F('grapes', (90, 40, 110), 0.4), loc=(rnd.uniform(-3, 3), -d / 2 - rnd.uniform(0.6, 2.8), 2.7),
            scale=(1, 1, 1.5), name='grapes')
    # dziedziniec gospodarczy: niski kamienny mur, beczka, kosz, pithos, lawa
    for (x, y, L, rz) in ((w / 2 + 2.5, 0.0, 6.5, 90), (w / 2 + 1.0, d / 2 - 0.1, 3.0, 0)):
        add(box(L, 0.6, 1.2, 0.08), T('wall_rubble', 0.9), loc=(x, y, 0.6), rot=(0, 0, rz), uv='box', tile=3, name='yard_wall')
    add(lathe([(0, 0), (0.3, 0), (0.75, 0.6), (0.8, 1.1), (0.55, 1.6), (0.35, 1.7), (0.38, 1.8), (0, 1.8)], 20),
        T('terracotta', 0.8), loc=(w / 2 + 1.2, -1.5, 0), uv='cyl', name='pithos')
    add(box(2.0, 0.5, 0.12, 0.02), T('wood', 0.8), loc=(1.6, -d / 2 - 1.2, 0.5), name='bench')
    for x in (0.9, 2.3):
        add(box(0.12, 0.4, 0.45, 0.01), T('wood_dark', 0.8), loc=(x, -d / 2 - 1.2, 0.22), name='bench_leg')


@prop('dom_cykladzki', 'Architektura', 'Dom wyspiarski z Akrotiri (Thera): plaski dach, kamienne naroza, okna w ramach z belek')
def akrotiri_house():
    begin('dom_cykladzki')
    wall = T('plaster', 0.9)
    w, d = 10.0, 8.0
    H1, H2 = 3.6, 3.2
    wing(-w / 2, w / 2, -d / 2, d / 2, H1 + H2, wall, 0.8, name='house')
    # kamienne naroza (ciosy) i belki stropowe na zewnatrz (typowe dla Akrotiri)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(8):
                z = 0.8 + k * 0.75
                big = k % 2 == 0
                add(box(1.1 if big else 0.6, 0.6 if big else 1.1, 0.7, 0.04), T('limestone', 0.85),
                    loc=(sx * (w / 2 - (0.5 if big else 0.25)), sy * (d / 2 - (0.25 if big else 0.5)), z + 0.35),
                    scale=(1.02, 1.02, 1), name='quoin')
    for z in (H1, H1 + H2):
        add(box(w + 0.1, 0.25, 0.25, 0.02), T('wood_dark', 0.8), loc=(0, -d / 2 - 0.03, z - 0.12), name='floor_beam')
        add(box(0.25, d + 0.1, 0.25, 0.02), T('wood_dark', 0.8), loc=(-w / 2 - 0.03, 0, z - 0.12), name='floor_beam')
    # okna: duze, w drewnianych ramach (pietro reprezentacyjne), male na parterze
    for x in (-2.8, 0.0, 2.8):
        add(box(1.6, 0.14, 1.7, 0.0), F('void', (22, 18, 16)), loc=(x, -d / 2 - 0.02, H1 + 1.4), name='win_hole')
        for sx in (-1, 1):
            add(box(0.16, 0.24, 2.0, 0.01), T('wood_dark', 0.8), loc=(x + sx * 0.88, -d / 2 - 0.05, H1 + 1.4), name='win_frame')
        for dz in (-1, 1):
            add(box(1.95, 0.24, 0.16, 0.01), T('wood_dark', 0.8), loc=(x, -d / 2 - 0.05, H1 + 1.4 + dz * 0.95), name='win_frame')
        add(box(0.08, 0.1, 1.7, 0.0), T('wood_dark', 0.8), loc=(x, -d / 2 - 0.05, H1 + 1.4), name='win_mullion')
        add(box(1.9, 0.6, 0.12, 0.02), T('limestone', 0.8), loc=(x, -d / 2 - 0.25, H1 + 0.4), name='win_sill')
    window(2.6, -d / 2 - 0.02, 2.3, 0.7, 0.6)
    door(-2.2, -d / 2 - 0.25, 0.0, 1.6, 2.5)
    # malowany fryz (niebieski i ochra) pod dachem
    add(box(w + 0.02, d + 0.02, 0.35, 0.0), T('plaster_blue', 0.8), loc=(0, 0, H1 + H2 - 0.55), uv='box', tile=2, name='frieze')
    add(box(w + 0.04, d + 0.04, 0.12, 0.0), T('plaster_ochre', 0.8), loc=(0, 0, H1 + H2 - 0.82), name='frieze2')
    # plaski dach z ubitej gliny, attyka, schody na dach, dzban i suszone figi
    add(box(w - 0.6, d - 0.6, 0.2, 0.0), T('clay', 0.95), loc=(0, 0, H1 + H2 + 0.0), uv='box', tile=4, name='roof')
    for sx in (-1, 1):
        add(box(0.3, d, 0.6, 0.03), wall, loc=(sx * (w / 2 - 0.15), 0, H1 + H2 + 0.3), name='parapet')
    for sy in (-1, 1):
        add(box(w, 0.3, 0.6, 0.03), wall, loc=(0, sy * (d / 2 - 0.15), H1 + H2 + 0.3), name='parapet')
    for k in range(10):
        add(box(1.4, 0.75, (k + 1) * 0.68, 0.03), wall, loc=(w / 2 + 0.75, d / 2 - 0.5 - k * 0.72, (k + 1) * 0.34),
            uv='box', tile=4, name='stair')
    add(lathe([(0, 0), (0.25, 0), (0.45, 0.5), (0.4, 0.8), (0.2, 1.0), (0.22, 1.1), (0, 1.1)], 16), T('terracotta', 0.8),
        loc=(-3.5, 2.5, H1 + H2 + 0.1), uv='cyl', name='jar')
    add(box(2.0, 1.2, 0.08, 0.0), T('straw', 0.9), loc=(2.0, 2.0, H1 + H2 + 0.12), name='drying_mat')



# =================================================================== bron: stojak, stos tarcz, tropaion, pole bitwy
SHIELD_PAINTS = [((150, 34, 28), 'lambda'), ((30, 30, 34), 'star'), ((200, 170, 90), 'club'), ((40, 70, 130), 'trident'),
                 ((150, 34, 28), 'star'), ((236, 228, 210), 'club')]


def painted_shield(k, loc, s, rot, name='shield'):
    c, bl = SHIELD_PAINTS[k % len(SHIELD_PAINTS)]
    aspis(loc, s, rot, F('shield' + str(c), c, 0.55), BRONZE(), bl, GOLD() if c != (200, 170, 90) else F('black_paint', (24, 22, 22), 0.6),
          name=name)


@prop('stojak_broni', 'Targ', 'Stojak z bronia hoplitow: wlocznie dory, tarcze aspis, helmy korynckie, miecze xiphos')
def weapon_rack():
    begin('stojak_broni')
    wood = T('wood_dark', 0.8)
    L = 5.2
    # dwa koziolki (A) + belki: gorna z wycieciami, dolna
    for x in (-L / 2, L / 2):
        for sy in (-1, 1):
            add(box(0.22, 0.22, 3.4, 0.03), wood, loc=(x, sy * 0.55, 1.6), rot=(sy * 12, 0, 0), name='trestle')
        add(box(0.2, 1.4, 0.18, 0.02), wood, loc=(x, 0, 0.7), name='trestle_bar')
    add(box(L + 0.6, 0.24, 0.24, 0.02), wood, loc=(0, 0, 3.15), name='top_bar')
    add(box(L + 0.2, 0.2, 0.2, 0.02), wood, loc=(0, -0.42, 0.75), name='low_bar')
    add(box(L + 0.2, 0.2, 0.2, 0.02), wood, loc=(0, 0.42, 0.75), name='low_bar')
    # wlocznie oparte o gorna belke (z tylu)
    for k in range(7):
        x = -L / 2 + 0.55 + k * (L - 1.1) / 6
        spear((x, 0.75, 0.05), (x + 0.05, -0.35, 6.2), 0.07, T('wood', 0.8), IRON(), name='spear')
    # tarcze zawieszone na kolkach z przodu
    for k in range(3):
        x = -1.75 + k * 1.75
        add(cyl(0.05, 0.4, 6), wood, loc=(x, -0.3, 2.85), rot=(90, 0, 0), uv='none', name='peg')
        painted_shield(k, (x, -0.68, 1.95), 0.78, (90 - 8, 0, 0), name='shield')
    # helmy na szczytach koziolkow
    for k, x in enumerate((-L / 2, L / 2)):
        helm((x, 0, 3.75), 0.42, (0, 0, -20 if k else 20), BRONZE(),
             F('crest_red', (150, 30, 26), 0.85) if k == 0 else F('crest_black', (24, 22, 22), 0.85), name='helm')
    # miecze w pochwach zawieszone na dolnej belce + skrzynka z mieczami
    for k in range(3):
        sword((-2.2 + k * 0.35, -0.6, 1.25), (0, 180, 0), 0.75, name='sword')
    add(box(1.4, 0.9, 0.6, 0.03), T('wood', 0.8), loc=(1.9, -1.5, 0.3), name='crate')
    for k in range(3):
        sword((1.55 + k * 0.32, -1.5, 0.95), (10 - k * 8, 0, 0), 0.6, name='crate_sword')


@prop('stos_tarcz', 'Wojsko', 'Stos tarcz hoplitow z malowanymi godlami i wlocznie')
def shield_pile():
    begin('stos_tarcz')
    rnd = random.Random(8)
    for k in range(6):
        a = k * 60 + rnd.uniform(-10, 10)
        r = 1.6
        x, y = math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r
        # tarcze oparte o siebie w krag (licem na zewnatrz)
        painted_shield(k, (x * 0.8, y * 0.8, 1.15), 0.95, (90 - 25, 0, a + 90), name='shield')
    for k in range(3):
        painted_shield(k + 2, (rnd.uniform(-2.6, 2.6), -2.6 + k * 0.4, 0.25), 0.9, (rnd.uniform(-6, 6), 0, rnd.uniform(0, 90)),
                       name='flat')
    for k in range(5):
        a = math.radians(k * 72 + 20)
        spear((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.05), (math.cos(a) * -0.2, math.sin(a) * -0.2, 5.0), 0.07,
              name='spear')
    helm((0.0, 0.0, 2.5), 0.45, (0, 0, 30), BRONZE(), F('crest_red', (150, 30, 26), 0.85), name='helm')


@prop('trofeum', 'Wojsko', 'Tropaion: zbroja pokonanego wroga na palu (helm, pancerz miesniowy, tarcza, wlocznie)')
def trophy():
    begin('trofeum')
    wood = T('wood_dark', 0.8)
    add(rock_bm(1.6, 4, 2, 0.25, 0.3, (1.3, 1.1, 0.45)), T('rock', 0.9), loc=(0, 0, 0.2), smooth=False, name='mound')
    add(cyl(0.22, 6.2, 10, r2=0.18), wood, loc=(0, 0, 3.1), uv='cyl', name='post')
    add(cyl(0.16, 3.6, 10), wood, loc=(0, 0, 4.4), rot=(0, 90, 0), uv='cyl', name='crossbar')
    # pancerz miesniowy (rzezba anatomiczna w brazie)
    sk = Skel()
    a = sk.n((0, 0, 3.3), 0.62)
    b = sk.n((0, 0, 4.0), 0.72)
    sk.e_(a, b)
    for sx in (-1, 1):
        c = sk.n((sx * 0.25, -0.28, 4.05), 0.36)
        sk.e_(b, c)
    add(sk.build(2), BRONZE(), uv='box', tile=2, name='cuirass')
    for k in range(10):   # pteryges (paski)
        a_ = math.radians(-80 + k * 18)
        add(box(0.24, 0.06, 0.7, 0.01), T('leather', 0.8), loc=(math.sin(a_) * 0.6, -math.cos(a_) * 0.48, 2.65),
            rot=(0, 0, math.degrees(a_)), name='pteryx')
    helm((0, 0, 5.45), 0.5, (0, 0, 0), BRONZE(), F('crest_black', (24, 22, 22), 0.85), name='helm')
    painted_shield(0, (1.75, -0.2, 3.9), 1.0, (75, 0, -20), name='shield')
    spear((-2.2, 0.4, 0.1), (-0.9, -0.4, 6.0), 0.07, name='spear')
    spear((-1.9, -0.6, 0.1), (-1.3, 0.3, 5.6), 0.07, name='spear')
    sword((-1.75, -0.45, 3.6), (0, 160, 90), 0.8, name='sword')
    add(C.bm_torus(0.25, 0.04, 16, 4), GOLD(), loc=(0, -0.35, 4.75), rot=(90, 0, 0), name='wreath')


@prop('pole_bitwy', 'Wojsko', 'Pobojowisko: wlocznie wbite w ziemie, porzucone tarcze, helmy i miecze')
def battlefield():
    begin('pole_bitwy')
    rnd = random.Random(12)
    add(blob_bm(3.2, 3, 2, 0.1, (1.3, 1.0, 0.08)), T('dirt', 0.95), loc=(0, 0, 0.0), name='trampled')
    for k in range(7):
        x, y = rnd.uniform(-3.2, 3.2), rnd.uniform(-2.4, 2.4)
        tl = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6))
        spear((x, y, -0.2), (x + tl[0] * 3, y + tl[1] * 3, rnd.uniform(3.8, 5.0)), 0.07, name='spear')
    for k in range(5):
        x, y = rnd.uniform(-3.0, 3.0), rnd.uniform(-2.2, 2.2)
        if rnd.random() < 0.5:
            painted_shield(k, (x, y, 0.2), 0.85, (rnd.uniform(-8, 8), 0, rnd.uniform(0, 360)), name='shield_flat')
        else:
            painted_shield(k, (x, y, 0.85), 0.85, (rnd.uniform(55, 75), 0, rnd.uniform(0, 360)), name='shield_lean')
    for k in range(3):
        helm((rnd.uniform(-2.5, 2.5), rnd.uniform(-2, 2), 0.32), 0.38, (rnd.uniform(-80, -40), 0, rnd.uniform(0, 360)),
             BRONZE(), False, name='helm')
    for k in range(3):
        sword((rnd.uniform(-2.5, 2.5), rnd.uniform(-2, 2), 0.06), (90, 0, rnd.uniform(0, 360)), 0.75, name='sword')
    for k in range(10):
        add(rock_bm(rnd.uniform(0.15, 0.35), 70 + k, 1, 0.35, 0.3), T('rock', 0.9),
            loc=(rnd.uniform(-3.5, 3.5), rnd.uniform(-2.6, 2.6), 0.05), smooth=False, name='stone')



# =================================================================== ptaki, kon trojanski
def eagle(loc, s=1.0, yaw=0.0, mat=None, wings_up=40, name='eagle'):
    """Orzel z rozpostartymi skrzydlami: piers, glowa z hakowatym dziobem, wachlarz ogona, szpony."""
    mat = mat or GOLD()
    W = xf(loc, (0, 0, yaw), s)
    sk = Skel()
    a = sk.n(tx(W, (0, 0.35, 0.35)), 0.38)          # ogon/zad
    b = sk.n(tx(W, (0, 0.0, 0.95)), 0.55)            # piers
    sk.e_(a, b)
    c = sk.n(tx(W, (0, -0.25, 1.6)), 0.34)           # szyja
    sk.e_(b, c)
    d = sk.n(tx(W, (0, -0.4, 1.95)), 0.3)            # glowa
    sk.e_(c, d)
    add(sk.build(2), mat, uv='box', name=name)
    R3 = W.to_3x3()
    # dziob hakowaty
    add(C.bm_tube([tx(W, (0, -0.62, 1.98)), tx(W, (0, -0.85, 1.92)), tx(W, (0, -0.92, 1.75))], 0.1 * s,
                  radii=[1.0, 0.7, 0.15], res=4), F('beak_gold', (235, 190, 80), 0.3, 1.0), uv='none', name=name + '_beak')
    for sd in (-1, 1):
        add(C.bm_sphere(0.06 * s, 8, 5), F('void', (14, 10, 10)), loc=tx(W, (sd * 0.2, -0.55, 2.05)), name=name + '_eye')
        add(C.bm_tube([tx(W, (sd * 0.1, -0.45, 2.15)), tx(W, (sd * 0.22, -0.6, 2.1))], 0.05 * s, res=3), mat, uv='none',
            name=name + '_brow')
        w = wing_bm(3.0, 1.3, 0.8, 13)
        if sd < 0:
            bmesh.ops.transform(w, matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=w.verts)
        M = W @ Matrix.Translation((sd * 0.35, 0.05, 1.3)) @ Matrix.Rotation(sd * -wings_up * D2R, 4, 'Y') @ \
            Matrix.Rotation(-12 * D2R, 4, 'X')
        bmesh.ops.transform(w, matrix=M, verts=w.verts)
        add(w, mat, uv='box', tile=2, name=name + '_wing')
        # nogi z piorami ("spodnie") i szpony
        add(C.bm_tube([tx(W, (sd * 0.22, 0.05, 0.6)), tx(W, (sd * 0.24, -0.05, 0.2))], 0.13 * s, radii=[1.2, 0.6], res=4),
            mat, uv='none', name=name + '_leg')
        for k in (-1, 0, 1):
            add(C.bm_tube([tx(W, (sd * 0.24, -0.05, 0.12)), tx(W, (sd * 0.24 + k * 0.12, -0.3, 0.05)),
                           tx(W, (sd * 0.24 + k * 0.14, -0.38, -0.05))], 0.035 * s, radii=[1, 0.8, 0.2], res=3),
                F('talon', (60, 50, 40), 0.4, 0.6), uv='none', name=name + '_talon')
    # ogon - wachlarz pior
    for k in range(7):
        a_ = math.radians(-30 + k * 10)
        poly = [(-0.09, 0), (0.09, 0), (0.1, 0.9), (0, 1.0), (-0.1, 0.9)]
        fb = C.bm_extrude(poly, 0.03, 0.0, 1)
        C.bm_transform(fb, rot=(-60, 0, math.degrees(a_)))
        bmesh.ops.transform(fb, matrix=W @ Matrix.Translation((0, 0.55, 0.3)), verts=fb.verts)
        add(fb, mat, uv='none', name=name + '_tail')


@prop('orzel_zeusa', 'Olimp', 'Zloty orzel Zeusa z rozpostartymi skrzydlami na kolumnie doryckiej')
def eagle_column():
    begin('orzel_zeusa')
    p_arch.column((0, 0, 0), 7.0, 0.7, 'doric', segs=28)
    add(blob_bm(0.7, 3, 2, 0.3, (1.3, 1.0, 0.5)), T('rock_white', 0.8), loc=(0, 0, 8.1), smooth=False, name='perch')
    eagle((0, 0, 8.25), 1.2, -20, GOLD(), 35)
    # piorun w szponach
    add(C.bm_extrude([(-1.2, 0), (-0.2, 0.15), (-0.35, -0.1), (1.2, 0.05), (0.2, -0.1), (0.35, 0.15)], 0.12, 0.02, 1),
        GLOW('bolt', (255, 240, 170), 3), loc=(0, -0.3, 8.35), rot=(90, 0, -20), uv='none', name='bolt')
    marker('Light', (0, -0.3, 8.6), range=10, brightness=1, color=[255, 230, 150])


@prop('kon_trojanski', 'Unikaty', 'Kon trojanski: drewniany, z desek, na platformie z kolami, z ukryta klapa')
def trojan_horse():
    begin('kon_trojanski')
    wood = T('wood', 0.85)
    dark = T('wood_dark', 0.85)
    add(box(6.4, 3.0, 0.5, 0.04), dark, loc=(0, 0, 1.25), uv='box', tile=3, name='platform')
    for k in range(9):
        add(box(0.12, 3.05, 0.52, 0.0), wood, loc=(-3.0 + k * 0.75, 0, 1.25), name='plank_line')
    for sx in (-2.3, 0.0, 2.3):
        for sy in (-1, 1):
            add(C.bm_torus(0.8, 0.14, 24, 6), dark, loc=(sx, sy * 1.65, 0.95), rot=(90, 0, 0), name='wheel')
            for k in range(4):
                add(box(0.1, 0.1, 1.55, 0.0), dark, loc=(sx, sy * 1.65, 0.95), rot=(0, k * 45, 0), name='spoke')
            add(cyl(0.2, 0.3, 10), dark, loc=(sx, sy * 1.65, 0.95), rot=(90, 0, 0), name='hub')
    P = horse(xf((0.2, 0, 1.5), (0, 0, 180), 1.6), wood, False, dark, name='horse')
    # pasy desek (poziome listwy) na tulowiu i klapa
    for k in range(5):
        z = 1.5 + (2.6 + k * 0.38) * 1.6 / 1.6
        add(C.bm_torus(1.05, 0.04, 28, 3), dark, loc=(0.2 + 0.4, 0, 1.5 + (2.55 + k * 0.17) * 1.6 - 1.6 * 0.0),
            rot=(0, 90, 0), scale=(1, 0.75, 1.1), name='band') if False else None
    hatch = Vector(P['back']) + Vector((0, -1.05, -0.2))
    add(box(1.0, 0.1, 0.8, 0.02), dark, loc=tuple(hatch), name='hatch')
    add(box(0.9, 0.12, 0.7, 0.0), F('void', (14, 10, 10)), loc=tuple(hatch + Vector((0.0, -0.02, 0.0))), name='hatch_gap') if False else None
    for k in range(4):
        add(C.bm_sphere(0.04, 6, 4), IRON(), loc=tuple(hatch + Vector((-0.4 + k * 0.27, -0.07, 0.3))), name='nail')
    # liny do ciagniecia
    for sy in (-1, 1):
        add(C.bm_tube([(3.2, sy * 0.8, 1.3), (4.4, sy * 1.0, 0.6), (5.6, sy * 0.9, 0.1)], 0.06, res=3), T('rope', 0.9),
            uv='none', name='rope')



# =================================================================== ogien, oltarz, koksownik, pochodnia, tron
def flame(loc, s=1.0, seed=0, name='flame', mat=None, core_mat=None):
    """Plomien z kilku skreconych jezykow (zewnetrzny pomaranczowy + jasny rdzen)."""
    rnd = random.Random(seed)
    outer, inner = [], []
    for k in range(5):
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.3, 0.3)
        r0 = 0.0 if k == 0 else 0.28
        h = rnd.uniform(0.9, 1.4) * (1.35 if k == 0 else 1.0)
        prof = [(0, 0), (0.32, 0.12), (0.36, 0.3), (0.26, 0.6), (0.12, 0.85), (0.0, 1.0)]
        b = lathe([(r * 0.9, z * h) for r, z in prof], 10)
        tw = rnd.uniform(0.6, 1.2)
        C.bm_map(b, lambda c, tw=tw, h=h: (c.x + math.sin(c.z / h * 3 + tw) * 0.08 * c.z / h,
                                           c.y + math.cos(c.z / h * 2.4 + tw) * 0.08 * c.z / h, c.z))
        C.bm_transform(b, loc=(math.cos(a) * r0, math.sin(a) * r0, 0), rot=(rnd.uniform(-10, 10), rnd.uniform(-10, 10), 0))
        outer.append(b)
    core = lathe([(0, 0), (0.25, 0.1), (0.22, 0.4), (0.1, 0.7), (0, 0.85)], 10)
    add(merge(outer), mat or FIRE(), loc=loc, scale=(s, s, s), uv='none', name=name)
    add(core, core_mat or FIRE_CORE(), loc=loc, scale=(s, s, s), uv='none', name=name + '_core')


@prop('oltarz', 'Architektura', 'Oltarz ofiarny: poduszki z wolutami, fryz tryglifow, rogi, ogien ofiarny')
def altar():
    begin('oltarz')
    m = MARBLE()
    add(box(5.0, 3.2, 0.4, 0.05), BLOCKS(), loc=(0, 0, 0.2), name='step')
    add(box(4.4, 2.6, 0.3, 0.05), m, loc=(0, 0, 0.55), name='plinth')
    add(box(4.0, 2.2, 1.6, 0.03), m, loc=(0, 0, 1.5), uv='box', tile=3, name='body')
    # fryz: tryglify i metopy
    for k in range(9):
        x = -1.8 + k * 0.45
        add(box(0.16, 0.08, 0.5, 0.01), F('triglyph', (60, 70, 100), 0.6) if k % 2 == 0 else m,
            loc=(x, -1.13, 2.0), name='triglyph')
    add(box(4.3, 2.5, 0.2, 0.04), m, loc=(0, 0, 2.4), name='cornice')
    # poduszki (pulvini) z wolutami na krancach
    for sx in (-1, 1):
        add(cyl(0.34, 2.4, 20), m, loc=(sx * 1.85, 0, 2.82), rot=(90, 0, 0), uv='cyl', name='pulvinus')
        for sy in (-1, 1):
            pts = []
            for k in range(30):
                a = k / 29 * 2.6 * math.pi
                rr = 0.32 * (1 - k / 34)
                pts.append((sx * 1.85 + math.cos(a) * rr, sy * 1.22, 2.82 + math.sin(a) * rr))
            add(C.bm_tube(pts, 0.04, res=3), m, uv='none', name='volute')
    add(box(3.0, 1.6, 0.25, 0.02), T('ash', 0.95), loc=(0, 0, 2.6), name='ash')
    for k in range(6):
        add(cyl(0.1, 1.4, 6), T('wood_dark', 0.9), loc=(-0.6 + k * 0.24, 0, 2.8), rot=(90, 0, 15 * (k % 2) - 7), uv='none',
            name='log')
    flame((0, 0, 2.75), 1.25, 3)
    marker('Fire', (0, 0, 3.0), size=3, heat=6)
    marker('Light', (0, 0, 3.6), range=16, brightness=1.6, color=[255, 160, 80])


@prop('koksownik', 'Architektura', 'Koksownik z brazu: trojnog na lwich lapach, misa z zarem i plomieniem')
def brazier():
    begin('koksownik')
    b = BRONZE()
    for k in range(3):
        a = 2 * math.pi * k / 3
        add(C.bm_tube([(math.cos(a) * 0.95, math.sin(a) * 0.95, 0.25), (math.cos(a) * 0.55, math.sin(a) * 0.55, 1.3),
                       (math.cos(a) * 0.5, math.sin(a) * 0.5, 2.0), (math.cos(a) * 0.8, math.sin(a) * 0.8, 2.6)], 0.08,
                      res=4), b, uv='none', name='leg')
        add(C.bm_sphere(0.17, 10, 6), b, loc=(math.cos(a) * 1.0, math.sin(a) * 1.0, 0.12), scale=(1.2, 1.2, 0.8), name='paw')
        add(C.bm_torus(0.12, 0.03, 12, 4), b, loc=(math.cos(a) * 0.52, math.sin(a) * 0.52, 1.65), rot=(90, 0, math.degrees(a)),
            name='ring')
    add(C.bm_torus(0.55, 0.05, 24, 5), b, loc=(0, 0, 1.3), name='brace')
    add(lathe([(0, 0), (0.35, 0), (0.9, 0.25), (1.15, 0.6), (1.25, 0.7), (1.05, 0.7), (0.9, 0.45), (0, 0.35)], 32), b,
        loc=(0, 0, 2.5), uv='box', name='bowl')
    for k in range(10):
        a = 2 * math.pi * k / 10
        add(C.bm_sphere(0.16, 6, 4), F('ember', (255, 90, 20), 0.6, 0.0, 4), loc=(math.cos(a) * 0.55, math.sin(a) * 0.55, 3.05),
            name='ember')
    flame((0, 0, 3.0), 1.0, 7)
    marker('Fire', (0, 0, 3.4), size=3, heat=6)
    marker('Light', (0, 0, 3.8), range=18, brightness=2, color=[255, 160, 80])


@prop('pochodnia', 'Architektura', 'Pochodnia na slupie z brazowym koszem')
def torch():
    begin('pochodnia')
    add(cyl(0.16, 4.0, 10, r2=0.13), T('wood_dark', 0.85), loc=(0, 0, 2.0), uv='cyl', name='pole')
    for z in (0.6, 2.2, 3.8):
        add(C.bm_torus(0.17, 0.03, 12, 4), BRONZE(), loc=(0, 0, z), name='band')
    add(lathe([(0.1, 0), (0.35, 0.3), (0.42, 0.6), (0.38, 0.6), (0.3, 0.32), (0.08, 0.05)], 16), BRONZE(), loc=(0, 0, 4.0),
        name='cup')
    for k in range(6):
        a = 2 * math.pi * k / 6
        add(cyl(0.025, 0.5, 4), BRONZE(), loc=(math.cos(a) * 0.38, math.sin(a) * 0.38, 4.8), uv='none', name='cage')
    flame((0, 0, 4.45), 0.55, 11)
    marker('Fire', (0, 0, 4.7), size=1.5, heat=4)
    marker('Light', (0, 0, 5.0), range=12, brightness=1.5, color=[255, 160, 80])


@prop('tron', 'Architektura', 'Tron Minosa (Knossos): alabastrowy tron o falistym oparciu, freski z gryfami')
def throne():
    begin('tron')
    alab = F('gypsum', (228, 222, 210), 0.45)
    add(box(5.0, 4.0, 0.4, 0.05), T('flagstone_white', 0.85), loc=(0, 0.3, 0.2), uv='box', tile=3, name='dais')
    # siedzisko wyprofilowane + noga z lukiem
    add(box(1.8, 1.4, 0.25, 0.05), alab, loc=(0, 0, 1.5), name='seat')
    bm = C.bm_extrude([(-0.9, 0), (0.9, 0), (0.9, 1.1), (0.55, 1.1), (0.45, 0.55), (0.0, 0.4), (-0.45, 0.55), (-0.55, 1.1),
                       (-0.9, 1.1)], 1.3, 0.04, 1)
    C.bm_transform(bm, rot=(90, 0, 0))
    add(bm, alab, loc=(0, 0.0, 0.4), uv='box', name='base')
    # faliste oparcie (charakterystyczne dla tronu z Knossos)
    poly = [(-0.9, 0)]
    for k in range(25):
        t = k / 24
        y = 1.6 + 0.35 * math.sin(t * math.pi) + 0.18 * math.sin(t * math.pi * 6)
        poly.append((-0.9 + 1.8 * t, y + 0.6 * math.sin(t * math.pi)))
    poly.append((0.9, 0))
    bm = C.bm_extrude(poly, 0.3, 0.03, 1)
    C.bm_transform(bm, rot=(90, 0, 0))
    add(bm, alab, loc=(0, 0.7, 1.55), uv='box', name='back')
    # sciana z freskiem: czerwone tlo, faliste pasy, gryfy w trawie (sylwetki)
    add(box(7.0, 0.5, 4.2, 0.03), T('plaster_red', 0.85), loc=(0, 1.35, 2.5), uv='box', tile=3, name='wall')
    add(box(7.0, 0.52, 0.25, 0.0), T('plaster_blue', 0.8), loc=(0, 1.35, 4.45), name='band')
    # fresk: pas biegnacych spiral i lilie (motywy minojskie)
    for k in range(9):
        pts = []
        cx = -3.0 + k * 0.75
        for j in range(22):
            a = j / 21 * 2.2 * math.pi
            rr = 0.28 * (1 - j / 26)
            pts.append((cx + math.cos(a) * rr, 1.08, 3.6 + math.sin(a) * rr))
        add(C.bm_tube(pts, 0.04, res=2), F('fresco_ochre', (220, 170, 90), 0.8), uv='none', name='spiral')
    for k in range(6):
        x = -2.6 + k * 1.04
        if abs(x) < 1.1:
            continue
        add(cyl(0.03, 1.2, 4), F('fresco_green', (90, 140, 90), 0.8), loc=(x, 1.08, 1.4), uv='none', name='stem')
        for sx in (-1, 1):
            add(C.bm_sphere(0.14, 8, 4), F('fresco_white', (240, 236, 226), 0.8), loc=(x + sx * 0.14, 1.08, 2.05),
                scale=(0.6, 0.3, 1.2), rot=(0, sx * 30, 0), name='lily')
    for sx in (-1, 1):
        add(lathe([(0, 0), (0.45, 0), (0.45, 0.15), (0.3, 0.3), (0.3, 1.0), (0, 1.0)], 20), alab, loc=(sx * 2.2, -0.6, 0.4),
            name='basin')



# =================================================================== targ: worki, namiot, ognisko, pithos
def sack_bm(h=1.1, r=0.5, seed=0):
    """Worek z juty: brzuchaty, zawiazany u gory (wezel + kryza)."""
    rnd = random.Random(seed)
    prof = [(0.0, 0.0), (r * 0.85, 0.02), (r * 1.0, h * 0.25), (r * 0.95, h * 0.6), (r * 0.6, h * 0.82), (r * 0.18, h * 0.9),
            (r * 0.16, h * 0.95), (r * 0.32, h * 1.08), (r * 0.12, h * 1.05), (0, h * 1.0)]
    bm = lathe(prof, 18)
    ph = rnd.uniform(0, 6)
    C.bm_map(bm, lambda c: (c.x * (1 + 0.06 * math.sin(c.z * 7 + ph) + 0.05 * math.sin(math.atan2(c.y, c.x) * 3 + ph)),
                            c.y * (1 + 0.05 * math.cos(c.z * 5 + ph)), c.z))
    return bm


@prop('worki', 'Targ', 'Worki z juty ze zbozem (zawiazane, jeden rozsypany)')
def sacks():
    begin('worki')
    jute = F('jute', (168, 136, 92), 0.95)
    for k, (x, y, rz, tilt) in enumerate(((0, 0, 0, 0), (1.0, 0.2, 30, 0), (0.5, -0.8, 60, 0), (0.45, 0.0, 0, 0))):
        z = 1.05 if k == 3 else 0.0
        add(sack_bm(1.1 if k != 3 else 0.95, 0.5, k), jute, loc=(x, y, z), rot=(tilt, 0, rz), uv='cyl', tile=2, name='sack')
        add(C.bm_torus(0.16, 0.035, 12, 4), T('rope', 0.9), loc=(x, y, z + (0.95 if k != 3 else 0.86) * 1.0),
            name='tie')
    # przewrocony, otwarty worek i rozsypane ziarno
    add(sack_bm(1.0, 0.48, 9), jute, loc=(-1.1, -0.6, 0.45), rot=(0, 95, 200), uv='cyl', tile=2, name='sack_open')
    add(blob_bm(0.6, 5, 2, 0.15, (1.4, 1.0, 0.18)), F('grain', (214, 182, 110), 0.9), loc=(-1.9, -1.0, 0.02), name='grain')
    rnd = random.Random(2)
    for k in range(25):
        add(C.bm_sphere(0.05, 5, 3), F('grain', (214, 182, 110), 0.9),
            loc=(-1.9 + rnd.uniform(-0.9, 0.9), -1.0 + rnd.uniform(-0.7, 0.7), 0.04), scale=(1, 0.6, 0.6), name='seed')
    add(lathe([(0, 0), (0.2, 0), (0.24, 0.25), (0.2, 0.3), (0.19, 0.06), (0, 0.06)], 14), T('wood', 0.8),
        loc=(-1.4, -1.6, 0.0), name='scoop') if False else None


@prop('namiot_wojskowy', 'Targ', 'Namiot wojskowy z plotna: kalenica na slupach, odchylona pola, liny i sledzie')
def tent():
    begin('namiot_wojskowy')
    cloth = T('cloth', 0.95)
    L, W, H = 6.0, 4.4, 3.0
    # dwie polacie z lekkim zwisem
    for sd in (-1, 1):
        def fn(u, v, sd=sd):
            x = (u - 0.5) * L
            y = sd * (W / 2) * v
            z = H * (1 - v) - 0.18 * math.sin(math.pi * u) * math.sin(math.pi * v)
            return (x, y, z + 0.05)
        add(param_shell(fn, 10, 4, None, 0.04, closed_u=False), cloth, uv='box', tile=3, name='canvas')
    # tylna sciana zamknieta, przednia z odchylonymi polami
    back = C.bm_extrude([(-W / 2, 0), (W / 2, 0), (0, H)], 0.05, 0.0, 1)
    C.bm_transform(back, rot=(90, 0, 90))
    add(back, cloth, loc=(L / 2, 0, 0.05), uv='box', tile=3, name='back')
    for sd in (-1, 1):
        flap = C.bm_extrude([(0, 0), (W / 2 * 0.9, 0), (0, H * 0.95)], 0.05, 0.0, 1)
        C.bm_transform(flap, rot=(90, 0, -90 + sd * 50))
        add(flap, cloth, loc=(-L / 2 - 0.05, sd * 0.05, 0.05), scale=(1, 1, 1), uv='box', tile=3, name='flap')
    add(box(0.12, W * 0.2, 0.12, 0.01), T('wood_dark', 0.8), loc=(-L / 2, 0, H - 0.1), name='ridge_end') if False else None
    add(cyl(0.08, L + 0.6, 8), T('wood_dark', 0.8), loc=(0, 0, H + 0.1), rot=(0, 90, 0), uv='none', name='ridge')
    for x in (-L / 2 - 0.1, L / 2 + 0.1):
        add(cyl(0.09, H + 0.4, 8), T('wood_dark', 0.8), loc=(x, 0, (H + 0.4) / 2), uv='none', name='pole')
    for x in (-L / 2 + 0.6, 0, L / 2 - 0.6):
        for sd in (-1, 1):
            a = (x, sd * W / 2, 0.15)
            b = (x, sd * (W / 2 + 1.6), 0.05)
            add(C.bm_tube([(x, sd * W / 2 * 0.98, 0.3), b], 0.02, res=2, smooth=False), T('rope', 0.9), uv='none', name='rope')
            add(cone(0.05, 0.5, 4), T('wood', 0.8), loc=(b[0], b[1], -0.25), uv='none', name='peg')
    for sd in (-1, 1):
        add(C.bm_tube([(-L / 2 - 0.1, 0, H + 0.3), (-L / 2 - 1.8, sd * 1.2, 0.05)], 0.02, res=2, smooth=False), T('rope', 0.9),
            uv='none', name='rope')
    add(box(1.3, 0.04, 0.8, 0.0), T('cloth_red', 0.9), loc=(-L / 2 - 0.75, 0, H + 0.1), name='pennant')
    # wyposazenie: poslanie, tarcza, amfora
    add(box(1.6, 3.0, 0.25, 0.08), T('cloth_red', 0.9), loc=(1.0, 0, 0.12), name='bedroll')
    add(lathe([(0, 0), (0.12, 0), (0.42, 0.45), (0.45, 0.8), (0.3, 1.25), (0.14, 1.35), (0.16, 1.5), (0, 1.4)], 14),
        T('terracotta', 0.8), loc=(-1.8, 1.4, 0.05), name='amphora')


@prop('ognisko', 'Targ', 'Ognisko w kregu kamieni z rozzarzonymi polanami i rozen')
def campfire():
    begin('ognisko')
    rnd = random.Random(4)
    for k in range(11):
        a = 2 * math.pi * k / 11
        add(rock_bm(rnd.uniform(0.32, 0.45), 20 + k, 1, 0.3, 0.3), T('rock', 0.9),
            loc=(math.cos(a) * 1.2, math.sin(a) * 1.2, 0.15), rot=(0, 0, rnd.uniform(0, 360)), smooth=False, name='stone')
    add(cyl(1.0, 0.06, 20), T('ash', 0.95), loc=(0, 0, 0.03), name='ash')
    for k in range(6):
        a = 2 * math.pi * k / 6
        add(cyl(0.11, 1.5, 7), T('wood_dark', 0.9), loc=(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.45),
            rot=(0, 62, math.degrees(a) + 180), uv='none', name='log')
    for k in range(8):
        add(C.bm_sphere(0.09, 6, 4), F('ember', (255, 90, 20), 0.6, 0.0, 4),
            loc=(rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 0.1), name='ember')
    flame((0, 0, 0.15), 0.9, 5)
    for sx in (-1, 1):
        add(C.bm_tube([(sx * 1.6, 0, 0), (sx * 1.6, 0, 1.5), (sx * 1.5, 0, 1.75)], 0.06, res=3), T('wood', 0.8), uv='none',
            name='spit_post')
    add(cyl(0.04, 3.4, 6), IRON(), loc=(0, 0, 1.65), rot=(0, 90, 0), uv='none', name='spit')
    add(blob_bm(0.32, 4, 1, 0.15, (1.6, 0.8, 0.8)), F('roast', (150, 80, 40), 0.5), loc=(0, 0, 1.6), name='roast')
    marker('Fire', (0, 0, 0.6), size=2, heat=5)
    marker('Light', (0, 0, 1.0), range=14, brightness=1.6, color=[255, 160, 80])


@prop('pithos', 'Targ', 'Pithos: wielki dzban zasobowy z reliefowymi pasami sznurowymi')
def pithos():
    begin('pithos')
    t = T('terracotta', 0.85)
    add(lathe([(0, 0), (0.55, 0), (0.95, 0.3), (1.35, 1.1), (1.45, 1.8), (1.3, 2.6), (0.95, 3.15), (0.75, 3.3),
               (0.85, 3.45), (0.95, 3.55), (0.78, 3.6), (0.62, 3.4), (0, 3.3)], 36), t, uv='cyl', tile=3, name='jar')
    for z, r in ((1.1, 1.36), (1.8, 1.47), (2.5, 1.33)):
        pts = []
        for k in range(73):
            a = 2 * math.pi * k / 72
            pts.append((math.cos(a) * r, math.sin(a) * r, z + 0.05 * math.sin(a * 18)))
        add(C.bm_tube(pts, 0.06, res=2), t, uv='none', name='rope_band')
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        add(C.bm_torus(0.2, 0.06, 12, 5), t, loc=(math.cos(a) * 1.38, math.sin(a) * 1.38, 2.2),
            rot=(90, 0, math.degrees(a) + 90), name='lug')



# =================================================================== fortyfikacje greckie (Messene), namiot, pole, kapliczka
def ashlar():
    return T('blocks', 0.85)


def greek_tower(cx, cy, w=7.0, h=12.0, name='tower'):
    """Wieza jak w murach Messene: ciosy w warstwach, dwa pietra okien (strzelnic), dach dwuspadowy z dachowek."""
    add(box(w + 0.6, w + 0.6, 1.2, 0.05), T('blocks_grey', 0.85), loc=(cx, cy, 0.6), uv='box', tile=3, name=name + '_footing')
    add(box(w, w, h, 0.04), ashlar(), loc=(cx, cy, 1.2 + h / 2), uv='box', tile=4, name=name)
    for z in (1.2 + h * 0.45, 1.2 + h - 0.15):
        add(box(w + 0.25, w + 0.25, 0.3, 0.03), ashlar(), loc=(cx, cy, z), name=name + '_course')
    # okna-strzelnice: waskie dolne, szersze gorne (do katapult), z kamiennymi nadprozami
    for face in range(4):
        R = Matrix.Rotation(face * math.pi / 2, 3, 'Z')
        for k, (zz, ww, hh, n) in enumerate(((1.2 + h * 0.3, 0.35, 1.3, 2), (1.2 + h * 0.75, 0.9, 1.3, 2))):
            for j in range(n):
                off = (j - (n - 1) / 2) * w * 0.4
                p = Vector((cx, cy, 0)) + R @ Vector((off, -w / 2 - 0.02, 0))
                add(box(ww, 0.12, hh, 0.0), F('void', (20, 16, 14)), loc=(p.x, p.y, zz), rot=(0, 0, face * 90), name=name + '_slit')
                p2 = Vector((cx, cy, 0)) + R @ Vector((off, -w / 2 - 0.08, 0))
                add(box(ww + 0.6, 0.25, 0.3, 0.02), T('limestone', 0.8), loc=(p2.x, p2.y, zz + hh / 2 + 0.15),
                    rot=(0, 0, face * 90), name=name + '_lintel')
    gable_roof(cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2, 1.2 + h, 1.2 + h + w * 0.28, ashlar(), 0.5, name=name + '_roof')
    return 1.2 + h


def curtain_wall(x0, x1, y, h=7.0, t=3.0, name='wall'):
    L = x1 - x0
    add(box(L, t + 0.4, 1.0, 0.04), T('blocks_grey', 0.85), loc=((x0 + x1) / 2, y, 0.5), uv='box', tile=3, name=name + '_footing')
    add(box(L, t, h, 0.03), ashlar(), loc=((x0 + x1) / 2, y, 1.0 + h / 2), uv='box', tile=4, name=name)
    # parapet z blankami (zeby na przedniej krawedzi chodnika)
    add(box(L, 0.6, 1.0, 0.03), ashlar(), loc=((x0 + x1) / 2, y - t / 2 + 0.3, 1.0 + h + 0.5), name=name + '_parapet')
    x = x0 + 0.6
    while x < x1 - 0.6:
        add(box(1.1, 0.6, 0.9, 0.03), ashlar(), loc=(x, y - t / 2 + 0.3, 1.0 + h + 1.45), name=name + '_merlon')
        add(box(1.3, 0.7, 0.18, 0.02), T('limestone', 0.8), loc=(x, y - t / 2 + 0.3, 1.0 + h + 1.95), name=name + '_cap')
        x += 1.9


@prop('mur_z_wieza', 'Wojsko', 'Mury miasta z wieza (typ z Messene): ciosy, strzelnice, dach z dachowek')
def city_wall_tower():
    begin('mur_z_wieza')
    curtain_wall(-14, 3.5, 0.0, 7.0, 3.0)
    greek_tower(7.5, 0.5, 8.0, 11.0)
    door(7.5, -3.6, 1.2, 1.6, 2.4)
    add(box(3.0, 2.2, 1.2, 0.03), T('blocks_grey', 0.85), loc=(7.5, -4.6, 0.6), name='ramp')
    for x in (-8.0, -2.0):
        add(box(1.4, 0.1, 3.8, 0.0), T('cloth_red', 0.9), loc=(x, -1.56, 5.5), uv='box', tile=2, name='banner')
        add(cyl(0.05, 1.8, 6), T('wood_dark', 0.85), loc=(x, -1.6, 7.45), rot=(0, 90, 0), uv='none', name='banner_rod')


@prop('wieza_straznicza', 'Architektura', 'Grecka wieza straznicza (pyrgos) z ciosow, z dachem z dachowek')
def watchtower():
    begin('wieza_straznicza')
    top = greek_tower(0, 0, 7.0, 13.0)
    door(0, -3.6, 1.2, 1.5, 2.3)
    add(box(2.6, 1.8, 1.2, 0.03), T('blocks_grey', 0.85), loc=(0, -4.4, 0.6), name='step')
    add(cyl(0.08, 4.0, 6), T('wood_dark', 0.85), loc=(3.3, -3.3, top + 1.5), uv='none', name='pole')
    add(box(2.0, 0.05, 1.2, 0.0), T('cloth_red', 0.9), loc=(4.3, -3.3, top + 2.9), name='flag')


@prop('namiot_dowodcy', 'Wojsko', 'Namiot strategosa: prostokatny pawilon z portykiem na slupach, proporce, stol map')
def commander_tent():
    begin('namiot_dowodcy')
    cloth = T('cloth', 0.95)
    red = T('cloth_red', 0.9)
    L, W, Hw, Hr = 9.0, 7.0, 2.8, 4.8
    # sciany boczne (lekko faliste)
    for sd in (-1, 1):
        def fn(u, v, sd=sd):
            x = (u - 0.5) * L
            return (x, sd * (W / 2 + 0.05 * math.sin(u * 30)), v * Hw)
        add(param_shell(fn, 20, 2, None, 0.04, closed_u=False), red, uv='box', tile=3, name='side')
    for sx in (-1, 1):
        def fn(u, v, sx=sx):
            y = (u - 0.5) * W
            return (sx * L / 2, y, v * Hw)
        add(param_shell(fn, 14, 2, None, 0.04, closed_u=False), red, uv='box', tile=3, name='end')
    for sd in (-1, 1):
        def fn(u, v, sd=sd):
            x = (u - 0.5) * (L + 0.6)
            y = sd * (W / 2 + 0.4) * v
            z = Hr - (Hr - Hw + 0.2) * v - 0.15 * math.sin(math.pi * u) * math.sin(math.pi * v)
            return (x, y, z)
        add(param_shell(fn, 12, 4, None, 0.05, closed_u=False), cloth, uv='box', tile=3, name='roof')
    for sx in (-1, 1):
        g = C.bm_extrude([(-W / 2, Hw), (W / 2, Hw), (0, Hr)], 0.05, 0.0, 1)
        C.bm_transform(g, rot=(90, 0, 90))
        add(g, cloth, loc=(sx * L / 2, 0, 0), uv='box', tile=3, name='gable')
    # frędzle (lambrekin) na okapach
    for sd in (-1, 1):
        for k in range(16):
            add(box(0.5, 0.04, 0.35, 0.0), red if k % 2 else T('cloth_yellow', 0.9),
                loc=(-L / 2 + 0.3 + k * L / 16, sd * (W / 2 + 0.42), Hw - 0.35), name='valance')
    # portyk przed wejsciem
    for x in (-1.8, 1.8):
        add(cyl(0.12, 3.4, 8), T('wood_dark', 0.85), loc=(x, -W / 2 - 2.6, 1.7), uv='none', name='porch_pole')
        add(cone(0.12, 0.4, 6), GOLD(), loc=(x, -W / 2 - 2.6, 3.4), uv='none', name='finial')
    def fnp(u, v):
        return ((u - 0.5) * 4.2, -W / 2 - v * 2.7, 3.3 - 0.4 * v + 0.12 * math.sin(math.pi * u))
    add(param_shell(fnp, 8, 3, None, 0.04, closed_u=False), cloth, uv='box', tile=3, name='porch_roof')
    add(box(2.2, 0.06, 2.4, 0.0), F('void', (30, 20, 18)), loc=(0, -W / 2 - 0.06, 1.2), name='entrance')
    for sx in (-1, 1):
        add(box(1.1, 0.06, 2.5, 0.0), red, loc=(sx * 1.45, -W / 2 - 0.25, 1.25), rot=(0, 0, -sx * 25), name='door_flap')
    # proporce na szczytach
    for sx in (-1, 1):
        add(cyl(0.06, 2.4, 6), T('wood_dark', 0.85), loc=(sx * L / 2, 0, Hr + 1.0), uv='none', name='staff')
        add(box(1.4, 0.04, 0.7, 0.0), red, loc=(sx * L / 2 + 0.7, 0, Hr + 1.85), name='pennant')
    # stol z mapa, krzesla, stojak z bronia przy wejsciu
    add(box(2.4, 1.4, 0.12, 0.02), T('wood', 0.8), loc=(3.2, -W / 2 - 2.2, 1.0), name='table')
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(box(0.1, 0.1, 0.95, 0.0), T('wood_dark', 0.85), loc=(3.2 + sx * 1.05, -W / 2 - 2.2 + sy * 0.55, 0.47), name='leg')
    add(box(1.6, 1.0, 0.02, 0.0), F('papyrus', (222, 200, 150), 0.9), loc=(3.2, -W / 2 - 2.2, 1.07), rot=(0, 0, 8), name='map')
    helm((3.6, -W / 2 - 2.0, 1.4), 0.3, (0, 0, 60), BRONZE(), F('crest_red', (150, 30, 26), 0.85), name='helm')
    painted_shield(0, (-3.0, -W / 2 - 1.4, 1.0), 0.85, (70, 0, 0), name='shield')
    spear((-3.6, -W / 2 - 1.0, 0.0), (-3.4, -W / 2 - 1.3, 4.6), 0.07, name='spear')


@prop('pole_pszenicy', 'Wies', 'Pole dojrzalej pszenicy (gesty lan z klosami)')
def wheat():
    begin('pole_pszenicy')
    rnd = random.Random(10)
    stalks, ears = [], []
    for k in range(520):
        x, y = rnd.uniform(-5, 5), rnd.uniform(-5, 5)
        h = rnd.uniform(1.2, 1.6)
        lx, ly = rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15)
        bm = bmesh.new()
        v = [bm.verts.new((x - 0.02, y, 0)), bm.verts.new((x + 0.02, y, 0)), bm.verts.new((x + lx + 0.01, y + ly, h)),
             bm.verts.new((x + lx - 0.01, y + ly, h))]
        bm.faces.new(v)
        stalks.append(bm)
        e = C.bm_sphere(0.05, 5, 4)
        C.bm_transform(e, loc=(x + lx * 1.1, y + ly * 1.1, h + 0.12), scale=(1, 1, 3.2), rot=(ly * 120, -lx * 120, 0))
        ears.append(e)
    add(merge(stalks), F('wheat_stalk', (190, 160, 80), 0.85), uv='none', name='stalks')
    add(merge(ears), F('wheat_ear', (222, 184, 96), 0.75), uv='none', name='ears')
    add(box(10.4, 10.4, 0.1, 0.0), T('dirt_ruts', 0.95), loc=(0, 0, 0.05), uv='box', tile=6, name='soil')
    for k in range(8):   # snopki na skraju
        x = -4.5 + k * 1.3
        add(cyl(0.35, 1.3, 10, r2=0.18), T('straw', 0.9), loc=(x, -5.8, 0.65), uv='cyl', name='sheaf')
        add(C.bm_torus(0.2, 0.04, 10, 4), T('rope', 0.9), loc=(x, -5.8, 0.75), name='band')


@prop('kapliczka', 'Wies', 'Przydrozny naiskos: kapliczka z dwiema kolumnami, posazek i dary')
def shrine():
    begin('kapliczka')
    m = MARBLE()
    add(box(2.6, 2.2, 0.4, 0.04), BLOCKS(), loc=(0, 0, 0.2), name='base')
    add(box(2.2, 1.8, 0.3, 0.04), m, loc=(0, 0, 0.55), name='podium')
    add(box(2.0, 0.25, 2.4, 0.03), m, loc=(0, 0.75, 1.9), name='back')
    for sx in (-1, 1):
        add(box(0.25, 1.6, 2.4, 0.03), m, loc=(sx * 0.9, 0.0, 1.9), name='wall')
        from .props import fluted_column_bm
        add(fluted_column_bm(0.14, 2.2, 12, 0.9, 24, 2), m, loc=(sx * 0.55, -0.75, 0.7), uv='cyl', name='column')
    add(box(2.3, 1.9, 0.25, 0.03), m, loc=(0, 0, 3.22), name='architrave')
    ped = C.bm_extrude([(-1.15, 0), (1.15, 0), (0, 0.6)], 1.9, 0.02, 1)
    C.bm_transform(ped, rot=(90, 0, 0))
    add(ped, m, loc=(0, 0, 3.35), uv='box', name='pediment')
    figure((0, 0.3, 0.7), 0.38, BRONZE(), 'still', 0, 'idol', female=True, dress='long')
    add(lathe([(0, 0), (0.18, 0), (0.22, 0.08), (0.08, 0.1), (0, 0.1)], 12), T('terracotta', 0.8), loc=(0.4, -0.55, 0.7),
        name='lamp')
    add(C.bm_sphere(0.05, 6, 4), FIRE(), loc=(0.55, -0.55, 0.82), name='lamp_flame')
    for k, c in enumerate(((200, 40, 40), (240, 210, 80), (240, 240, 240))):
        add(C.bm_sphere(0.09, 6, 4), F('flower' + str(c), c, 0.6), loc=(-0.5 + k * 0.15, -0.6, 0.75), name='offering')
    marker('Light', (0.55, -0.55, 0.9), range=6, brightness=0.8, color=[255, 170, 90])


@prop('ogien_sygnalowy', 'Wojsko', 'Wieza z ogniem sygnalowym: drewniane rusztowanie, kosz z plonacym drewnem')
def signal_fire():
    begin('ogien_sygnalowy')
    wood = T('wood_dark', 0.85)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(box(0.25, 0.25, 6.4, 0.02), wood, loc=(sx * 1.2, sy * 1.2, 3.1), rot=(-sy * 5, sx * 5, 0), name='leg')
    for z in (1.5, 3.5):
        for sx in (-1, 1):
            add(box(0.15, 2.6, 0.15, 0.0), wood, loc=(sx * 1.15, 0, z), name='brace')
            add(box(2.6, 0.15, 0.15, 0.0), wood, loc=(0, sx * 1.15, z), name='brace')
    add(box(3.0, 3.0, 0.2, 0.02), T('wood', 0.85), loc=(0, 0, 6.2), name='deck')
    add(lathe([(0.3, 0), (0.9, 0.1), (1.1, 0.7), (1.0, 0.7), (0.8, 0.2), (0.3, 0.1)], 16), IRON(), loc=(0, 0, 6.3), name='basket')
    for k in range(6):
        a = 2 * math.pi * k / 6
        add(cyl(0.1, 1.4, 6), wood, loc=(math.cos(a) * 0.2, math.sin(a) * 0.2, 6.7), rot=(0, 60, math.degrees(a)), uv='none',
            name='log')
    flame((0, 0, 6.5), 1.3, 8)
    for k in range(9):
        add(box(0.3, 0.3, 0.12, 0.0), wood, loc=(-0.6, -1.65, 0.3 + k * 0.7), name='rung')
    marker('Fire', (0, 0, 7.0), size=4, heat=8)
    marker('Light', (0, 0, 7.5), range=30, brightness=2.5, color=[255, 160, 80])
    marker('Smoke', (0, 0, 8.5), size=3, opacity=0.4)


import os as _os
if _os.environ.get('OLTEST'):
    @prop('_t1', 'Test', '')
    def _t1():
        begin('_t1')
        figure((0, 0, 0), 1.0, MARBLE(), 'still', 0, 'a', cloak=True)

    @prop('_t2', 'Test', '')
    def _t2():
        begin('_t2')
        figure((0, 0, 0), 1.0, MARBLE(), 'still', 0, 'a')

    @prop('_t3', 'Test', '')
    def _t3():
        begin('_t3')
        figure((0, 0, 0), 1.0, MARBLE(), 'still', 0, 'a', female=True)
