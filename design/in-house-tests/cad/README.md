# Printed parts (CadQuery)

**Status: designed and sliced, not printed.** Each part is a function in [`parts.py`](parts.py). [`build.py`](build.py) writes a STEP and an STL in the use frame, an STL turned onto the bed, and [`out/parts.json`](out/parts.json) (volume, mass when solid, bounding box, bed footprint, watertightness, printer fit). [`assemblies.py`](assemblies.py) places the parts with stand-ins for bought parts and renders each apparatus ([`out/renders/`](out/renders)). Numbers come from [`../SPEC.md`](../SPEC.md).

```bash
python build.py              # all parts (about 3 min)
xvfb-run -a python assemblies.py   # renders
python make_docs.py         # this README and ../ASSEMBLY.md
```

Slicing is in [`../print/`](../print). Mass below is for a solid part; printed mass is lower (see the plates).

## Shared bench parts

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `pan_adapter` | 1 | A1M | 15 % | 18.25 | 86 x 86 x 11 | [STEP](out/step/pan_adapter.step) · [STL](out/stl/pan_adapter.stl) · [bed](out/print/pan_adapter.stl) | sits on the HR-100A pan |
| `riser_40` | 1 | A1M | 25 % | 4.61 | 14 x 14 x 48 | [STEP](out/step/riser_40.step) · [STL](out/stl/riser_40.stl) · [bed](out/print/riser_40.stl) | 40 mm riser |
| `riser_80` | 1 | A1M | 25 % | 8.16 | 14 x 14 x 88 | [STEP](out/step/riser_80.step) · [STL](out/stl/riser_80.stl) · [bed](out/print/riser_80.stl) | 80 mm riser |
| `riser_120` | 1 | A1M | 25 % | 11.7 | 14 x 14 x 128 | [STEP](out/step/riser_120.step) · [STL](out/stl/riser_120.stl) · [bed](out/print/riser_120.stl) | 120 mm riser |
| `riser_160` | 1 | A1M | 25 % | 15.24 | 14 x 14 x 168 | [STEP](out/step/riser_160.step) · [STL](out/stl/riser_160.stl) · [bed](out/print/riser_160.stl) | 160 mm riser |
| `tripod_spider` | 1 | A1M | 25 % | 16.52 | 122 x 108 x 8 | [STEP](out/step/tripod_spider.step) · [STL](out/stl/tripod_spider.stl) · [bed](out/print/tripod_spider.stl) |  |
| `tripod_leg_40` | 3 | A1M | 25 % | 3.14 | 8 x 8 x 40 | [STEP](out/step/tripod_leg_40.step) · [STL](out/stl/tripod_leg_40.stl) · [bed](out/print/tripod_leg_40.stl) | print lying on a face |
| `tripod_leg_80` | 3 | A1M | 25 % | 6.28 | 8 x 8 x 80 | [STEP](out/step/tripod_leg_80.step) · [STL](out/stl/tripod_leg_80.stl) · [bed](out/print/tripod_leg_80.stl) | print lying on a face |
| `tripod_leg_120` | 3 | A1M | 25 % | 9.42 | 8 x 8 x 120 | [STEP](out/step/tripod_leg_120.step) · [STL](out/stl/tripod_leg_120.stl) · [bed](out/print/tripod_leg_120.stl) | print lying on a face |
| `tripod_leg_160` | 3 | A1M | 25 % | 12.55 | 8 x 8 x 160 | [STEP](out/step/tripod_leg_160.step) · [STL](out/stl/tripod_leg_160.stl) · [bed](out/print/tripod_leg_160.stl) | print lying on a face |
| `camera_tower` | 1 | A1M | 25 % | 71.6 | 70 x 50 x 170 | [STEP](out/step/camera_tower.step) · [STL](out/stl/camera_tower.stl) · [bed](out/print/camera_tower.stl) |  |
| `camera_carriage` | 1 | A1M | 25 % | 12.56 | 32 x 23 x 36 | [STEP](out/step/camera_carriage.step) · [STL](out/stl/camera_carriage.stl) · [bed](out/print/camera_carriage.stl) | camera plate on the bed |
| `camera_rod_clamp` | 2 | A1M | 25 % | 20.35 | 32 x 75 x 36 | [STEP](out/step/camera_rod_clamp.step) · [STL](out/stl/camera_rod_clamp.stl) · [bed](out/print/camera_rod_clamp.stl) | one for the camera, one for the backlight; plate on the bed |
| `backlight_foot` | 2 | A1M | 25 % | 30.65 | 60 x 40 x 25 | [STEP](out/step/backlight_foot.step) · [STL](out/stl/backlight_foot.stl) · [bed](out/print/backlight_foot.stl) |  |
| `stage_motor_block` | 1 | A1M | 40 % | 70.92 | 80 x 43 x 20 | [STEP](out/step/stage_motor_block.step) · [STL](out/stl/stage_motor_block.stl) · [bed](out/print/stage_motor_block.stl) | DIY stage, tests 8 and 9 |
| `stage_end_block` | 1 | A1M | 40 % | 77.11 | 80 x 43 x 20 | [STEP](out/step/stage_end_block.step) · [STL](out/stl/stage_end_block.stl) · [bed](out/print/stage_end_block.stl) | DIY stage, tests 8 and 9 |
| `stage_carriage` | 1 | A1M | 40 % | 83.44 | 80 x 37 x 30 | [STEP](out/step/stage_carriage.step) · [STL](out/stl/stage_carriage.stl) · [bed](out/print/stage_carriage.stl) | DIY stage; front face on the bed |

