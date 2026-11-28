#!/usr/bin/python3
"""Build fc1.kicad_pcb from fc1_design.py with KiCad 9's pcbnew (system python).

  /usr/bin/python3 build_pcb.py place    # footprints, nets, hand-routed guard area -> fc1.kicad_pcb
  /usr/bin/python3 build_pcb.py dsn      # write fc1.dsn for FreeRouting (guard area kept out)
  /usr/bin/python3 build_pcb.py finish   # import fc1.ses, stitch GND, pours, silkscreen, mask openings
FreeRouting (v2.6.0, Java 25) is run between `dsn` and `finish`, see README.md.
"""
import math
import os
import re
import sys
import uuid

import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I_MM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fc1_design as D  # noqa: E402

PCB = os.path.join(HERE, "fc1.kicad_pcb")
NS = uuid.UUID("6f1c2a52-6a1e-4c47-9a57-fc1fc1fc1fc1")
FPDIR = "/usr/share/kicad/footprints/"


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def netname(n):
    return "/" + n


def nc_name(ref, pin, symname):
    return "unconnected-(%s-%s-Pad%s)" % (ref, symname, pin)


# names of the unconnected pins as eeschema writes them
NC_PIN_NAMES = {("K1", "6"): "SHLD", ("U1", "3"): "IC", ("U3", "6"): "AIN2", ("U3", "7"): "AIN3",
                ("U3", "2"): "ALERT{slash}RDY"}


def pt(x, y):
    return VECTOR2I_MM(x, y)


def get_net(board, name):
    n = board.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
    return n


def add_track(board, pts, net, width, layer=pcbnew.F_Cu, locked=True):
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(x0, y0))
        t.SetEnd(pt(x1, y1))
        t.SetWidth(FromMM(width))
        t.SetLayer(layer)
        t.SetNet(net)
        t.SetLocked(locked)
        board.Add(t)


def add_via(board, x, y, net, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(FromMM(d))
    v.SetDrill(FromMM(drill))
    v.SetNet(net)
    board.Add(v)
    return v


def poly_zone(board, pts, layer, net=None, priority=0, clearance=None, rule_area=False, name="",
              thermal=True, min_w=0.25):
    z = pcbnew.ZONE(board)
    if rule_area:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowCopperPour(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
    else:
        z.SetLayer(layer)
        z.SetNet(net)
        z.SetAssignedPriority(priority)
        z.SetMinThickness(FromMM(min_w))
        if clearance is not None:
            z.SetLocalClearance(FromMM(clearance))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
        z.SetThermalReliefGap(FromMM(0.3))
        z.SetThermalReliefSpokeWidth(FromMM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(FromMM(x), FromMM(y))
    board.Add(z)
    return z


def add_text(board, text, x, y, size=1.0, layer=pcbnew.F_SilkS, angle=0, thick=0.15, justify=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(FromMM(size), FromMM(size)))
    t.SetTextThickness(FromMM(thick))
    if angle:
        t.SetTextAngleDegrees(angle)
    if layer in (pcbnew.B_SilkS, pcbnew.B_Cu, pcbnew.B_Mask):
        t.SetMirrored(True)
    if justify < 0:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif justify > 0:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    board.Add(t)


def add_poly_shape(board, pts, layer, filled=True, width=0.0):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetFilled(filled)
    s.SetLayer(layer)
    s.SetWidth(FromMM(width))
    s.SetPolyPoints([pt(x, y) for x, y in pts])
    board.Add(s)


# ------------------------------------------------------------------- place
def stage_place():
    board = pcbnew.NewBoard(PCB)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    board.SetCopperLayerCount(2)
    ds.SetBoardThickness(FromMM(1.6))

    # outline
    W, H = D.BOARD_W, D.BOARD_H
    corners = [(0, 0), (W, 0), (W, H), (0, H), (0, 0)]
    for (x0, y0), (x1, y1) in zip(corners[:-1], corners[1:]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(x0, y0))
        s.SetEnd(pt(x1, y1))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(FromMM(0.1))
        board.Add(s)

    for ref, (lib_id, value, fpid, pinmap, fields) in D.PARTS.items():
        lib, name = fpid.split(":")
        libpath = os.path.join(HERE, "fc1.pretty") if lib == "fc1" else FPDIR + lib + ".pretty"
        fp = pcbnew.FootprintLoad(libpath, name)
        assert fp is not None, fpid
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("sym", ref)))
        fp.SetSheetname("/")
        fp.SetSheetfile("fc1.kicad_sch")
        for k, v in fields.items():
            fp.SetField(k, v)
            f = fp.GetFieldByName(k)
            f.SetVisible(False)
            f.SetLayer(pcbnew.F_Fab)
        if ref in D.DNP:
            fp.SetDNP(True)
        if ref in D.NOT_IN_BOM:
            fp.SetExcludedFromBOM(True)
        x, y, rot, side = D.PLACE[ref]
        board.Add(fp)
        fp.SetPosition(pt(x, y))
        if side == "B":
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in pinmap:
                net = pinmap[num]
                if net is None:
                    nm = nc_name(ref, num, NC_PIN_NAMES[(ref, num)])
                    pad.SetNet(get_net(board, nm))
                else:
                    pad.SetNet(get_net(board, netname(net)))
        # small reference text
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(FromMM(0.8), FromMM(0.8)))
        fp.Reference().SetTextThickness(FromMM(0.12))

    hand_route(board)
    pcbnew.SaveBoard(PCB, board)
    report_overlaps(board)
    print("placed", len(board.GetFootprints()), "footprints")


