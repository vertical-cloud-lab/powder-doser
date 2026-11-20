# Animations in the README

Every GIF here except the livestream clip was made on an issue or PR whose branch
isn't merged. [`scripts/readme_gifs.py`](../../../scripts/readme_gifs.py) fetches
each one from the commit it was posted at and shrinks the larger ones with
gifsicle (`-O3 --lossy=30`, and a narrower width where one is listed), so the
README keeps working if those branches are deleted.
[`scripts/livestream_clip_gif.py`](../../../scripts/livestream_clip_gif.py) makes
the livestream clip.

| GIF | What it shows | Made on | Source (commit: path) |
|---|---|---|---|
| [`assembly.gif`](assembly.gif) | The doser assembled in CAD in 19 steps, with each step's parts highlighted in the bill of materials (numbered as in SI Fig. S4) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/assembly_steps.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/assembly_steps.gif) |
| [`doser_motion.gif`](doser_motion.gif) | Tilt, turn and tap, close up on the CAD (scaled to 800 px wide) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/doser_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/doser_motion.gif) |
| [`livestream_three_phase_dose.gif`](livestream_three_phase_dose.gif) | A three-phase 1 g salt dose on the real doser, from the bench livestream (3 Sep 2026, 4× speed; 1.0040 g in 90 s) | this README ([#214](https://github.com/vertical-cloud-lab/powder-doser/issues/214)); the dose is [#148](https://github.com/vertical-cloud-lab/powder-doser/issues/148#issuecomment-5533802075) | YouTube broadcast [`xjtJNMo8DKw`](https://youtu.be/xjtJNMo8DKw?t=15158), 15158–15278 s, via `scripts/livestream_clip_gif.py` |
| [`three_phase_dose.gif`](three_phase_dose.gif) | A 0.5 g salt dose with the optimizer's recommended settings (`bo-005`), replayed on the CAD with the logged mass (scaled to 960 px wide) | [#175](https://github.com/vertical-cloud-lab/powder-doser/pull/175) | [`ff074df`: `docs/optimization/slides/procedure/procedure_annotated.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/procedure/procedure_annotated.gif) |
| [`thirteen_powders.gif`](thirteen_powders.gif) | One doser, 13 powders: mass per auger turn and 1 g doses, built up step by step (scaled to 1280 px wide) | [#173](https://github.com/vertical-cloud-lab/powder-doser/pull/173) | [`d75b7b7`: `paper/figures/versatility/versatility_build.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/d75b7b7/paper/figures/versatility/versatility_build.gif) |
| [`livestream_white_rice_flour.gif`](livestream_white_rice_flour.gif) | White rice flour, block C at 90° tilt, from the bench livestream (4 Aug 2026, 4× speed) | [#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116) | [`e51e8e8`: `docs/battery-runs/clips/wrf_C90.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/e51e8e8/docs/battery-runs/clips/wrf_C90.gif) |
| [`ai_recreation_motion.gif`](ai_recreation_motion.gif) | An agent's text-to-cad (build123d) recreation of the doser, servos-above variant, tilting, turning and tapping | [#176](https://github.com/vertical-cloud-lab/powder-doser/pull/176) ([#172](https://github.com/vertical-cloud-lab/powder-doser/issues/172)) | [`61717c7`: `cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/61717c7/cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif) |
| [`dem_twin.gif`](dem_twin.gif) | DEM twin of the rig's auger: 29k salt grains, 27.5° tilt, 60 rpm | [#158](https://github.com/vertical-cloud-lab/powder-doser/issues/158#issuecomment-6094253357) | [`ac9580e`: `sim/dem/results/rig_t27p5_r60.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ac9580e/sim/dem/results/rig_t27p5_r60.gif) |
| [`multi_doser_v10.gif`](multi_doser_v10.gif) | The chain-carousel multi-doser, v10 (CAD only; scaled to 800 px wide) | [#185](https://github.com/vertical-cloud-lab/powder-doser/pull/185) ([#128](https://github.com/vertical-cloud-lab/powder-doser/issues/128)) | [`c72c5bc`: `cad/chain-carousel-v10/renders/v10/overview_v10.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/c72c5bc/cad/chain-carousel-v10/renders/v10/overview_v10.gif) |

## The livestream clip

The bench camera streams the doser to the lab's YouTube channel
([@byu-vcl-hardware-streams](https://youtube.com/@byu-vcl-hardware-streams)),
so every run since August is on video. YouTube refuses requests from the
GitHub Actions runner's datacenter address, so the 120 s section was fetched
with yt-dlp on the runner through an SSH SOCKS tunnel to the doser's Pi, which
only relayed the traffic (nothing was installed or written on it). The commands
are in the docstring of `scripts/livestream_clip_gif.py`. The camera burns its
clock (MDT) into the frame; the phase times in the GIF were read off the
balance display in the clip and agree with the run log in #148. The settings
are block G's (`DOSE_PHASES` in `hardware/test-module/firmware/powder_battery.py`
on the #116 branches): bulk at 45° and 55 rpm until 0.5 g is left, fine at
22.5° in eighth-turns of the auger until less than 50 mg is left, then two taps
per cycle at 0° until within 5 mg.

## Finding them

The GIFs were found by pulling every issue, PR, comment, review comment and
review in the repository through `gh api` (2,848 texts on 20 Nov 2026) and
listing every link to a GIF or video: 183 GIFs, 61 MP4s, 105 YouTube videos
and 19 uploaded videos. Most of the GIFs are about the chain carousel (#185),
the physics simulations (#196), the powder tests (#190) and the optimization
slides (#175); the ones above are those about the doser in the paper.
