"""Runtime-settable parameter overlay for the test-rig firmware.

``config.py`` holds the bench defaults, but the blank-auger vibration
sweep (issue #139) needs to change dispense parameters *thousands* of
times without re-uploading firmware.  This module provides a small
validated overlay on top of ``config``: every entry in :data:`SPEC` has a
short lower-case runtime name, the ``config`` attribute it shadows, a
coercion function and a range, so the host can do::

    set stepper_rpm 45
    set tap_count 3
    params

and get back a machine-parseable snapshot of *everything* that was
actually in force for the run that follows.  Recording that snapshot
alongside the balance trace is what makes the sweep reproducible --
"what did we actually run?" must never be an inference from a git hash.

The module deliberately imports nothing from ``machine`` (and nothing
from ``config`` at import time), so it runs unmodified under CPython and
can be unit-tested on the host::

    python -m unittest discover characterization/tests
"""

try:  # MicroPython ships ``json``; the name differs on some ports.
    import json as _json
except ImportError:  # pragma: no cover - exercised only on odd ports
    import ujson as _json


class ParamError(ValueError):
    """Raised for an unknown parameter name or an out-of-range value."""


def _as_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off"):
        return False
    raise ParamError("expected a boolean, got {!r}".format(value))


class Param(object):
    """One runtime-settable knob.

    ``attr`` is the ``config`` attribute this shadows, or ``None`` for a
    knob the firmware owns outright (e.g. ``deenergize_after``, which has
    no bench default because the pre-sweep firmware always left the Tic
    energised).
    """

    def __init__(self, name, attr, kind, lo=None, hi=None,
                 default=None, choices=None, doc=""):
        self.name = name
        self.attr = attr
        self.kind = kind
        self.lo = lo
        self.hi = hi
        self.default = default
        self.choices = choices
        self.doc = doc

    def coerce(self, value):
        try:
            coerced = self.kind(value)
        except ParamError:
            raise
        except Exception:
            raise ParamError("{}: cannot interpret {!r} as {}".format(
                self.name, value, getattr(self.kind, "__name__", self.kind)))
        if self.choices is not None and coerced not in self.choices:
            raise ParamError("{}: {!r} not in {}".format(
                self.name, coerced, list(self.choices)))
        if self.lo is not None and coerced < self.lo:
            raise ParamError("{}: {} below minimum {}".format(
                self.name, coerced, self.lo))
        if self.hi is not None and coerced > self.hi:
            raise ParamError("{}: {} above maximum {}".format(
                self.name, coerced, self.hi))
        return coerced


# The Tic T500 only accepts these step modes; offering 1/64 would be
# silently clamped by the controller and quietly desynchronise the
# firmware's local position shadow.
TIC_STEP_MODES = (1, 2, 4, 8, 16, 32)

SPEC = (
    # -- stepper ------------------------------------------------------
    Param("stepper_rpm", "STEPPER_SPEED_RPM", float, 0.1, 600.0,
          doc="auger speed; step frequency = rpm/60 * steps_per_rev"),
    Param("stepper_microsteps", "STEPPER_MICROSTEPS", int,
          choices=TIC_STEP_MODES, doc="Tic step mode denominator"),
    Param("stepper_accel", "STEPPER_ACCEL_REV_PER_S2", float, 0.01, 1000.0,
          doc="acceleration and deceleration, rev/s^2"),
    Param("dispense_deg", "STEPPER_DISPENSE_DEG", float, -3600.0, 3600.0,
          doc="degrees of auger rotation for the 'd' command"),
    Param("deenergize_after", None, _as_bool, default=False,
          doc="de-energise the Tic after each move (kills coil hum)"),
    Param("move_pad_ms", None, int, 0, 10000, default=2000,
          doc="extra wait after the estimated move time; the pre-#139 "
              "firmware hard-coded 2000 ms, which smears settle-time "
              "measurements by up to 2 s"),
    # -- ERM vibration motor -----------------------------------------
    Param("vib_effect", "VIBRATION_EFFECT_ID", int, 1, 123,
          doc="DRV2605 waveform library effect index"),
    Param("vib_duration_s", "VIBRATION_DURATION_S", float, 0.0, 60.0),
    Param("vib_library", "VIBRATION_LIBRARY", int, 1, 7),
    # -- solenoid tap -------------------------------------------------
    Param("tap_count", "TAP_COUNT", int, 0, 100),
    Param("tap_on_ms", "TAP_ON_MS", int, 1, 2000),
    Param("tap_off_ms", "TAP_OFF_MS", int, 1, 5000),
    Param("tap_duty", "TAP_PWM_DUTY", float, 0.0, 1.0),
    # -- servo --------------------------------------------------------
    Param("servo_speed_dps", "SERVO_SPEED_DEG_PER_S", float, 0.0, 1000.0),
    Param("servo_hold", None, _as_bool, default=True,
          doc="keep driving the servo PWM after a move; digital servos "
              "hunt around the setpoint and inject continuous noise"),
)

_BY_NAME = dict((p.name, p) for p in SPEC)


class Params(object):
    """Validated overlay of runtime values on top of ``config``."""

    def __init__(self, config, spec=SPEC):
        self._config = config
        self._spec = spec
        self._by_name = dict((p.name, p) for p in spec)
        self._overrides = {}

    # -- introspection ---------------------------------------------------
    def names(self):
        return sorted(self._by_name)

    def spec(self, name):
        try:
            return self._by_name[name]
        except KeyError:
            raise ParamError("unknown parameter {!r}".format(name))

    def base(self, name):
        """The value this knob would have with no runtime override."""
        param = self.spec(name)
        if param.attr is None:
            return param.default
        return getattr(self._config, param.attr, param.default)

    # -- access ----------------------------------------------------------
    def get(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return self.base(name)

    __getitem__ = get

    def set(self, name, value):
        param = self.spec(name)
        coerced = param.coerce(value)
        self._overrides[name] = coerced
        return coerced

    def reset(self, name=None):
        """Drop one override, or all of them."""
        if name is None:
            self._overrides = {}
            return
        self.spec(name)  # validate the name even when clearing
        self._overrides.pop(name, None)

    def is_overridden(self, name):
        return name in self._overrides

    def as_dict(self):
        return dict((p.name, self.get(p.name)) for p in self._spec)

    def snapshot(self):
        """Single-line JSON of the full active parameter set.

        Emitted by the ``params`` command.  The host writes this verbatim
        into the run log, so a trace can always be replayed against the
        parameters that produced it.
        """
        return _json.dumps(self.as_dict())
