"""What every SOP runner shares: devices, prompts, waits, the run log."""

import os
import sys
import time

from .. import devices
from ..analysis.common import check  # noqa: F401  (re-exported for the runners)
from ..runlog import RunLogger


class Context:
    """Devices and bookkeeping for one run. In --sim everything is simulated
    on one fake clock; otherwise the doser is reached through the bridge and
    the accessory over USB."""

    def __init__(self, test, args, needs_accessory=False, profile=None):
        self.test = test
        self.args = args
        self.sim = bool(args.sim)
        self.yes = bool(args.yes or args.sim)
        self.world = None
        self.acc = None
        self.cams = {}
        if self.sim:
            from ..sim import SimWorld
            self.world = SimWorld(args.jar, seed=args.seed)
            self.doser = devices.LocalDoser(self.world, self.world)
            self.acc = devices.SimAccessoryClient(self.world, profile=profile, seed=args.seed)
        else:
            host, _, port = args.doser.partition(":")
            self.doser = devices.DoserClient(host or "127.0.0.1", int(port or 8765))
            try:
                self.acc = devices.AccessoryClient(args.accessory)
            except Exception as exc:  # noqa: BLE001
                if needs_accessory:
                    raise devices.DeviceError("accessory Pico not reachable on {}: {}".format(args.accessory, exc))
                print("[bench] no accessory ({}); RH/T will not be logged".format(exc))
            if self.acc is not None and profile is not None:
                self.acc.call("motor {}".format(profile))
        params = {k: v for k, v in vars(args).items() if isinstance(v, (str, int, float, bool, type(None)))}
        self.log = RunLogger(args.out, test, args.jar, args.operator, params, self.sim, args.note,
                             clock=self.now)
        print("[bench] run folder: {}".format(self.log.dir))

    # -- time ------------------------------------------------------------------
    def now(self):
        return self.world.now() if self.world is not None else time.time()

    def sleep(self, seconds):
        if self.world is not None:
            self.world.advance(seconds)
        else:
            time.sleep(seconds)

    # -- people ------------------------------------------------------------------
    def say(self, text):
        print("[{}] {}".format(self.test, text))
        self.log.event("say", text=text)

    def prompt(self, text, action=None, **kw):
        """Ask the operator to do something. In --sim/--yes the simulated
        operator does it (world.operator(action))."""
        self.log.event("prompt", text=text, action=action)
        if self.yes:
            print("[{}] (operator) {}".format(self.test, text))
        else:
            input("[{}] {}  -- press Enter when done ".format(self.test, text))
        if self.world is not None and action:
            self.world.operator(action, **kw)

    def ask_number(self, text, default):
        if self.yes:
            return default
        s = input("[{}] {} [{}]: ".format(self.test, text, default)).strip()
        return float(s) if s else default

    # -- devices --------------------------------------------------------------------
    def camera(self, name="silhouette"):
        if name not in self.cams:
            if self.world is not None:
                self.cams[name] = devices.SimCamera(self.world, name)
            elif getattr(self.args, "images", None):
                self.cams[name] = devices.FileCamera(self.args.images)
            else:
                index = {"silhouette": 0, "drum": 0, "microscope": 1, "micrometer": 1}.get(name, 0)
                # the drum's 10 fps needs a reduced frame (full-size stills are slower)
                size = (1536, 864) if name == "drum" else (4608, 2592) if index == 0 else (4056, 3040)
                self.cams[name] = devices.PiCamera(index, size=size)
        return self.cams[name]

    def env(self, label):
        """Bench RH and T from the accessory's SHT45 into the manifest."""
        if self.acc is None:
            self.log.env(label, None, None, "not available")
            return None
        try:
            r = self.acc.call("env")
        except devices.DeviceError as exc:
            self.log.env(label, None, None, "error: {}".format(exc))
            return None
        self.log.env(label, round(r["t_c"], 2), round(r["rh"], 1))
        return r["t_c"], r["rh"]

    def weigh(self, stable=True):
        if stable:
            return self.doser.weigh_stable(sleep=self.sleep)
        return self.doser.weigh()[0]

    def set_rpm(self, rpm, required=False):
        if rpm is None:
            return None
        ok = self.doser.set_rpm(rpm)
        if not ok:
            msg = ("the doser firmware has no 'rpm' command (apply software/doser_patches/"
                   "0001-rpm-command.patch); using its default speed")
            if required:
                raise devices.DeviceError(msg)
            self.say(msg)
        self.log.event("rpm", rpm=rpm, supported=ok)
        return ok

    def estop(self):
        for fn in (lambda: self.acc and self.acc.call("estop", check=False),
                   lambda: self.doser.estop()):
            try:
                fn()
            except Exception:  # noqa: BLE001 - best effort on the way out
                pass

    def finish(self, results, checks):
        self.env("end")
        out = self.log.finish(results, checks)
        for c in self.cams.values():
            c.close()
        if self.acc is not None:
            self.acc.close()
        n_pass = sum(1 for c in checks if c["pass"])
        print("[{}] done: {} of {} checks pass; results in {}".format(
            self.test, n_pass, len(checks), os.path.join(self.log.dir, "results.json")))
        return out


def floats(text):
    return [float(x) for x in str(text).split(",") if x.strip()]


def ints(text):
    return [int(float(x)) for x in str(text).split(",") if x.strip()]


def eprint(*a):
    print(*a, file=sys.stderr)


def ev_time(e):
    """Event time in host seconds: the reader thread's receive stamp on the
    bench, the device clock in --sim (which is the world clock)."""
    return e["t_host"] if "t_host" in e else e["t"] / 1000.0


def dose_to(ctx, target_g, tol_g=0.05, max_revs=200, frac=0.8, settle_s=1.0, on_step=None):
    """Turn the auger until the balance reads target_g (within tol_g): one
    revolution first, then steps of frac x the remainder at the measured
    g/rev (0.1 to 10 revolutions). Returns (grams, revolutions)."""
    g = ctx.weigh()
    gpr = None
    revs = 0.0
    while target_g - g > tol_g and revs < max_revs:
        step = 1.0 if gpr is None else min(10.0, max(0.1, frac * (target_g - g) / gpr))
        ctx.doser.rotate(360.0 * step)
        revs += step
        ctx.sleep(settle_s)
        g_new = ctx.weigh()
        if g_new - g > 1e-4:
            r = (g_new - g) / step
            gpr = r if gpr is None else 0.5 * (gpr + r)
        g = g_new
        if on_step is not None and on_step(g):
            break
    return g, revs