## 1. Heap angle of repose

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `pedestal_d12` | 1 | A1M | 100 % | 1.39 | 13 x 13 x 12 | [STEP](out/step/pedestal_d12.step) · [STL](out/stl/pedestal_d12.stl) · [bed](out/print/pedestal_d12.stl) | top face down for a flat, sharp rim |
| `pedestal_d20` | 1 | A1M | 100 % | 1.81 | 20 x 20 x 12 | [STEP](out/step/pedestal_d20.step) · [STL](out/stl/pedestal_d20.stl) · [bed](out/print/pedestal_d20.stl) | top face down for a flat, sharp rim |
| `pedestal_d30` | 1 | A1M | 100 % | 3.43 | 30 x 30 x 12 | [STEP](out/step/pedestal_d30.step) · [STL](out/stl/pedestal_d30.stl) · [bed](out/print/pedestal_d30.stl) | top face down for a flat, sharp rim |
| `pedestal_d40` | 1 | A1M | 100 % | 5.79 | 40 x 40 x 12 | [STEP](out/step/pedestal_d40.step) · [STL](out/stl/pedestal_d40.stl) · [bed](out/print/pedestal_d40.stl) | top face down for a flat, sharp rim |
| `overflow_tray` | 1 | A1M | 25 % | 27.91 | 120 x 120 x 10 | [STEP](out/step/overflow_tray.step) · [STL](out/stl/overflow_tray.stl) · [bed](out/print/overflow_tray.stl) |  |

## 2. Bulk and tapped density

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `cyl_fill_holder` | 1 | A1M | 25 % | 14.0 | 52 x 52 x 9 | [STEP](out/step/cyl_fill_holder.step) · [STL](out/stl/cyl_fill_holder.stl) · [bed](out/print/cyl_fill_holder.stl) |  |
| `funnel_collar` | 1 | A1M | 25 % | 3.02 | 40 x 40 x 26 | [STEP](out/step/funnel_collar.step) · [STL](out/stl/funnel_collar.stl) · [bed](out/print/funnel_collar.stl) |  |
| `tapper_base` | 1 | A1M | 25 % | 113.9 | 90 x 140 x 46 | [STEP](out/step/tapper_base.step) · [STL](out/stl/tapper_base.stl) · [bed](out/print/tapper_base.stl) |  |
| `tapper_cam` | 1 | A1M | 100 % | 1.84 | 23 x 20 x 8 | [STEP](out/step/tapper_cam.step) · [STL](out/stl/tapper_cam.stl) · [bed](out/print/tapper_cam.stl) |  |
| `tapper_carriage` | 1 | A1M | 40 % | 61.28 | 64 x 53 x 80 | [STEP](out/step/tapper_carriage.step) · [STL](out/stl/tapper_carriage.stl) · [bed](out/print/tapper_carriage.stl) | upright; tree supports under the upper collar |

