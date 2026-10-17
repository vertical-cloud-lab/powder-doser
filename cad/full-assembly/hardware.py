"""Fasteners for the current-design assembly: which screw goes where.

Every joint is read off the hole geometry in the STEP files (Fusion parts,
AI tap-collar base, purchased-part models); the numbers are in the README,
"Fasteners".  Lengths are the shortest standard length that passes the
grip plus a full nut.

Screws and nuts are placed by a "seat" frame: origin on the bearing face,
+Z pointing the way the screw goes in (for a nut, +Z points away from the
part it clamps).  ``models()`` returns each fastener in that canonical
frame: screw head in z < 0 and shank in 0 <= z <= L; nut and washer in
0 <= z <= thickness.  The McMaster-Carr STEP files in
``components/mcmaster/`` are used when present (each is re-oriented into
the canonical frame from its own geometry); otherwise an ISO-dimension
stand-in is built, so the assembly always renders.

Joint summary (world = Fusion baseplate frame, see onshape/layout.py):

* hinge, per side: M5 x 45 button head screw from inside the knuckle,
  through the knuckle (12.5), tower (12.3) and 28 T gear (12.3) with the
  0.3 and 0.6 mm gaps, nylon-insert locknut outside the gear.  The auger
  tube passes 3.6 mm inside the knuckles, so only a low head fits there
  (2.75 mm, 0.85 mm clear of the tube at every tilt).  The plate turns on
  the screw shank (Ø5.7 holes in the plate, Ø5.3 in the tower).
* brackets and tap-collar base to the mounting plate: M3 button head
  screws from under the plate's 6 mm floor, hex nut on top.  Only 2 mm
  separate the floor from the baseplate at tilt 0, so a button head
  (1.65 mm) is the only head that fits underneath.  The base's other hole
  is countersunk on top (90 deg, Ø6), so it takes an M3 x 30 flat head
  from above with the nut under the floor; that nut and the screw tip
  stand 0.4 and 1.0 mm proud of the 2 mm gap at tilt 0.
* M3 nuts are nylon-insert locknuts, as on the rig ("all nuts have been
  replaced with locknuts", #132), except the one under the plate's floor,
  where only a plain nut fits.
* bracket clamp: M3 x 14 across the two 3 mm ears (2 mm split), locknut.
* tap-collar clamp: M3 x 20 button head through the 5.8 mm ears (2.2 mm
  split), nut underneath.  The nut only clears the base's hard-stop bump
  with the collar rolled away from the stepper (``COLLAR_ROLL_DEG``).
* solenoid: M3 x 5 through the collar's 1.2 mm plate into the frame's
  tapped ears.
* stepper: M2.5 x 8 through the 6 mm plate into the NEMA 11 face
  (2.5 mm deep threads; the screw goes 2 mm in).
* servos: M3 x 14 through each 5 mm post and the 2.5 mm flange, locknut
  on the flange (3.7 mm from the case wall, room for an M3 nut, not M4).
* servo pinions: M3 x 10 through the pinion's Ø3.4 bore into the servo
  output shaft (2.4 mm of thread; x 12 could bottom out in the spline).
* mounting board (``with_board``): #10 x 1-1/4 in pan head wood screws
  (316 stainless: McMaster has no 18-8 one in this size),
  four down through the baseplate's Ø5.5 corner holes (6 mm plate) and two
  through the legs (5 mm) into the board's front edge, 19 mm down, i.e.
  halfway down the 38.1 mm board (onshape/layout.py, "Mounting board").
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import numpy as np

HERE = Path(__file__).resolve().parent
MCM_DIR = HERE / "components" / "mcmaster"

# --------------------------------------------------------------------------- #
# catalogue: key -> spec (mm).  Head diameter dk and height k, nut width s
# and height m are McMaster-Carr's own figures for the part number in
# MCMASTER, read from its catalog tables on 2 Oct 2026
# (components/mcmaster/parts.json; fastener_check.py compares them).
# Every screw is fully threaded; P is the coarse pitch.
# --------------------------------------------------------------------------- #
PITCH = {2.5: 0.45, 3.0: 0.5, 5.0: 0.8}
HARDWARE = {
    "bhcs_m5x45": dict(kind="bhcs", d=5.0, L=45.0, dk=9.5, k=2.75,
                       desc="Button head screw, 18-8 stainless, M5 x 0.8 mm, 45 mm long"),
    "locknut_m5": dict(kind="nut", d=5.0, s=8.0, m=5.0, insert=True,
                       desc="Nylon-insert locknut, 18-8 stainless, M5 x 0.8 mm"),
    "shcs_m3x14": dict(kind="shcs", d=3.0, L=14.0, dk=5.5, k=3.0,
                       desc="Socket head screw, 18-8 stainless, M3 x 0.5 mm, 14 mm long"),
    "shcs_m3x10": dict(kind="shcs", d=3.0, L=10.0, dk=5.5, k=3.0,
                       desc="Socket head screw, 18-8 stainless, M3 x 0.5 mm, 10 mm long"),
    "shcs_m3x5": dict(kind="shcs", d=3.0, L=5.0, dk=5.5, k=3.0,
                      desc="Socket head screw, 18-8 stainless, M3 x 0.5 mm, 5 mm long"),
    "bhcs_m3x20": dict(kind="bhcs", d=3.0, L=20.0, dk=5.7, k=1.65,
                       desc="Button head screw, 18-8 stainless, M3 x 0.5 mm, 20 mm long"),
    "bhcs_m3x25": dict(kind="bhcs", d=3.0, L=25.0, dk=5.7, k=1.65,
                       desc="Button head screw, 18-8 stainless, M3 x 0.5 mm, 25 mm long"),
    "fhcs_m3x30": dict(kind="fhcs", d=3.0, L=30.0, dk=6.0, k=1.7,
                       desc="Flat head screw (90 deg), 18-8 stainless, M3 x 0.5 mm, 30 mm long"),
    "locknut_m3": dict(kind="nut", d=3.0, s=5.5, m=4.0, insert=True,
                       desc="Nylon-insert locknut, 18-8 stainless, M3 x 0.5 mm"),
    "hexnut_m3": dict(kind="nut", d=3.0, s=5.5, m=2.4,
                      desc="Hex nut, 18-8 stainless, M3 x 0.5 mm"),
    "shcs_m2p5x8": dict(kind="shcs", d=2.5, L=8.0, dk=4.5, k=2.5,
                        desc="Socket head screw, 18-8 stainless, M2.5 x 0.45 mm, 8 mm long"),
    # #10 wood screw (0.19 in major, 13 threads per inch), McMaster's figures
    # in inches: head 0.365 x 0.128, threaded 3/4 in from the tip
    "wood_10x1p25": dict(kind="wood", d=0.19 * 25.4, L=1.25 * 25.4, dk=0.365 * 25.4, k=0.128 * 25.4,
                         P=25.4 / 13, d_root=3.3, thread_len=0.75 * 25.4,
                         desc="Pan head Phillips screw for wood (plywood, OSB), 316 stainless, #10, "
                              "1-1/4 in long"),
}


def _frame(origin, z_dir, x_hint=(0.0, 0.0, 1.0)) -> np.ndarray:
    """4 x 4 seat frame: origin, +Z along z_dir (any X perpendicular)."""
    z = np.asarray(z_dir, float)
    z /= np.linalg.norm(z)
    h = np.asarray(x_hint, float)
    if abs(np.dot(h, z)) > 0.9:
        h = np.array([1.0, 0.0, 0.0]) if abs(z[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = h - np.dot(h, z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, origin
    return M


def fastener_placements(tilt_deg: float = 0.0, roll_deg: float | None = None,
                        with_board: bool = False) -> list[tuple[str, str, str, np.ndarray]]:
    """[(instance name, hardware key, joint, world 4 x 4)] for every fastener
    (with_board: also the screws into the mounting board)."""
    import sys
    sys.path.insert(0, str(HERE / "onshape"))
    import layout as L

    roll = L.COLLAR_ROLL_DEG if roll_deg is None else roll_deg
    P = L.placements(tilt_deg, roll)
    W = {n: M for n, (_, M) in P.items()}
    out = []

    def add(name, key, joint, parent_M, origin, z_dir):
        out.append((name, key, joint, parent_M @ _frame(origin, z_dir)))

    # hinge: fixed in the towers, so it doesn't tilt
    for s, tag in ((1, "+X"), (-1, "-X")):
        add(f"Hinge screw ({tag})", "bhcs_m5x45", "hinge", np.eye(4),
            (s * 16.1, L.HINGE_Y, L.HINGE_Z), (s, 0, 0))
        add(f"Hinge locknut ({tag})", "locknut_m5", "hinge", np.eye(4),
            (s * 54.1, L.HINGE_Y, L.HINGE_Z), (s, 0, 0))

    # brackets to the plate (bracket frame: base on z = 0, holes at x = +-24,
    # y = 6), clamp across the split ears at (y, z) = (6, 49.2)
    for b in ("rear", "front"):
        M = W[f"Bracket ({b})"]
        for sx in (-1, 1):
            add(f"Bracket screw ({b}, {'+' if sx > 0 else '-'})", "bhcs_m3x20", "brackets",
                M, (sx * 24.0, 6.0, -6.0), (0, 0, 1))
            add(f"Bracket nut ({b}, {'+' if sx > 0 else '-'})", "locknut_m3", "brackets",
                M, (sx * 24.0, 6.0, 8.0), (0, 0, 1))
        add(f"Bracket clamp screw ({b})", "shcs_m3x14", "brackets", M, (4.0, 6.0, 49.2), (-1, 0, 0))
        add(f"Bracket clamp nut ({b})", "locknut_m3", "brackets", M, (-4.0, 6.0, 49.2), (-1, 0, 0))

    # tap-collar base: holes at x = -24 (14 mm tall) and +24 (19.7 mm, the
    # hard-stop side), y = 0
    M = W["Tap collar base (AI)"]
    add("Tap base screw (-)", "bhcs_m3x25", "tap collar", M, (-24.0, 0.0, -6.0), (0, 0, 1))
    add("Tap base nut (-)", "locknut_m3", "tap collar", M, (-24.0, 0.0, 14.0), (0, 0, 1))
    add("Tap base screw (+)", "fhcs_m3x30", "tap collar", M, (24.0, 0.0, 21.0), (0, 0, -1))
    add("Tap base nut (+)", "hexnut_m3", "tap collar", M, (24.0, 0.0, -6.0), (0, 0, -1))

    # tap-collar clamp (collar frame: ears at x = -20.2, y = 8.5, z = +-1.1..6.9)
    M = W["Tap collar"]
    add("Tap collar clamp screw", "bhcs_m3x20", "tap collar", M, (-20.2, 8.5, 6.9), (0, 0, -1))
    add("Tap collar clamp nut", "locknut_m3", "tap collar", M, (-20.2, 8.5, -6.9), (0, 0, -1))
    # solenoid: through the 1.2 mm plate (y = 15.8..17) into the tapped ears
    for x, z, tag in ((-9.1, 33.0, "lower"), (9.1, 49.0, "upper")):
        add(f"Solenoid screw ({tag})", "shcs_m3x5", "solenoid", M, (x, 17.0, z), (0, -1, 0))

    # stepper: plate x = -89.33..-83.33 (MP frame), 23 mm square about (0, -9.8)
    M = W["Mounting plate"]
    for sy in (-1, 1):
        for sz in (-1, 1):
            add(f"Stepper screw ({'+' if sy > 0 else '-'}{'+' if sz > 0 else '-'})", "shcs_m2p5x8",
                "stepper", M, (-83.33, sy * 11.5, -9.8 + sz * 11.5), (-1, 0, 0))

    # servos: through the posts (|x| = 67.1..72.1) and flange, nut inside
    for s, tag in ((1, "+X"), (-1, "-X")):
        for y in (11.5, 59.54):
            for z in (11.48, 20.52):
                pos = f"{tag}, y{y:.0f} z{z:.0f}"
                add(f"Servo screw ({pos})", "shcs_m3x14", "servos", np.eye(4),
                    (s * 72.1, y, z), (-s, 0, 0))
                add(f"Servo nut ({pos})", "locknut_m3", "servos", np.eye(4),
                    (s * 64.6, y, z), (-s, 0, 0))
        # servo pinion: head on the 60 deg recess where it is Ø5.5 (z = 1.25)
        Mp = W[f"Servo pinion ({tag})"]
        add(f"Servo pinion screw ({tag})", "shcs_m3x10", "servos", Mp, (0.0, 0.0, 1.25), (0, 0, 1))

    if with_board:
        # baseplate to the board: down through the corner holes, and through
        # the legs into the front edge
        for x, y in L.BOARD_HOLES:
            add(f"Board screw ({'+' if x > 0 else '-'}X, y{y:.0f})", "wood_10x1p25", "board",
                np.eye(4), (x, y, 6.0), (0, 0, -1))
        for x, z in L.LEG_HOLES:
            add(f"Board screw (leg {'+' if x > 0 else '-'}X)", "wood_10x1p25", "board",
                np.eye(4), (x, L.LEG_FRONT_Y, z), (0, 1, 0))
    return out


# --------------------------------------------------------------------------- #
# models in the canonical seat frame
# --------------------------------------------------------------------------- #
def _thread_profile(r_major: float, P: float, z0: float, z1: float) -> list[tuple[float, float]]:
    """(r, z) zig-zag from z0 to z1: crests at r_major, roots 0.6 P deeper.
    Revolved, it reads as a thread in renders (rings, not a helix)."""
    r_minor = r_major - 0.6 * P
    n = max(1, int((z1 - z0) / P))
    pts = [(r_minor, z0)]
    for i in range(n):
        pts += [(r_major, z0 + (i + 0.5) * P), (r_minor, z0 + (i + 1) * P)]
    return pts


def _hex_turned(s: float, m: float, top: bool = True, bottom: bool = True) -> cq.Workplane:
    """Hex prism with its corners turned off at 30 deg (ISO 4032 / DIN 934):
    the chamfer circle is 0.95 s on the faces, so the flats stay flat."""
    R = s * 1.1547 / 2 + 0.5
    h = (R - 0.475 * s) * np.tan(np.radians(30))
    prof = [(0.0, 0.0), (0.475 * s if bottom else R, 0.0), (R, h if bottom else 0.0),
            (R, m - h if top else m), (0.475 * s if top else R, m), (0.0, m)]
    prof = [q for i, q in enumerate(prof) if i == 0 or q != prof[i - 1]]
    cone = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    return cq.Workplane("XY").polygon(6, s * 1.1547).extrude(m).intersect(cone)


def _iso_model(spec: dict, cosmetic: bool = True) -> cq.Workplane:
    """Stand-in in the seat frame.  cosmetic=False gives the plain shapes
    the renders used until 2 Oct 2026 (no threads, flat-topped locknut)."""
    d = spec["d"]
    P = spec.get("P") or PITCH[d]
    if spec["kind"] == "wood":
        return _wood_screw(spec, cosmetic)
    if spec["kind"] in ("shcs", "bhcs", "fhcs"):
        L, dk, k = spec["L"], spec["dk"], spec["k"]
        # shank, as an (r, z) profile from the bearing face to the tip
        if cosmetic:
            z_thr = min(1.5 * P, 0.2 * L)
            shank = [(d / 2, 0.0), (d / 2, z_thr)] + _thread_profile(d / 2, P, z_thr, L - 0.3 * P)[1:]
            shank += [(d / 2 - 0.6 * P, L), (0.0, L)]
        else:
            shank = [(d / 2, 0.0), (d / 2, L), (0.0, L)]
    if spec["kind"] == "fhcs":     # seat = the flush head top; L is overall
        # 90 deg head: Ø dk at the top face (z = 0), meeting the shank at z = k
        prof = [(0.0, 0.0), (dk / 2, 0.0), (d / 2, k)] + [(r, z) for r, z in shank if z > k]
        body = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
        sock = cq.Workplane("XY").workplane(offset=-0.01).polygon(6, 0.35 * dk * 1.1547).extrude(0.8 * k)
        return body.cut(sock)
    if spec["kind"] in ("shcs", "bhcs"):
        # socket from below the head (the dome bulges past -k) to 0.4 k deep
        sock = (cq.Workplane("XY").workplane(offset=-1.3 * k)
                .polygon(6, 0.5 * dk * 1.1547).extrude(0.9 * k))
        rev = cq.Workplane("XZ").polyline([(0.0, 0.0)] + shank).close().revolve(360, (0, 0, 0), (0, 1, 0))
        if spec["kind"] == "bhcs":     # dome head on the shank
            head = (cq.Workplane("XZ").moveTo(0, -k)
                    .threePointArc((0.3 * dk, -0.85 * k), (dk / 2, -0.3 * k))
                    .lineTo(dk / 2, 0).lineTo(0, 0).close()
                    .revolve(360, (0, 0, 0), (0, 1, 0)))
        else:
            head = cq.Workplane("XY").workplane(offset=-k).circle(dk / 2).extrude(k)
            head = head.faces("<Z").edges().fillet(0.08 * dk)
        return head.union(rev).cut(sock)
    s, m = spec["s"], spec["m"]
    if not cosmetic:
        nut = cq.Workplane("XY").polygon(6, s * 1.1547).extrude(m).faces(">Z or <Z").chamfer(0.12 * s)
    elif spec.get("insert"):
        # nylon-insert locknut (DIN 985 shape): hex body, round crown rolled
        # over the nylon ring, ring visible in the top (see nylon_insert())
        m_hex = 0.76 * m
        nut = _hex_turned(s, m_hex, top=False)
        crown = (cq.Workplane("XY").workplane(offset=m_hex - 0.01).circle(0.47 * s)
                 .extrude(m - m_hex + 0.01).faces(">Z").edges().fillet(0.35 * (m - m_hex)))
        nut = nut.union(crown).cut(cq.Workplane("XY").workplane(offset=m - 0.45)
                                   .circle(0.38 * s).extrude(1.0))
    else:
        nut = _hex_turned(s, m)
    nut = nut.cut(cq.Workplane("XY").circle(d / 2 - 0.6 * P).extrude(m))
    if cosmetic:     # internal thread: cut rings out to the major diameter
        prof = [(d / 2 - 0.61 * P, 0.0)] + [(d / 2 - 0.6 * P + (0.6 * P if i % 2 else 0.0), z)
                                             for i, (_, z) in enumerate(_thread_profile(d / 2, P, 0.3 * P, m - 0.3 * P))][1:]
        prof += [(d / 2 - 0.61 * P, m)]
        rings = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
        nut = nut.cut(rings)
    return nut


def _wood_screw(spec: dict, cosmetic: bool = True) -> cq.Workplane:
    """Pan head Phillips screw for wood: plain shank under the head, then
    the thread to a gimlet point (crests shrinking over the last 2.5
    pitches)."""
    d, L, dk, k, P = spec["d"], spec["L"], spec["dk"], spec["k"], spec["P"]
    r, r0 = d / 2, spec["d_root"] / 2
    tip = 2.5 * P
    if cosmetic:
        z_thr = L - spec["thread_len"]
        prof = [(0.0, 0.0), (0.93 * r, 0.0), (0.93 * r, z_thr)]
        z = z_thr
        while z + P < L - 0.2:
            taper = min(1.0, (L - (z + P / 2)) / tip)
            prof += [(r0 + (r - r0) * taper, z + P / 2), (r0 * min(1.0, (L - z - P) / tip), z + P)]
            z += P
        prof += [(0.0, L)]
    else:
        prof = [(0.0, 0.0), (r, 0.0), (r, L - tip), (0.0, L)]
    body = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    # pan head: flat top, rounded edge
    head = (cq.Workplane("XZ").moveTo(0, 0).lineTo(dk / 2, 0).lineTo(dk / 2, -0.4 * k)
            .threePointArc((0.47 * dk, -0.8 * k), (0.36 * dk, -k)).lineTo(0, -k).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)))
    # Phillips recess: two crossed slots
    w, ln, dep = 0.13 * dk, 0.52 * dk, 0.6 * k
    cross = (cq.Workplane("XY").workplane(offset=-k - 0.1).rect(ln, w).extrude(dep + 0.1)
             .union(cq.Workplane("XY").workplane(offset=-k - 0.1).rect(w, ln).extrude(dep + 0.1)))
    return head.union(body).cut(cross)


def nylon_insert(spec: dict):
    """The nylon ring of a nylon-insert locknut, in the nut's seat frame
    (for renders that colour it separately), or None."""
    if not spec.get("insert"):
        return None
    s, m, d = spec["s"], spec["m"], spec["d"]
    return (cq.Workplane("XY").workplane(offset=m - 0.45).circle(0.38 * s).circle(0.47 * d)
            .extrude(0.35).val())


def _mcmaster_model(path: Path, spec: dict):
    """Re-orient a McMaster STEP into the seat frame from its geometry:
    the axis is the bounding-box direction the (screw) part is longest in,
    or shortest in (nut); the head is the end with the larger section."""
    shp = cq.importers.importStep(str(path))
    comp = cq.Compound.makeCompound(shp.vals())
    bb = comp.BoundingBox()
    ext = np.array([bb.xlen, bb.ylen, bb.zlen])
    ctr = np.array([bb.center.x, bb.center.y, bb.center.z])
    axis = int(np.argmax(ext)) if spec["kind"] != "nut" else int(np.argmin(ext))
    e = np.zeros(3)
    e[axis] = 1.0
    lo, hi = ctr[axis] - ext[axis] / 2, ctr[axis] + ext[axis] / 2
    if spec["kind"] == "nut":
        sign, z0 = 1.0, lo
    else:
        # the end where the section is wider is the head
        def section_area(t):
            box_lo = [bb.xmin - 1, bb.ymin - 1, bb.zmin - 1]
            box_hi = [bb.xmax + 1, bb.ymax + 1, bb.zmax + 1]
            box_lo[axis], box_hi[axis] = t - 0.05, t + 0.05
            box = cq.Solid.makeBox(*(np.array(box_hi) - np.array(box_lo)), pnt=cq.Vector(*box_lo))
            return comp.intersect(box).Volume()
        a_lo = section_area(lo + 0.4 * spec["k"])
        a_hi = section_area(hi - 0.4 * spec["k"])
        k_seat = 0.0 if spec["kind"] == "fhcs" else spec["k"]   # flat head: seat = head top
        if a_lo > a_hi:      # head at the low end: shank runs +axis
            sign, z0 = 1.0, lo + k_seat
        else:
            sign, z0 = -1.0, hi - k_seat
    # rotation taking +axis*sign to +Z
    src = e * sign
    tgt = np.array([0.0, 0.0, 1.0])
    v = np.cross(src, tgt)
    c = float(np.dot(src, tgt))
    if np.linalg.norm(v) < 1e-9:
        R = np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + K + K @ K * (1.0 / (1.0 + c))
    off = ctr.copy()
    off[axis] = z0
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = -R @ off
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Shape.cast(comp.moved(cq.Location(tr)).wrapped)


def mcmaster_file(key: str) -> Path | None:
    pn = MCMASTER.get(key)
    if not pn:
        return None
    p = MCM_DIR / f"{pn}.step"
    return p if p.exists() else None


def models() -> dict[str, tuple[object, str]]:
    """key -> (shape in the seat frame, source)."""
    out = {}
    for key, spec in HARDWARE.items():
        f = mcmaster_file(key)
        if f is not None:
            out[key] = (_mcmaster_model(f, spec), f"McMaster-Carr {MCMASTER[key]}")
        else:
            out[key] = (_iso_model(spec).val(), "ISO-dimension stand-in")
    return out


# key -> McMaster-Carr part number.  Each was confirmed against two or more
# public listings that quote McMaster's own description (Clearpath Robotics
# fastener docs, reli-tool cross-references, published BOMs); see README,
# "Fasteners".  mcmaster.com itself refused the lab account on 2 Oct 2026.
# All are in McMaster's own (logged-out) catalog tables:
# components/mcmaster/catalog_rows.json.
MCMASTER: dict[str, str] = {
    "bhcs_m5x45": "92095A223",
    "locknut_m5": "93625A200",
    "shcs_m3x14": "91292A027",
    "shcs_m3x10": "91292A113",
    "locknut_m3": "93625A100",
    "shcs_m3x5": "91292A110",
    "bhcs_m3x20": "92095A185",
    "bhcs_m3x25": "92095A186",
    "fhcs_m3x30": "92125A140",
    "hexnut_m3": "91828A211",
    "shcs_m2p5x8": "91292A012",
    "wood_10x1p25": "93360A609",
}


HW_STEP_DIR = HERE / "components" / "hardware"
SHORT = {
    "bhcs_m5x45": "M5 x 45 button head screw",
    "locknut_m5": "M5 nylon-insert locknut",
    "shcs_m3x14": "M3 x 14 socket head screw",
    "shcs_m3x10": "M3 x 10 socket head screw",
    "locknut_m3": "M3 nylon-insert locknut",
    "shcs_m3x5": "M3 x 5 socket head screw",
    "bhcs_m3x20": "M3 x 20 button head screw",
    "bhcs_m3x25": "M3 x 25 button head screw",
    "fhcs_m3x30": "M3 x 30 flat head screw",
    "hexnut_m3": "M3 hex nut",
    "shcs_m2p5x8": "M2.5 x 8 socket head screw",
    "wood_10x1p25": "#10 x 1-1/4 in pan head wood screw",
}


def export_steps() -> dict[str, Path]:
    """Write every fastener, in its seat frame, to components/hardware/
    (the files the Onshape document imports)."""
    HW_STEP_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, (shape, src) in models().items():
        f = HW_STEP_DIR / f"{key}.step"
        cq.exporters.export(cq.Workplane("XY").add(shape), str(f))
        out[key] = f
    return out


def bom_rows(with_board: bool = False) -> list[dict]:
    """One row per hardware key, with quantity and the joints it is used in."""
    pl = fastener_placements(with_board=with_board)
    rows = []
    for key, spec in HARDWARE.items():
        uses = [j for _, k, j, _ in pl if k == key]
        if not uses:
            continue
        rows.append(dict(key=key, desc=spec["desc"], qty=len(uses),
                         joints=sorted(set(uses)), mcmaster=MCMASTER.get(key, "")))
    return rows


if __name__ == "__main__":
    export_steps()
    for r in bom_rows(with_board=True):
        print(f"{r['qty']:3d}  {r['mcmaster'] or '-':10s} {r['desc']}  ({', '.join(r['joints'])})")
    print(sum(r["qty"] for r in bom_rows(with_board=True)), "fasteners")
