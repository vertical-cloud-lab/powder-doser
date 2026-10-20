#!/usr/bin/env python3
"""Issue #186 helper: talk to the trickle_tap runner through the
executor's own serial session class (same port lock, same raw log
format), without dosing.

    rig_cmd.py --log PATH [--takeover] CMD [CMD ...]

CMD is one of
  w            one scale read
  wst          read until 3 consecutive ST reads agree within 0.3 mg
  a<deg>       plate angle (blocking smooth move), e.g. a45
  wait<s>      pause, e.g. wait5
  rot<deg>     the runner's signed 'r <deg>' (auger degrees; negative =
               reverse), e.g. rot-180, then one scale read
  tap<n>       n x the runner's 't' (3 solenoid taps each), then one
               scale read
  dose:<g>:<tol_g>  reverse-rotation steps at the current plate angle
               until a stable read is within tol_g below <g> (the
               balance reading, not the cup total); see stepwise_dose
  handback     ctrl-C the runner and soft-reboot into the power-on main.py
  s            the runner's state listing
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/powder-doser/scripts"))
import opt_dose_capture as odc                               # noqa: E402

RUNNER_RPM = 60.0       # config.STEPPER_SPEED_RPM: what 'r' runs at after boot


def read_scale(sess, timeout_s=6):
    sess.send("w")
    line, _ = sess.collect_until(lambda l: l.startswith("[scale]"),
                                 timeout_s)
    print(line, flush=True)
    if not line:
        return None, None
    parts = line.split()
    try:
        return parts[1], float(parts[2])
    except (IndexError, ValueError):
        return parts[1] if len(parts) > 1 else None, None


def read_stable(sess, n_agree=3, tol_g=0.0003, max_reads=20):
    hist = []
    for _ in range(max_reads):
        st, g = read_scale(sess)
        if st == "ST" and g is not None:
            hist.append(g)
            if (len(hist) >= n_agree
                    and max(hist[-n_agree:]) - min(hist[-n_agree:]) <= tol_g):
                print("STABLE {:.4f}".format(hist[-1]), flush=True)
                return hist[-1]
        else:
            hist = []
        time.sleep(0.5)
    print("UNSTABLE", flush=True)
    return None


def stepwise_dose(sess, target_g, tol_g, fine_g=0.15, worst_g_per_deg=4e-4,
                  max_steps=300, stall_steps=20):
    """Dose by reverse auger steps with a stable read after each.

    Half turns while more than ``fine_g`` remains; then each step is
    sized so that, at the steepest flow seen so far (seeded above the
    10-20 A/B test's 62.5 mg per half turn), it adds at most half of
    what remains, so no single step can overshoot.  A step that adds
    under 2 mg is followed by a tap burst; ``stall_steps`` steps in a
    row adding under 5 mg in all stop the dose.
    """
    g = read_stable(sess)
    if g is None:
        print("DOSE abort: no stable read", flush=True)
        return None
    worst = worst_g_per_deg
    slow = []
    for i in range(max_steps):
        rem = target_g - g
        if rem <= tol_g:
            print("DOSE done {:.4f} g ({:+.1f} mg vs {:.4f} g)".format(
                g, (g - target_g) * 1e3, target_g), flush=True)
            return g
        if rem > fine_g:
            deg = 180.0
        else:
            deg = max(5.0, min(90.0, 0.5 * rem / worst))
        sess.send("r {:.1f}".format(-deg))
        read_scale(sess, deg / 360.0 * 60.0 / RUNNER_RPM + 8.0)
        g2 = read_stable(sess)
        if g2 is None:
            print("DOSE abort: no stable read after step", flush=True)
            return None
        added = g2 - g
        worst = max(worst, added / deg)
        print("DOSE step {} -{:.1f} deg: {:.4f} -> {:.4f} g ({:+.1f} mg)"
              .format(i, deg, g, g2, added * 1e3), flush=True)
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
    ap.add_argument("--takeover", action="store_true")
    ap.add_argument("cmds", nargs="+")
    args = ap.parse_args()
    sess = odc.PicoSession(args.port, 115200, args.log)
    try:
        if args.cmds != ["handback"]:
            sess.raw.write("--- rig_cmd {} ---\n".format(" ".join(args.cmds)))
            odc.ensure_runner(sess, takeover=args.takeover)
            sess.drain()
        for cmd in args.cmds:
            if cmd == "w":
                read_scale(sess)
            elif cmd == "wst":
                read_stable(sess)
            elif cmd.startswith("climb"):
                # climb:<from>:<to>:<step>:<guard_g> -- step the plate up,
                # stable read at each angle; on a jump over guard_g from
                # the first angle's reading, step back one and stop.
                lo, hi, step, guard = [float(x) for x in cmd.split(":")[1:]]
                ang, ref, prev = lo, None, lo
                while ang <= hi + 1e-6:
                    sess.send("a {}".format(ang))
                    sess.drain(quiet_s=0.5, max_s=4.0)
                    time.sleep(1.0)
                    g = read_stable(sess)
                    print("CLIMB {:.1f} deg -> {}".format(ang, g), flush=True)
                    if ref is None:
                        ref = g
                    elif g is None or ref is None or abs(g - ref) > guard:
                        print("GUARD: {} vs {} at {:.1f} deg; back to "
                              "{:.1f}".format(g, ref, ang, prev), flush=True)
                        sess.send("a {}".format(prev))
                        sess.drain(quiet_s=0.5, max_s=4.0)
                        time.sleep(1.0)
                        print("CLIMB back {:.1f} deg -> {}".format(
                            prev, read_stable(sess)), flush=True)
                        break
                    prev = ang
                    ang += step
            elif cmd.startswith("rot"):
                # 'r' blocks the runner until the move (plus its 2.2 s
                # pad) ends, so the read queued behind it marks the end.
                deg = float(cmd[3:])
                sess.send("r {}".format(deg))
                st, g = read_scale(
                    sess, abs(deg) / 360.0 * 60.0 / RUNNER_RPM + 8.0)
                print("ROT {:+.0f} deg -> {} {}".format(deg, st, g),
                      flush=True)
            elif cmd.startswith("dose:"):
                target, tol = [float(x) for x in cmd.split(":")[1:]]
                stepwise_dose(sess, target, tol)
            elif cmd.startswith("tap"):
                n = int(cmd[3:] or 1)
                for _ in range(n):
                    sess.send("t")
                st, g = read_scale(sess, 6.0 + n)
                print("TAP x{} -> {} {}".format(n, st, g), flush=True)
            elif cmd.startswith("a"):
                sess.send("a {}".format(float(cmd[1:])))
                sess.drain(quiet_s=0.5, max_s=4.0)
                print("ANGLE {}".format(float(cmd[1:])), flush=True)
            elif cmd.startswith("wait"):
                time.sleep(float(cmd[4:]))
            elif cmd == "s":
                sess.send("s")
                for line in sess.lines(6, idle_stop_s=1.0):
                    if not line.startswith("  "):
                        print(line, flush=True)
            elif cmd == "handback":
                sess.raw.write("--- handback {} ---\n".format(
                    odc.oc.utcnow_iso()))
                sess.port.write(b"\x03")
                sess.collect_until(lambda l: l.startswith(">>>"), 5)
                sess.port.write(b"\x04")
                line, seen = sess.collect_until(
                    lambda l: "ready" in l, 20)
                for l in seen:
                    print(l, flush=True)
            else:
                raise SystemExit("unknown cmd {!r}".format(cmd))
    finally:
        sess.close()


if __name__ == "__main__":
    main()
