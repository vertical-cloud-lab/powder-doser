#!/usr/bin/env python3
"""Issue #186 (2026-10-20, 15 wt% cup): clear the outlet and finish the
dose at the current plate angle with the runner's own 'r' and 't'.

    unclog_dose.py --log PATH TARGET_G TOL_G

Same method as rig_cmd.py's dose: (10-20), which finished the 7.5 wt%
cup: reverse steps with a stable read after each, and a tap burst after
any step that adds under 2 mg.  Two changes for a bigger remainder:
full turns while more than coarse_g remains and the last step fed
(flowing), and a 60-step no-flow budget so the clog phase (10-20: 25
half turns for 7 mg) doesn't abort it.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig_cmd as rc                                          # noqa: E402

odc = rc.odc


def dose(sess, target_g, tol_g, fine_g=0.15, coarse_g=0.5, worst=4e-4,
         max_steps=500, stall_steps=60):
    g = rc.read_stable(sess)
    if g is None:
        print("DOSE abort: no stable read", flush=True)
        return None
    flowing, slow = False, []
    for i in range(max_steps):
        rem = target_g - g
        if rem <= tol_g:
            print("DOSE done {:.4f} g ({:+.1f} mg vs {:.4f} g)".format(
                g, (g - target_g) * 1e3, target_g), flush=True)
            return g
        if rem > coarse_g and flowing:
            deg = 360.0
        elif rem > fine_g:
            deg = 180.0
        else:
            deg = max(5.0, min(90.0, 0.5 * rem / worst))
        sess.send("r {:.1f}".format(-deg))
        rc.read_scale(sess, deg / 360.0 * 60.0 / rc.RUNNER_RPM + 8.0)
        g2 = rc.read_stable(sess)
        if g2 is None:
            print("DOSE abort: no stable read after step", flush=True)
            return None
        added = g2 - g
        worst = max(worst, added / deg)
        flowing = added > 0.010
        print("DOSE step {} -{:.1f} deg: {:.4f} -> {:.4f} g ({:+.1f} mg) "
              "{}".format(i, deg, g, g2, added * 1e3,
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
    ap.add_argument("target_g", type=float)
    ap.add_argument("tol_g", type=float)
    args = ap.parse_args()
    sess = odc.PicoSession(args.port, 115200, args.log)
    try:
        sess.raw.write("--- unclog_dose {} {} ---\n".format(
            args.target_g, args.tol_g))
        odc.ensure_runner(sess, takeover=False)
        sess.drain()
        dose(sess, args.target_g, args.tol_g)
        time.sleep(30)
        print("FINAL", rc.read_stable(sess), time.strftime(
            "%H:%M:%S", time.gmtime()), flush=True)
    finally:
        sess.close()


if __name__ == "__main__":
    main()
