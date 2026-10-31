"""Beverloo fit + figure + animation for the LMGC90 silo runs.
Usage: python post_lmgc90.py <scratch dir with W*/result.json> <out dir>"""
import os, sys, json, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection

S, OUT = sys.argv[1], sys.argv[2]
runs = []
for f in sorted(glob.glob(os.path.join(S, 'W*', 'result.json'))):
    r = json.load(open(f)); r['dir'] = os.path.dirname(f); runs.append(r)
runs.sort(key=lambda r: r['W_over_d'])
W = np.array([r['W_over_d'] for r in runs]); Q = np.array([r['rate_dimless'] for r in runs])
ok = np.isfinite(Q)
fit = None
if ok.sum() >= 2:
    # 2D Beverloo: Q* = C (W/d - k)^(3/2)  ->  Q*^(2/3) linear in W/d
    p = np.polyfit(W[ok], Q[ok] ** (2 / 3), 1)
    C = p[0] ** 1.5; k = -p[1] / p[0]
    fit = dict(C=float(C), k=float(k))
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
for r in runs:
    ax[0].plot(r['t'], r['n_out'], label='W/d = %g' % r['W_over_d'])
ax[0].set_xlabel('time (s)  [d = 1 mm; scale by sqrt(d/g)]'); ax[0].set_ylabel('discs discharged (-)')
ax[0].set_title('LMGC90 NSCD: 2D silo discharge, %d discs' % runs[0]['n_discs']); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
ax[1].plot(W, Q, 'ko', label='LMGC90 (steady rate)')
if fit:
    ww = np.linspace(max(fit['k'], 0) + 0.01, W.max() * 1.1, 100)
    ax[1].plot(ww, fit['C'] * (ww - fit['k']) ** 1.5, 'r-', label='Beverloo 2D fit: C=%.2f, k=%.2f' % (fit['C'], fit['k']))
ax[1].set_xlabel('orifice width W/d (-)'); ax[1].set_ylabel('discharge rate Q sqrt(d/g) (discs per unit time)')
ax[1].set_title('Flow rate vs orifice width'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'contact_dynamics_silo.png'), dpi=110)

anim = [r for r in runs if os.path.exists(os.path.join(r['dir'], 'frames.npy'))]
if anim:
    r = anim[0]
    F = np.load(os.path.join(r['dir'], 'frames.npy')); rad = np.load(os.path.join(r['dir'], 'radii.npy'))
    import imageio.v2 as imageio
    imgs = []
    dt_snap = 100 * r['dt']
    for k, fr in enumerate(F):
        f, a = plt.subplots(figsize=(4.0, 4.8), dpi=100)
        a.add_collection(PatchCollection([Circle((1e3 * x, 1e3 * y), 1e3 * rr) for (x, y), rr in zip(fr, rad)],
                                         facecolor='#e6a24c', edgecolor='#7a4b0f', linewidth=0.3))
        Ls = 30.0; Wm = r['W_over_d']
        a.plot([0, (Ls - Wm) / 2], [0, 0], 'k-', lw=2); a.plot([(Ls + Wm) / 2, Ls], [0, 0], 'k-', lw=2)
        a.plot([0, 0], [0, 40], 'k-', lw=2); a.plot([Ls, Ls], [0, 40], 'k-', lw=2)
        a.set_xlim(-2, 32); a.set_ylim(-12, 30); a.set_aspect('equal')
        a.set_xlabel('x (mm)'); a.set_ylabel('y (mm)')
        a.set_title('Contact dynamics (LMGC90 NSCD)\nsilo W/d=%g, t=%.2f s' % (Wm, k * dt_snap), fontsize=9)
        f.tight_layout(); f.canvas.draw()
        imgs.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(f)
    imageio.mimsave(os.path.join(OUT, 'contact_dynamics_silo.gif'), imgs, duration=1 / 12, loop=0)
    w = imageio.get_writer(os.path.join(OUT, 'contact_dynamics_silo.mp4'), fps=12, codec='libx264', pixelformat='yuv420p', macro_block_size=8)
    for im in imgs:
        w.append_data(im)
    w.close()
summary = dict(runs=[{k: v for k, v in r.items() if k not in ('t', 'n_out', 'dir')} for r in runs], beverloo_fit=fit)
json.dump(summary, open(os.path.join(OUT, 'post_results.json'), 'w'), indent=1)
print(json.dumps(summary, indent=1))
