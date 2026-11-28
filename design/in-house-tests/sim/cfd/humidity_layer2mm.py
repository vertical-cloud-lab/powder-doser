"""Test 6, case b with a 2 mm layer (3.85 g of the rice-flour-like powder in the Ø60 dish), still air,
3D on 5 mm cells. Same model as humidity_3d.case_b; only the sample mass (and so the layer) changes.
Writes humidity_3d_h5.0mm_layer2mm.json."""
import json
import numpy as np
import humidity_3d as h3

h3.SAMPLE_MASS = h3.RHO_B * np.pi * h3.DISH_R ** 2 * 0.002
r = h3.case_b(0.005)
ideal = h3.layer_only(0.002, 10, 6 * 3600.0)
out = {k: v for k, v in r.items() if k != "series"}
out["sample_mass_g"] = h3.SAMPLE_MASS * 1e3
out["series"] = r["series"]
json.dump(out, open("humidity_3d_h5.0mm_layer2mm.json", "w"), indent=1)
print({k: out[k] for k in ("layer_thickness_mm", "sample_mass_g", "uptake_t50_s", "uptake_t95_s",
                           "ideal_uptake_t50_s", "ideal_uptake_t95_s")}, out["sample_surface"], out["sensor"])
