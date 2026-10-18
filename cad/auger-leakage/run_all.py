"""Run the whole leakage study, at most two simulations at a time (about 80 min of CPU in total).

    python run_all.py            # skips runs whose out/<tag>.json already exists
    python run_all.py --list     # print the job list

Branch runs start from out/prefix.npz, so the prefix runs first.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
LOGS = os.path.join(OUT, "logs")
MAXP = 2

VIB = "--transit vib --transit-s 3 --vib-g 1.5 --vib-hz 25"
AVIB = "--transit avib --transit-s 3 --vib-g 2.0 --vib-hz 25"
AVIB5 = "--transit avib --transit-s 3 --vib-g 1.0 --vib-hz 5"
PAT = "--transit pat --transit-s 2"
JOBS = [
    # dose 2 rev at 30 deg world tilt, motor off 0.3 s; and at 15 deg with no wait (the afterflow case)
    ("prefix", "prefix --record"),
    *[(f"prefix_s{k}", f"prefix --seed {k}") for k in (1, 2)],
    ("prefix15", "prefix --dose-tilt 15 --stop 0 --name prefix15 --record"),
    *[(f"prefix15_s{k}", f"prefix --dose-tilt 15 --stop 0 --seed {k} --name prefix15_s{k}") for k in (1, 2)],
    # 1. rest pitch after a 30 deg dose: return to nozzle-up alpha, dwell, one paternoster index (real transit motion)
    *[(f"ret_a{a}", f"branch --alpha {a} --protocol return {PAT} --record --tag ret_a{a}") for a in (0, 5, 10, 15)],
    # 1b. stress tests after the return: vertical vibration (level module) and axial vibration (a knock along the auger)
    ("vib_a0_s0", f"branch --alpha 0 --protocol return {VIB} --record --tag vib_a0_s0"),
    ("vib_a5_s0", f"branch --alpha 5 --protocol return {VIB} --tag vib_a5_s0"),
    *[(f"avib_a{a}_s0", f"branch --alpha {a} --protocol return {AVIB} --record --tag avib_a{a}_s0") for a in (0, 5, 10, 15)],
    # 1c. rest pitch after a 15 deg dose with no wait: the afterflow is still running when the module tilts back
    *[(f"r15_a{a}", f"branch --prefix prefix15 --alpha {a} --protocol return {PAT} --record --tag r15_a{a}") for a in (0, 5, 10, 15)],
    ("r15hold_a0", f"branch --prefix prefix15 --alpha 0 --hold 0.6 --protocol return {PAT} --tag r15hold_a0"),
    # 3. v2 laps from a primed auger, both directions
    ("v2_a0_fwd", "v2lap --alpha 0 --dir fwd --record --tag v2_a0_fwd"),
    ("v2_a0_rev", "v2lap --alpha 0 --dir rev --record --tag v2_a0_rev"),
    *[(f"r15_a{a}_s{k}", f"branch --prefix prefix15_s{k} --alpha {a} --protocol return {PAT} --tag r15_a{a}_s{k}")
      for k in (1, 2) for a in (0, 5, 10, 15)],
    # 2. post-dose protocols after the 15 deg dose: reverse at the dose tilt, or return first and reverse at rest
    *[(f"r15revdose_a10_R{x}", f"branch --prefix prefix15 --alpha 10 --protocol revdose --R {x} {PAT} --tag r15revdose_a10_R{x}")
      for x in (0.25, 0.5, 1)],
    *[(f"r15retrev_a10_R{x}", f"branch --prefix prefix15 --alpha 10 --protocol returnrev --R {x} {PAT} --record --tag r15retrev_a10_R{x}")
      for x in (0.25, 0.5, 1, 2)],
    ("r15revdose_a0_R0.5", f"branch --prefix prefix15 --alpha 0 --protocol revdose --R 0.5 {PAT} --tag r15revdose_a0_R0.5"),
    ("r15retrev_a0_R0.5", f"branch --prefix prefix15 --alpha 0 --protocol returnrev --R 0.5 {PAT} --tag r15retrev_a0_R0.5"),
    ("v2_a10_fwd", "v2lap --alpha 10 --dir fwd --record --tag v2_a10_fwd"),
    ("v2_a10_rev", "v2lap --alpha 10 --dir rev --record --tag v2_a10_rev"),
    ("v2_a0_fwd_s1", "v2lap --alpha 0 --dir fwd --seed 1 --tag v2_a0_fwd_s1"),
    ("v2_a0_rev_s1", "v2lap --alpha 0 --dir rev --seed 1 --tag v2_a0_rev_s1"),
    # low-frequency axial shaking (5 Hz, up to 1 g: 10 mm of travel) after the 30 deg dose
    *[(f"avib5_a{a}", f"branch --alpha {a} --protocol return {AVIB5} --tag avib5_a{a}") for a in (0, 10)],
    # 4. storage: after a dose, return, then solenoid taps with the motor off; and from a primed (settled) auger
    *[(f"taps_a{a}", f"branch --alpha {a} --protocol return --transit taps --tag taps_a{a}") for a in (0, 10)],
    *[(f"store_a{a}", f"store --alpha {a} --seconds 2 --tag store_a{a}") for a in (0, 10)],
]


def main():
    if "--list" in sys.argv:
        for t, c in JOBS:
            print(f"{t:20s} python leak_sim.py {c}")
        return
    os.makedirs(LOGS, exist_ok=True)
    todo = [(t, c) for t, c in JOBS if not os.path.exists(os.path.join(OUT, f"{t}.json"))]
    for t, c in list(todo):        # already running (started by hand)?
        if subprocess.run(["pgrep", "-f", f"leak_sim.py {c.split(' --record')[0]}"], capture_output=True).returncode == 0:
            todo.remove((t, c))
    running = {}
    while todo or running:
        for t, p in list(running.items()):
            if p.poll() is not None:
                print(f"{time.strftime('%H:%M:%S')} done {t} (rc {p.returncode})", flush=True)
                del running[t]
        busy = int(subprocess.run(["pgrep", "-fc", "leak_sim.py"], capture_output=True, text=True).stdout.strip() or 0)
        while todo and busy < MAXP:
            t, c = todo[0]
            def ready(cc):
                if not cc.startswith("branch"):
                    return True
                if "--prefix " in cc:
                    p = cc.split("--prefix ")[1].split()[0]
                else:
                    k = cc.split("--seed ")[1].split()[0] if "--seed " in cc else "0"
                    p = "prefix" if k == "0" else f"prefix_s{k}"
                return os.path.exists(os.path.join(OUT, p + ".npz"))
            if not ready(c):
                nxt = next(((tt, cc) for tt, cc in todo if ready(cc)), None)
                if nxt is None:
                    break
                t, c = nxt
            todo.remove((t, c))
            log = open(os.path.join(LOGS, f"{t}.log"), "w")
            running[t] = subprocess.Popen([sys.executable, os.path.join(HERE, "leak_sim.py"), *c.split()],
                                          stdout=log, stderr=subprocess.STDOUT, cwd=HERE)
            print(f"{time.strftime('%H:%M:%S')} start {t}", flush=True)
            busy += 1
        time.sleep(5)


if __name__ == "__main__":
    main()
