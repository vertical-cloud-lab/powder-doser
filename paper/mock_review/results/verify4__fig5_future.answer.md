Resolved vs round-1 issues for Fig. 5

1. Resolved
- Panel (a) is now explicitly eight-channel rather than ambiguously generic N-channel. Evidence: `make_figures.py:427` sets `n = 8`, `make_figures.py:448` titles panel (a) `8-channel radial array\n(concept)`, and the caption says `Eight-channel radial array concept (schematic)` (`caption_fig5_future.md:3`). This resolves the round-1 request to decide whether panel (a) was eight-channel or generic N-channel.
- The caption now clearly marks the figure as conceptual / exploratory future work. Evidence: caption lead `Future work: multi-powder doser` plus panel descriptors `concept (schematic)` and `Preliminary programmatic-CAD study` (`caption_fig5_future.md:3`). Panel titles in the PDF match: `(a) 8-channel radial array (concept)` and `(b) ... (preliminary CAD)`; same text is hard-coded at `make_figures.py:448` and `make_figures.py:454`.
- HUMAN vs AI attribution is now explicit, and the no-GUI-CAD point is stated. Evidence: `caption_fig5_future.md:3` says `the concept was set by the human team and the CAD modelled by AI coding agents; no GUI CAD package was used.` This directly addresses the PR request to clarify AI vs engineer contributions (`pr97_comments.md`, thread at `paper/main.tex line 189`).
- The earlier “single balance” overclaim in the caption is gone. The current caption contains no `balance` wording (`caption_fig5_future.md:3`). That fixes the round-1 provenance item that said to drop `on a single balance` unless one was rendered.
- Panel (b) is now honestly labeled as preliminary CAD rather than finished hardware. Evidence: `make_figures.py:454` and `caption_fig5_future.md:3` both call it `preliminary CAD` / `Preliminary programmatic-CAD study`.

2. Previously flagged issues not yet resolved
- The strongest overclaim in the body text is still present. `main.pdf` page 7 still says: `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.` Exact extracted text shown from `main.pdf` p. 7. This is still not supported by the supplied branch tree. The tree shows CAD for `design/cad/inward-collection-cup/` and sealing-cap branches under `origin/copilot/design-channel-sealing-cap`, plus `design/cad/single-channel-module/stl/cartridge.stl`, but it does not show a complete N-channel / multi-doser geometry CAD path. Relevant branch-tree paths include:
  - `design/cad/inward-collection-cup/cad_model.py`
  - `design/cad/inward-collection-cup/inward_collection_cup_iso.png`
  - `design/cad/inward-collection-cup/inward_collection_cup_top.png`
  - branch `origin/copilot/design-channel-sealing-cap`
  - `design/cad/sealing-cap-bayonet-plug/cad_model.py`
  - `design/cad/sealing-cap-spring-hatch/cad_model.py`
  - `design/cad/sealing-cap-twist-shutter/cad_model.py`
  - `design/cad/single-channel-module/stl/cartridge.stl`
  That supports early cup and sealing-cap concepts, not the body’s broader `multi-doser geometry ... already have working CAD` claim.
- Provenance for panel (a) is still not documented in-source. Panel (a) is drawn directly in matplotlib in `make_figures.py:422-448`; there is still no file-level note in the source tying it to a repository CAD path because it is not CAD-backed. So the round-1 provenance concern remains unless the manuscript explicitly calls it a manuscript schematic. Right now the caption does call it a `schematic`, which helps, but `make_figures.py` still has no provenance comment for this panel.
- `make_figures.py` still lacks a provenance comment for panel (b). Round-1 suggested recording that the asset comes from the inward-collection-cup CAD. The current code only says `# (b) inward-tilting collection-cup render` (`make_figures.py:450`) and then loads `inward_collection_cup_iso.png` (`make_figures.py:452`). It does not cite the branch-tree source path `design/cad/inward-collection-cup/cad_model.py`.
- The future-work prose is still flagged by the HUMAN PR note as unstable: `The future work has changed a bit, but progress here has not yet been reported on Github. This section and its figures will be changed as updated information is uploaded.` (`pr97_comments.md`, thread at `paper/main.tex line 258`). Nothing in the supplied revised bundle resolves that repository-reporting gap.
- Dimensions / engineering annotations are still absent. Neither the PDF nor the caption gives channel spacing, tilt angle, cup diameter, or any scale. This was flagged in round 1 and remains true.

