"""Stream analyses (IMU, balance, load cell, charge) against synthetic data."""

import math

import numpy as np
import pytest

from bench import synth
from bench.analysis import faraday, humidity, orifice, plate, ucs


# -- test 3: tilting plate ------------------------------------------------------------

def test_slip_from_frames_and_imu():
    slip_t = 41.37
    ts = np.arange(0, 50, 0.2)
    frames = synth.ring_frames(ts, slip_t, seed=1)
    disp = plate.ring_displacement(frames, 12.0)
    t_s, _ = plate.detect_slip(ts, disp)
    assert t_s == pytest.approx(slip_t, abs=0.1)
    t, deg, jolt = synth.imu_ramp(0.5, 50, 20, 0.0, slip_t=slip_t)
    tj = plate.jolt_time(t, jolt)
    assert tj == pytest.approx(slip_t, abs=0.1)
    first = min(t_s, tj)
    assert plate.ramp_angle_at(t_s, t, deg, first) == pytest.approx(0.5 * slip_t, abs=0.06)
    assert plate.ramp_rate(t, deg, first) == pytest.approx(0.5, abs=0.01)


def test_ramp_angle_ignores_the_jolt_tilt_error():
    t = np.arange(0, 30, 0.05)
    deg = 0.5 * t
    deg[t >= 20.0] += 1.5            # the accelerometer reads the slip's jolt as tilt
    assert plate.ramp_angle_at(20.0, t, deg, 20.0) == pytest.approx(10.0, abs=1e-6)
    assert plate.angle_at(20.05, t, deg) > 11.0


def test_wall_friction_fit_recovers_phi_and_adhesion():
    rng = np.random.default_rng(4)
    area = math.pi * 12.5 ** 2
    sig, tau = [], []
    for lid in (0, 5, 15):
        for _ in range(3):
            m = 2.5 + 3.0 + lid
            th = synth.slip_angle_for(m, area, 22.0, 10.0) + rng.normal(0, 0.2)
            s, t = plate.stresses_at_slip(m, th, area)
            sig.append(s)
            tau.append(t)
    wf = plate.wall_friction_fit(sig, tau)
    assert wf.phi_w_deg == pytest.approx(22.0, abs=1.0)
    assert wf.c_w_pa == pytest.approx(10.0, abs=4.0)
    assert min(sig) > 60 and max(sig) < 460                 # SPEC: 70-450 Pa


def test_layer_start_from_frame_differences():
    ts = np.arange(0, 20, 0.25)
    frames = synth.ring_frames(ts, 12.0, ring_mm=(60.0, 3.0), seed=3)
    k, diffs = plate.layer_start(frames)
    assert ts[k] == pytest.approx(12.0, abs=0.3)


# -- test 5: orifice cup ------------------------------------------------------------------

@pytest.mark.parametrize("D", [6.0, 4.0, 3.0, 2.0])
def test_flow_rate_with_balance_lag(D):
    W = synth.beverloo_rate_g_s(D, 0.58, 1.5, 0.4, 1200)
    t, m, _ = synth.balance_stream(W, 5.0, hz=10, lag_s=0.25, seed=int(D * 10))
    f = orifice.flow_rate(t, m, lag_s=0.25)
    assert f.rate_g_s == pytest.approx(W, rel=0.02)


def test_beverloo_fit_and_critical_orifice():
    Ds = [6.0, 5.08, 4.0, 3.0, 2.54, 2.0]
    rng = np.random.default_rng(1)
    W = [synth.beverloo_rate_g_s(D, 0.58, 1.5, 0.4, 1200) * rng.normal(1, 0.01) for D in Ds]
    bf = orifice.beverloo_fit(Ds, W, 1200, 0.4)
    assert bf.C == pytest.approx(0.58, rel=0.05)
    assert bf.k == pytest.approx(1.5, abs=0.15)
    d_no, d_yes, est = orifice.critical_orifice({6: True, 3: True, 2: True, 1.5: False, 1: False})
    assert (d_no, d_yes) == (1.5, 2) and est == pytest.approx(math.sqrt(3.0))
    assert orifice.sigma_c_from_dc(1000.0, 3.0) == pytest.approx(1000 * 9.80665 * 0.003 / 2.2)


