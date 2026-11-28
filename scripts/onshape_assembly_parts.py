#!/usr/bin/env python3
"""Download every part the #193 Onshape assembly uses, and draw them all.

    python scripts/onshape_assembly_parts.py cad/onshape-193 [--max-calls N] [--render-only]

#193 lists one Onshape document per doser part, and scripts/onshape_export.py exports those
(STLs under SNAPSHOT_DIR/<doc>/<element>/stl/). The assembly ("Assembly 1") also pulls parts
from documents #193 doesn't list: the auger cap, tap collar base, solenoid and stepper motor
from "assembly_current.step", and the MG-996R servos from "Github parts". This script:

1. reads the assembly definition with the keys (1 counted call) and saves it as
   SNAPSHOT_DIR/assembly/assembly-1/definition.json (ids, part names, placements);
2. for every part instance, finds the STL already exported from the #193 Part Studio, or else
   exports that one part at the document version the assembly references, to
   SNAPSHOT_DIR/assembly/parts/<name>.stl (2 counted calls per part: a 307, then the file);
3. writes SNAPSHOT_DIR/assembly/parts.json (every part, how many, which file, printed or bought);
4. draws SNAPSHOT_DIR/assembly/all-parts.png (one tile per distinct part, with its count) and
   SNAPSHOT_DIR/assembly/assembly-from-stl.png (the STLs placed with the assembly's transforms).

The #193 Part Studios are the latest workspace versions. The assembly references saved
versions, so a part edited since its version was saved can sit slightly off in the render.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from onshape_export import CapReached, Onshape, OutOfBudget, describe, now, slug  # noqa: E402

ASM = ("f866631c78fbefd61e6856e4", "043fe020d0194e41cea13bc2", "3156bac055c13d8160e229b4")
# Bought, not printed: matched on the instance name.
BOUGHT = re.compile(r"MG-996R|solenoid_coil|solenoid_plunger|solenoid_yoke|stepper_motor|wood", re.I)
LABEL = {
    "68b18e694d8672d95f496279": "Baseplate",
    "53e9cce7f09a50f89c120028": "Mounting plate",
    "51aa3e7d16cc046d79714a7a": "Auger",
    "5e6db88e8a8d5328b172ba6d": "Auger clip (Bracket Recreation)",
    "b0b9aed3e11591e566530a68": "Tap collar (tapcollar)",
    "35ecacf511109e3b823b3ed0": "Servo pinion (Complete Servo Pinion)",
    "0401d55bca2deb006cc69926": "Stepper pinion (Stepper Pinion)",
    "6cb5182c1e0e0193cfea81bb": "Stand bracket (back)",
    "659ee3322c5c9c9ce8146b43": "Wood leg",
    "862c1d747b6c2d4728dee1aa": "MG-996R servo",
}
SIDES = {"cbbebd3d1064640d9bce4c7f": "Stand bracket (right side)", "7c0d89ca7e487cdf4a761fd7": "Stand bracket (left side)"}


def snapshot_stls(snap):
    """(did, eid) -> the STL files exported from that #193 Part Studio (workspace)."""
    m = json.loads((snap / "manifest.json").read_text())
    out = {}
    for d in m["documents"]:
        for e in d["elements"]:
            if e.get("dir"):
                files = sorted((snap / e["dir"] / "stl").glob("*.stl"))
                if files:
                    out[(d["did"], e["id"])] = files
    return out


def label(inst):
    if inst["elementId"] in SIDES:
        return SIDES[inst["elementId"]]
    if inst["documentId"] in LABEL:
        name = LABEL[inst["documentId"]]
        if inst["documentId"] == "862c1d747b6c2d4728dee1aa":
            name = {"JFH": "MG-996R servo", "JFD": "MG-996R output spline"}.get(inst["partId"], name)
        return name
    return re.sub(r"\s*<\d+>$", "", inst["name"])


