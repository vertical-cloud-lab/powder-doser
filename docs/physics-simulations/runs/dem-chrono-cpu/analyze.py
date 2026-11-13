"""Discharge rates from the PyChrono silo runs and a Beverloo fit; figure + GIF/MP4 of one run.
Usage: python analyze.py <scratch> <repo_dir> [anim_tag]"""
import sys, os, json, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sims-scratch/dem-chrono-cpu'
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
anim_tag = sys.argv[3] if len(sys.argv) > 3 else None
g = 9.81
runs = []
for f in sorted(glob.glob(os.path.join(src, 'L*_meta.json'))):
    meta = json.load(open(f))
    a = np.loadtxt(f.replace('_meta.json', '_outflow.csv'), delimiter=',', skiprows=1, ndmin=2)
    t, m = a[:, 0], a[:, 2]
    t_open = meta['t_settle']
    M = meta['total_mass_kg']
    # steady window: from 0.1 s after opening until 60 % of the inventory has left (or end of run)
    w = (t >= t_open + 0.1) & (m <= 0.6 * M)
    if w.sum() >= 5:
        k, b = np.polyfit(t[w], m[w], 1)
    else:
        k = b = float('nan')
    rho_b = M / ((meta['box_mm'] * 1e-3) ** 2 * meta['fill_height_m'])
    runs.append(dict(meta=meta, t=t, m=m, w=w, Wdot=k, b=b, rho_b=rho_b))
d_mean = float(np.sum(np.array(runs[0]['meta']['d_m']) * np.array(runs[0]['meta']['nfrac'])))
out = dict(d_mean_m=d_mean, runs=[])
for r in runs:
    out['runs'].append(dict(L_mm=r['meta']['L_mm'], L_over_d=r['meta']['L_mm'] * 1e-3 / d_mean,
                            mass_flow_g_s=r['Wdot'] * 1e3, bulk_density_kg_m3=r['rho_b'], n_out=r['meta']['n_out'],
                            n=r['meta']['n'], fill_height_mm=r['meta']['fill_height_m'] * 1e3, wall_s=r['meta']['wall_s'],
                            window_points=int(r['w'].sum())))
good = [r for r in runs if np.isfinite(r['Wdot']) and r['Wdot'] > 0]
rho_b = float(np.mean([r['rho_b'] for r in runs]))
out['bulk_density_mean_kg_m3'] = rho_b
if len(good) >= 2:
    Ls = np.array([r['meta']['L_mm'] * 1e-3 for r in good]); Ws = np.array([r['Wdot'] for r in good])
    # Beverloo for a square orifice of side L: W = C_sq rho_b sqrt(g) (L - k d)^2.5 ; linear in L after ^(1/2.5)
    y = Ws ** 0.4
    s, i0 = np.polyfit(Ls, y, 1)
    k_fit = -i0 / s / d_mean
    C_sq = s ** 2.5 / (rho_b * np.sqrt(g))
    out.update(beverloo_k=float(k_fit), beverloo_C_square=float(C_sq), beverloo_C_circular_equiv=float(C_sq * np.pi / 4))
    # also C with k fixed at 1.5
    C15 = float(np.mean(Ws / (rho_b * np.sqrt(g) * (Ls - 1.5 * d_mean) ** 2.5)))
    out['beverloo_C_square_k1p5'] = C15
