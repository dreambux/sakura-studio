"""Wypieka cala biblioteke tekstur map do maps/textures/ i robi plansze podgladu."""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)
from lib import recipes  # noqa: E402

OUT = os.path.join(HERE, 'textures')


def sheet(names, path, cell=256, cols=8):
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    rows = (len(names) + cols - 1) // cols
    im = Image.new('RGB', (cols * (cell + 8) + 8, rows * (cell + 30) + 8), (24, 26, 38))
    d = ImageDraw.Draw(im)
    for i, n in enumerate(names):
        t = Image.open(os.path.join(OUT, f'{n}_col.png')).convert('RGB').resize((cell, cell), Image.LANCZOS)
        x, y = 8 + (i % cols) * (cell + 8), 8 + (i // cols) * (cell + 30)
        im.paste(t, (x, y))
        d.text((x + 4, y + cell + 6), n, font=font, fill=(230, 230, 240))
    im.save(path)


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None
    t0 = time.time()
    res = recipes.build_library(OUT, only=only or None)
    print('tekstury:', len(res), f'{time.time() - t0:.0f} s')
    names = [n for n, _ in recipes.LIBRARY]
    sheet(names, os.path.join(HERE, 'textures_podglad.png'))
