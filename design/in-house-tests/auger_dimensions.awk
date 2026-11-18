# Dimensioned section drawing of the standard doser auger: the #193 Onshape "Auger", built from
# auger.fs (#172), the same part as the lab's Fusion threaded-auger-final. Writes an SVG to stdout:
#
#   awk -f auger_dimensions.awk > auger-dimensions.svg
#   google-chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 \
#       --window-size=1160,836 --screenshot=auger-dimensions.png auger-dimensions.svg
#
# Geometry in mm, from the Part Studio's feature list (cad/onshape-193/auger/part-studio-1/
# features.json.gz on PR #200's branch) and checked against its STL. z runs along the axis from the
# outlet face (z = 0) to the cap end (z = 250). The section is cut through the axis on the +X and -X
# half-planes: +X, where the flight and the cap thread start, is drawn above the axis; -X below it.

function px(v, z) { return X0[v] + S[v] * z }
function py(v, r) { return YA[v] - S[v] * r }          # r > 0 drawn up (+X), r < 0 down (-X)

function rwall(z) { return z < FUN ? ROUT + (RBORE - ROUT) * z / FUN : RBORE }   # funnel, then bore
function rcore(z) { return z <= FUN ? RTIP + (RCORE - RTIP) * z / FUN : RCORE }

# Cap-thread tooth radius at axial offset u from its crest centre (0 = no tooth). From the "Thread
# profile" sketch: 0.65 crest flat at r 13, 0.5 rounds, flanks 1 axial per 6 radial.
function tooth(u,    d) {
    if (u < 0) u = -u
    if (u <= 0.326438) return 13
    if (u <= 0.819634) { d = u - 0.326438; return 12.5 + sqrt(0.25 - d * d) }
    if (u <= 1.083333) return 12.582203 - (u - 0.819634) * 6
    return 0
}
# Outside radius at z on the +X side (side = 1) or the -X side (side = -1), above the gear.
function rout(z, side,    r, k, zc, t) {
    r = (z < ZSH) ? RTUBE : RNECK
    for (k = 0; k < 8; k++) {
        zc = (side > 0 ? ZTH : ZTH + TP / 2) + k * TP
        t = tooth(z - zc)
        if (t > r) r = t
    }
    return r
}

