"""Render the assembly + SOP video of every apparatus and join them into one MP4 with chapters.

    xvfb-run -a python make_video.py [--jobs 3] [key ...]

Per test: a title card, the assembly (step by step), the soldering of the FC-1 board (test 10 only)
and the SOP. Segments go to /tmp/iht-video/<key>.mp4 and are joined into
in_house_tests_assembly_sop.mp4; chapters.txt holds the YouTube chapter list.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path("/tmp/iht-video")
FINAL = HERE / "in_house_tests_assembly_sop.mp4"

TESTS = [
    ("t01_heap", "1. Heap angle of repose", "Tier 1. Angle of repose, avalanches and heap density from a pile the doser builds",
     ["Checked against ISO 4324 (fixed-base cone)", "About 1 g a pour, returned to the jar"]),
    ("t02_density", "2. Bulk and tapped density", "Tier 1. Bulk and tapped density, Hausner ratio, compaction curve",
     ["Checked against ASTM B212 and B527 (3 mm drop)", "3-8 g, returned"]),
    ("t03_tilt", "3. Tilting plate", "Tier 1. Wall friction on PLA, steel and glass at 70-450 Pa; layer start angle",
     ["Checked against Jenike / Schulze wall friction", "About 1 g, returned"]),
    ("t04_psd", "4. PSD and shape from images", "Tier 1. d10, d50, d90, aspect ratio, circularity",
     ["Checked against sieving and laser diffraction", "10-50 mg"]),
    ("t05_orifice", "5. Orifice cup", "Tier 2. Flow rate vs orifice; smallest orifice that flows -> low-stress strength",
     ["Checked against Hall and Carney funnels", "3-5 g, returned"]),
    ("t06_humidity", "6. Humidity chambers", "Tier 2. Water uptake vs RH; dosing before and after",
     ["Checked against loss on drying and DVS", "2-3 g per chamber"]),
    ("t07_drum", "7. Rotating drum", "Tier 2. Dynamic angle, avalanches, cohesive index, on the doser's own stepper",
     ["Checked against GranuDrum / Revolution", "About 7.5 mL"]),
    ("t08_ucs", "8. Unconfined strength", "Tier 3. Strength at 0.2-2 kPa: a low-stress flow function",
     ["Checked against an outsourced shear cell", "5-10 g"]),
    ("t09_spread", "9. Blade spreading", "Tier 3. Coverage, layer packing, streaks on a coupon",
     ["No standard: compared with DEM run 7", "0.2-0.5 g a layer"]),
    ("t10_faraday", "10. Faraday cup", "Tier 3. Charge per mass of the dosed powder",
     ["Custom FC-1 charge amplifier (femtoamp op-amp)", "0.5-1 g"]),
]


def render_one(key: str) -> dict:
    import engine
    from assembly_anim import assembly_segment
    from sop_anim import SOPS
    OUT.mkdir(parents=True, exist_ok=True)
    meta = next(t for t in TESTS if t[0] == key)
    path = OUT / f"{key}.mp4"
    t0 = time.time()
    w = engine.Writer(path)
    card = engine.title_card(meta[1], meta[2], meta[3])
    w.add(card, repeat=int(2.5 * engine.FPS))
    n0 = w.n
    assembly_segment(w, key)
    n1 = w.n
    if key == "t10_faraday":
        from solder_anim import solder_segment
        solder_segment(w)
    n2 = w.n
    SOPS[key](w)
    n3 = w.n
    w.close()
    return {"key": key, "frames": w.n, "seconds": round(w.n / engine.FPS, 1), "assembly_start_s": n0 / engine.FPS,
            "solder_start_s": n1 / engine.FPS if n2 > n1 else None, "sop_start_s": n2 / engine.FPS,
            "render_s": round(time.time() - t0, 1)}


def intro(path: Path):
    import engine
    w = engine.Writer(path)
    card = engine.title_card("In-house powder tests on the doser", "Ten apparatuses: assembly and SOP, as designed (not built)",
                             ["Teal: printed parts (A1 mini, PLA)   Purple: bought parts   Grey: the doser and balance",
                              "Captions follow the SOPs in design/in-house-tests/software/sop/",
                              "Powder is drawn from DEM trajectories where they exist, otherwise as an illustration"])
    w.add(card, repeat=int(5 * engine.FPS))
    w.close()


def main():
    args = sys.argv[1:]
    jobs = 3
    if "--jobs" in args:
        jobs = int(args[args.index("--jobs") + 1])
        args = [a for a in args if a not in ("--jobs", str(jobs))]
    keys = args or [t[0] for t in TESTS]
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool(jobs) as pool:
        res = pool.map(render_one, keys)
    meta_path = HERE / "segments.json"
    old = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    for r in res:
        old[r["key"]] = r
    meta_path.write_text(json.dumps(old, indent=1) + "\n")
    # join everything that exists, in order
    intro(OUT / "t00_intro.mp4")
    order = ["t00_intro"] + [t[0] for t in TESTS]
    lst = OUT / "concat.txt"
    lst.write_text("".join(f"file '{OUT / (k + '.mp4')}'\n" for k in order if (OUT / f"{k}.mp4").exists()))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(FINAL)], check=True)
    # chapters
    t = 5.0
    lines = ["0:00 Intro"]
    for k, title, *_ in TESTS:
        if k not in old:
            continue
        mm, ss = divmod(int(t), 60)
        lines.append(f"{mm}:{ss:02d} {title}")
        t += old[k]["seconds"]
    (HERE / "chapters.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("total", round(t, 1), "s ->", FINAL)


if __name__ == "__main__":
    main()
