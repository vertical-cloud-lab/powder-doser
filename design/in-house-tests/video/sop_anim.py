"""SOP animations: each test runs once on its apparatus, with the signal it records drawn as an inset.

Motion is scripted from the SOP; the powder is drawn as point sprites. Where the DEM worker's
trajectories exist (../sim/dem/frames/*.npz) the heap, drum and spreading SOPs use them; otherwise a
scripted stand-in is used and the caption says "illustration".
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh

import assemblies as A
import parts as P
from engine import FPS, Inset, Scene, Writer, ease, overlay, rot_about, T

HERE = Path(__file__).resolve().parent
DEM = HERE.parent / "sim" / "dem" / "frames"
RNG = np.random.default_rng(7)
SAND = "#c9a46a"


def _load_dem(name):
    """Load ../sim/dem/frames/<name>.npz (or the first file matching the glob <name>)."""
    f = DEM / f"{name}.npz"
    if not f.exists():
        hits = sorted(DEM.glob(f"{name}.npz")) if any(ch in name for ch in "*?[") else []
        if not hits:
            return None
        f = hits[0]
    d = np.load(f)
    out = {k: d[k] for k in d.files}
    out["_file"] = f.name
    return out


def _dem_pts(dem, k):
    p = np.asarray(dem["pos"][k], float)
    return p[~np.isnan(p).any(1)]


def _scene(key):
    a = A.ASSEMBLIES[key]()
    for c in a["comps"]:              # see into the balance: the breeze break almost clear
        if c.label == "breeze break":
            c.opacity = 0.06
    sc = Scene(a["comps"])
    return a, sc


def _idx(a, label_start):
    return [i for i, c in enumerate(a["comps"]) if c.label.startswith(label_start)]


def _frame(w, sc, a, caption, inset=None, step="", tag="SOP"):
    w.add(overlay(sc.grab(), title=a["title"], caption=caption, step=step, tag=tag, inset=inset))


def _captions(test_no, fallback):
    f = HERE.parent / "software" / "sop" / "steps.json"
    try:
        d = json.loads(f.read_text())
        steps = d.get(str(test_no)) or d.get(f"{test_no}")
        if steps and len(steps) >= 3:
            return [s["caption"] for s in steps]
    except Exception:  # noqa: BLE001
        pass
    return fallback


def stream(p0, p1, n, t, speed=1.0, spread=0.6):
    """Grains falling from p0 to p1 (a vertical-ish stream), phase-shifted by t."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    u = (np.arange(n) / n + t * speed) % 1.0
    pts = p0 + (p1 - p0) * (u ** 2)[:, None]
    pts[:, :2] += RNG.normal(0, spread, (n, 2)) * (0.3 + u[:, None])
    return pts


def cone_points(r, h, z0, n, apex_xy=(0.0, 0.0)):
    """Points filling a cone (heap) of base radius r and height h on z0."""
    rr = r * np.sqrt(RNG.random(n))
    th = RNG.random(n) * 2 * math.pi
    zmax = h * (1 - rr / r)
    z = z0 + zmax * RNG.random(n) ** 0.35
    return np.c_[apex_xy[0] + rr * np.cos(th), apex_xy[1] + rr * np.sin(th), z]


# --------------------------------------------------------------------------------------------------
# 1. heap
# --------------------------------------------------------------------------------------------------

