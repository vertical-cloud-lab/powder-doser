"""Dimensions for the chain-carousel test rig v5 (issue #128), in mm.

v5 is v4 with a real balance under the station (sgbaird, 2026-11-04: "the multi-doser needs to be using a real scale").
The dose falls straight into a beaker on an A&D HR-202i (220 g x 0.1 mg, 51 g x 0.01 mg fine range), the higher-capacity
0.1 mg sibling of the lab's HR-100A that design/brainstorming.md names. Nothing touches the balance but the beaker on its
riser. To make room, v4's station column (the P16, its guide cradle and cradle post, all standing in the balance's chamber)
is gone: the EC now rides on an 8 mm lift bar through its base, carried by two P16s beside the balance, and the bar's end
shoes run in vertical guides on two station posts (keeping the EC square on the rise, as v4's cradle walls did). The whole
carousel is 80 mm higher so the parked EC, the bar and the NEMA 34 clear the balance's top; the frame's front base rail
and both station rails are gone (the balance stands where they were), and the latch rail hangs from a 2020 beam off the
-y side. Everything down to "v4" below is v4's, unchanged unless a comment says "v5".


v4 is v3 with Sam's item 7 of 2026-10-29: the augers ride OUTSIDE the loop. Each module sits on its carriage's outer face
(the carriage still bolts to the A-1 tabs from outside), so at the loading position the auger faces the side hatch and comes
straight off its plate against the side tabs; at the station the module hangs under the bottom run and the electronics
carriage reaches up round the auger to dock on the plate's auger side. Everything else is v3's (below).

v3 was v2 with Sam's critiques of 2026-10-29 applied (augers still inside the loop): a kinematic dock with magnets
between his small electronics carriage and a new mounting plate, a guide that the carriage parks in on its own
kinematic seat, a spring-loaded door on every auger's outlet that the docked carriage pushes open, a latch that holds
the plate on its carriage upside down and is opened by a cam at the station, an acrylic enclosure with a front hatch
(scale) and a side hatch (swaps), side tabs at the loading position, no funnel, and the lab's A&D HR-100A modelled.
Everything down to "v3" below is v2's, unchanged unless a comment says so.

v2 is a vertical twin-chain loop: two #35 chains in vertical planes, one at
the front of the carriages (the auger's outlet/hinge end) and one at the
back (cap end). Each chain runs round four 32T sprockets on the corners of a
rectangle; the front and back sprockets at each corner share one shaft, so
the two chains can't drift out of step. The carriages bolt to an A-1 lug on
each chain from the outside of the loop and the modules ride on the inside,
between the chains. The station is on the bottom straight.

One place for every number the model uses. Purchased-part dimensions come
from the vendor's own tables (sources in BOM.md); printed-part numbers are
design choices. World frame: x along the augers (front chain's centre plane
at x = 0, back chain's at x = CHAIN_L), y across the loop (a positive chain
shift moves the bottom run toward +y; the machine runs the other way,
RUN_DIRECTION = -1), z up, bench top at z = 0.
"""
from __future__ import annotations

import math

# --- ANSI #35 roller chain (ASME B29.1; the Aobbmok listing on the ME order) ---
# Checked against Nitro's RC35 dimension table (nitrochain.com/35-roller-chain-10ft, read 2026-10-27; cad/vendor/AUDIT_other.md):
# P 3/8, b1 3/16, d1 (bushing) 0.200, L 0.488, d2 0.141, h2 0.346, T 0.050 in.
P = 9.525            # pitch (3/8")
BUSH_D = 5.08        # #35 is rollerless: the bushing (0.200") is what the teeth seat on
CHAIN_PIN_D = 3.58   # 0.141". Was PIN_D, which the 5 mm hinge pin further down overrode: the chain was drawn with 5 mm pins
W_IN = 4.78          # width between inner plates (0.188")
PLATE_T = 1.27       # 0.050"
PLATE_H = 8.79       # plate height, 0.346" (Nitro h2; was 9.0 = 0.354")
N_LINKS = 104        # per chain, cut from a 10 ft roll (two loops use 208 of its 320 links)
INNER_W = W_IN + 2 * PLATE_T              # 7.32, inner link across the plates
OUTER_GAP = INNER_W + 0.05                 # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T          # 9.91
PIN_LEN = 0.488 * 25.4                     # 12.40: Nitro's overall width L, riveted pin ends 1.24 mm proud (was 0.45 mm proud)
# v11 (Sam, 2026-11-25: "find a cheap but still good quality chain online, link it here, and apply those dimensions"): Nitro Chain
# RC35-1R-10FT (N2 series, $23.53 per 10 ft, read 2026-11-26, https://www.nitrochain.com/35-roller-chain-10ft): the numbers above
# are its product page's (P, b1, d1, d2, L, h2) and its size chart's (T); two more from Nitro, applied here:
PIN_LEN_CL = 0.518 * 25.4                  # 13.16: width over a connecting link (CL35, and the CL35-A1 the carriages bolt to), Nitro's CL35 page
PLATE_WAIST = 0.75 * PLATE_H               # 6.59: the plates' waist, scaled off Nitro's RC35 drawing (not published; v2-v10 drew 7.69)
# 2026-11-27 (Sterling: "Do all of your 'not done' items"; v11's README listed this waist as assumed): McMaster's own 3-D CAD for its #35
# chain, 6261K172 (and the 6261K191 connecting link), read logged out through the doser Pi and measured with cadquery
# (checks/vendor_v11.json, VENDOR-CHECK.md). Its inner (roller-link) plates are 8.81 high with a 7.49 waist; its outer (pin-link) plates
# and its connecting link's plates are lower, 7.76, the outer plates with a 6.39 waist and the connecting link's straight; each waist one
# R 13.08 arc. Nitro publishes neither the waist nor a separate outer-plate height, so v11 now draws McMaster's (Tsubaki's RS35 table
# likewise lists a lower pin-link plate). Pitch, pins, bushings and Nitro's pin lengths are unchanged.
PLATE_WAIST = 7.49                         # inner plates' waist (was 6.59)
PLATE_H_OUT = 7.76                         # outer plates' and connecting links' height (was PLATE_H, 8.79)
PLATE_WAIST_OUT = 6.39                     # outer plates' waist
PLATE_WAIST_R = 13.08                      # the waist arc's radius, both plates

# A-1 attachment connecting link (bent tab, one hole): Nitro CL35-A1, which
# matches Tsubaki's RS35 A-1 table: S = 0.250 in pitch line -> tab face,
# C = 0.375 in chain centre plane -> hole, X = 0.562 in -> tab end, N = 0.312
# in tab width, hole 0.133 in (M3; Red Boar's is 0.10 in). With the chain in a vertical plane
# the tab lies along the pins, on the outside of the loop, and its hole is
# radial: vertical at the station, square to the augers and to the travel.
A1_C = 6.35          # S: pitch line -> tab mounting face (radially outward)
A1_HOLE_D = 3.38
A1_TAB_L = 7.9       # N
A1_HOLE_C = 9.525    # C, from the chain centre plane toward the modules
A1_X = 14.3          # X, tab end from the chain centre plane

# --- 32T ANSI 35 sprockets, type B (hub one side): 35BS32-5/8, Surplus Center 601139 ---
# 32 teeth: four 90-degree wraps of exactly 8 links each, and a pitch radius
# big enough that the auger's 44T gear clears the corner shafts (see SHAFT_CLEAR).
N_TEETH = 32
PD = P / math.sin(math.pi / N_TEETH)                 # 97.13 pitch diameter
R = PD / 2                                           # 48.57
OD = P * (0.6 + 1 / math.tan(math.pi / N_TEETH))     # 102.42 outside diameter
TOOTH_W = 4.27       # 0.168" single-strand #35 tooth
SEAT_D = 1.005 * BUSH_D + 0.076                      # ANSI seating-curve diameter
HUB_D = 50.8         # 2 in hub
LTB = 22.225         # length through bore, 7/8 in
SPROCKET_BORE = 15.875  # 5/8 in finished bore, 3/16 x 3/32 in keyway, 2 set screws
KEYWAY = (4.76, 2.38)

# --- loop: four sprockets on a rectangle, 104 links ---
LOOP_M, LOOP_N = 12, 24  # links on the bottom/top runs and on each side
LOOP_B = LOOP_M * P  # 114.3 horizontal centre distance: 32T tips (102.4 OD) clear by 11.9 mm
LOOP_A = LOOP_N * P  # 228.6 vertical centre distance: room to tilt module 1 to 90 deg
assert 2 * (LOOP_M + LOOP_N) + N_TEETH == N_LINKS   # closes exactly: 24 + 48 + 32
LOOP_Y = LOOP_B / 2  # corner shafts at y = +-57.15
# Raised from 210 mm (Oct 13) so the station's Actuonix P16-150 fits under the hinge standing upright, as in the
# paternoster: rod end 72 mm under the hinge, 197.4 mm retracted + 20 mm docking stroke, 21.7 mm base clevis on a
# base rail (top at 35 mm). That needs the hinge at 351 mm or more; Z_RUN 345 puts it at 356.65.
Z_RUN = 366.5        # v11: lowered 98.5 mm so the tall-cage balance stands on the bench under the station (v10: 465). bottom run's pitch line above the bench (v4: 385; v5: 80 mm higher, so the HR-202i stands under the station)
Z_BOT = Z_RUN + R    # bottom corner shafts
Z_TOP = Z_BOT + LOOP_A                               # top corner shafts (as built, before tensioning)
CHAIN_L = 345.0      # v11: 40 mm longer carriages (v2-v10: 305), so the module and EC have room to turn to 90 deg in front of the hinge. front chain -> back chain, centre plane to centre plane

# --- modules ---
MODULE_LINKS = 8                                      # 8 pitches = 76.2 mm
N_MODULES = N_LINKS // MODULE_LINKS                   # 13

# --- the module on a carriage (Sam's Oct 8 mounting plate + the lab auger) ---
# Sam's studio frame: hinge axis = his y, auger axis = his x at z = 0, the
# plate's underside at z = -18. On a carriage his x points front -> back,
# his y along the travel and his z into the loop.
HINGE_X = 73.0       # v11: 40 mm further back (v2-v10: 33). hinge axis, from the front chain's centre plane
SAM_DROP = 18.0      # hinge axis above the plate's underside
GEAR_R = 23.0        # the auger's 44T gear (46 OD), its widest part
AUGER_Z0_XS = 0.4    # auger STEP z = 0 (outlet end) in Sam's x
AUGER_LEN = 250.0

