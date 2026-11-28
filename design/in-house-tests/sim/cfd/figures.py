"""Figures for the humidity chamber and the Faraday cup (reads the JSON / NPZ results)."""
import json
import os

import numpy as np

import plotstyle as ps
import humidity_3d as h3
import humidity_fan2d as hf
import faraday_flow as ff

SET = h3.RH_SET


def ffile(prefix, case, ext):
    """faraday_flow_/faraday_track_ result file for a case: 0.75 mm grid if present, else 1 mm."""
    for tag in ("",):
        fn = f"{prefix}{case}{tag}.{ext}"
        if os.path.exists(fn):
            return fn, tag
    return None, None


def _load(fn):
    return json.load(open(fn)) if os.path.exists(fn) else None


def humidity_a():
    fig, ax = ps.plt.subplots(figsize=(6.4, 4.2))
    k = 0
    for fn, lab, ls in (("humidity_3d_h2.5mm.json", "3D, still air, 2.5 mm grid", "-"),
                        ("humidity_3d_h5.0mm.json", "3D, still air, 5 mm grid", "--")):
        r = _load(fn)
        if r:
            s = r["case_a"]["series"]
            ax.plot(np.array(s["t"]) / 60, 100 * np.array(s["sample"]), color=ps.CAT[0], ls=ls, lw=2, label=lab)
    r2 = _load("humidity_fan2d.json")
    if r2:
        items = [("still_2d", "2D section, still air", ps.CAT[1], "-"),
                 ("fan_below_nu3e-04_enh1", "2D, fan under the shelf", ps.CAT[2], "-"),
                 ("fan_below_nu3e-04_enh2", "2D, fan under the shelf, x2 wall transfer", ps.CAT[2], "--"),
                 ("fan_above_nu3e-04_enh1", "2D, fan over the dish", ps.CAT[3], "-")]
        for key, lab, c, ls in items:
            if key in r2:
                s = r2[key]["case_a"]["series"]
                ax.plot(np.array(s["t"]) / 60, 100 * np.array(s["sample"]), color=c, ls=ls, lw=2, label=lab)
    for f, txt in ((0.95, "95 % of set point"), (0.99, "99 %")):
        ax.axhline(100 * f * SET, color=ps.TEXT2, lw=0.8, ls=":")
        ax.text(19.5, 100 * f * SET - 1.4, txt, color=ps.TEXT2, fontsize=8, ha="right")
    ax.set_xlim(0, 20)
    ax.set_ylim(38, 78)
    ax.set_xlabel("time after the lid closes (min)")
    ax.set_ylabel("RH at the sample (%)")
    ax.set_title("Box closed on 40 % room air over NaCl slurry (75.3 %)", loc="left")
    ps.tidy(ax)
    ax.legend(fontsize=7.5, loc="lower right")
    fig.text(0.01, 0.005, "Computed, not measured.", color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("humidity_case_a.png", dpi=150)


def humidity_b():
    fig, axs = ps.plt.subplots(1, 2, figsize=(10.5, 4.2))
    r3 = None
    for fn in ("humidity_3d_h2.5mm.json", "humidity_3d_h5.0mm.json"):
        rr = _load(fn)
        if rr and "case_b" in rr:
            r3 = rr
            break
    r2 = _load("humidity_fan2d.json")
    if r3:
        s = r3["case_b"]["series"]
        t = np.array(s["t"]) / 3600
        axs[0].plot(t, 100 * np.array(s["sample_surface"]), color=ps.CAT[0], lw=2, label="still air (3D, 5 mm): sample surface")
        axs[0].plot(t, 100 * np.array(s["sensor"]), color=ps.CAT[0], lw=1.5, ls="--", label="still air (3D, 5 mm): sensor")
        axs[1].plot(t, s["uptake"], color=ps.CAT[0], lw=2, label="still air (3D, 5 mm)")
        axs[1].plot(np.array(s["ideal_t"]) / 3600, s["ideal_uptake"], color=ps.TEXT, lw=1.2, ls="-.",
                    label="surface held at the set point (powder-limited)")
    if r2:
        for key, lab, c, ls in (("fan_below_nu3e-04_enh1", "fan under the shelf (2D)", ps.CAT[2], "-"),
                                ("fan_below_nu3e-04_enh2", "fan, x2 wall transfer (2D)", ps.CAT[2], ":")):
            if key in r2:
                s = r2[key]["case_b"]["series"]
                t = np.array(s["t"]) / 3600
                if ls == "-":
                    axs[0].plot(t, 100 * np.array(s["sample_surface"]), color=c, lw=2, label=lab + ": sample surface")
                    axs[0].plot(t, 100 * np.array(s["sensor"]), color=c, lw=1.5, ls="--", label=lab + ": sensor")
                axs[1].plot(t, s["uptake"], color=c, lw=2, ls=ls, label=lab)
    axs[0].axhline(100 * 0.95 * SET, color=ps.TEXT2, lw=0.8, ls=":")
    axs[0].set_xlabel("time after the sample goes in (h)")
    axs[0].set_ylabel("RH (%)")
    axs[0].set_title("RH at the sample and at the SHT45", loc="left", fontsize=9)
    axs[1].set_xlabel("time after the sample goes in (h)")
    axs[1].set_ylabel("water taken up (mg per g)")
    axs[1].set_title("2 g rice-flour-like sample, 1 mm layer, 40 -> 75.3 % RH", loc="left", fontsize=9)
    for a in axs:
        ps.tidy(a)
        a.set_xlim(0, 6)
        a.legend(fontsize=7)
    fig.text(0.01, 0.005, "Computed, not measured. GAB isotherm constants are assumed (README).",
             color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("humidity_case_b.png", dpi=150)


def fan_flow():
    files = [("fanflow_below_nu3e-04.npz", "below", "Fan under the shelf, across the slurry"),
             ("fanflow_above_nu3e-04.npz", "above", "Fan over the dish")]
    files = [f for f in files if os.path.exists(f[0])]
    if not files:
        return
    fig, axs = ps.plt.subplots(len(files), 1, figsize=(7.5, 3.4 * len(files)))
    axs = np.atleast_1d(axs)
    for ax, (fn, fan, title) in zip(axs, files):
        d = np.load(fn)
        u, v, solid = d["u"], d["v"], d["solid"]
        uc = 0.5 * (u[:-1] + u[1:])
        vc = 0.5 * (v[:, :-1] + v[:, 1:])
        spd = np.hypot(uc, vc)
        spd = np.ma.masked_where(solid, spd)
        x = (np.arange(hf.NX) + 0.5) * hf.H * 1e3
        z = (np.arange(hf.NZ) + 0.5) * hf.H * 1e3
        im = ax.pcolormesh(x, z, spd.T, cmap="Blues", vmin=0, vmax=0.4, shading="auto")
        ax.streamplot(x, z, uc.T, vc.T, color="#191919", linewidth=0.5, density=1.3, arrowsize=0.6)
        ax.contourf(x, z, solid.T.astype(float), levels=[0.5, 1.5], colors=["#9a9a9a"])
        ax.contourf(x, z, d["shelf"].T.astype(float), levels=[0.5, 1.5], colors=["#c8c8c8"])
        ax.set_aspect("equal")
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        ax.plot([140], [60], "o", ms=6, mfc="white", mec=ps.TEXT, label="SHT45")
        fig.colorbar(im, ax=ax, label="speed (m/s)", shrink=0.8)
    axs[0].legend(fontsize=7, loc="upper right")
    fig.text(0.01, 0.005, "Computed (2D section, eddy viscosity 3e-4 m²/s), not measured.", color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig("humidity_fan_flow.png", dpi=150)


def faraday_flow_fig():
    cases = [c for c in ("fine1", "salt1") if ffile("faraday_flow_", c, "npz")[0]]
    if not cases:
        return
    fig, axs = ps.plt.subplots(1, len(cases), figsize=(4.8 * len(cases), 6))
    axs = np.atleast_1d(axs)
    for ax, c in zip(axs, cases):
        d = np.load(ffile("faraday_flow_", c, "npz")[0])
        u, v, lab, h = d["u"], d["v"], d["lab"], float(d["h"])
        uc = 0.5 * (u[:-1] + u[1:])
        vc = 0.5 * (v[:, :-1] + v[:, 1:])
        nr, nz = lab.shape
        r = (np.arange(nr) + 0.5) * h * 1e3
        z = (np.arange(nz) + 0.5) * h * 1e3
        spd = np.ma.masked_where(lab > 0, np.hypot(uc, vc))
        im = ax.pcolormesh(r, z, spd.T, cmap="Blues", norm=ps.matplotlib.colors.LogNorm(1e-3, 1.0), shading="auto")
        uu = np.where(lab > 0, np.nan, uc)
        vv = np.where(lab > 0, np.nan, vc)
        ax.streamplot(r, z, uu.T, vv.T, color="#191919", linewidth=0.5, density=1.6, arrowsize=0.6)
        ax.contourf(r, z, (lab == 1).T.astype(float), levels=[0.5, 1.5], colors=[ps.CAT[3]])
        ax.contourf(r, z, (lab == 2).T.astype(float), levels=[0.5, 1.5], colors=["#9a9a9a"])
        ax.set_aspect("equal")
        ax.set_xlim(0, 45)
        ax.set_xlabel("r (mm)")
        ax.set_ylabel("z (mm)")
        meta = json.load(open(ffile("faraday_flow_", c, "json")[0]))
        ax.set_title(f"{ff.CASES[c]['label']}\nair in through the Ø20 inlet {meta['Q_inlet_down_mLs']:.1f} mL/s",
                     loc="left", fontsize=8.5)
        fig.colorbar(im, ax=ax, label="air speed (m/s)", shrink=0.7)
    fig.text(0.01, 0.005, "Computed (axisymmetric, laminar), not measured. Yellow: inner cup; grey: can and lid.",
             color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig("faraday_flow.png", dpi=150)


def faraday_capture_fig():
    cases = [c for c in ("fine1", "fine01", "salt1") if ffile("faraday_track_", c, "json")[0]]
    if not cases:
        return
    fig, axs = ps.plt.subplots(1, 3, figsize=(13.5, 4.3))
    r = json.load(open(ffile("faraday_track_", cases[0], "json")[0]))
    sizes = r["sizes_um"]
    for k, (inj, lab) in enumerate((("stream", "released inside the stream"), ("edge", "shed at the stream edge"),
                                    ("splash", "splashed off the heap"))):
        key = f"rho2165_{inj}"
        if key not in r["results"]:
            continue
        y = [r["results"][key][f"{s:.0f}"]["captured"] for s in sizes]
        axs[0].plot(sizes, y, color=ps.CAT[k], lw=5 if k == 0 else 2, alpha=0.6 if k == 0 else 1.0,
                    marker="o", ms=5, label=lab)
    axs[0].set_xscale("log")
    axs[0].set_xlabel("grain size (um), 2165 kg/m³")
    axs[0].set_ylabel("fraction kept by the inner cup")
    axs[0].set_title(ff.CASES[cases[0]]["label"], loc="left", fontsize=9)
    mk = {"fine1": "o", "fine01": "s", "salt1": "^"}
    for c in cases:
        rr = json.load(open(ffile("faraday_track_", c, "json")[0]))
        for k, rho in enumerate(("1450", "2165", "3100")):
            for ax, inj, xkey in ((axs[1], "edge", "stokes_jet"), (axs[2], "splash", "settling_mm_s")):
                key = f"rho{rho}_{inj}"
                if key not in rr["results"]:
                    continue
                res = rr["results"][key]
                x = [res[f"{s:.0f}"][xkey] for s in rr["sizes_um"]]
                y = [res[f"{s:.0f}"]["captured"] for s in rr["sizes_um"]]
                ax.plot(x, y, ls="none", marker=mk[c], ms=6, mfc="none", mec=ps.CAT[k], mew=1.5,
                        label=f"{c}, {rho} kg/m³")
    axs[1].set_xscale("log")
    axs[1].set_xlabel("Stokes number tau_p v_inlet / b (b = 1.5 mm)")
    axs[1].set_ylabel("fraction kept (shed at the stream edge)")
    axs[1].set_title("Dust at the stream edge", loc="left", fontsize=9)
    axs[2].set_xscale("log")
    axs[2].set_xlabel("settling speed in still air (mm/s)")
    axs[2].set_ylabel("fraction kept (splash from the heap)")
    axs[2].set_title("Grains splashed off the heap", loc="left", fontsize=9)
    for a in axs:
        ps.tidy(a)
        a.set_ylim(-0.02, 1.04)
    axs[0].legend(fontsize=7.5, loc="lower right")
    axs[2].legend(fontsize=6, ncol=1, loc="lower right")
    fig.text(0.01, 0.005, "Computed, not measured. One-way tracking in the computed air flow; 120 grains per point "
             "(about ±3 % at 0.9). fine1 / fine01: Si-325-like stream at 1 / 0.1 g/s; salt1: salt-like stream at 1 g/s.",
             color=ps.TEXT2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig("faraday_capture.png", dpi=150)


def diffusion_fig():
    """Re-plot the diffusion validation from its JSON with sparse markers."""
    import validate_diffusion as vd
    r = _load("diffusion_validation.json")
    if not r:
        return
    fig, ax = ps.plt.subplots(figsize=(5.6, 3.9))
    tf = np.linspace(0.5, 900, 400)
    ax.plot(tf, vd.exact(vd.H, tf), color=ps.TEXT, lw=1.4, ls="--", label="exact, closed end (z = H)")
    ax.plot(tf, vd.exact(vd.H / 2, tf), color=ps.TEXT2, lw=1.4, ls=":", label="exact, mid-height")
    for k, run in enumerate(r["runs"][:3]):
        t = np.array(run["t"])
        idx = [int(np.argmin(np.abs(t - x))) for x in np.arange(20 + 10 * k, 900, 60)]
        ax.plot(t[idx], np.array(run["top"])[idx], "o", ms=6, color=ps.CAT[k], mfc="none", mew=1.5,
                label=f"solver, {run['h_mm']:.1f} mm cells, dt {run['dt_s']:.0f} s")
        ax.plot(t[idx], np.array(run["mid"])[idx], "s", ms=6, color=ps.CAT[k], mfc="none", mew=1.5)
    ax.set_xlabel("time after the step (s)")
    ax.set_ylabel("fraction of the step")
    ax.set_title("Diffusion check: 80 mm slab, D = 2.5e-5 m²/s", loc="left")
    ps.tidy(ax)
    ax.legend(fontsize=7.5, loc="lower right")
    fig.text(0.01, 0.005, "Circles: closed end; squares: mid-height. Computed.", color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("diffusion_validation.png", dpi=150)


if __name__ == "__main__":
    for f in (diffusion_fig, humidity_a, humidity_b, fan_flow, faraday_flow_fig, faraday_capture_fig):
        try:
            f()
            print("ok", f.__name__)
        except Exception as e:  # keep going; report
            print("FAILED", f.__name__, repr(e))
