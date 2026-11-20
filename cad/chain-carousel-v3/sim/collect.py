"""Gather the v3 station sims' JSON results into sim/results.json (run after dock_statics.py and station_mj.py)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
out = {"note": "Simulated, not built: predictions. See README.md for what each run models."}
st = json.loads((R / "statics.json").read_text())
out["masses"] = {k: v for k, v in st["masses"].items() if not k.endswith("parts")}
out["run1_dock_vs_tilt"] = st["dock"]
out["run2_seat_magnets"] = {k: v for k, v in st["magnets"].items() if k != "curve"}
out["run2_seat_magnets"]["curve"] = st["magnets"]["curve"]
for tag in ("asdrawn", "fixed", "fixed_yfree", "fixed_yfree_cycle"):
    f = R / f"station_mj_{tag}.json"
    if f.exists():
        out[f"run3_{tag}"] = json.loads(f.read_text())
out["run4_door"] = st["door"]
out["run5_latch"] = st["latch"]
v4 = HERE.parent.parent / "chain-carousel-v4" / "sim" / "results" / "dock_v4.json"
if v4.exists():
    out["run6_v4"] = json.loads(v4.read_text())
(HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
print("wrote", HERE / "results.json")