## 3. Tilting plate

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `tilt_base` | 1 | A1M | 25 % | 145.81 | 100 x 154 x 70 | [STEP](out/step/tilt_base.step) · [STL](out/stl/tilt_base.stl) · [bed](out/print/tilt_base.stl) |  |
| `tilt_plate` | 1 | A1M | 40 % | 55.98 | 87 x 128 x 16 | [STEP](out/step/tilt_plate.step) · [STL](out/stl/tilt_plate.stl) · [bed](out/print/tilt_plate.stl) | flat underside on the bed |
| `tilt_gear_30t` | 1 | A1M | 100 % | 6.44 | 48 x 48 x 4 | [STEP](out/step/tilt_gear_30t.step) · [STL](out/stl/tilt_gear_30t.stl) · [bed](out/print/tilt_gear_30t.stl) |  |
| `tilt_pinion_15t` | 1 | A1M | 100 % | 1.64 | 25 x 25 x 4 | [STEP](out/step/tilt_pinion_15t.step) · [STL](out/stl/tilt_pinion_15t.stl) · [bed](out/print/tilt_pinion_15t.stl) |  |
| `wall_ring` | 3 | A1M | 100 % | 0.73 | 27 x 27 x 6 | [STEP](out/step/wall_ring.step) · [STL](out/stl/wall_ring.stl) · [bed](out/print/wall_ring.stl) | auger settings: 0.20 mm layers, 3 walls |
| `ring_lid` | 2 | A1M | 25 % | 1.42 | 25 x 25 x 6 | [STEP](out/step/ring_lid.step) · [STL](out/stl/ring_lid.stl) · [bed](out/print/ring_lid.stl) |  |
| `strike_frame_1mm` | 1 | A1M | 25 % | 1.25 | 80 x 48 x 1 | [STEP](out/step/strike_frame_1mm.step) · [STL](out/stl/strike_frame_1mm.stl) · [bed](out/print/strike_frame_1mm.stl) |  |
| `strike_frame_2mm` | 1 | A1M | 25 % | 2.5 | 80 x 48 x 2 | [STEP](out/step/strike_frame_2mm.step) · [STL](out/stl/strike_frame_2mm.stl) · [bed](out/print/strike_frame_2mm.stl) |  |
| `strike_frame_3mm` | 1 | A1M | 25 % | 3.75 | 80 x 48 x 3 | [STEP](out/step/strike_frame_3mm.step) · [STL](out/stl/strike_frame_3mm.stl) · [bed](out/print/strike_frame_3mm.stl) |  |
| `strike_frame_5mm` | 1 | A1M | 25 % | 6.25 | 80 x 48 x 5 | [STEP](out/step/strike_frame_5mm.step) · [STL](out/stl/strike_frame_5mm.stl) · [bed](out/print/strike_frame_5mm.stl) |  |

## 4. PSD and shape from images

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `micro_base` | 1 | A1M | 25 % | 114.28 | 150 x 110 x 16 | [STEP](out/step/micro_base.step) · [STL](out/stl/micro_base.stl) · [bed](out/print/micro_base.stl) |  |
| `micro_column` | 1 | A1M | 25 % | 44.45 | 20 x 12 x 160 | [STEP](out/step/micro_column.step) · [STL](out/stl/micro_column.stl) · [bed](out/print/micro_column.stl) |  |
| `micro_carriage` | 1 | A1M | 25 % | 25.44 | 48 x 80 x 30 | [STEP](out/step/micro_carriage.step) · [STL](out/stl/micro_carriage.stl) · [bed](out/print/micro_carriage.stl) |  |
| `sieve_cup` | 1 | A1M | 25 % | 6.48 | 34 x 34 x 25 | [STEP](out/step/sieve_cup.step) · [STL](out/stl/sieve_cup.stl) · [bed](out/print/sieve_cup.stl) |  |
| `sieve_ring` | 1 | A1M | 25 % | 0.83 | 30 x 30 x 4 | [STEP](out/step/sieve_ring.step) · [STL](out/stl/sieve_ring.stl) · [bed](out/print/sieve_ring.stl) |  |

