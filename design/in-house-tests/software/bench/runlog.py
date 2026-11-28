"""One folder per run:

  runs/<UTC stamp>_<test>_<jar>/
    manifest.json   jar id, operator, date, RH/T, git commit, parameters, files
    results.json    results and acceptance checks (pass/fail)
    events.jsonl    everything that happened, time-stamped
    <stream>.csv    balance, imu, loadcell, charge, env, ... streams
    images/*.png    every photo the analysis used
"""

import csv
import datetime as dt
import json
import os
import platform
import subprocess
import time

import numpy as np

from . import __version__


def git_info(path):
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True,
                                text=True, timeout=5).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=path,
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return {"commit": commit or None, "dirty": bool(dirty)}
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None}


def _jsonable(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if hasattr(o, "to_dict"):
        return o.to_dict()
    raise TypeError(type(o).__name__)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=_jsonable, allow_nan=True)


class Stream:
    def __init__(self, path, fields):
        self.f = open(path, "w", newline="")
        self.w = csv.writer(self.f)
        self.fields = list(fields)
        self.w.writerow(self.fields)
        self.n = 0

    def write(self, row):
        if isinstance(row, dict):
            row = [row.get(k) for k in self.fields]
        self.w.writerow(["" if v is None else (round(v, 6) if isinstance(v, float) else v) for v in row])
        self.n += 1
        if self.n % 20 == 0:
            self.f.flush()

    def close(self):
        self.f.close()


class RunLogger:
    def __init__(self, root, test, jar, operator, params=None, sim=False, note="", clock=None):
        self.t0 = time.time()
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_jar = "".join(c if c.isalnum() or c in "-_." else "_" for c in jar)
        self.dir = os.path.join(root, "{}_{}_{}".format(stamp, test, safe_jar))
        n = 1
        while os.path.exists(self.dir):
            n += 1
            self.dir = os.path.join(root, "{}_{}_{}-{}".format(stamp, test, safe_jar, n))
        os.makedirs(os.path.join(self.dir, "images"))
        self.clock = clock or time.time
        self.streams = {}
        here = os.path.dirname(os.path.abspath(__file__))
        self.manifest = {
            "test": test, "jar": jar, "operator": operator,
            "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "sim": bool(sim), "note": note, "params": params or {},
            "software": {"bench": __version__, "python": platform.python_version(),
                         "host": platform.node() if not sim else "sim", **git_info(here)},
            "env": {}, "status": "running", "files": [],
        }
        self._events = open(os.path.join(self.dir, "events.jsonl"), "w")
        self._write_manifest()

    def _write_manifest(self):
        dump(self.manifest, os.path.join(self.dir, "manifest.json"))

    def env(self, label, t_c, rh, source="bench SHT45"):
        self.manifest["env"][label] = {"t_c": t_c, "rh": rh, "source": source}
        self._write_manifest()

    def event(self, kind, **data):
        rec = {"t": self.clock(), "kind": kind}
        rec.update(data)
        self._events.write(json.dumps(rec, default=_jsonable) + "\n")
        self._events.flush()

    def stream(self, name, fields):
        if name not in self.streams:
            self.streams[name] = Stream(os.path.join(self.dir, name + ".csv"), fields)
        return self.streams[name]

    def image(self, name, arr):
        from PIL import Image
        a = np.asarray(arr)
        if a.dtype != np.uint8:
            a = np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)
        rel = os.path.join("images", name + ".png")
        Image.fromarray(a).save(os.path.join(self.dir, rel))
        return rel

    def save_json(self, name, obj):
        dump(obj, os.path.join(self.dir, name))

    def finish(self, results, checks, status=None):
        for s in self.streams.values():
            s.close()
        self._events.close()
        passed = all(c["pass"] for c in checks) if checks else None
        out = {"results": results, "checks": checks, "all_pass": passed}
        dump(out, os.path.join(self.dir, "results.json"))
        self.manifest["status"] = status or ("pass" if passed else "check-failed" if checks else "done")
        self.manifest["duration_s"] = round(time.time() - self.t0, 2)
        self.manifest["files"] = sorted(os.path.relpath(os.path.join(dp, f), self.dir)
                                        for dp, _, fs in os.walk(self.dir) for f in fs)
        self._write_manifest()
        return out