def fetch(snap, max_calls):
    os_ = Onshape(max_calls)
    did, wid, eid = ASM
    asm = os_.call("GET", f"assemblies/d/{did}/w/{wid}/e/{eid}", params={"includeMateFeatures": "false"}).json()
    adir = snap / "assembly" / "assembly-1"
    (adir / "definition.json").write_text(json.dumps(asm, indent=1, sort_keys=True) + "\n")
    have = snapshot_stls(snap)
    occ = {o["path"][-1]: o for o in asm["rootAssembly"]["occurrences"] if len(o["path"]) == 1}
    parts, log = {}, {"started_utc": now(), "assembly": "Assembly / Assembly 1 (#193)", "parts": []}
    try:
        for inst in asm["rootAssembly"]["instances"]:
            if inst.get("type") != "Part" or inst.get("suppressed"):
                continue
            key = (inst["documentId"], inst["elementId"], inst["partId"])
            if key not in parts:
                files = have.get(key[:2])
                if files and len(files) == 1:
                    f, source = files[0], "#193 Part Studio, workspace (scripts/onshape_export.py)"
                else:
                    base = slug(inst["name"].split("<")[0])
                    # Two parts of one Part Studio can share a name (the MG-996R's): add the part id.
                    if sum(i.get("type") == "Part" and i["name"].split("<")[0] == inst["name"].split("<")[0]
                           and (i["documentId"], i["elementId"], i["partId"]) != key
                           for i in asm["rootAssembly"]["instances"]):
                        base += f"-{slug(inst['partId'])}"
                    f = snap / "assembly" / "parts" / f"{base}.stl"
                    if not f.exists():
                        f.parent.mkdir(parents=True, exist_ok=True)
                        path = (f"parts/d/{key[0]}/v/{inst['documentVersion']}/e/{key[1]}/partid/"
                                f"{inst['partId']}/stl")
                        r = os_.download(path, params={"mode": "binary", "units": "millimeter"})
                        f.write_bytes(r.content)
                    source = "this script: the one part, at the document version the assembly references"
                _, info = describe(f.read_bytes())
                parts[key] = {"label": label(inst), "onshape_name": re.sub(r"\s*<\d+>$", "", inst["name"]),
                              "documentId": key[0], "elementId": key[1], "partId": key[2],
                              "documentVersion": inst.get("documentVersion"), "file": str(f.relative_to(snap)),
                              "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "source": source,
                              "kind": ("bought" if BOUGHT.search(inst["name"]) else
                                       "wood" if label(inst) == "Wood leg" else "printed"),
                              "count": 0, "instances": [], **info}
            parts[key]["count"] += 1
            parts[key]["instances"].append({"name": inst["name"], "transform": occ[inst["id"]]["transform"]})
    except (CapReached, OutOfBudget) as ex:
        log["stopped"] = f"{type(ex).__name__}: {ex}"
        print("stopped:", log["stopped"])
    log.update(finished_utc=now(), calls_counted=os_.counted, calls=os_.log, parts=list(parts.values()))
    (snap / "assembly" / "parts.json").write_text(json.dumps(log, indent=1) + "\n")
    print(f"{len(parts)} distinct parts, {sum(p['count'] for p in parts.values())} instances, "
          f"{os_.counted} counted calls")
    return log


def snap_view(meshes, size, view=(1, -1, 1), parallel=True):
    """Render (mesh, rgb) pairs offscreen with VTK and return the image as an RGB array."""
    import pyvista as pv

    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    for m, color in meshes:
        pl.add_mesh(pv.wrap(m), color=color, smooth_shading=False, specular=0.15, ambient=0.25)
    pl.view_vector(view, viewup=(0, 0, 1))
    if parallel:
        pl.enable_parallel_projection()
    pl.reset_camera()
    pl.camera.zoom(1.08)
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def placed(m, transform):
    T = np.array(transform, dtype=float).reshape(4, 4)
    T[:3, 3] *= 1000  # Onshape's transforms are in metres, the STLs in mm
    m = m.copy()
    m.apply_transform(T)
    return m


