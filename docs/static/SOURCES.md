# Where the project page's files come from

`docs/index.html` is a single hand-editable HTML file with no build step and no
CSS or JavaScript framework. Everything it shows is in this folder, except the
MS&T talk, which loads from YouTube only when someone presses play.

| File | Source |
|---|---|
| `images/fig*.png`, `images/poster.jpg` | `docs/readme/` on the README branch for #214 ([`eac9f2c`](https://github.com/vertical-cloud-lab/powder-doser/tree/eac9f2c/docs/readme)), byte for byte. `scripts/readme_figures.py` on that branch crops them from the previews on #209. |
| `powder-doser-poster.pdf` | `docs/poster/powder-doser-poster.pdf` at `eac9f2c`, byte for byte: the PowerPoint export posted on #214 on 20 Nov 2026. |
| `videos/teaser_al4047_dose.mp4` | [`make_teaser.py`](make_teaser.py), from the three recordings behind #174's slide video ([`ed26df4`](https://github.com/vertical-cloud-lab/powder-doser/tree/ed26df4/docs/videos/2026-09-30-al4047-claude-dose)), with its sync: the phone camera on the bench ([QXSj0j1OqL8](https://youtu.be/QXSj0j1OqL8)), the phone's screen recording of the #166 thread ([dXRB7c6GeDw](https://youtu.be/dXRB7c6GeDw)) and the bench livestream ([yOK01jYPknA](https://youtu.be/yOK01jYPknA)). Unlike the slide video, the livestream stays a full panel on the right, so the dose itself shows. The table below lists the beats. |
| `videos/three_phase_procedure.mp4` | `docs/optimization/slides/procedure/procedure_annotated.mp4` on #175's branch ([`ff074df`](https://github.com/vertical-cloud-lab/powder-doser/tree/ff074df/docs/optimization/slides/procedure)). |
| `videos/doser_motion.mp4`, `videos/assembly_steps.mp4` | `cad/full-assembly/renders/doser_motion.gif` and `assembly_steps.gif` on #170's branch ([`7f5b3b7`](https://github.com/vertical-cloud-lab/powder-doser/tree/7f5b3b7/cad/full-assembly/renders)), converted from GIF to MP4. |
| `images/teaser_al4047_dose.jpg`, `images/three_phase_procedure.jpg`, `images/doser_motion.jpg`, `images/assembly_steps.jpg` | One frame of each video, shown until the video starts. `make_teaser.py` writes the teaser's, its first frame. |
| `screenshots/` | The page in headless Chrome at 1280 px and 390 px wide, for the pull request. The page doesn't link to them. |

### The teaser, beat by beat

All the beats are from 30 Sep 2026; times are MDT and the left and right panels
show the same moment.

| out (s) | wall clock | speed | left | right (livestream) |
|---|---|---|---|---|
| 0.0–4.0 | 14:36:31–14:37:31 | ×15 | phone camera: the filled auger is fitted to the doser | hands at the doser |
| 4.0–6.9 | 14:40:36–14:42:04 | ×30 | phone camera: last checks; the auger in place | the loaded doser |
| 6.9–12.9 | 14:59:03–14:59:51 | ×8 | screen: the whole phone, then into Claude's checklist "Dispensing 8 g of Al 4047 (9fxeqt)" | first pass: the tube at 40°, the reading climbs from 2.2 to 3.1 g |
| 12.9–14.4 | 15:29:52–15:30:35 | ×30 | screen: typing the follow-up after the clog | second pass, the tap stage |
| 14.4–15.8 | 15:30:35–15:30:42 | ×5 | screen: the @-mention of Claude typed in front of it, with GitHub's suggestions | second pass, the tap stage |
| 15.8–19.0 | 15:30:42–15:32:18 | ×30 | screen: the Actions page, where a Claude run is cancelled, then the rest of the message | second pass, the tap stage |
| 19.0–25.0 | 15:50:18–15:51:42 | ×14 | screen: Claude's plan, "Add a bulk-only mode to the firmware…" | the bulk-only top-up, 0 → 0.32 g |
| 25.0–28.7 | 15:57:10–15:57:40 | ×8 | screen: the dose trace in Claude's report; fade out | the auger is taken off the doser |

The phone camera stopped at 14:42:05 and the screen recording started at 14:59:01,
so the teaser has no footage of the 14:47:44 request itself. To rebuild it (needs
ffmpeg, yt-dlp, numpy, Pillow and requests; YouTube refuses datacenter IPs, so from
CI go through a lab Pi with `ssh -D 1080 -N`):

```bash
python docs/static/make_teaser.py download --proxy socks5h://127.0.0.1:1080   # 78 MB of fragments into /tmp/teaser-src
python docs/static/make_teaser.py render                                      # the .mp4 and its poster
python docs/static/make_teaser.py contact                                     # a contact sheet to check the cut
```

The other videos were re-encoded with ffmpeg as H.264 with no audio, so that they
autoplay muted and loop:

```bash
ffmpeg -i procedure_annotated.mp4 -an -vf "scale=1280:-2" -c:v libx264 -preset slow -crf 30 -pix_fmt yuv420p -movflags +faststart three_phase_procedure.mp4
ffmpeg -i doser_motion.gif -an -vf "fps=15,scale=960:-2:flags=lanczos" -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart doser_motion.mp4
ffmpeg -i assembly_steps.gif -an -vf "fps=15,scale=1280:-2:flags=lanczos" -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart assembly_steps.mp4
```

The captions under Figs. 1–7, S1 and S4 and Table 1 are copied from the
README on that branch, which takes them from #209's `CAPTIONS.md`. The README
has since been cut down to a pointer to this page, so the page is now the
only place they are kept up to date (the README with every figure is at
[`bf3f87a`](https://github.com/vertical-cloud-lab/powder-doser/blob/bf3f87a/README.md)).
The README shows this page's teaser as a GIF,
`docs/readme/gifs/al4047_claude_dose.gif`, which
[`scripts/readme_teaser_gif.py`](../../scripts/readme_teaser_gif.py) makes from
`videos/teaser_al4047_dose.mp4`; re-run it if the teaser changes.