# --- printed carriage ---
# Carriage frame: u along the travel, w radially inward (into the loop), x
# front -> back. Origin on the front chain's pitch line, mid-way between the
# A-1 link's pins. The plate sits on the two A-1 tabs, outside the chains.
CAR_W = 66.0         # along the travel: 10.2 mm between neighbours (v4: wider, the module swings through its 51.6 mm opening)
CAR_T = 5.0          # Sam's base plates are 5 mm
CAR_W0 = -A1_C                                       # plate's inner face (on the tabs)
CAR_X0, CAR_X1 = -23.0, CHAIN_L + 23.0               # tongue ends, beyond both chains
TONGUE_W = 40.0      # along the travel
TONGUE_L = 16.0      # beyond the chain's outer plates
RIB = (4.0, 7.0)     # edge ribs on the inside: width, height
HINGE_RAISE11 = 5.0  # v11: the hinge (and so the auger) 5 mm nearer the carriage plate, its mounting plate sinking into the carriage's opening,
                     # so the 44T gear meets the pinion at rest with no lift (Sam: "The auger can move a bit as well to get the hinge closer to the plate")
HINGE_W = CAR_W0 - CAR_T - SAM_DROP + HINGE_RAISE11  # v11: -24.35 (v4-v10: -29.35): hinge axis outside the carriage plate, the module outside the loop
LUG_U = 25.5         # hinge lug inner faces, 0.5 mm outside Sam's 50 mm knuckle
LUG_T = 4.0          # lugs end at u = +-29.5, inside the carriage's +-30
# On a corner two neighbours are 90 deg apart about the sprocket axis, so a
# point (u, w) on one meets the other unless |u| + w < R (48.6). The lugs are
# chamfered to |u| + w <= INNER_CORNER and the hinge screws are flush.
INNER_CORNER = 45.0
HINGE_D = 5.3        # Sam's knuckle holes (5.3 mm) and the lugs' pin holes
# Hinge pins: 5 mm clevis pins with a retaining-ring groove, head flush in a counterbore on the lug's outer
# face, an e-clip on the inner end between Sam's knuckle (|u| 15) and the auger tube (|u| 12.5). A threaded
# pin would loosen with the vibration and the roll over the top; a protruding thumb screw hits the next
# carriage on a corner (the |u| + w <= INNER_CORNER rule).
PIN_D = 5.0
PIN_HEAD = (8.0, 1.6)                                 # head diameter, height
PIN_CBORE = (8.6, 1.8)                                # counterbore in the lug for the head
PIN_GROOVE_U = 14.4                                   # e-clip groove (outer face), from the carriage centre along u: 0.6 mm inside the knuckle face
ECLIP = (8.85, 0.7)                                   # DIN 6799-4 (4 mm groove, 0.74 wide, on a 5 mm pin): McMaster 98543A112, OD 8.85, 0.7 thick
# Station reach-through: Sam's electronics carriage (his x 2.3-73.3, y +-18),
# the gear (his x 78.3-88.3) and the outlet's powder path when tilted.
WIN_X = (HINGE_X - 14.0, HINGE_X + 116.0)             # 130 mm: the docked electronics carriage sweeps the window's back edge at about 28 deg of tilt
WIN_U = 23.5                 # the U-yoke's steel arms pass at |y| 19.5-21.5 and their e-clips at 22.3
# Snap hooks that keep Sam's plate shut upside down (top of the loop): they
# overhang the plate's edge where it is 50 mm wide (his x 40-65).
SNAP_X = HINGE_X + 52.0
SNAP_LAP = 0.8       # overhang onto the plate's top edge

# --- 2020 frame, built vertically ---
EXT = 20.0
POST_Y = 180.0       # post centres (v4): the side runs' modules reach y +-161 outside the loop
SIDE_GAP = 30.0      # chain centre plane -> side plate's inner face
PLATE_T_SIDE = 6.35  # 1/4 in 6061 side plates
SIDE_W = 2 * POST_Y + EXT                             # 380 (v4)
_DZ = Z_RUN - 210.0                                   # everything above the bench moved up with the loop (Oct 18)
SIDE_Z = (180.0 + _DZ, 555.0 + _DZ)                   # front side plate bottom, top
SIDE_Z_BACK = (70.0 + _DZ, 555.0 + _DZ)               # the back plate runs down to carry the motor
FOOT_H = 15.0        # leveling foot: bench -> underside of the base rails
Z_BASE = FOOT_H      # base rails' underside
Z_TOP_RAIL = 576.0 + _DZ   # 751 (v4): top rails' underside, 21 mm over the side plates as v3; the top run's gears reach z 763
TENSION_TRAVEL = (-6.0, 8.0)  # top shafts' slot travel about nominal: down to fit the chain, up to tension it
DRIVE_TRAVEL = 4.0   # motor slides +-4 mm in its slots to tension the drive chain

# --- shafts and bearings (all four corners alike) ---
SHAFT_D = 15.875     # 5/8 in keyed shafting (the sprockets' bore)
# Surplus Center 600174. Its rear dome sits in a 49 mm hole in the plate (FYH catalogue).
# SBSFL202-10 = SBPFL202-10 2-bolt pressed-steel flangette, 5/8 in SB insert. USA Bearings & Belts' SBPFL202-10 table
# and drawing (read 2026-10-27; Surplus Center's own page is behind a bot check): a 3-3/16 (81.0), e 2-1/2 (63.5),
# B 2-5/16 (58.7), t 0.079 (2.0 mm sheet: two halves, so 4.0 at the bolt lobes), b 5/8 (15.9 dome to dome),
# S 9/32 (7.1 bolt hole), L .8661 (22.0 inner ring), n .236, k 1-1/4. The bearing's centre plane is one sheet (2.0)
# above the mounting face, the housing +-7.95 about it, and the inner ring runs from flush with the rear dome to 6.1 mm
# beyond the front one (set-screw collar outward). Was T 3.0, OUT 12.6, IN 9.6 (domes 10.6 / 8.6). cad/vendor/AUDIT_other.md
BRG = dict(L=81.0, W=58.7, J=63.5, T=4.0, OUT=16.05, IN=5.95, DOME_D=47.0, DOME_OUT=9.95, DOME_IN=5.95, RING_D=24.0,
           BOLT_D=6.35, HOLE=49.0)
SHAFT_CLEAR = R - HINGE_W - GEAR_R - SHAFT_D / 2     # 6.0: gear past a corner shaft

# --- StepperOnline 34HS59-6004D-E1000 (NEMA 34, 12 N*m, 1000-line encoder) ---
M34_FLANGE = 86.0
M34_BOLT_SQ = 69.58
M34_HOLE_D = 5.5
M34_PILOT_D = 73.0
M34_PILOT_H = 2.0      # StepperOnline STEP (paternoster/reference): 73 x 2.0 (was 1.6); its holes are 6.5 (M34_HOLE_D is our plate's slot)
M34_SHAFT_D = 14.0
M34_SHAFT_L = 37.0   # 25 mm of it keyed
M34_KEY_W = 5.0
M34_BODY_L = 150.0
M34_ENC_L = 19.0

# --- drive: NEMA 34 inside the frame on the back plate, #35 drive chain up to the B+ shaft ---
# Two 35BS15H sprockets (Surplus Center: 5/8 in keyed on the shaft, 1/2 in
# re-bored to 14 mm + 5 mm keyway on the motor): 1.99 in OD, 1-11/32 in hub,
# 3/4 in through the bore. 44 links from the roll's spare, 1:1.
N15 = 15
PD15 = P / math.sin(math.pi / N15)                   # 45.81
HUB15_D, LTB15 = 34.1, 19.05
DRIVE_LINKS = 44
C_DRIVE = (DRIVE_LINKS - N15) / 2 * P                # 138.11: closes exactly with 14-link spans (as v1's loop)
Z_MOTOR = Z_BOT - C_DRIVE                            # 120.46: motor axis, under the B+ shaft

# --- station test fixtures ---
HOLD_DOWN_GAP = 2.0          # lip above the tongue (was 0.5): the PyBullet runs showed tongues snagging on a 0.5 mm lip
HOLD_DOWN_LEAD = 3.0         # lead-in chamfers on the lip and the foot, 3 mm deep
# The foot under the tongue was 2 mm below it. The physics sim (sim/carousel_sim.py) found that a tongue's leading
# corner dips about 1.2 mm below the run line while its carriage swings off the B- sprocket, and that corner then
# hit the foot's end face and stalled the drive. 4 mm clears it with the lead-in chamfer to spare.
HOLD_DOWN_FOOT_GAP = 4.0
# Slider rails under the station carriage: two UHMW-topped bars along the travel, just under the carriage plate, so
# the plate rides on them at the station and its height no longer depends on how much the bottom run sags
# (the sim showed 2-4 mm of sag at 40 N chain tension, enough to hang a tongue on the hold-down foot).
SLIDER_GAP = 0.3                 # rail top below the plate's nominal outer face
SLIDER_X = ((152.0, 168.0), (256.0, 282.0))   # under solid plate: between the window and the first lightening hole, and behind the last one
LIGHTEN_XC = (190.0, 232.0)                  # lightening holes in the carriage plate, 34 mm long, 36 wide
SLIDER_HALF_L = 25.0             # along the travel, about the station: a carriage corner swinging off a sprocket dips below the run line beyond this
SLIDER_RAMP, SLIDER_RAMP_L = 3.0, 10.0   # lead-in at each end of a rail: drop, length
MAGNET_D, MAGNET_H = 6.35, 3.18                       # K&J D42-N52, 1/4 x 1/8 in


# --- carriage to chain: slide-on hooks with captive locknuts (through-bolted, from the outside) ---
# Each tab slides into a printed hook under it (between the tab and the chain's pitch line); an M3 nylon-insert
# locknut sits in a hex pocket in the hook, and an M3 x 12 button head goes in from the carriage's outer face
# through the plate and the tab into it. To take a carriage off: two screws out, slide it 10 mm along the run so
# the hooks clear the tabs, lift it out. Nothing has to be reached from inside the loop.
TAB_SCREW_L = 12.0
TAB_SCREW_CB = 1.8                                    # counterbore for its head in the plate's outer face: the head sits flush
SCREW_OUT = 10.0                                      # backed out this far to swap, the tips clear the tabs and stay in the plate
HOOK_SLIDE = 10.0                                     # slide along u to engage / free the hooks
NUT_AF, NUT_H = 5.5, 4.0                              # M3 nylon-insert locknut (DIN 985)

# --- chain tension and speeds (sim and test plan) ---
CHAIN_TENSION_N = 80.0       # per chain: 3-4 mm under a 5 N side push on a 228.6 mm side

