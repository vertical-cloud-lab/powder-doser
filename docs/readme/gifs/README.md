# Animations in the README

Every GIF here was made on an issue or PR whose branch isn't merged (one,
`loading_al4047.gif`, is cut from an MP4 there). [`scripts/readme_gifs.py`](../../../scripts/readme_gifs.py) fetches
each one from the commit it was posted at and shrinks the larger ones with
gifsicle (`-O3 --lossy=30`, and a narrower width where one is listed), so the
README keeps working if those branches are deleted. The exception is
`livestream_al4047_dose.gif`, which [`scripts/livestream_clip_gif.py`](../../../scripts/livestream_clip_gif.py)
cuts from the bench livestream on YouTube; its docstring has the fetch
commands and the timings.

| GIF | What it shows | Made on | Source (commit: path) |
|---|---|---|---|
| [`assembly.gif`](assembly.gif) | The doser assembled in CAD in 19 steps, with each step's parts highlighted in the bill of materials (numbered as in SI Fig. S4) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/assembly_steps.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/assembly_steps.gif) |
| [`doser_motion.gif`](doser_motion.gif) | Tilt, turn and tap, close up on the CAD (scaled to 800 px wide) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/doser_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/doser_motion.gif) |
| [`three_phase_dose.gif`](three_phase_dose.gif) | A 0.5 g salt dose with the optimizer's recommended settings (`bo-005`), replayed on the CAD with the logged mass (scaled to 960 px wide) | [#175](https://github.com/vertical-cloud-lab/powder-doser/pull/175) | [`ff074df`: `docs/optimization/slides/procedure/procedure_annotated.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/procedure/procedure_annotated.gif) |
| [`thirteen_powders.gif`](thirteen_powders.gif) | One doser, 13 powders: mass per auger turn and 1 g doses, built up step by step (scaled to 1280 px wide) | [#173](https://github.com/vertical-cloud-lab/powder-doser/pull/173) | [`d75b7b7`: `paper/figures/versatility/versatility_build.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/d75b7b7/paper/figures/versatility/versatility_build.gif) |
| [`livestream_white_rice_flour.gif`](livestream_white_rice_flour.gif) | White rice flour, block C at 90° tilt, from the bench livestream (4 Aug 2026, 4× speed) | [#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116) | [`e51e8e8`: `docs/battery-runs/clips/wrf_C90.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/e51e8e8/docs/battery-runs/clips/wrf_C90.gif) |
| [`ai_recreation_motion.gif`](ai_recreation_motion.gif) | An agent's text-to-cad (build123d) recreation of the doser, servos-above variant, tilting, turning and tapping | [#176](https://github.com/vertical-cloud-lab/powder-doser/pull/176) ([#172](https://github.com/vertical-cloud-lab/powder-doser/issues/172)) | [`61717c7`: `cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/61717c7/cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif) |
| [`dem_twin.gif`](dem_twin.gif) | DEM twin of the rig's auger: 29k salt grains, 27.5° tilt, 60 rpm | [#158](https://github.com/vertical-cloud-lab/powder-doser/issues/158#issuecomment-6094253357) | [`ac9580e`: `sim/dem/results/rig_t27p5_r60.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ac9580e/sim/dem/results/rig_t27p5_r60.gif) |
| [`loading_al4047.gif`](loading_al4047.gif) | Loading an auger with Al 4047 and fitting it to the doser (30 Sep 2026): phone camera and livestream side by side, the first 17.8 s of the slide video (560 px wide, 5 fps) | [#174](https://github.com/vertical-cloud-lab/powder-doser/pull/174) ([#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)) | [`ed26df4`: `docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4`](https://github.com/vertical-cloud-lab/powder-doser/blob/ed26df4/docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4) |
| [`livestream_al4047_dose.gif`](livestream_al4047_dose.gif) | The first pass of the 8 g Al 4047 dose into the aluminium cup (30 Sep 2026, trial `3e7490c2`): tare, the tilt to 40° and the bulk phase until the pass stopped at 3.49 g, from the bench livestream with the balance display in view (360 px wide, 20 fps, 5× speed) | [#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166) ([#214](https://github.com/vertical-cloud-lab/powder-doser/issues/214)) | YouTube [`yOK01jYPknA`](https://youtu.be/yOK01jYPknA?t=7045), 1:57:29-1:59:17, cut by [`scripts/livestream_clip_gif.py`](../../../scripts/livestream_clip_gif.py) |
| [`multi_doser_v10.gif`](multi_doser_v10.gif) | The chain-carousel multi-doser, v10 (CAD only; scaled to 800 px wide) | [#185](https://github.com/vertical-cloud-lab/powder-doser/pull/185) ([#128](https://github.com/vertical-cloud-lab/powder-doser/issues/128)) | [`c72c5bc`: `cad/chain-carousel-v10/renders/v10/overview_v10.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/c72c5bc/cad/chain-carousel-v10/renders/v10/overview_v10.gif) |

## Finding them

The GIFs were found by pulling every issue, PR, comment, review comment and
review in the repository through `gh api` (2,848 texts on 20 Nov 2026) and
listing every link to a GIF or video: 183 GIFs, 61 MP4s, 105 YouTube videos
and 19 uploaded videos. Most of the GIFs are about the chain carousel (#185),
the physics simulations (#196), the powder tests (#190) and the optimization
slides (#175); the ones above are those about the doser in the paper.

## Not used

- **The livestream clip of the 3 Sep 2026 salt dose**
  ([#148](https://github.com/vertical-cloud-lab/powder-doser/issues/148)): it
  shows salt scattered over the inside of the balance's draft shield, so it
  was dropped ([#214](https://github.com/vertical-cloud-lab/powder-doser/issues/214)).
- **The livestream clip of the 15 Sep 2026 salt dose**
  ([#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116)),
  made on #214 but never merged: it kept 4 frames per second at 4× speed, so
  it looked choppy, and an Al powder dosed into the aluminium cup was
  wanted instead. `livestream_al4047_dose.gif` replaced it.
