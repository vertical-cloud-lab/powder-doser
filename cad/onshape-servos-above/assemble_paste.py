"""Paste-in custom features for the servos-above doser's printed parts, plus one that places them all (0 calls).

    python assemble_paste.py           # paste/<part>.fs for every part script in parts/, and
                                       # paste/powder_doser_servos_above.fs: all of them in one Feature Studio,
                                       # plus "Powder doser, servos above (printed parts)"
    python assemble_paste.py --check   # also runs that feature with fsgen's local FeatureScript interpreter at
                                       # a few tilts and writes results/paste_assembly.json and a STEP per tilt

fsgen's paste export turns a part script into one custom feature whose dialog holds the part's variables.
In Onshape: create a Feature Studio, select all, paste the file, commit; then in a Part Studio insert a feature
from the Feature Studio's toolbar group. No API calls are involved, so this works while the company's API
allowance is used up (HTTP 402, 2026-10-27). It is not a native feature tree: the history is inside the
custom feature (open the Feature Studio to edit it); the native trees come from ``fsgen studio push``.

The assembly feature calls every part's feature with its default parameters and moves the result to where
text-to-cad's servos-above assembly puts it (assembly/placements_servos_above.json, from PR #176's
lib/frames.py). Its "Tilt" parameter turns the mounting plate and everything on it about the hinge, outlet
down, and the servo pinions with it (2:1); "Auger turn" spins the auger and cap, and the stepper pinion
against them (44:20).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PARTS = HERE / "parts"
PASTE = HERE / "paste"
PLACEMENTS = HERE / "assembly" / "placements_servos_above.json"

# script stem -> feature title (also the Part Studio name used for pushes)
TITLES = {
    "baseplate_servos_above": "Baseplate (servos above)",
    "mounting_plate_servos_above": "Mounting plate (servos above)",
    "auger": "Auger",
    "auger_cap": "Auger cap",
    "bracket": "Bracket",
    "tap_collar_base": "Tap collar base",
    "tap_collar": "Tap collar",
    "stepper_pinion": "Stepper pinion",
    "servo_pinion": "Servo pinion",
}
# assembly instance (placements_servos_above.json) -> script stem
INSTANCES = {
    "Baseplate": "baseplate_servos_above",
    "Mounting plate": "mounting_plate_servos_above",
    "Auger": "auger",
    "Auger cap": "auger_cap",
    "Bracket (rear)": "bracket",
    "Bracket (front)": "bracket",
    "Tap collar base": "tap_collar_base",
    "Tap collar": "tap_collar",
    "Stepper pinion": "stepper_pinion",
    "Servo pinion (+X)": "servo_pinion",
    "Servo pinion (-X)": "servo_pinion",
}
ASSEMBLY_TITLE = "Powder doser, servos above (printed parts)"
ASSEMBLY_FN = "powderDoserServosAbove"


def ident(name: str) -> str:
    words = "".join(c if c.isalnum() else " " for c in name).split()
    return (words[0].lower() + "".join(w[:1].upper() + w[1:] for w in words[1:])) if words else "part"


def fs_num(v: float) -> str:
    s = f"{v:.9f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def fs_value(p: dict) -> str:
    """A parameter's default as a FeatureScript literal."""
    d = p["default"]
    kind = p["kind"]
    mag = getattr(d, "v", d)                                     # fslite's quantities hold SI magnitudes
    if kind == "length":
        return f"{fs_num(float(mag) * 1000.0)} * millimeter"     # fslite keeps lengths in metres
    if kind == "angle":
        return f"{fs_num(math.degrees(float(mag)))} * degree"    # and angles in radians
    if kind == "integer":
        return str(int(round(float(mag))))
    if kind == "boolean":
        return "true" if d else "false"
    return fs_num(float(mag))


def axis_angle(R: np.ndarray) -> tuple[np.ndarray, float]:
    """Rotation matrix -> (unit axis, angle in degrees)."""
    c = max(-1.0, min(1.0, (np.trace(R) - 1.0) / 2.0))
    ang = math.acos(c)
    if ang < 1e-9:
        return np.array([0.0, 0.0, 1.0]), 0.0
    if math.pi - ang < 1e-6:                     # 180 deg: axis from R + I
        M = (R + np.eye(3)) / 2.0
        k = int(np.argmax(np.diag(M)))
        ax = M[:, k] / math.sqrt(max(M[k, k], 1e-12))
        return ax / np.linalg.norm(ax), 180.0
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2.0 * math.sin(ang))
    return ax / np.linalg.norm(ax), math.degrees(ang)


