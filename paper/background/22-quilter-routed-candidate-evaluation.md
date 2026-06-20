# Evaluation of the six Quilter-routed candidate boards

_Hands-on engineering note (not an Edison output). Answers @lbwinters'
prompt on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4755680152)
(relayed by @sgbaird,
[4755863119](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4755863119)):
go through each of the six Quilter.ai auto-placed-and-routed boards, highlight
and where possible fix any errors, do thorough visual + electrical testing,
recommend the best candidate, and explain the pins that "appeared to be
sticking up right where the pico and rs232 should go" in the 3-D view._

The six boards are committed verbatim under
[`starter_board/quilter_candidates/`](starter_board/quilter_candidates/) (see
its [`README`](starter_board/quilter_candidates/README.md) for the
attachment ↔ folder map). They are Quilter's output for the **`test_module_unplaced`**
board from [`build_starter_board.py`](starter_board/build_starter_board.py)
(100 × 100 mm, 15 footprints, 24 nets).

## Method

All numbers are reproducible with
[`quilter_candidates/analyze_quilter_candidates.py`](starter_board/quilter_candidates/analyze_quilter_candidates.py)
(`analysis_summary.json` is the captured run):

* **Connectivity / DRC** — KiCad 7 `pcbnew` is authoritative:
  `BuildConnectivity().GetUnconnectedCount()` for the ratsnest and
  `pcbnew.WriteDRCReport(...)` for the full design-rule pass (bucketed by
  violation type).
* **Geometry** — `kiutils` for outline, copper layers, plane nets, routed
  track length, via count, no-net copper, and per-net track widths.
* **Visual** — `kicad-cli pcb export svg` of `F.Cu`/`B.Cu`/`Edge.Cuts`/`F.SilkS`
  → the montage
  [`candidates_top+bottom_copper.png`](starter_board/quilter_candidates/candidates_top+bottom_copper.png).

> "Electrical simulation" in the SPICE sense is not meaningful here in the
> *small-signal / analog* reading — the board is a digital control + motor-driver
> carrier (no analog signal chain to solve), and the active parts are pre-built
> modules. The electrically relevant checks are therefore **connectivity,
> clearance/short DRC, current-carrying capacity of the power traces, and
> ground/return integrity**, all of which are covered above. The *power*-delivery
> side **is** worth simulating, and note
> [`23`](23-ngspice-power-integrity-simulation.md) does exactly that with
> **ngspice** (a resistor-mesh IR-drop `.op` solve of each candidate's routed
> +12 V / +5 V copper, plus a transient decoupling `.tran`), quantifying the thin
> 6 mil power-trace warning below.

## What every candidate has in common (the design Quilter received)

All six are the **same board**, so they share these traits — most of the
findings below are about the *upload*/Quilter settings, not any single
candidate:

* **4-layer stack, `Signal / GND / GND / Signal`.** `F.Cu` and `B.Cu` are the
  routed signal layers; **both** inner layers (`In1.Cu`, `In2.Cu`) are solid
  **`GND`** pours. This is good — it gives a continuous return plane directly
  under both the noisy +12 V/motor copper and the quiet 3V3/I²C/RS-232 copper,
  and it is what clears the *"No ground layer defined"* warning @lbwinters saw
  with the 2-layer stack (PR #76 point 3). There is **no dedicated power
  plane**, so +12 V / +5 V are distributed on traces only (see below).
* **Fully routed — 0 unconnected.** `pcbnew` reports an **unconnected ratsnest
  of 0** on all six: Quilter completed 100 % of the 24 nets. ✅
* **No copper-clearance, track-width, or hole DRC errors** on any candidate
  (0 each) — no shorts, no spacing violations. ✅
* **~½ of the routed copper is exported with no net** (`(net 0)` segments:
  266–306 of ~530–570 tracks). The traces are still physically connected (hence
  the 0 ratsnest), but the lost net labels are why KiCad's DRC reports ~**199
  `solder_mask_bridge`** "errors": a no-net track running between two header
  pads makes KiCad think the mask aperture bridges *different* nets. This is a
  **Quilter export quirk**, identical across all six, not a routing defect — see
  *Issues & fixes*.

## Per-candidate metrics

| candidate | outline | layers | track length | vias | no-net tracks | unconnected | mask slivers | silk overlaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 100×100 | 4 | **1470 mm** | **85** | 266 | 0 | 199 | 2 |
| 2 | 100×100 | 4 | 1187 mm | 78 | 302 | 0 | 199 | 0 |
| 3 | 100×100 | 4 | 1191 mm | **76** | 295 | 0 | 199 | 0 |
| **4** | 100×100 | 4 | **1077 mm** | **76** | 295 | 0 | 199 | 3 |
| 5 | 100×100 | 4 | 1249 mm | 80 | 292 | 0 | 198 | 2 |
| 6 | 100×100 | 4 | **1069 mm** | 79 | 306 | 0 | 199 | 4 |

(Track length and via count are the discriminators — everything else is either
identical or cosmetic. Lower length = less loop inductance / coupling; fewer
vias = fewer drilled layer-transitions, i.e. lower cost and higher yield.)

## Issues & fixes

1. **3-D "pins sticking up" at the Pico / RS-232 — root-caused and fixed.**
   In the 3-D view the Pico W (`U2`), the RS-232 module (`J2`) and the Tic
   carrier (`U5`) showed a column of bare pins standing straight up where the
   module body should sit. Cause: those three parts mount on a **generic 0.1″
   pin header** (the real land pattern) with no vendor STEP, so the generator
   fell back to the *library footprint's own* 3-D model — which for a
   `PinHeader_1x20/1x08_…_Vertical` footprint is a bare vertical header. KiCad
   then drew the header pins with nothing on top.
   **Fix** (in [`build_starter_board.py`](starter_board/build_starter_board.py),
   new `_is_header_carrier()`): for a module that mounts on a generic header and
   has no vendor STEP, the misleading header model is **omitted**, so KiCad
   shows the part's real `F.Fab` body outline with no phantom pins. The genuine
   pin-header connectors (`M1`–`M3`, `SOL1` — actual headers a cable plugs into)
   keep their pin-header model, and the parts with real STEPs (buck, shunt,
   DRV2605L, DRV8871, barrel jack, caps) are unchanged. The fix is in the
   *generator*, so it benefits the next upload; the six already-routed
   candidates still carry the old model and will show the phantom pins until
   re-exported. A proper module STEP (`Module:RPi_Pico`, a Waveshare-module
   model) can be dropped into `PACKAGES` later for a fully accurate 3-D body.

2. **No-net copper → solder-mask slivers (all six).** ~½ the tracks carry
   `(net 0)`, producing ~199 `solder_mask_bridge` DRC hits. Two practical
   mitigations, both outside the board file: (a) in KiCad, *Tools → Update PCB
   from Schematic* (or *Edit → Cleanup Tracks & Vias*) re-propagates net codes
   onto the touching copper, which clears most of these; (b) for fab, JLCPCB and
   most houses merge/relieve sub-0.25 mm mask webs automatically, and the slivers
   sit between same-net-after-cleanup header pads. This is a **Quilter-side
   export issue** — worth reporting to Quilter — not a defect we can clean in
   the verbatim files without re-routing.

3. **Power traces are thin — Quilter ignored the `Power` net class.** Every
   candidate routes **all** copper at **0.153–0.16 mm (~6 mil)**, including the
   +12 V input and the solenoid/stepper motor-power nets, even though the
   uploaded `.kicad_pro` defines a `Power` net class at **0.6 mm**. In KiCad 7
   the net-class widths live in the **project file, not the `.kicad_pcb`**, so a
   router that ingests only the board never sees them. At 6 mil / 1 oz copper
   the IPC-2221 ampacity is only ~0.5–0.7 A (10 °C rise); the DRV8871 solenoid
   and the Tic/stepper rail can peak above that. **Action for the re-run:** set
   the power-net trace width (≥0.5–0.8 mm) and current target **in Quilter's own
   net-class/rules UI** before routing, since the KiCad project net class does
   not transfer.

4. **Silk overlaps (0–4) and `lib_footprint_issues` (15) are cosmetic/benign.**
   The silk hits are reference-designator labels clipped by a neighbour's
   courtyard; the 15 library warnings are only *"library not configured"* for
   our `powder_doser_parts`/`Capacitor_THT` libs (we ship the footprints inline,
   so KiCad still renders them). Neither blocks fabrication.

## Recommendation

All six are electrically equivalent (100 % routed, no shorts/clearance errors,
same 4-layer 2×GND stack, same systemic export quirks), so the choice comes
down to **routing efficiency**:

> **Use Candidate 4.** It has the **fewest vias (76, tied with 3)** *and* the
> **second-shortest total copper (1077 mm)** — the best combined score, i.e. the
> least loop inductance and the fewest drilled layer-transitions (lowest cost /
> highest yield). Its only downside is 3 cosmetic silk-label overlaps.

* **Close alternative — Candidate 6** (1069 mm, the shortest copper, but 79 vias
  and 4 silk overlaps). Pick it over 4 only if absolute trace length matters
  more than via count.
* **If you want zero silk-label cleanup — Candidate 3** (76 vias, 0 silk
  overlaps, 1191 mm) is the tidiest, at ~10 % more copper than 4.
* **Avoid Candidate 1** — clearly the weakest: the longest copper by far
  (1470 mm, +37 % vs 4) and the most vias (85), because it placed the Pico and
  RS-232 modules far apart and bridged them with long diagonal traces (visible
  top-left of the montage).

Before sending any candidate to fab: re-open it in KiCad, run *Update PCB from
Schematic* + *Cleanup Tracks & Vias* (clears the no-net/mask-sliver noise), and
re-route the four power nets at ≥0.5 mm — or, better, **re-run Quilter once with
the power-net width set in its rules UI and the generator's fixed 3-D models**,
then re-pick from a clean set. Even the best candidate still warrants a human
pass on mixed-signal partitioning (keep the +12 V switching/motor return away
from the load-cell/RS-232 reference) before committing to a build.
