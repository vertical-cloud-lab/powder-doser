---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 26px;
    padding: 56px 72px 48px 72px;
  }
  /* Doumont: title area = message area. Use a full-sentence message in normal weight. */
  h1 {
    font-size: 32px;
    font-weight: 600;
    line-height: 1.25;
    color: #111;
    margin: 0 0 24px 0;
    border-bottom: 2px solid #d0d0d0;
    padding-bottom: 10px;
  }
  h2 { font-size: 28px; font-weight: 600; color: #222; }
  blockquote {
    border-left: 4px solid #888;
    color: #333;
    background: #f6f6f6;
    padding: 10px 16px;
    font-size: 22px;
    margin: 12px 0;
  }
  code, pre { font-size: 20px; }
  footer { color: #888; font-size: 14px; }
  /* Title slide */
  section.title h1 {
    border: none;
    font-size: 46px;
    font-weight: 700;
  }
  section.title { text-align: center; }
  /* Image-dominant slide: minimize chrome, image carries the signal */
  section.image-only h1 { font-size: 26px; font-weight: 500; margin-bottom: 12px; }
  section.image-only img { display: block; margin: 0 auto; max-height: 70vh; }
  section.image-only p { font-size: 22px; color: #444; }
  /* Two-column comparison */
  .cols  { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .cols3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 18px; align-items: center; }
  .cols3 img { max-width: 100%; max-height: 58vh; display: block; margin: 0 auto; }
  .cols h3 { margin-top: 0; }
  .label-before { color: #b00020; }
  .label-after  { color: #1b6e1b; }
  /* Issue/PR trajectory strip */
  .timeline {
    font-size: 16px; color: #555; letter-spacing: 0.5px;
    margin-top: 18px; padding-top: 6px; border-top: 1px dashed #ccc;
  }
  .timeline .hinge { color: #1b6e1b; font-weight: 700; }
footer: "powder-doser · project wrap-up"
---

<!-- _class: title -->
<!-- _paginate: false -->

# Powder dispenser

[![w:560](assets/final-print-on-ultimaker.jpg)](https://www.youtube.com/watch?v=0CAu-x3wXns)

Sterling Baird · Devora Najjar · Ron
*with Nasa's help on the Ultimaker print*

[▶ Project walkthrough on YouTube — *AI-designed powder dispenser, POSE 2026*](https://www.youtube.com/watch?v=0CAu-x3wXns)

[github.com/vertical-cloud-lab/powder-doser — PR #16](https://github.com/vertical-cloud-lab/powder-doser/pull/16)

---

<!-- _class: image-only -->

# Our final concept is a 3D-printed Archimedes auger.

<div class="cols">
  <div><img src="assets/manual-deck/auger-iso.png" alt="Auger side view" style="max-height:62vh;"></div>
  <div><img src="assets/manual-deck/auger-top-cross-section.png" alt="Auger top cross-section" style="max-height:62vh;"></div>
</div>

---

<!-- _class: image-only -->

# First sketch: a side-pivoting trough that pours over its long edge.

![w:880](assets/manual-deck/pivot-original.gif)

*Pivot axis runs along the trough length L; the trough rolls sideways and pours over the full long edge.*

---

<!-- _class: image-only -->

# Revised: a cam ramp keeps the rim engaged through the full rotation.

![w:880](assets/mechanism.gif)

*Rim stays in contact with the cam ramp throughout rotation; pours over the full long edge.*

---

<!-- _class: image-only -->

# Cam-driven scoop — side, iso, and top views.

<div class="cols3">
  <div><img src="assets/manual-deck/cam-scoop-side.png" alt="Side view"></div>
  <div><img src="assets/manual-deck/cam-scoop-iso.png" alt="Iso view"></div>
  <div><img src="assets/manual-deck/cam-scoop-top.png" alt="Top view"></div>
</div>

---

<!-- _class: image-only -->

# We screened seven candidate powders by hand-feel.

![w:880](assets/manual-deck/powder-candidates.png)

*Rice flour · brown rice flour · sodium alginate · calcium lactate · carboxymethyl cellulose · xanthan gum.*

---

<!-- _class: image-only -->

# Hand-scooping established the dose target — and the failure modes.

[![w:760](assets/manual-deck/manual-scoop-1.jpg)](https://www.youtube.com/watch?v=VAltAawtkA4)

[▶ Pouring xanthan gum — youtube.com/watch?v=VAltAawtkA4](https://www.youtube.com/watch?v=VAltAawtkA4)

---

<!-- _class: image-only -->

# Powder clung to scoop walls; one sample stayed put after dumping.

[![w:760](assets/manual-deck/manual-scoop-2.jpg)](https://www.youtube.com/watch?v=IMuK3LTAWLM)

[▶ Pouring rice flour — youtube.com/watch?v=IMuK3LTAWLM](https://www.youtube.com/watch?v=IMuK3LTAWLM)

*Surface forces (electrostatic, van der Waals) dominate at this scale — Devora's call from issue #3.*

---

<!-- _class: image-only -->

# A bistable snap-through trough was one alternative we explored.

![w:760](assets/manual-deck/bistable-trough.gif)

---

<!-- _class: image-only -->

# The bistable mechanism has two energy wells at ±1.9 mm.

![w:880](assets/bimodal-mechanism.gif)

*PR #5 — parametric OpenSCAD + FEA cross-check, peak snap **2.36 N**, 23 passing / 1 skipped.*

---

<!-- _class: image-only -->

# Commercial dispensers span lab balances to industrial feeders.

![w:880](assets/manual-deck/commercial-landscape.png)

*Edison Scientific surveyed the landscape — no off-the-shelf unit hit our μg–mg, low-cost, open-source target.*

---

<!-- _class: image-only -->

# We considered eight concepts before converging on the auger.

![w:880](assets/composite-spin.gif)

*Sterling Baird · Devora Najjar · Ron · with Nasa's help on the Ultimaker print.*
