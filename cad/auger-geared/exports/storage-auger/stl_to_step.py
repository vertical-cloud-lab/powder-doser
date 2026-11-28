#!/usr/bin/env python3
# ================================================================
# Zoo (zoo.dev) STL -> STEP converter for the storage augers
# ================================================================
#
# Asked for by @swcharles on PR #49 (comment 4847597739):
#   "give step files for the threaded storage auger and test, as well
#    as for the cap.  This is as opposed to the stl files currently
#    available."
#
# Why a separate converter (vs zoo_text_to_cad.py)
# ------------------------------------------------
# `zoo_text_to_cad.py` drives Zoo's *generative* Text-to-CAD model from
# a written prompt.  That is great for the KCL design source, but the
# model only *approximates* fiddly features such as the multi-turn
# helical thread and the internal Archimedean screw, so its STEP does
# not exactly match the print master.
#
# This script instead asks Zoo's geometry engine to *convert* the
# already-rendered OpenSCAD print master (the committed `.stl`) straight
# into STEP, so the STEP is an EXACT, lossless copy of the very mesh we
# 3-D print -- the real external thread, the real internal screw, the
# real funnel.  This is the faithful exchange file the reviewer asked
# for.
#
# Endpoint (synchronous):
#   POST /file/conversion/stl/step   (raw STL body) -> {outputs: {*.step}}
#
# Zoo emits an AP242 faceted B-rep in metre units; a handful of
# degenerate (zero-area) triangles come back with a `(NaN, NaN, NaN)`
# face normal, which is not valid STEP syntax, so we replace those with
# a unit +Z direction before saving.  The triangle vertices themselves
# are untouched, so the geometry stays bit-for-bit the STL geometry.
#
# Auth: the Zoo API key is provided as the ZOO_API_TOKEN environment
# variable.  Do NOT echo/print the token.
#
# Usage:
#   python3 stl_to_step.py                 # convert the default parts
#   python3 stl_to_step.py NAME ...        # only the named part(s)
# ================================================================

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.zoo.dev"
HERE = os.path.dirname(os.path.abspath(__file__))
# The OpenSCAD print masters live two levels up, in cad/auger-geared/.
SCAD_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))
STEP_DIR = os.path.join(HERE, "step")
ART_DIR = os.path.join(HERE, "zoo_artifacts")

# Parts whose STEP should be an exact conversion of the print master.
# The threaded family (comment 4847597739): the two threaded storage
# augers and the hand cap.
DEFAULT_PARTS = [
    "threaded_archimedes-auger-storage",
    "threaded_archimedes-auger-storage-test",
    "threaded-storage-cap",
]


def _token():
    tok = os.environ.get("ZOO_API_TOKEN", "").strip()
    if not tok:
        sys.exit("ZOO_API_TOKEN is not set")
    return tok


def convert(name):
    stl_path = os.path.join(SCAD_DIR, name + ".stl")
    if not os.path.exists(stl_path):
        sys.exit(f"missing print master: {stl_path}")
    with open(stl_path, "rb") as f:
        body = f.read()
    headers = {
        "Authorization": "Bearer " + _token(),
        "User-Agent": "powder-doser-agent/1.0",
        "Content-Type": "application/octet-stream",
    }
    req = urllib.request.Request(
        API + "/file/conversion/stl/step", data=body, headers=headers, method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read()[:500]!r}\n")
        raise
    if resp.get("status") != "completed":
        sys.exit(f"{name}: conversion status {resp.get('status')}: {resp.get('error')}")

    outputs = resp.get("outputs") or {}
    step_key = next((k for k in outputs if k.endswith(".step")), None)
    if not step_key:
        sys.exit(f"{name}: no .step in outputs {list(outputs)}")
    b64 = outputs[step_key]
    raw = base64.b64decode(b64 + "=" * (-len(b64) % 4))
    text = raw.decode("latin1")

    # Sanitise the few degenerate-triangle NaN normals (invalid syntax).
    nan_fixed = text.count("(NaN, NaN, NaN)")
    text = text.replace("(NaN, NaN, NaN)", "(0., 0., 1.)")

    os.makedirs(STEP_DIR, exist_ok=True)
    os.makedirs(ART_DIR, exist_ok=True)
    step_path = os.path.join(STEP_DIR, name + ".step")
    with open(step_path, "w", newline="\n") as f:
        f.write(text)

    # Geometry check: parse every CARTESIAN_POINT and report the bounding
    # box in millimetres (Zoo writes metres) so a regression is obvious.
    bbox = _bbox_mm(text)
    with open(os.path.join(ART_DIR, name + ".convert.json"), "w") as f:
        json.dump(
            {
                "source": "zoo file conversion stl->step",
                "operation_id": resp.get("id"),
                "src_file": os.path.relpath(stl_path, SCAD_DIR),
                "nan_normals_fixed": nan_fixed,
                "bbox_mm": bbox,
            },
            f,
            indent=2,
        )
    print(
        f"  wrote step/{name}.step ({len(text)} bytes, "
        f"op {resp.get('id')}, nan_fixed={nan_fixed}, "
        f"bbox_mm={bbox}, +{time.time() - t0:.0f}s)"
    )


_PT_RE = re.compile(
    r"CARTESIAN_POINT\('',\s*\(\s*([-0-9.eE]+),\s*([-0-9.eE]+),\s*([-0-9.eE]+)\)\)"
)


def _bbox_mm(text):
    xs = ys = zs = None
    lo = [1e9, 1e9, 1e9]
    hi = [-1e9, -1e9, -1e9]
    found = False
    for m in _PT_RE.finditer(text):
        found = True
        for i in range(3):
            v = float(m.group(i + 1)) * 1000.0  # metre -> mm
            lo[i] = min(lo[i], v)
            hi[i] = max(hi[i], v)
    if not found:
        return None
    return [round(lo[i], 3) for i in range(3)] + [round(hi[i], 3) for i in range(3)]


def main(argv):
    names = [a for a in argv if not a.startswith("-")] or DEFAULT_PARTS
    for name in names:
        print(f"converting {name} ...")
        convert(name)


if __name__ == "__main__":
    main(sys.argv[1:])
