I found six figure-specific internal-consistency problems for `fig4_design` (the repo figure that compiles as **Fig. 2** in `main.pdf`). The biggest ones are in panel **(b)**: the caption says the tap collar is **"carrying the solenoid striker and ERM vibration motor"**, but the actual asset `assets/tap_collar_final_iso.png` shows only the printed collar plus its grey `mount_plate` subpart, with **no solenoid and no ERM motor visible**. Panel **(a)** is weaker but still problematic: the caption says it shows **"flight clearances"**, yet the clearance is not clearly discernible in `assets/auger_geared_cross_section.png`; the helical channel is visible, but loading slots, nozzle, and other manuscript-described features are absent from this crop. There is also a text-level inconsistency between the manuscript body and the caption: Section 2.2 says the collar avoids loading the **"auger bearing"**, while the caption says it avoids transmitting load to the **"auger drive"**. Finally, panel (b) is silent about provenance even though the manuscript elsewhere says the **production tap collar was redesigned in Zoo Design Studio** after Copilot failed; and the asset filename implies a collar-only render even though the image includes the grey `mount_plate` subpart.

Detailed findings and proposed fixes:

1. **Caption overclaims what panel (b) shows: actuators are not visible**
   - **Figure caption file:** `caption_fig4_design.md:3`
     > "(b) Split-clamp tap collar carrying the solenoid striker and ERM vibration motor; ..."
   - **Compiled manuscript caption:** `main.pdf`, Fig. 2 caption
     > "(b) Split-clamp tap collar carrying the solenoid striker and ERM vibration motor; ..."
   - **Actual asset shown:** `assets/tap_collar_final_iso.png`
     - Visible: tan split-clamp collar body and grey base block.
     - Not visible: any solenoid, striker, ERM motor, wiring, or actuator housings.
   - **Branch-tree evidence for what exists:** `all_branches_file_tree.txt`
     - Bare/assembly tap-collar renders exist under `origin/copilot/design-tap-collar`:
       - `design/cad/tap-collar/renders/tap_collar_iso.png`
       - `design/cad/tap-collar/renders/assembly_iso.png`
       - `design/cad/tap-collar/renders/mount_plate_iso.png`
     - I found **no** branch-tree path showing a tap-collar render with the solenoid or ERM mounted. Files mentioning solenoid/ERM are separate vendor files or unrelated alternative concepts, e.g. `hardware/vibration-motor-and-solenoid.md`, `cad/alternatives/G-erm-sieve-iso.png`, `cad/alternatives/H-solenoid-sieve-iso.png`.
   - **Why this matters:** the current wording implies the actuators are shown, but the render only shows the printed support geometry.
   - **Corrected wording:**
     - Minimal fix: **"(b) Split-clamp tap collar and mount plate; the printed collar is designed to carry a solenoid striker and ERM vibration motor, and to couple impacts into the powder column without loading the auger bearing."**
     - If you want to avoid naming the grey part: **"(b) Split-clamp tap collar; the printed geometry provides mounting for the solenoid striker and ERM vibration motor ..."**

2. **Panel (b) omits a visible subpart: the image is not just the collar**
   - **Asset:** `assets/tap_collar_final_iso.png`
   - **Branch-tree paths indicating the sub-assembly structure:** under `origin/copilot/design-tap-collar`
     - `design/cad/tap-collar/stl/tap_collar.stl`
     - `design/cad/tap-collar/stl/mount_plate.stl`
     - `design/cad/tap-collar/renders/assembly_iso.png`
   - **Issue:** the caption and panel title treat panel (b) as only a "tap collar," but the render clearly includes the grey `mount_plate` beneath it.
   - **Source-code title:** `make_figures.py:355`
     > `ax.set_title("Tap collar + solenoid\nmount (split clamp)", fontsize=6)`
     This title implicitly acknowledges a mount, but the caption does not.
   - **Corrected wording:**
     - **"(b) Tap-collar sub-assembly (split-clamp collar on mount plate); the printed geometry provides mounting for the solenoid striker and ERM vibration motor ..."**

3. **Body text and caption disagree on what load is being isolated: bearing vs drive**
   - **Body text:** `main.pdf`, Section 2.2
     > "... the split-clamp tap collar that couples solenoid impacts into the powder column **without loading the auger bearing**, are shown in Fig. 2."
   - **Caption:** `caption_fig4_design.md:3` and `main.pdf`, Fig. 2 caption
     > "... the clamp couples impacts into the powder column **without transmitting load to the auger drive**."
   - **Issue:** "auger bearing" and "auger drive" are not the same component. The manuscript body is mechanically more specific.
   - **Corrected wording:**
     - Prefer the body-text version in both places: **"... without loading the auger bearing."**

4. **Panel (a) claims to show "flight clearances," but that is not clearly demonstrable from the render**
   - **Caption:** `caption_fig4_design.md:3`
     > "(a) Cross-section of the printed auger tube showing the helical channel and flight clearances."
   - **Asset:** `assets/auger_geared_cross_section.png`
     - Clearly visible: longitudinal cutaway of the tube and helical channel.
     - Not clearly visible: a readable radial gap that a reader could confidently identify as "flight clearance."
   - **Manuscript claim tying this panel to design specifics:** `main.pdf`, Section 2.2
     > "Key design specifics, including the auger tube cross-section ... are shown in Fig. 2."
   - **Issue:** the helical channel is visible; the clearance is, at best, ambiguous.
   - **Corrected wording:**
     - Conservative fix: **"(a) Longitudinal cross-section of the printed auger tube showing the helical channel."**
     - If you want to retain clearance only if you annotate it graphically: **add arrows/labels to the panel**, then keep "flight clearances."

