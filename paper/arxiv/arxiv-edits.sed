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
