Resolved in the revised Fig. 5

- The figure now clearly distinguishes schematic vs CAD-backed content at the panel-title level. Panel (a) is titled `N-channel radial array (concept)` and panel (b) `Inward-tilting channels over shared cup (CAD)` in `fig5_future.pdf`; the same wording is generated in `make_figures.py` (`def fig5()`, titles set by `ax.set_title(...)`). This addresses the earlier request to mark the figure as conceptual/exploratory rather than validated hardware. The caption also now opens `Future work: multi-powder doser.` in `caption_fig5_future.md`.

- The earlier panel-(b) wording problem is substantially improved. The current panel (b) asset actually shows inward-tilting channels converging over a central cup, not just an isolated cup. Evidence: `assets/inward_collection_cup_iso.png` visibly contains multiple tilted cylindrical channels arranged around a central cup; `make_figures.py` uses that exact asset in panel (b) via `show(ax, "inward_collection_cup_iso.png")`; the exported `fig5_future.pdf` title reads `Inward-tilting channels over shared cup (CAD)`. That is much better aligned than the round-1 complaint summarized in `round1_CONSOLIDATED.md` under `fig5_future → narrative`, which said panel (b) had been mislabeled as channels-over-cup when it effectively showed only the cup.

- The figure/caption now explicitly says panel (a) is a concept and panel (b) is CAD. That partially resolves the round-1 request in `round1_CONSOLIDATED.md` (`fig5_future → improvement` and `signposting`) to distinguish CAD-backed content from architecture schematics.

Not yet resolved from the previously flagged issues

- The `single balance` claim is still unsupported by panel (a). The caption still says `(a) N-channel radial array concept around a shared collection cup on a single balance` in `caption_fig5_future.md`, and the compiled `main.pdf` repeats the same text. But panel (a) in `fig5_future.pdf` shows only eight blue channel blocks around a labeled `shared cup`; there is no balance drawn or labeled. This was explicitly flagged in `round1_CONSOLIDATED.md` under `fig5_future → provenance`: `Drop "on a single balance" from caption (a) or render a balance into the schematic.` That issue remains.

- The `N-channel` label is still inconsistent with the code-determined visible count in panel (a). `make_figures.py` hard-codes `n = 8` in `fig5()`, then draws eight rectangles around the cup, while the title remains `N-channel radial array (concept)` and the caption remains `$N$-channel radial array concept...`. This was the exact round-1 issue in `round1_CONSOLIDATED.md` under `fig5_future → consistency`: `Decide whether panel (a) is 8-channel or generic N-channel: either relabel it as eight-channel or redraw it to look generic.` Not fixed.

- The manuscript still overclaims repository support for the future-work hardware. `main.pdf` still says: `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository.` The supplied branch tree does support `design/cad/inward-collection-cup/` and sealing-cap branches such as `origin/copilot/design-channel-sealing-cap -> design/cad/sealing-cap-bayonet-plug/`, `.../sealing-cap-spring-hatch/`, and `.../sealing-cap-twist-shutter/`. But the branch tree does not show a complete N-channel multi-doser CAD directory analogous to panel (a); the only directly relevant geometry path is `design/cad/inward-collection-cup/`, plus a background note on `origin/copilot/zoo-design-studio-multi-doser -> paper/background/15-zoo-design-studio-multi-doser.md`. This was flagged in `round1_CONSOLIDATED.md` under `fig5_future → consistency`, `provenance`, and `narrative`. It remains unresolved.

- `Cartridge-sealing concepts` is still loose/inaccurate against the supplied tree. The branch tree shows a `design/cad/single-channel-module/stl/cartridge.stl`, and separately several `sealing-cap-*` concepts on `origin/copilot/design-channel-sealing-cap`. That supports outlet/channel sealing-cap concepts, not clearly `swappable sealed cartridges` as claimed in `main.pdf` Section 4. This was flagged in `round1_CONSOLIDATED.md` (`fig5_future → consistency` and `narrative`) and remains unresolved.

- Panel (a) and panel (b) still do not cleanly depict the same architecture. Panel (a) is a full 360° radial top-view schematic with eight evenly spaced channels. Panel (b) is an oblique CAD render showing a partial fan of inward-tilting channels over a shared cup, not a clear full radial array. Round 1 asked to `Make panel (a) and panel (b) describe the same channel count and architecture` (`round1_CONSOLIDATED.md`, `fig5_future → reviewer`). That is still not fixed.

- AI-vs-HUMAN attribution for this figure is still absent. The caption file contains no attribution language, and the `fig5()` block in `make_figures.py` contains no provenance comment tying panel (b) to `design/cad/inward-collection-cup/cad_model.py` or clarifying that the panel-(a) schematic is manuscript-drawn while panel (b) is repository CAD. This was requested in `round1_CONSOLIDATED.md` under `fig5_future → provenance` and `signposting`, and it remains unresolved.

