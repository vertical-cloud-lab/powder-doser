# Vendored KiCad library footprints

These `.kicad_mod` files are copied **verbatim** from the official KiCad
footprint libraries (`kicad-footprints`, v7.0.11) so that
`build_starter_board.py` can assemble the starter board from **real,
manufacturer-grade KiCad land patterns** instead of synthesized 0.1"
placeholders — and so the build stays self-contained and byte-for-byte
reproducible without a system KiCad install.

Only the handful of footprints actually used by the generator are vendored:

| File | Used for |
| --- | --- |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x02_P2.54mm_Vertical` | 2-pin connectors (ERM, solenoid), shunt-reg / stepper pin pairs, DRV2605L motor output |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x03_P2.54mm_Vertical` | Servo header, DRV8871 logic header |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x04_P2.54mm_Vertical` | Pololu D24V22F5 header, DRV8871 power/motor header |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x06_P2.54mm_Vertical` | DRV2605L control header, Tic T500 power/motor row |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x08_P2.54mm_Vertical` | Tic T500 control row |
| `Connector_PinHeader_2.54mm.pretty/PinHeader_1x20_P2.54mm_Vertical` | Raspberry Pi Pico W (one per castellated edge) |
| `Capacitor_THT.pretty/CP_Radial_D8.0mm_P3.50mm` | Electrolytic decoupling caps C1/C2/C3 |
| `Connector_BarrelJack.pretty/BarrelJack_Horizontal` | 2.1 mm DC barrel jack (Adafruit #373) |

## Provenance & licence

* Source: <https://gitlab.com/kicad/libraries/kicad-footprints> (Debian package
  `kicad-footprints` 7.0.11-1, `Homepage: https://kicad.github.io/footprints`).
* Licence: **CC-BY-SA-4.0 with the KiCad library exception**. The exception
  waives the share-alike requirement (article 3) for electronic designs and any
  generated files that use the library data, so the generated
  `test_module_*.kicad_pcb` boards are unencumbered. The `.kicad_mod` files
  themselves remain CC-BY-SA-4.0, © KiCad Community / contributors.