def hand_route(board):
    """Guarded input area and the feedback network, routed by hand (locked)."""
    SUM = get_net(board, "/SUM")
    GRD = get_net(board, "/GUARD")
    OUT = get_net(board, "/OUT")
    CF2 = get_net(board, "/CF2")
    w_sum = D.NETCLASS["HiZ"]["track"]
    # input: BNC centre -> U1 pin 8 (-IN), straight along y = 21.5
    add_track(board, [(8.5, 21.5), (23.095, 21.5)], SUM, w_sum)
    # SUM bus: up through C1.1, R1.1, C2.1 to K1 pin 1
    add_track(board, [(18.5, 21.5), (18.5, 4.0)], SUM, w_sum)
    # guard pins 7 and 2 joined under the package
    add_track(board, [(24.365, 21.5), (24.365, 26.45)], GRD, 0.4)
    # OUT: U1 pin 6 -> C1.2 -> R1.2 -> JP1 pin 2 ; CF2: C2.2 -> JP1 pin 1
    jx, j1y = D.PLACE["JP1"][0], D.PLACE["JP1"][1]
    add_track(board, [(25.635, 21.5), (25.635, 17.5), (21.62, 17.5), (21.62, 14.0), (jx - 1.0, 14.0),
                      (jx, j1y + 2.54)], OUT, 0.3)
    add_track(board, [(21.62, 10.5), (jx - 1.0, 10.5), (jx, j1y)], CF2, 0.3)
    # BNC shell -> JP5 centre pad; JP5 pad 3 -> guard copper (shell can be tied to GND or GUARD)
    SHELL = get_net(board, "/SHELL")
    add_track(board, [(5.96, 21.5), (5.96, 29.2), (9.0, 29.2), (9.0, 31.0)], SHELL, 0.3)
    add_track(board, [(10.3, 31.0), (10.3, 24.0)], GRD, 0.3)