## 5. Orifice cup

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `orifice_cup` | 1 | A1M | 40 % | 12.6 | 40 x 40 x 43 | [STEP](out/step/orifice_cup.step) · [STL](out/stl/orifice_cup.stl) · [bed](out/print/orifice_cup.stl) |  |
| `orifice_disc_1p00` | 1 | A1M | 100 % | 1.92 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_1p00.step) · [STL](out/stl/orifice_disc_1p00.stl) · [bed](out/print/orifice_disc_1p00.stl) | drill/ream to 1.0 mm after printing |
| `orifice_disc_1p50` | 1 | A1M | 100 % | 1.91 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_1p50.step) · [STL](out/stl/orifice_disc_1p50.stl) · [bed](out/print/orifice_disc_1p50.stl) | drill/ream to 1.5 mm after printing |
| `orifice_disc_2p00` | 1 | A1M | 100 % | 1.91 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_2p00.step) · [STL](out/stl/orifice_disc_2p00.stl) · [bed](out/print/orifice_disc_2p00.stl) | drill/ream to 2.0 mm after printing |
| `orifice_disc_2p54` | 1 | A1M | 100 % | 1.9 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_2p54.step) · [STL](out/stl/orifice_disc_2p54.stl) · [bed](out/print/orifice_disc_2p54.stl) | drill/ream to 2.54 mm after printing |
| `orifice_disc_3p00` | 1 | A1M | 100 % | 1.89 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_3p00.step) · [STL](out/stl/orifice_disc_3p00.stl) · [bed](out/print/orifice_disc_3p00.stl) | drill/ream to 3.0 mm after printing |
| `orifice_disc_4p00` | 1 | A1M | 100 % | 1.88 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_4p00.step) · [STL](out/stl/orifice_disc_4p00.stl) · [bed](out/print/orifice_disc_4p00.stl) | drill/ream to 4.0 mm after printing |
| `orifice_disc_5p08` | 1 | A1M | 100 % | 1.85 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_5p08.step) · [STL](out/stl/orifice_disc_5p08.stl) · [bed](out/print/orifice_disc_5p08.stl) | drill/ream to 5.08 mm after printing |
| `orifice_disc_6p00` | 1 | A1M | 100 % | 1.83 | 32 x 32 x 2 | [STEP](out/step/orifice_disc_6p00.step) · [STL](out/stl/orifice_disc_6p00.stl) · [bed](out/print/orifice_disc_6p00.stl) | drill/ream to 6.0 mm after printing |
| `gate_guide` | 1 | A1M | 25 % | 11.72 | 66 x 40 x 6 | [STEP](out/step/gate_guide.step) · [STL](out/stl/gate_guide.stl) · [bed](out/print/gate_guide.stl) |  |
| `gate_slide` | 1 | A1M | 100 % | 1.14 | 60 x 12 x 2 | [STEP](out/step/gate_slide.step) · [STL](out/stl/gate_slide.stl) · [bed](out/print/gate_slide.stl) |  |
| `cup_holder` | 1 | A1M | 25 % | 22.84 | 120 x 66 x 26 | [STEP](out/step/cup_holder.step) · [STL](out/stl/cup_holder.stl) · [bed](out/print/cup_holder.stl) |  |
| `catch_cup` | 1 | A1M | 25 % | 8.26 | 44 x 44 x 31 | [STEP](out/step/catch_cup.step) · [STL](out/stl/catch_cup.stl) · [bed](out/print/catch_cup.stl) |  |

