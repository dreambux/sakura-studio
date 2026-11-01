"""Koncepty map: dla kazdej mapy render z gory (z opisem) + z boku, uklad w Luau/JSON, teren w GLB.

  python maps/build_maps.py                 (wszystkie 14)
  python maps/build_maps.py -- agora troy  (wybrane po nazwie funkcji)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

bpy.ops.wm.read_factory_settings(use_empty=True)

from lib import props as P  # noqa: E402
from lib import p_nature, p_arch, p_harbor, p_market, p_themes, p_unique, p_more, p_extra, p_hq, p_platforms  # noqa: E402,F401
from lib import mapscene  # noqa: E402
from lib.m_maps14 import MAPS14  # noqa: E402
from lib.m_new import brama_lwow  # noqa: E402

MAPS = MAPS14 + [brama_lwow]

OUT = os.path.join(HERE, 'koncepty')


def export_terrain(M, path):
    objs = [o for o in M.coll.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    if not objs:
        return
    bpy.context.view_layer.objects.active = objs[0]
    try:
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                                  export_yup=True, export_materials='EXPORT', export_image_format='JPEG')
    except Exception as e:
        print('terrain export:', e)


if __name__ == '__main__':
    sel = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    if not sel:
        for name, (cat, fn, desc) in P.REGISTRY.items():
            fn()
        mapscene.to_collections()
    print('modele gotowe', len(P.REGISTRY), f'{time.time() - t0:.0f} s')
    sc = bpy.context.scene
    done = []
    for i, mk in enumerate(MAPS, 1):
        if sel and mk.__name__ not in sel:
            continue
        try:
            M, legend = mk()
        except Exception:
            import traceback
            traceback.print_exc()
            print('BLAD mapy', mk.__name__)
            continue
        sc.cycles.samples = 16
        tag = f'{i:02d}_{M.name}'
        top = os.path.join(OUT, f'{tag}_gora_raw.png')
        M.render_top(top, (1400, 1085))
        M.annotate(top, os.path.join(OUT, f'{tag}_gora.png'), legend)
        os.remove(top)
        M.render_side(os.path.join(OUT, f'{tag}_bok.png'), (1400, 790), dirv=(0.35, -1.0, 0.55))
        M.export_luau(os.path.join(OUT, f'{tag}_uklad.lua'))
        export_terrain(M, os.path.join(OUT, f'{tag}_teren.glb'))
        M.coll.hide_render = True
        M.coll.hide_viewport = True
        done.append(M.display)
        print(f'== mapa {tag} gotowa', f'{time.time() - t0:.0f} s')
    print('MAPY:', done)
