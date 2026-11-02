#!/usr/bin/env python3
"""Check whether a sketch outline in a public Onshape part studio fits a square bed.

Needs no Onshape API keys: the feature list of a *public* document can be read
anonymously, but parts, bounding boxes and STL export cannot (they return 401).
It takes the outline from one sketch's non-construction lines and circles,
rotates it in 0.1 deg steps, and reports the smallest square that holds it.

    python bed_fit_check.py                      # the Baseplate from issue #193
    python bed_fit_check.py DID WID EID "Sketch 1" 180

Run on 2026-11-02 against the Baseplate (document modified 2026-11-01): the
outline needs a 190.0 mm square at every angle, so it does not fit the A1 mini's
180 x 180 mm plate.
"""
import json
import math
import sys
import urllib.request

DID, WID, EID = "68b18e694d8672d95f496279", "ca6615cd1f43e41c93dbf2f5", "9f7a9b5e682bc05529f15125"
SKETCH, BED_MM = "Sketch 1", 180.0


def outline_points(features, sketch_name):
    pts = []
    for ft in features["features"]:
        msg = ft.get("message", ft)
        if msg.get("name") != sketch_name:
            continue
        for ent in msg.get("entities", []):
            e = ent.get("message", ent)
            if e.get("isConstruction"):
                continue
            g = e.get("geometry", {})
            g = g.get("message", g)
            if "pntX" in g and "dirX" in g:  # line segment
                for t in (e.get("startParam"), e.get("endParam")):
                    pts.append((g["pntX"] + g["dirX"] * t, g["pntY"] + g["dirY"] * t))
            elif "xCenter" in g and "radius" in g:  # circle or arc, sampled conservatively
                r = g["radius"]
                pts += [(g["xCenter"] + r * math.cos(a * math.pi / 36),
                         g["yCenter"] + r * math.sin(a * math.pi / 36)) for a in range(72)]
    return pts


def smallest_square(pts):
    best = None
    for d10 in range(900):
        t = math.radians(d10 / 10)
        xs = [x * math.cos(t) - y * math.sin(t) for x, y in pts]
        ys = [x * math.sin(t) + y * math.cos(t) for x, y in pts]
        w, h = (max(xs) - min(xs)) * 1000, (max(ys) - min(ys)) * 1000
        if best is None or max(w, h) < best[0]:
            best = (max(w, h), d10 / 10, w, h)
    return best


if __name__ == "__main__":
    if len(sys.argv) == 6:
        DID, WID, EID, SKETCH, BED_MM = *sys.argv[1:5], float(sys.argv[5])
    url = f"https://cad.onshape.com/api/v10/partstudios/d/{DID}/w/{WID}/e/{EID}/features"
    with urllib.request.urlopen(url, timeout=60) as r:
        feats = json.load(r)
    pts = outline_points(feats, SKETCH)
    if not pts:
        sys.exit(f"no geometry found in {SKETCH!r}")
    side, angle, w, h = smallest_square(pts)
    print(f"{SKETCH}: smallest enclosing square {side:.1f} mm at {angle:.1f} deg ({w:.1f} x {h:.1f} mm)")
    print(f"fits a {BED_MM:.0f} x {BED_MM:.0f} mm bed: {side <= BED_MM}")
