## Narrative role of fig2_genai (Figure 3 in the compiled PDF)

### The job this figure does

The paper makes two co-equal claims: a sub-$200 single-channel auger doser, and a methodological claim that AI-mediated CAD — with no GUI package ever opened — can produce a working instrument if you decompose the problem. The authors flag this explicitly: "The second, equally deliberate contribution of this work is methodological" (p. 2), and again in the Conclusions: "The methodological result is as transferable as the hardware: whole-assembly AI generation is not currently viable, but part-by-part generation against explicit interfaces, fortified by automated geometry checks and disciplined human review, is a practical and auditable way to design instruments" (p. 7).

fig2_genai is the only figure in the manuscript that provides visual evidence for that second claim. It is called out three times across Section 2.3 — once for the failure mode (panel a), once for the part-by-part success (panel c), and once for the silent-regression / stale-input case study (panels e–h) — covering exactly the three legs the prose argument rests on:

- panel (a) — "the first tap collar was an unimplementable amalgamation of separate functions … (Fig. 3a)"
- panel (c) — "Restricting each generation task to a single part … converted the agent from a liability into a productive collaborator (Fig. 3c)"
- panels (e–h) — "the agent proposed the raised-bracket solution to a gear-clearance problem we had misdiagnosed, Fig. 3e–h"

