"""The simulated bench (--sim): a powder with known properties, the doser,
the balance, the accessory's sensors and the cameras, on one fake clock.

The accessory side is the real firmware (accessory_main.Accessory) on
sim_hw's register-level fakes; the doser side is doser_bridge's mock
doser; images come from bench.synth. So a --sim run exercises the whole
measurement chain, and its results can be compared with the truth.
"""

import math

import numpy as np

from . import synth
from .analysis import humidity as hum

G = 9.80665

PRESETS = {
    "salt": dict(aor=33.0, aor_sd=0.4, rho_true=2165.0, rho_bulk=1250.0, kaw_a=0.14, kaw_inv_b=9.0,
                 phi_w={"PLA": 22.0, "steel": 17.0, "glass": 14.0, "rough": 31.0}, c_w=8.0,
                 layer_start={1: 38.5, 2: 36.5, 3: 35.5, 5: 34.5}, d50_um=425.0, gsd=1.35,
                 bev_C=0.58, bev_k=1.5, dc_mm=1.2, dc_tap_mm=0.9,
                 uptake={"silica": 0.05, "MgCl2": 0.2, "MgNO3": 0.4, "NaCl": 60.0, "KCl": 150.0}, tau_h=3.0,
                 drum_start=40.0, drum_stop=33.0, drum_sd=0.8, drum_dyn=35.0,
                 ucs_a=0.0, ucs_b=0.0, coverage=0.95, transfer=0.6, q_nc_per_g=20.0, g_per_rev=0.12),
    "flour": dict(aor=47.0, aor_sd=1.0, rho_true=1450.0, rho_bulk=550.0, kaw_a=0.32, kaw_inv_b=25.0,
                  phi_w={"PLA": 28.0, "steel": 24.0, "glass": 20.0, "rough": 40.0}, c_w=40.0,
                  layer_start={1: 62.0, 2: 55.0, 3: 51.0, 5: 47.0}, d50_um=60.0, gsd=1.8,
                  bev_C=0.55, bev_k=2.0, dc_mm=4.5, dc_tap_mm=3.0,
                  uptake={"silica": 2.0, "MgCl2": 30.0, "MgNO3": 45.0, "NaCl": 70.0, "KCl": 85.0}, tau_h=5.0,
                  drum_start=58.0, drum_stop=38.0, drum_sd=4.0, drum_dyn=45.0,
                  ucs_a=0.35, ucs_b=25.0, coverage=0.72, transfer=0.45, q_nc_per_g=5.0, g_per_rev=0.037),
    "generic": dict(aor=38.0, aor_sd=0.6, rho_true=2700.0, rho_bulk=1350.0, kaw_a=0.2, kaw_inv_b=14.0,
                    phi_w={"PLA": 24.0, "steel": 20.0, "glass": 17.0, "rough": 34.0}, c_w=15.0,
                    layer_start={1: 45.0, 2: 41.0, 3: 39.5, 5: 38.5}, d50_um=150.0, gsd=1.5,
                    bev_C=0.58, bev_k=1.6, dc_mm=2.2, dc_tap_mm=1.6,
                    uptake={"silica": 0.2, "MgCl2": 1.0, "MgNO3": 2.0, "NaCl": 5.0, "KCl": 9.0}, tau_h=4.0,
                    drum_start=47.0, drum_stop=36.0, drum_sd=2.0, drum_dyn=39.0,
                    ucs_a=0.15, ucs_b=8.0, coverage=0.88, transfer=0.55, q_nc_per_g=12.0, g_per_rev=0.08),
}


def preset_for(jar):
    j = jar.lower()
    if "nacl" in j or "salt" in j:
        return "salt"
    if "flour" in j:
        return "flour"
    return "generic"


