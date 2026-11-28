"""Test 10: Faraday cup. Charge from ADS1115 counts and C_f, drift-corrected
charge step, q/m."""

from dataclasses import asdict, dataclass

import numpy as np

from .common import linfit


def counts_to_nc(counts, fsr_v=4.096, cf_nf=10.0, sign=-1):
    v = np.asarray(counts, float) * fsr_v / 32768.0
    return sign * cf_nf * v


@dataclass
class ChargeStep:
    dq_nc: float
    drift_nc_s: float
    baseline_sd_nc: float
    settled: bool
    settle_change_pct: float
    t_read: float

    def to_dict(self):
        return asdict(self)


def charge_step(t, q_nc, t_dose_start, t_dose_end, settle_s=2.0, read_s=1.0):
    """Charge delivered: the mean over [t_end + settle, + read_s] minus the
    pre-dose baseline line (drift from the amplifier's bias current)
    extrapolated to the same times."""
    t = np.asarray(t, float)
    q = np.asarray(q_nc, float)
    pre = t < t_dose_start
    if pre.sum() >= 3:
        f = linfit(t[pre], q[pre])
        drift, icpt = f.slope, f.intercept
        base_sd = float(np.std(q[pre] - (drift * t[pre] + icpt)))
    else:
        drift, icpt, base_sd = 0.0, float(q[0]), float("nan")
    t_a = t_dose_end + settle_s
    win = (t >= t_a) & (t <= t_a + read_s)
    if win.sum() < 2:
        win = t >= t[-1] - read_s
    resid = q[win] - (drift * t[win] + icpt)
    dq = float(resid.mean())
    half = max(1, win.sum() // 2)
    first, last = resid[:half].mean(), resid[-half:].mean()
    change = 100.0 * abs(last - first) / max(abs(dq), 1e-9)
    return ChargeStep(dq, float(drift), base_sd, change < 2.0, float(change), float(t[win].mean()))


def q_over_m(dq_nc, mass_g):
    """C/kg from nC and g."""
    return dq_nc * 1e-9 / (mass_g * 1e-3)
