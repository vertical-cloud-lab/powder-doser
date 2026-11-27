"""Write the simulated A/B example for plot_refill_tap.py.

One 0.5 g dose with the refill-tap endgame and one with ``refill_enabled
0`` (the stock endgame), on identical TipPlants from test_refill_tap.py
(assumed refill response -- an illustration of the rule, not a
prediction of the rig).  Writes example_refill_run.csv /
example_stock_run.csv next to main_trickle_refill.py and renders
example_refill_run.png from them.

Run:  python3 hardware/test-module/firmware/trickle_tap/sim/make_refill_example.py
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_refill_tap as trt                      # noqa: E402
from refill_tap import RefillTapDoser              # noqa: E402

FOLDER = Path(__file__).resolve().parent.parent
PLANT = {"seed": 21, "tip_g": 0.0, "tip_charge_frac": 0.15,
         "tip_cap_g": 0.012, "tap_frac": 0.065, "ff_rest": 0.30,
         "direct_frac": 0.4}


def run(p_over, name):
    doser, tap, clock = trt.make(RefillTapDoser, trt.TipPlant(**PLANT),
                                 p_over)
    res = doser.dose(0.5)
    path = FOLDER / name
    with open(path, "w") as f:
        f.write(trt.tt.TELEMETRY_HEADER + "\n")
        for row in doser.telemetry:
            f.write(row + "\n")
    print("{}: {!r}, {} refills -> {}".format(
        name, res, len(doser.refill_events), path.name))
    return path


def main():
    refill = run({}, "example_refill_run.csv")
    stock = run({"refill_enabled": False}, "example_stock_run.csv")
    subprocess.check_call([
        sys.executable, str(FOLDER / "plot_refill_tap.py"), str(refill),
        "--compare", str(stock), "--goal", "0.5",
        "--label", "refill-tap", "--compare-label", "stock endgame",
        "--out", str(FOLDER / "example_refill_run.png"),
        "--title", "Simulated 0.5 g dose, tap stage: refill-tap vs stock "
                   "endgame (same plant)"])


if __name__ == "__main__":
    main()
