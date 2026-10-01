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

Every part's source is also in [`assembly/parts_manifest.json`](assembly/parts_manifest.json).

| Part | Status | Source |
|---|---|---|
| Auger (44T module-1 gear on the tube, flight on the outlet end only, Ø3 outlet) | **current file** | Sam's Fusion 360 `Threaded Auger Final.stl`, from the [#117 zip](https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-5004533979) ([video](https://youtu.be/sKrvGBTUc8U)) |
| Screw-on cap | **current file** | Sam's Fusion 360 `Cap Final.stl`, same zip |
| Stepper pinion, 20T module 1 | regenerated from spec | Fusion redesign spec ([video](https://youtu.be/EO9qnYssKRQ)); meshes the 44T gear at the same 32 mm centre distance as June |
| 12 V push-pull solenoid (TAU0730TM-14 label) | approximated | sized from rig photos against the 25 mm tube |
| Tap collar (clamp ring + solenoid cradle at 40° from vertical) | approximated | modelled from the 11 Sep photo; the real file is in Fusion/Onshape |
| Tap-collar hard-stop plate | June stand-in | PR #51 |
| Auger brackets (×2) | June stand-in | PR #47 split collars; the rig uses the Fusion flexible brackets ([video](https://youtu.be/Ldaato5X1x4)) and has no bracket in front of the tap collar |
| Mounting plate with the two 28T tilt gears | June stand-in | PR #66 CadQuery; Fusion redesign ([video](https://youtu.be/v8my5C7718w)) not shared |
| Baseplate with servo mounts | June stand-in | PR #66 CadQuery; Fusion redesign ([video](https://youtu.be/zOh_KagOwOU)) not shared |
| Servo pinions (×2, 14T) | June stand-in | PR #66; Fusion redesign ([video](https://youtu.be/X1pHIL-XZiQ)) not shared |
| Hinge pins, NEMA-11 and MG996R bodies | June | simple solids |

The Fusion auger drops into the June layout unchanged. Its gear sits
83.33 mm (L/3) from the outlet, which is where June put its gear band, and
20T + 44T at module 1 gives the June 32 mm centre distance.

The "Vibration" label is gone. There is no working vibration motor on the
rig, and the manuscript no longer claims vibration assistance. Use
`python3 annotate.py --vibration` to put it back.

The colours are the June palette rather than the rig's blue/white, so the
figure keeps its colour code (gold auger, purple tapping, grey tilt).

## Files still needed to finish it

These are only in Fusion 360 or Onshape. An STL or STEP export of each,
attached to #165 or committed under `components/fusion/`, is enough. I'll align
them the same way as the auger and cap.

1. **Tap collar**, the current version with the angled solenoid cradle, plus the hard-stop if it changed
2. **Flexible brackets**, and whatever now supports the tube in front of the tap collar
3. **Mounting plate**, including the tilt gears and the stepper mount
4. **Baseplate** with the servo mounts
5. **Stepper pinion** and **servo pinion** (optional: the regenerated 20T and June 14T are geometrically equivalent)
6. A solenoid model, if you have one (optional)

Fusion: right-click the body → *Save as Mesh* (STL), or *File → Export → STEP*.
A public share link only helps if downloads are enabled. Onshape: right-click
the Part Studio tab → *Export* → STEP/STL. Link-shared Onshape documents can
be thumbnailed anonymously but not exported, so an export or an API key is
needed. The `@claude` workflow doesn't pass `ONSHAPE_ACCESS_KEY` /
`ONSHAPE_SECRET_KEY` today.

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

`components/june/cad_model.py` and the June STLs are vendored from
`cad/mounting-plate-assembly/` on `copilot/add-servo-angle-control` @ `97521d2`,
which isn't on `main`.
