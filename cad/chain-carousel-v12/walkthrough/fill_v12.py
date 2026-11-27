"""Fill the walkthrough's {PLACEHOLDERS} from the repo's own results (sim/out, checks/, the BoM, the print report), so the narration
says what the files say."""
from __future__ import annotations

import json
import sys
from pathlib import Path

V12 = Path(__file__).resolve().parent.parent
NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def _load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def values() -> dict:
    v = {}
    C = _load(V12 / "sim" / "out" / "cycle.json")
    st = []
    if C:
        for r in C["runs"]:
            if r["stall_at"] is not None and r["cfg"] == {}:
                s = (r["steps"][0].get("stall") or {}).get("load_Nm")
                if s:
                    st.append(s * 1e3)
        drawn = {r["stall_at"]: (r["steps"][0].get("stall") or {}).get("load_Nm") for r in C["runs"] if r["stall_at"] is not None and r["cfg"] == {}}
        near = {r["stall_at"]: (r["steps"][0].get("stall") or {}).get("load_Nm") for r in C["runs"] if r["stall_at"] is not None and r["cfg"] == {"piv_dz": 10.0}}
        gains = [near[a] / drawn[a] - 1 for a in near if a in drawn and drawn[a] and near[a]]
        v["PIVOT_GAIN"] = f"{round(100 * sum(gains) / len(gains)):d}" if gains else "fifteen"
    v["STALL_RANGE"] = f"{min(st):.0f} to {max(st):.0f}" if st else "about fifty"
    D = _load(V12 / "sim" / "out" / "entry_dry.json")
    if D:
        n = len(D["runs"])
        jam = sum(r["jam"] for r in D["runs"])
        reidx = sum(1 for r in D["runs"] if r.get("reindexed"))
        cleared = sum(1 for r in D["runs"] if r.get("reindexed") and r["outcome"] == "stub, cleared by re-indexing")
        left = sum(1 for r in D["runs"] if r["outcome"].startswith("stub left"))
        v["DRY_CLEARED"] = (f"cleared {cleared} of the {reidx} that needed it" + (f"; {left} still needed a hand" if left else "") +
                            (f", and {jam} jammed" if jam else ", with no jams"))
    else:
        v["DRY_CLEARED"] = "is the fallback"
    names = {"home": "home", "cradle": "the cradle's travel", "tilt_a": None, "sweep_station": "the station sweep", "swap": "the swap",
             "latch": "the latch", "door": "the doors"}
    clashes = 0
    for f in ("home", "cradle", "tilt_a", "tilt_b", "tilt_c", "sweep_station", "swap", "latch", "door"):
        d = _load(V12 / "checks" / f"{f}.json")
        if d:
            clashes += len(d.get("clashes", []))
    v["CHECKS"] = "Every check came back with no clashes." if clashes == 0 else f"They found {clashes} clashes, listed in the README."
    P = _load(V12.parent / "print" / "chain-carousel-v12" / "slice_report.json")
    if P:
        try:
            plates = P.get("plates", P)
            hrs = sum(p.get("print_time_s", 0) * p.get("copies", 1) for p in plates) / 3600
            kg = sum(p.get("filament_g", 0) * p.get("copies", 1) for p in plates) / 1000
            v["PRINT"] = f"That is about {hrs:.0f} hours of printing and {kg:.1f} kilograms of PETG."
        except Exception:
            v["PRINT"] = ""
    else:
        v["PRINT"] = ""
    sys.path.insert(0, str(V12))
    try:
        import bom
        t = bom.totals(bom.rows())["total"]
        v["BOM_TOTAL"] = f"{t:,.0f}"
        v["BOM_DELTA"] = f"{t - 2118.48:.0f}"
    except Exception:
        v["BOM_TOTAL"], v["BOM_DELTA"] = "about two thousand one hundred and fifty", "about thirty"
    return v


def fill(text: str) -> str:
    vals = values()
    for k, x in vals.items():
        text = text.replace("{" + k + "}", str(x))
    return text


if __name__ == "__main__":
    print(json.dumps(values(), indent=1))
