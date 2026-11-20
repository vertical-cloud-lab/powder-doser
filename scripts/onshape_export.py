#!/usr/bin/env python3
"""Export the #193 Onshape Part Studios (and the assembly) as STL and STEP with the repo's keys.

    python scripts/onshape_export.py SNAPSHOT_DIR [--only NAME,...] [--max-calls N]
                                     [--wait-until HH:MM [--every SECONDS]]
                                     [--no-step] [--no-assembly] [--dry-run]

SNAPSHOT_DIR is the folder scripts/onshape_public_snapshot.py wrote (cad/onshape-193). Its
manifest.json holds every document, workspace and element id, so nothing is listed with the
keys. Files land next to each element's renders:
  SNAPSHOT_DIR/<doc>/<element>/stl/<part>.stl     one binary STL per part, in millimetres
  SNAPSHOT_DIR/<doc>/<element>/<element>.step     the whole Part Studio (or the assembly)
  SNAPSHOT_DIR/export.json                        every call and its status, file hashes, checks
The Baseplate goes first. --only takes #193 entry names ("Baseplate,Auger").

Budget. Onshape counts every 2xx/3xx answer to a keyed call against the yearly cap (the keys'
EDU Educator plan: 2,500 calls per company per year) and no 4xx/5xx answer, so a 402 costs
nothing. Per Part Studio: 2 calls for the STLs (a 307, then the file), and for the STEP 1 to
start the translation, 1 or more polls and 1 download. That is about 6 per Part Studio, or
about 80 for everything in #193 (--dry-run prints the estimate). --max-calls stops the run
before the budget is passed, and the first 402 stops it too.

--wait-until polls one document request every --every seconds until the keys are answered
again (a 402 isn't counted) or the time passes, and then exports.

After each Part Studio's STLs are saved, their union is checked against the element's Onshape
renders with docs/prints/2026-11-03-baseplate-h2d/check_stl.py (IoU of the top, front and
right silhouettes). Each element's sourceMicroversion is read anonymously (not counted) just
before export, so export.json shows whether the model had changed since the snapshot.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

API = "https://cad.onshape.com/api/v6"
JSON_ACCEPT = "application/json;charset=UTF-8; qs=0.09"
CHECK = Path(__file__).resolve().parent.parent / "docs/prints/2026-11-03-baseplate-h2d/check_stl.py"
FIRST = "Baseplate"
REDIRECTS = (301, 302, 303, 307, 308)


class CapReached(Exception):
    """HTTP 402: the yearly API cap. Not counted, but nothing else will be answered either."""


class OutOfBudget(Exception):
    """--max-calls reached."""


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def redact(url):
    """Host and path only (a redirect's query can carry a signature), ids as {id}."""
    u = urlparse(url)
    path = re.sub(r"[0-9a-f]{24}", "{id}", u.path)
    return path.replace("/api/v6", "") if u.hostname == "cad.onshape.com" else f"{u.hostname}{path}"


class Onshape:
    def __init__(self, max_calls):
        self.auth = (os.environ["ONSHAPE_ACCESS_KEY"].strip(), os.environ["ONSHAPE_SECRET_KEY"].strip())
        self.max_calls = max_calls
        self.counted = 0
        self.log = []

    def call(self, method, url, params=None, body=None, accept=JSON_ACCEPT):
        if self.counted >= self.max_calls:
            raise OutOfBudget(f"--max-calls {self.max_calls} reached")
        full = url if url.startswith("http") else f"{API}/{url}"
        host = urlparse(full).hostname or ""
        # The keys go to Onshape only, never to a redirect on some other host.
        auth = self.auth if host == "onshape.com" or host.endswith(".onshape.com") else None
        for attempt in range(5):
            r = requests.request(method, full, params=params, json=body, headers={"Accept": accept},
                                 auth=auth, allow_redirects=False, timeout=300)
            self.log.append({"utc": now(), "method": method, "path": redact(full), "status": r.status_code})
            if r.status_code != 429:  # rate limited: not counted, wait and retry
                break
            time.sleep(float(r.headers.get("Retry-After") or 10 * (attempt + 1)))
        if 200 <= r.status_code < 400:
            self.counted += 1
        if r.status_code == 402:
            raise CapReached(" ".join(r.text.split())[:200])
        if r.status_code >= 400:
            raise requests.HTTPError(f"{method} {redact(full)} -> {r.status_code}: {r.text.strip()[:300]}",
                                     response=r)
        return r

    def download(self, url, params=None):
        """GET that follows Onshape's 307 to the file, re-sending the keys (Onshape requires it)."""
        full = url if url.startswith("http") else f"{API}/{url}"
        r = self.call("GET", full, params=params, accept="*/*")
        for _ in range(3):
            if r.status_code not in REDIRECTS:
                return r
            full = urljoin(full, r.headers["Location"])
            r = self.call("GET", full, accept="*/*")
        raise RuntimeError(f"too many redirects for {redact(url)}")


def anon_microversion(did, wid, eid):
    """The Part Studio's sourceMicroversion, read without the keys (not counted)."""
    r = requests.get(f"{API}/partstudios/d/{did}/w/{wid}/e/{eid}/features",
                     headers={"Accept": JSON_ACCEPT}, timeout=180)
    return r.json().get("sourceMicroversion") if r.ok else f"HTTP {r.status_code}"


def filename(r, default):
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', r.headers.get("Content-Disposition", ""))
    return m.group(1) if m else default


def describe(data):
    import trimesh
    m = trimesh.load(io.BytesIO(data), file_type="stl", force="mesh")
    lo, hi = m.bounds
    return m, {"triangles": int(len(m.faces)), "watertight": bool(m.is_watertight),
               "volume_cm3": round(float(m.volume) / 1000, 3), "extent_mm": [round(float(x), 2) for x in hi - lo]}


def export_stl(os_, did, wid, eid, out, rec):
    """One binary STL per part (grouping=false gives a zip), in mm."""
    params = {"mode": "binary", "units": "millimeter", "scale": 1, "grouping": "false"}
    url = f"partstudios/d/{did}/w/{wid}/e/{eid}/stl"
    try:
        r = os_.download(url, params)
    except requests.HTTPError as ex:  # a 4xx is not counted; fall back to one STL of all parts
        if ex.response is None or ex.response.status_code != 400:
            raise
        params["grouping"] = "true"
        r = os_.download(url, params)
    data = r.content
    files = {}
    if data[:4] == b"PK\x03\x04":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                if not info.is_dir() and info.filename.lower().endswith(".stl"):
                    files[Path(info.filename).name] = z.read(info)
    else:
        files[filename(r, f"{out.name}.stl")] = data
    sdir = out / "stl"
    sdir.mkdir(parents=True, exist_ok=True)
    for old in sdir.glob("*.stl"):
        old.unlink()
    meshes, saved = [], []
    for name, blob in sorted(files.items()):
        stem = slug(Path(name).stem) or "part"
        p = sdir / f"{stem}.stl"
        n = 1
        while p.exists():  # two parts whose names slug alike
            n += 1
            p = sdir / f"{stem}-{n}.stl"
        p.write_bytes(blob)
        mesh, info = describe(blob)
        meshes.append(mesh)
        saved.append({"file": str(p), "part": Path(name).stem, "bytes": len(blob),
                      "sha256": hashlib.sha256(blob).hexdigest(), **info})
        print(f"     STL {p.name}: {info['extent_mm']} mm, {info['triangles']} triangles, "
              f"watertight {info['watertight']}", flush=True)
    rec["stl"] = saved
    rec["stl_grouping"] = params["grouping"]
    return meshes


def check(meshes, views):
    """check_stl.py on the union of the parts, against Onshape's renders of the Part Studio."""
    import trimesh
    if not meshes or not (CHECK.exists() and (views / "top.png").exists()):
        return None
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "all-parts.stl"
        trimesh.util.concatenate(meshes).export(p)
        res = subprocess.run([sys.executable, str(CHECK), str(p), str(views)], capture_output=True,
                             text=True, timeout=1800)
    lines = (res.stdout + res.stderr).strip().splitlines()
    for line in lines:
        print("       check:", line, flush=True)
    return lines


def export_step(os_, kind, did, wid, eid, dest, rec):
    r = os_.call("POST", f"{kind}/d/{did}/w/{wid}/e/{eid}/translations",
                 body={"formatName": "STEP", "storeInDocument": False, "flattenAssemblies": False,
                       "yAxisIsUp": False, "destinationName": dest.stem})
    tr = r.json()
    rec["step_translation"] = tr.get("id")
    wait, t0 = 5, time.time()
    while tr.get("requestState") == "ACTIVE" and time.time() - t0 < 600:
        time.sleep(wait)
        wait = min(wait * 2, 40)
        tr = os_.call("GET", f"translations/{tr['id']}").json()
    if tr.get("requestState") != "DONE" or not tr.get("resultExternalDataIds"):
        raise RuntimeError(f"STEP translation {tr.get('requestState')}: {tr.get('failureReason')}")
    r = os_.download(f"documents/d/{did}/externaldata/{tr['resultExternalDataIds'][0]}")
    dest.write_bytes(r.content)
    rec["step"] = {"file": str(dest), "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest()}
    print(f"     STEP {dest.name}: {len(r.content)} bytes", flush=True)


def wait_for_keys(os_, did, until, every):
    """Poll a document request until it isn't a 402 (True) or `until` passes (False)."""
    while True:
        try:
            os_.call("GET", f"documents/{did}")
            print(f"{now()} the keys are answered again", flush=True)
            return True
        except CapReached as ex:
            print(f"{now()} still 402 ({ex})", flush=True)
        if time.time() + every > until:
            return False
        time.sleep(every)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--only", default="", help="comma-separated #193 entry names")
    ap.add_argument("--max-calls", type=int, default=120)
    ap.add_argument("--wait-until", help="UTC HH:MM (today) to keep retrying a capped key until")
    ap.add_argument("--every", type=int, default=240, help="seconds between retries")
    ap.add_argument("--no-step", action="store_true")
    ap.add_argument("--no-assembly", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log", default="export.json", help="log file name inside SNAPSHOT_DIR")
    a = ap.parse_args()

    m = json.loads((a.snapshot / "manifest.json").read_text())
    only = {slug(x) for x in a.only.split(",") if x.strip()}
    jobs = []
    for d in m["documents"]:
        if only and slug(d["name"]) not in only:
            continue
        for e in d["elements"]:
            if not e.get("dir") or not e.get("extent_mm"):  # not snapshotted, or an empty Part Studio
                continue
            if e["type"] == "ASSEMBLY" and (a.no_assembly or a.no_step):
                continue
            jobs.append((d, e))
    jobs.sort(key=lambda j: j[0]["name"] != FIRST)
    per_ps = 2 + (0 if a.no_step else 4)
    estimate = sum(per_ps if e["type"] == "PARTSTUDIO" else 5 for _, e in jobs)
    print(f"{len(jobs)} elements, about {estimate} counted calls (--max-calls {a.max_calls})", flush=True)
    for d, e in jobs:
        print(f"  {d['name']}: {e['name']} ({e['type']}) -> {e['dir']}", flush=True)
    if a.dry_run:
        return 0

    os_ = Onshape(a.max_calls)
    record = {"started_utc": now(), "api": API, "snapshot_fetched_utc": m.get("fetched_utc"),
              "max_calls": a.max_calls, "estimate": estimate, "elements": []}
    code = 0
    try:
        if a.wait_until:
            hh, mm = map(int, a.wait_until.split(":"))
            until = dt.datetime.now(dt.timezone.utc).replace(hour=hh, minute=mm, second=0, microsecond=0)
            probe = next(d for d in m["documents"] if d["name"] == FIRST)["did"]
            if not wait_for_keys(os_, probe, until.timestamp(), a.every):
                record["stopped"] = f"keys still 402 at {now()} (waited until {a.wait_until} UTC)"
                return 3
        for d, e in jobs:
            did, wid, eid = d["did"], d["wid"], e["id"]
            out = a.snapshot / e["dir"]
            rec = {"entry": d["name"], "element": e["name"], "type": e["type"], "id": eid, "dir": e["dir"],
                   "snapshot_microversion": e.get("sourceMicroversion")}
            record["elements"].append(rec)
            print(f"{now()} {d['name']}: {e['name']}", flush=True)
            try:
                if e["type"] == "PARTSTUDIO":
                    rec["microversion_at_export"] = anon_microversion(did, wid, eid)
                    rec["unchanged_since_snapshot"] = rec["microversion_at_export"] == rec["snapshot_microversion"]
                    meshes = export_stl(os_, did, wid, eid, out, rec)
                    rec["check"] = check(meshes, out)
                if not a.no_step:
                    kind = "assemblies" if e["type"] == "ASSEMBLY" else "partstudios"
                    export_step(os_, kind, did, wid, eid, out / f"{slug(e['name'])}.step", rec)
            except (CapReached, OutOfBudget):
                raise
            except Exception as ex:  # record it and go on to the next element
                rec["error"] = f"{type(ex).__name__}: {ex}"
                print("     error:", rec["error"], flush=True)
                code = 1
    except (CapReached, OutOfBudget) as ex:
        record["stopped"] = f"{type(ex).__name__} at {now()}: {ex}"
        print("stopped:", record["stopped"], flush=True)
        code = 2
    finally:
        record["finished_utc"] = now()
        record["calls_counted"] = os_.counted
        record["calls"] = os_.log
        for r in record["elements"]:  # repo-relative paths
            for f in r.get("stl", []) + ([r["step"]] if r.get("step") else []):
                f["file"] = str(Path(f["file"]).relative_to(a.snapshot))
        (a.snapshot / a.log).write_text(json.dumps(record, indent=1) + "\n")
        print(f"counted calls: {os_.counted}; wrote {a.snapshot / a.log}", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