def report_overlaps(board):
    fps = list(board.GetFootprints())
    boxes = {}
    for fp in fps:
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() == 0:
            continue
        bb = cy.BBox()
        boxes[fp.GetReference()] = (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
    refs = sorted(boxes)
    bad = 0
    for i, a in enumerate(refs):
        ax0, ay0, ax1, ay1 = boxes[a]
        if a not in ("J1",) and (ax0 < -0.01 or ay0 < -0.01 or ax1 > D.BOARD_W + 0.01 or ay1 > D.BOARD_H + 0.01):
            print("  off-board courtyard %s %.2f %.2f %.2f %.2f" % (a, ax0, ay0, ax1, ay1))
        for b in refs[i + 1:]:
            bx0, by0, bx1, by1 = boxes[b]
            ox = min(ax1, bx1) - max(ax0, bx0)
            oy = min(ay1, by1) - max(ay0, by0)
            if ox > 0.01 and oy > 0.01:
                # boxes overlap; check the real courtyard polygons
                pa = board.FindFootprintByReference(a).GetCourtyard(pcbnew.F_CrtYd)
                pb = board.FindFootprintByReference(b).GetCourtyard(pcbnew.F_CrtYd)
                inter = pcbnew.SHAPE_POLY_SET(pa)
                inter.BooleanIntersection(pb)
                if inter.OutlineCount() and inter.Area() > 1e6 * 0.0001:
                    print("  OVERLAP %s / %s  (%.2f x %.2f mm box)" % (a, b, ox, oy))
                    bad += 1
    print("courtyard overlaps:", bad)


# --------------------------------------------------------------------- dsn
def stage_dsn():
    board = pcbnew.LoadBoard(PCB)
    keep = poly_zone(board, D.GUARD_POLY, None, rule_area=True, name="guard-keepout")
    ok = pcbnew.ExportSpecctraDSN(board, os.path.join(HERE, "fc1.dsn"))
    print("dsn", ok)
    # do not let the autorouter touch the guarded nets
    txt = open(os.path.join(HERE, "fc1.dsn")).read()
    for n in ("/SUM", "/GUARD"):
        txt = re.sub(r'\(net "?%s"?\s*\(pins[^)]*\)\s*\)' % re.escape(n), "", txt)
    open(os.path.join(HERE, "fc1.dsn"), "w").write(txt)


# ------------------------------------------------------------------ finish
def poly_set(pts):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in pts:
        ps.Append(FromMM(x), FromMM(y))
    return ps


def zone_from_polyset(board, ps, layer, net, priority, clearance, name, thermal=True):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetAssignedPriority(priority)
    z.SetMinThickness(FromMM(0.25))
    z.SetLocalClearance(FromMM(clearance))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(FromMM(0.3))
    z.SetThermalReliefSpokeWidth(FromMM(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName(name)
    z.Outline().RemoveAllContours()
    z.Outline().Append(ps)
    board.Add(z)
    return z


def copper_items(board):
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            items.append(p)
    for t in board.GetTracks():
        items.append(t)
    return items


def free_spot(board, items, x, y, r, layers=(pcbnew.F_Cu, pcbnew.B_Cu), net=None):
    c = pt(x, y)
    for it in items:
        if net is not None and it.GetNetCode() == net.GetNetCode():
            continue
        for L in layers:
            if not it.IsOnLayer(L):
                continue
            if it.GetEffectiveShape(L).Collide(c, FromMM(r)):
                return False
    for fp in board.GetFootprints():     # holes of mounting holes
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                if math.hypot(ToMM(p.GetPosition().x) - x, ToMM(p.GetPosition().y) - y) < ToMM(p.GetDrillSize().x) / 2 + r + 0.3:
                    return False
    return True


def inside_poly(x, y, poly):
    n, ins = len(poly), False
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            ins = not ins
    return ins


def near_poly(x, y, poly, m):
    return any(inside_poly(x + dx, y + dy, poly) for dx in (-m, 0, m) for dy in (-m, 0, m))


def stitch_gnd(board, GND):
    items = copper_items(board)
    placed = []
    W, H = D.BOARD_W, D.BOARD_H
    y = 1.2
    while y < H - 1.0:
        x = 1.2
        while x < W - 1.0:
            ok = (not near_poly(x, y, D.GUARD_POLY, 1.2)) and all(math.hypot(x - a, y - b) > 4.6 for a, b in placed)
            ok = ok and not any(overlap((x - 0.5, y - 0.5, x + 0.5, y + 0.5), text_box(tx, ty, tt, sz, an, jj))
                                for (tt, tx, ty, sz, an, jj, _s) in D.SILK)
            if ok and free_spot(board, items, x, y, 0.3 + 0.35):
                placed.append((x, y))
            x += 0.8
        y += 0.8
    for x, y in placed:
        add_via(board, x, y, GND)
    return placed


def text_box(x, y, txt, size, angle, just=0):
    w = 0.85 * size * len(txt) + 0.2
    h = size + 0.25
    if angle in (90, 270, -90):
        w, h = h, w
    if just < 0:
        return (x - 0.1, y - h / 2, x + w, y + h / 2)
    if just > 0:
        return (x - w, y - h / 2, x + 0.1, y + h / 2)
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def overlap(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def place_refdes(board):
    """Put each reference designator next to its part, clear of pads, holes and other text."""
    W, H = D.BOARD_W, D.BOARD_H
    blocked = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            blocked.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
    xs = [q[0] for q in D.GUARD_POLY]
    ys = [q[1] for q in D.GUARD_POLY]
    # the guard region has no solder mask: keep all silk out of it (approximate by its parts)
    guard_boxes = D.GUARD_BOXES
    texts = []
    for (txt, x, y, size, angle, just, side) in D.SILK:
        if side == "F":
            texts.append(text_box(x, y, txt, size, angle, just))
    fps = sorted(board.GetFootprints(), key=lambda f: f.GetReference())
    silk_of = {}
    for fp in fps:
        boxes = []
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT":
                bb = g.GetBoundingBox()
                boxes.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
        silk_of[fp.GetReference()] = boxes
    hidden = []
    for fp in fps:
        ref = fp.GetReference()
        t = fp.Reference()
        if ref.startswith("H") or D.REF_POS.get(ref) == "hide":
            t.SetVisible(False)
            continue
        if ref in D.REF_POS:
            tx, ty, ang = D.REF_POS[ref]
            t.SetTextSize(pcbnew.VECTOR2I(FromMM(0.8), FromMM(0.8)))
            t.SetTextThickness(FromMM(0.13))
            t.SetPosition(pt(tx, ty))
            t.SetTextAngleDegrees(ang)
            texts.append(text_box(tx, ty, ref, 0.8, ang))
            continue
        cy = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        x0, y0, x1, y1 = ToMM(cy.GetLeft()), ToMM(cy.GetTop()), ToMM(cy.GetRight()), ToMM(cy.GetBottom())
        cx, cyy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for size in (0.8, 0.7):
            cands = [(cx, y0 - size / 2 - 0.15, 0), (cx, y1 + size / 2 + 0.15, 0),
                     (x0 - 0.8 * len(ref) * size / 2 - 0.1, cyy, 0), (x1 + 0.8 * len(ref) * size / 2 + 0.1, cyy, 0),
                     (x0 - size / 2 - 0.15, cyy, 90), (x1 + size / 2 + 0.15, cyy, 90),
                     (cx, cyy, 0), (cx, cyy, 90)]
            for (tx, ty, ang) in cands:
                bx = text_box(tx, ty, ref, size, ang)
                if bx[0] < 0.4 or bx[1] < 0.4 or bx[2] > W - 0.4 or bx[3] > H - 0.4:
                    continue
                others = [b for r2, bl in silk_of.items() if r2 != ref for b in bl]
                if any(overlap(bx, g, 0.1) for g in blocked + texts + guard_boxes + others):
                    continue
                best = (tx, ty, ang, size, bx)
                break
            if best:
                break
        if best is None:
            t.SetVisible(False)
            hidden.append(ref)
            continue
        tx, ty, ang, size, bx = best
        t.SetTextSize(pcbnew.VECTOR2I(FromMM(size), FromMM(size)))
        t.SetTextThickness(FromMM(0.12 if size < 0.8 else 0.13))
        t.SetPosition(pt(tx, ty))
        t.SetTextAngleDegrees(ang)
        t.SetKeepUpright(True)
        texts.append(bx)
    print("refdes hidden (no room):", hidden)


def trim_footprint_silk(board):
    """Drop footprint silk that would sit on the bare guard copper or within 0.4 mm of the board edge."""
    W, H = D.BOARD_W, D.BOARD_H
    guard_boxes = D.GUARD_BOXES
    n = 0
    for fp in board.GetFootprints():
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() != pcbnew.F_SilkS or g.GetClass() == "PCB_TEXT":
                continue
            bb = g.GetBoundingBox()
            b = (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))
            if any(overlap(b, gb, 0.15) for gb in guard_boxes) or b[0] < 0.4 or b[1] < 0.4 or b[2] > W - 0.4 or b[3] > H - 0.4:
                fp.Remove(g)
                n += 1
    print("footprint silk items removed:", n)


def stage_finish(ses=True):
    board = pcbnew.LoadBoard(PCB)
    if ses:
        ok = pcbnew.ImportSpecctraSES(board, os.path.join(HERE, "fc1.ses"))
        print("ses import", ok)
        tiny = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLength() < FromMM(0.05)]
        for t in tiny:
            board.Remove(t)
        print("removed tiny autorouter stubs:", len(tiny))
    GND = get_net(board, "/GND")
    GRD = get_net(board, "/GUARD")
    W, H = D.BOARD_W, D.BOARD_H
    # GND stitching vias first (they must not land in the guard area)
    vias = stitch_gnd(board, GND)
    print("GND stitching vias:", len(vias))
    for (x, y) in D.GUARD_VIAS:
        add_via(board, x, y, GRD)
    gnd_ps = poly_set([(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)])
    hole = poly_set(D.GUARD_POLY)
    hole.Inflate(FromMM(0.4), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, FromMM(0.01))
    gnd_ps.BooleanSubtract(hole)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        zone_from_polyset(board, poly_set(D.GUARD_POLY), layer, GRD, 2, 0.2, "GUARD", thermal=False)
        zone_from_polyset(board, gnd_ps, layer, GND, 1, 0.3, "GND")
    for layer in (pcbnew.F_Mask, pcbnew.B_Mask):
        add_poly_shape(board, D.GUARD_POLY, layer)
    silkscreen(board)
    trim_footprint_silk(board)
    place_refdes(board)
    # drill/place origin at the board's lower-left corner (pos file: x right, y up)
    board.GetDesignSettings().SetAuxOrigin(pt(0, D.BOARD_H))
    board.GetDesignSettings().SetGridOrigin(pt(0, D.BOARD_H))
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("finished")


def silkscreen(board):
    for (txt, x, y, size, angle, just, side) in D.SILK:
        layer = pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS
        add_text(board, txt, x, y, size=size, angle=angle, justify=just, layer=layer,
                 thick=0.15 if size >= 1.0 else 0.12)


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "place"
    if st == "place":
        stage_place()
    elif st == "dsn":
        stage_dsn()
    elif st == "finish":
        stage_finish(ses=True)
    elif st == "finish-noses":
        stage_finish(ses=False)
