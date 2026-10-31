"""Post-process the three DPMFoam cases: first-arrival time of every particle at the plate,
air velocity in the mid-plane, figure + animation.  Also integrates the isolated-particle
equation of motion (Wen-Yu/Schiller-Naumann drag at alpha=1) as a reference curve.
Usage: python post_cfd.py <scratch dir with case_twoway, case_oneway, case_vacuum> <out dir>
"""
import os, re, sys, json, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

S, OUT = sys.argv[1], sys.argv[2]
NX, NY, NZ = 16, 70, 16
THR = 3.0e-3           # "arrived" = first crossing of the plane 3 mm above the plate (above any pile)
Y0 = 31.0e-3           # plug centre

def read_list(path, vec=True):
    txt = open(path).read()
    i = txt.find('(', txt.find('\n', txt.find('}')))  # first '(' after header
    body = txt[i + 1:txt.rfind(')')]
    if vec:
        nums = re.findall(r'\(([^()]*)\)', body)
        return np.array([[float(v) for v in n.split()[:3]] for n in nums])
    return np.array([float(v) for v in body.split()])

def times(case):
    ts = []
    for d in os.listdir(case):
        try:
            t = float(d)
        except ValueError:
            continue
        if t > 0:
            ts.append((t, d))
    return sorted(ts)

def internal_vec(path):
    txt = open(path).read()
    k = txt.find('internalField')
    n0 = txt.find('(', k)
    n = int(txt[k:n0].split()[-1])
    seg = txt[n0 + 1:]
    nums = re.findall(r'\(([^()]*)\)', seg[:n * 60])[:n]
    return np.array([[float(v) for v in s.split()] for s in nums])

