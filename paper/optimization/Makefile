# Build the optimization manuscript.  Needs pdflatex + bibtex (MiKTeX or TeX Live)
# and, for `make figures`, python3 with numpy, pandas and matplotlib.
LATEX ?= pdflatex
FLAGS  = -interaction=nonstopmode -halt-on-error

.PHONY: all figures stills refs contact clean analysis export docker-pdf

all: main.pdf si.pdf

main.pdf: main.tex refs.bib $(wildcard figures/*.pdf)
	$(LATEX) $(FLAGS) main
	bibtex main
	$(LATEX) $(FLAGS) main
	$(LATEX) $(FLAGS) main

# Statistics, model checks and SI tables from the dose records in data/ (numpy, pandas, scipy;
# gp_diagnostics also needs botorch[fully_bayesian], about 10 min on a laptop CPU)
analysis:
	python3 analysis/opt_stats.py
	python3 analysis/gp_diagnostics.py
	python3 analysis/si_tables.py

# Re-export the MongoDB snapshot (needs MONGODB_URI and pymongo)
export:
	python3 analysis/export_opt_trials.py

si.pdf: si.tex $(wildcard analysis/results/tables/*.tex) figures/figS_gp_cv.pdf
	$(LATEX) $(FLAGS) si
	$(LATEX) $(FLAGS) si

# Same build with MiKTeX in Docker, for machines without a TeX install (the MiKTeX .deb does
# not install on Ubuntu 26.04).  Copies the directory to a scratch dir the container can write.
docker-pdf:
	rm -rf /tmp/texwork && cp -r . /tmp/texwork && chmod -R a+rwX /tmp/texwork
	docker run --rm -v /tmp/texwork:/miktex/work miktex/miktex:latest bash -c \
	  "initexmf --set-config-value [MPM]AutoInstall=1; mpm --update-db; \
	   pdflatex -interaction=nonstopmode main; bibtex main; pdflatex -interaction=nonstopmode main; \
	   pdflatex -interaction=nonstopmode main; pdflatex -interaction=nonstopmode si; pdflatex -interaction=nonstopmode si"
	cp /tmp/texwork/main.pdf /tmp/texwork/si.pdf .

figures:
	python3 figures/make_figures.py
	python3 figures/make_overview_relations.py

# 3D stills for the overview figure.  Needs pyvista, vtk, cadquery and an X display, plus the
# PR #190 render scripts and the PR #170 doser CAD (POWDER_TESTS, DOSER_CAD; see the script).
stills:
	xvfb-run -a python3 figures/render3d/render_stills.py

refs:
	python3 scripts/validate_refs.py refs.bib

# Contact sheet of every page of main.pdf (needs pdftoppm from poppler-utils and Pillow)
contact: main.pdf
	python3 scripts/contact_sheet.py main.pdf contact_sheet.png --cols 6 --dpi 50

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.spl *.toc *.fls *.fdb_latexmk
