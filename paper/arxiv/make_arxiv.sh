#!/usr/bin/env bash
# Build the arXiv preprint bundle from the journal sources in paper/.
#
#   bash paper/arxiv/make_arxiv.sh                        # rebuilds the journal PDFs first
#   SKIP_JOURNAL_BUILD=1 bash paper/arxiv/make_arxiv.sh   # reuse paper/si.aux and si.pdf
#
# 1. Builds the journal SI and main text (si.tex and main.tex cross-reference each other
#    through xr), so paper/si.aux, paper/main.aux and paper/si.pdf are current.
# 2. Writes src/ms.tex: preamble.tex, then a neutral title block (title, authors,
#    affiliations and abstract read from ../main.tex), then the body of ../main.tex
#    (everything after "%%%MAIN TEXT%%%%") with the \input tables inlined, every
#    \siref{...} replaced by its SI number from si.aux, figure paths changed to figures/,
#    the edits in arxiv-edits.sed applied, and all TeX comments removed.
# 3. Runs pdflatex and bibtex on it once to make src/ms.bbl, copies only the figures ms.tex
#    includes, and copies the SI to src/anc/si.pdf (arXiv's ancillary-file directory).
# 4. Packs src/ into powder-doser-arxiv.tar.gz, unpacks it in an empty directory and compiles
#    it there with pdflatex alone (no BibTeX, no .bib or .bst present), as arXiv does. That
#    PDF is powder-doser-arxiv.pdf.
# Needs pdflatex and bibtex (TeX Live or MiKTeX), gawk, sed, tar and gzip. No Python.
set -euo pipefail
ARX=$(cd "$(dirname "$0")" && pwd)
PAPER=$(dirname "$ARX")
SRC="$ARX/src"
BUILD=$(mktemp -d)
CHECK=$(mktemp -d)
PDFLATEX="pdflatex -interaction=nonstopmode -halt-on-error"
die() { echo "make_arxiv: $*" >&2; exit 1; }

cd "$PAPER"
if [ "${SKIP_JOURNAL_BUILD:-0}" != 1 ]; then
  echo "Building the journal SI and main text ..."
  $PDFLATEX si >/dev/null; bibtex si >/dev/null
  $PDFLATEX main >/dev/null; bibtex main >/dev/null; $PDFLATEX main >/dev/null
  $PDFLATEX si >/dev/null; $PDFLATEX si >/dev/null; $PDFLATEX main >/dev/null
fi
[ -s si.aux ] && [ -s main.aux ] && [ -s si.pdf ] || die "paper/si.aux, main.aux or si.pdf missing"

# --- front matter, read from main.tex -------------------------------------------------------
TITLE=$(sed -n 's/^\\includegraphics{head_foot\/DOI} & \\noindent\\LARGE{\\textbf{\(.*\)}} \\\\$/\1/p' main.tex)
AUTHORS=$(sed -n 's/^ & \\noindent\\large{\(.*\)} \\\\$/\1/p' main.tex)
ABSTRACT=$(sed -n 's/^\\includegraphics{head_foot\/dates} & \\noindent\\normalsize{\(.*\)} \\\\$/\1/p' main.tex)
AFFILS=$(grep '^\\footnotetext{\\textit{\$\^{[a-z]}\$~' main.tex || true)
SINOTE=$(grep '^\\footnotetext{\\dag~Supplementary Information available:' main.tex || true)
for v in TITLE AUTHORS ABSTRACT AFFILS SINOTE; do [ -n "${!v}" ] || die "$v not found in main.tex"; done
# The SI is an ancillary file on arXiv, not a journal ESI with a DOI.
SINOTE=$(printf '%s' "$SINOTE" | sed \
  -e 's/Supplementary Information available:/Supplementary Information (SI), in the ancillary file \\texttt{anc\/si.pdf} on this preprint'"'"'s arXiv page:/' \
  -e 's/ See DOI: [0-9.]*\/[0-9]*\.}$/}/')
case "$SINOTE" in *DOI*) die "placeholder DOI left in the SI note";; esac

