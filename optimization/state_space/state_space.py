#!/usr/bin/env python3
"""State-space representation of the powder-doser flow (issue #140).

This is the executable form of ``docs/state-space-model.md``: the same state
vector, inputs, dynamics and salt parameter set, in code, so that the model can
be simulated, linearized, discretized and handed to an LQG / MPC design.

Layout
------
``PowderDoserModel`` holds the parameters and implements

* ``f(x, u)``      -- the continuous-time vector field of the flowing mode
* ``tap(x)``       -- the discrete tap event (an impulsive reset map)
* ``step(x, u, dt)``-- RK4 integration of the continuous part
* ``measure(x)``   -- the balance output (lag + bias + quantization)
* ``linearize()``  -- A, B, C, D about an operating point (finite differences)
* ``discretize()`` -- zero-order-hold discrete-time (Ad, Bd) via ``expm``
* ``observability_report()`` -- what the balance alone can and cannot see

The default parameters are for **salt**, fitted by ``fit_salt_parameters.py``
from the datasets in PR #131.  They are *not* transferable to another powder:
every gain here is a powder property (see the caveats section of the doc).

Units: grams, seconds, plate degrees (0 = tube horizontal, 90 = plate limit),
auger rpm, auger revolutions for the phase state.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SALT_PARAMS_JSON = HERE / "salt_params.json"

# --- state vector layout ---------------------------------------------------
# Indices into the continuous state array.  The discrete mode `q` and the
# integer tap input are handled outside the array (they are not differentiable).
IDX = {
    "m_cup": 0,    # g   delivered mass actually in the cup
    "m_air": 1,    # g   in-flight / not-yet-landed inventory
    "x_lip": 2,    # g   tap-accessible inventory sitting at the tube lip
    "m_scr1": 3,   # g   screw hold-up, cell 1 (hopper end)
    "m_scr2": 4,   # g   screw hold-up, cell 2
    "m_scr3": 5,   # g   screw hold-up, cell 3 (lip end)
    "m_hop": 6,    # g   powder remaining in the tube/hopper
    "theta": 7,    # rev auger phase, mod 1 (cyclostationary pulsation)
    "omega": 8,    # rpm auger speed (actuator state)
    "alpha": 9,    # deg plate tilt (actuator state)
    "phi": 10,     # -   feed-factor scale (slow random walk / adapted online)
    "kappa": 11,   # -   lip consolidation, 0 loose ... 1 fully consolidated
    "y_bal": 12,   # g   balance indication (its own first-order lag)
    "b_bal": 13,   # g   balance bias / drift
}
N_STATES = len(IDX)
STATE_NAMES = [k for k, _ in sorted(IDX.items(), key=lambda kv: kv[1])]

# Inputs.  u = [omega_cmd (rpm), alpha_cmd (plate deg), tap rate (taps/s)].
# The tap input is genuinely impulsive/integer; `tap()` applies it exactly, and
# the continuous "taps/s" entry exists only so that a linearized design can
# treat a tap train as a rate input (see the doc, section "hybrid inputs").
IDX_U = {"omega_cmd": 0, "alpha_cmd": 1, "tap_rate": 2}
N_INPUTS = len(IDX_U)
INPUT_NAMES = [k for k, _ in sorted(IDX_U.items(), key=lambda kv: kv[1])]

MODES = ("flowing", "starved", "bridged")


@dataclass
class Params:
    """Model parameters.  Defaults are the salt fits (see `from_json`)."""

    # --- auger feed factor ff(alpha) = ff0 + gain*(a/a_peak)*exp(1-a/a_peak) --
    ff0_g_per_rev: float = 0.0480
    ff_gain_g_per_rev: float = 0.0844
    ff_a_peak_deg: float = 44.6
    # hopper draw-down gain, normalized to 1 at the fill the fit was taken at.
    # NOT identified: the two salt sessions confound fill with re-packing.
    fill_h50_g: float = 0.0
    # --- screw transport hold-up --------------------------------------------
    n_transport_rev: float = 1.0     # mean hopper -> lip transport, auger revs
    # --- per-revolution pulsation, P(theta) = 1 + a1 cos + b1 sin + ... ------
    pulse_a1: float = 0.755
    pulse_b1: float = -0.234
    pulse_a2: float = 0.055
    pulse_b2: float = -0.036
    # --- lip -----------------------------------------------------------------
    lip_cap0_g: float = 0.0043       # x_cap(0 deg) at the reference consolidation
    lip_cap_a_scale_deg: float = 24.0  # x_cap(a) = cap0 * exp(a / a_scale)
    tau_spill_s: float = 0.10        # lip -> free fall once over capacity
    # --- tap -----------------------------------------------------------------
    tap_release: float = 0.60        # fraction of x_lip freed by one tap (1-r)
    tap_floor0_g: float = 2.3e-4     # non-depleting floor at 0 deg
    tap_floor_a_scale_deg: float = 18.4  # floor(a) = floor0 * exp(a / a_scale)
    # --- transport / sensor time constants ------------------------------------
    tau_flight_s: float = 0.28       # lip -> balance pan (in-flight emptying)
    tau_balance_s: float = 0.14      # balance indication lag
    tau_omega_s: float = 0.05        # stepper speed slew
    tilt_rate_deg_per_s: float = 90.0  # servo plate rate limit
    balance_quantum_g: float = 1e-4
    balance_sigma_g: float = 6.6e-5  # from no-actuation control intervals
    balance_stable_band_g: float = 2e-4
    # --- process noise (1-sigma, for the Kalman/UKF design) -------------------
    sigma_phi_per_s: float = 0.02    # feed-factor random walk
    sigma_flow_rel: float = 0.05     # rev-to-rev multiplicative flow noise
    # --- limits --------------------------------------------------------------
    omega_max_rpm: float = 109.0
    alpha_max_deg: float = 90.0

    powder_id: str = "salt"
    provenance: str = "fit_salt_parameters.py on PR #131 data"

    # -- constructors ------------------------------------------------------
    @classmethod
    def from_json(cls, path: Path | str = SALT_PARAMS_JSON,
                  fill: str = "full") -> "Params":
        """Build parameters from the identification output.

        ``fill='full'`` uses the freshly-refilled-tube session (2026-07-31 PM,
        53.3 g weighed); ``fill='half'`` uses the drawn-down session, which is
        the one where taps still saw a depletable lip shelf.
        """
        d = json.loads(Path(path).read_text())
        ff = d["feed_factor"][fill]["fit"]
        tap = d["tap"][fill]
        pul = d["pulsation"]["harmonics"]
        infl = d["in_flight"]

        # lip capacity: the identified M_lip = A/(1-r) per tilt, where the
        # depletion term is actually resolvable (A above the fit residual).
        tilts, caps = [], []
        for a, e in tap["per_tilt"].items():
            f = e["fit"]
            if f.get("A_g", 0) > 2 * f.get("rms_resid_g", 1) and f.get("r", 1) < 0.95:
                tilts.append(float(a))
                caps.append(f["M_lip_g"])
        if len(tilts) >= 2:
            b, a0 = np.polyfit(np.asarray(tilts), np.log(np.asarray(caps)), 1)
            cap0, cap_scale = float(np.exp(a0)), float(1.0 / b)
        else:  # fall back on the class defaults
            cap0, cap_scale = cls.lip_cap0_g, cls.lip_cap_a_scale_deg

        r_vals = [e["fit"]["r"] for e in tap["per_tilt"].values()
                  if e["fit"].get("A_g", 0) > 2 * e["fit"].get("rms_resid_g", 1)
                  and e["fit"].get("r", 1) < 0.95]
        floor = tap["tilt_scaling"].get("y_inf", {})

        return cls(
            ff0_g_per_rev=ff["ff0_g_per_rev"],
            ff_gain_g_per_rev=ff["gain_g_per_rev"],
            ff_a_peak_deg=ff["a_peak_deg"],
            pulse_a1=pul["a1"], pulse_b1=pul["b1"],
            pulse_a2=pul["a2"], pulse_b2=pul["b2"],
            lip_cap0_g=cap0, lip_cap_a_scale_deg=cap_scale,
            tap_release=1.0 - float(np.median(r_vals)) if r_vals else cls.tap_release,
            tap_floor0_g=floor.get("k0_g", cls.tap_floor0_g),
            tap_floor_a_scale_deg=floor.get("a_scale_deg", cls.tap_floor_a_scale_deg),
            tau_flight_s=infl["first_order_fit"]["tau_s"],
            tau_balance_s=infl["dual_lag_fit"]["tau_balance_s"],
            balance_sigma_g=d["balance"]["no_actuation_interval_g"]["sd"],
            powder_id=d["powder_id"],
            provenance=f"{Path(path).name} ({fill} tube)",
        )


def initial_state(m_hop_g: float = 53.3, alpha_deg: float = 0.0,
                  primed: bool = True, params: Params | None = None) -> np.ndarray:
    """A plausible start-of-dose state (empty cup, tube loaded, lip at rest)."""
    p = params or Params()
    x = np.zeros(N_STATES)
    x[IDX["m_hop"]] = m_hop_g
    x[IDX["alpha"]] = alpha_deg
    x[IDX["phi"]] = 1.0
    x[IDX["kappa"]] = 0.0
    if primed:
        prime = p.ff0_g_per_rev * p.n_transport_rev / 3.0
        x[IDX["m_scr1"]] = x[IDX["m_scr2"]] = x[IDX["m_scr3"]] = prime
        x[IDX["x_lip"]] = lip_capacity(alpha_deg, 0.0, p)
    return x


# ---------------------------------------------------------------------------
# constitutive relations (the "gain schedules" of the model)
# ---------------------------------------------------------------------------

def feed_factor(alpha_deg: float, m_hop_g: float, p: Params) -> float:
    """Mass conveyed per auger revolution, g/rev, at tilt `alpha_deg`."""
    a = max(alpha_deg, 0.0)
    ff = p.ff0_g_per_rev + p.ff_gain_g_per_rev * (a / p.ff_a_peak_deg) * math.exp(
        1.0 - a / p.ff_a_peak_deg)
    if p.fill_h50_g > 0:  # optional draw-down term (not identified for salt)
        ff *= m_hop_g / (m_hop_g + p.fill_h50_g)
    return ff


def pulsation(theta_rev: float, p: Params) -> float:
    """Normalized flow modulation over one auger revolution (mean 1)."""
    w = 2.0 * math.pi * theta_rev
    return max(0.0, 1.0 + p.pulse_a1 * math.cos(w) + p.pulse_b1 * math.sin(w)
               + p.pulse_a2 * math.cos(2 * w) + p.pulse_b2 * math.sin(2 * w))


def lip_capacity(alpha_deg: float, kappa: float, p: Params) -> float:
    """How much tap-accessible powder the lip can hold, g.

    Grows with tilt (a steeper lip holds a bigger loose shelf) and collapses as
    the material consolidates -- the mechanism behind the 10-20x drop in tap
    yield measured on the freshly refilled tube.
    """
    return ((1.0 - kappa) * p.lip_cap0_g
            * math.exp(max(alpha_deg, 0.0) / p.lip_cap_a_scale_deg))


def tap_floor(alpha_deg: float, p: Params) -> float:
    """Non-depleting per-tap yield, g: the trickle a tap shakes off the column
    behind the lip, independent of the shelf inventory."""
    return p.tap_floor0_g * math.exp(max(alpha_deg, 0.0) / p.tap_floor_a_scale_deg)


# ---------------------------------------------------------------------------

class PowderDoserModel:
    """Continuous-time model plus the discrete tap map."""

    def __init__(self, params: Params | None = None, mode: str = "flowing"):
        self.p = params or Params()
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        self.mode = mode

    # -- flows -------------------------------------------------------------
    def conveying_rate(self, x: np.ndarray) -> float:
        """Mass rate the screw lifts out of the hopper, g/s."""
        p = self.p
        if self.mode == "bridged" or x[IDX["m_hop"]] <= 0.0:
            return 0.0
        gain = 0.0 if self.mode == "starved" else 1.0
        ff = feed_factor(x[IDX["alpha"]], x[IDX["m_hop"]], p)
        rev_per_s = x[IDX["omega"]] / 60.0
        return gain * x[IDX["phi"]] * ff * rev_per_s * pulsation(x[IDX["theta"]], p)

    def spill_rate(self, x: np.ndarray) -> float:
        """Rate at which the lip sheds mass into free fall, g/s."""
        cap = lip_capacity(x[IDX["alpha"]], x[IDX["kappa"]], self.p)
        return max(0.0, x[IDX["x_lip"]] - cap) / self.p.tau_spill_s

    # -- continuous dynamics -------------------------------------------------
    def f(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """dx/dt for the continuous states (taps are applied by `tap`)."""
        p = self.p
        dx = np.zeros_like(x)
        q_conv = self.conveying_rate(x)

        # screw hold-up: a 3-cell chain in the revolution domain, so powder
        # stops moving the instant the screw stops (transport lag, not dead time)
        k_cell = 3.0 / p.n_transport_rev * (x[IDX["omega"]] / 60.0)  # 1/s
        s1, s2, s3 = x[IDX["m_scr1"]], x[IDX["m_scr2"]], x[IDX["m_scr3"]]
        dx[IDX["m_scr1"]] = q_conv - k_cell * s1
        dx[IDX["m_scr2"]] = k_cell * (s1 - s2)
        dx[IDX["m_scr3"]] = k_cell * (s2 - s3)
        q_lip_in = k_cell * s3

        q_spill = self.spill_rate(x)
        dx[IDX["m_hop"]] = -q_conv
        dx[IDX["x_lip"]] = q_lip_in - q_spill

        # free fall -> cup, and the balance's own first-order indication lag
        dx[IDX["m_air"]] = q_spill - x[IDX["m_air"]] / p.tau_flight_s
        dx[IDX["m_cup"]] = x[IDX["m_air"]] / p.tau_flight_s
        dx[IDX["y_bal"]] = (x[IDX["m_cup"]] + x[IDX["b_bal"]]
                            - x[IDX["y_bal"]]) / p.tau_balance_s

        # actuator states
        dx[IDX["theta"]] = x[IDX["omega"]] / 60.0
        dx[IDX["omega"]] = (np.clip(u[IDX_U["omega_cmd"]], 0.0, p.omega_max_rpm)
                            - x[IDX["omega"]]) / p.tau_omega_s
        err = np.clip(u[IDX_U["alpha_cmd"]], 0.0, p.alpha_max_deg) - x[IDX["alpha"]]
        dx[IDX["alpha"]] = np.clip(err / 0.05, -p.tilt_rate_deg_per_s,
                                   p.tilt_rate_deg_per_s)

        # tap treated as a rate input (linearized-design convenience): the
        # exact impulsive version is `tap()`
        rate = max(0.0, float(u[IDX_U["tap_rate"]]))
        if rate > 0.0:
            per_tap = (p.tap_release * x[IDX["x_lip"]]
                       + tap_floor(x[IDX["alpha"]], p))
            dx[IDX["x_lip"]] -= p.tap_release * x[IDX["x_lip"]] * rate
            dx[IDX["m_air"]] += per_tap * rate

        # slow / parameter states: random walks with zero drift
        dx[IDX["phi"]] = 0.0
        dx[IDX["kappa"]] = 0.0
        dx[IDX["b_bal"]] = 0.0
        return dx

    # -- discrete tap event --------------------------------------------------
    def tap(self, x: np.ndarray, n: int = 1) -> tuple[np.ndarray, float]:
        """Apply `n` single taps as an impulsive reset map.

        Each tap frees ``tap_release`` of the tap-accessible lip inventory plus
        a non-depleting floor term; the released mass enters the in-flight
        state, so it reaches the balance with the same lag as auger flow.
        """
        x = x.copy()
        released = 0.0
        for _ in range(int(n)):
            dm = (self.p.tap_release * x[IDX["x_lip"]]
                  + tap_floor(x[IDX["alpha"]], self.p))
            dm = min(dm, x[IDX["x_lip"]] + tap_floor(x[IDX["alpha"]], self.p))
            x[IDX["x_lip"]] = max(0.0, x[IDX["x_lip"]] - self.p.tap_release
                                  * x[IDX["x_lip"]])
            x[IDX["m_air"]] += dm
            released += dm
        return x, released

    # -- integration ---------------------------------------------------------
    def step(self, x: np.ndarray, u: np.ndarray, dt: float,
             substeps: int = 4) -> np.ndarray:
        """RK4 the continuous part over `dt` (taps applied separately)."""
        h = dt / substeps
        for _ in range(substeps):
            k1 = self.f(x, u)
            k2 = self.f(x + 0.5 * h * k1, u)
            k3 = self.f(x + 0.5 * h * k2, u)
            k4 = self.f(x + h * k3, u)
            x = x + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            x[IDX["theta"]] %= 1.0
            for key in ("m_cup", "m_air", "x_lip", "m_scr1", "m_scr2", "m_scr3",
                        "m_hop"):
                x[IDX[key]] = max(0.0, x[IDX[key]])
        return x

    # -- measurement ---------------------------------------------------------
    def measure(self, x: np.ndarray, rng: np.random.Generator | None = None,
                quantize: bool = True) -> float:
        """Balance reading, g (lag + bias already in the state)."""
        y = x[IDX["y_bal"]]
        if rng is not None:
            y = y + rng.normal(0.0, self.p.balance_sigma_g)
        if quantize:
            y = round(y / self.p.balance_quantum_g) * self.p.balance_quantum_g
        return float(y)

    def is_stable_frame(self, x: np.ndarray) -> bool:
        """The balance's own 'stable' flag: indication has caught up with the pan."""
        return abs(x[IDX["m_cup"]] + x[IDX["b_bal"]] - x[IDX["y_bal"]]) < \
            self.p.balance_stable_band_g

    # -- linear design models -------------------------------------------------
    def linearize(self, x0: np.ndarray, u0: np.ndarray,
                  eps: float = 1e-6) -> tuple[np.ndarray, np.ndarray,
                                              np.ndarray, np.ndarray]:
        """Numerical Jacobians (A, B, C, D) about (x0, u0).

        C is the balance row: the only sensor is the indicated mass.
        """
        n, m = N_STATES, N_INPUTS
        A = np.zeros((n, n))
        f0 = self.f(x0, u0)
        for j in range(n):
            dx = np.zeros(n)
            dx[j] = eps * max(1.0, abs(x0[j]))
            A[:, j] = (self.f(x0 + dx, u0) - self.f(x0 - dx, u0)) / (2 * dx[j])
        B = np.zeros((n, m))
        for j in range(m):
            du = np.zeros(m)
            du[j] = eps * max(1.0, abs(u0[j]))
            B[:, j] = (self.f(x0, u0 + du) - self.f(x0, u0 - du)) / (2 * du[j])
        C = np.zeros((1, n))
        C[0, IDX["y_bal"]] = 1.0
        D = np.zeros((1, m))
        _ = f0
        return A, B, C, D

    def discretize(self, x0: np.ndarray, u0: np.ndarray,
                   dt: float) -> tuple[np.ndarray, np.ndarray]:
        """Zero-order-hold discretization of the linearization at (x0, u0)."""
        from scipy.linalg import expm
        A, B, _, _ = self.linearize(x0, u0)
        n, m = A.shape[0], B.shape[1]
        M = np.zeros((n + m, n + m))
        M[:n, :n] = A
        M[:n, n:] = B
        E = expm(M * dt)
        return E[:n, :n], E[:n, n:]

    # -- structural analysis --------------------------------------------------
    def observability_report(self, x0: np.ndarray, u0: np.ndarray) -> dict:
        """Which states the balance alone can resolve at this operating point."""
        A, _, C, _ = self.linearize(x0, u0)
        n = A.shape[0]
        obs = np.vstack([C @ np.linalg.matrix_power(A, k) for k in range(n)])
        rank = int(np.linalg.matrix_rank(obs, tol=1e-9))
        # which states have any path to the output at all
        reachable_to_y = np.abs(obs).sum(axis=0) > 1e-9
        # structural rank is optimistic: what matters for an estimator is how
        # many directions are observable *well enough* to beat the balance
        # noise, so report the singular-value spectrum too.
        sv = np.linalg.svd(obs, compute_uv=False)
        _, _, vt = np.linalg.svd(obs)
        weak = []
        for k in range(n):
            if sv[k] < sv[0] * 1e-6:
                j = np.argsort(-np.abs(vt[k]))[:3]
                weak.append([STATE_NAMES[i] for i in j])
        return {
            "rank": rank,
            "n_states": n,
            "observable": rank == n,
            "states_with_no_path_to_balance": [STATE_NAMES[i] for i in range(n)
                                               if not reachable_to_y[i]],
            "singular_values": sv.tolist(),
            "n_directions_above_1e6_condition": int(np.sum(sv > sv[0] * 1e-6)),
            "weak_directions_dominant_states": weak,
        }


