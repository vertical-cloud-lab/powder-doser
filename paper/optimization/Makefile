# Build the optimization manuscript.  Needs pdflatex + bibtex (MiKTeX or TeX Live)
# and, for `make figures`, python3 with numpy, pandas and matplotlib.
LATEX ?= pdflatex
FLAGS  = -interaction=nonstopmode -halt-on-error

.PHONY: all figures stills refs clean

all: main.pdf

main.pdf: main.tex refs.bib $(wildcard figures/*.pdf)
	$(LATEX) $(FLAGS) main
	bibtex main
	$(LATEX) $(FLAGS) main
	$(LATEX) $(FLAGS) main

figures:
	python3 figures/make_figures.py
	python3 figures/make_overview_relations.py
	python3 figures/make_overview_relations.py --board
	python3 figures/make_overview_relations.py --flat

# 3D stills for the overview figure.  Needs pyvista, vtk, cadquery and an X display, plus the
# PR #190 render scripts and the PR #170 doser CAD (POWDER_TESTS, DOSER_CAD; see the script).
stills:
	xvfb-run -a python3 figures/render3d/render_stills.py

refs:
	python3 scripts/validate_refs.py refs.bib

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.spl *.toc *.fls *.fdb_latexmk