# --- src/ms.tex ------------------------------------------------------------------------------
rm -rf "$SRC"; mkdir -p "$SRC/figures" "$SRC/anc"
LINE=$(grep -n '^%%%MAIN TEXT%%%%$' main.tex | cut -d: -f1)
[ -n "$LINE" ] || die "%%%MAIN TEXT%%%% marker not found"
{
  grep -v '^%' "$ARX/preamble.tex"
  printf '\n\\begin{document}\n\n\\twocolumn[\n  \\begin{@twocolumnfalse}\n\\begin{center}\n'
  printf '{\\LARGE\\bfseries %s\\par}\n\\vspace{0.5cm}\n' "$TITLE"
  printf '{\\large %s\\par}\n\\end{center}\n\\vspace{0.3cm}\n' "$AUTHORS"
  printf '\\noindent\\hfill\\begin{minipage}{0.9\\textwidth}\n\\noindent\\textbf{Abstract.} %s\n\\end{minipage}\\hfill\\null\n' "$ABSTRACT"
  printf '\\vspace{0.7cm}\n  \\end{@twocolumnfalse}\n]\n\n'
  printf '%s\n' "$AFFILS" "$SINOTE"
  printf '\n'
  # Body: inline the \input tables, then resolve \siref, flatten figure paths, apply the
  # arXiv-only edits and strip comments (arXiv publishes the source).
  tail -n +"$((LINE + 1))" main.tex | gawk '
    {
      line = $0
      while (match(line, /\\input\{v2\/tables\/[A-Za-z0-9_]+\}/)) {
        pre = substr(line, 1, RSTART - 1)
        f = substr(line, RSTART + 7, RLENGTH - 8) ".tex"
        line = substr(line, RSTART + RLENGTH)
        if (pre != "") print pre "%"
        n = 0
        while ((getline l < f) > 0) { print l; n++ }
        close(f)
        if (n == 0) { print "missing table " f > "/dev/stderr"; exit 2 }
      }
      print line
    }' | sed -f "$ARX/arxiv-edits.sed" | gawk -v aux=si.aux '
    BEGIN {
      while ((getline l < aux) > 0)
        if (match(l, /^\\newlabel\{([^}]*)\}\{\{([^}]*)\}/, m)) lab[m[1]] = m[2]
    }
    function strip(s,   i, c, bs) {
      bs = 0
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c == "%" && bs % 2 == 0) {
          if (i > 1 && substr(s, i - 1, 1) ~ /[ \t]/) { s = substr(s, 1, i - 1); sub(/[ \t]+$/, "", s); return s }
          return substr(s, 1, i)
        }
        if (c == "\\") bs++; else bs = 0
      }
      return s
    }
    /^[ \t]*%/ { next }
    {
      s = strip($0)
      while (match(s, /\\siref\{([^}]*)\}/, m)) {
        if (!(m[1] in lab)) { print "unresolved \\siref{" m[1] "}" > "/dev/stderr"; exit 2 }
        s = substr(s, 1, RSTART - 1) lab[m[1]] substr(s, RSTART + RLENGTH)
      }
      gsub(/v2\/figures\//, "figures/", s)
      print s
    }'
} > "$SRC/ms.tex"
grep -q 'siref\|\\input{\|head_foot\|00\.0000' "$SRC/ms.tex" && die "leftover siref, input, head_foot or placeholder DOI in ms.tex"

# Figures: only those ms.tex includes.
grep -o '\\includegraphics\(\[[^]]*\]\)\{0,1\}{[^}]*}' "$SRC/ms.tex" | sed 's/.*{\(.*\)}/\1/' | sort -u |
while read -r f; do
  [ -f "$PAPER/v2/$f" ] || die "figure $f not found in paper/v2/"
  cp "$PAPER/v2/$f" "$SRC/$f"
done
cp si.pdf "$SRC/anc/si.pdf"

# --- .bbl: one full build with BibTeX outside the bundle -------------------------------------
cp -r "$SRC/ms.tex" "$SRC/figures" references.bib rsc.bst "$BUILD/"
( cd "$BUILD" && $PDFLATEX ms >/dev/null && bibtex ms >/dev/null && $PDFLATEX ms >/dev/null && $PDFLATEX ms >/dev/null ) \
  || die "build of ms.tex failed; see $BUILD/ms.log"
cp "$BUILD/ms.bbl" "$SRC/ms.bbl"

# Numbering check: every label the journal build has must get the same number here, because
# the SI (anc/si.pdf) cites main-text figures, tables and sections by number.
gawk 'FNR == 1 { file++ }
  match($0, /^\\newlabel\{([^}]*)\}\{\{([^}]*)\}/, m) { if (file == 1) j[m[1]] = m[2]; else a[m[1]] = m[2] }
  END { bad = 0
        for (k in j) if (k !~ /@cref|^sub@/ && (k in a) && a[k] != j[k]) { print "label " k ": journal " j[k] ", arXiv " a[k]; bad++ }
        exit (bad > 0 ? 1 : 0) }' main.aux "$BUILD/ms.aux" || die "main-text numbering differs from the journal build"

# --- tarball and clean-directory check ---------------------------------------------------------
TAR="$ARX/powder-doser-arxiv.tar.gz"
tar -C "$SRC" --sort=name --owner=0 --group=0 --numeric-owner --mtime='2026-11-28 00:00:00Z' \
  -cf - ms.tex ms.bbl figures anc | gzip -n -9 > "$TAR"
tar -xzf "$TAR" -C "$CHECK"
( cd "$CHECK" && ls *.bib *.bst 2>/dev/null && exit 1
  for i in 1 2 3; do $PDFLATEX ms >/dev/null || exit 1; done ) || die "clean-directory build failed; see $CHECK/ms.log"
if grep -E 'undefined|Rerun to get|not found|Missing' "$CHECK/ms.log"; then die "warnings in the clean-directory build ($CHECK/ms.log)"; fi
cp "$CHECK/ms.pdf" "$ARX/powder-doser-arxiv.pdf"
echo "tarball: $(du -h "$TAR" | cut -f1) ($(tar -tzf "$TAR" | grep -vc '/$') files)"
echo "PDF:     $(pdfinfo "$ARX/powder-doser-arxiv.pdf" 2>/dev/null | grep Pages || echo built)"
rm -rf "$BUILD" "$CHECK"
