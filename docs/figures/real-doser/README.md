# Companion images of the real (as-built) powder doser

Requested in [issue #165](https://github.com/vertical-cloud-lab/powder-doser/issues/165):
a photo of the fully assembled, functional system to pair with the annotated CAD
render, ideally in the same orientation / perspective.

| File | What it is |
|---|---|
| `cad-render-annotated.png` | The reference CAD render (Rotation / Tapping / Vibration / Tilt / Powder stream) from issue #165. |
| `companion-real-doser.jpg` | **Primary companion image.** Frame at t ≈ 65 s of the first automated dispense video, cropped to the render's aspect ratio (1653×1080) with a light auto-level + small saturation bump. Same orientation as the render: auger tube running to the upper-left, rotation gear train center, tap solenoid on top, tilt gear/servo at right, powder collected in a crucible on the balance below right. |
| `companion-real-doser-raw-frame.jpg` | The same frame, untouched (full 1920×1080), for provenance / re-cropping. |
| `side-by-side.png` | Labeled two-panel figure: CAD render (left) vs. as-built frame (right). |
| `alt-test-rig-mid-dose.jpg` | Alternate: frame at t ≈ 114 s of the closed-loop test rig video — module on the black test table mid-dose, beaker + A&D HR-100A draft shield below, breadboard electronics at right. Mirrored orientation relative to the render. |
| `alt-bench-module-brown-rice-flour.jpg` | Alternate (native photo, 4032×3024): module loaded with brown rice flour on the bench, from [#116 (comment, 2026-08-04)](https://github.com/vertical-cloud-lab/powder-doser/issues/116#issuecomment-5184344406). Mirrored orientation relative to the render. |

## Provenance

- `companion-real-doser*`: ["first test" video](https://youtu.be/L0jCNZVXHoc) (BYU
  Vertical Cloud Lab channel), linked from
  [#117 (comment, 2026-07-27)](https://github.com/vertical-cloud-lab/powder-doser/issues/117#issuecomment-5097409563) —
  the first automated salt dispense into a crucible on the balance inside the glovebox.
  Extract the frame with:

  ```bash
  yt-dlp -f "bv*[height<=1080]" -o vid.mp4 https://youtu.be/L0jCNZVXHoc
  ffmpeg -ss 65.0 -i vid.mp4 -frames:v 1 -q:v 2 companion-real-doser-raw-frame.jpg
  ```

  (YouTube blocks the GitHub-runner IP; downloads were done on the Pi per the
  established workflow, then transferred rate-capped.)
- `alt-test-rig-mid-dose.jpg`: [test-rig video](https://youtu.be/qYwFWl76y3c) at t ≈ 114 s,
  linked from [#124 (comment)](https://github.com/vertical-cloud-lab/powder-doser/pull/124#issuecomment-4972355376)
  / [#100](https://github.com/vertical-cloud-lab/powder-doser/issues/100).
- More footage: the [Powder Doser playlist](https://www.youtube.com/playlist?list=PLZTWCFxzhTQv42fTuW2Tjs9o1KuWA_b-I)
  and the [hardware-streams channel](https://youtube.com/@byu-vcl-hardware-streams).