# --- frame pitch (evaluated and rejected, kept as a parameter) ---
# Pitching the whole frame outlet-end up would keep every outlet up all the way round (each module rolls about an
# axis parallel to its auger). The auger-leakage study (../auger-leakage/) found no measurable difference at 0, 5,
# 10 and 15 deg: the only afterflow leaves while the module is still above 10 deg on the way back from the dose,
# where no rest pitch can catch it. A pitch also makes the dose stream drift back into the docked electronics
# carriage's footprint (layout.stream_check): the fixed D-funnel catches it only up to about 2.4 deg. So 0.
FRAME_PITCH_DEG = 0.0
# Run direction. Each lap turns every module once about its own axis, which acts like one auger turn. With the
# bottom run travelling toward +y (counter-clockwise seen from the back) that turn is a forward one and a primed
# auger pumped about one revolution's dose out during a lap (proxy sim); the other way it retracts powder from the
# exit. So v2 runs with the bottom run travelling toward -y. kinematics.py keeps +shift = toward +y; the
# machine's normal travel is RUN_DIRECTION * shift.
RUN_DIRECTION = -1           # -1: bottom run toward -y (clockwise seen from the back)

# --- station: Actuonix P16-150-22-12-P, pinned at both ends (as the paternoster) ---
ACT_STROKE = 150.0
ACT_RETRACTED = 197.4        # hole to hole, retracted (Actuonix STEP): stroke + 47.4
CLEVIS_GAP = 8.4             # between the base clevis cheeks: the P16's rear tab is 8 thick (datasheet)
SHOULDER_CLEVIS_L = 16.0     # McMaster 4 x 16 mm shoulder screw (M3 thread) through cheek, tab, cheek
ACT_CLEVIS_D = 4.25          # both clevis holes
# Carriage pin at the carriage's centre-of-mass height. The P16 is pinned at both ends, so it gives the carriage no
# moment: the dock (rim + locating pins + magnet face) has to hold the carriage's attitude. With the pin under the
# carriage (the paternoster's (40, -72)) the carriage is an inverted pendulum on it, COM 39 mm above, and the dock opens
# at a few newtons of gear load once tilted (station sim + the main session's tooth-contact model). At COM height the
# carriage hangs balanced: two 4 mm steel stub pins pressed through the carriage's solid side post (x 29-35) and a
# printed boss, a U-yoke on the rod end with 2 mm steel arms up both sides (outside the carriage's |y| 18), so the
# carriage can turn freely in it. Station sim, dock-opening separating force at 30 deg: 13.3 N here, 10.2 N at
# (45, -34), 6.1 N for the old pin, 0.4 N with the pin on the mesh line (83.4, -52).
YOKE_X, YOKE_Z = 32.0, -34.0 # carriage stub-pin axis, Sam's frame (carriage as drawn)
UFORK_L = 60.0               # stub-pin axis -> the P16's rod-end hole, along the actuator: the crossbar clears the carriage's
                             # front-bottom corner (51 mm from the pins) as the carriage turns 92 deg in the yoke
UFORK_Y = (19.5, 21.5)       # steel arm, |y| (2 mm); printed boss on the post |y| 18-19.5; e-clip outside at 21.7-22.3
TONGUE_X, TONGUE_Y = YOKE_X, 15.0   # guide tongue under the yoke's crossbar, rides the approach fork
YOKE_STOP_Z = -11.0 - 0.3 - 4.0     # stop blocks on the arms (yoke frame z of the block's bottom): 0.3 mm under the pin plate's
                                    # tail. Was a block under the carriage's back bottom (|y| 15.5-19.5), which the carriage's
                                    # front-bottom corner swept into past 70 deg of tilt (check_interference --tilt); now, as the
                                    # paternoster, the stop and the tail sit at |y| 18.2-19.5, outside the carriage's |y| 18
DOCK_EXT = 20.0              # actuator extension when the carriage meets the plate; 90 deg needs 282.5 of the P16's 347.4 mm
# Locating pins on the carriage rim (steel dowels, conical tips) into a hole and a slot in the plate's underside: they
# carry the along-plate load at tilt instead of friction; the slot runs along x to take the 40 mm pin spacing's tolerance.
LOCPIN_D, LOCPIN_PROUD = 4.0, 3.0    # dowel diameter; protrudes 3 mm above the rim (2.1 mm into the plate when docked)
LOCPIN_XY = ((30.0, 16.0), (70.0, -16.0))   # Sam's frame; the first goes in a 4.2 mm hole, the second in a 4.2 x 6 slot
LOCPIN_HOLE, LOCPIN_SLOT = 4.2, 6.0
SEP_RATIO_STEEL = 0.55       # separating / tangential force at the mesh with the steel pinion and dry PTFE lube
DOCK_RISE = 0.9              # Sam's Part Studio leaves the carriage 0.9 mm under the plate; docked, they touch
CLEVIS_H = 21.7              # base clevis pin above its foot
FORK_H = 36.0
TILT_DOSE_WORLD = 30.0       # default dose tilt, degrees from horizontal in the world (frame tilt = this + pitch)
TILT_MAX_FRAME = 90.0        # hinge travel limit (the P16-150 reaches 90 deg with 65 mm of stroke to spare)
NEMA11_X, NEMA11_Z = 68.3, -33.15  # NEMA 11 mounting face on the inside of Sam's carriage's back wall (x 68.3-73.3), boss in his
                                   # pilot recess, M2.5 screws from outside; its 20 mm shaft ends at x 88.3, the pinion's back face.
                                   # Pinion axis 32.25 mm under the auger axis when docked (Sam's pilot is at -33.0: the motor sits
                                   # 0.15 mm low in the 22.1 mm recess); 32.25 mm leaves 0.12 mm of backlash after the plate bends
                                   # under the magnet (gear-mesh study: 32.1 mm jammed with printed-gear runout)
PINION_X0 = NEMA11_X + 10.0        # pinion's motor-side face: 78.3-88.3, on the shaft's last 10 mm
SOL_X, SOL_Z = 12.0, -24.0   # solenoid under the auger tube near the outlet, plunger up
GEAR_X = 78.4                # the auger's 44T gear face nearest the outlet, in Sam's x (gear 10 mm wide)

# Dock electromagnet behind the pinion + steel armature tab under each plate's back strip (the gear-mesh
# preload: the module's weight alone can't hold the 20T:44T mesh against the NEMA 11, see cad/gear-mesh/).
# Adafruit 3872 P20/15: 20 x 15 mm, 5 V, 0.22 A, about 24.5 N holding at zero gap. Sam's frame, carriage as
# drawn (top face z -18.9; docked it rises DOCK_RISE so the rim touches the plate and sets the 32.25 mm centre
# distance). The face sits 0.15 mm under the armature when docked, so the rim, not the magnet, locates.
DOCK_MAG_D, DOCK_MAG_H = 20.0, 15.0
DOCK_MAG_XY = (99.5, 0.0)
DOCK_MAG_FACE_Z = -18.0 - 2.0 - 0.15 - DOCK_RISE  # -21.05 as drawn
ARMATURE_X = (89.0, 111.0)   # low-carbon steel tab, 2 mm, |y| <= 14, top face on the plate's underside (z -18)
ARMATURE_HW, ARMATURE_T = 14.0, 2.0
ARMATURE_SCREWS = ((94.0, -10.0), (94.0, 10.0))   # M3 x 6 flat heads into M3 inserts in the plate's back strip

# vial on a 100 g load cell (gravity-referenced: plumb in the world)
VIAL_H = 61.0
VIAL_D = 28.0
LC_L = 47.0                  # TAL221 (SparkFun SEN-14727) is 47 x 12 x 6 (datasheet); was 80, the TAL220's length
CUP_ARM = 63.0               # vial cup's arm (printed): 33 mm longer than with the 80 mm stand-in, so the real 47 mm cell's fixed end stays on the level wedge
VIAL_DROP = 30.0             # outlet to funnel mouth, world vertical
FUNNEL = dict(top_d=36.0, spout_d=18.0, h=22.0)


# =====================================================================================================================
# v3 (Sam's critiques of 2026-10-29). Sam's frame, docked at the station unless a comment says otherwise: x along the
# auger from the hinge axis (outlet end at x = 0.4), y along the hinge axis (the travel at the station), z away from
# the plate (auger axis z = 0, plate underside z = -18).
# =====================================================================================================================

# --- 1. kinematic dock between the electronics carriage (EC) and the mounting plate (a Kelvin clamp) ---------------
# Sam's Aug 27 carriage (his fit-together video) located the plate with four cone-tipped posts in four holes, which is
# one more constraint than a rigid pair needs. v3 uses exactly six contacts: two 1/4 in chrome-steel balls pressed into
# the plate's underside sit in a cone (A, +y) and a vee (B, -y, its groove along y, toward A) on the EC, and a third
# ball on the EC presses on the plate's steel armature (the flat, C). Preload: a small N52 magnet under the cone and
# under the vee (each pulls its ball in) and v2's switchable dock electromagnet, now just in front of the flat.
KC_BALL_D = 6.35                     # McMaster 9642K23-class 52100 chrome steel ball, 1/4 in (grade 25)
KC_A = (30.0, 18.5)                  # plate ball over the EC's cone seat (x, y): the cone stays 1 mm off the NEMA 11 (|y| 14)
KC_B = (30.0, -18.5)                 # plate ball over the EC's vee (8 mm dowels: y -22.5..-14.5)
KC_C = (114.5, 0.0)                  # EC ball under the plate's armature (the flat), 0.8 mm behind the electromagnet
KC_BALL_Z = -18.6                    # plate balls' centres: 3.8 mm proud of the underside (pressed 2.6 mm into the plate)
KC_SEAT_TOP = -19.6                  # top of the EC's seat ears when docked: 1.6 mm under the plate
KC_CONE_HALF = 45.0                  # cone seat half-angle (printed, line contact: about 11 MPa at 5 N)
VEE_DOWEL_D, VEE_DOWEL_L = 3.175, 12.7   # 1/8 x 1/2 in hardened dowels, two per vee (steel on steel: point contacts)
VEE_SPACING = 2 * (KC_BALL_D / 2 + VEE_DOWEL_D / 2) * math.sin(math.radians(45.0))   # 6.73: 90 deg vee
KC_MAG_D, KC_MAG_H = 6.35, 6.35      # K&J D44-N52 (1/4 x 1/4 in) under the cone and under the vee
KC_MAG_GAP = 0.6                     # magnet face below the seated ball's lowest point
DOCK_RISE_V3 = 0.9                   # EC as drawn -> docked: the pinion's centre distance stays 32.25 mm (v2)
EC_RIM_CUT = 1.8                     # Sam's carriage top rim cut down 1.8 mm (to 0.2 under the seat ears): only the three contacts touch the plate
ARMATURE_X3 = (89.5, 121.0)          # steel armature (2 mm, |y| <= ARMATURE_HW3): from behind the 44T gear's slot out past the plate
ARMATURE_HW3 = 11.0
ARMATURE_SCREWS3 = ((92.0, -7.0), (92.0, 7.0))   # M3 flat heads into heat-set inserts in the plate's back strip
DOCK_MAG_XY3 = (100.0, 0.0)          # Adafruit 3872 face 0.15 mm under the armature (as v2), 12 mm ahead of the flat