def sop_heap(w: Writer):
    a, sc = _scene("t01_heap")
    caps = _captions(1, ["Tilt the doser to 45° (a 45)", "Turn the auger one revolution (r 360)",
                         "Photograph the silhouette; log the balance", "Repeat until the heap stops growing",
                         "Fit both flanks: angle of repose", "Tip the heap back into the jar; pour 3 heaps"])
    z_top = A.RISER_Z + 160 + 4.0
    outlet = np.array([0.0, 0.0, z_top + 12.0])
    aug = _idx(a, "doser auger")[0]
    M0 = a["comps"][aug].M
    axis = trimesh.transformations.rotation_matrix(math.radians(-(90 - 45)), [1, 0, 0])[:3, :3] @ np.array([0, 0, 1.0])
    dem = _load_dem("t1_heap_d20_coh") or _load_dem("t1_heap_d20_dry")
    aor = 34.0
    rev_n, per_rev = 14, int(0.9 * FPS)
    masses, revs = [], []
    inset = Inset((880, 80, 1260, 330), "revolutions", "heap g", (0, rev_n), (0, 1.2), title="Heap mass (balance)")
    frames_total = rev_n * per_rev
    grain_m = None
    if dem is not None:
        R = float(dem.get("pedestal_R_mm", 10.0))
        grain_m = 2165e-9 * 4 / 3 * np.pi * np.asarray(dem["r"], float) ** 3      # g, r in mm
        inset.ylim = (0, 0.5)
    for f in range(frames_total):
        t = f / frames_total
        rev = f / per_rev
        sc.pose(aug, rot_about(outlet, axis, 360 * rev) @ M0)
        h_full = 10 * math.tan(math.radians(aor))
        grow = min(1.0, (t * 1.25) ** 0.7)
        h = h_full * grow
        r = min(10.0, h / math.tan(math.radians(aor)) if h > 0 else 0.1)
        n_heap = int(200 + 2600 * grow)
        if dem is not None:
            k = min(len(dem["pos"]) - 1, int(t * (len(dem["pos"]) - 1)))
            raw = np.asarray(dem["pos"][k], float)
            ok = ~np.isnan(raw).any(1)
            heap = raw[ok] + np.array([0, 0, z_top])
            on = ok & (np.hypot(raw[:, 0], raw[:, 1]) < R) & (raw[:, 2] > 0.3) & (raw[:, 2] < 9.5)
            mass_now = float(grain_m[on].sum())
            sc.particles("heap", heap, SAND, 4.0)
            sc.particles("fall", np.zeros((0, 3)), SAND, 3.0)
        else:
            heap = cone_points(max(r, 0.5), max(h, 0.2), z_top, n_heap)
            fall = stream(outlet + [0, 0, -1.5], [0, 0, z_top + h], 120, f / FPS, speed=1.6, spread=0.25)
            sc.particles("heap", heap, SAND, 4.0)
            sc.particles("fall", fall, SAND, 3.0)
            mass_now = None
        m = mass_now if mass_now is not None else 1.1 * grow - (0.08 if 0.55 < t < 0.58 else 0.0)
        if f % 4 == 0:
            revs.append(rev)
            masses.append(max(0.0, m))
        inset.series = [{"x": revs, "y": masses, "color": (42, 157, 143, 255), "style": "line"}]
        if t > 0.8:
            inset.note = f"flank fit: {aor:.0f}° (illustration)" if dem is None else f"DEM ({dem['_file'][:-4]}), shown as poured"
        sc.camera((0, 0, z_top + 2), -30 + 20 * t, 8, 120)
        cap = caps[min(len(caps) - 1, int(t * len(caps)))]
        _frame(w, sc, a, cap, inset, step=f"rev {int(rev) + 1}")
    sc.close()


# --------------------------------------------------------------------------------------------------
# 2. bulk and tapped density
# --------------------------------------------------------------------------------------------------

