"""Sklada plansze zbiorcza ze wszystkich hero renderow (renders/Jednostki.png)
i tabele klipow do README (wypisuje na stdout)."""
import json
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ['Legionista', 'Hoplita', 'Luczniczka', 'Balista', 'Wyrocznia', 'Meduza', 'Minotaur', 'Kaplan']


def lineup():
    cell, pad = 460, 14
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 26)
    W = 4 * cell + 5 * pad
    H = 2 * (cell + 44) + 3 * pad + 70
    sheet = Image.new('RGB', (W, H), (24, 26, 38))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 18), 'Ostatni Legion - jednostki', font=font, fill=(245, 214, 140))
    for i, n in enumerate(ORDER):
        data = json.load(open(os.path.join(ROOT, 'export', n, f'{n}.json'), encoding='utf-8'))
        im = Image.open(os.path.join(ROOT, 'renders', f'{n}_hero.png')).resize((cell, cell), Image.LANCZOS)
        x = pad + (i % 4) * (cell + pad)
        y = 70 + (i // 4) * (cell + 44 + pad)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + cell + 8), data['display'], font=font, fill=(235, 235, 245))
    sheet.save(os.path.join(ROOT, 'renders', 'Jednostki.png'), optimize=True)


def table():
    for n in ORDER:
        data = json.load(open(os.path.join(ROOT, 'export', n, f'{n}.json'), encoding='utf-8'))
        print(f"\n### {data['display']}\n")
        print('| Klip | Nazwa | Poziomy | Klatki | Trafienia (klatka) |')
        print('|---|---|---|---|---|')
        for cn, c in data['clips'].items():
            hits = ', '.join(str(e['frame']) for e in c['events'] if e['name'] in ('Hit', 'Shoot'))
            print(f"| {cn} | {c['label'].split(': ')[-1]} | {c['level'] or '-'} | {c['length']} | {hits or '-'} |")


if __name__ == '__main__':
    lineup()
    table()
