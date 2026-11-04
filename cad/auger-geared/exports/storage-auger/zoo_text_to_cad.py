#!/usr/bin/env python3
# ================================================================
# Zoo (zoo.dev) Text-to-CAD runner for the storage augers
# ================================================================
#
# Asked for by @sgbaird on PR #49 (comment 4747154534):
#   "use the zoo.dev API to get the KCL instead of trying yourself.
#    Run multiple iterations if needed to get it right."
#
# Rather than hand-author the KCL, this script drives Zoo's
# Text-to-CAD ("ML-ephant") generative API to produce the KCL for the
# storage-auger family, then keeps the model's KCL output plus the
# STEP/GLTF it exports from that same source so the KCL and STEP are
# guaranteed to describe the same geometry.
#
# Auth: the Zoo API key is provided as the ZOO_API_TOKEN environment
# variable.  Do NOT echo/print the token.
#
# Usage:
#   python3 zoo_text_to_cad.py            # submit every PROMPTS entry,
#                                         # poll, save kcl/step/gltf
#   python3 zoo_text_to_cad.py NAME ...   # only the named part(s)
#   python3 zoo_text_to_cad.py --iterate NAME "edit instruction"
#                                         # refine an existing .kcl via
#                                         # the text-to-cad iteration API
#   python3 zoo_text_to_cad.py --fetch ID # re-fetch a prior operation
#
# Endpoints (see https://zoo.dev/docs/api):
#   POST /ai/text-to-cad/{output_format}?kcl=true   -> async op
#   GET  /user/text-to-cad/{id}                      -> poll
#   POST /ai/text-to-cad/iteration                   -> refine KCL
# ================================================================

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.zoo.dev"
HERE = os.path.dirname(os.path.abspath(__file__))
KCL_DIR = os.path.join(HERE, "kcl")
STEP_DIR = os.path.join(HERE, "step")
ART_DIR = os.path.join(HERE, "zoo_artifacts")


def _headers():
    tok = os.environ.get("ZOO_API_TOKEN", "").strip()
    if not tok:
        sys.exit("ZOO_API_TOKEN is not set")
    return {
        "Authorization": "Bearer " + tok,
        "User-Agent": "powder-doser-agent/1.0",
        "Content-Type": "application/json",
    }


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code} on {method} {path}: {e.read()[:500]!r}\n")
        raise


# ---- prompts ---------------------------------------------------
# Dimensions are copied from the OpenSCAD masters
# (storage-auger-core.scad / threaded-storage-auger-core.scad /
# auger-core.scad) so the generated geometry matches the print masters.

_COMMON = (
    "All dimensions in millimetres. The part is a vertical hollow tube "
    "with a 25 mm outer diameter (12.5 mm outer radius) and a 21 mm "
    "inner bore diameter (10.5 mm bore radius, 2 mm wall). "
)

_FUNNEL = (
    "The bottom 12 mm is a closed funnel cone: the bore tapers from the "
    "10.5 mm bore radius down to a 1.5 mm radius, ending in a 3 mm "
    "diameter exit hole through the very bottom face. "
)

_TOP_CAP = (
    "The top is closed by a 6 mm thick cap pierced by four 4 mm by 7 mm "
    "rectangular loading slots arranged in a cross on a 6.5 mm radius, "
    "and a central 2.5 mm diameter pilot hole on the axis. "
)

_SCREW = (
    "Inside the bottom third of the tube there is a single-flight "
    "Archimedean screw on a central 8 mm diameter shaft. The shaft "
    "tapers from 0.8 mm diameter at the exit up to 8 mm diameter over "
    "the bottom 12 mm, then stays 8 mm. A 2 mm thick helical fin with a "
    "10 mm pitch winds around the shaft, with an outer fin radius of "
    "10.5 mm so it nearly touches the bore wall. The screw and fin "
    "occupy only the bottom one third of the tube height; the top two "
    "thirds of the bore is left completely open as a loose-powder "
    "storage volume. "
)

_GEAR = (
    "Around the outside of the tube, centred 83.33 mm up from the "
    "bottom, there is an external spur gear band that is 10 mm tall "
    "(face width) with 48 teeth, module 1, a 48 mm pitch diameter and a "
    "50 mm tip diameter. The 21 mm bore stays fully open straight "
    "through the gear band (the gear is an annular ring around the "
    "tube, it must not close off the bore). "
)

_THREAD = (
    "The top 25.4 mm (about one inch) of the outer wall carries a "
    "single-start right-hand external screw thread with a 4 mm pitch; "
    "the thread crest is flush with the 25 mm outer diameter (it never "
    "exceeds the 25 mm outer diameter so brackets can still slide over "
    "it) and the thread root is at 23 mm diameter. The filling (top) "
    "end is a smooth open cylinder with no top cap. "
)