Remaining concrete inconsistencies or unsupported claims that can be fixed without new bench data

- Caption vs drawing mismatch for `single balance`. The easiest fix is textual: remove `on a single balance` from `caption_fig5_future.md` and the corresponding manuscript caption unless a balance is actually drawn. Right now neither panel visibly shows one.

- Code/title mismatch for channel count. Because `make_figures.py` explicitly sets `n = 8`, either:
  - change the title/caption from `N-channel` to `8-channel`, or
  - rewrite panel (a) so it is visibly generic rather than exactly eight-fold.
  As written, the code makes a specific eight-channel schematic while the text advertises an arbitrary N.

- Section 4 repository-claim overreach. In `main.pdf`, replace `the multi-doser geometry and the cartridge-sealing concepts already have working CAD in the repository` with wording grounded in the supplied tree, e.g. early CAD studies exist for the shared-cup concept and sealing-cap concepts. Concrete branch-tree support you can cite: `design/cad/inward-collection-cup/README.md`, `design/cad/inward-collection-cup/cad_model.py`, `design/cad/inward-collection-cup/inward_collection_cup_iso.png`, `design/cad/inward-collection-cup/inward_collection_cup_top.png`, and the sealing-cap directories on `origin/copilot/design-channel-sealing-cap`.

- `Swappable sealed cartridges` is not adequately supported by the supplied repository evidence for this figure. If kept in Section 4, it should be narrowed to what the branch tree actually supports, or separated from the present figure so the figure is not made to imply that cartridge hardware is already designed at the multi-doser level.

- Panel (b) should be labeled more narrowly as a positional/layout CAD study unless you add annotations. The current title `Inward-tilting channels over shared cup (CAD)` is much better than before, but the render still does not show dimensions, channel count clearly, or balance integration. A more conservative wording would be `Shared-cup inward-tilt CAD study` or `Preliminary CAD study of inward-tilting channels over a shared cup`.

- The figure still lacks direct provenance signposting. A fix that needs no new experiments: add one sentence in the caption stating that panel (a) is a manuscript schematic and panel (b) is a CAD render generated from the repository’s `design/cad/inward-collection-cup/` study; HUMAN contribution was review/selection/curation, AI contribution was code/CAD generation. Per your instruction, keep this only at HUMAN vs AI and do not name individuals.

- If you want repository traceability from the figure source itself, add a comment in `make_figures.py` above panel (b) pointing to the branch-tree path `design/cad/inward-collection-cup/cad_model.py`. Round 1 asked for this because reviewers wanted AI-use claims to be auditable from GitHub.

- The architecture logic is still underexplained. The shared-cup idea is visible, but the figure does not explain how a single shared cup interfaces with the balance or how cross-contamination/spillover is mitigated. You do not need bench data to fix this. A short caption clause or a small callout can flag these as future engineering considerations rather than silently implying they are solved.

Prioritized action list

1. Remove or justify `on a single balance` in panel (a) caption; right now it is not shown.
2. Resolve `N-channel` vs hard-coded `n = 8` by either relabeling as `8-channel` or redrawing panel (a) to be genuinely generic.
3. Soften the Section 4 sentence in `main.pdf` claiming `working CAD` for `multi-doser geometry` and `cartridge-sealing concepts`; ground it in the actual branch-tree paths.
4. Add one explicit HUMAN-vs-AI provenance sentence to the caption, and optionally a source comment in `make_figures.py` for panel (b) pointing to `design/cad/inward-collection-cup/`.
5. Tighten panel (b) wording to `preliminary CAD study` or similar unless you add annotations that support a stronger architectural claim.
6. Add one brief callout or caption clause on unresolved system-level risks/logic for the shared-cup design: spillover, cross-contamination, and single-balance operation.

- Discretionary analytical decisions made during the analysis
- Treated `fig5_future.pdf`, `caption_fig5_future.md`, `make_figures.py`, `assets/inward_collection_cup_iso.png`, `main.pdf`, `pr97_comments.md`, and `round1_CONSOLIDATED.md` as the primary evidence base, using `all_branches_file_tree.txt` only to name repository-supported paths and branches.
- Counted a round-1 issue as resolved when the revised figure/caption/source now matched each other and no longer made the specific earlier mismatch, even if the panel could still be improved further.
- Treated the visible geometry generated by `make_figures.py` (`n = 8`) as stronger evidence than the generic `N-channel` wording when judging internal consistency.
- Treated branch-tree paths such as `design/cad/inward-collection-cup/` and `origin/copilot/design-channel-sealing-cap` as evidence of file existence only, not proof of uninspected contents beyond what filenames support.
- Classified the absence of AI-vs-HUMAN attribution as a remaining signposting/provenance problem rather than a geometry inconsistency, because it does not change what the figure depicts but does affect auditability.