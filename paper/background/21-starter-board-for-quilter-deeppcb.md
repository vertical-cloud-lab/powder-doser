# Generated KiCad starter board for Quilter / DeepPCB

_Hands-on build note (not an Edison output). Implements the Rank-1
recommendation from note [`20`](20-topology-to-starter-board-for-powder-doser.md):
turn this repo's existing control-board **schematic** (the
`hardware/test-module/kicad/` project from PR
[#61](https://github.com/vertical-cloud-lab/powder-doser/pull/61) — 14 parts,
20 nets, but **no footprints / no `.kicad_pcb` / no outline**) into an actual
**router-ready starter board** that can be uploaded to the autonomous-layout
vendors from notes [`16`](16-quilter-ai-pcb-layout.md) (Quilter) and
[`17`](17-deeppcb-ai-pcb-routing.md) (DeepPCB). Answers @sgbaird's request on
PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654482011)
("try to make an actual starter board that we could upload to quilter or
DeepPCB")._

> **Update (PR #100 scale-integration alignment, rev B).** Following
> @lbwinters' request on PR
> [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4918742223)
> to regenerate the KiCad files against the changes in PR
> [#100](https://github.com/vertical-cloud-lab/powder-doser/pull/100)
> (closed-loop dosing with the A&D HR-100A balance, issue #99), the netlist now
> matches PR #100's `hardware/test-module/kicad/generate.py` rev B exactly:
>
> - The scale interface is the **Waveshare Pico-2CH-RS232 module as `U6`**
>   (`Waveshare_2CH_RS232`), reached through its **channel-0 4-pin TTL header**
>   (`VCC`/`GND`/`TXD`/`RXD`) — PR #100: *"only its 4-pin TTL header reaches
>   the Pico"*. The previous model (a 40-pin Pico-form-factor receptacle `J2`
>   with board copper re-routing four UART lines) is replaced.
> - **`VCC` is on `+3V3`, not VSYS/+5 V**, so the module's TTL-side swing stays
>   inside the RP2040's −0.3/+3.6 V absolute maximum (the on-board charge pump
>   makes the ±RS-232 rails from 3.3 V). This is the safety conclusion of
>   PR #100's ngspice analysis (`rs232_analysis.py`, 9/9 checks — re-run and
>   re-confirmed during this regeneration).
> - Nets renamed to PR #100's **`SCALE_TX`** (`GP12` → `U6.TXD`) and
>   **`SCALE_RX`** (`GP13` ← `U6.RXD`) — the module's TTL header is labelled
>   from the Pico's point of view, so the link wires **straight across** with
>   no crossover and no copper re-map. The spare channel-1 nets
>   (`RS232_1_TXD`/`RS232_1_RXD` on `GP8`/`GP9`) are dropped: PR #100 doesn't
>   use them, and channel 1 stays available on the module itself.
>
> Board counts become **15 footprints / 101 pads / 75 net-assigned / 22
> nets** (placed outline ~140 × 82 mm; unplaced target stays 100 × 100 mm).
> A source-level cross-check of `NETLIST` against PR #100's `PLACEMENTS`
> confirms identical refs (`J1`,`C1`–`C3`,`U1`–`U6`,`SR1`,`SOL1`,`M1`–`M3`),
> identical 22-net set, and identical pin→net maps — the only deltas are this
> board's two physical-pin corrections (Pololu #3776's duplicate `A`/`B`
> access holes; the D24V22F5's real single `GND`), both electrically
> equivalent. A `kicad-cli` netlist comparison against PR #100's committed
> `test_module.kicad_sch` confirms the scale nets connect identically
> (`SCALE_TX`/`SCALE_RX`: `U2`↔`U6`); it also revealed that PR #100's
> schematic still carries PR #61's off-by-2.54 mm label bug on its small
> symbols (its exported netlist leaves `C1`–`C3`, `J1`, `SR1`, `M1`–`M3`,
> `SOL1` floating) — this generator computes label positions from the pin
> endpoints, so all 22 nets here are fully populated (75 pins, zero
> unconnected).

> **Update (RS-232 scale-interface module).** Following @lbwinters' and
> @sgbaird's requests on PR
> [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4721881856)
> ([and](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4723451001))
> to add the footprints needed to integrate the **A&D balance** for gravimetric
> dosing, the board now carries a **Waveshare Pico-2CH-RS232** module
> (`SP3232EEN`, 2 channels). It mounts on a **side 2×20 header** next to the
> Pico W — in the spirit of Adafruit's [Proto Doubler PiCowbell #5906](https://www.adafruit.com/product/5906) —
> so its **own embedded RS-232 charge-pump capacitors** stand in for a discrete
> `MAX3232` + ~5 caps on our board. Because the module hard-wires its channels to
> `GP0/GP1` and `GP4/GP5` (already used here for I²C and the Tic UART), board
> copper re-routes the four UART lines to *free* Pico UART pins: **UART0
> `GP12/GP13` = channel 0 (scale)** and **UART1 `GP8/GP9` = channel 1 (spare)**.
> The board therefore grows to **15 footprints / 137 pads / 86 net-assigned /
> 24 nets** (the new `J2` receptacle plus 4 new RS-232 nets); `kicad-cli sch
> export netlist` confirms 86 pins across 24 named nets with zero unconnected,
> `pcbnew` reports **0 courtyard overlaps** on both trios, output stays
> byte-for-byte reproducible and Quilter-compatible (KiCad 7 `20221018`), and
> the wider logic domain pushes the outline to ~141 × 82 mm. The module
> datasheets are committed under
> `hardware/vendor-files/waveshare-pico-2ch-rs232/datasheets/`.
> *(Superseded by the PR #100 alignment update above: the module is now `U6`
> on its 4-pin TTL header, powered from `+3V3`, nets `SCALE_TX`/`SCALE_RX`.)*

> **Update (real component packages).** Following @sgbaird's follow-up on
> PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4654591085)
> ("I committed a bunch of files related to the components already … run
> again, full"), the build no longer uses generic header *proxies*: each
> component's **body outline, courtyard, and 3-D model** are now taken from
> the real vendor design files committed under
> [`hardware/vendor-files/`](https://github.com/vertical-cloud-lab/powder-doser/tree/copilot/identify-vibration-motor-solenoid-parts/hardware/vendor-files)
> (PR [#25](https://github.com/vertical-cloud-lab/powder-doser/pull/25)).
> The netlist (20 nets) is unchanged; only the geometry is now real.

> **Update (real KiCad land patterns).** Following @lbwinters' request on
> PR [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4696547112)
> ("swap those placeholders for the exact kicad footprints, so that we're
> working with the real parts and not ai-generated placeholders … just do that
> now instead of waiting for when we're finalizing the design"), the **pads
> themselves are no longer synthesized.** Every part's land pattern is now copied
> from a genuine KiCad 7 library footprint
> ([`starter_board/kicad_footprints/`](starter_board/kicad_footprints/) —
> vendored verbatim from the upstream `kicad-footprints` library so the build
> stays self-contained), remapped pin-by-pin onto this board's netlist:
>
> - **Caps** → `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` (square pin-1 `+`, round `−`, 3.5 mm pitch).
> - **Barrel jack** → `Connector_BarrelJack:BarrelJack_Horizontal` (real tip / sleeve / switch lugs).
> - **Off-board actuators + Pololu carriers** → real `Connector_PinHeader_2.54mm:PinHeader_1x0N` land patterns (the genuine 0.1″ headers these parts plug into), with the carriers' real vendor body overlaid on top.
> - **Raspberry Pi Pico W** → two real `PinHeader_1x20` columns at the documented **17.78 mm** castellation spacing (KiCad 7.0.11 ships no dedicated Pico footprint).
>
> Pad counts / nets are unchanged (14 footprints, 97 pads, 69 net-assigned,
> 20 nets); only the geometry under each pad is now a manufacturer-grade land
> pattern. Output stays byte-for-byte reproducible and Quilter-compatible
> (KiCad 7 format `20221018`); `pcbnew`'s DRC reports **0 footprint errors**
> (no courtyard overlaps) on both trios.

![Generated starter board (real component bodies + nets + Edge.Cuts outline, unrouted)](starter_board/test_module_starter.png)

## What this is

Notes `16`/`17` established the missing-middle problem: Quilter and DeepPCB
only do **placement + routing**, and both *require a fully-defined starter
board as input* — a `.kicad_pcb` whose footprints already carry assigned pads,
a netlist, and a board outline (Edge.Cuts). The bench-rig schematic on PR #61
has the complete topology but stops at the schematic; note `20`'s audit found
the footprints, board file, outline, and placement all missing.

[`starter_board/build_starter_board.py`](starter_board/build_starter_board.py)
closes that gap. It is fully **headless and self-contained** — it depends only
on the pure-Python [`kiutils`](https://pypi.org/project/kiutils/) package (no
KiCad install, no GUI, no network, no logins), so it runs in the GitHub/Copilot
sandbox and in CI — and emits, under
[`starter_board/`](starter_board/):

| File | What it is |
| --- | --- |
| [`test_module_starter.kicad_pcb`](starter_board/test_module_starter.kicad_pcb) | The starter board: 15 footprints, 101 pads (75 net-assigned), real component body outlines (F.Fab) + courtyards (F.CrtYd), 4 vendor 3-D models, and a compact, domain-grouped ~140 × 82 mm Edge.Cuts outline. **This is the file you upload.** |
| [`test_module_starter.kicad_sch`](starter_board/test_module_starter.kicad_sch) | The matching **schematic** (15 symbols, 22 nets, 75 connected pins) — DeepPCB / Quilter ask for this alongside the board. Built from the *same* `NETLIST` / `PINOUTS`, so its netlist is identical to the board's; connectivity is global-label-only (no wires beyond short label stubs), verified pin-by-pin with `kicad-cli`'s netlist exporter. |
| [`test_module_starter.kicad_pro`](starter_board/test_module_starter.kicad_pro) | Project / DRC rules: `Default` (0.25 mm track / 0.2 mm clearance) and a wider `Power` net class (0.6 mm track / 0.3 mm clearance) assigned to `+12V`, `+5V`, `+3V3`, `GND`. Registers the schematic root sheet so the `.kicad_pcb` / `.kicad_sch` / `.kicad_pro` open together as one project. |
| [`test_module_starter.svg`](starter_board/test_module_starter.svg) / `.png` | Board preview — bodies, pads, ratsnest, outline (rendered by `kicad-cli` when present, otherwise by the script's built-in dependency-free SVG fallback). |
| [`test_module_starter_schematic.svg`](starter_board/test_module_starter_schematic.svg) / `.png` | Schematic preview (rendered by `kicad-cli` when present). |
| [`starter_board_summary.json`](starter_board/starter_board_summary.json) | Machine-readable BOM + net summary, including each part's real `body_mm`, vendor 3-D `model` path, and `source` provenance, plus the `unplaced_variant` filenames/outline. |

### Two variants: pre-placed vs. unplaced (auto-place test)

The generator emits **two** upload trios from the same netlist so the autonomous
tools can be tested on *placement* as well as *routing*, and so their placement
can be compared against this generator's:

| Variant | Files | Components | Use |
| --- | --- | --- | --- |
| **Placed** (default) | `test_module_starter.kicad_pcb` / `.kicad_sch` / `.kicad_pro` | Domain/cluster-packed **inside** the ~140 × 82 mm outline | Upload to test **routing** of a board this generator already placed. |
| **Unplaced** | `test_module_unplaced.kicad_pcb` / `.kicad_sch` / `.kicad_pro` | Same parts/nets, staged **outside** a right-sized **100 × 100 mm** empty outline | Upload to test the tool's **auto-placement** (then routing); compare its placement against the placed variant. |

The two variants share the same netlist and symbols; the schematics differ only
in the owning project name (each `.kicad_sch` names *its own* project so the
trio is internally consistent — see [Quilter review fixes](#quilter-review-fixes-pr-76-comment-4723827215)).
The unplaced board's Edge.Cuts target is a **right-sized 100 × 100 mm square**
(independent of the wider placed floorplan) with every footprint shifted one
outline-width + 12 mm to its right, so the board area is empty and the router
must place the parts onto a sensibly-sized board.

![Generated starter-board schematic (15 symbols, 22 nets, global-label connectivity)](starter_board/test_module_starter_schematic.png)

## How it was built (note `20` Rank 1)

1. **Netlist provenance.** The `NETLIST` and `PINOUTS` tables in the script
   started from the `PLACEMENTS` / `SYMBOL_PINS` structures in PR #61's
   `hardware/test-module/kicad/generate.py` (commit `147e505`), so the component
   set and net connectivity match the bench-rig schematic. The **physical pin
   counts** were then corrected part-by-part against the manufacturers' pinouts
   and the `hardware/vendor-files/` datasheets/Eagle files (PR #25) — PR #61's
   symbols were simplified placeholders (e.g. the Pico W had only 15 pins). See
   **[Pin-count verification](#pin-count-verification)** below for the audit and
   every change. Keeping the tables inline makes the build reproducible on *this*
   branch without needing the PR #61 hardware tree present.
2. **Real component packages (from the committed vendor files).** Each
   *physical* pin of the real part becomes one through-hole **0.1″ pad** (so a
   Pico W footprint has all 40 pads, a Tic T500 all 14, etc.; pins sharing a
   name, such as the Pico's eight GND, are all tied to the same net), but the
   body **outline, courtyard, and 3-D model** now come from the real vendor
   design files committed under `hardware/vendor-files/` (PR #25), via the
   `PACKAGES` table:
   - **Adafruit breakouts** (DRV2605L #2305 → 17.78 × 16.51 mm, DRV8871 #3190 →
     20.32 × 24.13 mm): outline read from the vendor **Eagle `.brd`** (layer 20 /
     Dimension); their `.step` is attached as the footprint 3-D model.
   - **Pololu carriers** (D24V22F5 #2858, Tic T500 #3135, shunt regulator #3776):
     published 0.1″-grid PCB size, cross-checked against the vendor **STEP**
     envelope; the `.step` (where a loose file exists) is attached.
   - **Off-board actuators** (NEMA-11 stepper, servo #1142, solenoid #412, ERM
     #1201): they live *off* the board, so they appear only as their on-board
     **connector** (header auto-sized to the pins); the actuator body / STEP is
     recorded in the BOM `source` for reference, not drawn as a board courtyard.
   - **Raspberry Pi Pico W** (PR #61's MCU, not in the PR #25 vendor set):
     the full **40-pin** 2×20 0.1″ castellated module, 21 × 51 mm (the long
     51 mm edge runs along the pin columns).

   3-D model paths point at `hardware/vendor-files/…` so they resolve once PR #25
   merges; KiCad simply omits a missing model and the `.kicad_pcb` stays
   self-contained.
3. **Net assignment.** A board net table is built and every connected pad is
   tagged with its net, so the board carries the full 20-net ratsnest.
4. **Floorplan + outline.** The schematic-sheet anchor coordinates are *ignored*
   for the board; instead `_pack_positions()` lays the real component bodies out
   with a **domain- and cluster-aware compact packer** (see *Compact placement*
   below): each regulator/driver is packed in one contiguous row with its caps
   and load connector, the power/mechanics domain sits on the left and the
   logic/control domain on the right (separated by a `DOMAIN_GAP` aisle), and
   each cluster's off-board connector is biased to the outward board edge. A
   `_assert_no_overlap()` courtyard check guarantees the result stays DRC-clean,
   and an Edge.Cuts rectangle is drawn around all component courtyards + 5 mm.
   Absolute placement is unimportant — Quilter/DeepPCB re-place everything — but a
   domain-grouped start hands them short local nets.
5. **Schematic companion.** From the same `NETLIST` / `PINOUTS`, the script also
   emits `test_module_starter.kicad_sch`: each part becomes a labelled rectangle
   symbol with one pin per physical pin (numbered exactly like the board pads),
   and each connected pin gets a global net label on a short stub wire.
   KiCad treats matching global labels as one net, so the 20-net topology is
   reproduced with no drawn nets to route. `validate_schematic_netlist()` then
   round-trips it through `kicad-cli` to prove the connectivity (see below).
   This answers @lbwinters' request on PR
   [#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4663888863)
   for the `.kicad_sch` needed to run a Quilter / DeepPCB test.

## Verification

The build is verified structurally and headlessly with `kiutils`, the builder's
own geometry guard, and `kicad-cli`'s netlist exporter:

- **15 footprints / 101 pads / 75 net-assigned / 22 nets** — re-parsed from the
  written `.kicad_pcb`. Every physical pin of each real part is now a pad (the
  Pico W's full 40, the Waveshare RS-232 module's 4-pin TTL header, the Tic
  T500's 14, etc.), with every same-named pin (e.g. the eight Pico GND pins)
  tied to its net.
- **No courtyard overlaps** — `_assert_no_overlap()` checks every pair of real
  F.CrtYd extents before writing the board and raises if any two collide, so the
  compact placement stays clearance-clean.
- **12 3-D models attached** — 4 from vendor STEP files (DRV2605L, DRV8871,
  D24V22F5, shunt regulator), the rest from the parts' own KiCad library
  footprints (the Pico / RS-232 / Tic header-carriers deliberately omit the
  misleading bare-header model — see note `22`) — plus **60 F.Fab**
  body-outline + **60 F.CrtYd** courtyard segments.

**Compact, domain-aware placement (issue [#94](https://github.com/vertical-cloud-lab/powder-doser/issues/94)).**
The first DeepPCB run flagged the board as *"still very spaced out"*: the earliest
build reused the schematic-sheet anchor coordinates as the board floorplan, which
left 14 small breakouts strewn across a **279 × 199 mm** board (routers keep that
excess area). The board now ignores those coordinates and `_pack_positions()`
**domain- and cluster-packs** the real component bodies. The first fix was a pure
area shelf-pack (~80 × 118 mm); the Edison review below then asked for placement
*intelligence*, so the packer now:

- packs each **cluster** (a regulator/driver with its decoupling caps and its
  off-board load connector) as one rigid contiguous row, keeping the high-value
  local nets — driver→load, regulator→cap — short;
- lays the **power/mechanics domain** (barrel jack, buck, DRV8871+solenoid,
  shunt+Tic+stepper) on the **left** and the **logic/control domain** (Pico,
  DRV2605L+ERM, servo) on the **right**, separated by a `DOMAIN_GAP = 6 mm`
  aisle, partitioning the noisy +12 V switching from the quiet 3V3/I2C nets;
- biases each cluster's **off-board connector** (`J1`, `SOL1`, `M1`–`M3`) to the
  outward end of its row (left edge of the left domain, right edge of the right
  domain) for cable exit, without divorcing it from the driver it serves.

The result is a wider, less-tall **~117 × 82 mm** board (Edison's preferred
aspect; later widened to ~141 × 82 mm when the RS-232 module joined the logic
domain — see the top update block) that `_assert_no_overlap()` keeps DRC-clean.
Crucially, keeping clusters
intact *reduced* the estimated ratsnest (part-centre HPWL ≈1150 → ≈1051 mm)
rather than inflating it — the failure mode of a naive input reorder. The
schematic-sheet layout is unchanged (its spacing doesn't affect connectivity or
routing).

**Placement review (Edison `ANALYSIS`).** The compact board, generator, and both
trios were fed back through an Edison data-analysis pass
([`edison_artifacts/board_placement_review_for_powder_doser.*`](edison_artifacts/board_placement_review_for_powder_doser.answer.md);
runner [`edison_run_board_placement_analysis.py`](edison_run_board_placement_analysis.py))
to sanity-check the layout. It confirmed the compact board is well-sized and that
its **main remaining issue was placement intelligence, not density** — a pure
area shelf-pack mixes power and logic domains and leaves connectors inboard.
Acting on that feedback:

- **Applied — domain/cluster/edge-aware placement.** `_pack_positions()` was
  rewritten from the area shelf-pack into the domain-partitioned, cluster-rigid,
  connector-edge-biased packer described above (review recommendations #1, #3,
  #5, #6). `PLACEMENT_CLUSTERS` / `EDGE_REFS` encode the metadata.
- **Applied — power breakout clearance.** A 0.6 mm `Power` trace plus the old
  0.3 mm clearance (1.2 mm) could not fit between adjacent 0.1″ header pads (the
  copper-to-copper gap is only `PITCH − PAD_SIZE = 0.84 mm`). The `Power` class
  clearance is now held at the board minimum (0.2 mm) so power can break out of
  the headers and neck down through them — the routing behaviour the
  DeepPCB/Quilter test is meant to exercise.
- **Future work.** A literal **bottom-edge connector band** was prototyped but
  *lengthened* every driver→connector net (HPWL ≈1402 mm), so connectors are kept
  in their clusters and only biased outward; full edge pinning, rigid decoupling-cap
  pre-placement, four M3 mounting-hole keep-outs, the barrel jack's real
  oversized/slotted pads, and a board-level GND pour need per-part placement /
  footprint overrides and a human-in-the-loop pass, and are deliberately left for
  a later revision.


**File-format version (KiCad 7+).** The board is written with the **KiCad 7.0
`.kicad_pcb` format version `20221018`** (board and every embedded footprint),
matching the schematic's KiCad 7 `20230121` version. This addresses the Quilter
upload error reported on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4665359897)
— *"Version 20211014 not supported. Quilter supports KiCAD versions 7.0 and
newer"* — which came from `kiutils`' default `create_new` stamp of the KiCad 6
version `20211014`. The builder now overrides it via `KICAD7_PCB_VERSION` so the
upload trio is accepted.

The **schematic** (`test_module_starter.kicad_sch`) is verified the way KiCad's
own connectivity engine sees it: the build exports its netlist with
`kicad-cli sch export netlist` and asserts every one of the **75 connected pins
lands on its intended net across all 22 named nets**, with no stray
`unconnected-(…)` entries (`validate_schematic_netlist()`; runs automatically
when `kicad-cli` is on `PATH`, skipped gracefully otherwise). Because both the
board and the schematic are emitted from the same `NETLIST` / `PINOUTS` tables —
pins numbered identically (left column then right) and placed on the same 0.1″
pitch — the schematic netlist matches the board's pad nets exactly. UUIDs are
derived with a stable `sha256` hash, so re-running is byte-for-byte reproducible.

A KiCad GUI/`kicad-cli` DRC pass is still recommended before routing (it
couldn't be run in this headless sandbox), but the board opens as a
fully-netted, outlined, unrouted board — the precise hand-off artifact Quilter
and DeepPCB ask for.

## Pin-count verification

@lbwinters flagged on PR
[#76](https://github.com/vertical-cloud-lab/powder-doser/pull/76#issuecomment-4695926604)
that the **Pi Pico W symbol had too few pins** (12 + 3 = 15 instead of 40). PR
#61's `SYMBOL_PINS` were simplified placeholders that listed only the *netted*
pins, so several parts were physically incomplete. Every part was re-audited
one-by-one against the manufacturer pinout and the `hardware/vendor-files/`
datasheets / Eagle files (PR #25), and the `PINOUTS` table (and a couple of
`NETLIST` ground entries) corrected so each footprint now carries **one pad per
real physical pin**, with pins that share a name (e.g. the Pico's eight GND) all
tied to the same net on both the board and the schematic:

| Part (source) | Real pins | Was | Now | Change |
| --- | --- | --- | --- | --- |
| `Barrel_Jack_12V` — Adafruit #373 2.1 mm jack | 3 | 2 | **3** | added the switch lug (`SW`, left no-connect) |
| `D24V22F5_Buck` — Pololu #2858 | 4 | 5 | **4** | merged the placeholder `GND_IN`/`GND_OUT` into the regulator's single `GND` pin |
| `Cap_Polar` — radial electrolytic | 2 | 2 | 2 | — |
| `Shunt_Regulator` — Pololu #3776 | 4 | 2 | **4** | added the board's duplicate access holes (`A`/`+` on one node, `B`/`−` on the other) |
| `Pi_Pico_W` — Raspberry Pi Pico W | 40 | 15 | **40** | rebuilt to the full official 2×20 castellated pinout (GP0–GP28, RUN, ADC_VREF, 3V3_EN, VBUS, VSYS, 8×GND, …); unused GPIO are no-connect |
| `DRV2605L_Breakout` — Adafruit #2305 | 8 | 8 | 8 | — (VIN, GND, SDA, SCL, EN, IN/TRIG, OUT+, OUT−) |
| `DRV8871_Breakout` — Adafruit #3190 | 7 | 6 | **7** | added the logic-header `GND` (power/motor terminal `VM`,`GND`,`OUT1`,`OUT2` + logic `IN1`,`IN2`,`GND`) |
| `Tic_T500` — Pololu #3135 | 14 | 11 | **14** | added the missing control pins `RC`, logic `GND`, and `5V` out |
| `Stepper_4wire` — NEMA-11 bipolar | 4 | 4 | 4 | — |
| `Servo_3pin` — hobby servo | 3 | 3 | 3 | — |
| `ERM_Motor` — Adafruit #1201 | 2 | 2 | 2 | — |
| `Solenoid` — Adafruit #412 | 2 | 2 | 2 | — |
| `Waveshare_2CH_RS232` — Waveshare Pico-2CH-RS232 | 4 | — | **4** | new part `U6`: the module's channel-0 4-pin TTL header (`VCC`→`+3V3`, `GND`, `TXD`, `RXD`), per PR #100 — only that header reaches this board; the module carries its own DB9 to the scale |

The board therefore grew from **66 → 97 pads** (69 net-assigned across 20 nets),
and the Pico W body was re-proportioned to 21 × 51 mm so its long edge runs along
the 40-pin columns. The **RS-232 module** was first added as a 40-pad
Pico-form-factor receptacle (`J2`), then re-modelled per PR #100 as `U6`'s
4-pin TTL header (see the top update block), bringing the board to **101 pads /
75 net-assigned / 22 nets**. `validate_schematic_netlist()` re-confirms all connected pins land on
their intended nets with zero unconnected stragglers, and `_assert_no_overlap()`
keeps the compact placement DRC-clean.

## Uploading it

DeepPCB and Quilter ask for the full KiCad project — board **and** schematic —
so upload the trio together: `test_module_starter.kicad_pcb` +
`test_module_starter.kicad_sch` + `test_module_starter.kicad_pro`.

- **Quilter** (note `16`, manual / web-UI only): open
  [app.quilter.ai](https://app.quilter.ai), start a new project from the trio
  (`.kicad_pcb` + `.kicad_sch` + `.kicad_pro`), and let it place + route. No
  API, so this step is human-in-the-loop.
- **DeepPCB** (note `17`, scriptable API): the `.kicad_pcb` is the upload
  payload for `POST /boards` (with the `.kicad_sch` / `.kicad_pro` for a
  complete project); the provisioned `DEEPPCB_API_KEY`
  ([`deeppcb_api_ping.py`](deeppcb_api_ping.py)) authenticates from this
  sandbox, but a real route is **credit-metered** (free tier = 1 board /
  ~30 min), so the actual `POST /boards` + `PATCH /boards/{id}/confirm` calls
  are left for a deliberate, budgeted run rather than every CI commit.

## Quilter review fixes (PR #76 comment 4723827215)

@lbwinters uploaded the trios to **Quilter.ai** and raised four points. Each was
investigated against the [Quilter documentation](https://docs.quilter.ai) (an
Edison `ANALYSIS` pass over the files + docs is archived at
[`edison_artifacts/quilter_review_for_powder_doser.*`](edison_artifacts/);
runner [`edison_run_quilter_review_analysis.py`](edison_run_quilter_review_analysis.py)).

### 1. "Pin count mismatch between schematics and board" (fixed)

Quilter's *schematic-informed placement* pairs each board footprint with its
schematic symbol; if it can't pair them it falls back and warns *"There are
component mismatches between schematics and board: Pin count mismatch detected."*
Every actual pin/pad count already matched perfectly (verified part-by-part with
`kiutils`), so the warning was **not** a literal count difference. The real cause:
the generated `.kicad_pcb` footprints carried **no link back to their schematic
symbols** — no `(path "/<symbol-uuid>")` and no `(attr …)` (the fields KiCad's
*Update PCB from Schematic* normally writes). With nothing to pair on, Quilter
compared by reference/heuristics and reported a mismatch.

**Fix.** A shared `_symbol_uuid(lib_id, ref, x, y)` helper now generates each
symbol-instance UUID once; the schematic writer (`_sym_instance`) and the board
writer (`build_board`) both use it, so every footprint emits
`(path "/<symbol-uuid>")` + `(attr through_hole)` (all parts are through-hole)
linking it to *its* schematic symbol. The placed/unplaced schematics were also
made to name *their own* project (`test_module_starter` / `test_module_unplaced`)
so each trio is internally consistent. The build verifies a 1:1 footprint↔symbol
UUID bijection (15 ↔ 15) and stays byte-for-byte reproducible.

### 2. Right-sized board for auto-placement (fixed)

Quilter places onto whatever outline is uploaded and **can't resize the outline
itself**, so the unplaced board's outline matters. It previously mirrored the
wider *placed* floorplan (≈141 × 82 mm, only ~37–44 % utilised — the "wasted
space" the review flagged). A utilisation analysis (component courtyards ≈
5060 mm² / bodies ≈ 4220 mm²; tallest parts the two 52 mm Pico/RS-232 modules,
so the board must be ≥ ~63 mm in one dimension) puts the sensible band for
through-hole mixed-signal auto-place/route at ~35–55 % utilisation. The unplaced
outline is now an independent **100 × 100 mm** square (`UNPLACED_OUTLINE_MM`):
~51 % courtyard / ~42 % body utilisation, comfortably fits the 52 mm modules with
`EDGE_MARGIN` to spare, leaves copper room for the 2-layer routes, and lands on
JLCPCB's 100 × 100 mm prototype price break. The placed variant is left at its
domain-packed size (it is *our* placement, not a Quilter auto-place target).

### 3. Stackup & the "no ground layer" warning (recommendation)

Quilter asks for a stackup and warns *"No ground layer is defined in this
stackup. Signal integrity may be reduced without a dedicated ground plane"* for a
2-layer board, because a 2-layer stack has no dedicated internal ground plane.
Quilter only auto-detects power/ground layers whose **names** are `gnd`/`ground`
and `pwr`/`power`.

- **JLCPCB 2-layer 6 mil/6 mil (current choice) — adequate for a prototype.**
  The 6 mil (0.152 mm) min trace/space easily clears this design's net classes
  (0.25 mm track / 0.2 mm clearance, 0.6 mm power). To answer the warning on a
  2-layer board, **flood the bottom copper with a `GND` pour** so signals have a
  ground reference (name it `GND` so Quilter detects it). This is acceptable here
  because every net is low-speed: I²C ≤ 400 kHz, UART/RS-232, and essentially-DC
  stepper/solenoid/servo drive — no controlled-impedance or high-edge-rate nets.
- **Recommended optimum: JLCPCB 4-layer (e.g. `JLC04161H-7628`),
  Signal / GND / Power / Signal.** A dedicated internal **ground plane on L2**
  directly resolves the warning and gives a clean, uninterrupted return path
  under the noisy +12 V switching buck and the DRV8871/Tic motor currents that
  sit next to the quieter 3V3/I²C and load-cell-interface nets — exactly the
  mixed-signal partitioning this board needs. JLCPCB 4-layer is only a few
  dollars more for prototypes. Name L2 `GND` and L3 `PWR` for Quilter detection.

**Recommendation:** use the **4-layer Sig/GND/Pwr/Sig** stackup for the real run
(best signal integrity for a motor + load-cell mixed-signal board); if cost or
simplicity forces 2-layer, keep JLCPCB 2-layer 6/6 **plus a bottom-side `GND`
pour**. Either way the warning is addressed by providing a named ground.

### 4. Stackup datasheet verification (ready)

After a stackup is chosen, Quilter presents a datasheet of values to confirm
before a run. We're ready to verify it when @lbwinters sends it; the values to
check against this design are: copper weight (1 oz default), finished thickness
(1.6 mm), min trace/space (must be ≤ our 0.25 mm track / 0.2 mm clearance — both
clear 6 mil), min drill/annular ring (vs our 1.0 mm THT drills / 1.7 mm pads),
the layer→`GND`/`PWR` name mapping (point 3), and — for 4-layer — the dielectric
heights (e.g. `JLC04161H-7628`). Send the datasheet and we'll check each row.

## Honest limitations

- **Real land patterns, generic where no exact part exists.** Pads are now
  copied from genuine KiCad 7 library footprints (vendored under
  [`starter_board/kicad_footprints/`](starter_board/kicad_footprints/)) rather
  than synthesized, and body **outlines, courtyards, and 3-D models** are the
  real vendor parts (PR #25 `hardware/vendor-files/` Eagle `.brd` outlines +
  STEP envelopes + spec sheets). The Pololu/Adafruit *carriers* (D24V22F5,
  shunt regulator, Tic T500, DRV2605L/DRV8871, Pico W) are represented by the
  genuine 0.1″ **pin-header land pattern they plug into**, with the carrier's
  real body overlaid — which is the correct footprint for a through-hole module
  on a 0.1″ grid. Before fabrication, a designer may still prefer a single
  combined module footprint (e.g. `Module:RPi_Pico_SMD_TH`, or SnapEDA parts)
  in place of the two header columns; the router output is a **layout study**,
  not a manufacturing release.
- **3-D models resolve after PR #25 merges.** The `model` paths point into
  `hardware/vendor-files/` (PR #25); until that branch lands they won't render,
  which is harmless (KiCad just skips a missing model).
- **Mixed-signal partitioning still wants a human pass.** The note `20`
  caveat stands: keeping SR1's back-EMF clamp tight to C3 / the Tic T500 VIN,
  and separating the 12 V motor return from logic ground, are constraints an
  autonomous placer won't prioritize without explicit grouping — worth a review
  pass after Quilter/DeepPCB returns candidates.

## Reproducing

```bash
pip install kiutils            # pure-Python; cairosvg optional for the PNG
python paper/background/starter_board/build_starter_board.py
```

`kicad-cli` (KiCad ≥ 7) is optional; when it is absent the script falls back to
a built-in, dependency-free SVG renderer (bodies, pads, ratsnest, outline), and
`cairosvg` (if installed) converts that to PNG. The `.kicad_pcb`, `.kicad_pro`,
and summary are produced regardless. The real library land patterns are read
from the vendored
[`starter_board/kicad_footprints/`](starter_board/kicad_footprints/) directory
(copied verbatim from the upstream `kicad-footprints` library, so no KiCad
install is required); if a system KiCad is present, its
`/usr/share/kicad/footprints` is used as a fallback library path.
