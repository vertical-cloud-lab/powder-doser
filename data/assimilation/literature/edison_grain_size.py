#!/usr/bin/env python3
"""Edison Scientific literature search for issue #210: predicting particle (grain)
size or particle size distribution from powder flow data.

Two tasks are sent to https://api.platform.edisonscientific.com:

* ``grain_size_from_flow``: a deep literature review (``LITERATURE_HIGH``,
  ``job-futurehouse-paperqa3-high``) of work that infers particle size or the
  particle size distribution from flow or process data, and of how that could
  be applied to the doser's balance data.
* ``precedent``: a "has anyone done this?" check (``PRECEDENT``,
  ``job-futurehouse-paperqa3-precedent``) for size inference from screw/auger
  feeder or gravimetric dosing data specifically.

Run from the repo root with ``EDISON_PLATFORM_API_KEY`` set. ``edison-client``
0.18 needs Python < 3.14 (its ``litellm`` pin has no 3.14 wheels)::

    python -m venv /tmp/edison-venv && /tmp/edison-venv/bin/pip install edison-client
    /tmp/edison-venv/bin/python data/assimilation/literature/edison_grain_size.py submit
    /tmp/edison-venv/bin/python data/assimilation/literature/edison_grain_size.py wait
    /tmp/edison-venv/bin/python data/assimilation/literature/edison_grain_size.py fetch [key ...]

``submit`` writes ``_task_id.json`` (the literature review) and
``_task_id_precedent.json``. ``wait`` blocks, polling every 240 s, until both
tasks finish. ``fetch`` writes, for each task, ``<key>.task.json`` (the full
verbose task record: agent state, environment frame with every retrieved
context, references, cost), ``<key>.answer.md``, ``<key>.references.md`` and
any files attached to the trajectory under ``<key>_files/``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from edison_client import EdisonClient, JobNames

SERVICE_URI = "https://api.platform.edisonscientific.com"
OUT = Path(__file__).resolve().parent
TAGS = ["powder-doser", "issue-210", "grain-size-from-flow"]
DONE = {"success", "fail", "failed", "cancelled", "error"}

GRAIN_SIZE_QUERY = """\
I run an open-hardware benchtop gravimetric powder doser and want to infer each powder's \
particle (grain) size, or its particle size distribution (PSD), from the doser's own flow \
data, as a data assimilation / inverse problem. What published work predicts or infers the \
particle size or PSD of powders or granular materials from flow or process data, rather than \
from direct sizing (sieving, laser diffraction, imaging)?

The doser: a small auger (screw) in a tube that tilts 0-45 degrees above horizontal, driven \
by a stepper motor, with a vibration motor and a solenoid tapper, dispensing into a cup on an \
analytical balance (0.1 mg resolution). My data: balance mass-versus-time readings every \
0.1-0.4 s during continuous auger rotation at fixed speeds (15, 45 and 90 rpm); mass \
delivered per single auger revolution at three tube angles; spontaneous outflow during \
holds; mass per tap; closed-loop doses to target masses (bulk, fine and tap stages) with an \
on-board Kalman filter's mass and flow-rate estimates; and stall and clog events. Powders \
(identity known, PSD not measured on the device): table salt, sodium sulfate, barium \
chloride, calcium lactate, silicon -110/+200 mesh and -325 mesh, gas-atomized AlSi10Mg and \
Al 4047, white and brown rice flour, xanthan gum, carboxymethyl cellulose, sodium alginate \
and fumed silica.

