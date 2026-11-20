# Where the project page's files come from

`docs/index.html` is a single hand-editable HTML file with no build step and no
CSS or JavaScript framework. Everything it shows is in this folder, except the
MS&T talk, which loads from YouTube only when someone presses play.

| File | Source |
|---|---|
| `images/fig*.png`, `images/poster.jpg` | `docs/readme/` on the README branch for #214 ([`eac9f2c`](https://github.com/vertical-cloud-lab/powder-doser/tree/eac9f2c/docs/readme)), byte for byte. `scripts/readme_figures.py` on that branch crops them from the previews on #209. |
| `powder-doser-poster.pdf` | `docs/poster/powder-doser-poster.pdf` at `eac9f2c`, byte for byte: the PowerPoint export posted on #214 on 20 Nov 2026. |
| `videos/teaser_al4047_dose.mp4` | The first 17.4 s of `docs/videos/2026-09-30-al4047-claude-dose/al4047_claude_dose_slide.mp4` on #174's branch ([`ed26df4`](https://github.com/vertical-cloud-lab/powder-doser/tree/ed26df4/docs/videos/2026-09-30-al4047-claude-dose)), up to where the video cuts to the GitHub thread. |
| `videos/three_phase_procedure.mp4` | `docs/optimization/slides/procedure/procedure_annotated.mp4` on #175's branch ([`ff074df`](https://github.com/vertical-cloud-lab/powder-doser/tree/ff074df/docs/optimization/slides/procedure)). |
| `videos/doser_motion.mp4`, `videos/assembly_steps.mp4` | `cad/full-assembly/renders/doser_motion.gif` and `assembly_steps.gif` on #170's branch ([`7f5b3b7`](https://github.com/vertical-cloud-lab/powder-doser/tree/7f5b3b7/cad/full-assembly/renders)), converted from GIF to MP4. |
| `images/teaser_al4047_dose.jpg`, `images/three_phase_procedure.jpg`, `images/doser_motion.jpg`, `images/assembly_steps.jpg` | One frame of each video, shown until the video starts. |
| `screenshots/` | The page in headless Chrome at 1280 px and 390 px wide, for the pull request. The page doesn't link to them. |

The videos were re-encoded with ffmpeg as H.264 with no audio, so that they
autoplay muted and loop:

```bash
ffmpeg -t 17.4 -i al4047_claude_dose_slide.mp4 -an -vf "scale=1280:-2,fps=30" -c:v libx264 -preset slow -crf 30 -pix_fmt yuv420p -movflags +faststart teaser_al4047_dose.mp4
ffmpeg -i procedure_annotated.mp4 -an -vf "scale=1280:-2" -c:v libx264 -preset slow -crf 30 -pix_fmt yuv420p -movflags +faststart three_phase_procedure.mp4
ffmpeg -i doser_motion.gif -an -vf "fps=15,scale=960:-2:flags=lanczos" -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart doser_motion.mp4
ffmpeg -i assembly_steps.gif -an -vf "fps=15,scale=1280:-2:flags=lanczos" -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart assembly_steps.mp4
```

The captions under Figs. 1–7, S1 and S4 and Table 1 are copied from the
README on that branch, which takes them from #209's `CAPTIONS.md`. If the
README's figures or captions change, update both.