def rot(axis, deg: float, point=(0.0, 0.0, 0.0)) -> np.ndarray:
    a = np.asarray(axis, float) / np.linalg.norm(axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    M = np.eye(4)
    M[:3, :3] = np.eye(3) + s * K + (1 - c) * K @ K
    p = np.asarray(point, float)
    M[:3, 3] = p - M[:3, :3] @ p
    return M


def fs_vec(v, unit: str | None = None) -> str:
    s = f"vector({', '.join(fs_num(float(x)) for x in v)})"
    return f"{s} * {unit}" if unit else s


def fs_placement(M: np.ndarray) -> str:
    """4x4 -> transform(translation) * rotationAround(axis through the origin, angle), checked numerically."""
    ax, deg = axis_angle(M[:3, :3])
    back = np.eye(4)
    back[:3, 3] = M[:3, 3]
    back = back @ rot(ax, deg)
    assert np.allclose(back, M, atol=1e-6), (M, back)
    t = f"transform({fs_vec(M[:3, 3], 'millimeter')})"
    if deg == 0.0:
        return t
    return f"{t} * rotationAround(line({fs_vec((0, 0, 0), 'millimeter')}, {fs_vec(ax)}), {fs_num(deg)} * degree)"


def split_paste(code: str) -> tuple[str, str]:
    """(header + helpers, the rest) of one paste export: everything before the first annotation is shared."""
    i = code.index('annotation { "Feature Type Name"')
    return code[:i], code[i:]


# fsgen's paste export scopes a feature without an explicit booleanScope to every solid in the Part Studio,
# so pasted next to other parts (or called by the assembly feature) the auger's gear and thread cuts would cut
# them too. Each part's feature is limited to the solids it made itself.
ALL_SOLIDS = "qAllModifiableSolidBodies()"
OWN_SOLIDS = "qBodyType(qCreatedBy(id, EntityType.BODY), BodyType.SOLID)"


def export_part(stem: str) -> tuple[str, dict]:
    from fsgen.native.paste import paste_export
    from fsgen.native.script import trace
    code, chk = paste_export(trace((PARTS / f"{stem}.fs").read_text(), "studio"), TITLES[stem])
    chk["scoped_all_solids"] = code.count(ALL_SOLIDS)
    return code.replace(ALL_SOLIDS, OWN_SOLIDS), chk


def assembly_feature(defaults: dict[str, str], fn_of: dict[str, str], pl: dict) -> str:
    hp = pl["hinge_point_mm"]
    servo, stepper = pl["servo_ratio"], pl["stepper_ratio"]
    tilting = set(pl["tilting"])
    P = {k: np.array(v["matrix"]) for k, v in pl["parts"].items()}
    A = P["Auger"]
    S = P["Stepper pinion"]
    L = ["// Every printed part of the servos-above doser, where text-to-cad's assembly (PR #176) puts it.",
         "// Calls each part's feature above with its default parameters (edit the defaults here).",
         f'annotation {{ "Feature Type Name" : "{ASSEMBLY_TITLE}" }}',
         f"export const {ASSEMBLY_FN} = defineFeature(function(context is Context, id is Id, definition is map)",
         "    precondition", "    {",
         '        annotation { "Name" : "Tilt (outlet down)" }',
         "        isAngle(definition.tilt, { (degree) : [0, 0, 45] } as AngleBoundSpec);",
         '        annotation { "Name" : "Auger turn" }',
         "        isAngle(definition.augerTurn, { (degree) : [-3600, 0, 3600] } as AngleBoundSpec);",
         "    }", "    {",
         f"        const hinge = rotationAround(line({fs_vec(hp, 'millimeter')}, vector(1, 0, 0)), definition.tilt);",
         f"        const spin = rotationAround(line({fs_vec(A[:3, 3], 'millimeter')}, {fs_vec(A[:3, 2])}), "
         "definition.augerTurn);",
         f"        const pinionSpin = rotationAround(line({fs_vec(S[:3, 3], 'millimeter')}, {fs_vec(S[:3, 2])}), "
         f"-{fs_num(stepper)} * definition.augerTurn);"]
    for name, stem in INSTANCES.items():
        sub = ident(name)
        L.append(f"        // {name}: {TITLES[stem]}")
        L.append(f'        {fn_of[stem]}(context, id + "{sub}", {defaults[stem]});')
        place = fs_placement(P[name])
        if name.startswith("Servo pinion"):
            sign = "-" if "+X" in name else ""
            place = (f"{place} * rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 0, 1)), "
                     f"{sign}{fs_num(servo)} * definition.tilt)")
        elif name in ("Auger", "Auger cap"):
            place = f"hinge * spin * {place}"
        elif name == "Stepper pinion":
            place = f"hinge * pinionSpin * {place}"
        elif name in tilting:
            place = f"hinge * {place}"
        if place != "transform(vector(0, 0, 0) * millimeter)":
            L.append(f'        opTransform(context, id + "{sub}Place", {{ "bodies" : '
                     f'qBodyType(qCreatedBy(id + "{sub}", EntityType.BODY), BodyType.SOLID), "transform" : {place} }});')
    L += ["    });", ""]
    return "\n".join(L)


def build(check: bool) -> None:
    from fsgen.fslite.runner import run_source
    from fsgen.fslite.values import mk
    pl = json.loads(PLACEMENTS.read_text())
    PASTE.mkdir(parents=True, exist_ok=True)
    head, bodies, defaults, fn_of, report = None, [], {}, {}, {}
    for stem in TITLES:
        if not (PARTS / f"{stem}.fs").exists():
            raise SystemExit(f"parts/{stem}.fs is missing")
        code, chk = export_part(stem)
        (PASTE / f"{stem}.fs").write_text(code)
        h, rest = split_paste(code)
        head = head or h
        if h != head:
            raise SystemExit(f"{stem}: its paste header differs from the others'; merge by hand")
        bodies.append(rest)
        run = run_source(code)
        if not run.ok:
            raise SystemExit(f"{stem}: the paste feature does not run locally: {run.error}")
        m = run.metrics()
        if m["bodies"] != chk["native_parts"] or abs(m["volume_mm3"] - chk["native_volume_mm3"]) > 1e-3 * max(
                1.0, chk["native_volume_mm3"]):
            raise SystemExit(f"{stem}: scoped paste feature {m} differs from the native local build "
                             f"({chk['native_parts']} parts, {chk['native_volume_mm3']} mm3)")
        fn_of[stem] = run.feature
        defaults[stem] = "{ " + ", ".join(f'"{p["name"]}" : {fs_value(p)}' for p in run.params) + " }"
        report[stem] = {"feature": run.feature, "title": TITLES[stem], "parameters": [p["name"] for p in run.params],
                        "paste_volume_mm3": chk.get("paste_volume_mm3"), "native_volume_mm3": chk["native_volume_mm3"],
                        "paste_matches_native_local_build": bool(chk["ok"])}
        print(f"paste/{stem}.fs: {run.feature}, {len(run.params)} parameters, local volume "
              f"{chk.get('paste_volume_mm3')} mm3 (native local build {chk['native_volume_mm3']})")
    combined = head + "\n".join(bodies) + "\n" + assembly_feature(defaults, fn_of, pl)
    out = PASTE / "powder_doser_servos_above.fs"
    out.write_text(combined)
    print(f"-> {out.relative_to(HERE)} ({len(combined.splitlines())} lines, {len(TITLES) + 1} features)")
    if not check:
        return
    res = {"parts": report, "assembly": {}}
    runs = []
    for tilt in (0.0, 45.0):
        params = {"tilt": mk(math.radians(tilt), (0, 1)), "augerTurn": mk(0.0, (0, 1))}   # fslite angles
        run = run_source(combined, feature=ASSEMBLY_FN, params=params)
        if not run.ok:
            raise SystemExit(f"assembly feature failed locally at tilt {tilt}: {run.error}")
        m = run.metrics()
        res["assembly"][f"tilt_{int(tilt)}"] = m
        print(f"assembly at tilt {tilt:g} deg: {m['bodies']} bodies, {m['volume_mm3']} mm3, box {m['bbox_mm']}")
        write_step(run, HERE / "results" / f"paste_assembly_tilt{int(tilt)}.step")
        runs.append(run)
    render(runs, HERE / "renders" / "paste_assembly_local.png",
           [f"{ASSEMBLY_TITLE}: tilt {t} deg" for t in (0, 45)])
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "paste_assembly.json").write_text(json.dumps(res, indent=1) + "\n")


