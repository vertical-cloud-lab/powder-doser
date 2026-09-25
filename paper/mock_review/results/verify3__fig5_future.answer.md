Resolved items from round 1

1. The 8-channel vs generic-N mismatch is resolved.
- In `make_figures.py`, `fig5()` hard-codes `n = 8` for panel (a), and the panel title is now `8-channel radial array\n(concept)`.
- The exported figure text in `fig5_future.pdf` matches that title: `8-channel radial array (concept)`.
- The caption now matches too: `caption_fig5_future.md` says `(a) Eight-channel radial array concept around a shared collection cup.`
- This fixes the round-1 consistency issue that panel (a) visually/code-wise showed eight channels while the wording had been more generic.

2. The prior “single balance” overclaim is resolved.
- Round 1 flagged caption wording that implied the array was `on a single balance` without such a balance being shown.
- The revised caption in `caption_fig5_future.md` now says only: `(a) Eight-channel radial array concept around a shared collection cup.`
- Neither `caption_fig5_future.md` nor `make_figures.py::fig5()` mentions a balance.
- The current `fig5_future.pdf` also contains no balance label.

3. Panel (b) is now described more cautiously as preliminary CAD, and that wording matches the visible panel.
- `caption_fig5_future.md`: `(b) Preliminary CAD study of inward-tilting channels over the shared cup.`
- `make_figures.py::fig5()` sets panel (b) title to `Inward-tilting channels\nover shared cup\n(preliminary CAD)`.
- The supplied asset `assets/inward_collection_cup_iso.png` does in fact show multiple inward-tilting channel/tube geometries converging toward a central cup region, so the revised caption/title now matches the render better than the round-1 versions did.
- Relevant branch-tree provenance path: `design/cad/inward-collection-cup/inward_collection_cup_iso.png` in `all_branches_file_tree.txt`.

4. The figure now clearly signals concept status for panel (a) and preliminary status for panel (b).
- Panel (a) title in `fig5_future.pdf`: `8-channel radial array (concept)`.
- Panel (b) title: `Inward-tilting channels over shared cup (preliminary CAD)`.
- Caption lead in `caption_fig5_future.md`: `Future work: multi-powder doser.`
- That addresses the round-1 request to mark the figure as exploratory rather than validated hardware, at least at figure/caption level.

Previously flagged issues not yet resolved

1. The manuscript body still overclaims repository support for the full multi-doser geometry.
- In `main.pdf` Section 4, the text still says: `Each will be reported separately; the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.`
- The branch tree does support the inward-cup CAD study and sealing-cap concepts, but not a clearly named full N-channel multi-doser repository path.
- Relevant branch-tree evidence:
  - `design/cad/inward-collection-cup/README.md`
  - `design/cad/inward-collection-cup/cad_model.py`
  - `design/cad/inward-collection-cup/inward_collection_cup_iso.png`
  - `design/cad/inward-collection-cup/inward_collection_cup_top.png`
  - branch `origin/copilot/design-channel-sealing-cap` with paths such as `design/cad/sealing-cap-bayonet-plug/...` and `design/cad/sealing-cap-spring-hatch/...`
- I do not see, in `all_branches_file_tree.txt`, a correspondingly explicit multi-channel or multi-doser CAD directory for the full array architecture. The only branch name hint is `origin/copilot/zoo-design-studio-multi-doser`, but its listed files are manuscript/background files, not CAD assets.
- So the round-1 “soften the certainty / stop saying the full multi-doser geometry already has working CAD in the repository” issue is still open.

2. The round-1 request to align Section 4 with the HUMAN review note is still not resolved.
- `pr97_comments.md`, thread `paper/main.tex line 258 (Future work) — @swcharles`: `The future work has changed a bit, but progress here has not yet been reported on Github. This section and its figures will be changed as updated information is uploaded.`
- The current Section 4 sentence in `main.pdf` remains assertive: `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.`
- That is still in tension with the review comment above.

3. The figure still does not add HUMAN-vs-AI attribution for this future-work concept.
- Round 1 repeatedly asked for AI-vs-human signposting across the manuscript and specifically suggested adding provenance/signposting for Fig. 5.
- `caption_fig5_future.md` contains only two neutral descriptive sentences; it does not say whether panel (a) is a manuscript schematic, whether panel (b) is an AI-authored programmatic CAD render under human review, or that no GUI CAD package was used.
- This matters because `pr97_comments.md` at `paper/main.tex line 189` says: `Throughout this section, clarify where ai was used. We should be signposting the design contributions of ai versus engineers throughout the manuscript--it should always be clear who did what.`
- The current revised figure still does not do that.

Remaining concrete inconsistencies or unsupported claims that can be fixed without new bench data