# --- convenience -----------------------------------------------------------

SALT = (Params.from_json() if SALT_PARAMS_JSON.exists() else Params())


def reduced_bulk_model(alpha_deg: float = 25.0, omega_rpm: float = 45.0,
                       p: Params | None = None) -> dict:
    """The 4-state design model used in the doc's LQG section.

    z = [m_cup, m_air, x_lip, phi],  v = [omega, tap rate],  y = m_cup.
    Valid in the bulk phase, where the lip is spilling (x_lip > capacity) and
    the screw hold-up is at steady state.
    """
    p = p or SALT
    ff = feed_factor(alpha_deg, 1e3, p)
    k = 1.0 / p.tau_spill_s
    tf = p.tau_flight_s
    A = np.array([
        [0.0, 1.0 / tf, 0.0, 0.0],
        [0.0, -1.0 / tf, k, 0.0],
        [0.0, 0.0, -k, ff * omega_rpm / 60.0],
        [0.0, 0.0, 0.0, 0.0],
    ])
    B = np.array([
        [0.0, 0.0],
        [0.0, p.tap_release * lip_capacity(alpha_deg, 0.0, p)
         + tap_floor(alpha_deg, p)],
        [ff / 60.0, -p.tap_release * lip_capacity(alpha_deg, 0.0, p)],
        [0.0, 0.0],
    ])
    C = np.array([[1.0, 0.0, 0.0, 0.0]])
    return {"A": A, "B": B, "C": C, "states": ["m_cup", "m_air", "x_lip", "phi"],
            "inputs": ["omega_rpm", "tap_rate_per_s"],
            "operating_point": {"alpha_deg": alpha_deg, "omega_rpm": omega_rpm,
                                "ff_g_per_rev": ff}}