def sop_density(w: Writer):
    a, sc = _scene("t02_density")
    caps = _captions(2, ["Fill the cylinder by doser to 6 g (on the balance)", "Photograph the poured column: bulk density",
                         "Cylinder into the cam-drop tapper", "3 mm drops at 250 taps/min", "Photograph after 1, 2, 5 ... 1250 taps",
                         "Fit Kawakita; Hausner = rho_tap / rho_bulk"])
    cam_i = _idx(a, "snail cam")[0]
    car = sc.group("carriage")
    pw = sc.group("powder")
    base = {i: a["comps"][i].M.copy() for i in car + pw + [cam_i]}
    shaft_pt, shaft_dir = np.array([0, 28, P.TAP_SHAFT_Z]), np.array([0, 1.0, 0])
    ac, bc = 0.16, 0.08                       # Kawakita a, b (illustration)
    h0 = 60.0
    taps_axis, h_axis = [], []
    inset = Inset((880, 80, 1260, 330), "taps", "column mm", (1, 1250), (48, 62), title="Column height", logx=True)
    n_real = int(4.0 * FPS)                   # 4 s at real speed (about 17 taps)
    n_ff = int(8.0 * FPS)                     # then fast-forward to 1250 taps
    total = n_real + n_ff
    for f in range(total):
        if f < n_real:
            ts = f / FPS
            ang = 360 * (250 / 2 / 60) * ts       # cam rev/s = 250 taps/min / 2 lobes
            N = 250 / 60 * ts
        else:
            u = (f - n_real) / n_ff
            N = 17 * (1250 / 17) ** u
            ang = 360 * N / 2
        phase = (ang % 180) / 180
        lift = 3.0 * max(0.0, (phase - 0.14) / 0.86) if phase < 0.985 else 0.0
        h = h0 * (1 - ac * bc * N / (1 + bc * N))
        sc.pose(cam_i, rot_about(shaft_pt, shaft_dir, ang) @ base[cam_i])
        for i in car:
            M = base[i].copy(); M[2, 3] += lift; sc.pose(i, M)
        for i in pw:
            M = base[i].copy(); M[2, 3] += lift; M[:3, 2] *= h / h0; sc.pose(i, M)
        if f % 3 == 0 and N >= 1:
            taps_axis.append(max(1.0, N)); h_axis.append(h)
        inset.series = [{"x": taps_axis, "y": h_axis, "color": (123, 94, 167, 255), "style": "line"}]
        inset.note = f"{int(N)} taps"
        sc.camera((0, 0, 50), -55 + 15 * f / total, 15, 330)
        cap = caps[min(len(caps) - 1, 2 + int(4 * f / total))] if len(caps) > 5 else caps[-1]
        _frame(w, sc, a, cap, inset, step=f"{int(N)} taps")
    sc.close()


# --------------------------------------------------------------------------------------------------
# 3. tilting plate
# --------------------------------------------------------------------------------------------------

def sop_tilt(w: Writer):
    a, sc = _scene("t03_tilt")
    caps = _captions(3, ["Fill the ring on 0.5 mm shims; strike off; pull the shims", "Add the lid: 150 Pa",
                         "Tilt at 0.5°/s; the IMU logs the angle", "Slip: the ring moves 0.5 mm (camera) and the IMU sees a jolt",
                         "Wall friction angle = slip angle; repeat at 3 stresses", "Mode B: layer start angle for 1-5 mm layers"])
    plate = sc.group("plate"); ring = sc.group("ring"); pin = sc.group("pinion")
    base = {i: a["comps"][i].M.copy() for i in plate + ring + pin}
    hinge_pt, hinge_dir = np.array([0, 0, P.HINGE_Z]), np.array([1.0, 0, 0])
    sz = P.HINGE_Z - P.CENTRE_D
    slip = 24.5
    angs, ts = [], []
    inset = Inset((880, 80, 1260, 330), "time s", "plate angle °", (0, 70), (0, 35), title="IMU angle", hlines=[(slip, (231, 111, 81, 255))])
    total = int(14 * FPS)
    slide = 0.0
    for f in range(total):
        t_s = f / FPS * 5.0                      # 5x speed: 0.5 deg/s -> 2.5 deg/s on screen
        ang = min(30.0, 0.5 * t_s) if t_s < 60 else 30.0
        R = rot_about(hinge_pt, hinge_dir, ang)
        for i in plate:
            sc.pose(i, R @ base[i])
        if ang >= slip:
            slide = min(70.0, slide + 2.5)
        for i in ring:
            M = base[i].copy(); M[1, 3] -= slide; sc.pose(i, R @ M)
        for i in pin:
            sc.pose(i, rot_about([0, 0, sz], [1, 0, 0], -2 * ang) @ base[i])
        ts.append(t_s); angs.append(ang + (0.35 * math.sin(40 * t_s) if slip <= ang < slip + 0.6 else 0.0))
        inset.series = [{"x": ts, "y": angs, "color": (42, 157, 143, 255), "style": "line"}]
        inset.note = f"slip at {slip:.1f}° -> mu_w = {math.tan(math.radians(slip)):.2f}" if ang >= slip else ""
        sc.camera((0, 50, 55), -60 + 25 * f / total, 22, 440)
        cap = caps[min(len(caps) - 1, 2 + int(3 * f / total))]
        _frame(w, sc, a, cap, inset, step=f"{ang:4.1f}°")
    sc.close()


