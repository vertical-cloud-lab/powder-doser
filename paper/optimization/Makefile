# Build the optimization manuscript.  Needs pdflatex + bibtex (MiKTeX or TeX Live)
# and, for `make figures`, python3 with numpy, pandas and matplotlib.
LATEX ?= pdflatex
FLAGS  = -interaction=nonstopmode -halt-on-error

.PHONY: all figures refs clean

all: main.pdf

main.pdf: main.tex refs.bib $(wildcard figures/*.pdf)
	$(LATEX) $(FLAGS) main
	bibtex main
	$(LATEX) $(FLAGS) main
	$(LATEX) $(FLAGS) main

figures:
	python3 figures/make_figures.py
	python3 figures/make_overview_relations.py

refs:
	python3 scripts/validate_refs.py refs.bib

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.spl *.toc *.fls *.fdb_latexmk
