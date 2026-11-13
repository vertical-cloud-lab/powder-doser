"""Post-process the 4C PASI run: membrane centre deflection vs time, particle positions,
figure + animation.  Usage: python post_4c.py <run dir with out-vtk-files> <out dir>"""
import os, re, sys, glob, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RUN, OUT = sys.argv[1], sys.argv[2]
V = os.path.join(RUN, 'out-vtk-files')

def arrays(path):
    txt = open(path).read()
    out = {}
    t = re.search(r'Name="TIME"[^>]*>\s*([-+0-9.eE]+)', txt)
    out['TIME'] = float(t.group(1)) if t else None
    pts = re.search(r'<Points>\s*<DataArray[^>]*>(.*?)</DataArray>', txt, re.S)
    out['points'] = np.array(pts.group(1).split(), float).reshape(-1, 3)
    for m in re.finditer(r'<DataArray[^>]*Name="([^"]+)"[^>]*NumberOfComponents="(\d+)"[^>]*>(.*?)</DataArray>', txt, re.S):
        name, nc, data = m.group(1), int(m.group(2)), m.group(3)
        try:
            out[name] = np.array(data.split(), float).reshape(-1, nc)
        except ValueError:
            pass
    for m in re.finditer(r'<DataArray[^>]*Name="([^"]+)"[^>]*format="ascii"\s*>(.*?)</DataArray>', txt, re.S):
        if m.group(1) not in out:
            try:
                out[m.group(1)] = np.array(m.group(2).split(), float)
            except ValueError:
                pass
    return out

sfiles = sorted(glob.glob(os.path.join(V, 'structure-*-0.vtu')))
pfiles = sorted(glob.glob(os.path.join(V, 'particle-phase1-owned-*-0.vtu')))
T, wc, frames = [], [], []
for sf in sfiles:
    step = sf.split('-')[-2]
    pf = os.path.join(V, 'particle-phase1-owned-%s-0.vtu' % step)
    S = arrays(sf)
    X = S['points']; U = S['displacement']
    ic = np.argsort(np.hypot(X[:, 0], X[:, 1]))[:4]          # 4 nodes nearest the centre
    t = S['TIME'] if S['TIME'] is not None else float(step) * 5e-6
    T.append(t); wc.append(U[ic, 2].mean())
    P = arrays(pf) if os.path.exists(pf) else None
    frames.append((t, X + U, P['points'] if P is not None else np.zeros((0, 3))))
T, wc = np.array(T), np.array(wc)
order = np.argsort(T); T, wc = T[order], wc[order]; frames = [frames[i] for i in order]

# reference: static deflection of the same membrane under the dose weight is not computed
# separately; we report the late-time mean (last 20 % of the run) as the quasi-static value.
late = T > 0.8 * T.max()
w_late = float(wc[late].mean()) if late.any() else float('nan')
imin = int(np.argmin(wc))
after = T > T[imin]
zc = T[after][np.argmax(wc[after] > 0)] if (wc[after] > 0).any() else float('nan')
res = dict(t_end=float(T.max()), n_frames=len(T), w_centre_min_mm=float(wc.min() * 1e3), t_at_min_ms=float(T[imin] * 1e3),
           w_centre_max_up_mm=float(wc.max() * 1e3), t_at_max_up_ms=float(T[int(np.argmax(wc))] * 1e3),
           t_first_upward_ms=float(zc * 1e3), n_particles=int(len(frames[-1][2])))
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
ax[0].plot(1e3 * T, 1e3 * wc, 'o-', ms=3)
ax[0].axvline(23.8, color='k', ls=':', lw=0.8, label='first grain contact (free fall, 23.8 ms)')
ax[0].axhline(0, color='0.6', lw=0.6)
ax[0].set_xlabel('time (ms)'); ax[0].set_ylabel('membrane centre deflection w (mm)')
ax[0].set_title('4C PASI: 11 mg NaCl dose dropped 3 mm onto a membrane'); ax[0].grid(alpha=0.3); ax[0].legend(fontsize=8)
t, XS, PP = frames[imin]
sel = np.abs(XS[:, 1] - XS[np.argmin(np.abs(XS[:, 1])), 1]) < 1e-4
xs = XS[sel]; o = np.argsort(xs[:, 0])
ax[1].plot(1e3 * xs[o, 0], 1e3 * xs[o, 2], 'k.-', label='membrane (row of nodes nearest y=0)')
if len(PP):
    ax[1].scatter(1e3 * PP[:, 0], 1e3 * PP[:, 2], s=6, c='tab:orange', label='grains (all, projected)')
ax[1].set_xlabel('x (mm)'); ax[1].set_ylabel('z (mm), vertical exaggeration'); ax[1].set_title('state at max deflection, t = %.1f ms' % (1e3 * t))
ax[1].set_ylim(1e3 * xs[:, 2].min() - 0.15, (1e3 * PP[:, 2].max() + 0.4) if len(PP) else 1.0)
ax[1].legend(fontsize=7, loc='upper right'); ax[1].grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, 'dem_fem_membrane.png'), dpi=110)

import imageio.v2 as imageio
imgs = []
for (t, XS, PP) in frames:
    f, a = plt.subplots(figsize=(6.4, 3.2), dpi=100)
    sel = np.abs(XS[:, 1] - XS[np.argmin(np.abs(XS[:, 1])), 1]) < 1e-4
    xs = XS[sel]; o = np.argsort(xs[:, 0])
    a.plot(1e3 * xs[o, 0], 1e3 * xs[o, 2], 'k-', lw=2)
    if len(PP):
        a.scatter(1e3 * PP[:, 0], 1e3 * PP[:, 2], s=8, c='tab:orange')
    a.set_xlim(-9, 9); a.set_ylim(-2.5, 4.0); a.set_aspect('equal')
    a.set_xlabel('x (mm)'); a.set_ylabel('z (mm)')
    a.set_title('DEM-FEM coupling (4C PASI): grains on a membrane, t = %5.1f ms' % (1e3 * t), fontsize=9)
    f.tight_layout(); f.canvas.draw()
    imgs.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(f)
imageio.mimsave(os.path.join(OUT, 'dem_fem_membrane.gif'), imgs, duration=1 / 10, loop=0)
w = imageio.get_writer(os.path.join(OUT, 'dem_fem_membrane.mp4'), fps=10, codec='libx264', pixelformat='yuv420p', macro_block_size=8)
for im in imgs:
    w.append_data(im)
w.close()
res['t_ms'] = (1e3 * T).tolist(); res['w_centre_mm'] = (1e3 * wc).tolist()
json.dump(res, open(os.path.join(OUT, 'post_results.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('t_ms', 'w_centre_mm')}, indent=1))
