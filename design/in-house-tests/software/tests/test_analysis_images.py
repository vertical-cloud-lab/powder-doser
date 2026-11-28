"""Image analyses against synthetic images with known answers."""

import math

import numpy as np
import pytest

from bench import synth
from bench.analysis import column, drum, heap, psd, spread


# -- test 1: heap -----------------------------------------------------------------

@pytest.mark.parametrize("left,right,round_mm", [(25.0, 25.0, 1.0), (30.0, 33.0, 1.5), (36.0, 36.0, 1.0),
                                                 (41.0, 39.0, 1.2), (48.0, 48.0, 2.0)])
def test_heap_flank_angles_within_half_a_degree(left, right, round_mm):
    img, tr = synth.heap_image(left, right, round_mm=round_mm, rough_mm=0.03, noise=0.02, blur_px=1.0,
                               seed=int(left * 10 + right))
    ref, _ = synth.heap_image(left, right, empty=True, seed=7)
    r = heap.analyze_heap(img, 28.6, ref=ref, mass_g=1.0)
    assert abs(r.left_deg - left) < 0.5
    assert abs(r.right_deg - right) < 0.5
    assert r.volume_mm3 == pytest.approx(tr["volume_mm3"], rel=0.03)
    assert r.height_mm == pytest.approx(tr["height_mm"], abs=0.1)
    assert r.apex_deg == pytest.approx(tr["apex_deg"], abs=0.5)
    assert r.density_kg_m3 == pytest.approx(1e6 / tr["volume_mm3"], rel=0.03)


def test_heap_without_reference_image():
    img, tr = synth.heap_image(34.0, 36.0, round_mm=1.0, rough_mm=0.03, seed=3)
    r = heap.analyze_heap(img, 28.6)
    assert abs(r.left_deg - 34.0) < 0.5 and abs(r.right_deg - 36.0) < 0.5


def test_heap_growth_and_avalanches():
    assert not heap.growth_stopped([0.1, 0.3, 0.5])
    assert heap.growth_stopped([0.5, 0.80, 0.81, 0.815, 0.82])
    assert heap.avalanche_drops([0.5, 0.6, 0.57, 0.65, 0.649]) == pytest.approx([0.03])


# -- test 2: column ---------------------------------------------------------------

GEOM = dict(px_per_mm=16.0, datum_row=1220, x_range=(72, 248), axis_x=159.5)


@pytest.mark.parametrize("h,tilt,bump", [(18.0, 0.0, 0.0), (36.4, 0.3, 0.2), (55.1, 0.1, -0.2), (68.9, 0.2, 0.3)])
def test_column_height_within_0p05_mm(h, tilt, bump):
    img, _ = synth.column_image(h, tilt_mm=tilt, bump_mm=bump, seed=int(h * 10))
    ct = column.column_top(img, GEOM["px_per_mm"], GEOM["datum_row"], GEOM["x_range"], axis_x=GEOM["axis_x"])
    assert ct.top_mm == pytest.approx(h, abs=0.05)


def test_water_calibration_and_densities():
    bore = 13.0
    area = math.pi * (bore / 2) ** 2
    hs, gs = [], []
    for ml in range(1, 9):
        img, _ = synth.column_image(ml * 1000.0 / area, bump_mm=0.0, seed=ml)
        hs.append(column.column_top(img, 16.0, 1220, (72, 248), mode="center").top_mm)
        gs.append(ml * column.water_density(22.0))
    cal = column.VolumeCalibration.from_water(hs, gs, 22.0, meniscus_ml=0.0)
    assert cal.residual_ml < 0.02
    assert cal.bore_mm == pytest.approx(bore, abs=0.02)
    taps = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1250]
    v_true = synth.kawakita_volumes(taps, 8.0, 0.18, 1 / 12.0)
    vols = []
    for n, v in zip(taps, v_true):
        img, _ = synth.column_image(v * 1000 / area, bump_mm=0.1, tilt_mm=0.1, seed=n + 100)
        h = column.column_top(img, 16.0, 1220, (72, 248), axis_x=159.5).top_mm
        vols.append(float(cal.powder_volume(h)))
    d = column.densities(6.0, taps, vols)
    assert d.rho_bulk == pytest.approx(750.0, rel=0.005)
    assert d.hausner == pytest.approx(v_true[0] / v_true[-1], rel=0.005)
    assert d.kawakita_a == pytest.approx(0.18, abs=0.005)
    assert d.kawakita_inv_b == pytest.approx(12.0, rel=0.1)
    assert d.kawakita_r2 > 0.999


def test_water_density_table():
    assert column.water_density(4.0) == pytest.approx(0.99997, abs=1e-5)
    assert column.water_density(20.0) == pytest.approx(0.99820, abs=1e-5)
    assert column.water_density(25.0) == pytest.approx(0.99705, abs=1e-5)


# -- test 4: PSD -------------------------------------------------------------------