Please cover the following, with quantitative results (accuracy, R2, error in d50) where \
available and full citations with DOIs:
1. Physics-based inversion: discharge or throughput laws that depend on particle size \
(Beverloo-type orifice and hopper flow, screw/auger feeder models), and statistics of flow \
fluctuations, intermittency, avalanches and clogging (for example their dependence on the \
outlet-to-particle size ratio, or the shot-noise variance of mass increments) that have been \
used, or could be used, to estimate particle size.
2. Signal-based sizing of flowing particles: acoustic emission, vibration and impact sensors, \
and analogous grain-size inversions in geophysics (bedload transport, debris flows).
3. Data-driven models (soft sensors, machine learning, multivariate/PLS) that predict PSD \
from process or flow measurements, and the forward models that predict feeder or flow \
behavior from PSD and other material properties (pharmaceutical loss-in-weight feeders, \
material property databases, metal additive-manufacturing powder flow tests such as the Hall \
flowmeter, revolution powder analyzer and FT4).
4. Bayesian calibration and data assimilation for granular materials (for example DEM \
parameter inference with sequential Monte Carlo or particle filters, ensemble Kalman \
filters, Gaussian-process surrogates): what has been estimated from bulk flow measurements, \
and whether particle size is identifiable separately from cohesion, friction, shape, density \
and moisture.
5. Whether anyone has inferred particle size from screw/auger feeder or gravimetric dosing \
data specifically, which features of mass-versus-time data carry the most size information, \
and which extra measurements (for example a few laser-diffraction PSDs as ground truth) would \
make such a model credible.
"""

PRECEDENT_QUERY = """\
Has anyone inferred or predicted the particle size or particle size distribution of a \
powder from gravimetric dispensing or feeding data, that is, from balance mass-versus-time \
readings, mass-flow-rate fluctuations, or the mass delivered per screw revolution of a \
screw/auger feeder, loss-in-weight feeder or automated powder dosing instrument?
"""

TASKS = {
    "grain_size_from_flow": (JobNames.LITERATURE_HIGH, GRAIN_SIZE_QUERY, "_task_id.json"),
    "precedent": (JobNames.PRECEDENT, PRECEDENT_QUERY, "_task_id_precedent.json"),
}


def client() -> EdisonClient:
    key = os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        sys.exit("EDISON_PLATFORM_API_KEY is not set")
    return EdisonClient(service_uri=SERVICE_URI, api_key=key)


def task_ids() -> dict[str, str]:
    return {k: json.loads((OUT / f).read_text())["task_id"] for k, (_, _, f) in TASKS.items()}


def submit() -> None:
    c = client()
    for key, (job, query, fname) in TASKS.items():
        if (OUT / fname).exists():
            print(f"{key}: already submitted ({fname} exists), skipping")
            continue
        tid = c.create_task({"name": job, "query": query, "tags": TAGS + [key]})
        record = {
            "task_id": str(tid),
            "key": key,
            "job_name": job.value,
            "service_uri": SERVICE_URI,
            "submitted_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (OUT / fname).write_text(json.dumps(record, indent=2) + "\n")
        print(f"{key}: submitted {job.value} task_id={tid}")


def wait(interval: int = 240) -> None:
    c = client()
    ids = task_ids()
    while True:
        status = {k: str(c.get_task(task_id=t, lite=True).status) for k, t in ids.items()}
        print(datetime.now(timezone.utc).strftime("%H:%M:%S"), status, flush=True)
        if all(s in DONE for s in status.values()):
            return
        time.sleep(interval)


def _find(obj, key):
    """First value stored under ``key`` anywhere in a nested dict/list."""
    if isinstance(obj, dict):
        if obj.get(key):
            return obj[key]
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            found = _find(v, key)
            if found:
                return found
    return None


def fetch(keys: list[str] | None = None) -> None:
    c = client()
    for key, tid in task_ids().items():
        if keys and key not in keys:
            continue
        verbose = c.get_task(task_id=tid, verbose=True)
        data = verbose.model_dump(mode="json")
        (OUT / f"{key}.task.json").write_text(json.dumps(data, indent=1, default=str) + "\n")

        brief = c.get_task(task_id=tid)
        answer = (
            getattr(brief, "formatted_answer", None)
            or _find(data, "formatted_answer")
            or getattr(brief, "answer", None)
            or _find(data, "answer")
            or ""
        )
        refs = getattr(brief, "references", None) or _find(data, "references") or ""
        if not isinstance(refs, str):
            refs = json.dumps(refs, indent=1, default=str)
        (OUT / f"{key}.answer.md").write_text(str(answer).rstrip() + "\n")
        (OUT / f"{key}.references.md").write_text(refs.rstrip() + "\n")
        print(f"{key}: status={data.get('status')} answer={len(str(answer))} chars "
              f"references={len(refs)} chars")

        try:
            files = c.list_files(trajectory_id=tid)
        except Exception as exc:  # noqa: BLE001 - a listing failure shouldn't lose the answer
            print(f"{key}: list_files failed ({type(exc).__name__}: {exc})")
            continue
        entries = files.get("data", files) if isinstance(files, dict) else files
        if not entries:
            print(f"{key}: no files attached to the trajectory")
            continue
        fdir = OUT / f"{key}_files"
        fdir.mkdir(exist_ok=True)
        (fdir / "list_files.json").write_text(json.dumps(files, indent=1, default=str) + "\n")
        for entry in entries if isinstance(entries, list) else []:
            ds = entry.get("data_storage") or entry.get("data_storage_entry") or entry
            sid = ds.get("id") if isinstance(ds, dict) else None
            if not sid:
                continue
            got = c.fetch_data_from_storage(sid)
            paths = got if isinstance(got, list) else [got]
            for p in paths:
                if isinstance(p, Path):
                    dest = fdir / p.name
                    (shutil.copytree if p.is_dir() else shutil.copy2)(p, dest)
                elif p is not None and hasattr(p, "content"):
                    name = getattr(p, "filename", None) or f"{sid}.txt"
                    (fdir / Path(name).name).write_text(str(p.content))
            print(f"{key}: saved data entry {sid}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Edison literature search for issue #210: grain size from powder flow data."
    )
    ap.add_argument("cmd", choices=["submit", "wait", "fetch"])
    ap.add_argument("keys", nargs="*", help="fetch only these tasks (default: all)")
    args = ap.parse_args()
    if args.cmd == "fetch":
        fetch(args.keys)
    else:
        {"submit": submit, "wait": wait}[args.cmd]()


if __name__ == "__main__":
    main()