# --------------------------------------------------------------------------------------------------
# 4. PSD from images (2D)
# --------------------------------------------------------------------------------------------------

def sop_psd(w: Writer):
    from PIL import Image, ImageDraw
    from engine import font
    a, sc = _scene("t04_psd")
    caps = _captions(4, ["Sprinkle 10-50 mg on a slide (sieve cup on the ERM)", "Backlit image at 1.55 µm/px",
                         "Threshold, split touching grains, drop edge grains", "Area-equivalent diameter, shape of each grain",
                         "10+ fields, 2000+ grains: d10, d50, d90", "Volume- and number-weighted PSD"])
    for f in range(int(3 * FPS)):
        sc.camera((0, 0, 60), -45 + 20 * f / (3 * FPS), 22, 420)
        _frame(w, sc, a, caps[0])
    sc.close()
    # synthetic field: lognormal grains (d50 = 120 um, sigma_g = 1.4) on a 1280 x 720 px field at 1.55 um/px
    d = np.exp(RNG.normal(math.log(120), math.log(1.4), 260))
    xy = RNG.random((260, 2)) * [1240, 600] + [20, 60]
    bins = np.linspace(20, 400, 26)
    found = []
    for f in range(int(9 * FPS)):
        u = f / (9 * FPS)
        im = Image.new("RGB", (1280, 720), (238, 240, 236))
        dr = ImageDraw.Draw(im)
        k = int(min(1.0, u * 1.6) * len(d))
        for j, (dd, (x, y)) in enumerate(zip(d, xy)):
            r = dd / 1.55 / 2 * 0.9
            ar = 1 + 0.35 * ((j * 37) % 10) / 10
            dr.ellipse([x - r * ar, y - r / ar, x + r * ar, y + r / ar], fill=(70, 62, 52))
            if j < k:
                dr.ellipse([x - r * ar - 2, y - r / ar - 2, x + r * ar + 2, y + r / ar + 2], outline=(42, 200, 170), width=2)
        found = d[:k]
        hist, _ = np.histogram(found, bins)
        ins = Inset((880, 330, 1260, 640), "ECD µm", "count", (20, 400), (0, max(8, int(hist.max() * 1.2) if len(found) else 8)),
                    title="Size distribution")
        cen = 0.5 * (bins[1:] + bins[:-1])
        ins.series = [{"x": list(cen), "y": list(hist), "color": (123, 94, 167, 255), "style": "dots"}]
        if len(found) > 30:
            ins.note = f"d10 {np.percentile(found, 10):.0f}  d50 {np.percentile(found, 50):.0f}  d90 {np.percentile(found, 90):.0f} µm"
        frame = np.asarray(im)
        cap = caps[min(len(caps) - 1, 1 + int(u * (len(caps) - 1)))]
        w.add(overlay(frame, title="4. PSD and shape from images (synthetic field)", caption=cap, tag="SOP", inset=ins))


# --------------------------------------------------------------------------------------------------
# 5. orifice cup
# --------------------------------------------------------------------------------------------------

