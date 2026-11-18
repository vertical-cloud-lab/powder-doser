#!/bin/bash
# pdflatex from MiKTeX's official Docker image, for runners where the MiKTeX apt
# package does not install (Ubuntu 26.04: its "noble" build needs libicu74 and Qt
# packages that 26.04 no longer has).  Install once as ~/bin/pdflatex:
#
#     docker pull miktex/miktex:essential
#     install -m 755 paper/v2/tools/pdflatex-miktex-docker.sh ~/bin/pdflatex
#
# build_figures.py falls back to ~/bin/pdflatex when pdflatex is not on PATH.
# LaTeX packages install on first use and persist in the "miktex" Docker volume.
# The image's entrypoint never applies MIKTEX_UID (it only remaps when the user is
# not already uid 1000), so the user is remapped here; otherwise the container
# cannot write the .log/.pdf into a work directory owned by the runner's user.
# On a fresh volume, first run (as below, with "bash -c"):
#     miktex packages update-package-database; miktex packages update;
#     initexmf --set-config-value '[MPM]AutoInstall=1'
U=$(id -u); G=$(id -g)
exec docker run --rm -v miktex:/var/lib/miktex -v "$PWD":/miktex/work -w /miktex/work \
  --entrypoint bash miktex/miktex:essential -c \
  "groupmod -o -g $G miktex && usermod -o -u $U -g $G miktex >/dev/null && chown -R miktex:miktex /var/lib/miktex && exec gosu miktex pdflatex \"\$@\"" pdflatex "$@"
