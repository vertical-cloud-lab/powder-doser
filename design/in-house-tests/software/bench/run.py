"""Run one in-house test (SOP) and log it.

    python -m bench.run list
    python -m bench.run status [--sim]
    python -m bench.run heap --jar NaCl-01 --pours 3            # on the bench
    python -m bench.run heap --jar NaCl-01 --sim                # practice / test
    python -m bench.run 2 --jar NaCl-01 --cal runs/.../cylinder_cal.csv

Every run writes runs/<UTC stamp>_<test>_<jar>/ (see bench/runlog.py).
Exit code 0 when every acceptance check passes, 1 when one fails.
Ctrl-C stops the accessory (estop) and the doser (!) and marks the run aborted.
"""

import argparse
import getpass
import json
import sys

from . import devices
from .sops import TESTS, density, psd
from .sops.common import Context

PROFILE = {"density": "cam", "ucs": "stage", "spread": "stage"}
NEEDS_ACC = {"density", "plate", "orifice", "ucs", "spread", "faraday"}
EXTRA = {
    "watercal": ("Water calibration of the density cylinder (test 2)", density.add_args_watercal,
                 density.run_watercal, None),
    "psdcal": ("Stage micrometer scale for the PSD camera (test 4)", psd.add_args_cal, psd.run_cal, None),
}


def add_common(p):
    p.add_argument("--jar", required=True, help="jar id, e.g. NaCl-01")
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001
        user = "unknown"
    p.add_argument("--operator", default=user)
    p.add_argument("--sim", action="store_true", help="simulated devices and powder")
    p.add_argument("--yes", action="store_true", help="no operator prompts")
    p.add_argument("--out", default="runs", help="folder for run folders")
    p.add_argument("--doser", default="127.0.0.1:8765", help="bridge address (SSH forward)")
    p.add_argument("--accessory", default="/dev/ttyACM0", help="accessory Pico serial port")
    p.add_argument("--images", default=None, help="replay images from this folder instead of a camera")
    p.add_argument("--note", default="")
    p.add_argument("--seed", type=int, default=0, help="--sim random seed")


def build_parser():
    ap = argparse.ArgumentParser(prog="python -m bench.run", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list the tests")
    st = sub.add_parser("status", help="check the doser bridge, accessory and cameras")
    st.add_argument("--sim", action="store_true")
    st.add_argument("--doser", default="127.0.0.1:8765")
    st.add_argument("--accessory", default="/dev/ttyACM0")
    for mod in TESTS:
        p = sub.add_parser(mod.NAME, aliases=[str(mod.NUMBER)], help="{}: {}".format(mod.NUMBER, mod.TITLE))
        add_common(p)
        mod.add_args(p)
        p.set_defaults(func=mod.run, test=mod.NAME)
    for name, (title, add, fn, _) in EXTRA.items():
        p = sub.add_parser(name, help=title)
        add_common(p)
        add(p)
        p.set_defaults(func=fn, test=name)
    return ap


def status(args):
    out = {}
    if args.sim:
        from .sim import SimWorld
        w = SimWorld()
        doser = devices.LocalDoser(w, w)
        acc = devices.SimAccessoryClient(w)
    else:
        host, _, port = args.doser.partition(":")
        try:
            doser = devices.DoserClient(host, int(port or 8765))
        except OSError as exc:
            doser = None
            out["doser"] = "bridge not reachable ({}); is the SSH forward up?".format(exc)
        try:
            acc = devices.AccessoryClient(args.accessory)
        except Exception as exc:  # noqa: BLE001
            acc = None
            out["accessory"] = "not reachable ({})".format(exc)
    if doser is not None:
        out["bridge"] = doser.request(".ping") if not args.sim else {"ok": True, "pong": "sim"}
        out["doser_state"] = doser.request("s").get("lines")
        g = doser.request("w")
        out["balance"] = {k: g.get(k) for k in ("ok", "grams", "stable", "err")}
    if acc is not None:
        s = acc.call("status")
        out["accessory"] = {k: s.get(k) for k in ("fw", "devices", "motor", "relay", "cal")}
        out["i2c"] = acc.call("i2c")["found"]
        out["env"] = {k: acc.call("env").get(k) for k in ("t_c", "rh")}
    if not args.sim:
        try:
            from picamera2 import Picamera2
            out["cameras"] = Picamera2.global_camera_info()
        except Exception as exc:  # noqa: BLE001
            out["cameras"] = "picamera2 unavailable ({})".format(exc)
    print(json.dumps(out, indent=2, default=str))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "list":
        for mod in TESTS:
            print("{:>2}  {:<9} {}".format(mod.NUMBER, mod.NAME, mod.TITLE))
        for name, (title, *_rest) in EXTRA.items():
            print("    {:<9} {}".format(name, title))
        return 0
    if args.cmd == "status":
        return status(args)
    test = args.test
    ctx = Context(test, args, needs_accessory=test in NEEDS_ACC, profile=PROFILE.get(test))
    try:
        res, checks = args.func(ctx, args)
    except KeyboardInterrupt:
        ctx.estop()
        ctx.log.finish({"aborted": True}, [], status="aborted")
        print("\n[bench] aborted; accessory and doser stopped")
        return 130
    except Exception as exc:
        ctx.estop()
        ctx.log.finish({"error": repr(exc)}, [], status="error")
        raise
    out = ctx.finish(res, checks)
    for c in checks:
        print("  [{}] {}  ({})".format("pass" if c["pass"] else "FAIL", c["check"], c["value"]))
    return 0 if out["all_pass"] in (True, None) else 1


if __name__ == "__main__":
    sys.exit(main())