function line(x1, y1, x2, y2, cls) {
    printf "<line class=\"%s\" x1=\"%.2f\" y1=\"%.2f\" x2=\"%.2f\" y2=\"%.2f\"/>\n", cls, x1, y1, x2, y2
}
function text(x, y, s, cls, anchor) {
    printf "<text class=\"%s\" x=\"%.2f\" y=\"%.2f\" text-anchor=\"%s\">%s</text>\n", cls, x, y, anchor, s
}
function leader(x1, y1, x2, y2, x3, y3) {
    printf "<path class=\"leader\" d=\"M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f\"/>\n", x1, y1, x2, y2, x3, y3
}
function dline(x1, y1, x2, y2) {
    printf "<line class=\"dim\" x1=\"%.2f\" y1=\"%.2f\" x2=\"%.2f\" y2=\"%.2f\" marker-start=\"url(#arr)\" marker-end=\"url(#arr)\"/>\n", x1, y1, x2, y2
}
function ext(x, yfrom, yto,    d) { d = (yto > yfrom) ? 1 : -1; line(x, yfrom, x, yto + 5 * d, "ext") }
# Horizontal dimension from x1 to x2 at height y; extension lines start at yf1 and yf2.
function hdim(x1, x2, y, label, yf1, yf2) {
    ext(x1, yf1, y); ext(x2, yf2, y); dline(x1, y, x2, y); text((x1 + x2) / 2, y - 4, label, "dt", "middle")
}
function path(v, n, zs, rs, cls,    i, s) {
    s = sprintf("M%.2f,%.2f", px(v, zs[1]), py(v, rs[1]))
    for (i = 2; i <= n; i++) s = s sprintf(" L%.2f,%.2f", px(v, zs[i]), py(v, rs[i]))
    printf "<path class=\"%s\" d=\"%s Z\"/>\n", cls, s
}
# Cut face of the wall (tube, funnel, gear, cap thread) on one side, from the outlet to zmax.
function wall(v, side, zmax,    n, i, z, zprev, zs, rs) {
    n = 0
    n++; zs[n] = 0; rs[n] = side * ROUT
    n++; zs[n] = 0; rs[n] = side * RTUBE
    if (zmax > ZG0) {
        n++; zs[n] = ZG0; rs[n] = side * RTUBE
        n++; zs[n] = ZG0; rs[n] = side * RGEAR
        n++; zs[n] = ZG1; rs[n] = side * RGEAR
        n++; zs[n] = ZG1; rs[n] = side * RTUBE
        zprev = 0
        for (i = 0; i <= 700; i++) {               # z 215 .. 250 in 0.05 steps
            z = 215 + i * 0.05
            if (zprev < ZSH && z >= ZSH) {         # the shoulder at z = 225: Ø25 body to Ø23 neck
                n++; zs[n] = ZSH; rs[n] = side * rout(ZSH - 1e-6, side)
                n++; zs[n] = ZSH; rs[n] = side * rout(ZSH, side)
            }
            n++; zs[n] = z; rs[n] = side * rout(z, side)
            zprev = z
        }
    } else {
        n++; zs[n] = zmax; rs[n] = side * RTUBE
    }
    n++; zs[n] = zmax; rs[n] = side * RBORE
    n++; zs[n] = FUN; rs[n] = side * RBORE
    path(v, n, zs, rs, "cut")
}
function core(v, zmax,    zs, rs, ze) {
    ze = (zmax < ZFL) ? zmax : ZFL
    zs[1] = 0; rs[1] = -RTIP; zs[2] = FUN; rs[2] = -RCORE; zs[3] = ze; rs[3] = -RCORE
    zs[4] = ze; rs[4] = RCORE; zs[5] = FUN; rs[5] = RCORE; zs[6] = 0; rs[6] = RTIP
    path(v, 6, zs, rs, "cut")
}
# Flight blades cut by the section: on +X at z = k P, on -X at z = (k + 1/2) P; each FT thick, from
# the core to the wall. The last one (+X, z = 83.33) sits on the end of the core, from r 0.4.
function blades(v, zmax,    k, z0, z1, side, zs, rs) {
    for (k = 0; k <= 8; k++) {
        for (side = 1; side >= -1; side -= 2) {
            z0 = (side > 0 ? k : k + 0.5) * P
            z1 = z0 + FT
            if (z0 > ZFL + 1e-6 || z1 > zmax) continue
            zs[1] = z0; rs[1] = side * rcore(z0); zs[2] = z0; rs[2] = side * rwall(z0)
            zs[3] = z1; rs[3] = side * rwall(z1); zs[4] = z1; rs[4] = side * rcore(z1)
            if (z0 >= ZFL - 1e-6) { rs[1] = side * RTIP; rs[4] = side * RTIP }
            path(v, 4, zs, rs, "cut")
        }
    }
}