# --- 2. the guide: the EC parks on its own kinematic seat below the passing carriages and rises square ------------------
# A printed cradle on a 2020 post: a floor with a second Kelvin clamp for three balls under the EC (cone, vee, flat), side
# walls 0.3 mm off the EC's narrow lower body (|y| 15) and a front wall 0.3 mm ahead of its front face. No back wall above
# the floor: the tilt carries the EC backward and up out of the cradle, parallel to the side walls. The P16 pushes the EC
# through a pin in a slotted clevis under its back half, so the EC's centre of mass is ahead of the pin and it leans on the
# front wall while it rises; the slot (lost motion) lets the actuator stop anywhere near the dock or the seat without
# forcing either: the magnets hold the dock, the EC's weight holds the seat.
EC_BASE_T = 3.0                      # printed base under Sam's carriage (as drawn its bottom is at z -60.8)
EC_BASE_Z = -60.8                    # base's top face, as drawn
EC_BALLS = ((69.0, 11.5), (69.0, -11.5), (40.0, 0.0))   # cone, vee (along y), flat, under the base: the EC's centre of mass
                                                     # (x 52) is inside their triangle and clear of the clevis
EC_PIN = (58.0, -76.0)               # clevis pin (x, z), as drawn: 6 mm behind the EC's centre of mass, so it leans forward;
                                     # 12 mm under the base, so at 90 deg the P16's rod passes under the flat ball
EC_CHEEK_Y = (4.8, 9.8)              # clevis cheeks: 9.6 mm apart, the rod (8.94) swings between them at any tilt; two 0.8 mm
                                     # PTFE washers each side take up the gap round the rod end's 6 mm tab
EC_SLOT = 2.0                        # lost motion in the clevis slots
GUIDE_CLEAR = 0.3                    # side and front walls off the EC's lower body
GUIDE_WALL_T = 2.5
PARK_DROP = 20.0                     # parked EC sits this far below its docked position (v2's DOCK_EXT)

# --- 4. the outlet door: a spring-loaded shutter on every auger, pushed open by the docked EC --------------------------
# A printed housing between Sam's knuckle arms holds a 1.5 mm shutter 0.3 mm in front of the auger's end face. A
# stainless compression spring pushes it down over the 3 mm exit. Its push rod runs down beside the exit (y = DOOR_ROD_Y,
# out of the dose stream) to below the plate; a finger on the EC's front lifts it DOOR_TRAVEL in the last 10 mm of the
# dock, so the exit is uncovered only while the EC holds the module, and the door closes before the EC lets go.
DOOR_GAP = 0.3                       # shutter's back face to the auger's end face
DOOR_T = 1.5                         # shutter thickness
DOOR_W = 10.0                        # shutter width (y)
DOOR_CLOSED_Z = (-3.5, 4.0)          # shutter's bottom and top edges, closed (covers the exit, z -1.5..1.5, by 2-2.5 mm)
DOOR_TRAVEL = 6.0                    # open: bottom edge at +2.5, 1 mm above the exit
DOOR_ROD_Y = 7.5                     # push strip beside the exit (y 6-9)
DOOR_ROD_D = 3.0                     # push strip width (it is the shutter's own +y strip, 1.5 thick)
DOOR_ROD_BOTTOM = -22.0              # rod's lower end, closed (inside the carriage window, above its outer face)
DOOR_SPRING = (3.0, 16.0, 0.06)      # OD, free length, rate N/mm (stainless): 11.5 mm fitted shut (0.27 N), 5.5 open (0.63 N)
DOOR_TOP = 19.5                      # housing's top (z): |u| 13 + w 31.2 = 44.2, inside the 45 mm corner rule
DOOR_SPRING_SEAT = DOOR_TOP - 3.0    # the cap's underside, where the spring's fixed end sits
DOOR_SPRING_SHUT = DOOR_SPRING_SEAT - (DOOR_CLOSED_Z[1] + 1.0)   # 11.5: seat to the shutter's boss, door shut

# --- 4a. the plate latch: holds the plate on its carriage upside down; a cam at the station opens it ------------------------
# A printed bolt slides along x in a housing on the carriage's inner face behind the plate, at y = LATCH_Y (beside the auger
# tube). A spring pushes it forward over a keeper on the plate's back end. Its follower pin runs down through a slot in the
# carriage plate; at the station a fixed rail along the travel pushes the follower back LATCH_TRAVEL, so every carriage's
# latch is open while it sits at the station (module right side up, resting on the carriage) and closes as it leaves.
LATCH_Y = 19.0                       # v4: his y is the world's -y at the station, so +19 puts the follower and the station's rail on
                                     # the world's -y side, within +-28 mm of the station where no carriage tips round a corner
LATCH_W = 8.0                        # bolt width (y)
LATCH_KEEPER_X = (98.0, 103.0)       # keeper block on the plate's back end, |y| 14-24, top face z -13
LATCH_LAP = 3.0                      # bolt over the keeper when closed
LATCH_TRAVEL = 4.5                   # bolt stroke: open leaves 1.5 mm between the bolt and the keeper's back edge
LATCH_RAIL_FLAT = 4.0                # rail flat, +- about the station follower (the index repeats to +-0.5 mm)
LATCH_FOLLOW_X = 120.0               # follower pin (closed), x
LATCH_FOLLOW_PROUD = 4.0             # follower tip below the carriage's outer face
LATCH_SPRING = (4.0, 12.7, 0.25)     # OD, free length, rate N/mm: 0.9 N closed, 2.0 N open

# --- 5. enclosure: clear acrylic on the 2020 frame, a front hatch for the scale, a side hatch for swaps -------------------
ACRYLIC_T = 3.0                      # 1/8 in cast acrylic (actual 0.118 in)
PANEL_STANDOFF = 6.0                 # panels on spacers outside the frame: the side runs' carriages reach y +-117, the side tabs +-124
WIN_BACK_V3 = 125.0                  # v3 carriage window's back edge (Sam's x): EC v3's flat ball and boss reach x 119
PAD_X0_V3 = 90.5                     # pads under the plate's back corners start here (EC v3's bracket arms end at x 90)
PAD_U0_V3 = 15.5                     # pads at |u| 15.5-23.5: the EC's base and its seat balls sweep |y| <= 14.7 through the
                                     # carriage's plane at 30-35 deg of tilt
SIDE_TAB_FOOT_GAP = 4.0              # side tab foot outside the tongue (v4 makes it 1 mm: the auger pull goes through it)
HATCH_FRONT = (300.0, 330.0)         # v5: front hatch (y width, z height), centred on the station, from the bench up: the
                                     # HR-202i's display pokes out under the door, and a hand reaches its side doors (v4: 180 x 230)
HATCH_SIDE = (400.0, 230.0)          # side hatch on +y (x width, z height), centred on the loading position. v11 (2026-11-27): 400 mm
                                     # (v3-v10: 330), so a whole carriage (391 mm over its tongues, x -23..368) lifts out through it 4.5 mm
                                     # clear each side (check_interference.py --swap); the opening (x -27.5..372.5) stays 8.85 mm inside
                                     # the posts' faces and 13.85 mm from the standoffs; the door is 408 x 238
HATCH_OPEN_DEG = 110.0

# --- 6. the scale: A&D HR-100A (the lab's balance: 102 g x 0.1 mg), from A&D's manual (HR-A/HR-AZ manual section 22) ------
HR_W, HR_D, HR_H = 198.0, 253.0, 315.0       # base 198 wide, 61.5 + 191.5 deep; 315 tall over the breeze break
HR_PAN_D, HR_PAN_Z = 90.0, 86.5              # weighing pan, height of the pan
HR_CHAMBER_D_IN, HR_CHAMBER_H_IN = 156.0, 198.0   # round glass breeze break: inside diameter, inside height above the pan
HR_PAN_FROM_FRONT = 162.0                    # pan centre behind the front (display) edge, measured off the drawing
BEAKER_D, BEAKER_H = 38.0, 49.0              # 25 mL low-form beaker (DWK/Kimble 14000-25 class)


# =====================================================================================================================
# v4 (Sam's item 7): the augers outside the loop. Sam's frame on a carriage: his x along the auger, his z AWAY from the
# carriage (outward), his y = -u. The plate's underside (z -18) sits on the carriage's outer face.
# =====================================================================================================================
OPEN_U = 25.8                        # the carriage's opening: the module (plate +-25, gear +-23) swings up through it into the loop
OPEN_X = (HINGE_X - 14.0, HINGE_X + 255.0)   # carriage x 19-288: from in front of the hinge to past the cap (Sam x 252.4)
OPEN_U_BACK = 27.6                   # wider over Sam's x 52-104, where his plate is +-27.02 (its back strip)
OPEN_BACK_X = (52.0, 104.0)          # Sam's x (carriage x = HINGE_X + these), ahead of the latch housing
LUG_U4 = 26.0                        # hinge lugs on the outer face, |u| 26-30, round the plate's knuckles (|u| 15-25)
TILT_MAX_V4 = 50.0                   # the module swings into the loop; at about 55 deg its cap reaches the top run
# kinematic dock on the plate's auger side (the EC docks from outside, round the auger): the side strips between the clamps
KC4_A = (44.0, 19.5)                 # cone (plate ball)
KC4_B = (44.0, -19.5)                # vee along y (plate ball)
KC4_C = (64.0, 19.5)                 # flat: a steel washer on the plate's top face, the EC's ball C on it
KC4_BALL_Z = -13.0 + KC_BALL_D / 2 - 2.6     # -12.425: plate balls pressed 2.6 mm into the top face, 3.8 proud toward +z
KC4_SEAT_TOP = KC4_BALL_Z + 1.0              # -11.425: the seats' faces, 1.6 mm off the plate's top face
KC4_PAD = (10.0, 1.0)                # M5 steel washer (OD, thickness) bonded in a pocket in the plate's top face at KC4_C
DOCK_RISE_V4 = -0.9                  # EC v4 (Sam's carriage mirrored through the auger axis) moves 0.9 toward the plate to dock:
                                     # the pinion sits 32.25 mm from the auger axis on the auger's far side