def test_no_flow_detection():
    t = np.arange(0, 60, 0.1)
    m = np.random.default_rng(0).normal(0, 0.0003, t.size)
    assert not orifice.flowed(t, m, 0.05, 0.0, 60.0)
    t2, m2, _ = synth.balance_stream(0.01, 5.0, t_end=60.0)
    assert orifice.flowed(t2, m2, 0.05, 0.0, 60.0)


# -- test 6: humidity ------------------------------------------------------------------------

def test_uptake_fit_and_deliquescence():
    t, u = synth.uptake_series(25.0, 4.0, noise=0.2, seed=2)
    f = humidity.uptake_fit(t, u)
    assert f.u_eq == pytest.approx(25.0, rel=0.05)
    assert f.tau_h == pytest.approx(4.0, rel=0.15)
    assert f.r2 > 0.99
    onset = humidity.deliquescence_onset([5, 32.8, 52.9, 75.3, 84.3], [0.1, 0.3, 0.6, 40, 70])
    assert onset[0] == 52.9 and onset[1] == 75.3
    assert humidity.nominal_rh("NaCl", 25.0) == pytest.approx(75.29)
    assert humidity.nominal_rh("MgCl2", 22.5) == pytest.approx((33.07 + 32.78) / 2)
    assert humidity.uptake_mg_per_g([3.06], 3.0)[0] == pytest.approx(20.0)


# -- test 8: unconfined strength ------------------------------------------------------------------

@pytest.mark.parametrize("peak", [0.5, 3.2, 12.0])
def test_ucs_peak_force(peak):
    t, g, _ = synth.ucs_stream(peak, noise_g=0.002, seed=int(peak * 10))
    pk = ucs.peak_force(t, g, 20.0)
    assert pk.detected and pk.failed
    assert pk.peak_g == pytest.approx(peak, rel=0.02, abs=0.01)
    area = math.pi * 0.01 ** 2
    assert pk.sigma_c_pa == pytest.approx(pk.peak_g / 1000 * 9.80665 / area)


def test_ucs_collapse_and_flow_function():
    t = np.arange(0, 20, 1 / 80)
    g = 11.0 + np.random.default_rng(0).normal(0, 0.002, t.size)
    pk = ucs.peak_force(t, g)
    assert not pk.detected and pk.sigma_c_pa == 0.0
    assert ucs.consolidation_mass_g(1000.0) == pytest.approx(32.0, rel=0.01)       # SPEC: 1 kPa = 32 g
    ff = ucs.flow_function([200, 500, 1000, 2000], [100, 150, 220, 380])
    assert ff["ffc"][0] == pytest.approx(2.0) and ff["class"][3] == "easy-flowing"
    assert ucs.jenike_class(None).startswith("free")


# -- test 10: Faraday cup ---------------------------------------------------------------------------

def test_charge_step_with_drift():
    t, q, _ = synth.charge_stream(25.0, drift_nc_s=0.01, noise_nc=0.03, seed=1)
    cs = faraday.charge_step(t, q, 5.0, 8.0, settle_s=2.0)
    assert cs.dq_nc == pytest.approx(25.0, abs=0.3)
    assert cs.settled
    assert faraday.q_over_m(25.0, 0.8) == pytest.approx(3.125e-5)
    assert faraday.counts_to_nc(16384, 4.096, 10.0)[()] == pytest.approx(-20.48)


def test_isotherm_from_box_results():
    boxes = [{"nominal_rh": rh, "fit": {"u_eq": u}} for rh, u in
             ((84.3, 150.0), (5.0, 0.05), (32.8, 0.2), (75.3, 60.0), (52.9, 0.4))]
    iso = humidity.isotherm(boxes)
    assert iso["rh"] == [5.0, 32.8, 52.9, 75.3, 84.3]
    assert iso["onset"][:2] == (52.9, 75.3)
