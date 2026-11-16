# Build the optimization manuscript.  Needs pdflatex + bibtex (MiKTeX or TeX Live)
# and, for `make figures`, python3 with numpy, pandas and matplotlib.
LATEX ?= pdflatex
FLAGS  = -interaction=nonstopmode -halt-on-error

.PHONY: all figures refs contact clean

all: main.pdf

main.pdf: main.tex refs.bib $(wildcard figures/*.pdf)
	$(LATEX) $(FLAGS) main
	bibtex main
	$(LATEX) $(FLAGS) main
	$(LATEX) $(FLAGS) main

figures:
	python3 figures/make_figures.py

refs:
	python3 scripts/validate_refs.py refs.bib

# Contact sheet of every page of main.pdf (needs pdftoppm from poppler-utils and Pillow)
contact: main.pdf
	python3 scripts/contact_sheet.py main.pdf contact_sheet.png --cols 6 --dpi 50

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.spl *.toc *.fls *.fdb_latexmk