3. Remaining concrete inconsistencies or unsupported claims that can be fixed without new bench data
- Body-text overclaim about repository CAD remains the biggest fixable problem. As noted above, `main.pdf` p. 7 says `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.` The branch tree supports only a shared-cup CAD study plus sealing-cap concepts. A tighter, file-grounded rewrite would point only to the paths actually evidenced in `all_branches_file_tree.txt`, especially `design/cad/inward-collection-cup/` and the sealing-cap directories on `origin/copilot/design-channel-sealing-cap`.
- `cartridge-sealing` is not the terminology best supported by the tree. The actual branch is `origin/copilot/design-channel-sealing-cap`, and the files are under `design/cad/sealing-cap-*`. There is a `design/cad/single-channel-module/stl/cartridge.stl`, but that alone does not substantiate a developed `cartridge-sealing` CAD concept. This is a wording fix, not a data issue.
- Panel (a) and the Section 4 prose are still slightly out of sync on channel count. The figure/caption commit to eight channels (`make_figures.py:427`, `caption_fig5_future.md:3`), while the body says `N printed channels ... with a loaded subset of 8–12 powders` (`main.pdf` p. 7 extract). That is not fatal, but it leaves the architecture underspecified. Either keep panel (a) explicitly as an eight-channel example and say so in the prose, or make the schematic visually generic and remove `8-channel`.
- Panel (b) still lacks explicit source signposting in the code. Since the figure relies on `assets/inward_collection_cup_iso.png`, a short code comment naming the candidate upstream branch-tree source would make the provenance auditable: `design/cad/inward-collection-cup/cad_model.py`, `.../inward_collection_cup_iso.png`, and `.../inward_collection_cup_top.png` from the branch tree.
- The caption’s AI/HUMAN attribution is good, but it is figure-global rather than panel-specific. Since panel (a) is a manuscript schematic and panel (b) is a CAD render, a cleaner caption would separate them: humans set the architecture for both; panel (a) is a schematic drawn for the manuscript; panel (b) is a programmatic CAD render. That would reduce ambiguity about whether panel (a) is also CAD-backed.
- The figure still does not tell the reader whether panel (b) is a full array design or an exploratory convergence study. The title `Inward-tilting channels over shared cup (preliminary CAD)` is close, but the caption could be a bit sharper: say `preliminary layout study` or `preliminary convergence study` if that is what is meant. This is implementable from current files alone.
- Candidate supporting files exist in the branch tree but are not yet used. If you want a more defensible CAD-backed Fig. 5 without new experiments, likely relevant paths named in `all_branches_file_tree.txt` are:
  - `design/cad/inward-collection-cup/inward_collection_cup_top.png`
  - `design/cad/inward-collection-cup/sketch_top_side.png`
  - `design/cad/inward-collection-cup/README.md`
  Those would help align the schematic/CAD story and document geometry better.

Short prioritized action list
- Rewrite the Section 4 sentence in `main.pdf` / `main.tex` so it matches the repository evidence: cite only the shared-cup CAD study and sealing-cap concept files actually represented in `all_branches_file_tree.txt`.
- Replace `cartridge-sealing concepts` with wording grounded in the tree, likely `sealing-cap concepts` or similarly narrow language.
- Make the prose and panel (a) agree on channel count: either commit to eight channels throughout or make panel (a) generic.
- Tighten panel (b) caption wording from broad `study of inward-tilting channels` to `preliminary layout/convergence CAD study` if that is the intended claim.
- Add a provenance comment in `make_figures.py` above panel (b) naming `design/cad/inward-collection-cup/cad_model.py` and companion render files from the branch tree.
- If space permits, swap in or add a top-view asset named in the branch tree, especially `design/cad/inward-collection-cup/inward_collection_cup_top.png` or `sketch_top_side.png`, to better connect the eight-channel schematic to the CAD-backed content.

- Discretionary analytical decisions made during the analysis
- Treated the supplied revised evidence set (`fig5_future.pdf`, `caption_fig5_future.md`, `make_figures.py`, `main.pdf`, `pr97_comments.md`, `all_branches_file_tree.txt`, and `assets/inward_collection_cup_iso.png`) as the only admissible basis for claims.
- Used the compiled manuscript text in `main.pdf` as authoritative for the current body-language under review, even though only the figure bundle rather than `main.tex` source was supplied.
- Counted an item as resolved when the revised figure/caption/source clearly removed or narrowed the exact earlier overclaim, even if broader future-work concerns remained.
- Treated branch-tree paths as evidence of repository scope and candidate provenance, but did not assume contents of unbundled files beyond what their names support.
- Did not press the known synthetic-placeholder issue for dispensing data, per the user’s instruction to leave that out here.