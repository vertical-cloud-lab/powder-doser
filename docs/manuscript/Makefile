# Build the powder-excavator design manuscript.
#
# Requirements:
#   * pdflatex + bibtex (TeX Live)
#   * cairosvg + Pillow (Python; pip install cairosvg Pillow)
#
# Targets:
#   make            -> build main.pdf
#   make figures    -> regenerate PDFs from the SVGs in ../figures/
#   make clean      -> remove build artifacts and converted PDFs
#   make distclean  -> additionally remove main.pdf

TEX     := pdflatex -interaction=nonstopmode -halt-on-error
BIBTEX  := bibtex
PYTHON  := python3

FIGDIR  := ../figures
SVGS    := $(wildcard $(FIGDIR)/panel-*.svg)
PDFS    := $(SVGS:.svg=.pdf)

.PHONY: all figures clean distclean
all: main.pdf

# Convert each SVG panel to a PDF that pdflatex can include. Done via
# cairosvg so the build has no system-level rsvg/inkscape dependency.
$(FIGDIR)/%.pdf: $(FIGDIR)/%.svg
	$(PYTHON) -c "import cairosvg; cairosvg.svg2pdf(url='$<', write_to='$@')"

figures: $(PDFS)

main.pdf: main.tex refs.bib $(PDFS)
	$(TEX) main
	$(BIBTEX) main
	$(TEX) main
	$(TEX) main

clean:
	rm -f main.aux main.log main.bbl main.blg main.out main.toc
	rm -f $(PDFS)

distclean: clean
	rm -f main.pdf
