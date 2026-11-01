"""Wypieka cala biblioteke tekstur map (maps/textures) i plansze podgladu per kategoria (maps/katalog_tekstur)."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
from lib import library as L  # noqa: E402

OUT = os.path.join(HERE, 'textures')
SHEETS = os.path.join(HERE, 'katalog_tekstur')


def sheet(cat, names, path, cell=256, cols=8):
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    rows = (len(names) + cols - 1) // cols
    im = Image.new('RGB', (cols * (cell + 8) + 8, rows * (cell + 30) + 52), (24, 26, 38))
    d = ImageDraw.Draw(im)
    d.text((10, 12), f'Tekstury: {cat} ({len(names)})', font=fb, fill=(245, 214, 140))
    for i, n in enumerate(names):
        t = Image.open(os.path.join(OUT, f'{n}_col.png')).convert('RGB').resize((cell, cell), Image.LANCZOS)
        x, y = 8 + (i % cols) * (cell + 8), 48 + (i // cols) * (cell + 30)
        im.paste(t, (x, y))
        d.text((x + 4, y + cell + 6), n, font=font, fill=(230, 230, 240))
    im.save(path)


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None
    t0 = time.time()
    done = L.build(OUT, only=only or None)
    print('tekstury:', len(done), f'{time.time() - t0:.0f} s')
    os.makedirs(SHEETS, exist_ok=True)
    cats = {}
    for c, n, _ in L.LIB:
        if os.path.exists(os.path.join(OUT, f'{n}_col.png')):
            cats.setdefault(c, []).append(n)
    for c, ns in cats.items():
        sheet(c, ns, os.path.join(SHEETS, f'{c}.png'))
    print('plansze:', list(cats))