def sop_orifice(w: Writer):
    a, sc = _scene("t05_orifice")
    caps = _captions(5, ["Gate shut; the doser fills the cup to 5 g", "Open the gate (servo, 10 mm)",
                         "The balance logs the outflow at 10 Hz", "Steady rate W from the linear part",
                         "Step down the discs until nothing flows in 60 s", "Repeat the smallest with taps: D_c, D_c,tapped"])
    gate = sc.group("gate")
    base = {i: a["comps"][i].M.copy() for i in gate}
    top = A.FLOOR + 120 + 6
    zc = top + 10
    cup_floor = zc + 11
    total = int(14 * FPS)
    ts, ms = [], []
    inset = Inset((880, 80, 1260, 330), "time s", "mass g", (0, 10), (0, 5.5), title="Balance (catch cup)")
    for f in range(total):
        u = f / total
        t_s = u * 10
        fill_level = min(1.0, u / 0.35)
        open_u = ease((u - 0.4) / 0.06)
        for i in gate:
            M = base[i].copy(); M[0, 3] += 10 * open_u; sc.pose(i, M)
        flow = 0.0
        if u > 0.45:
            flow = min(5.0, (u - 0.45) / 0.45 * 5.0)
        in_cup = cone_points(11.5, 3, cup_floor, int(1500 * fill_level * (1 - flow / 5.0)) + 10)
        in_cup[:, 2] = cup_floor + (in_cup[:, 2] - cup_floor) + 18 * fill_level * (1 - flow / 5.0) * RNG.random(len(in_cup))
        sc.particles("cup", in_cup, SAND, 5)
        if u < 0.35:
            sc.particles("fall", stream([0, 0, zc + 64], [0, 0, cup_floor + 18 * fill_level], 100, f / FPS, 1.5, 0.3), SAND, 4.5)
        elif u > 0.45 and flow < 5.0:
            sc.particles("fall", stream([0, 0, zc + 4], [0, 0, A.PAN_TOP + 2], 160, f / FPS, 1.8, 0.2), SAND, 4.5)
        else:
            sc.particles("fall", np.zeros((0, 3)), SAND, 4.5)
        sc.particles("catch", cone_points(18, 4 * flow / 5 + 0.2, A.PAN_TOP + 1.2, int(60 + 600 * flow / 5)), SAND, 5)
        ts.append(t_s); ms.append(flow)
        inset.series = [{"x": ts, "y": ms, "color": (42, 157, 143, 255), "style": "line"}]
        if u > 0.75:
            inset.note = "W = slope; Beverloo fit over discs"
        sc.camera((0, 0, zc - 20), -30 + 20 * u, 12, 330)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset)
    sc.close()


# --------------------------------------------------------------------------------------------------
# 6. humidity
# --------------------------------------------------------------------------------------------------

def sop_humidity(w: Writer):
    a, sc = _scene("t06_humidity")
    caps = _captions(6, ["Fingerprint the jar as received", "Spread 2-5 g in the dish; weigh",
                         "Close the box over the salt slurry", "Weigh at 0, 1, 2, 4, 8, 24 h",
                         "Fingerprint and heap AoR again", "Dry over silica gel; repeat: does it reverse?"])
    salts = [("MgCl2", 32.8, 0.4), ("Mg(NO3)2", 52.9, 0.9), ("NaCl", 75.3, 6.0), ("KCl", 84.3, 14.0)]
    total = int(12 * FPS)
    inset = Inset((860, 80, 1260, 360), "hours", "uptake mg/g", (0, 24), (0, 16), title="Water uptake (NaCl-like, illustration)")
    th = np.linspace(0, 24, 97)
    for f in range(total):
        u = f / total
        n = int(u * len(th)) + 1
        inset.series = [{"x": list(th[:n]), "y": list(up * (1 - np.exp(-th[:n] / 3.0))), "color": col, "style": "line"}
                        for (nm, rh, up), col in zip(salts, [(120, 170, 220, 255), (42, 157, 143, 255), (231, 111, 81, 255), (123, 94, 167, 255)])]
        inset.note = "MgCl2 33 %  Mg(NO3)2 53 %  NaCl 75 %  KCl 84 % RH"
        sc.camera((0, 0, 40), -40 + 40 * u, 28, 420)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset, step=f"{24 * u:4.1f} h")
    sc.close()


