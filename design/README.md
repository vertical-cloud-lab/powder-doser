# Design — channel-sealing caps

This branch addresses issue
**vertical-cloud-lab/powder-doser#36** ("Channel-Sealing Cap Design for
Modular Powder Dosing").

| | |
|---|---|
| [`cap-brainstorming.md`](cap-brainstorming.md) | Six cap concepts (twist shutter, screw cap, bayonet plug, spring hatch, slide gate, silicone septum), with trade-offs vs. the cap requirements C1–C7 distilled from issue #36. |
| [`requests.md`](requests.md) | Things the issue text invited me to ask for. |
| [`cad/sealing-cap-twist-shutter/`](cad/sealing-cap-twist-shutter/) | Concept §2.1 — two-disc twist shutter. CAD + sketch + STEP + STLs + renders. |
| [`cad/sealing-cap-spring-hatch/`](cad/sealing-cap-spring-hatch/) | Concept §2.2 — spring-loaded auto-opening hatch (zero mechanism-side actuator). |
| [`cad/sealing-cap-bayonet-plug/`](cad/sealing-cap-bayonet-plug/) | Concept §2.3 — quarter-turn bayonet plug with O-ring face seal. |

All three CAD packages target the PR-#16 Archimedes-auger envelope
(Ø25 OD, Ø3 mm exit), include a reference auger stub for visual sanity,
and follow the repo CAD-package convention (see PRs #31 / #33 / #35):
`cad_model.py` (CadQuery → STEP + per-part STLs in `stl/`),
`sketch_2d.py` (matplotlib dimensioned), `renders/` (SVG + PNG iso /
front / top / side + the dimensioned schematic), and a `README.md`.