EC4_ARM = (15.5, 23.5)               # the arms' |y| (between the clamps' 14.55 and the plate's 25)
EC4_ARM_X = ((38.5, 68.3), (38.5, 49.5))     # +y arm (cone and C), -y arm (vee)
# plate latch (v4): a pin in a hole, so it holds the plate both ways (the opening leaves nothing under the plate)
LATCH4_KEEPER_X = (98.0, 106.0)      # keeper block on the plate's back end, |y| 14-24, z -18..-9, a 4.2 mm hole along x at z -13.5
LATCH4_PIN = (4.0, -13.5)            # bolt pin diameter, its axis z
LATCH4_ENGAGE = 4.0                  # pin in the hole when closed
LATCH4_FOLLOW_TIP = 24.0             # the follower runs from the bolt beside the tube out to z +24 (beside the cap's +14.5)
# cap rest at the station: with the latch open the module rests 0.5 mm down on it, on its cap, until the EC docks
CAP_REST_X = (229.0, 247.0)          # Sam's x, under the cap (Sam x 224.7-252.4, radius 14.5)
CAP_REST_GAP = 0.5
SIDE_TAB_FOOT_GAP_V4 = 1.0           # v4's side tabs: the foot 1 mm outside the tongue, so pulling an auger off barely moves the carriage
SIDE_TAB_FOOT_GAP = SIDE_TAB_FOOT_GAP_V4
LUG_U = LUG_U4                       # parts.clevis_pin sizes the hinge pins' grip from LUG_U
TUBE_REST_X = (106.0, 116.0)         # the station's rest under the auger tube (Sam's x, behind the keeper), face 0.5 mm off the tube

# Park depth (2026-10-30, check_interference --sweep): at v3's 20 mm the parked EC v4's arms still straddle the auger, and
# the augers passing the station hit them 2 links either side of it (up to 242 mm3). 8 mm deeper cleared every pose tried
# (checks/sweep.json, park_drop_test). The P16's base pin drops with it (the base clevis rises 20.2 mm above its rail).
PARK_DROP = 28.0


# =====================================================================================================================
# v5: the balance under the station. A&D HR-202i (HR-i series), from A&D's HR-i instruction manual, 15.1 "External
# Dimensions" (as read for byu-vcl's lab_models; checked again here, see README "The balance"). Display toward the
# front (-x), the weighing chamber under the dose point, the mechanism tower behind it (+x).
# =====================================================================================================================
HR2_W, HR2_W_DOORS = 200.0, 217.0            # body width; over the side doors' grips
HR2_D, HR2_D_ALL = 428.0, 442.0              # body depth; overall
HR2_H, HR2_H_ALL = 310.0, 316.0              # body height; over the top door's grip
HR2_PAN_D, HR2_PAN_Y, HR2_PAN_TOP = 90.0, 163.0, 50.0   # pan dia., its centre behind the front, its top above the bench (all printed on p.60)
HR2_CH = (183.0, 164.5, 250.0)               # chamber inside: width, depth, height above the pan
HR2_CH_Y = HR2_PAN_Y - 86.5                  # chamber's front glass behind the front (the pan is 86.5 mm behind it)
HR2_DOOR = (148.5, 251.0)                    # side doors (depth, height); both slide back
HR2_TOP_DOOR = (164.0, 148.5)                # top door (width, depth); slides back over the tower
HR2_FEET_X = 166.0                           # rear feet apart
HR2_GLASS, HR2_FRAME = 4.0, 7.0
HR2_NOSE = (24.0, 46.0)                      # display section's top: 28 at the nose, 50 at the glass (A&D's DXF; + 4 in the builder)
HR2_FLOOR = 40.0                             # chamber floor and the side doors' sills (A&D's DXF)
HR2_CAP_G, HR2_READ_MG = 220.0, 0.1
HR2_FINE = (51.0, 0.01)                      # fine range: g, mg
HR2_TOP_GAP = 10.0                           # the parked EC, the lift bar and the NEMA 34 stay this far over the balance's top
HR2_REAR = (276.0, 244.0, 221.0)             # rear housing: starts this far behind the front; its top at its front, at the back (A&D's DXF)
HR2_DOOR_TRAVEL = 205.0                      # the top and side doors slide straight back about this far (A&D's DXF, open outlines)
HR2_KG = 7.9

# the beaker on a printed riser, so the dose falls about 150 mm instead of 340 (the beaker's rim stays under the side doors'
# opening, so it comes out through a side door; the top door is under the station)
BRISER_FOOT_D, BRISER_TUBE_D, BRISER_WALL = 80.0, 44.0, 1.6
BEAKER_RIM_Z = 282.0                         # beaker rim above the bench: 9 mm under the side doors' opening's top (291, A&D's DXF), so
                                             # it clears it lifted 6 mm out of the riser's cup
BEAKER_RISER_H = BEAKER_RIM_Z - BEAKER_H - HR2_PAN_TOP + 5.0   # 194: the beaker sits 5 mm down in the riser's cup

# lift bar and the two P16s (v5's station column, moved out of the balance's chamber)
LIFT_BAR_D = 8.0                             # 8 mm precision steel shaft (h6), through the EC's base on v4's clevis-pin axis
P16_Y = 146.0                                # the P16s' axes, +-y (the balance's side doors reach +-108.5 about its centre)
LIFT_BAR_L = 2 * 132.0                       # bar ends in the end blocks' clamps, |y| 120-132
SHOE = (14.0, 10.0, 20.0)                    # guide shoe on each bar end: x, y, z (in its guide's 14.2 mm slot)
GUIDE_SLOT_W = 14.2
STATION_POST_Y = POST_Y                      # station posts on the side base rails, at the P16s' x
LATCH_BEAM_Z = 0.0                           # set in layout: the latch rail's pad sits on the beam where v4's post ended
TILT_MAX_V5 = 40.0                           # v5: the lift bar passes under the neighbouring modules; past about 41 deg it rises into
                                             # them (check_interference --tilt: 42 deg touches module 13's plate). v4: 50


# =====================================================================================================================
# v6 (Sam, PR #185, 2026-11-10): the module, the frame and the station reworked. Sam's frame (x along the auger from the
# hinge axis, y along the hinge axis, z away from the plate on the auger's side) unless a comment says "world".
# =====================================================================================================================
# --- 1. mounting plate v6: Sam's front (knuckles, clip 1, gear housing) kept, the plate extended to the cap ---------------
PLATE6_X1 = 252.0                    # the plate's back end: the cap's end (Sam x 252.0). It has to swing through the carriage's
                                     # opening, which ends at x 255 (the back A-1 tab's hook is behind it)
PLATE6_HW = 25.0                     # the extension's half width (Sam's plate is +-25, +-27.02 over its gear housing)
CLIP2_X = (150.0, 162.0)             # clip 2, centred 156: halfway between the gear's back face (88.4) and the cap (224.4)
CLIP_R_IN, CLIP_R_OUT, CLIP_TOP = 12.65, 16.5, 8.0   # C-clip round the 25 mm tube: its arms end 8 mm past the axis, so the
                                     # mouth is 2 * sqrt(12.65^2 - 8^2) = 19.6 mm and the tube snaps in and pulls out along +z
CAP_CRADLE_X = (228.0, 244.0)        # a saddle under the cap (R 14.5 + 0.2)
# the dock's plate half, printed: domes of the 1/4 in balls' exposed shape at A and B (the EC's cone and vee are unchanged),
# the plate's own face at C (no washer). A K&J D42-N52 (1/4 x 1/8 in) magnet pressed into the plate's underside under each,
# 1.8 mm of plastic between it and the face, is what the EC's three magnets pull on (there is no steel left in the plate).
KC6_MAG = (6.35, 3.18)
# --- 2. the latch at the plate's back end: a pin and a rest shelf on one spring bolt --------------------------------------
LATCH_Y6 = 21.0                      # beside the cap (R 14.5): the keeper is at y 16-26
KEEPER6_X = (244.0, PLATE6_X1)       # keeper block on the plate's back end, y 16-26, z -18..-8; a 4.2 mm hole along x at z -13.5
LATCH6_PIN = (4.0, 10.0, -13.5)      # dowel diameter, length, axis z
LATCH6_ENGAGE = 4.0                  # pin in the keeper's hole, closed
SHELF6 = (8.0, 2.0)                  # the bolt's rest shelf over the keeper's top face (z -8): its reach over the keeper closed, thickness
LATCH6_HOUSING_X = (255.5, 279.0)    # on the carriage's outer face, behind the opening (x 255) and short of the plate's end (x 280)
LATCH6_FOLLOW_X = 263.0              # follower dowel (3 mm), closed
LATCH6_MANUAL = 10.0                 # pushed back by hand this far to take a module off: pin and shelf both clear
LATCH6_FOLLOW_TIP = 10.0             # the follower's tip (Sam z). At v5's +24 the tips of carriages passing over the NEMA 34 (inside the
                                     # frame under the bottom run's +y half, its top at z 418.5) ran into it now that the latch is at the back
LATCH6_CAM_Z = (2.0, 8.0)            # the station's cam, Sam z: on the followers' exposed 11.5 mm, clear of the housings (z -1.5)
# --- 3. carriage v6: the opening 5 mm longer at the front, so the plate's edge clears it at 90 deg -----------------------
OPEN_X6 = (HINGE_X - 19.0, HINGE_X + 255.0)
OPEN_U_KEEPER = 27.6                 # wider over the keeper (Sam x 240-255), which swings through it
# --- 4. frame: rungs between the front and back posts on each side (a ladder) instead of posts on the base rails ------------
RUNG_LOW_ZC = 195.0                  # world: lower rungs' centre (the lift P16s' shelves); set from the P16-50's base pin
RUNG_UP_ZC = 308.0                   # world: upper rungs' centre (the guides); under the back plate's bottom edge (325)
# --- 5. station: the lift (two P16-50) only docks; a third P16 tilts --------------------------------------------------------
P16L_STROKE, P16L_RETRACTED = 50.0, 97.4      # Actuonix P16-50-22-12-P: retracted hole to hole = stroke + 47.4, as the -150
LIFT6_BARS_X = (10.0, 60.0)          # the two lift bars' x (Sam), both at the EC's as-drawn z 76 (v5's bar height)
LIFT6_BAR_Z = 76.0
LIFT6_P16_X = 35.0                   # the lift P16s' axes (Sam x), between the bars
HOOK6_W = 8.3                        # the EC's hooks: slot width round the 8 mm bars
TILT6_R, TILT6_PHI0 = 60.0, -135.0   # world: the tilt pin's radius from the hinge axis and its angle (deg, from +x toward +z) untilted
TILT6_Y = -30.0                      # world: the tilt P16's axis (Sam y = STATION_Y - this = 34.76): outside the EC and the stream
TILT6_B = (318.0, 372.0)             # world (x, z): the tilt P16's base pin, on a bracket on the back side plate
TILT6_ARM_Y = (23.5, 29.5)           # Sam y of the EC's tilt arm (the rod end's 6 mm tab rides 2.3 mm beside it on a PTFE washer, single shear;
                                     # at 25-31 the P16's 8.94 mm rod brushed the arm, home check)