# --------------------------------------------------------------------------------------------------
# 7. rotating drum
# --------------------------------------------------------------------------------------------------

def drum_bed(theta_deg, n=2600, r=19.6, fill=0.40):
    """Points in a circular segment of a drum (x, z in the drum plane) with the free surface at theta."""
    pts = []
    th = math.radians(theta_deg)
    # free-surface offset d such that the segment area = fill * pi r^2
    lo, hi = -r, r
    for _ in range(40):
        dmid = 0.5 * (lo + hi)
        ang = 2 * math.acos(max(-1, min(1, dmid / r)))
        area = 0.5 * r * r * (ang - math.sin(ang))
        if area > fill * math.pi * r * r:
            lo = dmid
        else:
            hi = dmid
    dline = 0.5 * (lo + hi)
    while len(pts) < n:
        q = (RNG.random((n, 2)) * 2 - 1) * r
        ok = (q ** 2).sum(1) < (r - 0.5) ** 2
        # rotate into the surface frame: surface normal tilted by theta
        nrm = np.array([-math.sin(th), math.cos(th)])
        ok &= q @ nrm < -dline
        pts.extend(q[ok][: n - len(pts)])
    return np.array(pts)


def sop_drum(w: Writer):
    a, sc = _scene("t07_drum")
    caps = _captions(7, ["Fill 40 % (about 7.5 mL); window on", "Module horizontal (p horizontal)",
                         "Turn at 1, 2, 5, 10, 20 rpm, 90 s each", "Camera on the axis, 10 fps",
                         "Free-surface angle per frame", "Avalanche angles and scatter: cohesive index"])
    drum = sc.group("drum")
    base = {i: a["comps"][i].M.copy() for i in drum}
    ax_pt, ax_dir = np.array([0, 0, 38.25]), np.array([0, 1.0, 0])
    y_drum = 35.4 - P.DRUM_EXT - 3 - 7.5     # mid-depth of the drum, doser frame
    dem = _load_dem("drum_coh_5rpm") or _load_dem("drum_dry_5rpm")
    total = int(14 * FPS)
    ts, angs = [], []
    inset = Inset((880, 80, 1260, 330), "time s", "surface °", (0, 14), (20, 50), title="Dynamic angle (illustration)")
    ang_rot = 0.0
    for f in range(total):
        u = f / total
        rpm = 5.0
        ang_rot += 360 * rpm / 60 / FPS * 3       # shown at 3x
        R = rot_about(ax_pt, ax_dir, ang_rot)
        for i in drum:
            sc.pose(i, R @ base[i])
        theta = 36 + 4 * math.sin(2 * math.pi * f / (2.2 * FPS)) + 2 * (RNG.random() - 0.5)
        q = drum_bed(theta, 1800)
        depth = (RNG.random(len(q)) - 0.5) * 13
        pts = np.c_[q[:, 0], y_drum + depth, 38.25 + q[:, 1]]
        sc.particles("bed", pts, SAND, 4.5)
        ts.append(u * 14); angs.append(theta)
        inset.series = [{"x": ts, "y": angs, "color": (231, 111, 81, 255), "style": "line"}]
        sc.camera((0, y_drum, 38), -20 + 15 * u, 10, 190)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset, step=f"{rpm:.0f} rpm")
    sc.close()


# --------------------------------------------------------------------------------------------------
# 8. unconfined strength
# --------------------------------------------------------------------------------------------------

