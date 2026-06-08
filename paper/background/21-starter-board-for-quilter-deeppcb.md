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

![Generated starter board (footprints + nets + Edge.Cuts outline, unrouted)](starter_board/test_module_starter.png)

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
| [`test_module_starter.kicad_pcb`](starter_board/test_module_starter.kicad_pcb) | The starter board: 14 footprints, 66 pads (59 net-assigned), a 145 × 109 mm Edge.Cuts outline. **This is the file you upload.** |
| [`test_module_starter.kicad_pro`](starter_board/test_module_starter.kicad_pro) | Project / DRC rules: `Default` (0.25 mm track / 0.2 mm clearance) and a wider `Power` net class (0.6 mm track / 0.3 mm clearance) assigned to `+12V`, `+5V`, `+3V3`, `GND`. |
| [`test_module_starter.svg`](starter_board/test_module_starter.svg) / `.png` | Board-only preview (rendered by `kicad-cli` + `cairosvg` when present). |
| [`starter_board_summary.json`](starter_board/starter_board_summary.json) | Machine-readable BOM + net summary for review. |

## How it was built (note `20` Rank 1)

1. **Netlist provenance.** The `NETLIST` and `PINOUTS` tables in the script are
   transcribed verbatim from the `PLACEMENTS` / `SYMBOL_PINS` structures in PR
   #61's `hardware/test-module/kicad/generate.py` (commit `147e505`), so the
   component set, pin names, and net connectivity match the schematic exactly.
   Keeping them inline makes the build reproducible on *this* branch without
   needing the PR #61 hardware tree present.
2. **Proxy footprints.** Because none of the breakouts (Pi Pico W, DRV2605L,
   DRV8871, Tic T500, Pololu buck / shunt regulator, servo, solenoid,
   NEMA-11) have stock KiCad footprints, each is rendered as a through-hole
   **0.1″ pin-header proxy** — one pad per schematic pin, pin 1 marked
   rectangular, pads on `*.Cu` + `*.Mask` with a silk courtyard. Functionally
   correct for routing; the silk outline is a generic header rather than the
   exact module body (note `20` §4 Rank 1).
3. **Net assignment.** A board net table is built and every connected pad is
   tagged with its net, so the board carries the full 20-net ratsnest.
4. **Floorplan + outline.** The schematic-sheet anchor coordinates are reused
   (compacted ×0.5) as a rough, non-overlapping starting placement; a
   `_assert_no_overlap()` courtyard check guarantees the result stays
   DRC-clean, and an Edge.Cuts rectangle is drawn around all pads + 5 mm.
   Absolute placement is unimportant — Quilter/DeepPCB re-place everything.

## Verification (KiCad 7)

Loaded in KiCad 7.0.11 (`pcbnew`) and run through `WriteDRCReport`:

- **0 footprint (geometry/clearance/courtyard) errors** — no overlaps.
- **39 `unconnected_items`** — these are exactly the ratsnest connections to be
  routed, i.e. the *intended* input state of an unrouted starter board, not
  errors.
- **14 `lib_footprint_issues` warnings** — only "library `powder_doser_proxies`
  not in the global table," which is expected and harmless because the
  footprints are embedded in the board file (nothing to resolve on upload).

So the board opens cleanly in KiCad and presents a fully-netted, outlined,
unrouted board — the precise hand-off artifact Quilter and DeepPCB ask for.

## Uploading it

- **Quilter** (note `16`, manual / web-UI only): open
  [app.quilter.ai](https://app.quilter.ai), start a new project from the
  `.kicad_pcb` (+ `.kicad_pro` for the net-class rules), and let it place +
  route. No API, so this step is human-in-the-loop.
- **DeepPCB** (note `17`, scriptable API): the same `.kicad_pcb` is the upload
  payload for `POST /boards`; the provisioned `DEEPPCB_API_KEY`
  ([`deeppcb_api_ping.py`](deeppcb_api_ping.py)) authenticates from this
  sandbox, but a real route is **credit-metered** (free tier = 1 board /
  ~30 min), so the actual `POST /boards` + `PATCH /boards/{id}/confirm` calls
  are left for a deliberate, budgeted run rather than every CI commit.

## Honest limitations (carried forward from note `20`)

- **Proxy footprints, not real parts.** Pad *counts and nets* are correct, but
  the physical pad geometry / module outlines are generic 0.1″ headers. Before
  fabrication these must be swapped for the real Pico W / Adafruit / Pololu
  footprints (e.g. `Module:RPi_Pico_SMD_TH`, SnapEDA/Adafruit libraries). The
  router output is therefore a **layout study**, not a manufacturing release.
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

`kicad-cli` (KiCad ≥ 7) is optional and only used to render the SVG/PNG
preview; the `.kicad_pcb`, `.kicad_pro`, and summary are produced without it.
