"""Copy the small, reviewable outputs of finished runs into sim/dem/results/.

Raw particle dumps (hundreds of MB per case) stay out of git; this keeps,
per case: the run config, the generated LIGGGHTS input, the case metadata,
the outflow time series and the dosing metrics. Benchmark results, figures
and movies are copied alongside.

    python export_results.py --runs /tmp/dem/runs --bench /tmp/dem/bench --frames /tmp/dem/frames
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import metrics  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="/tmp/dem/runs")
    ap.add_argument("--bench", default="/tmp/dem/bench")
    ap.add_argument("--frames", default="/tmp/dem/frames")
    ap.add_argument("--out", default=os.path.join(HERE, "results"))
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "cases"), exist_ok=True)
    rows = []
    for case in sorted(glob.glob(os.path.join(a.runs, "*", "case.json"))):
        d = os.path.dirname(case)
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "outflow.txt")):
            continue
        dst = os.path.join(a.out, "cases", name)
        os.makedirs(dst, exist_ok=True)
        meta = json.load(open(case))
        json.dump(meta["cfg"], open(os.path.join(dst, "config.json"), "w"), indent=1)
        shutil.copy(case, os.path.join(dst, "case.json"))
        shutil.copy(os.path.join(d, "outflow.txt"), os.path.join(dst, "outflow.txt"))
        if os.path.exists(os.path.join(d, "outflow_corrected.txt")):
            shutil.copy(os.path.join(d, "outflow_corrected.txt"), os.path.join(dst, "outflow_corrected.txt"))
        if os.path.exists(os.path.join(d, "in.auger")):
            shutil.copy(os.path.join(d, "in.auger"), os.path.join(dst, "in.auger"))
        try:
            r = metrics(d)
            r["finished"] = os.path.exists(os.path.join(d, "done"))
            json.dump(r, open(os.path.join(dst, "metrics.json"), "w"), indent=1)
            rows.append(r)
        except Exception as e:  # noqa: BLE001
            print("metrics failed", name, e)
    with open(os.path.join(a.out, "metrics.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    b = os.path.join(a.bench, "bench_results.jsonl")
    if os.path.exists(b):
        shutil.copy(b, os.path.join(a.out, "bench_results.jsonl"))
    for ext in ("gif", "mp4"):
        for f in glob.glob(os.path.join(a.frames, f"*.{ext}")):
            shutil.copy(f, os.path.join(a.out, os.path.basename(f)))
    print(f"exported {len(rows)} cases to {a.out}")


if __name__ == "__main__":
    main()
