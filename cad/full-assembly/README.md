# Full assembly, current design

The annotated overview render from [#165](https://github.com/vertical-cloud-lab/powder-doser/issues/165)
(manuscript Fig. 1a) was made in June from the AI-era parts. The rig has
changed since then. This package rebuilds that render with the parts that
changed swapped in, from **exactly the same camera**, so the two images
line up.

![Current design, annotated](renders/assembly_iso_az090_annotated_white.png)

| June render vs. current design (same camera) |
|---|
| ![](renders/compare_june_vs_current.png) |

| New assembly from the outlet end vs. the rig on 11 Sep 2026 ([#156](https://github.com/vertical-cloud-lab/powder-doser/issues/156)) |
|---|
| ![](renders/compare_front_vs_photo.png) |

## What is in the assembly

This table is the Fig. 1a render. Every part's source is also in
[`assembly/parts_manifest.json`](assembly/parts_manifest.json). The
[Onshape assembly](#onshape-assembly-all-current-files) below uses the current
Fusion file for every printed part.

| Part | Status | Source |
|---|---|---|
| Auger (44T module-1 gear on the tube, flight on the outlet end only, Ø3 outlet) | **current file** | Sam's Fusion 360 `Threaded Auger Final.stl`, from the [#117 zip](https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-5004533979) ([video](https://youtu.be/sKrvGBTUc8U)) |
| Screw-on cap | **current file** | Sam's Fusion 360 `Cap Final.stl`, same zip |
| Stepper pinion, 20T module 1 | regenerated from spec | Fusion redesign spec ([video](https://youtu.be/EO9qnYssKRQ)); meshes the 44T gear at the same 32 mm centre distance as June |
| 12 V push-pull solenoid (TAU0730TM-14 label) | approximated | sized from rig photos against the 25 mm tube |
| Tap collar (clamp ring + solenoid cradle at 40° from vertical) | approximated | modelled from the 11 Sep photo; the real file is now in `components/fusion-step/` (Onshape assembly below) |
| Tap-collar hard-stop plate | June stand-in | PR #51 |
| Auger brackets (×2) | June stand-in | PR #47 split collars; the rig uses the Fusion flexible brackets ([video](https://youtu.be/Ldaato5X1x4)) and has no bracket in front of the tap collar |
| Mounting plate with the two 28T tilt gears | June stand-in | PR #66 CadQuery; Fusion redesign ([video](https://youtu.be/v8my5C7718w)) now in `components/fusion-step/` |
| Baseplate with servo mounts | June stand-in | PR #66 CadQuery; Fusion redesign ([video](https://youtu.be/zOh_KagOwOU)) now in `components/fusion-step/` |
| Servo pinions (×2, 14T) | June stand-in | PR #66; Fusion redesign ([video](https://youtu.be/X1pHIL-XZiQ)) now in `components/fusion-step/` |
| Hinge pins, NEMA-11 and MG996R bodies | June | simple solids |

The Fusion auger drops into the June layout unchanged. Its gear sits
83.33 mm (L/3) from the outlet, which is where June put its gear band, and
20T + 44T at module 1 gives the June 32 mm centre distance.

The "Vibration" label is gone. There is no working vibration motor on the
rig, and the manuscript no longer claims vibration assistance. Use
`python3 annotate.py --vibration` to put it back.

The colours are the June palette rather than the rig's blue/white, so the
figure keeps its colour code (gold auger, purple tapping, grey tilt).

## Onshape assembly (all current files)

**[Powder doser - full assembly (current design)](https://cad.onshape.com/documents/ae9f107d3972fc9d390e541f/w/b4151a24f733d0ffc48da6d2/e/dfbe0ae499cd860a85aa8da6)**,
owned by the Vertical Cloud Lab Onshape company. One document holds a Part
Studio per file and the *Powder doser assembly* tab. This is the full
current design. The Fig. 1a render above still uses the June stand-ins
listed in the table.

| Onshape, isometric | Onshape, from the outlet end |
|---|---|
| ![](renders/onshape_assembly_iso.png) | ![](renders/onshape_assembly_front.png) |

| Part | Source |
|---|---|
| Baseplate, mounting plate (with both 28T tilt gears), auger bracket (x2), tap collar, auger, auger cap, stepper pinion (20T), servo pinion (14T, x2) | lab Fusion 360 account, share links in [PR #170](https://github.com/vertical-cloud-lab/powder-doser/pull/170), exported to STEP in `components/fusion-step/` |
| Tap-collar base (hard-stop plate) | AI version still in use: `mount_plate.step` from PR #51 (`cad/mounting-plate-assembly/imported-parts/tap-collar/` @ `eaf528a`), in `components/ai-step/` |
| NEMA 11 11HS18-0674S, MG996R (x2), Adafruit 412 solenoid | simplified models from the datasheet dimensions, `onshape/purchased_parts.py` -> `components/purchased/` |

The Fusion links were exported through the share page's own Download API,
with `onshape/fetch_fusion_shares.py` run on the rig's Raspberry Pi. The
links must keep *Allow download* switched on for this to work.
`components/fusion-step/shares_stp.json` records the Fusion version of
each export.

### How the parts are placed

Every part keeps the frame its STEP was exported in.
[`onshape/layout.py`](onshape/layout.py) maps each one into the baseplate's
frame (Z up, hinge along X, outlet towards -Y, stepper on -X). The numbers
come from the STEP geometry, not from eyeballing:

- Mounting plate: its knuckles sit 0.3 mm inside the baseplate towers and
  its 28T gears 0.6 mm outside them. The floor has M3 rows 48 mm apart
  across the tube. The brackets and the tap-collar base stand on the rows at
  124 / 58.3 mm (brackets) and 42.3 mm (base) behind the hinge. Their bores
  are 29.25 mm up, so the auger axis is level with the hinge.
- Stepper: the NEMA 11 pilot hole is 32 mm from the auger axis, which is
  (20 + 44) / 2 at module 1. The motor sits behind its plate and the 20T
  pinion is in front of it, as on the 11 Sep photo. The pinion's hub sits
  0.5 mm off the plate, and the auger's 44T gear is centred on the pinion
  teeth, which puts the outlet 11.6 mm in front of the hinge axis. The
  pinion is phased by half a tooth (no tooth overlap).
- Servos: the baseplate posts' holes form a 48.04 x 9.04 mm MG996R pattern.
  The spline sits straight under the hinge, 27.26 mm = 1.298 x (28 + 14) / 2
  away, so the 14T pinions mesh the 28T gears. The flange is on the posts'
  inner faces.
- Tap collar: on the auger over its base, with the clamp ears over the
  base's hard-stop bump. The solenoid plate faces the cap, so the solenoid
  hangs over the collar's Ø6.9 plunger hole. The roll about the auger is 0
  (plunger vertical). On the rig the collar has turned about 40° towards
  +X; see `COLLAR_ROLL_DEG`.

`python3 layout.py` writes `placements.json` and runs a pairwise
interference check. The only overlaps left are expected ones: the cap
thread on the auger thread (the two threads are modelled overlapping),
1.1 mm³ at the NEMA pilot, and 0.35 mm per side where the 40.7 mm MG996R
case meets the posts. The posts are 40.0 mm apart, so either the real case
is a bit shorter at that height or it is a press fit.

The parts are placed with absolute transforms, not mates, at tilt 0. In
Onshape, *Fix* the baseplate and add a revolute mate on the hinge if you
want to drive the tilt.

### Re-running

```bash
pip install cadquery requests numpy
cd cad/full-assembly/onshape
python3 purchased_parts.py      # NEMA 11 / MG996R / Adafruit 412 models
python3 layout.py               # placements.json + interference check
python3 onshape_build.py        # sync the Onshape document (needs ONSHAPE_ACCESS_KEY/SECRET_KEY)
```

`onshape_build.py` is idempotent against `onshape_document.json`. It
re-imports a STEP only if its contents changed. It resets the transforms
of the instances it created to `layout.py` and leaves hand-added instances
alone. The API key has no delete scope, so a superseded Part Studio is
renamed "(superseded, safe to delete)" instead of being removed. Three tabs
can be deleted by hand: *Adafruit 412 solenoid (superseded, ...)*,
*Baseplate (stray upload, ...)* and the empty *Part Studio 1*.

## Running it

```bash
pip install cadquery vtk trimesh pillow
cd cad/full-assembly
xvfb-run -a python3 build.py --hires   # renders + assembly exports (about 1 min)
python3 annotate.py                    # annotated 970x663 render (+ _white copy)
python3 annotate.py --src assembly_iso_az090_hires.png --out assembly_iso_az090_hires_annotated.png
python3 compare.py                     # the two comparison panels
```

The camera is pinned to the June az = 90° view after its `ResetCamera()`.
With every part set back to its June version, the June script and this one
produce the same image. The annotation uses Carlito (metric-compatible with
Calibri, `apt install fonts-crosextra-carlito`) and falls back to Liberation
Sans. The annotated PNGs keep the transparent background the June figure
had; the `_white` copies are for viewing on GitHub.

| Output | What it is |
|---|---|
| `renders/assembly_iso_az090.png` | the reference view, tilt 0 |
| `renders/assembly_iso_az090_annotated.png` | labelled, transparent background (970×663) |
| `renders/assembly_iso_az090_hires_annotated.png` | labelled, print resolution (3881×2650) |
| `renders/assembly_iso_az090_tilt22p5.png`, `_tilt45.png` | same direction at 22.5° and 45° tube tilt |
| `renders/assembly_front_from_outlet.png` | view from the outlet end, to compare with photos |
| `assembly/full_assembly.glb` / `.stl` | the whole assembly in the June frame (mm), per-part colours in the GLB |
| `components/generated/*.stl` | the regenerated pinion and the approximated collar and solenoid |
| `components/fusion-step/*.step` | the eight lab Fusion 360 designs, exported 1 Oct 2026 |
| `renders/onshape_assembly_{iso,front,top,right}.png` | shaded views of the Onshape assembly, rendered by Onshape |

`components/june/cad_model.py` and the June STLs are vendored from
`cad/mounting-plate-assembly/` on `copilot/add-servo-angle-control` @ `97521d2`,
which isn't on `main`.
