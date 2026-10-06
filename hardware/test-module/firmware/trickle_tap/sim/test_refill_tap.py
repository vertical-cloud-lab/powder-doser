"""CPython tests for the refill-tap endgame (no hardware needed).

Drives the real ``RefillTapDoser`` (and through it the stock
``TrickleTapDoser`` / ``ThreePhaseDoser`` machinery) on the fakes from
``test_trickle_tap.py``, plus ``TipPlant``: a plant whose tap yield
decays as the tube tip drains and whose auger rotation from rest
refills it -- the shape of the PR #166 rig logs (2.8 mg on the first tap
after the auger stops, about 0.5 mg after 40).  TipPlant's refill
response is an ASSUMPTION; these tests check the endgame's decisions,
guards and budgets, not how much a real refill helps (that is what the
rig runs are for).

Run:  python3 hardware/test-module/firmware/trickle_tap/sim/test_refill_tap.py
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_trickle_tap as tt         # noqa: E402  (stubs config/tic, fakes)
import main_three_phase as m3         # noqa: E402
import trickle_params                 # noqa: E402
from trickle_controller import TrickleTapDoser, params_dict   # noqa: E402
from refill_tap import FIRMWARE_ID, RefillTapDoser            # noqa: E402

check = tt.check
TOL = trickle_params.TOLERANCE_G


class TipPlant(tt.Plant):
    """tt.Plant plus a drainable tube tip that the taps work on.

    A tap moves ``tap_frac`` of the tip charge to the pan and shakes
    ``tube_feed_g`` down from the tube into the tip (the slow resupply
    that holds drained real yields near 0.5 mg).  A rotation from rest of
    ``revs`` pushes ``ff_rest * revs`` out of the screw: ``direct_frac``
    of it falls straight into the pan, the rest charges the tip, and
    with probability ``slug_p`` a ``slug_g`` slug drops as well.
    """

    def __init__(self, tip_g=0.003, tap_frac=0.065, tube_feed_g=0.0003,
                 tube_g=0.2, ff_rest=0.35, direct_frac=0.4, slug_p=0.0,
                 slug_g=0.0, **kw):
        super().__init__(**kw)
        self.tip = tip_g
        self.tap_frac = tap_frac
        self.tube_feed = tube_feed_g
        self.tube = tube_g
        self.ff_rest = ff_rest
        self.direct_frac = direct_frac
        self.slug_p = slug_p
        self.slug_g = slug_g
        self.rotations = 0

    def nudge(self, revs):
        moved = min(self.hopper, self.ff_rest * revs)
        self.hopper -= moved
        direct = self.direct_frac * moved
        if self.slug_p > 0.0 and self.rng.random() < self.slug_p:
            direct += self.slug_g
        self.pan += direct
        self.tip += (1.0 - self.direct_frac) * moved
        self.rotations += 1

    def tap_once(self):
        moved = self.tap_frac * self.tip
        self.tip -= moved
        self.pan += moved
        feed = min(self.tube, self.tube_feed)
        self.tube -= feed
        self.tip += feed


class TimedStepper(tt.FakeStepper):
    """FakeStepper whose position moves cost the rig's wall-clock time:
    Stepper._wait_estimated_time waits the move + 0.2 s + 2 s."""

    def __init__(self, plant, clock):
        super().__init__(plant)
        self.clock = clock

    def rotate_degrees(self, deg):
        super().rotate_degrees(deg)
        move_s = abs(deg) / 360.0 / (max(1.0, self._rpm) / 60.0)
        self.clock.sleep_ms(int(1000 * (move_s + 2.2)))


def make(cls, plant, p_over=None, log=lambda *a: None):
    clock = tt.VirtualClock(plant)
    scale = tt.FakeScale(plant, clock)
    stepper = TimedStepper(plant, clock)
    tap = tt.FakeTap(plant)
    servo = tt.FakeServo(plant)
    p = params_dict(trickle_params)
    p["log_to_flash"] = False
    p["print_every_n_polls"] = 10 ** 9
    if cls is RefillTapDoser:
        import refill_params
        p.update(params_dict(refill_params))
    if p_over:
        p.update(p_over)
    doser = cls(stepper, tap, servo, scale, tt._config, p=p, log=log,
                monotonic=clock.time, sleep_ms=clock.sleep_ms,
                ticks_ms=clock.ticks_ms)
    return doser, tap, clock


def endgame(cls, plant_kw, target=0.5, short_g=0.050, p_over=None,
            log=lambda *a: None):
    """Run ONLY the tap stage, from rest, ``short_g`` under ``target``.

    Calls ``_run_phase`` exactly as both builds' dose() does for stage
    3, so the result does not depend on which bulk/trickle is around it.
    """
    plant = TipPlant(**plant_kw)
    start = target - short_g
    plant.pan = plant.b = start
    doser, tap, clock = make(cls, plant, p_over, log)
    p = doser.p
    doser.timeout_s = p["dose_timeout_s"]
    doser.thresholds = [p["trickle_start_remaining_g"], p["tolerance_g"]]
    doser.overshoot_abort_g = float(p.get("overshoot_abort_g", 0.0))
    doser.refill_events, doser.tap_yields = [], []
    state = {"taps": 0, "deg": 0.0, "nudges": 0}
    grams, status, cycles = doser._run_phase(
        3, doser._tap_phase(), p["tolerance_g"], target, start, clock.t,
        state)
    return {"grams": grams, "status": status, "cycles": cycles,
            "taps": state["taps"], "deg": state["deg"],
            "nudges": state["nudges"], "refills": state.get("refills", 0),
            "t_s": clock.t, "err_mg": 1000.0 * (plant.pan - target),
            "doser": doser, "plant": plant}


# ---------------------------------------------------------------------------

def test_disabled_is_the_stock_endgame():
    for off in ({"refill_enabled": False}, {"refill_deg": 0.0}):
        for seed in (1, 2, 3):
            kw = {"seed": seed, "tip_g": 0.002 * seed}
            a = endgame(TrickleTapDoser, kw)
            b = endgame(RefillTapDoser, kw, p_over=off)
            same = all(a[k] == b[k] for k in ("grams", "status", "cycles",
                                              "taps", "deg", "nudges"))
            check("{} seed {}: identical to the stock endgame ({} cycles, "
                  "{} nudges, {})".format(off, seed, a["cycles"],
                                          a["nudges"], a["status"]), same)
            check("{} seed {}: no refills".format(off, seed),
                  b["refills"] == 0 and not b["doser"].refill_events)


def test_drained_tip_finishes_faster_with_refills():
    kw = {"seed": 11, "tip_g": 0.003}
    a = endgame(TrickleTapDoser, kw, short_g=0.050)
    b = endgame(RefillTapDoser, kw, short_g=0.050)
    print("    stock : {} in {:.0f} s, {} taps, {} nudges, {:+.1f} mg".format(
        a["status"], a["t_s"], a["taps"], a["nudges"], a["err_mg"]))
    print("    refill: {} in {:.0f} s, {} taps, {} refills, {:+.1f} mg".format(
        b["status"], b["t_s"], b["taps"], b["refills"], b["err_mg"]))
    check("refill endgame ends ok and inside tolerance",
          b["status"] is None and abs(b["err_mg"]) <= 1000.0 * TOL)
    check("refills happened", b["refills"] > 0)
    check("at most half the stock endgame's time",
          b["t_s"] <= 0.5 * a["t_s"])


def test_no_refill_inside_the_floor():
    b = endgame(RefillTapDoser, {"seed": 4, "tip_g": 0.003}, short_g=0.060)
    floor = b["doser"].p["refill_min_to_go_g"]
    ev = b["doser"].refill_events
    check("every refill had >= refill_min_to_go_g still needed ({} "
          "refills)".format(len(ev)),
          ev and all(e["need_g"] >= floor for e in ev))
    c = endgame(RefillTapDoser, {"seed": 4, "tip_g": 0.0}, short_g=0.020)
    check("starting inside the floor: no refills, stock nudges only "
          "({} nudges)".format(c["nudges"]),
          c["refills"] == 0 and c["nudges"] > 0)


def test_refills_wait_for_tap_evidence():
    p_over = {"refill_min_taps": 3}
    b = endgame(RefillTapDoser, {"seed": 5, "tip_g": 0.0, "ff_rest": 0.05},
                short_g=0.080, p_over=p_over)
    ev = b["doser"].refill_events
    gaps = [e["after_tap"] - prev for prev, e in
            zip([0] + [x["after_tap"] for x in ev], ev)]
    check("{} refills, each after >= 3 taps since the last (gaps {})".format(
        len(ev), gaps), len(ev) >= 2 and min(gaps) >= 3)


def test_refill_budget():
    b = endgame(RefillTapDoser, {"seed": 6, "tip_g": 0.0, "ff_rest": 0.02},
                short_g=0.080, p_over={"refill_max": 3})
    check("refill_max 3 -> exactly 3 refills ({})".format(b["refills"]),
          b["refills"] == 3)


def test_worst_refill_guard():
    # Every refill also drops a 30 mg slug: after the first, no refill
    # may run with 30 mg or less of room to the band's upper edge.
    b = endgame(RefillTapDoser, {"seed": 7, "tip_g": 0.0, "slug_p": 1.0,
                                 "slug_g": 0.030}, short_g=0.120)
    ev = b["doser"].refill_events
    worst, ok = 0.0, True
    for e in ev:
        room = 0.5 + TOL - e["mass_before_g"]
        if worst > 0.0 and room <= worst:
            ok = False
        worst = max(worst, e["delivered_g"])
    print("    {} refills, delivered {} mg; final {:+.1f} mg ({})".format(
        len(ev), [round(1000 * e["delivered_g"], 1) for e in ev],
        b["err_mg"], b["status"]))
    check("no refill with room <= the worst refill seen", ok and len(ev) >= 1)
    check("slug plant still does not overshoot",
          b["status"] != m3.DoseResult.OVERSHOOT
          and b["err_mg"] <= 1000.0 * TOL)


def test_full_dose_and_result_line():
    lines = []
    plant = tt.Plant(seed=3)
    doser, tap, clock = make(RefillTapDoser, plant, log=lines.append)
    res = doser.dose(0.5)
    check("full dose through bulk/trickle/refill-tap ok ({!r})".format(res),
          res.ok)
    rows = list(doser.telemetry)
    width = len(tt.TELEMETRY_HEADER.split(","))
    check("telemetry rows keep the {}-column layout".format(width),
          rows and all(len(r.split(",")) == width for r in rows))
    if hasattr(TrickleTapDoser, "_emit_result"):      # PR #166 build
        doc = doser.last_result
        n_res = sum(1 for ln in lines if str(ln).startswith("RESULT "))
        check("exactly one RESULT line ({})".format(n_res), n_res == 1)
        check("RESULT fw is tagged {}".format(FIRMWARE_ID),
              doc is not None and doc["fw"] == FIRMWARE_ID)
        check("RESULT carries the refill section",
              doc is not None and "refill" in doc
              and doc["refill"]["params"]["refill_deg"]
              == doser.p["refill_deg"])
    else:
        print("    (PR #154 build: no RESULT line to check)")


def test_refill_rows_in_telemetry():
    plant = TipPlant(seed=8, tip_g=0.0)
    doser, tap, clock = make(RefillTapDoser, plant,
                             p_over={"bulk_enabled": False})
    # start the dose right at the tap stage: trickle cut immediately
    doser.p["cutoff_margin_g"] = 0.060
    res = doser.dose(0.080)
    phases = [r.split(",")[1] for r in doser.telemetry]
    check("refill rows labelled 'refill' in the CSV ({} of them, {} "
          "refills)".format(phases.count("refill"),
                            len(doser.refill_events)),
          phases.count("refill") == len(doser.refill_events) > 0)
    check("dose ends ok ({!r})".format(res), res.ok)


def test_runner_module_imports_and_routes():
    import main_trickle_refill as mtr
    plant = TipPlant(seed=9)
    doser, tap, clock = make(RefillTapDoser, plant)
    rig = object.__new__(mtr.RefillRig)
    rig.doser = doser
    rig.handle("set refill_deg 15")
    check("set refill_deg reaches the endgame", doser.p["refill_deg"] == 15.0)
    rig.handle("refills")
    check("help lists the refills command", "refills" in mtr.HELP)


def test_ab_summary():
    """Seeded A/B over drained-tip starts 30-80 mg short (logic demo)."""
    rows = {"stock": [], "refill": []}
    for seed in range(30):
        import random
        rng = random.Random(seed)
        kw = {"seed": seed, "tip_g": rng.uniform(0.0, 0.010),
              "tap_frac": rng.uniform(0.04, 0.09),
              "ff_rest": rng.uniform(0.10, 0.40),
              "direct_frac": rng.uniform(0.2, 0.6)}
        short = rng.uniform(0.030, 0.080)
        rows["stock"].append(endgame(TrickleTapDoser, kw, short_g=short))
        rows["refill"].append(endgame(RefillTapDoser, kw, short_g=short))
    print("    {:7s} {:>6s} {:>6s} {:>9s} {:>7s} {:>8s} {:>9s}".format(
        "", "ok", "over", "median s", "p90 s", "taps", "refills"))
    for name, rs in rows.items():
        ok = sum(1 for r in rs if r["status"] is None
                 and abs(r["err_mg"]) <= 1000.0 * TOL)
        over = sum(1 for r in rs if r["err_mg"] > 1000.0 * TOL)
        ts = sorted(r["t_s"] for r in rs)
        print("    {:7s} {:>6d} {:>6d} {:>9.0f} {:>7.0f} {:>8.0f} {:>9.1f}"
              .format(name, ok, over, statistics.median(ts),
                      ts[int(0.9 * len(ts))],
                      statistics.median(r["taps"] for r in rs),
                      statistics.mean(r["refills"] for r in rs)))
    over = sum(1 for r in rows["refill"] if r["err_mg"] > 1000.0 * TOL)
    check("refill endgame: no overshoot over 30 seeded starts", over == 0)
    check("refill endgame: median time below the stock endgame's",
          statistics.median(r["t_s"] for r in rows["refill"])
          < statistics.median(r["t_s"] for r in rows["stock"]))


def main():
    for fn in (test_disabled_is_the_stock_endgame,
               test_drained_tip_finishes_faster_with_refills,
               test_no_refill_inside_the_floor,
               test_refills_wait_for_tap_evidence,
               test_refill_budget,
               test_worst_refill_guard,
               test_full_dose_and_result_line,
               test_refill_rows_in_telemetry,
               test_runner_module_imports_and_routes,
               test_ab_summary):
        print(fn.__name__)
        fn()
    if tt._FAILURES:
        print("\n{} check(s) FAILED: {}".format(
            len(tt._FAILURES), "; ".join(tt._FAILURES)))
        return 1
    print("\nall refill-tap checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
