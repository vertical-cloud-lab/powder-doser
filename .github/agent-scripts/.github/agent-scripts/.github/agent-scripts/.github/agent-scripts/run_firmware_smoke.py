#!/usr/bin/env python3
"""
run_firmware_smoke.py
Host-side smoke tests for MicroPython firmware by providing a stubbed 'machine' module
and importing firmware modules under CPython. Writes reports/firmware-smoke.json.
Exit 2 if any component fails.
"""
from __future__ import annotations
import argparse
import importlib
import importlib.util
import json
import sys
import types
import traceback
from pathlib import Path

DEFAULT_FW_PATH = Path("hardware/test-module/firmware")
REPORT = Path("reports/firmware-smoke.json")


# Minimal machine stubs
class Pin:
    OUT = 0
    IN = 1

    def __init__(self, pin=None, mode=None):
        self.pin = pin
        self.mode = mode
        self.value_state = 0

    def value(self, v=None):
        if v is None:
            return self.value_state
        self.value_state = v


class PWM:
    def __init__(self, pin):
        self.pin = pin
        self.freq = None
        self.duty = None

    def freq(self, f):
        self.freq = f

    def duty_u16(self, v):
        self.duty = v


class I2C:
    def __init__(self, *args, **kwargs):
        pass


def insert_stub_machine():
    mod = types.ModuleType("machine")
    mod.Pin = Pin
    mod.PWM = PWM
    mod.I2C = I2C
    sys.modules["machine"] = mod


def import_firmware_module(path: Path, module_name="main"):
    # add firmware path to sys.path temporarily
    sys.path.insert(0, str(path.resolve()))
    try:
        return importlib.import_module(module_name)
    except Exception:
        # attempt to import as package.main
        try:
            spec = importlib.util.find_spec(module_name)
            if spec:
                return importlib.import_module(module_name)
        except Exception:
            raise
    finally:
        if str(path.resolve()) in sys.path:
            sys.path.remove(str(path.resolve()))


def run_component_tests(mod):
    results = {}
    # heuristics: look for classes named Stepper, Servo, Tap, Vibration
    for name in ("Stepper", "Servo", "Tap", "Vibration"):
        ok = False
        err = None
        try:
            cls = getattr(mod, name, None)
            if cls is None:
                # try within submodules
                cls = getattr(mod, name.lower(), None)
            if cls is None:
                results[name.lower()] = {"ok": False, "error": f"{name} not found"}
                continue
            # attempt to instantiate and call small set of methods
            inst = cls() if callable(cls) else None
            if inst is None:
                results[name.lower()] = {"ok": False, "error": f"{name} not instantiable"}
                continue
            # call a few common method names safely
            for method_name in ("set_speed", "rotate_degrees", "move_to", "tap", "buzz"):
                if hasattr(inst, method_name):
                    try:
                        getattr(inst, method_name)(0 if method_name != "rotate_degrees" else 0)
                    except TypeError:
                        # try with no args
                        try:
                            getattr(inst, method_name)()
                        except Exception:
                            pass
            ok = True
        except Exception as e:
            ok = False
            err = traceback.format_exc()
        results[name.lower()] = {"ok": ok, "error": err}
    return results


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue", type=int, default=87)
    p.add_argument("--pr", type=int, default=61)
    p.add_argument("--firmware-path", default=str(DEFAULT_FW_PATH))
    args = p.parse_args(argv)

    insert_stub_machine()
    failures = 0
    components = {}
    try:
        mod = import_firmware_module(Path(args.firmware_path), module_name="main")
        components = run_component_tests(mod)
        for name, res in components.items():
            if not res.get("ok"):
                failures += 1
    except Exception as e:
        components["import_error"] = {"ok": False, "error": str(e)}
        failures += 1

    out = {"components": components, "summary": {"passed": sum(1 for v in components.values() if v.get("ok")), "failed": sum(1 for v in components.values() if not v.get("ok"))}}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    if failures:
        print(f"{failures} component failures", file=sys.stderr)
        sys.exit(2)
    print("Firmware smoke tests passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
