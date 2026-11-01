"""Buduje jednostki Ostatniego Legionu: model + animacje + eksport + rendery.

Uzycie (Blender w trybie tla albo modul bpy):
  blender -b -P build_all.py -- legionista hoplita ...      (bez nazw = wszystkie)
  python build_all.py legionista --no-render
Opcje: --no-render, --quick (mniej probek), --only-hero
"""
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from lib import core, materials as M, export as E, render as RD  # noqa: E402

UNITS = ['legionista', 'hoplita', 'lucznicza', 'balista', 'wyrocznia', 'meduza', 'minotaur', 'kaplan', 'afrodyta', 'centurion', 'hermes']


def run(unit, do_render=True, quick=False):
    t0 = time.time()
    core.reset_scene()
    M.clear_cache()
    mod = importlib.import_module('units.' + unit)
    info = mod.INFO
    name = info['name']
    out = os.path.join(ROOT, 'export', name)
    os.makedirs(out, exist_ok=True)
    rig = mod.build(out)
    bounds = E.export_glb(rig, os.path.join(out, f'{name}.glb'))
    anim = mod.animate(rig)
    data = E.write_data(rig, anim, bounds, name, info['display'], out, extra=info.get('extra'))
    cam = info.get('cam', {})
    RD.setup(target=cam.get('target', (0, 0, 2.5)), dist=cam.get('dist', 12.0), ped_r=info.get('ped_r', 2.6), ped_c=info.get('ped_c', (0, 0, 0)),
             samples=16 if quick else 40, cam_dir=cam.get('dir', (0.45, -1.0, 0.42)))
    bpy.context.scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f'{name}.blend'), compress=True)
    hooks = mod.hooks(rig) if hasattr(mod, 'hooks') else ()
    if do_render:
        RD.render_sheets(rig, anim, os.path.join(ROOT, 'renders'), name, info['display'], info['subtitle'],
                         hooks=hooks)
    parts = bounds['parts']
    print(f'== {name}: {len(parts)} czesci, max {max(t for _, t in parts)} trojk., '
          f'klipy {list(data["clips"])}, {time.time() - t0:.0f} s')


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    flags = {a for a in argv if a.startswith('--')}
    names = [a for a in argv if not a.startswith('--')] or UNITS
    for u in names:
        run(u, do_render='--no-render' not in flags, quick='--quick' in flags)
