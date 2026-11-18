#!/usr/bin/env python3
"""Assemble the v2 figures as LaTeX subfigures, with their captions.

Review of 11 Nov 2026 (paper/review_2026-11-11/NOTES.md, items G1-G3):
captions are text typeset by LaTeX, never drawn inside the image, and the
multi-panel figures are LaTeX subfigures built from one PDF per panel.
Review of 17 Nov 2026 (paper/review_2026-11-17/NOTES.md, item G): every
preview image carries its caption, and the captions live in CAPTIONS.md, which
the team edits directly.

Captions live in CAPTIONS.md, once, in Markdown.  This script writes

    figures.tex             every figure (subcaption) and table, with captions,
                            ready to paste into the manuscript; compiled to
                            figures.pdf.  Alternative versions for review
                            (e.g. Fig. 7, version B) come last.
    figures-preview.tex     each figure with its caption, one per page (tall
                            pages, so nothing breaks); each page is rendered to
                            preview/figN_*.png
    FIGURES-AND-TABLES.md   each preview, with the caption text (and its links)
                            folded underneath, and every table in Markdown
    PR-BODY.md              the same for the PR description (absolute image
                            URLs at a given commit: --sha abc1234)

Run the figure scripts first (see README.md), then:

    python3 build_figures.py [--sha <7-char commit>] [--no-latex]

LaTeX: MiKTeX's pdflatex (packages install on first use).  Where the MiKTeX
apt package does not install (Ubuntu 26.04 runners), ~/bin/pdflatex can wrap
the official miktex/miktex Docker image; see README.md.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
FIGS, PREVIEW, TABLES = HERE / "figures", HERE / "preview", HERE / "tables"
REPO = "https://github.com/vertical-cloud-lab/powder-doser"


# ----------------------------------------------------------------------------
# Layout of each figure.  Titles and captions are read from CAPTIONS.md by the
# figure number n ("## Fig. 6 Title"); "6B" is version B of Fig. 6, shown
# after Fig. 6 in the previews and FIGURES-AND-TABLES.md, and at the end of
# figures.tex.
# ----------------------------------------------------------------------------
CAPTIONS_MD = HERE / "CAPTIONS.md"

FIGURES = [
    dict(
        n="1", key="doser", stem="fig1_doser",
        tex=r"""
\begin{subfigure}[b]{W(doser_a_photo)}\includegraphics{figures/doser_a_photo.pdf}\caption{As tested}\end{subfigure}\hfill
\begin{minipage}[b]{W(doser_b_exploded)}
\begin{subfigure}[b]{\linewidth}\includegraphics{figures/doser_b_exploded.pdf}\caption{Exploded view}\end{subfigure}\\[6pt]
\begin{subfigure}[b]{W(doser_c_auger)}\centering\includegraphics{figures/doser_c_auger.pdf}\caption{Auger section}\end{subfigure}\hfill
\begin{subfigure}[b]{W(doser_d_cam)}\includegraphics{figures/doser_d_cam.pdf}\caption{Fixed camera}\end{subfigure}
\end{minipage}"""),
    dict(
        n="2", key="timeline", stem="fig2_timeline",
        tex=r"""
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/timeline_a.pdf}\caption{Designs over time}\end{subfigure}\\[4pt]
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/timeline_b_band.pdf}\caption{Agents and models}\end{subfigure}"""),
    dict(
        n="3", key="redesign", stem="fig3_redesign",
        tex=r"""
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/redesign_a_tapcollar.pdf}\caption{Tap collar}\end{subfigure}\\[6pt]
\begin{subfigure}[b]{W(redesign_b_auger)}\includegraphics{figures/redesign_b_auger.pdf}\caption{Auger}\end{subfigure}\hfill
\begin{subfigure}[b]{W(redesign_c_bracket)}\includegraphics{figures/redesign_c_bracket.pdf}\caption{Bracket}\end{subfigure}"""),
    dict(
        n="4", key="dosing", stem="fig4_dosing",
        tex=r"""
\includegraphics{figures/dosing.pdf}"""),
    dict(
        n="5", key="use", stem="fig5_use",
        tex=r"""