1. Section 4 should stop implying that the whole multi-doser architecture is already CAD-backed in the repository.
- Current body text in `main.pdf`: `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.`
- What the supplied branch tree concretely supports is narrower:
  - a shared-cup / inward-tilting-channel CAD study under `design/cad/inward-collection-cup/`
  - sealing-cap concepts under branch `origin/copilot/design-channel-sealing-cap`
  - a `design/cad/single-channel-module/stl/cartridge.stl`
- A safer manuscript claim would name those specific artifacts instead of claiming the full multi-doser geometry is already repository-backed.

2. The caption could better distinguish schematic vs CAD-backed content.
- Panel (a) is drawn directly in `make_figures.py` with Matplotlib patches, not loaded from a CAD asset:
  - `make_figures.py::fig5()` constructs rectangles and a circle for panel (a), with `n = 8`.
- Panel (b) is a loaded CAD render asset:
  - `show(ax, "inward_collection_cup_iso.png")` in `make_figures.py::fig5()`.
- Right now the caption does not make that distinction explicit. A reviewer can infer it, but the provenance is cleaner if stated.

3. The caption still misses the requested HUMAN vs AI signposting.
- This can be fixed without new measurements.
- A defensible wording, grounded in the supplied files, would say that panel (a) is a concept schematic assembled for the manuscript, panel (b) is a programmatic CAD study from the repository, and that humans reviewed/curated the concepts while AI coding agents authored parametric CAD code where applicable.
- Per the user’s instruction, attribution should remain HUMAN vs AI only, and should not mention any GUI CAD package because `pr97_comments.md` explicitly says none was used.

4. Provenance for panel (b) can be made explicit in caption or SI.
- The branch tree provides exact candidate source paths that can be cited:
  - `design/cad/inward-collection-cup/README.md`
  - `design/cad/inward-collection-cup/cad_model.py`
  - `design/cad/inward-collection-cup/inward_collection_cup_iso.png`
  - `design/cad/inward-collection-cup/inward_collection_cup_top.png`
  - `design/cad/inward-collection-cup/sketch_2d.py`
  - `design/cad/inward-collection-cup/sketch_top_side.png`
- If the manuscript wants the “working CAD in repository” claim to survive in any form, citing these exact paths would make it auditable.

5. The future-work prose should be narrowed to what this revised figure actually shows.
- Figure 5 shows:
  - panel (a): an 8-channel radial concept around a shared cup
  - panel (b): a preliminary inward-tilting shared-cup CAD study
- It does not show:
  - swappable sealed cartridges
  - a 50-powder pool architecture
  - control/arbitration for many channels on one weighing system
- Those ideas may belong in Section 4, but they are not supported by Figure 5 itself and should not be presented as figure-backed unless separately sourced.

Short prioritized action list

1. Rewrite the Section 4 sentence in `main.pdf` so it names the specific repository-backed pieces (`design/cad/inward-collection-cup/...` and the sealing-cap branch) instead of claiming the full `multi-doser geometry` already has working CAD in the repository.
2. Add one caption sentence distinguishing panel (a) as a concept schematic and panel (b) as a preliminary programmatic CAD render from the repository.
3. Add one brief HUMAN-vs-AI provenance clause for Figure 5, consistent with `pr97_comments.md` line-189 guidance and the project rule that only programmatic CAD / Zoo exploratory use occurred.
4. If keeping the broader future-work claims in Section 4, explicitly separate what is shown in Fig. 5 from what is only proposed (sealed cartridges, 50-powder pool, single-weighing-system logistics).
5. Optionally cite the exact branch-tree paths for panel (b) in caption or SI: `design/cad/inward-collection-cup/cad_model.py`, `.../inward_collection_cup_iso.png`, `.../inward_collection_cup_top.png`, and `.../sketch_top_side.png`.

- Discretionary analytical decisions made during the analysis
- Treated the supplied revised figure artifact set (`fig5_future.pdf`, `caption_fig5_future.md`, `make_figures.py`, `assets/inward_collection_cup_iso.png`, `main.pdf`, `pr97_comments.md`, `all_branches_file_tree.txt`) as the complete admissible evidence base.
- Used the compiled `main.pdf` as the authoritative source for the current Section 4 wording, while using `make_figures.py` as the authoritative source for what the revised figure actually draws.
- Counted a round-1 issue as resolved only when the revised PDF/caption/code now agreed with each other, not merely when the wording became vaguer.
- Treated branch-tree paths as evidence of repository file existence and provenance candidates, but did not assume unseen file contents beyond what the supplied filenames support.
- Interpreted the visible `assets/inward_collection_cup_iso.png` render as supporting the revised panel-(b) wording because the render now visibly includes multiple inward-tilting channels over a central cup region.