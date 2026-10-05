"""Frame-by-frame timeline for the dose-procedure animation.

The animation replays one real dose: ``bo-005`` of the salt campaign
``salt-20260929T014732Z`` (0.5 g target, 99.7 s, 2.4 mg under), the point
the campaign recommends.  Its trial record gives the time of every stage,
the auger speed the PI controller commanded at each trickle poll, the
balance reading after every tap cycle, and the parameters the dose ran with.

Each stage plays at its own speed, so the 73 s tap stage doesn't take over
the clip (the multiplier is in ``timeline_overlay.json`` for the ``xN``
corner label):

| stage              | real time (s) | speed |
|--------------------|---------------|-------|
| tare, tilt to 40 deg | 0-4.0        | x5    |
| bulk               | 4.0-9.2       | x1    |
| tilt 40 -> 10 deg  | 9.2-12.8      | x4    |
| trickle            | 12.8-23.1     | x2    |
| tilt 10 -> 15 deg  | 23.1-24.4     | x2.7  |
| taps 1-8           | 24.4-47.4     | x6    |
| taps 9-24, settle  | 47.4-99.7     | x30   |

What is drawn at real speed and what isn't:
- The tilt angles, the stage order, the auger speeds (100 rpm in bulk, the
  logged 2-15 rpm in trickle) and the tap times are the dose's own, scaled
  by the stage's speed.  Fast spinning is motion-blurred (up to 8 renders
  averaged per frame) instead of strobing.
- A tap's plunger stroke is drawn over 0.15 s whatever the speed, so it
  can be seen (the real pulse is 60 ms).
- Grains are 0.5 mg each, emitted so the cup fills the way the balance did.
- The tilt-up at the start and the return to 0 deg at the end are added
  for the clip; on the rig the plate stays at the last tilt between doses.

    python3 make_timeline.py      # -> timeline.json, timeline_overlay.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CAMPAIGN = REPO / "data/opt/salt-20260929T014732Z"
TRIAL = CAMPAIGN / "zero/trial_d48311a0-aa27-43f1-a6fc-4227efdfee69.json"   # bo-005
FPS = 30
GRAIN_G = 0.0005            # mass of one drawn grain
MAX_BLUR = 8                # renders averaged per frame, at most
BLUR_DEG = 2.5              # one blur sub-frame per this many degrees of auger turn
AUGER_SIGN = -1.0           # the dispensing direction, as in cad/full-assembly/video.py
TAP_DRAW_S = 0.15           # a tap's plunger stroke as drawn
TAP_PROFILE = [(0.0, 0.0), (0.04, 1.0), (0.07, 1.0), (0.15, 0.0)]   # (s, share of stroke)
FALL_LEAD_S = 0.45          # grains leave the outlet this long before the balance sees them


def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def load():
    d = json.load(open(TRIAL))
    cols = d["telemetry"]["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in d["telemetry"]["rows"]]
    f = lambda r, k: float(r[k]) if r.get(k) not in (None, "") else None   # noqa: E731
    tel = [dict(t=f(r, "t_s"), phase=r["phase"], z=f(r, "z_g"), rpm=f(r, "rpm_cmd")) for r in rows]
    return d, tel


def build():
    d, tel = load()
    p = d["parameters_executed"]
    bulk_tilt, trickle_tilt, tap_tilt = p["bulk_tilt_deg"], p["trickle_tilt_deg"], p["tap_tilt_deg"]
    bulk_rpm = p["bulk_rpm"]
    t_tot = d["outcomes"]["t_total_s"]
    final_g = d["outcomes"]["settled_final_g"]

    # --- real-time events, from the log --------------------------------------------------- #
    bulk_on, bulk_off = 4.0, 6.31          # "poll 1 ... elapsed 4.0 s"; halted at the 6.31 s poll
    bulk_end = 9.17                        # settled reading
    trickle_rows = [r for r in tel if r["phase"] == "trickle"]
    tr_on = trickle_rows[0]["t"]           # 12.81
    tr_off = d["stop_events"][1]["t_stop_s"]   # 20.66, predictive cutoff
    tr_end = [r for r in tel if r["phase"] == "trickle_end"][0]["t"]   # 23.05
    tap_rows = [r for r in tel if r["phase"] == "tap"]
    tap_times = [r["t"] - 1.6 for r in tap_rows]   # each cycle: tap, 1.5 s settle, read
    tap_gain = np.diff([tr_end_z := [r for r in tel if r["phase"] == "trickle_end"][0]["z"]]
                       + [r["z"] for r in tap_rows])
    tilt_tap_on = tap_times[0] - 0.2

    # balance trace (real time, g): readings, 0 before the first one
    trace_t = [0.0, bulk_on] + [r["t"] for r in tel] + [t_tot]
    trace_m = [0.0, 0.0] + [r["z"] for r in tel] + [final_g]

    # trickle rpm, held between polls
    tr_t = [r["t"] for r in trickle_rows]
    tr_rpm = [r["rpm"] or 0.0 for r in trickle_rows]

    def auger_rpm(R):
        if bulk_on <= R < bulk_off:
            return bulk_rpm * min(1.0, (R - bulk_on) / 0.15)
        if tr_on <= R < tr_off:
            i = max(0, np.searchsorted(tr_t, R, side="right") - 1)
            return tr_rpm[i]
        return 0.0

    def bulk_tap_on(R):        # cadence taps, 60 ms per 500 ms, while the auger turns in bulk
        return bulk_on <= R < bulk_off and ((R - bulk_on) % 0.5) < 0.06

    # emission (g/s, real time): the balance's gain moved earlier by the fall + lag
    def emit_rate(R):
        Rb = R + FALL_LEAD_S
        if Rb > tr_end + 0.6 or R < bulk_on:
            return 0.0
        dm = np.interp(Rb + 0.05, trace_t, trace_m) - np.interp(Rb - 0.05, trace_t, trace_m)
        return max(dm / 0.1, 0.0)

    # --- output segments: (name, real start, real end, output seconds, tilt fn) ---------- #
    def hold(a):
        return lambda u: a

    def move(a, b):
        return lambda u: a + (b - a) * ease(u)

    segs = [
        ("rest", 0.0, 0.0, 1.0, hold(0.0), "Ready"),
        ("tare", 0.0, bulk_on, 0.8, move(0.0, bulk_tilt), "Bulk"),
        ("bulk", bulk_on, bulk_end, bulk_end - bulk_on, hold(bulk_tilt), "Bulk"),
        ("tilt1", bulk_end, tr_on, 0.9, move(bulk_tilt, trickle_tilt), "Trickle"),
        ("trickle", tr_on, tr_end, (tr_end - tr_on) / 2, hold(trickle_tilt), "Trickle"),
        ("tilt2", tr_end, tilt_tap_on, 0.5, move(trickle_tilt, tap_tilt), "Taps"),
        ("taps1", tilt_tap_on, 47.4, (47.4 - tilt_tap_on) / 6, hold(tap_tilt), "Taps"),
        ("taps2", 47.4, t_tot, (t_tot - 47.4) / 30, hold(tap_tilt), "Taps"),
        ("home", t_tot, t_tot, 0.8, move(tap_tilt, 0.0), "Done"),
        ("end", t_tot, t_tot, 1.5, hold(0.0), "Done"),
    ]

    frames, overlay = [], []
    auger = 0.0
    carry = 0.0
    puffs_done = set()
    t_out = 0.0
    tap_draw = []                     # output times at which a drawn tap starts
    for name, r0, r1, dur, tilt_fn, stage in segs:
        n = round(dur * FPS)
        speed = (r1 - r0) / dur if r1 > r0 else 0.0
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            R0, R1 = r0 + (r1 - r0) * u0, r0 + (r1 - r0) * u1
            # auger: integrate rpm over the real interval of this frame
            sub_R = np.linspace(R0, R1, 9)
            dang = sum(auger_rpm(0.5 * (a + b)) * 6.0 * (b - a) for a, b in zip(sub_R[:-1], sub_R[1:]))
            nsub = int(min(MAX_BLUR, max(1, np.ceil(abs(dang) / BLUR_DEG))))
            angs = [auger + AUGER_SIGN * dang * (k + 0.5) / nsub for k in range(nsub)]
            auger += AUGER_SIGN * dang
            # taps: bulk cadence taps (real speed in bulk) and tap-stage taps (drawn at TAP_DRAW_S)
            taps = []
            for k in range(nsub):
                Rk = R0 + (R1 - R0) * (k + 0.5) / nsub
                taps.append(1.0 if (name == "bulk" and bulk_tap_on(Rk)) else 0.0)
            puff = 0
            for j, tt in enumerate(tap_times):
                if R0 <= tt < R1 and j not in puffs_done:
                    puffs_done.add(j)
                    tap_draw.append(t_out + (tt - R0) / max(speed, 1e-9) / 1.0 if speed else t_out)
                    puff = max(1, int(round(tap_gain[j] / GRAIN_G)))
            for start in tap_draw:
                for k in range(nsub):
                    tk = t_out + (k + 0.5) / nsub / FPS - start
                    if 0.0 <= tk <= TAP_DRAW_S:
                        taps[k] = max(taps[k], float(np.interp(tk, *zip(*TAP_PROFILE))))
            # emission
            g = sum(emit_rate(0.5 * (a + b)) * (b - a) for a, b in zip(sub_R[:-1], sub_R[1:]))
            if name in ("taps1", "taps2"):
                g = 0.0                                   # tap-stage powder leaves as puffs
            carry += g / GRAIN_G
            emit = float(carry)
            carry = 0.0
            frames.append(dict(t=round(t_out, 4), tilt=round(float(tilt_fn((i + 1) / n)), 3),
                               auger=[round(a, 3) for a in angs], tap=[round(x, 3) for x in taps],
                               emit=round(emit, 3), puff=puff, stage=name))
            Rm = 0.5 * (R0 + R1)
            overlay.append(dict(t=round(t_out, 4), real_s=round(R1, 3), stage=stage, seg=name,
                                speed=round(speed, 2),
                                mass_g=round(float(np.interp(R1, trace_t, trace_m)), 5),
                                rpm=round(auger_rpm(Rm), 2), tilt=frames[-1]["tilt"],
                                tapping=bool(max(taps) > 0)))
            t_out += 1.0 / FPS
    meta = dict(source=str(TRIAL.relative_to(REPO)), label="bo-005", fps=FPS, grain_g=GRAIN_G,
                params=d["parameters"], outcomes=d["outcomes"], tap_times_real=tap_times,
                trace_t=trace_t, trace_m=trace_m, n_frames=len(frames))
    return frames, overlay, meta


def main():
    frames, overlay, meta = build()
    (HERE / "timeline.json").write_text(json.dumps(dict(fps=FPS, frames=frames)))
    (HERE / "timeline_overlay.json").write_text(json.dumps(dict(meta=meta, frames=overlay)))
    n_emit = sum(f["emit"] for f in frames) + sum(f["puff"] for f in frames)
    print(f"{len(frames)} frames ({len(frames) / FPS:.1f} s), {n_emit:.0f} grains, "
          f"{sum(len(f['auger']) for f in frames)} renders")


if __name__ == "__main__":
    main()
