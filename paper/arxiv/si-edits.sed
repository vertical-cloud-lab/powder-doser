# Edits to ../si.tex for the arXiv copy of the SI (anc/si.pdf) only. If this file has any
# line that is not a comment, make_arxiv.sh builds the SI from an edited copy of si.tex
# instead of copying ../si.pdf. Each edit says why.
#
# AI usage log. The session logs downloaded in October are attached to an unpublished draft
# release that only people with write access can see, not to a public archive yet (28 Nov 2026).
s|were downloaded then and are part of the archived release\.|were downloaded then and will be part of the archived release.|
# Construction guide. The Onshape assembly cited here (ae9f107d...) returned 403 to an
# anonymous client on 28 Nov 2026, and the animation is on the project page, not in the README
# on main. The project page lists the current parts and a public assembly of them.
s|^the build in 19 steps\. Both come from a CAD assembly of the team's part files,$|the build in 19 steps. Both come from a CAD assembly of the team's part files;|
/^which is also a public Onshape document$/d
s|^(\\url{https://cad.onshape.com/documents/ae9f107d3972fc9d390e541f}); the same$|the current parts and an assembly of them are Onshape documents listed on the project page (\\url{https://vertical-cloud-lab.github.io/powder-doser/}), which also animates the same|
s|^steps are animated in the repository README\. The wiring guide and firmware are$|steps. The wiring guide and firmware are|