TILT6_SLOT = 2.0                     # lost motion along the actuator at the tilt pin
TILT_MAX_V6 = 90.0
# --- 6. the guides' funnel-type kinematic seats --------------------------------------------------------------------------
SHOE6_NOSE = (10.0, 4.5)             # the shoe's conical nose: base diameter, height (90 deg cone, its tip rounded off)
GUIDE6_FUNNEL = 4.0                  # the slots' mouths flare 45 deg, 4 mm each side
GUIDE6_RELIEF = 0.5                  # the slot opens 0.5 mm each side over its bottom 8 mm, so the seats locate the shoe


# =====================================================================================================================
# v7 (Sam, PR #185, 2026-11-10, second note): v6's ladder and long plate kept; v6's lift frame (two P16-50s, two bars,
# hooks) and its back-mounted tilt P16 gone; ONE P16-150 under the station again, as v2-v4, now standing behind the
# balance's draft cage (the balance re-modelled as a base and a draft cage, no tall rear module); the dock moved to the
# scale side of the auger on posts printed on the plate, so the EC is Sam's compact carriage with no arms. Sam's frame
# unless a comment says "world".
# =====================================================================================================================
# --- the dock on posts: the plate reaches past the auger to the EC (domes at A and B, a flat at C) -------------------------
KC7_A = (46.5, 19.5)                 # post A: dome into the EC's cone. x 42.5-50.5 clears clip 1 (x 26-42)
KC7_B = (46.5, -19.5)                # post B: dome into the EC's vee
KC7_C = (64.0, 19.5)                 # post C: its flat tip under the EC's ball C. x 60-68 clears the gear housing (x 66+, |y| > 22)
KC7_POST = (8.0, 8.0)                # post section (x, y): |y| 15.5-23.5, 3 mm off the 25 mm tube
KC7_SEAT = 18.0                      # docked: the EC's seat faces, at its rim (Sam's carriage turned over, as drawn 18.9, docked 18.0)
KC7_TIP = KC7_SEAT - 1.575           # 16.425: the posts' tip faces (v4's ball-in-cone geometry moved 29.4 mm out, past the auger)
KC7_BALL_Z = KC7_TIP + 0.575         # 17.0: the domes' sphere centres (r 3.175, 3.75 proud of the tip)
KC7_MAG_DEPTH = 1.8                  # plastic between the post's magnet (D42-N52, in a print-pause pocket) and its tip face
# --- the EC (Sam's Oct 13 carriage turned over, as v4) with three ears at its rim and a tail for the P16 and the guides --------
PARK_DROP7 = 10.0                    # parked this far under the dock. Enough because nothing reaches round the auger any more: the
                                     # pinion clears the passing gears by 8.2, the ears the domes by 7.8, the finger the door strip by 4
EC7_TAIL_X = (73.3, 109.0)           # tail behind the EC's back wall (as drawn): under the 44T gear, past the pinion (z >= 46)
EC7_TAIL_Z = (46.0, 52.0)            # as drawn: the web (the pinion's outer edge is at 44.2)
EC7_PIN = (78.0, 54.9)               # the P16's rod-end pin (as drawn x, z; docked Sam z 54.0), along y
EC7_SHOE_X = (95.0, 109.0)           # the two guide shoes on the tail (as drawn), |y| 13.5-23.5, z 40-60, conical noses (v6's) at +z
EC7_SHOE_Y = (13.5, 23.5)
EC7_SHOE_Z = (40.0, 60.0)
# --- the P16-150: pinned to the EC's tail and to a clevis on a cross bar behind the balance -------------------------------
P16_7_BX = 250.0                     # world x of the P16's base pin. Its z is set (layout) so it is retracted + 1 mm with the EC parked:
                                     # the P16 leans 44.5 deg, back from the EC over the draft cage's back-top corner (2-D study:
                                     # 90 deg needs 130 of its 150 mm, the moment arm about the hinge is 21 mm docked, 95 at 64 deg)
CROSS7_GUIDE_X = 136.4               # world: the guide cross bar's centre (along y between the upper rungs), 4 mm behind the cage
RUNG7_UP_ZC = 310.0                  # world: upper rungs and the guide bar (their tops 320, under the back plate's 325)
GUIDE7_FUNNEL = 4.0                  # v6's funnel mouths, 45 deg, 4 mm each side (Sam: "apply them wherever we move the guides")
GUIDE7_RELIEF = 0.5
# --- the balance (Sam: "None of the scales we've seen or used have the large module at the back") ---------------------
# A base and a draft cage, nothing behind the cage over the base's height. The cage keeps v5's HR-202i chamber (183 x 164.5
# x 250 over the pan, pan 86.5 behind the front glass), so the pan, the beaker and the dose height are v5's; the depth over
# the base is 263 mm (the HR-100A's is 253). The top door is replaced by a dosing lid with a hole under the dose point (the single
# doser's AutoTrickler-lid idea): the exit is on the hinge axis, so the stream falls through the same hole at every tilt.
BAL7_FRAME, BAL7_GLASS = 7.0, 4.0
BAL7_BACK_X = 78.0 + BAL7_GLASS + BAL7_FRAME + 3.0      # the base's back, from the pan centre (92)
BAL7_TOP = HR2_PAN_TOP + 250.0 + BAL7_GLASS + BAL7_FRAME   # 311: the cage's top
BAL7_LID_HOLE = 30.0
BAL7_DOOR_OPEN = 70.0                # side doors slid back for the beaker (38 mm): keeps them in front of the P16's cross bar
# --- the latch (v6's, its spring pocket fixed) ---------------------------------------------------------------------------
LATCH7_CARRIER_X1 = 266.0            # the bolt's carrier ends here (v6: 270): the spring gets 11.5 mm closed (v6: 6.0, solid at 4.5)
LATCH7_CHANNEL_X1 = 277.5            # channel's back wall, 1.5 mm inside the housing's end (279)
LATCH7_SPRING = (3.0, 14.0, 0.3, 2.6)   # OD, free length, rate N/mm, solid length: 0.75 N closed, 2.1 N at the cam, 3.0 N by hand
LATCH7_MANUAL = 8.0                  # by hand (taking a plate off): the shelf (7 mm over the keeper) clears by 1 mm
SHELF7 = (7.0, 2.0)                  # v6: 8 mm. At the cam's 4.5 mm it is still 2.5 mm under the keeper


# =====================================================================================================================
# v9 (Sam, PR #185, 2026-11-17): v7 kept as the main version; v9 is a variation on it. "remove the draft cage on the scale. If
# we have close-able plexiglas surrounding the doser, that should be able to replace the draft cage ... add some internal
# panels ... to decrease the draft from the carousel moving around ... a bay window sort of enclosure in the front to give
# more space for the scale ... how close can we get the auger while not sacrificing the good aspects of the electronics
# carriage designs? ... you can put the scale on a block instead of lowering the whole multidoser." The carousel, the ladder,
# the station's P16 and guides, the dock on posts and the latch are v7's. Sam's frame (x along the auger from the hinge axis,
# y along it, z away from the plate on the auger's side, i.e. down at the station) unless a comment says "world".
# =====================================================================================================================
# --- what sits over the beaker (study.py, from v7's CAD, the beaker's lip + 2 mm): v7's EC body 69.9 mm under the exit
# (parked), its solenoid 62.8, its door finger 35.1, every module's door push strip 22.0, the tube 12.5, the door housing 11.6.
# --- EC v9: v7's EC with its front 18 mm cut off, so nothing of it is over the beaker but a slim door finger ----------------
EC9_FRONT = 20.5                     # as drawn: the EC's new front face (v7: 2.3). The NEMA 11's body starts at 23.3
EC9_WALL = 2.5                       # a new front wall, 20.5-23.0, across the carriage's section (|y| 18, z 18.9-59.2)
FINGER9_T = 3.0                      # the finger is a 3 x 4 mm arm from the front wall to the push strip (as drawn z 16.9-19.9:
                                     # docked 16.0-19.0, 3.5 mm under the tube; parked 26.0-29.0, 4 mm under the closed strip)
SOL9_X = 99.0                        # the solenoid moves behind the gear onto the tail (between the guide shoes), plunger up under
                                     # the tube as before (as drawn: frame z 24-53.7, plunger tip 16). v7's place (x 3.5-20.5) is
                                     # over the beaker, and in v7's layout the NEMA 11's body fills the space in front of the gear
SOL9_CRADLE = (89.0, 109.0, 10.5, 2.5)   # its cradle under the tail's web: x0, x1, half width, floor thickness
# --- the beaker on the pan, the balance on a block ------------------------------------------------------------------------
D9 = 32.0                            # world: exit -> beaker's rim. The parked finger's underside is 29.0 under the exit (3 mm over
                                     # the rim); every passing module's push strip 22.0; the tube 12.5
PAN9_AHEAD = 7.0                     # world: the pan's (and the beaker's) centre this far in front (-x) of the exit: the lip ends
                                     # 7.1 mm in front of the EC's new face, the stream lands 7.4 mm behind the beaker's centre
                                     # (10 mm inside its wall), and the balance's back stays 4.9 mm clear of the guides
BEAKER9_RIM_Z = None                 # set below
BAL9_PAN_TOP = 50.0                  # v7's balance model: the pan's top above the balance's feet (A&D's HR-i drawing; the
                                     # HR-100A's is 86.5, which needs a block 36.5 mm lower)
BLOCK9 = (252.0, 210.0)              # world: the block's footprint (x, y): the balance's feet (x -145.5..72 from the pan, +-9;
                                     # y +-75) with 4-10 mm to spare; its back edge stays 8 mm in front of the guide cross bar
BLOCK9_X = (-160.0, 92.0)            # from the pan's centre (x): front and back edges (the feet are at -145.5 and 72, r 9)
# --- the enclosure: a bay window round the balance, and a weighing chamber inside -----------------------------------------
BAY9_DEPTH = 100.0                   # world: the bay stands this far proud of the front panel's outer face (the balance's display
                                     # nose is 79 mm proud of it)
BAY9_HW = 118.0                      # world: the bay's (and the chamber's) half width about the station, outer faces
BAY9_TOP = 408.0                     # world: the bay's top and the chamber's deck (top face)
BAY9_DOOR = (200.0, 115.0)           # its front door's opening (y width, z height), up to the bay's top (405): the beaker (rim 403.65)
                                     # slides out level under the deck and the bay's top (1.35 mm) and the parked finger (2.8 mm)
DECK9_X1 = 160.0                     # world: the chamber's deck and side baffles end here; the back baffle stands at x 160-163,
                                     # 3 mm in front of the NEMA 34 (x 166); the tilting EC sweeps x <= 156.5 below the deck
