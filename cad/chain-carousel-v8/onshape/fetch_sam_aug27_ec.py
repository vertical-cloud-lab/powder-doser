"""Export Sam's Aug 27 electronics carriage Part Studio (his "first design", issue #128 comment 5441933422) as STEP, for
v8's EC (Sam, PR #185, 2026-11-12: "design a new electronics carriage more similar to the first design"). Read-only; every
call is logged in api_calls.jsonl.

    python fetch_sam_aug27_ec.py
"""
from __future__ import annotations

import time
from pathlib import Path

from client import Onshape

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "reference"
DID, WID, EID = "fc58e8f075dd5981b4307d7e", "8916fbe4fc097631f09c9941", "0c17210877afc0cc581b35cc"


def main() -> None:
    os_ = Onshape(budget=12, run="sam-aug27-ec-export")
    OUT.mkdir(exist_ok=True)
    body = {"formatName": "STEP", "storeInDocument": False, "flattenAssemblies": False, "yAxisIsUp": False}
    tr = os_.post(f"/partstudios/d/{DID}/w/{WID}/e/{EID}/translations", json=body)
    st = tr
    for _ in range(8):
        time.sleep(5)
        st = os_.get(f"/translations/{tr['id']}")
        if st["requestState"] in ("DONE", "FAILED"):
            break
    if st["requestState"] != "DONE":
        raise RuntimeError(f"translation {st['requestState']}: {st.get('failureReason')}")
    r = os_.get(f"/documents/d/{DID}/externaldata/{st['resultExternalDataIds'][0]}", raw=True,
                headers={"Accept": "application/octet-stream"})
    (OUT / "sam-aug27-electronics-carriage.step").write_bytes(r.content)
    print("sam-aug27-electronics-carriage.step", len(r.content), "bytes; calls:", os_.calls)


if __name__ == "__main__":
    main()