res, frames = {}, {}
for mode in ('twoway', 'oneway', 'vacuum'):
    case = os.path.join(S, 'case_' + mode)
    ts = times(case)
    first = {}
    fr = []
    uair = []
    for t, d in ts:
        lag = os.path.join(case, d, 'lagrangian', 'kinematicCloud')
        if not os.path.exists(os.path.join(lag, 'positions')):
            continue
        P = read_list(os.path.join(lag, 'positions'))
        ids = read_list(os.path.join(lag, 'origId'), vec=False).astype(int)
        for i, y in zip(ids, P[:, 1]):
            if y < THR and i not in first:
                first[i] = t
        fr.append((t, P[:, 0].copy(), P[:, 1].copy()))
        ua = os.path.join(case, d, 'U.air')
        if mode == 'twoway' and os.path.exists(ua):
            U = internal_vec(ua).reshape(NZ, NY, NX, 3)
            uair.append((t, 0.5 * (U[NZ // 2 - 1] + U[NZ // 2])[:, :, 1]))
    n = len(fr[0][1]) if fr else 0
    arr = np.array(sorted(first.values()))
    q = lambda p: float(np.percentile(arr, p)) if len(arr) else float('nan')
    res[mode] = dict(n_particles=n, n_arrived=len(arr), t_first=q(0), t10=q(10), t50=q(50), t90=q(90),
                     t_last=q(100), spread_10_90_ms=1e3 * (q(90) - q(10)),
                     wall_s=None)
    log = os.path.join(case, 'log.DPMFoam')
    if os.path.exists(log):
        m = re.findall(r'ClockTime = (\d+) s', open(log).read())
        res[mode]['wall_s'] = int(m[-1]) if m else None
    frames[mode] = fr
    res[mode]['arrival_times'] = arr.tolist()
    if mode == 'twoway':
        frames['uair'] = uair

# isolated-particle reference ODE (same drag law as ErgunWenYu at alpha = 1: Schiller-Naumann)
def ode(d, rho=2670.0, h=Y0, rhoa=1.2, mu=1.8e-5, dt=1e-5):
    y, v, t = h, 0.0, 0.0
    while y > THR:
        re_ = rhoa * abs(v) * d / mu
        cd = 24 / max(re_, 1e-12) * (1 + 0.15 * re_ ** 0.687) if re_ < 1000 else 0.44
        fd = 0.5 * rhoa * v * abs(v) * cd * np.pi * d * d / 4
        a = -9.81 - fd / (rho * np.pi * d ** 3 / 6)
        v += a * dt; y += v * dt; t += dt
    return t, v
t100, v100 = ode(100e-6)
t35, v35 = ode(35e-6)
tvac = np.sqrt(2 * (Y0 - THR) / 9.81)
ref = dict(isolated_100um_arrival_s=t100, isolated_100um_impact_speed=abs(v100),
           isolated_35um_arrival_s=t35, isolated_35um_impact_speed=abs(v35), vacuum_point_arrival_s=tvac)

# ---------------- figure ----------------
plt.rcParams.update({'font.size': 10})
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
cols = {'twoway': '#1f77b4', 'oneway': '#d62728', 'vacuum': '#7f7f7f'}
lab = {'twoway': 'air, two-way coupled (CFD-DEM)', 'oneway': 'air, one-way (gas at rest, no contacts)',
       'vacuum': 'vacuum (DEM only)'}
for mode in ('vacuum', 'twoway', 'oneway'):
    a = np.array(res[mode]['arrival_times'])
    if len(a):
        ax[0].step(1e3 * a, np.arange(1, len(a) + 1) / res[mode]['n_particles'], where='post', color=cols[mode], label=lab[mode])
for t_, name, ls in ((tvac, 'free fall, point', ':'), (t100, 'isolated 100 um (ODE)', '--')):
    ax[0].axvline(1e3 * t_, color='k', ls=ls, lw=0.8)
    ax[0].text(1e3 * t_ + 1, 0.05, name, rotation=90, fontsize=8, va='bottom')
ax[0].set_xlabel('time after release (ms)'); ax[0].set_ylabel('fraction of plug past y = 3 mm (-)')
ax[0].set_title('Plug arrival: 846 x 100 um, 31 mm drop', fontsize=10)
ax[0].legend(fontsize=8, loc='lower right'); ax[0].grid(alpha=0.3)
if frames.get('uair'):
    # air velocity on the axis at the time the plug is mid-way
    tt = [u[0] for u in frames['uair']]
    k = int(np.argmin(np.abs(np.array(tt) - 0.5 * res['twoway']['t50'])))
    t_, uy = frames['uair'][k]
    im = ax[1].imshow(uy, origin='lower', extent=[-4, 4, 0, 35], cmap='RdBu', vmin=-abs(uy).max(), vmax=abs(uy).max(), aspect='auto')
    fr = frames['twoway'][[f[0] for f in frames['twoway']].index(t_)] if t_ in [f[0] for f in frames['twoway']] else None
    if fr is not None:
        ax[1].scatter(1e3 * fr[1], 1e3 * fr[2], s=1, c='k')
    plt.colorbar(im, ax=ax[1], label='air vertical velocity u_y (m/s)')
    ax[1].set_xlabel('x (mm)'); ax[1].set_ylabel('height above plate y (mm)')
    ax[1].set_title('two-way, t = %.0f ms: air u_y, mid-plane' % (1e3 * t_), fontsize=10)
    res['twoway']['air_uy_min_at_snapshot'] = float(uy.min())
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'cfd_dem_arrival.png'), dpi=110)

# ---------------- animation ----------------
import imageio.v2 as imageio
import imageio_ffmpeg
os.environ.setdefault('IMAGEIO_FFMPEG_EXE', imageio_ffmpeg.get_ffmpeg_exe())
imgs = []
nfr = min(len(frames[m]) for m in ('twoway', 'oneway', 'vacuum'))
for k in range(nfr):
    f, axs = plt.subplots(1, 3, figsize=(6.4, 4.0), dpi=100)
    for a, mode in zip(axs, ('vacuum', 'twoway', 'oneway')):
        t_, x, y = frames[mode][k]
        if mode == 'twoway' and k < len(frames['uair']):
            uy = frames['uair'][k][1]
            a.imshow(uy, origin='lower', extent=[-4, 4, 0, 35], cmap='RdBu', vmin=-0.5, vmax=0.5, aspect='auto')
        a.scatter(1e3 * x, 1e3 * y, s=0.6, c='k')
        a.set_xlim(-4, 4); a.set_ylim(0, 35); a.set_title({'vacuum': 'vacuum', 'twoway': 'air 2-way\n(colour: u_y air)', 'oneway': 'air 1-way'}[mode], fontsize=8)
        a.set_xlabel('x (mm)', fontsize=8); a.tick_params(labelsize=7)
    axs[0].set_ylabel('y (mm)', fontsize=8)
    f.suptitle('CFD-DEM (OpenFOAM v1912 DPMFoam): AlSi10Mg-like plug, t = %3.0f ms' % (1e3 * frames['twoway'][k][0]), fontsize=9)
    f.tight_layout()
    f.canvas.draw()
    imgs.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(f)
imageio.mimsave(os.path.join(OUT, 'cfd_dem_plug.gif'), imgs, duration=1 / 10, loop=0)
w = imageio.get_writer(os.path.join(OUT, 'cfd_dem_plug.mp4'), fps=10, codec='libx264', pixelformat='yuv420p', macro_block_size=8)
for im in imgs:
    w.append_data(im)
w.close()
json.dump(dict(cases=res, reference=ref), open(os.path.join(OUT, 'post_results.json'), 'w'), indent=1)
print(json.dumps({m: {k: v for k, v in r.items() if k != 'arrival_times'} for m, r in res.items()}, indent=1))
print(json.dumps(ref, indent=1))