DECK9_CUT = (27.0, 160.0, -27.5, 27.5)   # world (x0, x1, y0 - STATION_Y, y1 - STATION_Y): the deck's station opening: the EC
                                     # (x 29-142, y -25..+25 about the station) and the P16's sweep through the deck (x 110-150)
P16SLOT9 = (13.0, 300.0)             # the back baffle's slot for the P16: half width, its bottom (world z)
GUIDEBAR9_NOTCH = 1.0                # the side baffles are notched round the guide cross bar with this much clearance


# =====================================================================================================================
# v10 (Sam, PR #185, 2026-11-19): "instead of a linear actuator on the bottom pushing the augers up, what if it was inside,
# defaulting to fully extending, and then pulling it up to dose? ... None of the wires can cross the carousel boundary, so they
# would have to come out the front and wrap around to the electronics at the back ... try having a keyed rail of some kind on the
# electronics carriage, instead of the kinematic couplings ... each mounting plate would have some kind of T or L bracket that
# would slot into the electronics carriage every time an auger passed the dosing station. Give the entrance and exit a ramp ...
# give the electronics carriage some guides so it's not flopping around in between augers." v10 is v9 (the balance on a block, no
# draft cage, the bay window and the weighing chamber) with the station turned upside down: the EC is inside the loop on the
# plate's side of the module, and nothing of the station is under the auger. Sam's frame (x along the auger from the hinge axis,
# y along it, z away from the plate on the auger's side, i.e. down at the station) unless a comment says "world".
# =====================================================================================================================
# --- the coupled pose: the rail's ramps lift each arriving module this far about its hinge (cap end up, into the loop), so its
# 44T gear rises into mesh with the EC's pinion while the pinion stays 4 mm over the passing carriages' inner faces
TAU0 = 4.0                           # deg
# --- 1. the keyed rail: a printed T-bracket on every plate, a T-slot along the travel (y) under the EC -----------------------
T10_FOOT = (44.0, 76.0, 8.0, 2.0)    # foot on the plate's underside: x0, x1, half width (y), thickness; two M3 x 6 into inserts at x 47.5 and
                                     # 72.5, outside the head so a hex key reaches them (under the rail's 1 mm clearance when coupled)
T10_SCREW_X = (47.5, 72.5)
T10_STEM_X = (57.0, 63.0)            # stem, 6 mm along x (through the slot's mouth)
T10_HEAD_X = (52.0, 68.0)            # head (the T's wings), 16 mm along x
T10_HY = 8.0                         # the bracket's half length along y (16 mm): the hinge pins already hold the module's roll and yaw
T10_HEAD_Z = (-28.0, -31.0)          # head: its underside (on the rail's lips when coupled) and top
RAIL10_CLEAR = 0.3                   # T to slot, each side
RAIL10_FLAT = 1.5                    # the lips' flat, +- about the station (the index repeats to +-0.5)
RAIL10_RAMP = 8.0                    # each ramp's length along y: the module is lifted while |offset| < 8 + 1.5 + 8 = 17.5 mm
RAIL10_FUNNEL = 2.5                  # the slot's mouth flares this much in x and z at each end
RAIL10_X = (45.0, 75.0)              # the rail block, x
RAIL10_BOTTOM = -21.0                # its underside (Sam z at the coupled pose): world >= 459.6 over x 45-75, 1 mm over the passing
                                     # carriages' inner faces (458.65)
RAIL10_TOP = -36.0
# --- 2. the outlet door: v4's shutter (it slides toward the plate to open), its push strip under the exit gone; a 1.5 mm steel
# pull wire from the shutter's boss up through the spring and the housing's cap, then back over the plate's front edge to a printed
# tab inside the loop. A ramp on the EC lifts the tab 6 mm as the module slides in, and the spring shuts the door as it leaves.
DOOR10_WIRE_D = 0.6                  # the door's cable: 0.6 mm stainless wire rope in a 1.6 mm OD PTFE sleeve (a first try used a bent 1.5 mm wire)
DOOR10_TAB_X = (23.0, 33.0)          # the tab, closed (Sam x, y half width, z): 10.5 mm past the plate's underside; it rides on two rails
                                     # either side of its cable (x 28). At x 13-19 (first try)
                                     # the EC's door ramp in front of it met carriage 1's front at 60-65 deg (check_interference --tilt10)
DOOR10_TAB_HY = 2.5
DOOR10_TAB_Z = (-28.0, -30.5)
DOOR10_RAMP_FLAT = 4.0               # the door ramp's flat, +- about the station; it opens the door while |offset| < 6.5
DOOR10_RAMP = 10.0                   # ramp length each end (the door is shut again by |offset| 16.5)
DOOR10_RAMP_X = ((23.5, 26.0), (30.0, 32.5))   # the door ramp's two rails, a slot for the cable between them
# --- 3. EC v10: built on Sam's compact carriage's parts (NEMA 11, 20T steel pinion, solenoid), on the plate's side ---------------
PINION10_Z = -32.25                  # the pinion's axis: 32.25 mm from the auger's axis, as v2-v9
NEMA11_10_X = 93.5                   # its mounting face (1.5 mm behind the 44T gear's back face): the body runs back to x 137, behind the gear; the shaft forward to the pinion
PINION10_X0 = 78.3                   # the pinion's front face (x 78.3-88.3, under the 44T gear at 78.4-88.4)
MOTOR10_RELIEF = (87.0, 140.0, 18.0, 1.5)   # pocket in the plate's underside over the motor: x0, x1, half width, depth
EC10_SPINE = (21.5, 93.5, 9.0, -37.5, -43.0)   # x0, x1, half width, z near, z far: over the door ramp and the rail (from x 10, its front met
                                     # the front chain's A-1 link at 60 deg)
EC10_CHEEK = (88.8, 170.0, 14.5, 19.0, -22.0, -50.0)   # the two cheeks beside the motor: x0, x1, y0, y1, z near, z far
SOL10_X = 156.0                      # the solenoid over clip 2 (x 150-162), plunger toward the plate: it taps the plate's slab there
SOL10_TIP = -19.2                    # plunger tip at rest (Sam z), 1.2 mm off the slab
EC10_ARM = (74.0, 124.0, 14.5, 48.0, -37.5, -43.0)   # the arm out to the P16 and the guide shoe on the world -y side (Sam +y)
P16_10_PIN = (90.0, -30.0)           # the P16's rod-end pin on the arm (Sam x, z); its Sam y is set so the P16 is at world y P16_10_YW
P16_10_YW = -34.0                    # world y of the P16's plane: beside the module (station - 27) and inside the B- shaft (-49.2)
P16_10_BX = -18.0                    # world x of the P16's base pin, on a bracket on the front side plate; z solved for full extension
P16_10_STROKE, P16_10_RETRACTED = 100.0, 147.4   # Actuonix P16-100-22-12-P: stroke + 47.4 hole to hole
SHOE10 = (108.0, 122.0, -30.5, -37.5)  # the guide shoe on the arm: x0, x1, nose tip z, top z (its Sam y as the P16's)
SHOE10_NOSE = (10.0, 4.5)
TILT_MAX_V10 = 65.0                  # the station's tilt limit: check_interference --tilt10 is clear at 4-65 deg; at 70 the EC's front (the door ramp's web)
                                     # meets the front chain's A-1 link. A first door with a bent pull wire reached carriage 1's front edge at 38 deg
# --- 4. the guide and the station beam inside the loop -----------------------------------------------------------------------
BEAM10_YW = -56.0                    # world: a 2020 from the front side plate to the back side plate, crossing both sprocket planes
BEAM10_ZC = 600.0                    #   between the bottom (z <= 564.8) and top (z >= 691) sprockets
GUIDE10_SEAT_GAP = 0.5               # seat under the shoe's nose
# --- 5. the drop and the weighing chamber ----------------------------------------------------------------------------------
D10 = 18.0                           # world: exit -> beaker's rim: the tube (12.5 under the exit) + 1.5 + the deck (3) + 1 mm
PAN10_AHEAD = 0.0                    # the pan's centre right under the exit (nothing of the station is under the module any more)
DECK10_FRONT_X1 = 55.0               # world: the front deck runs to here (clip 1 starts at x 59), then steps down to v9's 408
DECK10_HOLE = 16.0                   # the dose hole in the front deck, under the exit
# --- 6. the latch: its cam opens over the whole of the rail's lift (|offset| < 17.5), so the pin is out before the ramp lifts
LATCH_RAIL_FLAT = 18.0               # v4-v9: 4.0. Its ramps (30 deg, v4-v9 25) end at 25.8, inside the +-28 mm where no carriage tips round a corner
LATCH10_RAMP_DEG = 30.0              # steeper than v6's 25 deg: at 25 the cam's +y end reached the NEMA 34 (home check, 27 mm3)
# --- 7. wiring: the EC's and the P16's leads out through a grommet in the front side plate ----------------------------------
GROMMET10 = (20.0, 26.0)             # hole, grommet flange (McMaster 9600K-style, 3/4 in hole)
CABLE10_D = 7.0                      # the bundle: NEMA 11 (4), solenoid (2), P16 (5) in a braided sleeve