def sop_ucs(w: Writer):
    a, sc = _scene("t08_ucs")
    caps = _captions(8, ["Fill the closed mould with the doser", "Piston + weights: consolidate at 1 kPa, 60 s",
                         "Lift the weights; slide the rings off", "Open the mould: the column stands (or collapses)",
                         "Lower the platen at 0.1 mm/s; log the load cell", "sigma_c = peak force / area; repeat at 2-3 stresses"])
    gA, gB, rings, pis, plat = (sc.group(g) for g in ("mouldA", "mouldB", "rings", "piston", "platen"))
    base = {i: a["comps"][i].M.copy() for i in gA + gB + rings + pis + plat}
    zb = 8 + 20 + 6.4 + 4
    col_xy = np.array([-10.0, 0.0])
    total = int(16 * FPS)
    ds, Fs = [], []
    inset = Inset((880, 80, 1260, 330), "platen mm", "force mN", (0, 3), (0, 30), title="Load cell (illustration)")
    crushed = False
    for f in range(total):
        u = f / total
        lift_p = 60 * ease((u - 0.15) / 0.1)
        ring_up = 60 * ease((u - 0.25) / 0.1)
        open_m = 25 * ease((u - 0.37) / 0.1)
        for i in pis:
            M = base[i].copy(); M[2, 3] += lift_p - 2 * ease(u / 0.1); sc.pose(i, M)
        for i in rings:
            M = base[i].copy(); M[2, 3] += ring_up; sc.pose(i, M)
        for i in gA:
            M = base[i].copy(); M[1, 3] += open_m; sc.pose(i, M)
        for i in gB:
            M = base[i].copy(); M[1, 3] -= open_m; sc.pose(i, M)
        dz = 0.0
        if u > 0.5:
            dz = (u - 0.5) / 0.5 * 14
        for i in plat:
            M = base[i].copy(); M[2, 3] -= dz; sc.pose(i, M)
        disp = max(0.0, dz - 10.0)
        F = 0.0
        if disp > 0 and not crushed:
            F = 26 * (disp / 1.2) if disp < 1.2 else max(0.0, 26 - 40 * (disp - 1.2))
            crushed = disp > 1.2
        if u > 0.5:
            ds.append(disp); Fs.append(F)
        inset.series = [{"x": ds, "y": Fs, "color": (123, 94, 167, 255), "style": "line"}]
        if crushed:
            inset.note = "peak 26 mN -> sigma_c = 83 Pa"
        hcol = 40.0 if not crushed else max(10.0, 40 - 30 * (u - 0.84) / 0.16)
        col = cone_points(10, 1, zb, 1) if False else None
        rr = 9.9 * np.sqrt(RNG.random(2200)); th = RNG.random(2200) * 2 * math.pi
        zz = zb + RNG.random(2200) * hcol
        pts = np.c_[col_xy[0] + rr * np.cos(th), col_xy[1] + rr * np.sin(th), zz]
        if crushed:
            spread = (u - 0.84) / 0.16 * 9
            pts[:, :2] += (pts[:, :2] - col_xy) / 9.9 * spread * RNG.random((2200, 1))
        sc.particles("col", pts, SAND, 5)
        sc.camera((0, 10, 70), -50 + 25 * u, 18, 330)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset)
    sc.close()


# --------------------------------------------------------------------------------------------------
# 9. spreading
# --------------------------------------------------------------------------------------------------

