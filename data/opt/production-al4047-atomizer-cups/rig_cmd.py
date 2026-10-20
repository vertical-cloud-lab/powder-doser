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
  handback     ctrl-C the runner and soft-reboot into the power-on main.py
  s            the runner's state listing
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/powder-doser/scripts"))
import opt_dose_capture as odc                               # noqa: E402


def read_scale(sess):
    sess.send("w")
    line, _ = sess.collect_until(lambda l: l.startswith("[scale]"), 6)
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
