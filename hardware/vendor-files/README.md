# Vendor CAD / PCB / design files

Vendor-published mechanical (CAD) and electrical (PCB) design files for
the parts in the BOM at
[`../vibration-motor-and-solenoid.md`](../vibration-motor-and-solenoid.md).
Each part has its own subdirectory with the upstream files and the
license shipped alongside them.

When a vendor doesn't publish design files (or only ships them behind a
form / login), the entry below has a **manual-download link** instead so
you can grab it yourself.

## Index (BOM order)

| BOM | Part | Vendor | Local files | Manual link(s) |
|-----|------|--------|-------------|----------------|
| 1 | DRV2605L Haptic Motor Controller breakout | Adafruit #2305 | [`adafruit-2305-drv2605l/`](adafruit-2305-drv2605l/) — `.f3d`/`.step`/`.stl` mechanical (MIT) + Eagle `.brd`/`.sch` PCB (CC BY-SA 3.0) | — |
| 2 | Vibrating Mini Motor Disc — ERM coin (10 mm × 2.7 mm, 3 V) | Adafruit #1201 | _(not in upstream `Adafruit_CAD_Parts`; commodity ERM, no published CAD)_ | [Datasheet PDF on product page](https://www.adafruit.com/product/1201) |
| 3 | LRA (linear resonant actuator) — discontinued #1631 | Precision Microdrives | _(category page only — pick a specific LRA before fetching its STEP)_ | [precisionmicrodrives.com/lras](https://www.precisionmicrodrives.com/product-category/lras) |
| 4 | JF-0530B 5 V mini push–pull solenoid | Adafruit #412 | _(commodity solenoid; no upstream CAD published)_ | [Mechanical drawing on product page](https://www.adafruit.com/product/412) |
| 5 | DRV8871 DC Motor Driver Breakout | Adafruit #3190 | [`adafruit-3190-drv8871/`](adafruit-3190-drv8871/) — `.f3d`/`.step`/`.stl` mechanical (MIT) + Eagle `.brd`/`.sch` PCB (CC BY-SA 3.0) | — |
| 6 | Perma-Proto Bonnet Mini Kit for Pi | Adafruit #2310 | [`adafruit-2310-perma-proto-bonnet/`](adafruit-2310-perma-proto-bonnet/) — Eagle `.brd`/`.sch` PCB (CC BY-SA 3.0). Mechanical CAD not in upstream `Adafruit_CAD_Parts`. | [Product page](https://www.adafruit.com/product/2310) |
| 8 | 2.1 mm DC barrel-jack breakout | Adafruit #373 | _(commodity barrel jack; no upstream CAD)_ | [Product page](https://www.adafruit.com/product/373) |
| 10 | NEMA 11 bipolar stepper, 11HS18-0674S | StepperOnline | _(StepperOnline blocks direct curl; download manually from product page)_ | [Product page → "3D Models" / "Drawing" tab](https://www.omc-stepperonline.com/nema-11-bipolar-1-8deg-10ncm-14-16oz-in-0-67a-28x28x45mm-4-wires-11hs18-0674s) |
| 11 | Tic T500 USB Multi-Interface Stepper Motor Controller | Pololu #3135 | [`pololu-3135-tic-t500/dimensions/tic-t500-drill-guide.pdf`](pololu-3135-tic-t500/dimensions/tic-t500-drill-guide.pdf) | Full Eagle / 3D pack on the [resources tab](https://www.pololu.com/product/3135/resources) |
| 11-alt | DRV8825 Stepper Motor Driver Carrier, High Current | Pololu #2133 | [`pololu-2133-drv8825/dimensions/drv8825-dimensions.pdf`](pololu-2133-drv8825/dimensions/drv8825-dimensions.pdf) | [Product page → "Resources"](https://www.pololu.com/product/2133/resources) |
| 12 | 5 mm ↔ 5 mm aluminum flexible shaft coupler ST-FC01 | StepperOnline | _(StepperOnline blocks direct curl)_ | [Product page → "Drawing" tab](https://www.omc-stepperonline.com/5mm-5mm-flexible-shaft-coupling-18x25mm-cnc-stepper-motor-shaft-coupler-st-fc01) |
| 13 | 12 V / 5 A switching power supply | Adafruit #352 | _(generic wall-wart; no published CAD)_ | [Product page](https://www.adafruit.com/product/352) |
| 15 | D24V22F5 5 V / 2.5 A step-down regulator | Pololu #2858 | [`pololu-2858-d24v22f5/dimensions/d24v22f5-drill-guide.dxf`](pololu-2858-d24v22f5/dimensions/d24v22f5-drill-guide.dxf) | [Product page → "Resources"](https://www.pololu.com/product/2858/resources) |
| 16 | Standard-size High-Torque Metal-Gear digital servo (HD-1810MG) | Adafruit #1142 | _(not in upstream `Adafruit_CAD_Parts`)_ | [Product page](https://www.adafruit.com/product/1142) — see also the closely-related Adafruit [#1143 STEP/STL in `Adafruit_CAD_Parts`](https://github.com/adafruit/Adafruit_CAD_Parts/tree/master/1143%20Micro%20Servo%20-%20High%20Torque%20Metal%20Gear) for envelope reference |
| 16-alt | SG-92R micro-servo | Adafruit #169 | _(not in upstream `Adafruit_CAD_Parts`)_ | [Product page](https://www.adafruit.com/product/169) — Adafruit [#2201 sub-micro STEP](https://github.com/adafruit/Adafruit_CAD_Parts/tree/master/2201%20Submicro%20servo) is an OK envelope proxy |
| 17 | M2/M3 servo-mount screws + horn | from #1142 accessory bag | — | (ships with the servo) |
| 18 | 33 V / 9 W shunt regulator | Pololu #3776 | [`pololu-3776-shunt-regulator-9w/dimensions/shunt-regulator-9w-drill-guide.dxf`](pololu-3776-shunt-regulator-9w/dimensions/shunt-regulator-9w-drill-guide.dxf) | [Product page → "Resources"](https://www.pololu.com/product/3776/resources) |
| — | Pi Zero 2 W | Adafruit #5291 / Raspberry Pi | _(see official mechanical drawing)_ | [Raspberry Pi mechanical drawing PDF](https://datasheets.raspberrypi.com/pizero2/pi-zero-2-w-mechanical-drawing.pdf) |
| — | Mini aluminum heat sink (13 × 13 × 3 mm) | Adafruit #3084 | _(commodity finned heat sink; no upstream CAD)_ | [Product page](https://www.adafruit.com/product/3084) |
| — | 16 GB Class-10 microSD with adapter | Adafruit #2693 | _(commodity SD card; no published CAD)_ | [Product page](https://www.adafruit.com/product/2693) |
| — | 5 V / 2.4 A USB power supply (micro-USB) | Adafruit #1995 | _(generic wall-wart; no published CAD)_ | [Product page](https://www.adafruit.com/product/1995) |

## Licenses

* Files copied from [`adafruit/Adafruit_CAD_Parts`](https://github.com/adafruit/Adafruit_CAD_Parts)
  ship under the **MIT License** (`LICENSE` next to each `cad/` folder).
* Files copied from `adafruit/Adafruit-*-PCB` repositories ship under
  **Creative Commons Attribution-ShareAlike 3.0 Unported** (CC BY-SA 3.0,
  `LICENSE.txt` next to each `pcb/` folder).
* Pololu drill-guide PDFs/DXFs are reproduced verbatim from the
  product-page "Resources" tab; redistribution rights follow Pololu's
  posted [terms of use](https://www.pololu.com/about/copyright). They
  are included here as engineering references, not as design originals.

## How these were fetched

```bash
# Adafruit mechanical CAD (sparse-checkout to keep the clone small)
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/adafruit/Adafruit_CAD_Parts.git
cd Adafruit_CAD_Parts
git sparse-checkout set "2305 DRV2605L" "3190 DRV8871 Breakout"

# Adafruit PCB sources
git clone --depth 1 https://github.com/adafruit/Adafruit-DRV2605-PCB.git
git clone --depth 1 https://github.com/adafruit/Adafruit-DRV8871-Breakout-PCB.git
git clone --depth 1 https://github.com/adafruit/Adafruit-Perma-Proto-Bonnet-PCB.git

# Pololu drill guides (direct from product-page Resources tab)
curl -O https://www.pololu.com/file/0J1428/tic-t500-drill-guide.pdf            # #3135
curl -O https://www.pololu.com/file/0J590/drv8825-dimensions.pdf               # #2133
curl -O https://www.pololu.com/file/0J1042/d24v22f5-drill-guide.dxf            # #2858
curl -O https://www.pololu.com/file/0J1814/shunt-regulator-9w-drill-guide.dxf  # #3776
```

To refresh, re-run the snippet above and copy the new files over the
ones in this directory.
