"""Dump station geometry (Sam frame at the station, actuator pins) for one design: run with cwd = the design folder."""
import json, sys, numpy as np
sys.path.insert(0, ".")
import layout as L
out = {}
S = L.station_frame()
for t in (0.0, 15.0, 30.0, 45.0, 50.0):
    Ms = L.sam_frame(S, t)
    C = L.electronics_frame(t, L.PARK_DROP)
    B, P = L.actuator_pins(t, L.PARK_DROP)
    out[str(t)] = dict(sam=Ms.tolist(), ec=C.tolist(), B=B.tolist(), P=P.tolist())
B0, P0 = L.actuator_pins(0.0, 0.0)
out["parked"] = dict(ec=L.electronics_frame(0.0, 0.0).tolist(), B=B0.tolist(), P=P0.tolist(), cradle=L.CRADLE_M.tolist())
out["HINGE_STATION"] = np.asarray(L.HINGE_STATION).tolist()
out["CRADLE_POST"] = list(L.CRADLE_POST)
out["LATCH_RAIL_POST"] = list(L.LATCH_RAIL_POST)
out["STATION_Y"] = float(L.STATION_Y)
for k in ("CRADLE_POST_S", "LATCH_POST_S"):
    if hasattr(L, k):
        out[k] = list(getattr(L, k))
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("ok", sys.argv[1])
