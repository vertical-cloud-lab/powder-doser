"""Load the firmware's runtime-parameter overlay on the host.

``hardware/test-module/firmware/params.py`` is written to run on the Pico,
but it deliberately imports nothing from ``machine``, so the host can load
it directly.  Doing so means the sweep validates parameter names and
ranges against *the same table the firmware enforces* -- a typo or an
out-of-range level fails on the host in milliseconds instead of producing
a run that the rig silently rejected halfway through the night.

It also gives the host test suite real coverage of the firmware module.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

FIRMWARE_DIR = (Path(__file__).resolve().parent.parent
                / "hardware" / "test-module" / "firmware")
PARAMS_PATH = FIRMWARE_DIR / "params.py"

_cached: ModuleType | None = None


def load_params_module() -> ModuleType:
    """Import ``params.py`` from the firmware tree (cached)."""
    global _cached
    if _cached is not None:
        return _cached
    if not PARAMS_PATH.exists():  # pragma: no cover - repo layout guard
        raise FileNotFoundError(
            "firmware params module not found at {}".format(PARAMS_PATH))
    spec = importlib.util.spec_from_file_location(
        "powder_doser_firmware_params", PARAMS_PATH)
    module = importlib.util.module_from_spec(spec)
    # Registered under a namespaced key so it can't collide with an
    # unrelated top-level ``params`` on the host's sys.path.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _cached = module
    return module


class StubConfig:
    """Stand-in for the Pico's ``config.py``, which is not in the repo.

    Values are the bench defaults quoted in the firmware docstring and
    hardware notes.  Used for host-side validation and for the offline
    mock; the real rig always reports its own values back via ``params``.
    """

    STEPPER_FULL_STEPS_REV = 200
    STEPPER_SPEED_RPM = 30.0
    STEPPER_MICROSTEPS = 8
    STEPPER_ACCEL_REV_PER_S2 = 2.0
    STEPPER_DISPENSE_DEG = 90.0
    STEPPER_DIRECTION = 1

    VIBRATION_LIBRARY = 1
    VIBRATION_EFFECT_ID = 47
    VIBRATION_DURATION_S = 0.5

    TAP_COUNT = 2
    TAP_ON_MS = 40
    TAP_OFF_MS = 200
    TAP_PWM_DUTY = 0.8

    SERVO_MIN_ANGLE_DEG = 0.0
    SERVO_MAX_ANGLE_DEG = 180.0
    SERVO_DEFAULT_DEG = 90.0
    SERVO_SPEED_DEG_PER_S = 60.0
    SERVO_UPDATE_HZ = 50
    SERVO_PRESETS = {"horizontal": 0.0, "tilt": 45.0,
                     "vertical": 90.0, "tip": 135.0}


def make_params(config=None):
    """A :class:`Params` instance backed by ``config`` (default stub)."""
    module = load_params_module()
    return module.Params(config if config is not None else StubConfig())


def validate(name: str, value, config=None):
    """Coerce and range-check one parameter the way the firmware will."""
    return make_params(config).set(name, value)


def parameter_names() -> list:
    return make_params().names()