def _field_set(n_fields, d50_px, gsd, seed0=0):
    tables, truths = [], []
    for f in range(n_fields):
        img, tr = synth.particle_field(n=170, d50_px=d50_px, gsd=gsd, touch_frac=0.15, seed=seed0 + f)
        tables.append(psd.analyze_field(img, 2.0, field=f))
        truths.append(tr)
    return psd.merge(tables), truths


def test_psd_lognormal_recovery_with_touching_grains():
    d50_px, gsd = 30.0, 1.4
    table, truths = _field_set(5, d50_px, gsd)
    s = psd.psd_summary(table, n_boot=150, by_field=True, um_per_px=2.0)
    assert s["d50_n"] == pytest.approx(d50_px * 2.0, rel=0.05)
    assert s["d10_n"] == pytest.approx(synth.lognormal_quantile(d50_px, gsd, 0.1) * 2.0, rel=0.05)
    assert s["d90_n"] == pytest.approx(synth.lognormal_quantile(d50_px, gsd, 0.9) * 2.0, rel=0.06)
    # the volume median is dominated by a few big grains: within 10 % and inside its CI band
    dv = synth.lognormal_quantile(d50_px, gsd, 0.5, "volume") * 2.0
    assert s["d50_v"] == pytest.approx(dv, rel=0.10)
    # the watershed split the touching pairs: count close to the true in-field count
    true_inside = sum(int((~t["edge"]).sum()) for t in truths)
    assert s["n"] == pytest.approx(true_inside, rel=0.03)
    assert 0.75 < s["aspect_mean"] < 0.92
    assert 0.8 < s["circularity_mean"] <= 1.0


def test_psd_weighted_quantile_and_scale():
    x = np.arange(1, 101, dtype=float)
    assert psd.weighted_quantile(x, np.ones_like(x), 0.5) == pytest.approx(50.5, abs=0.5)
    img, _ = synth.micrometer_image(1.55, 10.0)
    assert psd.scale_from_micrometer(img, 10.0) == pytest.approx(1.55, rel=0.002)


def test_psd_adaptive_threshold_runs():
    img, tr = synth.particle_field(n=120, d50_px=25, gsd=1.3, seed=11)
    img = img * np.linspace(0.85, 1.0, img.shape[1])[None, :]           # uneven backlight
    t = psd.analyze_field(img, 1.0, method="adaptive")
    assert t["ecd_um"].size == pytest.approx(int((~tr["edge"]).sum()), rel=0.1)


# -- test 7: drum ----------------------------------------------------------------------

@pytest.mark.parametrize("angle", [22.0, 31.5, 38.0, 47.0])
def test_drum_surface_angle(angle):
    img, tr = synth.drum_image(angle, seed=int(angle * 10))
    xs, ys = drum.surface_profile(img, tr["center"], tr["radius_px"])
    sa = drum.surface_angle(xs, ys)
    assert sa.angle_deg == pytest.approx(angle, abs=0.3)
    assert sa.r2 > 0.99
    assert drum.fill_fraction(img, tr["center"], tr["radius_px"]) == pytest.approx(0.40, abs=0.03)


def test_drum_found_by_hough():
    img, tr = synth.drum_image(33.0, seed=5)
    (x, y), r = drum.find_drum(img)
    assert abs(x - tr["center"][0]) < 3 and abs(y - tr["center"][1]) < 3 and abs(r - tr["radius_px"]) < 4


def test_drum_avalanche_angles_and_cohesive_index():
    t, a, tr = synth.drum_angle_series(1.0, 120, 10, start_deg=42, stop_deg=34, sd=1.0, noise=0.2, seed=2)
    av = drum.avalanches(t, a, deg_per_frame=0.6)
    assert av.n == len(tr["starts"])
    assert av.start_mean == pytest.approx(np.mean(tr["starts"]), abs=0.3)
    assert av.stop_mean == pytest.approx(np.mean(tr["stops"]), abs=0.3)
    flat = [(np.arange(50.0), np.full(50, 10.0)) for _ in range(5)]
    assert drum.cohesive_index(flat, 100.0) == pytest.approx(0.0)
    assert drum.froude(20, 0.02) == pytest.approx((20 * 2 * math.pi / 60) ** 2 * 0.02 / 9.80665)


# -- test 9: spreading -------------------------------------------------------------------

@pytest.mark.parametrize("seed,void,streaks", [(0, 0.05, 2), (1, 0.10, 4), (2, 0.02, 0)])
def test_spread_coverage_and_streaks(seed, void, streaks):
    img, tr = synth.spread_image(coverage_void=void, n_streaks=streaks, seed=seed)
    m = spread.covered_mask(img)
    assert spread.coverage(m) == pytest.approx(tr["coverage"], abs=0.012)
    sf, n = spread.streaks(m)
    if streaks:
        assert sf == pytest.approx(tr["streak_frac"], rel=0.25)
    else:
        assert sf < 0.002
    assert spread.saturated_fraction(img) < 0.01
    assert spread.packing_fraction(0.2, 3000.0, 0.15, 2165.0) == pytest.approx(0.2 / 1000 / (2165 * 4.5e-7))
