"""Line protocol of the accessory Pico: one command per line in, one JSON
object per line out.

Request:  ``<cmd> [args...] [key=value ...] [#<id>]``
          e.g. ``table 30 rate=0.5 stream=20 #17``
Reply:    ``{"ok": true, "cmd": "table", "id": 17, "t": <device ms>, ...}``
Error:    ``{"ok": false, "cmd": "table", "err": "..."}``
Event:    ``{"ev": "imu", "t": <device ms>, ...}`` (streams, task completion)

CPython-importable; the tests exercise it directly.
"""

try:
    import ujson as json
except ImportError:
    import json


class ProtocolError(Exception):
    pass


# name -> (usage, what it does). Order is the order `help` lists them.
COMMANDS = (
    ("ping", "ping", "liveness check"),
    ("help", "help", "this list"),
    ("status", "status", "devices, positions, tasks, calibration"),
    ("estop", "estop | !", "stop every task, de-energise the stepper, tapper off, relay closed"),
    ("stop", "stop [task|all]", "end a task or stream (all by default)"),
    ("gate", "gate open|close|<servo deg> [speed=deg/s]", "orifice gate, servo A, eased ramp"),
    ("servo", "servo a|b <servo deg> [speed=deg/s]", "raw servo move, eased ramp"),
    ("table", "table <deg> [rate=deg/s] [stream=Hz] [halt=g] | table stop",
     "tilt table (table deg = servo B deg / 2), constant-rate ramp, IMU stream, optional halt on jolt"),
    ("imu", "imu [n=N] | imu zero | imu stream <Hz> [s=sec]", "plate angle from gravity, raw axes"),
    ("motor", "motor [cam|stage]", "show or select the stepper profile (idle only)"),
    ("cam", "cam home | cam taps <n> [rate=taps/min]", "cam-drop tapper, 2 lobes: 1 turn = 2 taps"),
    ("stage", "stage home|pos|off|stop | stage move|rel <mm> [speed=mm/s] | stage speed <mm/s>",
     "100 mm linear stage, 0.005 mm per microstep"),
    ("tap", "tap <n> [rate=taps/min] [on=ms]", "orifice-cup solenoid (DRV8871 #2)"),
    ("lc", "lc read|tare [n=N] | lc cal <grams> [n=N] | lc rate <sps> | lc stream <Hz> [s=sec]",
     "NAU7802 load cell"),
    ("env", "env | env stream <Hz> [s=sec]", "SHT45 temperature and RH"),
    ("q", "q zero [ms=] | q short | q read [n=N] | q gain <fsr V> | q cf <nF> | q stream <Hz> [s=sec]",
     "charge amplifier: reed-relay reset, ADS1115 AIN0-AIN1"),
    ("light", "light on|off|<0-100>", "backlight PWM"),
    ("i2c", "i2c", "scan the I2C bus"),
    ("cal", "cal [show|save|clear]", "calibration file on the Pico's flash"),
)

COMMAND_NAMES = tuple(c[0] for c in COMMANDS)
ALIASES = {"!": "estop", "?": "help", "h": "help", "s": "status"}


def parse_line(line):
    """Split a command line into (cmd, args, kwargs, req_id).

    Tokens of the form key=value go to kwargs; a token ``#<int>`` is the
    request id echoed in the reply; everything else is positional. The
    command and positional words are lower-cased.
    """
    if isinstance(line, bytes):
        line = line.decode()
    toks = line.strip().split()
    if not toks:
        return None, [], {}, None
    cmd = toks[0].lower()
    cmd = ALIASES.get(cmd, cmd)
    args = []
    kw = {}
    req_id = None
    for tok in toks[1:]:
        if tok.startswith("#") and len(tok) > 1:
            try:
                req_id = int(tok[1:])
                continue
            except ValueError:
                raise ProtocolError("bad request id {}".format(tok))
        if "=" in tok:
            k, _, v = tok.partition("=")
            if not k or not v:
                raise ProtocolError("bad key=value {}".format(tok))
            kw[k.lower()] = v
        else:
            args.append(tok.lower())
    return cmd, args, kw, req_id


def num(value, name, lo=None, hi=None, default=None):
    """Parse a number and check its range; ``None`` gives the default."""
    if value is None:
        if default is None:
            raise ProtocolError("missing {}".format(name))
        return default
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ProtocolError("{} must be a number, not {}".format(name, value))
    if x != x or x in (float("inf"), float("-inf")):
        raise ProtocolError("{} must be finite".format(name))
    if lo is not None and x < lo:
        raise ProtocolError("{} = {} is below {}".format(name, value, lo))
    if hi is not None and x > hi:
        raise ProtocolError("{} = {} is above {}".format(name, value, hi))
    return x


def integer(value, name, lo=None, hi=None, default=None):
    x = num(value, name, lo, hi, default)
    if int(x) != x:
        raise ProtocolError("{} must be a whole number".format(name))
    return int(x)


def arg(args, i, name=None, default=None):
    if i < len(args):
        return args[i]
    if default is None and name is not None:
        raise ProtocolError("missing {}".format(name))
    return default


def _clean(v):
    if isinstance(v, float):
        if v != v:
            return None
        return round(v, 5)
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if isinstance(v, dict):
        return {k: _clean(x) for k, x in v.items()}
    return v


def reply(cmd, t, ok=True, req_id=None, **values):
    d = {"ok": ok, "cmd": cmd, "t": t}
    if req_id is not None:
        d["id"] = req_id
    for k, v in values.items():
        d[k] = _clean(v)
    return d


def error(cmd, t, msg, req_id=None):
    return reply(cmd, t, ok=False, req_id=req_id, err=str(msg))


def event(ev, t, **values):
    d = {"ev": ev, "t": t}
    for k, v in values.items():
        d[k] = _clean(v)
    return d


def dumps(obj):
    return json.dumps(obj)


def loads(line):
    return json.loads(line)


def help_list():
    return [{"cmd": name, "usage": usage, "does": what}
            for name, usage, what in COMMANDS]
