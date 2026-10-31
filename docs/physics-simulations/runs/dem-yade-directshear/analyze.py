"""Mohr-Coulomb fits (peak and residual) of the Yade periodic triaxial runs, per Bond number.
Usage: python analyze.py <scratch> <repo_dir>"""
import sys, os, json, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sims-scratch/dem-yade-directshear'
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
series = {}
for f in sorted(glob.glob(os.path.join(src, 's3_*_Bo*_meta.json'))):
    meta = json.load(open(f))
    a = np.loadtxt(f.replace('_meta.json', '.csv'), delimiter=',', skiprows=1, ndmin=2)
    eps = a[:, 1]; s1 = a[:, 4]; s3 = 0.5 * (a[:, 2] + a[:, 3]); ev = a[:, 5]
    q = s1 - s3
    ok = eps > 0.002
    ip = int(np.argmax(np.where(ok, q, -np.inf)))
    res_m = eps >= eps.max() - 0.03
    series.setdefault(meta['Bo'], []).append(dict(
        meta=meta, eps=eps, q=q, s1=s1, s3=s3, ev=ev, ncoh=a[:, 6], ncont=a[:, 7],
        s1_peak=s1[ip], s3_peak=s3[ip], eps_peak=eps[ip], s1_res=s1[res_m].mean(), s3_res=s3[res_m].mean(),
        eps_end=eps.max()))


def mc_fit(s1, s3):
    s = 0.5 * (s1 + s3); t = 0.5 * (s1 - s3)
    k, a0 = np.polyfit(s, t, 1)
    phi = np.arcsin(k); c = a0 / np.cos(phi)
    return float(np.degrees(phi)), float(c)


out = {}
for Bo, runs in sorted(series.items()):
    runs.sort(key=lambda r: r['meta']['sigma3_Pa'])
    o = dict(runs=[])
    for r in runs:
        o['runs'].append(dict(sigma3_Pa=r['meta']['sigma3_Pa'], sigma1_peak_Pa=float(r['s1_peak']),
                              sigma3_at_peak_Pa=float(r['s3_peak']), eps_axial_peak=float(r['eps_peak']),
                              sigma1_residual_Pa=float(r['s1_res']), sigma3_residual_Pa=float(r['s3_res']),
                              eps_axial_end=float(r['eps_end']), phi_after_compaction=r['meta']['phi_after_compaction'],
                              compaction_done=r['meta']['compaction_done'], wall_s=r['meta']['wall_s'],
                              frac_contacts_cohesive_start=float(r['ncoh'][0] / max(r['ncont'][0], 1)),
                              frac_contacts_cohesive_end=float(r['ncoh'][-1] / max(r['ncont'][-1], 1)),
                              normalCohesion_Pa=r['meta']['normalCohesion_Pa'], F_adh_N=r['meta']['F_adh_N']))
    if len(runs) >= 2:
        phip, cp = mc_fit(np.array([r['s1_peak'] for r in runs]), np.array([r['s3_peak'] for r in runs]))
        phir, cr = mc_fit(np.array([r['s1_res'] for r in runs]), np.array([r['s3_res'] for r in runs]))
        o.update(peak_friction_angle_deg=phip, peak_cohesion_Pa=cp, residual_friction_angle_deg=phir, residual_cohesion_Pa=cr)
    out['Bo=%g' % Bo] = o
json.dump(out, open(os.path.join(src, 'summary.json'), 'w'), indent=1)
print(json.dumps({k: {kk: v for kk, v in o.items() if kk != 'runs'} for k, o in out.items()}, indent=1))

fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
cols = {50.0: '#1b9e77', 150.0: '#d95f02', 400.0: '#7570b3'}
ls = {5.0: '-', 50.0: '--'}
for Bo, runs in sorted(series.items()):
    for r in runs:
        s3n = r['meta']['sigma3_Pa']
        axs[0].plot(r['eps'] * 100, r['q'] / s3n, ls.get(Bo, '-'), color=cols.get(s3n, 'k'), lw=1.2,
                    label='Bo = %g, sigma3 = %g Pa' % (Bo, s3n))
        axs[0].plot(r['eps_peak'] * 100, (r['s1_peak'] - r['s3_peak']) / s3n, 'o', color=cols.get(s3n, 'k'), ms=4)
axs[0].set_xlabel('axial strain (%)'); axs[0].set_ylabel('deviator stress / confining stress, q / sigma3 (-)')
axs[0].grid(alpha=0.3); axs[0].legend(fontsize=7, ncol=2)
axs[0].set_title('Yade periodic triaxial compression (N = 600 salt-size spheres)', fontsize=9)
ax = axs[1]
mk = {5.0: 'o', 50.0: 's'}
for Bo, runs in sorted(series.items()):
    o = out['Bo=%g' % Bo]
    sp = np.array([0.5 * (r['s1_peak'] + r['s3_peak']) for r in runs]); tp = np.array([0.5 * (r['s1_peak'] - r['s3_peak']) for r in runs])
    sr = np.array([0.5 * (r['s1_res'] + r['s3_res']) for r in runs]); tr = np.array([0.5 * (r['s1_res'] - r['s3_res']) for r in runs])
    ax.plot(sp, tp, mk.get(Bo, 'o'), color='k', mfc='k', ms=6)
    ax.plot(sr, tr, mk.get(Bo, 'o'), color='k', mfc='none', ms=6)
    if 'peak_friction_angle_deg' in o:
        xs = np.linspace(0, sp.max() * 1.1, 50)
        for phi, c, lst, lab in ((o['peak_friction_angle_deg'], o['peak_cohesion_Pa'], ls.get(Bo, '-'), 'peak'),
                                 (o['residual_friction_angle_deg'], o['residual_cohesion_Pa'], ':', 'residual')):
            ph = np.radians(phi)
            ax.plot(xs, c * np.cos(ph) + xs * np.sin(ph), lst, color='C0' if Bo == 5.0 else 'C3', lw=1,
                    label='Bo = %g %s: phi = %.1f deg, c = %.1f Pa' % (Bo, lab, phi, c))
ax.set_xlabel('s = (sigma1 + sigma3)/2 (Pa)'); ax.set_ylabel('t = (sigma1 - sigma3)/2 (Pa)')
ax.set_xlim(0, None); ax.set_ylim(0, None); ax.grid(alpha=0.3); ax.legend(fontsize=7, loc='upper left')
ax.set_title('Failure states (filled: peak, open: residual) and Mohr-Coulomb fits', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(dst, 'triaxial_mohr_coulomb.png'), dpi=110)