def solids_mm(run) -> list:
    """The solids the local run left, scaled from fslite's metres to millimetres."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Pnt, gp_Trsf
    tr = gp_Trsf()
    tr.SetScale(gp_Pnt(0, 0, 0), 1000.0)
    return [(str(b.creator), BRepBuilderAPI_Transform(b.shape, tr, True).Shape())
            for b in run.context.bodies if b.kind == "solid"]


def write_step(run, path: Path) -> None:
    from OCP.BRep import BRep_Builder
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
    from OCP.TopoDS import TopoDS_Compound
    comp, bld = TopoDS_Compound(), BRep_Builder()
    bld.MakeCompound(comp)
    solids = solids_mm(run)
    for _, shape in solids:
        bld.Add(comp, shape)
    path.parent.mkdir(parents=True, exist_ok=True)
    w = STEPControl_Writer()
    w.Transfer(comp, STEPControl_AsIs)
    w.Write(str(path))
    print(f"   {len(solids)} solids -> {path.relative_to(HERE)}")


COLORS = {"baseplate": "#8c9199", "mountingPlate": "#b3b5ba", "auger": "#cca140", "augerCap": "#3352a6",
          "bracket": "#739ebf", "tapCollarBase": "#598cb3", "tapCollar": "#8c59b3", "stepperPinion": "#4d9966",
          "servoPinion": "#4d9966"}


def render(runs: list, path: Path, titles: list[str]) -> None:
    """Side-by-side isometric views of the local results, one colour per part (matplotlib; no GPU)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    light = np.array([0.4, -0.5, 0.75])
    light /= np.linalg.norm(light)
    fig = plt.figure(figsize=(7.5 * len(runs), 7.5), dpi=110)
    for k, (run, title) in enumerate(zip(runs, titles)):
        ax = fig.add_subplot(1, len(runs), k + 1, projection="3d")
        lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
        for creator, shape in solids_mm(run):
            part = creator.split(".")[1] if "." in creator else creator
            base = re_part(part)
            BRepMesh_IncrementalMesh(shape, 0.25, False, 0.4, True)
            tris = []
            exp = TopExp_Explorer(shape, TopAbs_FACE)
            while exp.More():
                f = TopoDS.Face_s(exp.Current()) if hasattr(TopoDS, "Face_s") else TopoDS.Face(exp.Current())
                loc = TopLoc_Location()
                tri = BRep_Tool.Triangulation_s(f, loc)
                if tri is not None:
                    trsf = loc.Transformation()
                    pts = np.array([[q.X(), q.Y(), q.Z()] for q in
                                    (tri.Node(i).Transformed(trsf) for i in range(1, tri.NbNodes() + 1))])
                    rev = f.Orientation() == TopAbs_REVERSED
                    for i in range(1, tri.NbTriangles() + 1):
                        a, b, c = tri.Triangle(i).Get()
                        tris.append(pts[[a - 1, c - 1, b - 1]] if rev else pts[[a - 1, b - 1, c - 1]])
                exp.Next()
            tris = np.array(tris)
            lo, hi = np.minimum(lo, tris.reshape(-1, 3).min(0)), np.maximum(hi, tris.reshape(-1, 3).max(0))
            n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            shade = 0.45 + 0.55 * np.clip(n @ light, 0, 1)
            rgb = np.array(matplotlib.colors.to_rgb(COLORS.get(base, "#999999")))
            ax.add_collection3d(Poly3DCollection(tris, facecolors=np.clip(rgb * shade[:, None], 0, 1),
                                                 edgecolors="none"))
        ctr, span = (lo + hi) / 2, (hi - lo).max() / 2 * 1.02
        ax.set_xlim(ctr[0] - span, ctr[0] + span)
        ax.set_ylim(ctr[1] - span, ctr[1] + span)
        ax.set_zlim(ctr[2] - span, ctr[2] + span)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=22, azim=-58)
        ax.set_axis_off()
        ax.set_title(title, fontsize=13)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.93, wspace=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    print("->", path.relative_to(HERE))


def re_part(sub: str) -> str:
    """Assembly sub-feature id -> colour key ("bracketRear" -> "bracket", "servoPinionX" -> "servoPinion")."""
    for key in sorted(COLORS, key=len, reverse=True):
        if sub.startswith(key):
            return key
    return sub


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.setrecursionlimit(10000)
    build(a.check)