\begin{subfigure}[b]{W(use_a_fill)}\includegraphics{figures/use_a_fill.pdf}\caption{Fill}\end{subfigure}\hfill\raisebox{1.05in}{$\rightarrow$}\hfill
\begin{subfigure}[b]{W(use_b_fit)}\includegraphics{figures/use_b_fit.pdf}\caption{Fit}\end{subfigure}\hfill\raisebox{1.05in}{$\rightarrow$}\hfill
\begin{subfigure}[b]{W(use_c_ready)}\includegraphics{figures/use_c_ready.pdf}\caption{Over the cup}\end{subfigure}\hfill
\begin{subfigure}[b]{W(use_d_augers)}\includegraphics{figures/use_d_augers.pdf}\caption{One auger per powder}\end{subfigure}"""),
    dict(
        n="6", key="openloop", stem="fig6_open_loop",
        tex=r"""
\begin{subfigure}[b]{W(openloop_a_rev)}\includegraphics{figures/openloop_a_rev.pdf}\caption{Per revolution}\end{subfigure}\hfill
\begin{subfigure}[b]{W(openloop_b_tap)}\includegraphics{figures/openloop_b_tap.pdf}\caption{Per tap}\end{subfigure}\hfill
\begin{subfigure}[b]{W(openloop_c_time)}\includegraphics{figures/openloop_c_time.pdf}\caption{In time}\end{subfigure}""",
        label="fgr:v2openloop"),
    dict(
        n="7", key="closedloop", stem="fig7_closed_loop",
        tex=r"""
\includegraphics{figures/closedloop.pdf}""",
        label="fgr:v2closedloop"),
]

SI_FIGURES = [
    dict(
        n="S1", key="cadcompare", stem="figS1_cad_comparison",
        tex=r"""
\includegraphics{figures/figS_cad_comparison.pdf}"""),
    dict(
        n="S2", key="revvar", stem="figS2_rev_variation",
        tex=r"""
\includegraphics{figures/figS_rev_variation.pdf}"""),
    dict(
        n="S3", key="dosetime", stem="figS3_dose_time",
        tex=r"""
\includegraphics{figures/figS_dose_time.pdf}"""),
    dict(
        n="S4", key="exploded", stem="figS4_assembly_exploded",
        tex=r"""
\includegraphics{figures/figS_assembly_exploded.pdf}"""),
]

# Alternative versions for review (17 Nov: Fig. 6 with banded rows; Fig. 7 in mg).
ALTERNATIVES = [
    dict(
        n="6B", key="openloopbanded", stem="fig6B_open_loop_banded",
        tex=r"""
\begin{subfigure}[b]{W(openloop_a_rev_banded)}\includegraphics{figures/openloop_a_rev_banded.pdf}\caption{Per revolution}\end{subfigure}%
\begin{subfigure}[b]{W(openloop_b_tap_banded)}\includegraphics{figures/openloop_b_tap_banded.pdf}\caption{Per tap}\end{subfigure}\hfill
\begin{subfigure}[b]{W(openloop_c_time)}\includegraphics{figures/openloop_c_time.pdf}\caption{In time}\end{subfigure}"""),
    dict(
        n="7B", key="closedloopmg", stem="fig7B_closed_loop_mg",
        tex=r"""
\includegraphics{figures/closedloop_mg.pdf}"""),
    dict(
        n="7C", key="closedloopoverlay", stem="fig7C_closed_loop_mg_overlay",
        tex=r"""