def _demo() -> None:
    p = SALT
    model = PowderDoserModel(p)
    print(f"parameters: {p.powder_id} ({p.provenance})")
    print(f"  ff(0 deg)  = {feed_factor(0, 53.3, p)*1e3:6.1f} mg/rev")
    print(f"  ff(25 deg) = {feed_factor(25, 53.3, p)*1e3:6.1f} mg/rev")
    print(f"  ff(40 deg) = {feed_factor(40, 53.3, p)*1e3:6.1f} mg/rev")
    print(f"  ff(70 deg) = {feed_factor(70, 53.3, p)*1e3:6.1f} mg/rev")
    print(f"  tau_flight = {p.tau_flight_s:.2f} s, tau_balance = "
          f"{p.tau_balance_s:.2f} s")

    x = initial_state(53.3, alpha_deg=25.0, params=p)
    u = np.array([45.0, 25.0, 0.0])
    t, dt = 0.0, 0.05
    while x[IDX["y_bal"]] < 0.9 and t < 60:
        x = model.step(x, u, dt)
        t += dt
    print(f"\nbulk phase: reached {x[IDX['y_bal']]*1e3:.0f} mg in {t:.1f} s "
          f"({x[IDX['theta']]:.2f} rev phase)")
    u_halt = np.array([0.0, 25.0, 0.0])
    m_at_halt = x[IDX["m_cup"]]
    for _ in range(int(3.0 / dt)):
        x = model.step(x, u_halt, dt)
    print(f"post-halt drift: +{(x[IDX['m_cup']] - m_at_halt)*1e3:.1f} mg "
          f"(in-flight inventory that any anticipative stop must model)")

    x_t = x.copy()
    print("\nten single taps at 25 deg (mg):", end=" ")
    for _ in range(10):
        x_t, dm = model.tap(x_t)
        print(f"{dm*1e3:.2f}", end=" ")
    print()

    x_run = initial_state(53.3, alpha_deg=25.0, params=p)
    x_run[IDX["omega"]] = 45.0
    for label, xs, us in (("auger turning", x_run, u), ("auger halted", x, u_halt)):
        rep = model.observability_report(xs, us)
        print(f"\nobservability from the balance alone, {label}: rank "
              f"{rep['rank']}/{rep['n_states']} "
              f"({rep['n_directions_above_1e6_condition']} well-conditioned); "
              f"no path to the sensor: {rep['states_with_no_path_to_balance']}")

    red = reduced_bulk_model()
    print("\nreduced bulk design model A =")
    print(np.array2string(red["A"], precision=3, suppress_small=True))


if __name__ == "__main__":
    _demo()
