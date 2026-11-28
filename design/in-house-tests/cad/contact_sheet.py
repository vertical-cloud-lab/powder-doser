import json, math, sys
from pathlib import Path
import numpy as np, pyvista as pv
pv.OFF_SCREEN = True
out = Path(sys.argv[1]); db = json.loads((out/"parts.json").read_text())
names = [n for n in db if "error" not in db[n]]
# one representative per family
skip = lambda n: any(n.startswith(p) for p in ("riser_40","riser_80","riser_120","tripod_leg_40","tripod_leg_80","tripod_leg_120","orifice_disc_1p","orifice_disc_2p0","orifice_disc_2p54","orifice_disc_3","orifice_disc_4","orifice_disc_5","strike_frame_1","strike_frame_2","strike_frame_3","pedestal_d12","pedestal_d30"))
names = [n for n in names if not skip(n)]
cols = 8; rows = math.ceil(len(names)/cols)
pl = pv.Plotter(shape=(rows, cols), window_size=(cols*260, rows*230), off_screen=True)
for i, n in enumerate(names):
    pl.subplot(i//cols, i%cols)
    m = pv.read(str(out/"stl"/f"{n}.stl"))
    pl.add_mesh(m, color="#5fb3a7", smooth_shading=False, show_edges=False)
    pl.add_text(n, font_size=7, position="upper_left")
    pl.view_isometric(); pl.camera.zoom(1.2)
    pl.set_background("white")
pl.screenshot(sys.argv[2])
print(len(names), "parts")