\begin{subfigure}[b]{W(closedloop_mg_overlay)}\includegraphics{figures/closedloop_mg_overlay.pdf}\caption{All targets, one axis}\end{subfigure}\hfill
\begin{subfigure}[b]{W(closedloop_mg_box)}\includegraphics{figures/closedloop_mg_box.pdf}\caption{Spread by target}\end{subfigure}"""),
]

TABLES_MD = [  # (heading, markdown file, note)
    ("Table 1 The 13 powders", "table_powders.md",
     "Mass per auger revolution: protocol C mean at 22.5° (Fig. 6a). Closed-loop columns: valid "
     "doses within the acceptance limit (±10% at 50 mg, ±5% at 200 mg and 1 g) out of the number "
     "run (Fig. 7); a dash means not run. Silicon grades by sieve size: −325 mesh passes a 44 µm "
     "sieve; −110/+200 mesh lies between about 75 and 150 µm."),
    ("Table 2 Test protocols", "table_protocols.md", "Carried from the draft (`main.tex`)."),
    ("Table 3 Closed-loop doses by target", "table_closed_loop.md",
     "Protocols G and H, both rounds. Times are given here rather than as a figure panel; SI "
     "Fig. S3 shows every dose."),
    ("Table 4 AI tools, dates and models", "table_ai_tools.md",
     "Condensed from `paper/figures/data/ai_tools_timeline.csv`."),
    ("Table S1 Open-loop delivery per powder", "table_open_loop.md",
     "Protocols C and E, round 1, one run per powder. Mass per auger revolution (mean ± standard "
     "error of six revolutions) at 0°, 22.5° and 45°; the revolution-to-revolution coefficient of "
     "variation (CV) at 22.5°; mass released by one solenoid tap at 22.5° (mean ± standard error "
     "of eight taps). Replaces the tilt panel of the earlier draft (old Fig. 4a)."),
    ("Candidate table for the lessons-learned discussion", "table_ai_failures.md",
     "Carried from the draft's failure-modes table."),
]
TABLES_TEX = ["table_powders.tex", "table_protocols.tex", "table_closed_loop.tex",
              "table_ai_tools.tex", "table_open_loop.tex", "table_ai_failures.tex"]


# ----------------------------------------------------------------------------
def read_captions() -> dict[str, tuple[str, str]]:
    """{"6": (title, caption)} from CAPTIONS.md; line breaks inside a caption are spaces."""
    text = CAPTIONS_MD.read_text()
    caps = {}
    for mo in re.finditer(r"^## Fig\. (\S+) (.+?)\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S):
        caps[mo.group(1)] = (mo.group(2).strip(), " ".join(mo.group(3).split()))
    return caps


def attach_captions() -> None:
    caps = read_captions()
    for f in FIGURES + SI_FIGURES + ALTERNATIVES:
        if f["n"] not in caps:
            raise SystemExit(f"CAPTIONS.md has no caption for Fig. {f['n']}")
        f["title"], f["caption"] = caps[f["n"]]


def fig_name(n: str) -> str:
    """"6B" -> "6, version B"; "S2" -> "S2"."""
    mo = re.fullmatch(r"(\d+)([B-Z])", n)
    return f"{mo.group(1)}, version {mo.group(2)}" if mo else n


def figure_order(si: bool = False) -> list[dict]:
    """Main (or SI) figures, each followed by its alternative versions."""
    out = []
    for f in (SI_FIGURES if si else FIGURES):
        out.append(f)
        out += [a for a in ALTERNATIVES if re.fullmatch(rf"{f['n']}[B-Z]", a["n"])]
    return out


def pdf_width_in(stem: str) -> float:
    b = (FIGS / f"{stem}.pdf").read_bytes()
    mb = re.search(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", b)
    return (float(mb.group(3)) - float(mb.group(1))) / 72


def layout(tex: str) -> str:
    return re.sub(r"W\((\w+)\)", lambda mo: f"{pdf_width_in(mo.group(1)):.3f}in", tex)


def md_links(s: str) -> str:
    return re.sub(r"(?<![\w/\[])#(\d+)", lambda mo: f"[#{mo.group(1)}]({REPO}/issues/{mo.group(1)})", s)


def tex_text(s: str) -> str:
    s = s.replace("\\*", "*")
    s = s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    s = re.sub(r"(?<![\w/])#(\d+)", lambda mo: rf"\href{{{REPO}/issues/{mo.group(1)}}}{{\#{mo.group(1)}}}", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = s.replace("*", r"\textsuperscript{*}")
    # keep a number with its unit, and "Fig. 6" together, on one line
    s = re.sub(r"(\d) (mg|g|s|mm|rpm|µm|in|cm|%)(?![\w])", r"\1~\2", s)
    s = re.sub(r"\b(Fig\.|Figs\.|Table|protocol) (?=[\dS])", r"\1~", s)
    return s


PREAMBLE = r"""\documentclass[9pt]{extarticle}
\usepackage[paperwidth=21cm,paperheight=PAPERH,textwidth=17.1cm,textheight=TEXTH,centering]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{graphicx}
\usepackage[labelfont=bf,font=small,justification=raggedright,singlelinecheck=false]{caption}
\usepackage[labelformat=parens,labelfont=bf,font=footnotesize,justification=centering]{subcaption}
\usepackage{newunicodechar}
\newunicodechar{±}{\ensuremath{\pm}}
\newunicodechar{°}{\ensuremath{^\circ}}
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{µ}{\ensuremath{\mu}}
\newunicodechar{μ}{\ensuremath{\mu}}
\newunicodechar{×}{\ensuremath{\times}}
\newunicodechar{≈}{\ensuremath{\approx}}
\newunicodechar{†}{\ensuremath{^\dagger}}
\newunicodechar{≤}{\ensuremath{\le}}
\newunicodechar{≥}{\ensuremath{\ge}}
\usepackage{array,booktabs}
\usepackage[hidelinks]{hyperref}
\newcommand{\siref}[1]{S\ref{#1}}
\setlength{\parindent}{0pt}
"""


def figure_env(f: dict, preview: bool) -> str:
    """A float (figures.tex) or, for the previews, the same figure set in place
    with its caption on a page of its own (no float placement to go wrong)."""
    cap = f"\\caption{{\\textbf{{{tex_text(f['title'])}.}} {tex_text(f['caption'])}}}"
    lab = f.get("label", f"fgr:v2{f['key']}")
    body = layout(f["tex"]).strip("\n")
    alt = re.fullmatch(r"\d+[B-Z]", f["n"])
    if preview:
        env = (f"\\noindent\\begin{{minipage}}{{\\textwidth}}\\captionsetup{{type=figure}}\n"
               f"\\centering\n{body}\n{cap}\n\\end{{minipage}}\n\\clearpage\n")
    else:
        env = f"\\begin{{figure*}}[p]\n\\centering\n{body}\n{cap}\n\\label{{{lab}}}\n\\end{{figure*}}\n"
    if alt:   # numbered "6, version B", without moving the main sequence on
        env = (f"\\begingroup\\renewcommand{{\\thefigure}}{{{fig_name(f['n'])}}}\n{env}"
               f"\\endgroup\\addtocounter{{figure}}{{-1}}\n")
    return env


def write_tex(preview: bool) -> Path:
    name = "figures-preview.tex" if preview else "figures.tex"
    pre = PREAMBLE.replace("PAPERH", "70cm" if preview else "29.7cm") \
                  .replace("TEXTH", "67cm" if preview else "26cm")
    parts = [f"% Generated by paper/v2/build_figures.py from CAPTIONS.md -- do not edit by hand.\n{pre}"]
    if preview:
        parts.append("\\pagestyle{empty}\n")
    parts.append("\\begin{document}\n")
    for f in (figure_order() if preview else FIGURES):
        parts.append(figure_env(f, preview))
    if not preview:
        parts.append("\\clearpage\n")
        for t in TABLES_TEX:
            parts.append(f"\\input{{tables/{t}}}\n")
        parts.append("\\clearpage\n")
    parts.append("\\setcounter{figure}{0}\n\\renewcommand{\\thefigure}{S\\arabic{figure}}\n")
    for f in (figure_order(si=True) if preview else SI_FIGURES):
        parts.append(figure_env(f, preview))
    if not preview and ALTERNATIVES:
        parts.append("\\clearpage\n\\section*{Alternative versions for review}\n"
                     "\\renewcommand{\\thefigure}{\\arabic{figure}}\n")
        for f in ALTERNATIVES:
            parts.append(figure_env(f, preview))
    parts.append("\\end{document}\n")
    out = HERE / name
    out.write_text("".join(parts))
    return out


def compile_tex(path: Path) -> Path:
    pdflatex = shutil.which("pdflatex") or str(Path.home() / "bin" / "pdflatex")
    for _ in range(2):
        r = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", path.name],
                           cwd=HERE, capture_output=True, text=True)
        if r.returncode != 0:
            log = (HERE / path.with_suffix(".log").name).read_text(errors="replace")
            raise SystemExit("pdflatex failed:\n" + "\n".join(
                l for l in log.splitlines() if l.startswith("!") or "Error" in l)[:3000])
    for ext in (".aux", ".log", ".out"):
        p = HERE / path.with_suffix(ext).name
        if p.exists():
            p.unlink()
    return HERE / path.with_suffix(".pdf").name


def render_previews(pdf: Path) -> None:
    """One page per figure, caption included (17 Nov, item G), trimmed to the ink."""
    PREVIEW.mkdir(exist_ok=True)
    tmp = HERE / ".preview_pages"
    tmp.mkdir(exist_ok=True)
    pdftoppm = shutil.which("pdftoppm") or str(Path.home() / "bin" / "pdftoppm")
    subprocess.run([pdftoppm, "-r", "200", "-png", str(pdf), str(tmp / "p")], check=True)
    pages = sorted(tmp.glob("p-*.png"))
    stems = [f["stem"] for f in figure_order()] + [f["stem"] for f in figure_order(si=True)]
    assert len(pages) == len(stems), (len(pages), stems)
    for page, stem in zip(pages, stems):
        im = Image.open(page).convert("RGB")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        box = ImageChops.difference(im, bg).getbbox()
        pad = 24
        im = im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0),
                      min(box[2] + pad, im.width), min(box[3] + pad, im.height)))
        im.save(PREVIEW / f"{stem}.png", optimize=True)
        print("preview", stem, im.size)
    shutil.rmtree(tmp)


def figure_md(f: dict, img_url: str, level: str = "###") -> str:
    name = fig_name(f["n"])
    return (f"{level} Fig. {name} {f['title']}\n\n![Fig. {name}]({img_url})\n\n"
            f"<details><summary>Caption as text, with links (edit it in "
            f"<code>CAPTIONS.md</code>)</summary>\n\n"
            f"**Fig. {name} {f['title']}.** {md_links(f['caption'])}\n\n</details>\n")


def tables_md() -> str:
    out = []
    for head, fn, note in TABLES_MD:
        body = (TABLES / fn).read_text().strip()
        out.append(f"### {head}\n\n{md_links(note)}\n\n{body}\n")
    return "\n".join(out)


S4_NOTE = ("The 19 build steps from PR #170 are still only in "
           "`paper/figures/figS_assembly_steps.pdf`, and nothing yet shows the new stand (fitted "
           "2 Oct) being assembled or its height being adjusted.\n")


def write_markdown(sha: str | None) -> None:
    intro = (
        "# Figures and tables for review (v2)\n\n"
        "Each image is the figure as typeset in [`figures.pdf`](figures.pdf), with its caption "
        "underneath (review of 17 Nov, [`../review_2026-11-17/NOTES.md`](../review_2026-11-17/NOTES.md)). "
        "The same caption is folded under each image as text, with its links. **To edit a "
        "caption, edit [`CAPTIONS.md`](CAPTIONS.md)** and rebuild. Alternative versions for "
        "review follow their figure (e.g. Fig. 7, version B). The panels are LaTeX subfigures "
        "assembled in [`figures.tex`](figures.tex). Title and abstract: "
        "[`TITLE-ABSTRACT.md`](TITLE-ABSTRACT.md). How each item maps to the whiteboard and the "
        "meetings: [`README.md`](README.md).\n\n## Main text\n\n")
    parts = [intro]
    for f in figure_order():
        parts.append(figure_md(f, f"preview/{f['stem']}.png") + "\n")
    parts.append("## Tables\n\n" + tables_md() + "\n## Supporting information\n\n")
    for f in figure_order(si=True):
        parts.append(figure_md(f, f"preview/{f['stem']}.png") + "\n")
    parts.append(S4_NOTE)
    (HERE / "FIGURES-AND-TABLES.md").write_text("".join(parts))
    print("wrote FIGURES-AND-TABLES.md")
    if sha:
        raw = f"{REPO}/blob/{sha}/paper/v2/preview"
        body = [f"<!-- generated by paper/v2/build_figures.py --sha {sha} -->\n"]
        for f in figure_order():
            body.append(figure_md(f, f"{raw}/{f['stem']}.png?raw=true", "####") + "\n")
        (HERE / "PR-FIGURES.md").write_text("".join(body))
        si = [figure_md(f, f"{raw}/{f['stem']}.png?raw=true", "####") + "\n"
              for f in figure_order(si=True)]
        (HERE / "PR-SI.md").write_text("".join(si))
        (HERE / "PR-TABLES.md").write_text(tables_md().replace("### ", "#### "))
        print("wrote PR-FIGURES.md, PR-SI.md, PR-TABLES.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", help="7-character commit for absolute image URLs (PR description)")
    ap.add_argument("--no-latex", action="store_true")
    a = ap.parse_args()
    attach_captions()
    if not a.no_latex:
        compile_tex(write_tex(preview=False))
        render_previews(compile_tex(write_tex(preview=True)))
        (HERE / "figures-preview.pdf").unlink()
    else:
        write_tex(False), write_tex(True)
    write_markdown(a.sha)
