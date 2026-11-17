# Powder-property tests: animated walkthroughs and approximate costs

Animated 3D walkthroughs of the flow and characterization tests proposed for the
optimization paper (#179, PR #184, Q3 of the
[review answers](https://github.com/vertical-cloud-lab/powder-doser/pull/184#issuecomment-6302289770)).
Each one shows how the apparatus goes together and how the test runs, with a live chart of
what the test measures. They are schematics: proportions follow the standards where the
standards fix them (orifice sizes, cup volumes, sieve diameters) and are otherwise
approximate, and every number on screen is illustrative, not a measurement.

| Animation | Test | Standard | Property |
|---|---|---|---|
| [`hall_flow`](animations/hall_flow.gif) ([MP4](animations/hall_flow.mp4)) | Hall flowmeter, Carney funnel | ASTM B213, ASTM B964 | Flow rate, s/50 g |
| [`density`](animations/density.gif) ([MP4](animations/density.mp4)) | Apparent and tap density | ASTM B212, ASTM B527 | Hausner ratio |
| [`angle_of_repose`](animations/angle_of_repose.gif) ([MP4](animations/angle_of_repose.mp4)) | Fixed-funnel angle of repose | ISO 4324, USP <1174> | Angle of repose |
| [`sieve`](animations/sieve.gif) ([MP4](animations/sieve.mp4)) | Dry sieve analysis | ASTM B214 (ASTM E11 sieves) | PSD above about 45 µm |
| [`laser_diffraction`](animations/laser_diffraction.gif) ([MP4](animations/laser_diffraction.mp4)) | Laser diffraction | ASTM B822 (ISO 13320) | PSD, D10/D50/D90 |
| [`moisture_lod`](animations/moisture_lod.gif) ([MP4](animations/moisture_lod.mp4)) | Loss on drying, oven method | USP <731> | Moisture, % |
| [`ft4_shear`](animations/ft4_shear.gif) ([MP4](animations/ft4_shear.mp4)) | FT4 shear cell | ASTM D7891-24 | Yield locus, *ff*<sub>c</sub> |
| [`ring_shear`](animations/ring_shear.gif) ([MP4](animations/ring_shear.mp4)) | Schulze ring shear tester | ASTM D6773-22 | Yield locus, *ff*<sub>c</sub> |

## Approximate costs (28 Oct 2026)

[`costs.csv`](costs.csv) has 126 rows, each with the price text as shown, the source URL, the
retrieval route and date. In short (USD):

| Test | In-house, cheapest credible route | Outsourced, per sample |
|---|---|---|
| Hall / Carney flow, apparent density | Unbranded kit with both funnels, stand and cup: $341–$791 | Quote only |
| Tap density | Two Class A cylinders: $60 (automated tapper $4,956) | $250 (Micromeritics) |
| Angle of repose | Ring stand and funnel: $35–$60 | $175 (Micromeritics) |
| Sieve analysis | Six 200 mm sieves $654, plus a Ro-Tap $2,250 used to $3,460 new | $275 (Micromeritics) |
| Laser diffraction | $35k–$100k new (Malvern's range), $15k–$27k used | $5.10–$9.10 + $64.40/job (University of Utah, dry); $385 (Micromeritics) |
| Moisture (loss on drying) | Oven and desiccator: $833–$908 | $150 (Micromeritics) |
| Shear cell | Brookfield PFT $32,315 new, $9,650 refurbished; FT4 and Schulze quote only | $650 shear + wall friction (Micromeritics) |

Balances, shipping, tax and operator time are not included. Contract prices are list prices
for normal turnaround.

## Rebuilding

The scenes are plain Python on [PyVista](https://pyvista.org)/VTK, rendered off-screen
(Mesa's software OpenGL under Xvfb works; no GPU needed), composited with Pillow and
matplotlib, and encoded with ffmpeg (from `imageio-ffmpeg` if none is installed).

```bash
python -m venv .venv && .venv/bin/pip install -r render/requirements.txt
PYTHON=.venv/bin/python render/render_all.sh              # all scenes, 3 at a time
PYTHON=.venv/bin/python render/render_all.sh hall_flow    # one scene
# quick stills while editing a scene:
cd render && PREVIEW="2,8.5,20" PREVIEW_DIR=/tmp/preview xvfb-run -a python hall_flow.py
```

If several renders crash on their first frame under load, give each its own X display and
keep `LP_NUM_THREADS=2` (both are set by `render_all.sh`, which also retries).

`render/common.py` holds the shared pieces (stage and lighting, lathe-turned parts with
cutaways, falling-grain streams and heaps, the title card, step captions, labels, readouts,
the chart panel, and encoding). Each scene file is one test: a timeline of steps and a
`frame(t)` function. `render/shear_analysis.py` fits the yield locus and constructs the two
Mohr circles for both shear-cell scenes.