Panels (b) and (d) are not directly called out in the body, but they earn their seats: (b) gives the after-iteration comparator for (a) and is the only visual evidence in the paper of Zoo Design Studio output (which reviewer @swcharles emphasized in PR #97 — "Zoo Design Studio is regarded as the best option by the researchers"), and (d) is the visual exhibit for the central whole-assembly-fails claim. Without (d) the strongest sentence in the Conclusions has no picture behind it.

### Is the role coherent and non-redundant with the rest of the paper?

Yes. The closest candidates for overlap are Figure 1(e), the compressed 8-entry design timeline, and Figure 2 (PDF numbering — the "Design specifics" cross-section figure with the auger tube and split-clamp tap collar). They do different jobs:

- Fig. 1(e) names the four design generations as a chronology ("Apr 23 Scoop/excavator sketch … May 14 Part-by-part redesign … Jun 1 97-entry design log"). It is an index, not evidence. Nothing in it shows what an AI-generated part actually looked like, what failed, or what was fixed.
- Fig. 2 (PDF) shows the final mechanical geometry of the auger tube cross-section and the split-clamp tap collar — engineering documentation of the parts that ship, with no AI provenance content.
- fig2_genai is the only figure that shows AI outputs across iterations, side by side, with success and failure. Reusing render assets from elsewhere in the repo (auger_assembly_iso.png also feeds Fig. 1a context; single_channel_module_iso.png is the v2-module render also referenced for Fig. 1b) is asset-level reuse only; the figure's job — "what AI CAD looks like when it works and when it doesn't" — is not done anywhere else.

The PR #97 reviewer comments support this read: no reviewer asked to cut, merge, or move fig2_genai. The comments on it are factual ("a) is bad because of interferences, incorrect tolerancing, no space for relevant components … the 'not connected to its own mounting plate' issue is from the bracket in the original design — it doesn't make sense in relation to the tap collar"; and "we ended up resorting to zoo for the tap collar"). The current caption already incorporates both of those fixes — the (a) description was rewritten, and (b) now says "the production tap collar was subsequently redesigned in Zoo Design Studio (three iterations to a usable part)" — consistent with discussioncomment-17284756.

### Recommendation: KEEP in the main text. Do not move to SI, do not merge.

Justification grounded in the manuscript:

1. The paper's "equally deliberate" second contribution needs a main-text evidence figure or it is asserted but unsupported. fig2_genai is that figure.
2. It is the visual payload for three separately-developed body-text claims (a, c, e–h) and supplies the only main-text view of Zoo Design Studio output (b) — the tool the team judged "best of the tools tried" (p. 5).
3. There is no SI figure that covers any of this. The SI is BOM + nozzle variants + AI interaction logs; fig S1 is exit-nozzle variants only.
4. Removing it forces the reader to either trust the prose claims or read the 97-entry design log in the repository to verify them. That defeats the explicit goal of using this paper as a "documented case study of AI-assisted hardware design" (p. 2).

Moving it to SI is the worst option: it strands the figure that visually carries the second-contribution argument behind a separate PDF that most readers will not open.

Merging into Fig. 1 is feasible only if Fig. 1(e) is replaced with a 2-row evidence strip — but Fig. 1 is already the system-overview figure (a–d) and adding 8 more panels would push it past readability at single-column width. Better to keep them split.

### Issues to fix while keeping it (these are tractable, not arguments for cutting)

- Panel (d)'s in-figure title says "single prompt, v1 module," but Section 2.2 calls the whole-assembly attempt the second generation (v1 was the scoop/excavator hand-sketch); the asset comes from branch `origin/copilot/modular-single-channel-powder-doser-design` and is the v2-module ISO render. Change subtitle to "v2 module."
- Tension between the body text — "the agent proposed the raised-bracket solution to a gear-clearance problem we had misdiagnosed (Fig. 3e–h)" (p. 4) — and the caption — "The root cause was stale input files — a human-side error the agent silently designed around." The first frames (e–h) as an AI win; the second frames it as a stale-input regression. Both readings have repo support, but the figure can only show one. Pick one and align caption and body text.
- The figure is referenced as Figure 3 in the compiled PDF but as Figure 2 in the bundle (file name `fig2_genai.pdf`, caption file `caption_fig2_genai.md`, README "main.tex, Figure 2"). This is a numbering drift; whichever the authors intend, body callouts and caption labels must match the compiled output.
- Reviewer comment from @swcharles flags that "the 'not connected to its own mounting plate' issue is from the bracket in the original design — it doesn't make sense in relation to the tap collar." The current caption no longer claims that (it just lists tap-collar defects), so this looks resolved — confirm it stays resolved in the next rev.
- Panel (b) is the only figure-level reference to Zoo Design Studio in the paper. Per PR #97 (@swcharles: "Mention Zookeeper as a specific LLM used in Zoo Design Studio"), the (b) sub-caption could name Zookeeper rather than only "Zoo."

### Prioritized action list (this figure)

1. KEEP in the main text; do not move to SI or merge with Fig. 1.
2. Resolve the (e–h) framing conflict between body text ("agent proposed the raised-bracket solution") and caption ("agent silently designed around stale inputs"). Pick one story and align.
3. Fix panel (d) title from "v1 module" to "v2 module" to match Section 2.2 and the asset branch (`modular-single-channel-powder-doser-design`).
4. Reconcile the figure number across `fig2_genai.pdf` / `caption_fig2_genai.md` / `README.md` / main.tex callouts so file name, callouts, and compiled label agree.
5. In panel (b)'s caption add "via the Zookeeper agent" to make the only Zoo Design Studio main-text figure-callout name the agent (responding to @swcharles, PR #97 line 245).
6. Optional: add a brief subtitle annotation to (a) vs (b) explicitly tagging the workflow used for each ("whole-assembly programmatic CAD" vs "Zoo Design Studio / Zookeeper"), so a reader who skims only the figure can recover the central claim of Section 2.3.

### Discretionary decisions

- Used "Figure 3" when describing the figure's location in the compiled PDF and "fig2_genai" / "Figure 2" when referring to the bundle's naming; this avoids ambiguity but the manuscript itself must pick one.
- Treated reuse of `auger_assembly_iso.png` and `single_channel_module_iso.png` across figures as asset-level reuse rather than redundancy, because the framings and accompanying captions assign each instance a distinct narrative job. A stricter reviewer could call this duplication; I judged it acceptable.
- Recommended "keep in main text" rather than "keep with major surgery" because the three body-text callouts already correspond cleanly to specific panels; the issues I flag are editorial fixes, not structural ones.
- Did not recommend adding new panels (e.g. a CI-checks screenshot, an automated-self-check defect summary) even though Section 2.3 mentions them, because the manuscript states a quantitative analysis "is reported in the repository and will accompany the multi-doser follow-up" — i.e. the authors have already deferred that to a later paper.