## 6. Humidity chambers

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `hc_slurry_tray` | 6 | A1M | 15 % | 30.44 | 140 x 70 x 15 | [STEP](out/step/hc_slurry_tray.step) · [STL](out/stl/hc_slurry_tray.stl) · [bed](out/print/hc_slurry_tray.stl) |  |
| `hc_shelf` | 6 | A1M | 15 % | 34.54 | 150 x 90 x 32 | [STEP](out/step/hc_shelf.step) · [STL](out/stl/hc_shelf.stl) · [bed](out/print/hc_shelf.stl) |  |
| `hc_sample_dish` | 6 | A1M | 25 % | 9.13 | 92 x 80 x 5 | [STEP](out/step/hc_sample_dish.step) · [STL](out/stl/hc_sample_dish.stl) · [bed](out/print/hc_sample_dish.stl) |  |
| `hc_sensor_clip` | 6 | A1M | 25 % | 2.66 | 30 x 32 x 10 | [STEP](out/step/hc_sensor_clip.step) · [STL](out/stl/hc_sensor_clip.stl) · [bed](out/print/hc_sensor_clip.stl) | on its side: the hook prints as a prism |
| `hc_fan_mount` | 6 | A1M | 25 % | 3.55 | 30 x 39 x 13 | [STEP](out/step/hc_fan_mount.step) · [STL](out/stl/hc_fan_mount.stl) · [bed](out/print/hc_fan_mount.stl) | on its side: the hook prints as a prism |

## 7. Rotating drum

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `drum_shaft` | 1 | H2D | 40 % | 60.11 | 46 x 46 x 245 | [STEP](out/step/drum_shaft.step) · [STL](out/stl/drum_shaft.stl) · [bed](out/print/drum_shaft.stl) | 245 mm tall: H2D left nozzle (0.4), flange down, tree supports under the gear |
| `drum_body` | 1 | A1M | 40 % | 21.73 | 56 x 56 x 21 | [STEP](out/step/drum_body.step) · [STL](out/stl/drum_body.stl) · [bed](out/print/drum_body.stl) |  |
| `drum_body_d25` | 1 | A1M | 40 % | 26.1 | 56 x 56 x 31 | [STEP](out/step/drum_body_d25.step) · [STL](out/stl/drum_body_d25.stl) · [bed](out/print/drum_body_d25.stl) | 25 mm deep variant for cohesive powders (Edison q1) |
| `drum_bezel` | 1 | A1M | 25 % | 2.22 | 56 x 56 x 3 | [STEP](out/step/drum_bezel.step) · [STL](out/stl/drum_bezel.stl) · [bed](out/print/drum_bezel.stl) | window recess up |
| `drum_backdisc` | 2 | A1M | 25 % | 1.69 | 38 x 38 x 1 | [STEP](out/step/drum_backdisc.step) · [STL](out/stl/drum_backdisc.stl) · [bed](out/print/drum_backdisc.stl) | one black, one white |

## 8. Unconfined strength

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `ucs_base` | 1 | A1M | 30 % | 404.88 | 120 x 142 x 170 | [STEP](out/step/ucs_base.step) · [STL](out/stl/ucs_base.stl) · [bed](out/print/ucs_base.stl) |  |
| `ucs_sample_base` | 1 | A1M | 25 % | 7.91 | 44 x 44 x 6 | [STEP](out/step/ucs_sample_base.step) · [STL](out/stl/ucs_sample_base.stl) · [bed](out/print/ucs_sample_base.stl) |  |
| `split_mould_A` | 1 | A1M | 100 % | 9.55 | 30 x 15 x 40 | [STEP](out/step/split_mould_A.step) · [STL](out/stl/split_mould_A.stl) · [bed](out/print/split_mould_A.stl) | standing on its end: smooth bore |
| `split_mould_B` | 1 | A1M | 100 % | 9.55 | 30 x 15 x 40 | [STEP](out/step/split_mould_B.step) · [STL](out/stl/split_mould_B.stl) · [bed](out/print/split_mould_B.stl) | standing on its end: smooth bore |
| `mould_ring` | 2 | A1M | 25 % | 2.56 | 37 x 37 x 6 | [STEP](out/step/mould_ring.step) · [STL](out/stl/mould_ring.stl) · [bed](out/print/mould_ring.stl) |  |
| `ucs_piston` | 1 | A1M | 25 % | 11.54 | 30 x 30 x 58 | [STEP](out/step/ucs_piston.step) · [STL](out/stl/ucs_piston.stl) · [bed](out/print/ucs_piston.stl) |  |
| `ucs_platen` | 1 | A1M | 25 % | 16.74 | 34 x 40 x 40 | [STEP](out/step/ucs_platen.step) · [STL](out/stl/ucs_platen.stl) · [bed](out/print/ucs_platen.stl) | mounting plate on the bed |

