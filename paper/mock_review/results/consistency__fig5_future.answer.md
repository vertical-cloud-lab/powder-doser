I found four figure-specific consistency problems for **Figure 5 (future work, multi-powder doser)**, plus one adjacent repository-support problem that affects how strongly Figure 5 can be claimed in the manuscript.

1. **The manuscript says the future-work geometry already has “working CAD in the repository,” but the supplied repository tree only supports a much narrower claim.**
   - **Manuscript body:** `main.pdf`, Section 4: “*the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.*”
   - **What the supplied files support:** `all_branches_file_tree.txt` shows only one multi-doser geometry directory: `origin/copilot/brainstorming-design-possibilities/design/cad/inward-collection-cup/` with `cad_model.py`, `inward_collection_cup.step`, `inward_collection_cup_iso.png`, `inward_collection_cup_top.png`, etc. The separate branch `origin/copilot/zoo-design-studio-multi-doser` contains only `paper/background/15-zoo-design-studio-multi-doser.md` and `paper/background/23-zds-transcript-editing-session.md`; no CAD files are listed there. 
   - **Why this is inconsistent/unsupported:** The available tree supports a **single inward-collection-cup concept CAD study**, not a broader claim that “the multi-doser geometry” in general is already present as working CAD. There is no second multi-doser assembly CAD in the supplied tree.
   - **Proposed correction:** Replace with: “*A preliminary inward-collection-cup concept and related channel-sealing concepts already have CAD in the repository.*”

2. **The manuscript ties Figure 5 future work to “swappable sealed cartridges,” but the supplied repository tree does not support cartridge-specific sealing CAD.**
   - **Manuscript body:** `main.pdf`, Section 4: “*...with a loaded subset of 8–12 powders and a path to a 50-powder pool via swappable sealed cartridges...*” and then “*the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.*”
   - **What the supplied files support:** `all_branches_file_tree.txt` shows one file containing “cartridge” in its name across all branches: `origin/copilot/modular-single-channel-powder-doser-design/design/cad/single-channel-module/stl/cartridge.stl`. The branch `origin/copilot/design-channel-sealing-cap` does contain substantial CAD, but it is for `sealing-cap-bayonet-plug`, `sealing-cap-spring-hatch`, and `sealing-cap-twist-shutter` concepts, not cartridge-specific sealing.
   - **Why this is inconsistent/unsupported:** The text escalates from “channel-sealing cap concepts exist” to “swappable sealed cartridges” and “cartridge-sealing concepts already have working CAD.” The supplied branch tree does not back that stronger cartridge-specific wording.
   - **Proposed correction:** Replace with: “*...with a loaded subset of 8–12 powders and a path to larger powder pools via swappable sealed reservoirs or cartridges; outlet/channel-sealing concepts already have CAD in the repository.*”
   - If the authors want to keep “cartridges,” they need a repository path that actually contains cartridge-sealing CAD.

3. **Panel (a) is drawn as a specific 8-channel layout, while the caption and body text present it as generic “N-channel” future work.**
   - **Figure source:** `make_figures.py`, `fig5()`, lines 373–389 set `n = 8` and draw exactly eight radial channel blocks.
   - **Caption file:** `caption_fig5_future.md`: “*(a) N-channel radial array concept around a shared collection cup on a single balance.*”
   - **Manuscript body:** `main.pdf`, Section 4: “*...a multi-powder doser arraying N printed channels around a shared collection cup (Fig. 5), with a loaded subset of 8–12 powders...*”
   - **Why this is inconsistent:** The actual panel is not generic N; it is an 8-position schematic. That is not fatal, but it is a real internal mismatch between what is shown and how it is described.
   - **Proposed correction options:**
     - If the figure is meant to stay fixed: “*(a) Eight-channel radial array concept around a shared collection cup on a single balance.*”
     - If the generic wording is important: modify `make_figures.py` or the artwork so panel (a) visually reads as a variable-N schematic rather than a concrete 8-slot layout.

4. **Panel (b) does not show a balance, but both the caption and manuscript text tie the concept explicitly to a shared cup “on a single balance.”**
   - **Caption file:** `caption_fig5_future.md`: “*(a) N-channel radial array concept around a shared collection cup on a single balance. (b) CAD study of inward-tilting channels over the shared cup.*”
   - **Manuscript body:** `main.pdf`, Fig. 5 caption on page 7 repeats “*on a single balance*” for panel (a); Section 4 describes “*N printed channels around a shared collection cup (Fig. 5)*.”
   - **Asset actually shown:** `assets/inward_collection_cup_iso.png` shows inward-tilting tube placeholders over a central cup on a platform/base, but no identifiable balance hardware is visible in panel (b).
   - **Why this matters:** The wording is safe for panel (a), which is a conceptual schematic, but a reader could over-read panel (b) as showing a balance-integrated CAD study when it does not. This becomes more sensitive because the reviewer notes in `pr97_comments.md` insist on hardware accuracy around weighing terminology: “*Also, it's an HR-100A load cell*” is immediately corrected in the resource note to “*A&D HR-100A analytical balance ... NOT an HX711 load cell*” (`pr97_comments.md`, lines 125–127). Figure 5 does not make the wrong “load cell” claim, but panel (b) also does not visually substantiate a balance claim.
   - **Proposed correction:** “*(b) CAD study of inward-tilting channels over a shared collection cup; balance hardware not shown.*”