# =====================================================================================================================
# v11 (Sam, PR #185, 2026-11-25): v10's station inside the loop, with: "If the base plates need to be a bit longer, i.e. to give
# some more room for the rotation in the front, then go ahead ... The auger can move a bit as well to get the hinge closer to the
# plate, or the holes in the plate can be bigger ... The augers still need to be able to go up to 90 degrees ... punch a hole
# through the metal plate so the linear actuator has some more room ... I'm still confused about how the T rail thing works ...
# a ramp would be helpful for alignment ... not lifting if it's not necessary ... [the EC] can extend all the way down to the
# dispensing end of the auger, and thus to the cap, so it can directly open it ... move the solenoid up to the first third of
# the auger ... scale it to fit the scale with the higher draft cage (with the beaker sitting on a cylindrical pillar) ... find a
# cheap but still good quality chain ... just make an open door for the scale ... no need to include wires in the model ... Just
# keep a hole in the plate so the wires can get out." The base dimensions changed at the top of this file: CHAIN_L 345 (+40),
# HINGE_X 73 (+40), HINGE_RAISE11 5 (the hinge 5 mm nearer the carriage plate), Z_RUN 366.5 (-98.5). Sam's frame unless "world".
# =====================================================================================================================
TAU0 = 0.0                           # v11: no lift. The rail only aligns; every module stays at rest until the P16 tilts it
# --- 1. the keyed rail, straight: a T-bracket on every plate, a T-slot along the travel under the EC, flared at both ends ---------
T11_FOOT = (44.0, 76.0, 8.0, 2.0)    # foot on the plate's underside: x0, x1, half width (y), thickness; two M3 x 6 into inserts at 47.5, 72.5
T11_SCREW_X = (47.5, 72.5)
T11_STEM_X = (57.0, 63.0)            # stem, 6 mm along x
T11_HEAD_X = (52.0, 68.0)            # head, 16 mm along x
T11_HY = 8.0                         # half length along y
T11_HEAD_Z = (-24.0, -27.0)          # head: its underside (over the lips) and top
RAIL11_CLEAR = 0.3                   # T to slot, each side (x)
RAIL11_LIP_GAP = 0.2                 # lips to the head's underside at rest: the module rests on its own carriage, the lips pick it up as the P16 pulls
RAIL11_FLAT = 4.0                    # the slot's straight part, +- about the station
RAIL11_FUNNEL_L = 8.0                # each flared end's length along y
RAIL11_FUNNEL = 2.5                  # the mouth flares this much sideways and toward the loop at each end: alignment only, the lips stay level (no lift)
RAIL11_FUNNEL_DOWN = 1.5             # ... and the lips' top drops this much toward the plate (the lips are 2.8 mm thick, 1.3 at the mouth)
RAIL11_X = (45.0, 75.0)              # the rail block, x
RAIL11_BOTTOM = -21.0                # its underside: 1 mm over the passing T-brackets' feet (z -18..-20); a first try at -19 ran 1 mm into them
RAIL11_TOP = -31.0
# --- 2. the outlet door, opened directly by the EC (no cable): v4's shutter with a 1.5 mm stainless rod up its spring's axis,
# through the housing's cap, to a printed head; a ramp slot at the EC's front end catches the head and draws it 6 mm toward the loop
DOOR11_ROD_D = 1.5
DOOR11_HEAD = (6.0, 6.0, 2.5)        # head: x, y, z (printed, pressed on the rod's end)
DOOR11_HEAD_Z0 = -23.3               # the head's underside (toward the cap) with the door shut: 3.8 mm over the cap's outer face (-19.5)
DOOR11_LIP_T = 2.2                   # the ramp's lips, between the cap and the head: at the slot's ends they run at z -20.6..-22.8 (1.1 over the
                                     # passing caps), and on the flat 6 mm further toward the loop
DOOR11_RAMP_FLAT = 4.0               # the lips' flat, +- about the station: the door is fully open while |offset| < 4 + 3 (head half width)
DOOR11_RAMP = 10.0                   # each ramp's length along y
DOOR11_SLOT = 2.5                    # the gap between the two lips (x), for the rod
DOOR11_LIP_W = 2.3                   # each lip's width (x). 2026-11-27: was 2.2, which left the lips 0.05 mm short of the channel's walls
                                     # (two floating solids, found by slicing the EC in Bambu Studio); 2.3 runs them 0.05 mm into the walls
# --- 3. EC v11 ---------------------------------------------------------------------------------------------------------------
PINION11_T = 24                      # 24T steel pinion (KHK SS1-24 class): centre distance 34.25 (44T + 24T at module 1, +0.25), so the NEMA 11's
                                     # body (28 mm square on the pinion's axis) clears the passing plates by 2.25 mm with no lift (a 20T put it 0.25 mm off)
PINION11_Z = -34.25                  # the pinion's (and the motor's) axis
PINION11_X0 = 78.3                   # its front face (x 78.3-88.3, under the 44T gear at 78.4-88.4)
NEMA11_11_X = 93.5                   # the NEMA 11's mounting face, behind the gear; body to x 137
EC11_FRONT = -8.6                    # the EC's front face: it reaches past the outlet to the door rod's head (Sam: "extend all the way down to the
                                     # dispensing end of the auger, and thus to the cap")
EC11_BOTTOM = -19.0                  # 1 mm over the passing plates and carriages; over the doors' caps (-19.5) it is -20.6
EC11_HW = 9.0                        # the spine's half width
EC11_SPINE_Z = (-33.0, -37.5)        # the spine: its underside and top (over the door ramp, the solenoid's yoke and the rail)
SOL11_X = 32.0                       # the solenoid over clip 1 (Sam's clip, x 28-37): 13 % of the auger's length from the exit (v10: x 156, 62 %)
SOL11_TIP = -19.2                    # plunger tip at rest, 1.2 mm off the plate's underside (it taps the plate where clip 1 holds the tube)
EC11_CHEEK = (88.8, 140.0, 15.5, 19.5, -20.5, -50.5)   # the cheeks beside the NEMA 11: x0, x1, y0, y1, z near, z far
P16_11_PIN = (96.0, -25.0)           # the P16's rod-end pin on the EC's arm (Sam x, z): behind the gear (its back face 88.4) by the clevis's 6 mm and 1.6
P16_11_YW = -31.0                    # world y of the P16's plane: beside the module (station - 27) and inside the B- shaft (-49.2); its slot in the
                                     # front plate (y -41.5..-19.5) keeps 0.7 mm of plate under the T- tensioner block (y -72.2..-42.2; at -33 the housing hit it)
P16_11_B = (-62.0, 612.0)            # world (x, z) of the P16's base pin: in front of the front side plate (its outer face at x -36.35), on a clevis
                                     # hanging from a new 2020 bar across the front posts. Numerically (layout.p16_11_ext): 0-90 deg takes the
                                     # P16-150 from 336.6 to 205.7 mm hole to hole (10.8 short of full extension, 8.3 over full retraction), its
                                     # lever about the hinge 87 mm at rest and 30 mm or more all the way; its line passes 514 mm or higher over
                                     # the front chain plane (the B- sprocket tops out at 461 there)
EC11_ARM = (90.0, 126.0, 14.5, 46.0, -20.0, -30.0)    # the arm out to the P16 and the guide shoe on the world -y side: x0, x1, y0, y1, z near, z far
SHOE11 = (133.0, 145.0, -24.5, -31.6)  # the guide shoe: x0, x1, nose tip z, top z. 2026-11-27: moved behind the arm. v11 had lowered the arm to
                                     # z -20..-30 (the P16's pin at -25) but left the shoe at v10's -38..-31, so it floated 1 mm over the arm and
                                     # the guide's seat block, built under its tip, sat inside the arm (1759 mm3; the check skipped the pair). The
                                     # seat can't go under the arm (the passing plates are 2 mm below it), so the shoe now hangs from a bracket off
                                     # the arm's back (SHOE11_BRACKET), nose down, and the seat block sits behind the arm, 1 mm over the plates
SHOE11_Y = 36.0                      # its Sam y (near the P16's plane, 35.8)
SHOE11_BRACKET = (120.0, 147.0, -35.0, -31.5)  # the bracket from the arm's back to the shoe: x0, x1, z0, z1 (a riser joins it to the arm's far face)
TILT_MAX_V11 = 90.0
# --- 4. the P16 through the front side plate, its base on a bar across the front posts ------------------------------------------
P16SLOT11_Y = (-41.5, -19.5)         # the front side plate's slot for the P16 (world y): its housing (20 wide, y -41..-21) passes with 0.5-1.5 mm
P16SLOT11_PAD = 2.0                  # the slot's z range is the housing's and tube's sweep where they cross the plate, plus this
BAR11_ZC = 630.0                     # world: a 2020 across the front posts' front faces (x -76.35..-56.35), z 620-640: in front of the top bearings'
                                     # housings (to x -52.4), the P16's base clevis hanging from its underside
PANEL_STANDOFF_FRONT11 = 30.0        # the front acrylic panel on 30 mm standoffs (v10: 6): it clears the bar and the P16's housing, which bulges
                                     # down-front of its axis (to x -77.4) by 9 mm
# --- 5. the guide and the station beam inside the loop ---------------------------------------------------------------------------
BEAM11_YW = -56.0                    # world: 2020 from the front side plate to the back, crossing both sprocket planes 7 mm over the B- sprocket;
                                     # its guide's hanger (y -46..-42) passes 3 mm inside the B- shaft (at y -60 it crossed it)
BEAM11_ZC = 482.0
GUIDE11_SEAT_GAP = 0.5
# --- 6. the balance with its tall draft cage, on the bench; the beaker on a cylindrical pillar ----------------------------------
BAL11_CAGE_H = 254.0                 # the chamber's height over the pan: v7's model 4 mm taller, so the cage is 315 mm tall (the lab's HR-100A's height)
BAL11_TOP = HR2_PAN_TOP + BAL11_CAGE_H + BAL7_GLASS + BAL7_FRAME   # 315: the cage's top frame
BAL11_GEAR_CLEAR = 4.0               # the passing 44T gears (23 mm under the exit) over the cage's top frame
PILLAR11 = (40.0, 0.85)              # the beaker's pillar: OD, wall (printed PETG tube with a socket for the beaker on top). 2026-11-27: wall 1.6 ->
                                     # 0.85 (two 0.42 mm lines): Bambu Studio put the 1.6 mm wall at 53.6 g, half the HR-100A's 102 g; 0.85 slices to 29.9 g
LID11_T = 3.0                        # the dosing lid, set into the top frame's opening (the top door slid out), flush with the frame's top
LID11_HOLE = 24.0                    # its hole under the exit
BEAKER11_UNDER_LID = 3.0             # the beaker's rim this far under the lid
# --- 7. the front panel's doorway for the balance (no bay window, no weighing chamber) -------------------------------------------
DOOR_BAL11 = (240.0, 330.0)          # the opening (y width, z height), from the bench up, centred on the station
# --- 8. wiring: not drawn (Sam: "no need to include wires in the model unless it changes"); the grommet hole stays in the front plate
GROMMET11 = (20.6, 26.0)            # 2026-11-27: 13/16 in hole (was 20): no grommet with a 3/8 in inside fits a 3/4 in hole in 1/4 in plate
# --- 9. what the lower carousel (Z_RUN 366.5) moved: the ladder's rungs (they carry nothing in v11 but tie the posts, Sam: "I love the
# ladder rungs") go under the back plate's new bottom edge (226.5) and over the posts' foot brackets; the latch cam's foot narrows
RUNG11_LOW_ZC = 86.0                 # world: the lower rungs (their brackets under them, over the posts' foot brackets at z 35-55)
RUNG11_UP_ZC = 214.0                 # world: the upper rungs, their tops 2.5 mm under the back side plate's bottom edge
LATCH11_FOOT_Y = 21.0                # Sam y: the latch cam's web and foot keep to Sam y >= this near the back plate, beside the back hold-down
                                     # (Sam y -20..20): with the hinge 5 mm nearer the carriage the cam came 5 mm nearer it and ran into it
LATCH11_FOOT_DY = (8.0, 20.0)        # its two M5 through the back plate, from LATCH_Y6 (v6-v10: -9, +9)
GROMMET11_YZ = (P16_11_YW, 500.0)   # world: the wires' hole in the front side plate, under the P16's slot (the bundle runs out beside the P16)
