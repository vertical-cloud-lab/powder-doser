# Edits that apply to the arXiv version only. make_arxiv.sh runs them on the body of
# ../main.tex, after the \input tables are inlined and before comments are stripped.
# Each edit says why. To post the journal wording unchanged, delete the edits and rerun.
#
# Data availability. On 28 Nov 2026 nothing was archived on Zenodo (zenodo.org has no record;
# the upload was tested on the sandbox only) and the repository had no v1.0.0 tag or release,
# so the preprint does not claim either. The journal version keeps both for the release
# planned at submission (main.tex TODO; SUBMISSION-DECISIONS.md item 11). If v1.0.0 is
# archived before the preprint is posted, delete these three edits and put the DOI in the
# Charles2026Release entry of ../references.bib.
s| and in its archived release on Zenodo\.\\cite{Charles2026Release}|. A tagged release of the repository will be archived on Zenodo.|
s|can be found at the same repository and release\.|can be found in the same repository.|
s| The version of the code employed for this study is version 1\.0\.0\.||
# Experimental. The session logs downloaded in October are attached to an unpublished draft
# release that only people with write access can see, not to a public archive yet.
s|were downloaded then and are part of the archived release\.|were downloaded then and will be part of the archived release.|
# Data availability, Onshape. On 28 Nov 2026 all 12 Onshape documents on the project page
# opened for an anonymous client, but Onshape marks three of them as link-shared rather than
# public, and the page links to the print settings (issue #193) rather than listing them.
s|The current parts are public Onshape documents, listed with their print settings on the project page (\\url{https://vertical-cloud-lab.github.io/powder-doser/})|The current parts are Onshape documents that anyone can open, listed on the project page (\\url{https://vertical-cloud-lab.github.io/powder-doser/}), which links to their print settings|
# Data availability, SI Table of parts. The tap-collar base is AI-modelled and links to its
# STEP file on GitHub, not to Fusion 360, so not every part has a Fusion 360 link.
s|and each printed part tested has a public Fusion~360 link (SI Table~\\siref{tbl:parts})|and each printed part tested has a public link to its design file (SI Table~\\siref{tbl:parts})|