json.dump(out, open(os.path.join(src, 'summary.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))

fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.0))
cols = plt.cm.plasma(np.linspace(0.1, 0.8, len(runs)))
for r, c in zip(runs, cols):
    t0 = r['meta']['t_settle']
    axs[0].plot(r['t'] - t0, r['m'] * 1e3, color=c, label='L = %.1f mm (L/d = %.1f)' % (r['meta']['L_mm'], r['meta']['L_mm'] * 1e-3 / d_mean))
    if np.isfinite(r['Wdot']):
        tt = r['t'][r['w']]
        axs[0].plot(tt - t0, (r['Wdot'] * tt + r['b']) * 1e3, 'k--', lw=0.8)
axs[0].set_xlabel('time since orifice opened (s)'); axs[0].set_ylabel('discharged mass (g)')
axs[0].set_xlim(-0.05, None); axs[0].grid(alpha=0.3); axs[0].legend(fontsize=8)
axs[0].set_title('PyChrono 10.0 ChSystemSMC (CPU): silo discharge', fontsize=9)
ax = axs[1]
Lp = np.array([r['meta']['L_mm'] for r in runs]); Wp = np.array([r['Wdot'] * 1e3 for r in runs])
ax.plot(Lp, Wp, 'o', color='C3', label='DEM (steady-window slope)')
if 'beverloo_k' in out:
    xs = np.linspace(out['beverloo_k'] * d_mean * 1e3 + 0.01, Lp.max() * 1.1, 100)
    ax.plot(xs, 1e3 * out['beverloo_C_square'] * rho_b * np.sqrt(g) * (xs * 1e-3 - out['beverloo_k'] * d_mean) ** 2.5, 'k-',
            label='Beverloo fit: C_sq = %.2f (C_circ-equiv = %.2f), k = %.2f' % (out['beverloo_C_square'], out['beverloo_C_circular_equiv'], out['beverloo_k']))
    xs2 = np.linspace(1.5 * d_mean * 1e3 + 0.01, Lp.max() * 1.1, 100)
    ax.plot(xs2, 1e3 * 0.58 * 4 / np.pi * rho_b * np.sqrt(g) * (xs2 * 1e-3 - 1.5 * d_mean) ** 2.5, ':', color='gray',
            label='Beverloo textbook: C = 0.58 (x 4/pi for a square), k = 1.5')
ax.set_xlabel('square orifice side L (mm)'); ax.set_ylabel('mass flow rate W (g/s)'); ax.grid(alpha=0.3)
ax.legend(fontsize=7.5, loc='upper left'); ax.set_xlim(0, None); ax.set_ylim(0, None)
ax.set_title('Mass flow vs orifice size (coarse-grained salt, d = %.2f mm)' % (d_mean * 1e3), fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(dst, 'chrono_silo_beverloo.png'), dpi=110)

if anim_tag:
    import imageio.v2 as imageio
    z = np.load(os.path.join(src, anim_tag + '_snaps.npz'))
    snaps, ts = z['snaps'], z['t']
    meta = json.load(open(os.path.join(src, anim_tag + '_meta.json')))
    W = meta['box_mm'] / 2; L = meta['L_mm'] / 2
    frames = []
    for sn, t in zip(snaps, ts):
        fig, ax = plt.subplots(figsize=(4.0, 4.8), dpi=100)
        m = (np.abs(sn[:, 1]) < 3e-3) & (sn[:, 4] > 0.5)
        ax.scatter(sn[m, 0] * 1e3, sn[m, 2] * 1e3, s=(sn[m, 3] * 1e3 * 6.5) ** 2, c=sn[m, 2] * 1e3, cmap='viridis',
                   vmin=-6, vmax=40, edgecolors='none')
        ax.plot([-W, -W, -L], [45, 0, 0], 'k-', lw=2); ax.plot([W, W, L], [45, 0, 0], 'k-', lw=2)
        ax.set_xlim(-W - 1, W + 1); ax.set_ylim(-8, 45); ax.set_aspect('equal')
        ax.set_xlabel('x (mm)', fontsize=8); ax.set_ylabel('z (mm)', fontsize=8); ax.tick_params(labelsize=7)
        ax.set_title('Silo discharge - PyChrono %s ChSystemSMC\nL = %.0f mm, slice |y|<3 mm, t = %.2f s (open at %.2f s)'
                     % (meta['chrono_version'], meta['L_mm'], t, meta['t_settle']), fontsize=7.5)
        fig.tight_layout(); fig.canvas.draw()
        frames.append(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(fig)
    h_, w_ = frames[0].shape[:2]
    frames = [f[:h_ - h_ % 2, :w_ - w_ % 2] for f in frames]
    imageio.mimsave(os.path.join(dst, 'chrono_silo_discharge.gif'), frames, duration=1 / 12, loop=0)
    wr = imageio.get_writer(os.path.join(dst, 'chrono_silo_discharge.mp4'), fps=12, codec='libx264', pixelformat='yuv420p',
                            ffmpeg_params=['-crf', '23'])
    for f in frames: wr.append_data(f)
    wr.close(); print('frames', len(frames), frames[0].shape)