PROMPTS = {
    "archimedes-auger-storage": (
        "A 250 mm tall storage auger for a powder doser. "
        + _COMMON + _FUNNEL + _TOP_CAP + _SCREW + _GEAR
    ),
    "archimedes-auger-storage-test": (
        "A 90 mm tall short bench-test storage auger for a powder doser, "
        "with no external gear. "
        + _COMMON + _FUNNEL + _TOP_CAP + _SCREW
    ),
    "threaded_archimedes-auger-storage": (
        "A 250 mm tall threaded storage auger for a powder doser. "
        + _COMMON + _FUNNEL + _SCREW + _GEAR + _THREAD
    ),
    "threaded_archimedes-auger-storage-test": (
        "A 90 mm tall short bench-test threaded storage auger for a "
        "powder doser, with no external gear. "
        + _COMMON + _FUNNEL + _SCREW + _THREAD
    ),
    "threaded-storage-cap": (
        "A hand-operated screw-on cap, like a tall bottle cap, that "
        "screws onto the threaded end of a storage auger tube. All "
        "dimensions in millimetres. The cap is a cylinder 31.7 mm "
        "outer diameter and 31 mm tall, closed at the top by a 6 mm "
        "thick disc and open at the bottom. The inside is a 25.4 mm "
        "long internal screw thread with a 4 mm pitch, a 25.7 mm major "
        "(crest-to-crest) diameter and a 23.7 mm minor diameter, sized "
        "to screw onto a 25 mm diameter externally threaded tube with a "
        "small hand-fit clearance. The top outer edge has a 1.5 mm "
        "chamfer."
    ),
}


def _save(name, op):
    os.makedirs(ART_DIR, exist_ok=True)
    os.makedirs(KCL_DIR, exist_ok=True)
    os.makedirs(STEP_DIR, exist_ok=True)
    with open(os.path.join(ART_DIR, name + ".op.json"), "w") as f:
        json.dump({k: v for k, v in op.items() if k != "outputs"}, f, indent=2)
    code = op.get("code")
    if code:
        with open(os.path.join(KCL_DIR, name + ".kcl"), "w") as f:
            f.write(code)
        print(f"  wrote kcl/{name}.kcl ({len(code)} chars)")
    outs = op.get("outputs") or {}
    import base64
    for key, b64 in outs.items():
        if not isinstance(b64, str):
            continue
        pad = "=" * (-len(b64) % 4)
        raw = base64.b64decode(b64 + pad)
        if key.endswith(".step"):
            with open(os.path.join(STEP_DIR, name + ".step"), "wb") as f:
                f.write(raw)
            print(f"  wrote step/{name}.step ({len(raw)} bytes)")
        elif key.endswith(".gltf") or key.endswith(".glb"):
            # glTF references external .bin buffers we do not keep; skip it.
            continue


def _poll(op_id, label="", budget_s=600):
    t0 = time.time()
    while time.time() - t0 < budget_s:
        op = _req("GET", f"/user/text-to-cad/{op_id}")
        st = op.get("status")
        print(f"  [{label}] {op_id} {st} (+{int(time.time()-t0)}s)")
        if st in ("completed", "failed"):
            return op
        time.sleep(8)
    return _req("GET", f"/user/text-to-cad/{op_id}")


def submit(names):
    ops = {}
    for name in names:
        prompt = PROMPTS[name]
        op = _req("POST", "/ai/text-to-cad/step?kcl=true", {"prompt": prompt})
        ops[name] = op["id"]
        print(f"submitted {name}: {op['id']}")
        time.sleep(2)
    results = {}
    for name, op_id in ops.items():
        op = _poll(op_id, label=name)
        results[name] = op
        if op.get("status") == "completed":
            _save(name, op)
        else:
            print(f"  {name} FAILED: {op.get('error')}")
    return results


def iterate(name, instruction):
    src_path = os.path.join(KCL_DIR, name + ".kcl")
    with open(src_path) as f:
        source = f.read()
    op = _req(
        "POST",
        "/ml/text-to-cad/iteration",
        {
            "original_source_code": source,
            "prompt": instruction,
            "source_ranges": [],
            "kcl": True,
        },
    )
    op = _poll(op["id"], label=name + " (iterate)")
    if op.get("status") == "completed":
        _save(name, op)
    else:
        print(f"  iterate {name} FAILED: {op.get('error')}")
    return op


def main(argv):
    if not argv:
        submit(list(PROMPTS))
    elif argv[0] == "--fetch":
        op = _req("GET", f"/user/text-to-cad/{argv[1]}")
        print(json.dumps({k: v for k, v in op.items() if k != "outputs"}, indent=2)[:2000])
    elif argv[0] == "--iterate":
        iterate(argv[1], argv[2])
    else:
        submit([a for a in argv if a in PROMPTS])


if __name__ == "__main__":
    main(sys.argv[1:])