5. **Panel (a) is narrower in scope than the manuscript's surrounding design description, which may mislead readers**
   - **Manuscript description elsewhere:**
     - `main.pdf`, Section 2.1
       > "... loaded directly into the printed Archimedes auger (25 mm OD) through loading slots in the auger tube ..."
     - `main.pdf`, Fig. 1 caption
       > "loading slots → helical channel → exit nozzle ..."
   - **Actual panel (a) asset:** `assets/auger_geared_cross_section.png`
     - No loading slots visible.
     - No exit nozzle visible.
     - No visible gear/pinion despite the asset name `auger_geared_cross_section.png` and source branch path `origin/copilot/add-new-auger-design/cad/auger-geared/archimedes-auger-geared-cross-section.png`.
   - **Issue:** this is not a contradiction in the strictest sense because the Fig. 2 caption does not mention those features, but it is an **unsupported implication risk**: readers may expect the panel to illustrate the cited design specifics more fully than it does.
   - **Corrected wording:**
     - In caption: keep the claim tight. **Do not imply more than a helical-channel cutaway.**
     - Suggested: **"(a) Longitudinal cutaway of the auger tube and internal helix."**

6. **Provenance of the final tap collar is not co-located with the figure that shows it**
   - **Human-review requirement:** `pr97_comments.md:22-36`
     > "Throughout this section, clarify where ai was used. We should be signposting the design contributions of ai versus engineers throughout the manuscript..."
     > "Only distinguish what was human vs. what was AI ... no CAD UI such as Fusion 360 or Solidworks was used ... except ... Zoo Design Studio ..."
   - **Relevant manuscript attribution elsewhere:**
     - `main.pdf`, Fig. 3 caption
       > "... the production tap collar was subsequently redesigned in Zoo Design Studio (three iterations to a usable part)."
     - `main.pdf`, Section 2.3.0.3
       > "the final tap collar reached a usable design in three Zoo iterations after the same number of Copilot iterations failed to orient the solenoid correctly."
   - **Current Fig. 2 / repo-fig4 caption:** silent on provenance.
   - **Issue:** not a direct contradiction, but it weakens the AI-vs-human signposting exactly at the figure where the final collar is displayed.
   - **Corrected wording:**
     - If you want provenance here: **"(b) Final split-clamp tap-collar sub-assembly (Zoo Design Studio redesign after unsuccessful programmatic-CAD iterations); the printed geometry provides mounting for the solenoid striker and ERM vibration motor ..."**
     - If that is too heavy for a caption, add one sentence in the body text when first citing Fig. 2.

Things I checked that are **not** figure-specific inconsistencies:
- The reviewer complaint in `pr97_comments.md` about "Fig. 2a" being described incorrectly is about the **failed first AI tap collar** in the generative-AI figure, now **Fig. 3a** in `main.pdf`, not this design-specifics figure.
- The HR-100A / load-cell correction is a manuscript-level issue elsewhere, not part of `fig4_design`; this figure and its caption do not mention the balance.
- The split-clamp description itself is consistent with the render: the collar is visibly split.

Short prioritized action list for this figure:
1. **Fix panel (b) caption first.** Replace "carrying the solenoid striker and ERM vibration motor" with wording that says the printed geometry is **designed to mount** them, unless you replace the asset with a render that actually shows the actuators.
2. **Standardize bearing/drive wording.** Use **"without loading the auger bearing"** in both the body text and the caption.
3. **Tighten panel (a) caption.** Remove "flight clearances" unless you annotate the clearance explicitly in the graphic.
4. **Name the visible sub-assembly honestly.** If keeping the current panel (b) asset, mention the **mount plate** or call it a **tap-collar sub-assembly**.
5. **Optionally add provenance at first mention.** Since the final collar shown here came from a Zoo redesign, add one short AI-vs-human provenance note in the body text or caption.

- Treated `caption_fig4_design.md`, `make_figures.py`, `assets/tap_collar_final_iso.png`, `assets/auger_geared_cross_section.png`, `main.pdf`, `pr97_comments.md`, and `all_branches_file_tree.txt` as the only admissible evidence sources.
- Used the compiled PDF numbering (`main.pdf` Fig. 2) while also noting the repo-local name (`fig4_design`) because they differ.
- Counted as inconsistencies only cases where the figure/caption/body text overclaimed, disagreed, or omitted a visible subpart in a way likely to mislead a reader; I did not count every absent feature as an inconsistency unless the text implied it was shown.
- Treated the AI-attribution issue for panel (b) as a lower-priority consistency/signposting problem rather than a hard contradiction, because the provenance is present elsewhere in the manuscript.
- Preferred the manuscript body's "auger bearing" wording over the caption's "auger drive" because it is mechanically more specific and consistent with the described function.