class SimWorld:
    def __init__(self, jar="NaCl-01", seed=0, clock=None):
        import os
        import sys
        fw = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                          "firmware")
        if fw not in sys.path:
            sys.path.insert(0, fw)
        import sim_hw
        self.clock = clock or sim_hw.FakeClock(t0=0.0)
        self.preset = preset_for(jar)
        self.p = dict(PRESETS[self.preset])
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.acc = None
        self.scene = None
        self.s = {}
        self.plate_deg = 45.0
        self.gross = 0.0                 # what sits on the balance pan (g)
        self.tare_g = 0.0
        self.lag_s = 0.25
        self.reading = 0.0               # balance output after its first-order lag
        self.rpm = 60.0
        self.rotation = None
        self.env = (22.0, 38.0)
        self.frames = 0

    # -- time ----------------------------------------------------------------
    def now(self):
        return self.clock.t / 1000.0

    def attach_accessory(self, acc):
        self.acc = acc

    def advance(self, seconds):
        if seconds <= 0:
            return
        if self.acc is not None:
            self.acc.advance(seconds)
        else:
            self.clock.advance(seconds * 1000.0)
            self.tick(seconds)

    def tick(self, dt):
        """Continuous physics, called every accessory step (2 ms) or once
        per coarse jump."""
        fn = getattr(self, "_tick_" + str(self.scene), None)
        if fn:
            fn(dt)
        a = 1.0 if self.lag_s <= 0 else min(1.0, dt / self.lag_s)
        self.reading += a * (self.gross - self.reading)

    # -- hooks for the accessory fakes -----------------------------------------
    def accessory_hooks(self):
        return {"env": lambda: (self.env[0] + self.rng.normal(0, 0.02), self.env[1] + self.rng.normal(0, 0.1)),
                "lc_grams": self._lc_grams, "q_volts": self._q_volts, "jolt_g": self._jolt}

    # -- doser plant (doser_bridge.MockDoserSerial calls these) --------------------
    def rotate(self, auger_deg, rpm):
        self.rpm = rpm
        dur = abs(auger_deg) / 360.0 * 60.0 / max(rpm, 0.1)
        revs = max(0.0, auger_deg) / 360.0
        flow = 0.3 + self.plate_deg / 45.0 * 0.7
        n = 10
        for _ in range(n):
            self.advance(dur / n)
            dm = max(0.0, self.rng.normal(self.p["g_per_rev"] * flow * revs / n,
                                          0.08 * self.p["g_per_rev"] * flow * revs / n))
            self.deliver(dm)

    def tilt(self, plate_deg):
        self.advance(abs(plate_deg - self.plate_deg) / 30.0)
        self.plate_deg = plate_deg

    def tap(self, n):
        self.deliver(0.002 * n * self.p["g_per_rev"])

    def tare(self):
        self.advance(1.5)
        self.tare_g = self.gross

    def grams(self):
        self.advance(0.05)
        g = self.reading - self.tare_g + self.rng.normal(0, 0.00005)
        stable = abs(self.gross - self.reading) < 0.0005
        return round(g, 4), stable

    def estop(self):
        self.rotation = None

    def start_rotation(self, auger_deg, rpm):
        """rotate_async in --sim: the drum turns while frames are taken."""
        dur = abs(auger_deg) / 360.0 * 60.0 / max(rpm, 0.1)
        self.rotation = {"t0": self.now(), "t1": self.now() + dur, "rpm": rpm}
        self._drum_series(rpm, dur)
        world = self

        class Handle:
            def wait(self, timeout=None):
                left = world.rotation["t1"] - world.now() if world.rotation else 0
                world.advance(max(0.0, left))
                world.rotation = None
                return {"ok": True}
        return Handle()

    def deliver(self, dm):
        fn = getattr(self, "_deliver_" + str(self.scene), None)
        if fn:
            fn(dm)
        else:
            self.gross += dm

    # -- operator actions (prompts) ------------------------------------------------
    def operator(self, action, **kw):
        fn = getattr(self, "_op_" + action, None)
        if fn:
            fn(**kw)

    def set_scene(self, name, **kw):
        self.scene = name
        self.s = dict(kw)
        init = getattr(self, "_init_" + name, None)
        if init:
            init(**kw)

    def render(self, camera):
        self.frames += 1
        fn = getattr(self, "_render_" + str(self.scene))
        return fn(camera)

    # =========================================================================
    # 1 heap
    # =========================================================================
    def _init_heap(self, pedestal_mm=20.0, px_per_mm=28.6):
        self.s.update(pedestal_mm=pedestal_mm, px_per_mm=px_per_mm, heap_g=0.0, spilled=0.0)
        self.gross = 12.0 + 15.0 + 2.0             # pan adapter + riser + pedestal (SPEC 1)
        self._new_pour()

    def _new_pour(self):
        p = self.p
        aor = self.rng.normal(p["aor"], p["aor_sd"])
        d = self.rng.normal(0, 0.4)
        self.s.update(left=aor + d, right=aor - d, heap_g=0.0)
        R = self.s["pedestal_mm"] / 2.0
        t = math.tan(math.radians(aor))
        self.s["cap_g"] = p["rho_bulk"] * 1e-6 * math.pi * R ** 3 * t / 3.0

    def _deliver_heap(self, dm):
        cap = self.s["cap_g"]
        m = self.s["heap_g"]
        keep = dm * max(0.0, 1.0 - (m / cap) ** 4)
        if m > 0.5 * cap and self.rng.random() < 0.08:
            keep -= self.rng.uniform(0.01, 0.04) * m        # an avalanche off the rim
        self.s["heap_g"] = max(0.0, m + keep)
        self.gross = 29.0 + self.s["heap_g"]

    def _op_new_heap(self):
        self._new_pour()
        self.gross = 29.0

    def _render_heap(self, camera):
        s = self.s
        m = s["heap_g"]
        aor = 0.5 * (s["left"] + s["right"])
        vol = m / (self.p["rho_bulk"] * 1e-6)
        r = (3.0 * vol / (math.pi * math.tan(math.radians(aor)))) ** (1.0 / 3.0) if vol > 0 else 0.0
        hb = min(2.0 * r, s["pedestal_mm"])
        img, tr = synth.heap_image(s["left"], s["right"], base_mm=s["pedestal_mm"], px_per_mm=s["px_per_mm"],
                                   heap_base_mm=max(hb, 0.5), empty=m < 1e-4, seed=self.seed * 1000 + self.frames,
                                   round_mm=0.8, rough_mm=0.03)
        self.s["truth"] = tr
        return img

    # =========================================================================
    # 2 density (and the water calibration)
    # =========================================================================
    GEOM = {"px_per_mm": 16.0, "datum_row": 1220, "x_range": (72, 248), "axis_x": 159.5, "bore_mm": 13.0}

    def _init_density(self):
        self.s.update(powder_g=0.0, water_ml=0.0, taps0=None, v0=None)
        self.gross = 30.0                            # holder + cylinder, tared
        self.tare_g = 30.0
        self.reading = 30.0

    def _deliver_density(self, dm):
        self.s["powder_g"] += dm
        self.gross += dm

    def _op_add_water(self, ml=1.0):
        v = ml * (1 + self.rng.normal(0, 0.03))
        self.s["water_ml"] += v
        self.gross += v * 0.9978

    def _op_move_to_tapper(self):
        self.s["v0"] = self.s["powder_g"] / (self.p["rho_bulk"] / 1000.0)
        self.s["taps0"] = self._cam_taps()

    def _cam_taps(self):
        if self.acc is None:
            return 0.0
        hw = self.acc.hw
        if hw.motor.name != "cam":
            return 0.0
        return hw.tic.phys / hw.motor.usteps_rev * hw.motor.p["lobes"]

    def column_mm(self):
        g = self.GEOM
        area = math.pi * (g["bore_mm"] / 2.0) ** 2
        if self.s.get("water_ml", 0) > 0 and self.s.get("powder_g", 0) == 0:
            # the camera reads the flat centre of the meniscus; the water
            # raised at the wall (perimeter x 7.4 mm^2) sits above it
            men_ml = math.pi * g["bore_mm"] * 7.4 / 1000.0
            return (self.s["water_ml"] - men_ml) * 1000.0 / area
        if self.s.get("v0") is None:
            v = self.s["powder_g"] / (self.p["rho_bulk"] / 1000.0)
        else:
            n = max(0.0, self._cam_taps() - self.s["taps0"])
            v = float(synth.kawakita_volumes([n], self.s["v0"], self.p["kaw_a"], 1.0 / self.p["kaw_inv_b"])[0])
        return v * 1000.0 / area

    def _render_density(self, camera):
        g = self.GEOM
        bump = 0.0 if self.s.get("water_ml", 0) > 0 and self.s.get("powder_g", 0) == 0 else 0.15
        img, _ = synth.column_image(self.column_mm(), bore_mm=g["bore_mm"], px_per_mm=g["px_per_mm"],
                                    datum_row=g["datum_row"], bump_mm=bump, tilt_mm=0.05,
                                    seed=self.seed * 1000 + self.frames)
        return img

    # =========================================================================
    # 3 tilting plate
    # =========================================================================
    def _init_plate(self, mode="A", coupon="PLA", px_per_mm=12.0):
        self.s.update(mode=mode, coupon=coupon, px_per_mm=px_per_mm, slip_t=None, theta_s=None, placed=False)

    def _op_place_ring(self, mass_g, area_mm2=None, depth_mm=None):
        p = self.p
        if self.s["mode"] == "A":
            th = synth.slip_angle_for(mass_g, area_mm2, p["phi_w"][self.s["coupon"]], p["c_w"])
        else:
            th = p["layer_start"].get(int(depth_mm), p["layer_start"][2])
        self.s.update(theta_s=th + self.rng.normal(0, 0.25), slip_t=None, placed=True)

    def _table_deg(self):
        return self.acc.hw.table_from_pwm() if self.acc else 0.0

    def _tick_plate(self, dt):
        s = self.s
        if s.get("placed") and s["slip_t"] is None and self._table_deg() >= s["theta_s"]:
            s["slip_t"] = self.now()

    def _jolt(self):
        st = self.s.get("slip_t") if self.scene == "plate" else None
        return 0.05 if st is not None and 0 <= self.now() - st < 0.04 else 0.0

    def _render_plate(self, camera):
        s = self.s
        st = s["slip_t"] if s["slip_t"] is not None else 1e12
        ring = (25.0, 8.0) if s["mode"] == "A" else (60.0, 3.0)
        fr = synth.ring_frames([self.now()], st, px_per_mm=s["px_per_mm"], ring_mm=ring,
                               seed=self.seed * 1000 + self.frames, x0_mm=5.0)
        return fr[0]

    # =========================================================================
    # 4 PSD
    # =========================================================================
    def _init_psd(self, um_per_px=None, spacing_um=10.0):
        # zoom set so a median grain spans about 30 px, within the lens's 0.9-13 um/px
        self.s["um_per_px"] = um_per_px or min(12.9, max(0.9, self.p["d50_um"] / 30.0))
        self.s["spacing_um"] = spacing_um

    def _render_psd(self, camera):
        if camera == "micrometer":
            img, _ = synth.micrometer_image(self.s["um_per_px"], self.s["spacing_um"])
            return img
        d50_px = self.p["d50_um"] / self.s["um_per_px"]
        img, tr = synth.particle_field(n=170, d50_px=d50_px, gsd=self.p["gsd"], seed=self.seed * 1000 + self.frames)
        return img

    # =========================================================================
    # 5 orifice cup
    # =========================================================================
    def _init_orifice(self, disc_mm=6.0):
        self.s.update(disc_mm=disc_mm, cup_g=0.0, catch_g=0.0, on_cup=True, flow_noise=1.0)
        self.gross = 0.0

    def _deliver_orifice(self, dm):
        self.s["cup_g"] += dm
        if self.s["on_cup"]:
            self.gross += dm

    def _op_cup_to_holder(self):
        self.s["on_cup"] = False
        self.gross = 0.0                             # empty catch beaker, tared next
        self.s["flow_noise"] = float(self.rng.normal(1.0, 0.03))

    def _op_new_disc(self, disc_mm):
        self.s.update(disc_mm=disc_mm, cup_g=0.0, catch_g=0.0, on_cup=True)
        self.gross = 0.0

    def _gate_open(self):
        if self.acc is None:
            return False
        return self.acc.hw.servo_a.driven and self.acc.hw.servo_a.angle > 60.0

    def _tapping(self):
        if self.acc is None:
            return False
        return "tap" in self.acc.sim.acc.tasks

    def _tick_orifice(self, dt):
        s = self.s
        if s["on_cup"] or s["cup_g"] <= 0 or not self._gate_open():
            return
        p = self.p
        D = s["disc_mm"]
        d_mm = p["d50_um"] / 1000.0
        if D >= p["dc_mm"]:
            w = synth.beverloo_rate_g_s(D, p["bev_C"], p["bev_k"], d_mm, p["rho_bulk"]) * s["flow_noise"]
        elif D >= p["dc_tap_mm"] and self._tapping():
            # taps break arches: intermittent flow, half the rate at D_c scaled down
            w = 0.5 * synth.beverloo_rate_g_s(p["dc_mm"], p["bev_C"], p["bev_k"], d_mm, p["rho_bulk"]) \
                * (D / p["dc_mm"]) ** 2.5
        else:
            w = 0.0
        dm = min(s["cup_g"], w * dt)
        s["cup_g"] -= dm
        s["catch_g"] += dm
        self.gross = s["catch_g"]

    # =========================================================================
    # 6 humidity
    # =========================================================================
    def _init_humidity(self, box="NaCl", dish_g=4.0):
        self.s.update(box=box, dish_g=dish_g, t_in=None, sample_dry_g=None)
        self.gross = 0.0

    def _op_sample_in_box(self, sample_g=3.0):
        self.s.update(t_in=self.now(), sample_dry_g=sample_g)

    def _op_dish_on_balance(self):
        s = self.s
        u = 0.0
        if s["t_in"] is not None:
            th = (self.now() - s["t_in"]) / 3600.0
            u = self.p["uptake"][s["box"]] * (1 - math.exp(-th / self.p["tau_h"]))
        m = s["dish_g"] + (s["sample_dry_g"] or 0.0) * (1 + u / 1000.0)
        self.gross = m
        self.reading = m

    def _op_dish_off(self):
        self.gross = 0.0
        self.reading = 0.0

    def box_reading(self, box):
        rh = hum.nominal_rh(box, self.env[0]) + self.rng.normal(0, 0.3)
        return self.env[0] + self.rng.normal(0, 0.05), rh

    # =========================================================================
    # 7 drum
    # =========================================================================
    def _init_drum(self, px_per_mm=7.5):
        self.s.update(px_per_mm=px_per_mm, series=None)

    def _drum_series(self, rpm, dur):
        if self.scene != "drum":
            return
        p = self.p
        fps = 50.0
        if rpm <= 2.0:
            t, a, _ = synth.drum_angle_series(rpm, dur + 1, fps, p["drum_start"], p["drum_stop"], p["drum_sd"],
                                              noise=0.0, seed=self.seed + int(rpm * 10))
        else:
            t, a, _ = synth.drum_angle_series(rpm, dur + 1, fps, dynamic_deg=p["drum_dyn"] + 0.4 * rpm,
                                              noise=0.3 + 0.1 * p["drum_sd"], seed=self.seed + int(rpm * 10))
        self.s["series"] = (t + self.now(), a)

    def drum_angle(self):
        ser = self.s.get("series")
        if ser is None:
            return self.p["drum_stop"]
        return float(np.interp(self.now(), ser[0], ser[1]))

    def _render_drum(self, camera):
        img, _ = synth.drum_image(self.drum_angle(), px_per_mm=self.s["px_per_mm"], shape=(360, 360),
                                  seed=self.seed * 1000 + self.frames)
        return img

    def drum_geometry(self):
        R = 20.0 * self.s["px_per_mm"]
        return (180.0, 180.0), R

    # =========================================================================
    # 8 unconfined strength (load cell + stage)
    # =========================================================================
    def _init_ucs(self, gap0_mm=12.0, sample_g=11.0):
        self.s.update(gap0=gap0_mm, sample_g=sample_g, sample_on=False, peak_g=0.0, failed=False, sigma1=0.0)

    def _op_form_sample(self, sigma1_pa, sample_g=None):
        p = self.p
        sc = p["ucs_a"] * sigma1_pa + p["ucs_b"] if p["ucs_a"] > 0 else 0.0
        sc *= float(self.rng.normal(1.0, 0.05))
        area = math.pi * 0.01 ** 2
        self.s.update(sample_on=True, failed=False, sigma1=sigma1_pa,
                      peak_g=sc * area / G * 1000.0, sample_g=sample_g or self.s["sample_g"])

    def _op_remove_sample(self):
        self.s["sample_on"] = False

    def _stage_mm(self):
        return self.acc.hw.stage_mm() if self.acc else 0.0

    def _lc_grams(self):
        if self.scene != "ucs":
            return 0.0
        s = self.s
        if not s["sample_on"]:
            return 0.0
        pen = self._stage_mm() - s["gap0"]
        f = 0.0
        if s["peak_g"] > 0 and pen > 0:
            stiff = s["peak_g"] / 0.6
            if not s["failed"] and pen * stiff >= s["peak_g"]:
                s["failed"] = True
            f = 0.3 * s["peak_g"] if s["failed"] else pen * stiff
        return s["sample_g"] + f

    # =========================================================================
    # 9 spreading
    # =========================================================================
    def _init_spread(self, coupon="steel"):
        self.s.update(coupon=coupon, coupon_g=24.000 if coupon == "steel" else 4.000, line_g=0.0, layer_g=None,
                      spread_speed=None, on_balance=True)
        self.gross = self.s["coupon_g"]
        self.reading = self.gross
        self.tare_g = 0.0

    def _deliver_spread(self, dm):
        self.s["line_g"] += dm
        self.gross += dm

    def _op_coupon_off(self):
        self.s["on_balance"] = False
        self.gross = 0.0

    def _op_spread_done(self, speed):
        s = self.s
        s["spread_speed"] = speed
        frac = self.p["transfer"] * (1 - 0.002 * speed) * float(self.rng.normal(1, 0.03))
        s["layer_g"] = s["line_g"] * frac

    def _op_coupon_on(self):
        s = self.s
        s["on_balance"] = True
        self.gross = s["coupon_g"] + (s["layer_g"] if s["layer_g"] is not None else s["line_g"])
        self.reading = self.gross

    def _op_clean_coupon(self):
        s = self.s
        s.update(line_g=0.0, layer_g=None, spread_speed=None, on_balance=True)
        self.gross = s["coupon_g"]
        self.reading = self.gross

    def _render_spread(self, camera):
        s = self.s
        if s["spread_speed"] is None:
            void = 0.97
        else:
            void = 1.0 - (self.p["coverage"] - 0.0008 * s["spread_speed"])
        n_streaks = int(self.rng.poisson(0.5 + s["spread_speed"] / 40.0)) if s["spread_speed"] else 0
        img, tr = synth.spread_image(coverage_void=max(0.0, void), n_streaks=n_streaks,
                                     seed=self.seed * 1000 + self.frames)
        self.s["truth"] = tr
        return img

    # =========================================================================
    # 10 Faraday cup
    # =========================================================================
    def _init_faraday(self, cup_g=21.500):
        self.s.update(cup_g=cup_g, powder_g=0.0, q_nc=0.0, t_zero=None, in_cup=False)
        self.gross = 0.0

    def _op_cup_on_balance(self):
        self.gross = self.s["cup_g"] + self.s["powder_g"]
        self.reading = self.gross

    def _op_cup_in_shield(self):
        self.s["in_cup"] = True
        self.gross = 0.0
        self.reading = 0.0

    def _op_empty_cup(self):
        self.s.update(powder_g=0.0, q_nc=0.0, in_cup=False)
        self.gross = 0.0
        self.reading = 0.0

    def _deliver_faraday(self, dm):
        if self.s["in_cup"]:
            self.s["powder_g"] += dm
            self.s["q_nc"] += self.p["q_nc_per_g"] * dm * float(self.rng.normal(1.0, 0.1))

    def _tick_faraday(self, dt):
        """The reed relay shorts C_f: while it is closed the integrator holds zero."""
        if self.acc is not None and self.acc.sim.acc.relay_closed:
            self.s["t_zero"] = None
            self.s["q0"] = self.s["q_nc"]

    def _q_volts(self):
        if self.scene != "faraday" or self.acc is None:
            return 0.0
        acc = self.acc.sim.acc
        if acc.relay_closed:
            self.s["t_zero"] = None
            self.s["q0"] = self.s["q_nc"]
            return 0.0
        if self.s["t_zero"] is None:
            self.s["t_zero"] = self.now()
            self.s["q0"] = self.s["q_nc"]
        q = self.s["q_nc"] - self.s.get("q0", 0.0) + 0.005 * (self.now() - self.s["t_zero"])
        return -q / acc.q_cf_nf
