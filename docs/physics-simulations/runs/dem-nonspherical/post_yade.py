"""Figure + animation for the Yade heap runs.
Usage: python post_yade.py <run dir seed 1>[,<run dir seed 2>...] <repo out dir>
Profiles and animation from the first dir; bars = mean over dirs, dots = individual seeds."""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection

DS, OUT = sys.argv[1].split(','), sys.argv[2]
D = DS[0]
cases = [('sphere', 'spheres, no rolling resistance', '#7f7f7f'),
         ('sphere_rr', 'spheres + rolling resistance', '#1f77b4'),
         ('cube8', '8-sphere cube clumps', '#d62728')]
R = {c: json.load(open(os.path.join(D, 'result_%s.json' % c))) for c, _, _ in cases if os.path.exists(os.path.join(D, 'result_%s.json' % c))}
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
for c, lab, col in cases:
    if c not in R:
        continue
    r = R[c]
    ax[0].plot(r['profile_r_mm'], r['profile_h_mm'], 'o-', ms=3, color=col,
               label='%s: fit %.0f deg, h/r %.0f deg' % (lab, r['angle_of_repose_deg'], r['aor_from_height_over_foot_deg']))
ax[0].set_xlabel('radial distance from heap axis r (mm)'); ax[0].set_ylabel('heap surface height h (mm)')
ax[0].set_title('Heap profiles after lifting the cylinder (Yade, seed 1)'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
names = [c for c, _, _ in cases if c in R]
x = np.arange(len(names))
RS = {c: [json.load(open(os.path.join(dd, 'result_%s.json' % c))) for dd in DS] for c in names}
mfit = [np.mean([r['angle_of_repose_deg'] for r in RS[c]]) for c in names]
mhr = [np.mean([r['aor_from_height_over_foot_deg'] for r in RS[c]]) for c in names]
ax[1].bar(x - 0.2, mfit, 0.4, label='flank fit (mean of %d seeds)' % len(DS), color='#9ecae1')
ax[1].bar(x + 0.2, mhr, 0.4, label='atan(h / r_foot) (mean)', color='#3182bd')
for i, c in enumerate(names):
    ax[1].plot([i - 0.2] * len(DS), [r['angle_of_repose_deg'] for r in RS[c]], 'k.', ms=5)
    ax[1].plot([i + 0.2] * len(DS), [r['aor_from_height_over_foot_deg'] for r in RS[c]], 'k.', ms=5)
    ax[1].text(i, 2, 'phi=%.3f\nN=%d' % (np.mean([r['packing_fraction_column'] for r in RS[c]]), R[c]['n_particles']), ha='center', fontsize=8, color='w')
ax[1].set_xticks(x); ax[1].set_xticklabels(names); ax[1].set_ylabel('angle of repose (deg)')
ax[1].set_title('Angle of repose; mean column packing fraction phi'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3, axis='y')
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'dem_nonspherical_heaps.png'), dpi=110)

import imageio.v2 as imageio
F = {c: np.load(os.path.join(D, 'frames_%s.npy' % c), allow_pickle=True) for c in names}
nf = max(len(F[c]) for c in names)
step = max(1, nf // 60)
imgs = []
for k in range(0, nf, step):
    f, axs = plt.subplots(1, len(names), figsize=(6.4, 2.6), dpi=100)
    for a, c in zip(np.atleast_1d(axs), names):
        fr = F[c][min(k, len(F[c]) - 1)]
        t, xs, zs, rs = fr
        a.add_collection(PatchCollection([Circle((1e3 * xx, 1e3 * zz), 1e3 * rr) for xx, zz, rr in zip(xs, zs, rs)],
                                         facecolor=dict((cc, col) for cc, _, col in cases)[c], edgecolor='none'))
        a.set_xlim(-5, 5); a.set_ylim(0, 6); a.set_aspect('equal'); a.set_title('%s  t=%.2f s' % (c, t), fontsize=8)
        a.tick_params(labelsize=6); a.set_xlabel('x (mm)', fontsize=7)
    np.atleast_1d(axs)[0].set_ylabel('z (mm)', fontsize=7)
    f.suptitle('Non-spherical DEM (Yade): lifted-cylinder heap, slice |y| < 0.6 mm', fontsize=9)
    f.tight_layout(); f.canvas.draw()
    imgs.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(f)
imageio.mimsave(os.path.join(OUT, 'dem_nonspherical_heaps.gif'), imgs, duration=1 / 10, loop=0)
w = imageio.get_writer(os.path.join(OUT, 'dem_nonspherical_heaps.mp4'), fps=10, codec='libx264', pixelformat='yuv420p', macro_block_size=8)
for im in imgs:
    w.append_data(im)
w.close()
print({c: (R[c]['angle_of_repose_deg'], R[c]['aor_from_height_over_foot_deg'], R[c]['packing_fraction_column'], R[c]['n_particles']) for c in names})
