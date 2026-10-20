#!/usr/bin/env python3
"""Issue #186 (2026-10-20, 15 wt% cup): finish the dose with the runner's
own 'r' at the current plate angle (forward by default), with a stable
read after every step.

    topup.py --log PATH TARGET_G TOL_G [--sign 1] [--worst G_PER_DEG]

Each step is sized so that, at the steepest flow seen so far (seeded at
13 mg per turn, what forward turns gave at 25 deg after the outlet
re-packed), it adds at most half of what remains: 20-720 deg.  A step
that adds under 2 mg is followed by a tap burst; 25 steps in a row
adding under 5 mg in all stop it.  The target is the balance reading,
not the cup total.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_cmd as rc                                          # noqa: E402

odc = rc.odc


def topup(sess, target_g, tol_g, sign=1, worst=13e-3 / 360, min_deg=20.0,
          max_deg=720.0, max_steps=300, stall_steps=25):
    g = rc.read_stable(sess)
    if g is None:
        print("DOSE abort: no stable read", flush=True)
        return None
    slow = []
    for i in range(max_steps):
        rem = target_g - g
        if rem <= tol_g:
            print("DOSE done {:.4f} g ({:+.1f} mg vs {:.4f} g)".format(
                g, (g - target_g) * 1e3, target_g), flush=True)
            return g
        deg = max(min_deg, min(max_deg, 0.5 * rem / worst))
        sess.send("r {:.1f}".format(sign * deg))
        rc.read_scale(sess, deg / 360.0 * 60.0 / rc.RUNNER_RPM + 8.0)
        g2 = rc.read_stable(sess)
        if g2 is None:
            print("DOSE abort: no stable read after step", flush=True)
            return None
        added = g2 - g
        worst = max(worst, added / deg)
        print("DOSE step {} {:+.1f} deg: {:.4f} -> {:.4f} g ({:+.1f} mg) "
              "{}".format(i, sign * deg, g, g2, added * 1e3,
                          time.strftime("%H:%M:%S", time.gmtime())),
              flush=True)
        g = g2
        if g > target_g:
            print("DOSE over target: {:+.1f} mg".format(
                (g - target_g) * 1e3), flush=True)
            return g
        if added < 0.002:
            sess.send("t")
        slow = (slow + [added])[-stall_steps:]
        if len(slow) == stall_steps and sum(slow) < 0.005:
            print("DOSE abort: {} steps added {:.1f} mg".format(
                stall_steps, sum(slow) * 1e3), flush=True)
            return g
    print("DOSE abort: step budget", flush=True)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--sign", type=int, default=1, choices=(1, -1))
    ap.add_argument("--worst", type=float, default=13e-3 / 360)
    ap.add_argument("target_g", type=float)
    ap.add_argument("tol_g", type=float)
    args = ap.parse_args()
    sess = odc.PicoSession(args.port, 115200, args.log)
    try:
        sess.raw.write("--- topup {} {} ---\n".format(args.target_g,
                                                     args.tol_g))
        odc.ensure_runner(sess, takeover=False)
        sess.drain()
        topup(sess, args.target_g, args.tol_g, args.sign, args.worst)
        time.sleep(30)
        print("FINAL", rc.read_stable(sess), time.strftime(
            "%H:%M:%S", time.gmtime()), flush=True)
    finally:
        sess.close()


if __name__ == "__main__":
    main()
