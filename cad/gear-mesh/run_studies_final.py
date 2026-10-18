"""Second pass: the station as built in both designs ("final": stub pins at (32, -34), 32.25 mm centre distance).

    python run_studies_final.py
"""
import json

import mesh_mujoco as M

if __name__ == "__main__":
    M.stall_sweep(configs=["final"], name="stall_sweep_final")
    M.runout_sweep(configs=("final",), name="runout_sweep_final")
    M.speed_sweep(configs=("final",), ecc=0.05, pitch_err=0.0006, name="speed_sweep_final")
    rows = []
    for phase in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        for seek in (0.0, 0.25):
            r, _ = M.engage("final", 0.0, phase, seek, tag=f"engage_final_p{phase:g}_s{seek:g}")
            rows.append(r)
            print(r, flush=True)
    (M.OUT / "engage_final.json").write_text(json.dumps(rows, indent=1))
