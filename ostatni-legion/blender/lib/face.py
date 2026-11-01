"""Tekstury twarzy w stylu klasycznego Robloxa (wsciekla twarz).

Tekstura = kolor skory + narysowana twarz. Rzutowana na przod glowy (u = 0.5 + x/W,
v = 0.5 + (z - srodek)/W). Rysowane w 4x i zmniejszane (gladkie krawedzie).
"""
from PIL import Image, ImageDraw, ImageFilter

HEAD_UV_W = 1.3  # szerokosc (studs) pokryta przez teksture


def lin2srgb(c):
    def f(x):
        x = max(0.0, min(1.0, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return tuple(int(round(f(x) * 255)) for x in c)


def make_face(path, skin_lin, style='angry', size=512, brow=(14, 12, 12), eye=(10, 10, 10),
              mouth='teeth', lashes=False, scar=False, lips=(120, 30, 35), eye_glow=None,
              brow_w=1.0):
    S = size * 4
    skin = lin2srgb(skin_lin)
    im = Image.new('RGBA', (S, S), skin + (255,))
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (x * S, y * S)

    def poly(pts, fill):
        d.polygon([P(*p) for p in pts], fill=fill)

    def mirror(pts):
        return [(1 - x, y) for (x, y) in pts]

    def ell(cx, cy, rx, ry, fill):
        d.ellipse([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], fill=fill)

    def line(pts, w, fill):
        d.line([P(*p) for p in pts], fill=fill, width=int(w * S), joint='curve')
        for p in (pts[0], pts[-1]):
            ell(p[0], p[1], w / 2, w / 2, fill)

    # ---- oczy
    eye_y = 0.50
    ex = 0.385
    if style == 'snake':
        for sx in (ex, 1 - ex):
            ell(sx, eye_y, 0.062, 0.050, (8, 8, 8))
            ell(sx, eye_y, 0.052, 0.040, eye_glow or (250, 205, 40))
            ell(sx, eye_y, 0.011, 0.038, (5, 5, 5))
            ell(sx - 0.018, eye_y - 0.018, 0.010, 0.010, (255, 255, 230))
    elif style == 'beast':
        for sx in (ex, 1 - ex):
            ell(sx, eye_y, 0.055, 0.045, (20, 5, 5))
            ell(sx, eye_y, 0.044, 0.034, eye_glow or (235, 40, 20))
            ell(sx, eye_y, 0.020, 0.018, (255, 200, 120))
    else:
        for sx in (ex, 1 - ex):
            ell(sx, eye_y, 0.046, 0.062, eye)
            ell(sx - 0.016, eye_y - 0.022, 0.015, 0.015, (255, 255, 255))
        if lashes:
            for sgn, sx in ((-1, ex), (1, 1 - ex)):
                ox = sx + sgn * 0.040
                line([(ox, eye_y - 0.035), (ox + sgn * 0.035, eye_y - 0.060)], 0.014, eye)
                line([(ox + sgn * 0.004, eye_y - 0.010), (ox + sgn * 0.045, eye_y - 0.022)], 0.013, eye)

    # ---- brwi (skos w dol do srodka = zlosc)
    t = 0.075 * brow_w
    if style in ('angry', 'snake', 'beast', 'old'):
        b = [(0.245, 0.335), (0.470, 0.400), (0.470, 0.400 + t), (0.250, 0.335 + t * 0.85)]
    else:
        b = [(0.26, 0.355), (0.465, 0.395), (0.465, 0.395 + t), (0.265, 0.355 + t * 0.8)]
    if style == 'old':
        # krzaczaste siwe brwi
        for k in range(6):
            x0 = 0.24 + k * 0.04
            y0 = 0.33 + k * 0.014
            poly([(x0, y0 - 0.02), (x0 + 0.05, y0 + 0.01), (x0 + 0.04, y0 + 0.07), (x0 - 0.01, y0 + 0.05)], brow)
            poly(mirror([(x0, y0 - 0.02), (x0 + 0.05, y0 + 0.01), (x0 + 0.04, y0 + 0.07), (x0 - 0.01, y0 + 0.05)]), brow)
    else:
        poly(b, brow)
        poly(mirror(b), brow)

    # ---- blizna
    if scar:
        line([(0.62, 0.30), (0.67, 0.42), (0.64, 0.58)], 0.016, (120, 40, 40))
        for (x, y) in ((0.625, 0.34), (0.655, 0.42), (0.645, 0.52)):
            line([(x - 0.025, y - 0.008), (x + 0.025, y + 0.008)], 0.010, (120, 40, 40))

    # ---- usta
    if mouth == 'teeth':
        outer = [(0.345, 0.630), (0.655, 0.630), (0.680, 0.760), (0.320, 0.760)]
        poly(outer, (12, 10, 10))
        inner = [(0.365, 0.648), (0.635, 0.648), (0.656, 0.742), (0.344, 0.742)]
        poly(inner, (250, 248, 240))
        line([(0.350, 0.695), (0.650, 0.695)], 0.014, (12, 10, 10))
        for x in (0.43, 0.50, 0.57):
            line([(x, 0.650), (x, 0.740)], 0.012, (12, 10, 10))
    elif mouth == 'frown':
        pts = [(0.40, 0.715), (0.45, 0.690), (0.50, 0.684), (0.55, 0.690), (0.60, 0.715)]
        line(pts, 0.026, lips)
    elif mouth == 'fangs':
        pts = [(0.39, 0.705), (0.45, 0.685), (0.50, 0.680), (0.55, 0.685), (0.61, 0.705)]
        line(pts, 0.030, (40, 70, 35))
        for x in (0.455, 0.545):
            poly([(x - 0.020, 0.690), (x + 0.020, 0.690), (x, 0.745)], (250, 250, 240))
    elif mouth == 'smirk':
        pts = [(0.40, 0.700), (0.47, 0.705), (0.55, 0.700), (0.61, 0.680)]
        line(pts, 0.024, lips)

    im = im.filter(ImageFilter.GaussianBlur(1.2))
    im = im.resize((size, size), Image.LANCZOS)
    im.save(path)
    return path