def sop_spread(w: Writer):
    a, sc = _scene("t09_spread")
    caps = _captions(9, ["Weigh the coupon; set the gap with feeler gauges", "The doser lays a 0.3 g line",
                         "Blade sweeps at 50 mm/s", "Top-down photo with low-angle light",
                         "Weigh the coupon: areal mass, packing fraction", "Coverage and streak area from the image"])
    blade = sc.group("blade"); pw = sc.group("powder")
    base = {i: a["comps"][i].M.copy() for i in blade + pw}
    zc = 22.0 - 0.15 - 10.0 + 10.0
    total = int(12 * FPS)
    xs, cov = [], []
    inset = Inset((880, 80, 1260, 330), "blade x mm", "coverage %", (0, 130), (0, 100), title="Coverage behind the blade (illustration)")
    line0 = np.c_[84 + RNG.normal(0, 0.8, 1500), 88 + (RNG.random(1500) - 0.5) * 28, zc + RNG.random(1500) * 1.2]
    for f in range(total):
        u = f / total
        xb = 130 * ease((u - 0.15) / 0.7)
        for i in blade:
            M = base[i].copy(); M[0, 3] += xb; sc.pose(i, M)
        for i in pw:
            sc.show(i, False)
        bx = 60 + xb
        pile = line0.copy()
        pile[:, 0] = np.maximum(pile[:, 0], bx + 1.5 + RNG.random(len(pile)) * 3.0)
        keep = pile[:, 0] < 182
        pile = pile[keep]
        n_layer = int(max(0, bx - 84) * 30)
        lay = np.c_[84 + RNG.random(n_layer) * max(0.0, bx - 84), 88 + (RNG.random(n_layer) - 0.5) * 28, zc + RNG.random(n_layer) * 0.15]
        sc.particles("pile", pile, SAND, 5)
        sc.particles("layer", lay, SAND, 4.5)
        xs.append(xb); cov.append(min(92.0, 92 * min(1.0, xb / 20)) if xb > 0 else 0)
        inset.series = [{"x": xs, "y": cov, "color": (42, 157, 143, 255), "style": "line"}]
        sc.camera((120, 80, 20), -40 + 20 * u, 32, 300)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset)
    sc.close()


# --------------------------------------------------------------------------------------------------
# 10. Faraday cup
# --------------------------------------------------------------------------------------------------

def sop_faraday(w: Writer):
    a, sc = _scene("t10_faraday")
    caps = _captions(10, ["Reset the charge amplifier (reed relay, GP10)", "Dose N revolutions into the inner cup",
                          "Read Q 2 s after the last grain", "Lift the lead; weigh the inner cup",
                          "q/m = Q / m (C/kg), with its sign", "Repeat vs tilt, speed and RH"])
    top = A.FLOOR + 120 + 6
    zc = top + 4
    total = int(12 * FPS)
    ts, qs = [], []
    inset = Inset((880, 80, 1260, 330), "time s", "charge nC", (0, 12), (-12, 2), title="FC-1 output (illustration)")
    for f in range(total):
        u = f / total
        t_s = u * 12
        dosing = 0.15 < u < 0.7
        m = min(1.0, max(0.0, (u - 0.15) / 0.55))
        if dosing:
            sc.particles("fall", stream([0, 0, zc + 95], [0, 0, zc + 15 + 8 * m], 140, f / FPS, 1.6, 0.4), SAND, 4.5)
        else:
            sc.particles("fall", np.zeros((0, 3)), SAND, 4.5)
        sc.particles("cup", cone_points(18.5, 2 + 6 * m, zc + 15, int(40 + 1600 * m)), SAND, 5)
        q = -10 * m + (0.15 * math.sin(30 * t_s) if dosing else 0.0)
        ts.append(t_s); qs.append(q)
        inset.series = [{"x": ts, "y": qs, "color": (231, 111, 81, 255), "style": "line"}]
        if u > 0.75:
            inset.note = "-10 nC / 0.8 g = -1.2e-5 C/kg"
        sc.camera((0, 0, zc + 40), -30 + 20 * u, 16, 330)
        cap = caps[min(len(caps) - 1, int(u * len(caps)))]
        _frame(w, sc, a, cap, inset)
    sc.close()


SOPS = {"t01_heap": sop_heap, "t02_density": sop_density, "t03_tilt": sop_tilt, "t04_psd": sop_psd,
        "t05_orifice": sop_orifice, "t06_humidity": sop_humidity, "t07_drum": sop_drum, "t08_ucs": sop_ucs,
        "t09_spread": sop_spread, "t10_faraday": sop_faraday}

if __name__ == "__main__":
    import sys
    import time
    key, out = sys.argv[1], sys.argv[2]
    t0 = time.time()
    w = Writer(out)
    SOPS[key](w)
    w.close()
    print(key, w.n, "frames", round(time.time() - t0, 1), "s")
