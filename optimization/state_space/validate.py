#!/usr/bin/env python3
"""Validate the state-space model against the recorded salt doses (PR #131).

Replays the *measured* actuator commands (auger rpm, plate tilt, taps) from the
10 Hz PID telemetry through ``state_space.PowderDoserModel`` and compares the
simulated balance trace with the recorded one.

Two questions are answered:

1. Does the model structure reproduce a real dose?  (Yes, once the scalar
   feed-factor state ``phi`` is fitted — a one-parameter fit per run.)
2. What does the model get wrong with nominal parameters?  (Session-to-session
   feed-factor drift of ~1.5x at the same tilt: the reason ``phi`` has to be a
   state estimated online, not a calibration constant.)

Usage::

    python optimization/state_space/validate.py --data-root /tmp/pr131/data
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from state_space import (IDX, IDX_U, PowderDoserModel, Params, feed_factor,
                         initial_state)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]


def read_telemetry(path: Path) -> dict:
    import csv
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    return {
        "t": np.array([int(r["t_ms"]) / 1000.0 for r in rows]),
        "m": np.array([float(r["mass_g"]) for r in rows]),
        "tilt": np.array([float(r["tilt_deg"]) for r in rows]),
        "rpm": np.array([float(r["auger_rpm_cmd"]) for r in rows]),
        "taps": np.array([int(r["taps_cum"]) for r in rows]),
        "phase": np.array([r["phase"] for r in rows]),
    }


def simulate(tel: dict, phi: float, params: Params, dt: float = 0.01) -> np.ndarray:
    """Replay the recorded inputs; return the simulated balance trace on the
    telemetry timebase."""
    model = PowderDoserModel(params)
    x = initial_state(53.3, alpha_deg=float(tel["tilt"][0]), params=params)
    x[IDX["phi"]] = phi
    out = np.zeros_like(tel["t"])
    taps_done = int(tel["taps"][0])
    t = float(tel["t"][0])
    for i, ti in enumerate(tel["t"]):
        u = np.array([tel["rpm"][i], tel["tilt"][i], 0.0])
        while t < ti - 1e-9:
            h = min(dt, ti - t)
            x = model.step(x, u, h, substeps=2)
            t += h
        n_new = int(tel["taps"][i]) - taps_done
        if n_new > 0:
            x, _ = model.tap(x, n_new)
            taps_done += n_new
        out[i] = x[IDX["y_bal"]]
    return out


def fit_phi(tel: dict, params: Params, window: np.ndarray) -> tuple[float, float]:
    def cost(phi: float) -> float:
        sim = simulate(tel, phi, params)
        return float(np.sqrt(np.mean((sim[window] - tel["m"][window]) ** 2)))

    res = minimize_scalar(cost, bounds=(0.2, 5.0), method="bounded",
                          options={"xatol": 1e-3})
    return float(res.x), float(res.fun)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", type=Path, default=REPO_ROOT / "data")
    ap.add_argument("--params", type=Path, default=HERE / "salt_params.json")
    ap.add_argument("--fill", default="full", choices=("full", "half"))
    ap.add_argument("--figdir", type=Path, default=HERE / "figures")
    ap.add_argument("--out", type=Path, default=HERE / "validation.json")
    args = ap.parse_args()

    params = Params.from_json(args.params, fill=args.fill)
    tel_dir = args.data_root / "pid-dose/2026-07-29_salt"
    report = {"params": params.provenance, "runs": {}}

    traces = {}
    for run in ("run2", "run1"):
        tel = read_telemetry(tel_dir / f"telemetry_{run}_salt.csv")
        keep = tel["phase"] != "preroll"
        tel = {k: v[keep] for k, v in tel.items()}
        tel["t"] = tel["t"] - tel["t"][0]

        # run 1 bridged (starved) at ~12 s in; only its flowing stretch is a
        # fair test of the flowing-mode dynamics.
        dosing = np.flatnonzero(tel["rpm"] > 0)
        if run == "run1":
            # keep the first 90 s: the run then sat in 40 stall rounds for 420 s
            keep = tel["t"] <= 90.0
            tel = {k: v[keep] for k, v in tel.items()}
            # bridge = the first time the balance gains < 5 mg over a 5 s window
            # while the auger is still commanded to turn
            t_bridge = float(tel["t"][-1])
            for i, ti in enumerate(tel["t"]):
                if ti < 5.0 or tel["rpm"][i] <= 0:
                    continue
                j = int(np.searchsorted(tel["t"], ti + 5.0))
                if j >= len(tel["t"]):
                    break
                if tel["m"][j] - tel["m"][i] < 5e-3 and np.all(tel["rpm"][i:j] > 0):
                    t_bridge = float(ti)
                    break
            window = np.flatnonzero(tel["t"] <= t_bridge)
        else:
            t_bridge = None
            window = np.arange(len(tel["t"]))

        sim_nom = simulate(tel, 1.0, params)
        phi, rms = fit_phi(tel, params, window)
        sim_fit = simulate(tel, phi, params)
        traces[run] = (tel, sim_nom, sim_fit, window)

        final_meas = float(tel["m"][window][-1])
        entry = {
            "phi_fitted": phi,
            "rms_error_fitted_mg": rms * 1e3,
            "rms_error_nominal_mg": float(np.sqrt(np.mean(
                (sim_nom[window] - tel["m"][window]) ** 2)) * 1e3),
            "final_measured_g": final_meas,
            "final_simulated_g": float(sim_fit[window][-1]),
            "implied_ff_at_25deg_mg_per_rev":
                phi * feed_factor(25.0, 53.3, params) * 1e3,
            "nominal_ff_at_25deg_mg_per_rev": feed_factor(25.0, 53.3, params) * 1e3,
            "n_frames": int(window.size),
        }
        if run == "run1":
            entry["bridged_at_s"] = t_bridge
            entry["note"] = ("mass flat from here while the auger kept turning "
                             "and 80 taps fired: a discrete mode change "
                             "(starved/bridged), not a gain error")
            after = np.flatnonzero(tel["t"] > t_bridge + 30.0)
            if after.size:
                entry["flowing_mode_error_30s_after_bridge_mg"] = float(
                    (sim_fit[after[0]] - tel["m"][after[0]]) * 1e3)
        # post-halt in-flight check (run 2 only: run 1 never reached the target)
        if run == "run2":
            halt = int(np.flatnonzero(tel["rpm"] > 0)[-1])
            entry["post_halt_landed_measured_mg"] = float(
                (tel["m"][-1] - tel["m"][halt]) * 1e3)
            entry["post_halt_landed_simulated_mg"] = float(
                (sim_fit[-1] - sim_fit[halt]) * 1e3)
        _ = dosing
        report["runs"][run] = entry

    # --- figure ------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.figdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for ax, run, title in zip(axes, ("run2", "run1"),
                              ("Run 2 — clean dose (flowing mode)",
                               "Run 1 — hopper bridged mid-dose")):
        tel, sim_nom, sim_fit, window = traces[run]
        e = report["runs"][run]
        ax.plot(tel["t"], tel["m"] * 1e3, "k-", lw=1.6, label="balance (measured)")
        ax.plot(tel["t"], sim_nom * 1e3, color="#d62728", ls="--", lw=1.2,
                label=f"model, φ=1 (RMS {e['rms_error_nominal_mg']:.0f} mg)")
        ax.plot(tel["t"], sim_fit * 1e3, color="#2ca02c", lw=1.4,
                label=f"model, φ={e['phi_fitted']:.2f} (RMS {e['rms_error_fitted_mg']:.1f} mg)")
        if run == "run1":
            ax.axvline(e["bridged_at_s"], color="#888", ls=":", lw=1.5)
            ax.annotate("bridge / starvation\n(mode change)",
                        xy=(e["bridged_at_s"], 300), fontsize=8,
                        xytext=(e["bridged_at_s"] + 2, 200), color="#555")
            ax.set_xlim(0, min(60, tel["t"][-1]))
        ax.set_xlabel("time since dose start [s]")
        ax.set_ylabel("mass [mg]")
        ax.set_title(title)
        ax.legend(fontsize=7, loc="lower right")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    p = args.figdir / "fig3-model-vs-measured.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)

    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