BEGIN {
    # ---- geometry (mm), from the feature list ----
    L = 250; RTUBE = 12.5; RBORE = 10.5; ROUT = 1.5; FUN = 12; RCORE = 4; RTIP = 0.4
    P = 83.33 / 8; FT = 0.5; ZFL = 83.33                        # flight pitch and thickness; core top
    ZG0 = 83.333 - 5; ZG1 = 83.333 + 5; RGEAR = 23; RPITCH = 22    # 44T module-1 gear, 10 wide
    ZSH = 225; RNECK = 11.5; TP = 3.5; ZTH = ZSH - 1.65          # neck, thread pitch, first +X crest
    W = 1160; H = 836

    # ---- views: 1 = the whole auger at 4 px/mm; 2 = the outlet end at 12 px/mm ----
    X0[1] = 70;  S[1] = 4;  YA[1] = 230
    X0[2] = 110; S[2] = 12; YA[2] = 640

    print "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" W "\" height=\"" H "\" viewBox=\"0 0 " W " " H "\">"
    print "<defs><marker id=\"arr\" viewBox=\"0 0 10 10\" refX=\"10\" refY=\"5\" markerWidth=\"8\" markerHeight=\"8\" markerUnits=\"userSpaceOnUse\" orient=\"auto-start-reverse\"><path d=\"M0,1.5 L10,5 L0,8.5 z\" fill=\"#222\"/></marker></defs>"
    print "<style>"
    print "text { font-family: 'DejaVu Sans', Arial, sans-serif; fill: #222; }"
    print ".title { font-size: 17px; font-weight: bold; }"
    print ".dt { font-size: 12.5px; } .lbl { font-size: 11.5px; fill: #444; } .note { font-size: 13px; } .noteb { font-size: 13px; font-weight: bold; }"
    print ".cut { fill: #cfe0f1; stroke: #1f4e79; stroke-width: 1.1; stroke-linejoin: round; }"
    print ".dim { stroke: #222; stroke-width: 0.8; } .ext { stroke: #666; stroke-width: 0.6; }"
    print ".axis { stroke: #888; stroke-width: 0.8; stroke-dasharray: 14 3 2 3; fill: none; }"
    print ".pitch { stroke: #1f4e79; stroke-width: 0.7; stroke-dasharray: 8 2 2 2; }"
    print ".phantom { fill: none; stroke: #888; stroke-width: 0.9; stroke-dasharray: 5 3; }"
    print ".leader { stroke: #444; stroke-width: 0.6; fill: none; }"
    print ".box { fill: #f7f9fb; stroke: #c9d3dc; stroke-width: 1; }"
    print "</style>"
    print "<rect width=\"100%\" height=\"100%\" fill=\"#fff\"/>"

    text(20, 26, "Standard doser auger: section through the axis, drawn to scale. Dimensions in mm.", "title", "start")

    # ================= the whole auger =================
    v = 1
    printf "<path class=\"phantom\" d=\"M%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f L%.2f,%.2f\"/>\n", \
        px(v, 225), py(v, 11.75), px(v, 225), py(v, 14.5), px(v, 250), py(v, 14.5), px(v, 252), py(v, 12.5), \
        px(v, 252), py(v, -12.5), px(v, 250), py(v, -14.5), px(v, 225), py(v, -14.5), px(v, 225), py(v, -11.75)
    wall(v, 1, L); wall(v, -1, L); core(v, L); blades(v, L)
    line(px(v, -1.5), YA[v], px(v, 254), YA[v], "axis")
    line(px(v, ZG0 - 1.5), py(v, RPITCH), px(v, ZG1 + 1.5), py(v, RPITCH), "pitch")
    line(px(v, ZG0 - 1.5), py(v, -RPITCH), px(v, ZG1 + 1.5), py(v, -RPITCH), "pitch")
    text(px(v, -1.5), YA[v] - 8, "outlet", "lbl", "end")
    text(px(v, 252) + 6, py(v, 14.5) + 2, "cap", "lbl", "start")
    text(px(v, 252) + 6, py(v, 14.5) + 16, "(dashed)", "lbl", "start")

    # lengths along the outside, above
    ytube = py(v, RTUBE) - 3; ygear = py(v, RGEAR) - 3; ycap = py(v, 14.5) - 3
    hdim(px(v, 0), px(v, ZG0), 110, "78.33", ytube, ygear)
    hdim(px(v, ZG0), px(v, ZG1), 110, "", ygear, ygear)          # label beside it: the gap is narrow
    text(px(v, ZG1) + 8, 106, "10 (gear)", "dt", "start")
    hdim(px(v, ZSH), px(v, L), 110, "25 (thread)", ycap, ycap)
    hdim(px(v, 0), px(v, ZSH), 82, "225 (Ø25 body)", 110, 110)
    hdim(px(v, 0), px(v, L), 54, "250", 82, 110)

    # lengths inside, below
    ytb = py(v, -RTUBE) + 3; ygb = py(v, -RGEAR) + 3
    hdim(px(v, 0), px(v, FUN), 352, "12", ytb, ytb)
    hdim(px(v, FUN), px(v, ZFL), 352, "71.33", ytb, ygb)
    hdim(px(v, ZFL), px(v, L), 352, "166.67", ygb, py(v, -14.5) + 3)
    text(px(v, FUN / 2), 368, "funnel", "lbl", "middle")
    text(px(v, (FUN + ZFL) / 2), 368, "flight + Ø8 core", "lbl", "middle")
    text(px(v, (ZFL + L) / 2), 368, "open Ø21 bore (reservoir): no core, no flight", "lbl", "middle")
    hdim(px(v, 0), px(v, ZFL), 396, "83.33 = 8 turns × 10.416 pitch", 352, 352)

    # diameters
    dline(px(v, 140), py(v, RTUBE), px(v, 140), py(v, -RTUBE)); text(px(v, 140) - 5, YA[v] - 6, "Ø25", "dt", "end")
    dline(px(v, 160), py(v, RBORE), px(v, 160), py(v, -RBORE)); text(px(v, 160) + 5, YA[v] - 6, "Ø21", "dt", "start")
    line(px(v, ZG1) + 3, py(v, RGEAR), px(v, ZG1) + 30, py(v, RGEAR), "ext")
    line(px(v, ZG1) + 3, py(v, -RGEAR), px(v, ZG1) + 30, py(v, -RGEAR), "ext")
    dline(px(v, ZG1) + 24, py(v, RGEAR), px(v, ZG1) + 24, py(v, -RGEAR))
    text(px(v, ZG1) + 29, YA[v] - 6, "Ø46 (44 T, m 1)", "dt", "start")
    leader(px(v, 239.1), py(v, -13) + 1, px(v, 236), 300, px(v, 200), 300)
    text(px(v, 200) - 4, 304, "cap thread: Ø26 crest on Ø23 neck, 3.5 pitch, RH", "lbl", "end")

    # ================= the outlet end =================
    v = 2; ZD = 26
    text(20, 456, "Detail: the outlet end, at 3× the scale above", "noteb", "start")
    wall(v, 1, ZD); wall(v, -1, ZD); core(v, ZD); blades(v, ZD)
    line(px(v, -1), YA[v], px(v, ZD + 1), YA[v], "axis")
    s = sprintf("M%.2f,%.2f", px(v, ZD), py(v, RTUBE) - 6)          # break line
    for (i = 1; i <= 12; i++) s = s sprintf(" L%.2f,%.2f", px(v, ZD) + ((i % 2) ? 5 : -5), py(v, RTUBE) - 6 + i * (2 * S[v] * RTUBE + 12) / 12)
    printf "<path class=\"leader\" d=\"%s\"/>\n", s
    # outlet
    line(px(v, 0) - 3, py(v, ROUT), px(v, 0) - 34, py(v, ROUT), "ext")
    line(px(v, 0) - 3, py(v, -ROUT), px(v, 0) - 34, py(v, -ROUT), "ext")
    dline(px(v, 0) - 28, py(v, ROUT), px(v, 0) - 28, py(v, -ROUT)); text(px(v, 0) - 33, YA[v] + 5, "Ø3", "dt", "end")
    leader(px(v, 0) + 1, YA[v] + 3, px(v, 0) - 14, YA[v] + 60, px(v, 0) - 90, YA[v] + 60)
    text(px(v, 0) - 90, YA[v] + 75, "Ø0.8 core tip", "lbl", "start")
    # funnel
    hdim(px(v, 0), px(v, FUN), py(v, -RTUBE) + 26, "12", py(v, -RTUBE) + 3, py(v, -RBORE) + 3)
    leader(px(v, 8), py(v, -rwall(8)), px(v, 9.5), py(v, -RTUBE) + 14, px(v, 16), py(v, -RTUBE) + 14)
    text(px(v, 16) + 4, py(v, -RTUBE) + 18, "cone 36.9° from the axis", "lbl", "start")
    # core, bore and tube
    dline(px(v, 17.5), py(v, RCORE), px(v, 17.5), py(v, -RCORE)); text(px(v, 17.5) + 5, py(v, -RCORE) + 16, "Ø8", "dt", "start")
    dline(px(v, 24), py(v, RBORE), px(v, 24), py(v, -RBORE)); text(px(v, 24) - 5, py(v, -RBORE) - 8, "Ø21", "dt", "end")
    line(px(v, ZD) + 8, py(v, RTUBE), px(v, ZD) + 32, py(v, RTUBE), "ext")
    line(px(v, ZD) + 8, py(v, -RTUBE), px(v, ZD) + 32, py(v, -RTUBE), "ext")
    dline(px(v, ZD) + 26, py(v, RTUBE), px(v, ZD) + 26, py(v, -RTUBE)); text(px(v, ZD) + 31, YA[v] + 5, "Ø25", "dt", "start")
    # flight
    hdim(px(v, P), px(v, 2 * P), py(v, 7.6), "10.416 pitch", py(v, 7.6), py(v, 7.6))
    leader(px(v, 2 * P + FT / 2), py(v, 9.5), px(v, 2 * P + 2), py(v, RTUBE) - 14, px(v, 2 * P + 3), py(v, RTUBE) - 14)
    text(px(v, 2 * P + 3) + 4, py(v, RTUBE) - 10, "flight 0.5 thick", "lbl", "start")
    leader(px(v, FT / 2), py(v, 1.0), px(v, 3), py(v, RTUBE) - 14, px(v, 6), py(v, RTUBE) - 14)
    text(px(v, 6) + 4, py(v, RTUBE) - 10, "flight starts at the outlet face", "lbl", "start")

    # ================= notes =================
    bx = 510; by = 440
    printf "<rect class=\"box\" x=\"%d\" y=\"%d\" width=\"%d\" height=\"%d\" rx=\"4\"/>\n", bx, by, W - bx - 16, H - by - 16
    x = bx + 14; xt = x + 70; y = by + 26; dy = 19.5
    n = 0
    k[++n] = "Flight"; t[n] = "1 start, right-handed, 10.416 pitch, 8 turns (z 0 to 83.33)"
    k[++n] = "";       t[n] = "0.5 thick axially; from the core to the bore, and down"
    k[++n] = "";       t[n] = "the funnel to the outlet face"
    k[++n] = "Core";   t[n] = "solid Ø8 from z 12 to 83.33; a cone below it, from Ø0.8"
    k[++n] = "";       t[n] = "at the outlet face to Ø8 at z 12"
    k[++n] = "Outlet"; t[n] = "Ø3 hole around the Ø0.8 core tip: a 6.6 mm² annulus"
    k[++n] = "Gear";   t[n] = "spur, 44 teeth, module 1, 20° pressure angle; tip Ø46,"
    k[++n] = "";       t[n] = "pitch Ø44, root Ø41.7; 10 wide, z 78.33 to 88.33. Meshes the"
    k[++n] = "";       t[n] = "20-tooth stepper pinion, axes 32 apart: 2.2 stepper turns per turn"
    k[++n] = "Thread"; t[n] = "for the cap: right-handed, 3.5 pitch, Ø26 crest on a Ø23"
    k[++n] = "";       t[n] = "neck from z 225 to 250; the first crest is at z 223.35"
    k[++n] = "Cap";    t[n] = "separate part: Ø29 × 27, 25 deep, Ø23.5 bore"
    k[++n] = "Inside"; t[n] = "79 mL to the open end: funnel 1.3, flighted section 20.1,"
    k[++n] = "";       t[n] = "open bore 57.7"
    k[++n] = "Solid";  t[n] = "53.3 cm³; printed outlet-down, nozzle 0.4 mm or smaller"
    for (i = 1; i <= n; i++) {
        if (k[i] != "") text(x, y, k[i], "noteb", "start")
        text(xt, y, t[i], "note", "start"); y += dy
    }
    y += 8
    text(x, y, "Cut on the +X half-plane (drawn above the axis) and on -X (below). z = 0 at the outlet.", "lbl", "start"); y += 16
    text(x, y, "From the #193 Onshape Auger's feature list (PR #200's branch), built from auger.fs (#172).", "lbl", "start")

    print "</svg>"
}
