# Checks

| Script | What it checks |
|---|---|
| `fidelity.py` | A recreated part against the Fusion 360 / PR #170 STEP it duplicates (same frame, no registration): IoU, volume error, bounding-box deltas, two-way surface deviation |
| `interference.py` | Every pair of placed parts over the tilt range, both layouts, plus every screw and nut against the parts it passes through ([write-up](results/interference.md)) |
| `interference_reference.py` | The flagged pairs again on PR #170's own files, to separate inherited overlaps from ones the recreation introduced |
| `electronics_clearance.py` | The PCB and its holder against every placed part over the tilt range |
| `cap_thread.py` | Auger-cap overlap against the cap's turn on the thread (sets `lib.frames.CAP_TURN_DEG`) |
| `nozzle_clearance.py`, `clearance_compare.py` | How close a cup of a given diameter can come to the outlet, per layout and tilt |
| `printability.py` | Watertightness, wall thickness, best orientation and support area of the printed parts' STLs |
| `mounting_plate_holes.py`, `pcb_checks.py` | Hole positions on the mounting plate; the PCB model against its Gerbers |
| `fetch_reference.py`, `parts_index.py` | Fetch PR #170's files into `STEP/reference/`; load and place parts for the checks |

Results are written to `checks/results/`.