def render(snap):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import trimesh

    log = json.loads((snap / "assembly" / "parts.json").read_text())
    order = ["printed", "wood", "bought"]
    parts = sorted(log["parts"], key=lambda p: (order.index(p["kind"]), -np.prod(p["extent_mm"])))
    cmap = plt.get_cmap("tab20")
    meshes = {}
    for i, p in enumerate(parts):
        meshes[p["file"]] = trimesh.load(snap / p["file"], file_type="stl", force="mesh")
        p["color"] = {"bought": (0.55, 0.55, 0.58), "wood": (0.78, 0.6, 0.38)}.get(p["kind"], cmap(i % 20)[:3])

    # 1. every distinct part, each scaled to fit its tile, with its count and size
    cols = 6
    rows = -(-len(parts) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.0 * cols, 3.2 * rows))
    for ax in axes.flat:
        ax.axis("off")
    for ax, p in zip(axes.flat, parts):
        ax.imshow(snap_view([(meshes[p["file"]], p["color"])], (420, 380)))
        ext = " × ".join(f"{v:.0f}" for v in p["extent_mm"])
        tag = "" if p["kind"] == "printed" else f" ({p['kind']})"
        ax.set_title(f"{p['label']}\n×{p['count']}{tag}   {ext} mm", fontsize=9,
                     color="black" if p["kind"] == "printed" else "0.35",
                     fontweight="bold" if p["kind"] == "printed" else "normal")
    n = {k: sum(p["count"] for p in parts if p["kind"] == k) for k in order}
    fig.suptitle(f"Every part in the #193 Onshape assembly, drawn from the downloaded STLs: {len(parts)} distinct, "
                 f"{sum(n.values())} in all ({n['printed']} printed, {n['wood']} wood, {n['bought']} bought)\n"
                 "Each tile is scaled to fit; sizes are x × y × z in the part's own frame", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(snap / "assembly" / "all-parts.png", dpi=80)
    plt.close(fig)

    # 2. the assembly, from the same STLs and the assembly's placements
    scene = [(placed(meshes[p["file"]], inst["transform"]), p["color"], p["label"])
             for p in parts for inst in p["instances"]]
    frame = re.compile(r"Wood leg|Stand bracket|Baseplate")
    panels = [(scene, (1, -1, 1), "whole assembly, from Onshape's isometric direction"),
              (scene, (-1, 1, -0.6), "whole assembly, from below"),
              ([s for s in scene if not frame.search(s[2])], (-1, -1, -0.7),
               "the doser alone, from below (no baseplate, stand or legs)")]
    fig, axes = plt.subplots(1, 3, figsize=(21, 8.6))
    for ax, (sc, view, name) in zip(axes, panels):
        ax.imshow(snap_view([s[:2] for s in sc], (900, 900), view))
        ax.set_title(name, fontsize=12)
        ax.axis("off")
    handles = [plt.Rectangle((0, 0), 1, 1, color=p["color"]) for p in parts]
    fig.legend(handles, [f"{p['label']} ×{p['count']}" for p in parts], loc="lower center", ncol=5, fontsize=10.5,
               frameon=False)
    fig.suptitle("The #193 assembly drawn from the downloaded STLs, placed with Onshape's assembly transforms "
                 "(wood in tan, bought parts in grey)", fontsize=12)
    fig.tight_layout(rect=(0, 0.12, 1, 0.96))
    fig.savefig(snap / "assembly" / "assembly-from-stl.png", dpi=80)
    plt.close(fig)
    print("wrote", snap / "assembly" / "all-parts.png", "and", snap / "assembly" / "assembly-from-stl.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--max-calls", type=int, default=40)
    ap.add_argument("--render-only", action="store_true")
    a = ap.parse_args()
    if not a.render_only:
        fetch(a.snapshot, a.max_calls)
    render(a.snapshot)


if __name__ == "__main__":
    main()
