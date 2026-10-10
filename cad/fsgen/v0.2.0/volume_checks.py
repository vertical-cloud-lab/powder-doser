"""Onshape's volume checks vs. fsgen's local builds, and the Variable-Studio-only test (0 Onshape calls).

Onshape's volumes come from the push logs and ``onshape_doc.py mass`` (their calls are in the ledger).
Each is compared with local builds of the matching script, exactly as written and with the one
rounding fsgen 0.2.0 applies when it writes dimension expressions (6 significant digits:
``105.2426`` becomes ``105.243`` in the relief sketch; every other number in the dimensioned
sketches has 6 digits or fewer).

The Variable-Studio-only test: on the branch "hinge 5 mm lower, Variable Studio only (hingeDrop
10 mm)" only ``#hingeDrop`` was changed in Onshape's Variable Studio (5 -> 10 mm, ``onshape_doc.py
setvars``), as an edit in the Onshape UI would do, with no fsgen push. Two candidates:

* ``hinge_drop_10``: everything follows ``#hingeDrop`` (what ``fsgen studio push`` would build);
* ``hinge_drop_10_towers_frozen``: everything but the tower sketch follows. Onshape rejected that
  sketch's dimensions at push time, so fsgen sent it without any (fixed numbers).

Writes ``results/volume_checks.json``, the two variant scripts and their local builds in
``variable_studio_test/`` and ``renders/variable_studio_test_sections.png``.

    python volume_checks.py
"""
from __future__ import annotations

import ast
import json
import re
import tempfile
from pathlib import Path

import build123d as bd
from fsgen.fslite.runner import export as local_export
from fsgen.native.local import build_local
from fsgen.native.script import trace

HERE = Path(__file__).resolve().parent
MAIN = HERE / "baseplate_servos_above.fs"
VST = HERE / "variable_studio_test"
ROUNDING = ("105.2426", "105.243")  # the one number fsgen 0.2.0 rounds in a dimension expression


def hinge_drop_10(src: str) -> str:
    out, n = re.subn(r'variable\(context, "hingeDrop", 5 \* millimeter\)',
                     'variable(context, "hingeDrop", 10 * millimeter)', src)
    assert n == 1
    return out


def towers_frozen(src: str) -> str:
    """The tower sketch with the numbers it was pushed with (plateThickness 6, hingeDrop 5, hole 5.3 mm)."""
    a, b = src.index("    const hingeZ = "), src.index("    skSolve(tower);")
    block = (src[a:b].replace("#plateThickness", "(6 * millimeter)").replace("#hingeDrop", "(5 * millimeter)")
             .replace("#hingeHoleDiameter", "(5.3 * millimeter)"))
    return src[:a] + block + src[b:]


def build(src: str, out_dir: Path, stem: str) -> Path:
    loc = build_local(trace(src))
    if not loc.ok:
        raise RuntimeError(f"{stem}: {loc.error}")
    files = local_export(loc.run, out_dir, stem)
    return next(f for f in map(Path, files) if f.suffix == ".step")


def volume(step: Path) -> float:
    return round(sum(s.volume for s in bd.import_step(str(step)).solids()), 3)


def onshape_volume(log: Path) -> float:
    """The volume check line of a push log (a dict) or of ``onshape_doc.py mass`` (JSON)."""
    line = next(l for l in log.read_text().splitlines() if l.startswith("{") and "volume_mm3" in l)
    return (json.loads(line) if line.startswith('{"') else ast.literal_eval(line))["volume_mm3"]


def section(step: Path, x: float) -> list:
    from matplotlib.path import Path as MPath
    solid = bd.import_step(str(step)).solids()[0]
    cut = solid & bd.Box(0.002, 600, 600).moved(bd.Location((x, 0, 0)))
    paths = []
    for f in cut.faces():
        if abs(f.center().X - (x - 0.001)) > 1e-4 or abs(abs(f.normal_at().X) - 1) > 1e-6:
            continue
        verts, codes = [], []
        for w in [f.outer_wire(), *f.inner_wires()]:
            pts = [w.position_at(t / 200) for t in range(201)]
            verts += [(p.Y, p.Z) for p in pts]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 2) + [MPath.CLOSEPOLY]
        paths.append(MPath(verts, codes))
    return paths


