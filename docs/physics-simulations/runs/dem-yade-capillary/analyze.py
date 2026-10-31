"""Post-process the Yade column-collapse runs: final heap profiles, slope angle, H_f/H_0, runout, figure, GIF/MP4.
Usage: python analyze.py <scratch_dir_with_npz> <repo_run_dir>"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sims-scratch/dem-yade-capillary'
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
cases = [('dry', 'dry'), ('wet01', 'W = 0.1 % (vol.)'), ('wet1', 'W = 1 % (vol.)')]
colors = {'dry': '#4C72B0', 'wet01': '#DD8452', 'wet1': '#55A868'}
res = {}
data = {}
for c, lab in cases:
    f = os.path.join(src, c + '_snaps.npz')
    if not os.path.exists(f):
        print('missing', f); continue
    z = np.load(f)
    meta = json.load(open(os.path.join(src, c + '_meta.json')))
    snaps, t = z['snaps'], z['t']
    fin = snaps[-1]
    r = np.hypot(fin[:, 0], fin[:, 1]); top = fin[:, 2] + fin[:, 3]
    dmean = 1.7e-3
    edges = np.arange(0, r.max() + 1e-3, 1.0e-3)
    rc, h = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (r >= a) & (r < b)
        if m.sum() >= 1:
            rc.append(0.5 * (a + b)); h.append(top[m].max())
    rc, h = np.array(rc), np.array(h)
    Hf = float(top[r < 2.5e-3].max()) if np.any(r < 2.5e-3) else float(top.max())
    Rf = float(np.percentile(r, 99) + dmean / 2)
    sel = (h > 0.15 * Hf) & (h < 0.85 * Hf) & (rc > 1e-3)
    if sel.sum() >= 3:
        k, b0 = np.polyfit(rc[sel], h[sel], 1)
        ang = float(np.degrees(np.arctan(-k)))
    else:
        k = b0 = np.nan; ang = float('nan')
    H0, R0 = meta['H0'], meta['R0']
    res[c] = dict(label=lab, W=meta['W'], Vb_m3=meta['Vb'], H0_mm=H0 * 1e3, R0_mm=R0 * 1e3, Hf_mm=Hf * 1e3,
                  Hf_over_H0=Hf / H0, Rf_mm=Rf * 1e3, Rf_over_R0=Rf / R0, slope_angle_deg=ang,
                  n_fit_bins=int(sel.sum()), final_liquid_bridges=meta['final_bridges'],
                  t_end_s=meta['t_end'], wall_s=meta['wall_s'], steps=meta['steps'])
    data[c] = dict(rc=rc, h=h, k=k, b0=b0, sel=sel, snaps=snaps, t=t, meta=meta, lab=lab)
    print(c, json.dumps(res[c]))

# Bond number (Willett/Lambert contact limit F = 2 pi R gamma cos(theta), mean particle)
m0 = list(data.values())[0]['meta']
Rm = 0.85e-3
F = 2 * np.pi * Rm * m0['gamma'] * np.cos(m0['theta'])
mg = m0['rho'] * np.pi / 6 * (2 * Rm) ** 3 * 9.81
res['bond_number_mean_particle'] = float(F / mg)
json.dump(res, open(os.path.join(src, 'summary.json'), 'w'), indent=1)

# ---------------- figure ----------------
fig = plt.figure(figsize=(10, 6.2))
gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.15], hspace=0.38, wspace=0.25)
for j, (c, lab) in enumerate(cases):
    if c not in data: continue
    ax = fig.add_subplot(gs[0, j])
    fin = data[c]['snaps'][-1]
    m = np.abs(fin[:, 1]) < 2.5e-3
    ax.scatter(fin[m, 0] * 1e3, fin[m, 2] * 1e3, s=(fin[m, 3] * 1e3 * 7) ** 2, c=colors[c], edgecolors='none')
    R0 = data[c]['meta']['R0'] * 1e3; H0 = data[c]['meta']['H0'] * 1e3
    ax.plot([-R0, -R0, R0, R0], [0, H0, H0, 0], 'k--', lw=0.8)
    ax.set_xlim(-32, 32); ax.set_ylim(0, 30); ax.set_aspect('equal')
    ax.set_title('%s: final deposit\n(slice |y| < 2.5 mm)' % lab, fontsize=9)
    ax.set_xlabel('x (mm)'); ax.set_ylabel('z (mm)') if j == 0 else None
ax = fig.add_subplot(gs[1, :])
for c, lab in cases:
    if c not in data: continue
    dd = data[c]
    ax.plot(dd['rc'] * 1e3, dd['h'] * 1e3, 'o-', ms=3, color=colors[c],
            label='%s: slope %.0f deg, H_f/H_0 = %.2f, R_f/R_0 = %.2f' % (lab, res[c]['slope_angle_deg'], res[c]['Hf_over_H0'], res[c]['Rf_over_R0']))
    if np.isfinite(dd['k']):
        rr = dd['rc'][dd['sel']]
        ax.plot(rr * 1e3, (dd['k'] * rr + dd['b0']) * 1e3, '-', color='k', lw=1)
R0 = m0['R0'] * 1e3
ax.axvline(R0, color='gray', ls=':', lw=1); ax.text(R0 + 0.3, 1, 'initial column radius', fontsize=8, color='gray')
ax.set_xlabel('radial distance from column axis r (mm)'); ax.set_ylabel('surface height h(r) (mm)')
ax.set_xlim(0, 32); ax.set_ylim(0, None); ax.legend(fontsize=8, loc='upper right'); ax.grid(alpha=0.3)
ax.set_title('Yade column collapse, coarse-grained salt (N = %d, d = 1.44-1.96 mm), Willett liquid bridges, Bo = %.1f'
             % (m0['N'], res['bond_number_mean_particle']), fontsize=9)
fig.savefig(os.path.join(dst, 'capillary_column_collapse.png'), dpi=110, bbox_inches='tight')
plt.close(fig)

# ---------------- animation ----------------
import imageio.v2 as imageio
frames = []
nt = min(len(data[c]['t']) for c in data)
for i in range(nt):
    fig, axs = plt.subplots(1, 3, figsize=(6.4, 2.4), dpi=100)
    for ax, (c, lab) in zip(axs, cases):
        if c not in data: continue
        sn = data[c]['snaps'][i]; m = np.abs(sn[:, 1]) < 2.5e-3
        ax.scatter(sn[m, 0] * 1e3, sn[m, 2] * 1e3, s=(sn[m, 3] * 1e3 * 2.2) ** 2, c=colors[c], edgecolors='none')
        ax.set_xlim(-30, 30); ax.set_ylim(0, 45); ax.set_aspect('equal')
        ax.set_title(lab, fontsize=7); ax.tick_params(labelsize=6); ax.set_xlabel('x (mm)', fontsize=6)
    axs[0].set_ylabel('z (mm)', fontsize=6)
    tr = data['dry']['meta']['t_removed'] if 'dry' in data else 0.2
    fig.suptitle('Column collapse, liquid bridges - Yade %s   t = %.2f s (wall removed at %.2f s)'
                 % ('daily 2026-10-24', data[cases[0][0]]['t'][i], tr), fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    frames.append(img); plt.close(fig)
h_, w_ = frames[0].shape[:2]
frames = [f[:h_ - h_ % 2, :w_ - w_ % 2] for f in frames]
imageio.mimsave(os.path.join(dst, 'capillary_column_collapse.gif'), frames, duration=1 / 10, loop=0)
import imageio_ffmpeg
wr = imageio.get_writer(os.path.join(dst, 'capillary_column_collapse.mp4'), fps=10, codec='libx264',
                        pixelformat='yuv420p', ffmpeg_params=['-crf', '23'])
for f in frames: wr.append_data(f)
wr.close()
print('frames', len(frames), frames[0].shape)
