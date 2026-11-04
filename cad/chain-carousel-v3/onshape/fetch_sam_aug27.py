"""Export Sam's Aug 27 Part Studios (issue #128, 2026-08-27 comment) as STEP: the earlier electronics carriage with the
kinematic couplings, the auger carriage, and the frame carriage. Read-only; each call is logged in api_calls.jsonl.

    python fetch_sam_aug27.py [--elements]      # --elements lists each document's tabs first (1 call each)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from client import Onshape

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "reference"
DOCS = {   # Sam's links in https://github.com/vertical-cloud-lab/powder-doser/issues/128#issuecomment-5441933422
    "sam-aug27-electronics-carriage": ("fc58e8f075dd5981b4307d7e", "8916fbe4fc097631f09c9941", "0c17210877afc0cc581b35cc"),
    "sam-aug27-auger-carriage": ("e1673c561e8b44d71565c455", "423995042d8b43e853a9d98c", "a10aeb524bcd319ef9e44e32"),
    "sam-aug27-frame-carriage": ("f066bfa5549b8ef650963fab", "03471c180aa36007209ec6d7", "7cf1dc99ca88a8bf33d6d4b3"),
}


def main() -> None:
    os_ = Onshape(budget=30, run="sam-aug27-export")
    OUT.mkdir(exist_ok=True)
    meta = {}
    for name, (did, wid, eid) in DOCS.items():
        if "--elements" in sys.argv:
            els = os_.get(f"/documents/d/{did}/w/{wid}/elements")
            meta[name] = [{"id": e["id"], "name": e["name"], "type": e.get("elementType")} for e in els]
            print(name, json.dumps(meta[name], indent=1))
            kind = next((e.get("elementType") for e in els if e["id"] == eid), "PARTSTUDIO")
        else:
            kind = "PARTSTUDIO"
        base = "partstudios" if kind == "PARTSTUDIO" else "assemblies"
        body = {"formatName": "STEP", "storeInDocument": False, "flattenAssemblies": False, "yAxisIsUp": False}
        tr = os_.post(f"/{base}/d/{did}/w/{wid}/e/{eid}/translations", json=body)
        tid = tr["id"]
        for _ in range(20):
            time.sleep(4)
            st = os_.get(f"/translations/{tid}")
            if st["requestState"] in ("DONE", "FAILED"):
                break
        if st["requestState"] != "DONE":
            raise RuntimeError(f"{name}: translation {st['requestState']}: {st.get('failureReason')}")
        fid = st["resultExternalDataIds"][0]
        r = os_.get(f"/documents/d/{did}/externaldata/{fid}", raw=True, headers={"Accept": "application/octet-stream"})
        (OUT / f"{name}.step").write_bytes(r.content)
        print(name, kind, len(r.content), "bytes")
    if meta:
        (HERE / "sam_aug27_elements.json").write_text(json.dumps(meta, indent=1))
    print("calls this run:", os_.calls)


if __name__ == "__main__":
    main()