def figure(design: Path, follows: Path, frozen: Path, onshape_mm3: float, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch, PathPatch

    blue, orange, gray, ink, ink2, surface = "#2a78d6", "#eb6834", "#8c8b86", "#0b0b0b", "#52514e", "#fcfcfb"
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.0), dpi=200, sharey=True)
    fig.patch.set_facecolor(surface)
    for ax, x, what in ((axes[0], 35.0, "hinge tower"), (axes[1], 69.6, "servo cradle")):
        for p in section(frozen, x):
            ax.add_patch(PathPatch(p, facecolor=orange, edgecolor="none", alpha=0.8, zorder=1))
        for p in section(design, x):
            ax.add_patch(PathPatch(p, facecolor="none", edgecolor=gray, linewidth=1.0, linestyle=(0, (3, 2)), zorder=2))
        for p in section(follows, x):
            ax.add_patch(PathPatch(p, facecolor="none", edgecolor=blue, linewidth=1.6, zorder=3))
        ax.set_title(f"x = {x:g} mm, through the +X {what}", fontsize=9.5, color=ink2)
        ax.set_facecolor(surface)
        ax.set_aspect("equal")
        ax.set_xlim(22, 106)
        ax.set_ylim(-3, 80)
        ax.set_xlabel("y (mm)", fontsize=9, color=ink2)
        ax.grid(True, color="#e4e3df", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(colors=ink2, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("z (mm)", fontsize=9, color=ink2)
    handles = [Patch(facecolor=orange, alpha=0.8, label=f"Onshape after the Variable Studio edit: everything but the "
                                                         f"tower sketch moved (volume {onshape_mm3:,.3f} mm³, matched)"),
               Line2D([], [], color=blue, linewidth=1.6, label="fsgen push of hingeDrop 10 mm: the tower moves too"),
               Line2D([], [], color=gray, linewidth=1.0, linestyle=(0, (3, 2)), label="before: the design, hingeDrop 5 mm")]
    fig.legend(handles=handles, loc="lower center", ncol=1, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("#hingeDrop 5 → 10 mm changed only in Onshape's Variable Studio: the cradles follow, the towers don't",
                 fontsize=11, x=0.02, ha="left", fontweight="bold", color=ink)
    fig.tight_layout(rect=(0, 0.17, 1, 0.96))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=surface)
    print("->", out.relative_to(HERE))


if __name__ == "__main__":
    main_src = MAIN.read_text()
    thin_src = (HERE / "baseplate_thinner_table.fs").read_text()
    variants = {"hinge_drop_10": hinge_drop_10(main_src),
                "hinge_drop_10_towers_frozen": towers_frozen(hinge_drop_10(main_src))}
    for stem, src in variants.items():
        (VST / f"{stem}.fs").parent.mkdir(parents=True, exist_ok=True)
        (VST / f"{stem}.fs").write_text(src.replace("export function build", f"// generated by volume_checks.py from "
                                                    f"baseplate_servos_above.fs\nexport function build", 1))
    steps = {stem: build(src, VST / "out" / stem, stem) for stem, src in variants.items()}
    with tempfile.TemporaryDirectory() as tmp:
        rows = []
        for case, src, log in (
                ("main workspace (design)", main_src, HERE / "results" / "push_main.log"),
                ("branch: thinner table, fsgen push", thin_src, HERE / "results" / "push_thinner_table.log"),
                ("branch: hingeDrop 10 in the Variable Studio only", variants["hinge_drop_10_towers_frozen"],
                 HERE / "results" / "vs_only_hinge_drop_10_mass.log")):
            exact = volume(build(src, Path(tmp) / "exact", "x"))
            rounded = volume(build(src.replace(*ROUNDING), Path(tmp) / "rounded", "r"))
            rows.append({"case": case, "local_mm3": exact, "local_with_fsgen_rounding_mm3": rounded,
                         "onshape_mm3": onshape_volume(log), "onshape_minus_rounded_local_mm3":
                             round(onshape_volume(log) - rounded, 3)})
        full = volume(steps["hinge_drop_10"])
        full_r = volume(build(variants["hinge_drop_10"].replace(*ROUNDING), Path(tmp) / "full_r", "f"))
    res = {"volume_checks": rows,
           "variable_studio_test": {
               "edit": "hingeDrop 5 -> 10 mm in Onshape's Variable Studio only (no fsgen push)",
               "candidates_mm3": {"everything follows (fsgen push)": {"local": full, "with_rounding": full_r},
                                  "towers don't follow": {"local": rows[2]["local_mm3"],
                                                          "with_rounding": rows[2]["local_with_fsgen_rounding_mm3"]}},
               "onshape_mm3": rows[2]["onshape_mm3"]}}
    (HERE / "results" / "volume_checks.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    figure(HERE / "out" / "baseplate_servos_above" / "baseplate_servos_above.step", steps["hinge_drop_10"],
           steps["hinge_drop_10_towers_frozen"], rows[2]["onshape_mm3"],
           HERE / "renders" / "variable_studio_test_sections.png")