## 9. Blade spreading

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `coupon_bed` | 1 | A1M | 40 % | 82.31 | 140 x 50 x 10 | [STEP](out/step/coupon_bed.step) · [STL](out/stl/coupon_bed.stl) · [bed](out/print/coupon_bed.stl) |  |
| `spread_bracket` | 2 | A1M | 25 % | 21.57 | 40 x 40 x 40 | [STEP](out/step/spread_bracket.step) · [STL](out/stl/spread_bracket.stl) · [bed](out/print/spread_bracket.stl) |  |
| `blade_carriage` | 1 | A1M | 40 % | 70.04 | 60 x 116 x 32 | [STEP](out/step/blade_carriage.step) · [STL](out/stl/blade_carriage.stl) · [bed](out/print/blade_carriage.stl) |  |

## 10. Faraday cup

| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |
|---|---|---|---|---|---|---|---|
| `fc_lid` | 1 | A1M | 25 % | 19.65 | 76 x 76 x 15 | [STEP](out/step/fc_lid.step) · [STL](out/stl/fc_lid.stl) · [bed](out/print/fc_lid.stl) |  |
| `fc_insulator_base` | 1 | A1M | 25 % | 13.7 | 69 x 69 x 3 | [STEP](out/step/fc_insulator_base.step) · [STL](out/stl/fc_insulator_base.stl) · [bed](out/print/fc_insulator_base.stl) |  |
| `fc_cradle` | 1 | A1M | 25 % | 51.06 | 84 x 84 x 18 | [STEP](out/step/fc_cradle.step) · [STL](out/stl/fc_cradle.stl) · [bed](out/print/fc_cradle.stl) |  |
| `fc_pcb_box` | 1 | A1M | 25 % | 19.43 | 60 x 50 x 24 | [STEP](out/step/fc_pcb_box.step) · [STL](out/stl/fc_pcb_box.stl) · [bed](out/print/fc_pcb_box.stl) |  |
| `fc_pcb_lid` | 1 | A1M | 25 % | 8.03 | 60 x 50 x 4 | [STEP](out/step/fc_pcb_lid.step) · [STL](out/stl/fc_pcb_lid.stl) · [bed](out/print/fc_pcb_lid.stl) |  |

## Fits and hardware holes

| Interface | Printed size | Fit |
|---|---|---|
| Ø6 steel guide rods in the tapper base | Ø6.00 hole, 15 deep | press fit; printed holes come out about 0.1 mm small |
| Ø6 rods through the tapper carriage | Ø6.50 bores | slide fit; wrap the rods in PTFE tape, or ream to 6.2 |
| Ø5 hinge pin (tilt table) | Ø5.20 in the towers, Ø5.10 in the plate lugs | pin turns in the towers |
| Ø8 shafts in the DIY stage blocks | Ø8.06, 14 deep | press fit |
| LM8UU bearings in the stage carriage | Ø15.10 x 32 | press fit, two per side |
| 608 bearing (stage end block) | Ø22.10 x 7.2 | press fit |
| NEMA 17 pilot / NEMA 11 pilot | Ø22.6 / Ø22.5 | clearance |
| M3 heat-set inserts (drum shaft flange, drum, stage carriage) | Ø4.2 | for standard M3 x 4 inserts |
| M3 clearance | Ø3.2-3.4 |  |
| M2.5 self-tapping (IMU, NEMA 11 face) | Ø2.2-2.7 |  |
| Spigot / socket (risers, pedestals) | Ø9.90 spigot into Ø10.25 socket | slip fit, no glue: pedestals swap |
| Locating pins on the tripod spider | Ø3.0 pins, Ø3.5 blind holes | trays, cradles and the cup holder drop on |
| Coupon pockets | 0.71 deep (tilt plate), 0.91 deep (spreading bed) | 0.91 mm 304 coupons: 0.2 proud / flush |
| Orifice discs | printed 0.2 mm under size | drill or ream to 1.0-6.0 mm; check with pin gauges |

Printed holes shrink by about 0.1-0.2 mm on an A1 mini. Print one `wall_ring` and one `tapper_cam` first and check the fits before committing to a full plate.
