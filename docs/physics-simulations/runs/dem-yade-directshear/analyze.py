"""Mohr-Coulomb fit of the Yade periodic triaxial runs (peak and residual). Usage: python analyze.py <scratch> <repo_dir>"""
import sys, os, json, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

src = sys.argv[1] if len(sys.argv) > 1 else '/tmp/sims-scratch/dem-yade-directshear'
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
runs = []
for f in sorted(glob.glob(os.path.join(src, 's3_*_meta.json'))):
    meta = json.load(open(f))
    csv = f.replace('_meta.json', '.csv')
    a = np.loadtxt(csv, delimiter=',', skiprows=1, ndmin=2)
    eps = a[:, 1]; s1 = a[:, 4]; s3 = 0.5 * (a[:, 2] + a[:, 3]); ev = a[:, 5]
    q = s1 - s3
    ok = eps > 0.002
    ip = np.argmax(q * ok)
    res_m = eps >= eps.max() - 0.03
    runs.append(dict(meta=meta, eps=eps, q=q, s1=s1, s3=s3, ev=ev, ncoh=a[:, 6], ncont=a[:, 7],
                     s1_peak=s1[ip], s3_peak=s3[ip], eps_peak=eps[ip],
                     s1_res=s1[res_m].mean(), s3_res=s3[res_m].mean(), eps_end=eps.max()))
out = {'runs': []}
def mc_fit(s1, s3):
    s = 0.5 * (s1 + s3); t = 0.5 * (s1 - s3)
    k, a0 = np.polyfit(s, t, 1)
    phi = np.arcsin(k); c = a0 / np.cos(phi)
    return float(np.degrees(phi)), float(c), s, t
for r in runs:
    out['runs'].append(dict(sigma3_Pa=r['meta']['sigma3_Pa'], sigma1_peak_Pa=float(r['s1_peak']), sigma3_at_peak_Pa=float(r['s3_peak']),
                            eps_axial_peak=float(r['eps_peak']), sigma1_residual_Pa=float(r['s1_res']),
                            sigma3_residual_Pa=float(r['s3_res']), eps_axial_end=float(r['eps_end']),
                            phi_after_compaction=r['meta']['phi_after_compaction'], compaction_done=r['meta']['compaction_done'],
                            wall_s=r['meta']['wall_s'], frac_contacts_cohesive_end=float(r['ncoh'][-1] / max(r['ncont'][-1], 1))))
if len(runs) >= 2:
    s1p = np.array([r['s1_peak'] for r in runs]); s3p = np.array([r['s3_peak'] for r in runs])
    s1r = np.array([r['s1_res'] for r in runs]); s3r = np.array([r['s3_res'] for r in runs])
    phip, cp, sp_, tp = mc_fit(s1p, s3p)
    phir, cr, sr_, tr = mc_fit(s1r, s3r)
    out.update(peak_friction_angle_deg=phip, peak_cohesion_Pa=cp, residual_friction_angle_deg=phir, residual_cohesion_Pa=cr)
json.dump(out, open(os.path.join(src, 'summary.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))

fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2))
cols = plt.cm.viridis(np.linspace(0, 0.85, len(runs)))
for r, c in zip(runs, cols):
    axs[0].plot(r['eps'] * 100, r['q'] / r['s3'].mean(), color=c, label='sigma3 = %g Pa' % r['meta']['sigma3_Pa'])
    axs[0].plot(r['eps_peak'] * 100, (r['s1_peak'] - r['s3_peak']) / r['s3'].mean(), 'o', color=c, ms=5)
axs[0].set_xlabel('axial strain (%)'); axs[0].set_ylabel('deviator stress / confining stress, q / sigma3 (-)')
axs[0].legend(fontsize=8); axs[0].grid(alpha=0.3); axs[0].set_title('Periodic triaxial compression, cohesive contacts (Bo = 5)', fontsize=9)
ax = axs[1]
th = np.linspace(0, np.pi, 100)
for r, c in zip(runs, cols):
    for s1_, s3_, ls in ((r['s1_peak'], r['s3_peak'], '-'), (r['s1_res'], r['s3_res'], ':')):
        cen, rad = 0.5 * (s1_ + s3_), 0.5 * (s1_ - s3_)
        ax.plot(cen + rad * np.cos(th), rad * np.sin(th), ls, color=c, lw=1)
if 'peak_friction_angle_deg' in out:
    xs = np.linspace(0, max(s1p.max(), s1r.max()) * 1.05, 50)
    ax.plot(xs, out['peak_cohesion_Pa'] + xs * np.tan(np.radians(out['peak_friction_angle_deg'])), 'k-',
            label='peak: phi = %.1f deg, c = %.1f Pa' % (out['peak_friction_angle_deg'], out['peak_cohesion_Pa']))
    ax.plot(xs, out['residual_cohesion_Pa'] + xs * np.tan(np.radians(out['residual_friction_angle_deg'])), 'k:',
            label='residual: phi = %.1f deg, c = %.1f Pa' % (out['residual_friction_angle_deg'], out['residual_cohesion_Pa']))
ax.set_xlabel('normal stress sigma (Pa)'); ax.set_ylabel('shear stress tau (Pa)'); ax.set_aspect('equal')
ax.set_xlim(0, None); ax.set_ylim(0, None); ax.legend(fontsize=8, loc='upper left'); ax.grid(alpha=0.3)
ax.set_title('Mohr circles (solid: peak, dotted: residual) and Mohr-Coulomb envelopes', fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(dst, 'triaxial_mohr_coulomb.png'), dpi=110)