5. **The future-work reviewer comment says this section/figure is stale relative to GitHub-reported progress, which undercuts the strength of present-tense Figure 5 claims.**
   - **Human review comment:** `pr97_comments.md`, thread at `paper/main.tex line 258`, HUMAN reviewer: “*The future work has changed a bit, but progress here has not yet been reported on Github. This section and its figures will be changed as updated information is uploaded.*”
   - **Why this matters for Figure 5:** The current figure/caption/manuscript wording is being asked to carry more certainty than the documented repository state justifies. This is especially relevant for the “working CAD in the repository” and “swappable sealed cartridges” language.
   - **Proposed correction:** soften present-tense certainty throughout the Figure 5 discussion, e.g. “*preliminary concept CAD*,” “*under active revision*,” or “*current concept shown in Fig. 5*.”

What I **did not** find for Figure 5:
- I did **not** find a direct Figure 5 contradiction with the **no-hopper** correction. Figure 5’s caption does not mention a hopper, and panel (b) is just a concept render of inward-tilting channels over a cup.
- I did **not** find a direct Figure 5 contradiction with the **HR-100A / not HX711** correction. Figure 5 says “single balance,” not “load cell.”
- I did **not** find a Figure 5-specific AI-vs-human attribution error in the caption. The future-work figure is sourced from programmatic CAD/repository assets, and nothing in `pr97_comments.md` contradicts that at the figure level. The broader manuscript should still keep the HUMAN-vs-AI split explicit, as requested in `pr97_comments.md` lines 23–36.

A note on the asset itself:
- `make_figures.py` labels panel (b) “*Inward-tilting channels over shared cup (CAD)*.”
- `assets/inward_collection_cup_iso.png` appears to show about **8** inward-tilted tube/channel placeholders around the cup, which is consistent with panel (a)’s hard-coded `n = 8` in `make_figures.py`.
- But those are **not full single-channel modules** with visible motor, gear, tap collar, or servo hardware. So if the authors want the figure to communicate “arraying full printed channels/modules,” the wording should avoid implying that panel (b) is already a detailed module-level assembly.

## Suggested corrected wording for the full Figure 5 caption
Current (`caption_fig5_future.md`):
> “Future work: multi-powder doser. (a) $N$-channel radial array concept around a shared collection cup on a single balance. (b) CAD study of inward-tilting channels over the shared cup.”

Safer revision:
> “Future work: multi-powder doser. (a) Eight-channel radial array concept around a shared collection cup on a single analytical balance. (b) Preliminary CAD study of inward-tilting channel positions over the shared cup; balance hardware and full per-channel actuation are not shown.”

If the authors want to preserve generic scalability:
> “Future work: multi-powder doser. (a) Example eight-channel radial array illustrating a scalable $N$-channel concept around a shared collection cup on a single analytical balance. (b) Preliminary CAD study of inward-tilting channel positions over the shared cup; balance hardware and full per-channel actuation are not shown.”

## Suggested corrected wording for the manuscript body (Section 4)
Current key sentence in `main.pdf`:
> “Ongoing work extends the platform to (1) a multi-powder doser arraying N printed channels around a shared collection cup (Fig. 5), with a loaded subset of 8–12 powders and a path to a 50-powder pool via swappable sealed cartridges; ... Each will be reported separately; the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.”

Safer revision:
> “Ongoing work extends the platform to (1) a multi-powder doser concept arraying printed channels around a shared collection cup (Fig. 5), initially targeting roughly 8–12 powders and potentially larger powder pools through future sealed reservoir/cartridge designs; ... Each will be reported separately; a preliminary inward-collection-cup concept and channel-sealing concepts already have CAD in the repository.”

## Prioritized action list for Figure 5
- **1. Fix the strongest unsupported claim first:** change “working CAD in the repository” and “cartridge-sealing concepts” to wording that matches the actual repository tree.
- **2. Decide whether panel (a) is 8-channel or generic N-channel:** either relabel it as eight-channel or redraw it to look generic.
- **3. Clarify panel (b):** state that it is a preliminary positional/layout CAD study, not a full multi-module assembly and not a balance-integrated render.
- **4. Soften Section 4 future-work certainty:** align with the HUMAN reviewer comment that this area has changed and is not fully reported on GitHub yet.
- **5. If desired, add one sentence of provenance:** e.g. that the concept CAD is programmatic/AI-authored under HUMAN review, consistent with the manuscript’s broader attribution policy.

- Used only the supplied bundle (`main.pdf`, `caption_fig5_future.md`, `make_figures.py`, `assets/inward_collection_cup_iso.png`, `pr97_comments.md`, `all_branches_file_tree.txt`) and did not infer missing repository contents beyond the branch-tree paths.
- Treated `make_figures.py` as the authoritative source for what Figure 5 actually draws, including the hard-coded `n = 8` in panel (a).
- Distinguished between what is directly shown in the figure asset versus what is claimed in manuscript prose; flagged only cases where the prose exceeded the visible/rendered support or the repository tree support.
- Interpreted `origin/copilot/design-channel-sealing-cap` as evidence for channel/outlet sealing concepts, not cartridge-sealing concepts, because the filenames and directories are cap-based rather than cartridge-based.
- Did not elevate non-Figure-5 problems (for example stale “load cell” labeling elsewhere) into the main inconsistency list, because the user asked to focus on Figure 5 internal consistency.