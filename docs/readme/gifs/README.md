# Animations in the README

Every GIF here except the livestream clip was made on an issue or PR whose branch
isn't merged (one, `loading_al4047.gif`, is cut from an MP4 there). [`scripts/readme_gifs.py`](../../../scripts/readme_gifs.py) fetches
each one from the commit it was posted at and shrinks the larger ones with
gifsicle (`-O3 --lossy=30`, and a narrower width where one is listed), so the
README keeps working if those branches are deleted.
[`scripts/livestream_clip_gif.py`](../../../scripts/livestream_clip_gif.py) makes
the livestream clip.

| GIF | What it shows | Made on | Source (commit: path) |
|---|---|---|---|
| [`assembly.gif`](assembly.gif) | The doser assembled in CAD in 19 steps, with each step's parts highlighted in the bill of materials (numbered as in SI Fig. S4) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/assembly_steps.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/assembly_steps.gif) |
| [`doser_motion.gif`](doser_motion.gif) | Tilt, turn and tap, close up on the CAD (scaled to 800 px wide) | [#170](https://github.com/vertical-cloud-lab/powder-doser/pull/170) | [`7f5b3b7`: `cad/full-assembly/renders/doser_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/7f5b3b7/cad/full-assembly/renders/doser_motion.gif) |
| [`livestream_salt_dose.gif`](livestream_salt_dose.gif) | A 0.5 g salt dose on the real doser, from the bench livestream (15 Sep 2026, 4× speed; 0.4963 g in 100 s; fine and tap phases, bulk skipped), with the logged mass after each weighing | this README ([#214](https://github.com/vertical-cloud-lab/powder-doser/issues/214)); the dose is [#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5683919348) | YouTube broadcast [`r6ZEN1O8B0Y`](https://youtu.be/r6ZEN1O8B0Y?t=20484), about 20485–20595 s, via `scripts/livestream_clip_gif.py` |
| [`three_phase_dose.gif`](three_phase_dose.gif) | A 0.5 g salt dose with the optimizer's recommended settings (`bo-005`), replayed on the CAD with the logged mass (scaled to 960 px wide) | [#175](https://github.com/vertical-cloud-lab/powder-doser/pull/175) | [`ff074df`: `docs/optimization/slides/procedure/procedure_annotated.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ff074df/docs/optimization/slides/procedure/procedure_annotated.gif) |
| [`thirteen_powders.gif`](thirteen_powders.gif) | One doser, 13 powders: mass per auger turn and 1 g doses, built up step by step (scaled to 1280 px wide) | [#173](https://github.com/vertical-cloud-lab/powder-doser/pull/173) | [`d75b7b7`: `paper/figures/versatility/versatility_build.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/d75b7b7/paper/figures/versatility/versatility_build.gif) |
| [`livestream_white_rice_flour.gif`](livestream_white_rice_flour.gif) | White rice flour, block C at 90° tilt, from the bench livestream (4 Aug 2026, 4× speed) | [#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116) | [`e51e8e8`: `docs/battery-runs/clips/wrf_C90.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/e51e8e8/docs/battery-runs/clips/wrf_C90.gif) |
| [`ai_recreation_motion.gif`](ai_recreation_motion.gif) | An agent's text-to-cad (build123d) recreation of the doser, servos-above variant, tilting, turning and tapping | [#176](https://github.com/vertical-cloud-lab/powder-doser/pull/176) ([#172](https://github.com/vertical-cloud-lab/powder-doser/issues/172)) | [`61717c7`: `cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/61717c7/cad/text-to-cad/renders/assembly/assembly_servos_above_motion.gif) |
| [`dem_twin.gif`](dem_twin.gif) | DEM twin of the rig's auger: 29k salt grains, 27.5° tilt, 60 rpm | [#158](https://github.com/vertical-cloud-lab/powder-doser/issues/158#issuecomment-6094253357) | [`ac9580e`: `sim/dem/results/rig_t27p5_r60.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/ac9580e/sim/dem/results/rig_t27p5_r60.gif) |
| [`loading_al4047.gif`](loading_al4047.gif) | Loading an auger with Al 4047 and fitting it to the doser (30 Sep 2026): phone camera and livestream side by side, the first 17.8 s of the slide video (560 px wide, 5 fps) | [#174](https://github.com/vertical-cloud-lab/powder-doser/pull/174) ([#166](https://github.com/vertical-cloud-lab/powder-doser/pull/166)) | [`ed26df4`: `docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4`](https://github.com/vertical-cloud-lab/powder-doser/blob/ed26df4/docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4) |
| [`multi_doser_v10.gif`](multi_doser_v10.gif) | The chain-carousel multi-doser, v10 (CAD only; scaled to 800 px wide) | [#185](https://github.com/vertical-cloud-lab/powder-doser/pull/185) ([#128](https://github.com/vertical-cloud-lab/powder-doser/issues/128)) | [`c72c5bc`: `cad/chain-carousel-v10/renders/v10/overview_v10.gif`](https://github.com/vertical-cloud-lab/powder-doser/blob/c72c5bc/cad/chain-carousel-v10/renders/v10/overview_v10.gif) |

## The livestream clip

The bench camera streams the doser to the lab's YouTube channel
([@byu-vcl-hardware-streams](https://youtube.com/@byu-vcl-hardware-streams)),
so every run since August is on video. YouTube refuses requests from the
GitHub Actions runner's datacenter address, so the 152 s section was fetched
with yt-dlp on the runner through an SSH SOCKS tunnel to the doser's Pi, which
only relayed the traffic (nothing was installed or written on it). The commands
are in the docstring of `scripts/livestream_clip_gif.py`.

The camera burns its clock (MDT) into the frame. The run log
([`data/battery/20260915T164228Z_salt-demo/`](https://github.com/vertical-cloud-lab/powder-doser/tree/2522858/data/battery/20260915T164228Z_salt-demo)
at `2522858`) gives each weighing's mass, and its time to the whole second, so
the phase changes were placed from the footage and checked against the log:
the fine phase's eighth-turns show one every 5.31 s, as in the log (all but the
first, which the tilt just before it hides), and the tube levels for the tap
phase right after the 16th weighing. The balance
display is out of this camera's frame, so the masses under the video are the
log's, each shown from the weighing that produced it. The settings are block
G's (`DOSE_PHASES` in `hardware/test-module/firmware/powder_battery.py` at
`2522858`). A 0.5 g target skips the bulk phase; fine is at 22.5° in
eighth-turns of the auger until less than 50 mg is left, then tap gives two
taps per cycle at 0° until within 5 mg.

The tube tips down as the run starts and holds still while the balance is
zeroed. No dose phase moves the servos then: the move is fast and unramped,
like the start-up write in `Servo.__init__` (`main_three_phase.py`), while
every phase change ramps the tube over 0.75 s.

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
  The 15 Sep clip replaced it. In that one, about seven single grains land on
  the shield's back wall during the dose, each smaller than a pixel at the
  GIF's size.
