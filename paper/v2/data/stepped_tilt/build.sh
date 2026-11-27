#!/usr/bin/env bash
# Rebuild the stepped-tilt tables and figure (no Python needed: gawk + pdflatex).
#   raw/          byte-identical copies of the 16 trials_summary.csv files (see README.md)
#   trials.csv    one row per trial, all 133          (tidy.awk)
#   summary.csv   one row per powder, final settings  (summary.awk)
#   plot_doses.csv  the 103 completed doses, with marker classes for the figure
# Optional first step, to refresh raw/ from PR #131's branch:
#   ./build.sh --fetch [ref]     (default ref 401815e, claude/issue-130-20260721-1807)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
if [[ "${1:-}" == "--fetch" ]]; then
  ref=${2:-401815e}
  root=$(git -C "$here" rev-parse --show-toplevel)
  rm -f "$here"/raw/*.csv
  git -C "$root" ls-tree -r --name-only "$ref" data/stepped-tilt-trials | grep 'trials_summary.csv$' |
    while read -r f; do
      git -C "$root" show "$ref:$f" > "$here/raw/$(echo "$f" | sed 's#data/stepped-tilt-trials/##; s#/#__#g')"
    done
fi
cd "$here"
gawk -f tidy.awk raw/*.csv > trials.csv
gawk -f summary.awk trials.csv > summary.csv
gawk -F, 'NR==1{print "x,y,t,cls"; next}
          $6=="final" && $19==1 {printf "%s,%s,%s,%s\n", $24, $23, $15, $3"-"$16"-"($21==1?"in":"out")}' \
  trials.csv > plot_doses.csv
cd ../..   # paper/v2
pdflatex -interaction=nonstopmode steppedtilt.tex > /dev/null && mv steppedtilt.pdf figures/steppedtilt.pdf
echo "trials: $(($(wc -l < data/stepped_tilt/trials.csv) - 1)), completed doses: $(($(wc -l < data/stepped_tilt/plot_doses.csv) - 1))"
