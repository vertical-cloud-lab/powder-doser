#!/usr/bin/env python3
"""Assemble the v2 figures as LaTeX subfigures, with their captions.

Review of 11 Nov 2026 (paper/review_2026-11-11/NOTES.md, items G1-G3):
captions are shown as text beside each figure, never inside the image, and the
multi-panel figures are LaTeX subfigures built from one PDF per panel.

Captions live here, once, in Markdown.  This script writes

    figures.tex             every figure (subcaption) and table, with captions,
                            ready to paste into the manuscript; compiled to
                            figures.pdf
    figures-preview.tex     the same figures without their captions, one per
                            page; each page is rendered to preview/figN_*.png
    FIGURES-AND-TABLES.md   each preview with its caption as text underneath,
                            and every table written out in Markdown
    PR-BODY.md              the same for the PR description (absolute image
                            URLs at a given commit: --sha abc1234)

Run the figure scripts first (see README.md), then:

    python3 build_figures.py [--sha <7-char commit>] [--no-latex]

LaTeX: MiKTeX's pdflatex (packages install on first use).
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
# Captions (Markdown).  First sentence after the title: the takeaway (G2).
# "#123" becomes a link to that issue or pull request in both outputs.
# ----------------------------------------------------------------------------
FIGURES = [
    dict(
        n="1", key="doser", stem="fig1_doser", title="The doser",
        caption=(
            "One printed auger tube is both the powder reservoir and the dosing screw; "
            "the doser turns, tilts and taps it over a cup on an analytical balance. "
            "(a) The doser as tested in the second round (photographed 11 Sep 2026), with its "
            "parts labelled; the dashed box marks the part drawn in section in (c). "
            "(b) Exploded view of the current design, assembled in CAD from the team's parts "
            "(#170); the numbers refer to the bill of materials in the SI. "
            "(c) Section through the tested auger and its screw-on cap, the team's Fusion 360 "
            "part: the flight fills only the outlet end, and the 44-tooth gear is on the outside "
            "of the tube. "
            "(d) The fixed livestream camera's view of the cup after a 0.5 g NaCl dose "
            "(15 Sep 2026; 0.496 g delivered; #116)."),
        tex=r"""
\begin{subfigure}[b]{W(doser_a_photo)}\includegraphics{figures/doser_a_photo.pdf}\caption{As tested}\end{subfigure}\hfill
\begin{minipage}[b]{W(doser_b_exploded)}
\begin{subfigure}[b]{\linewidth}\includegraphics{figures/doser_b_exploded.pdf}\caption{Exploded view}\end{subfigure}\\[6pt]
\begin{subfigure}[b]{W(doser_c_auger)}\centering\includegraphics{figures/doser_c_auger.pdf}\caption{Auger section}\end{subfigure}\hfill
\begin{subfigure}[b]{W(doser_d_cam)}\includegraphics{figures/doser_d_cam.pdf}\caption{Fixed camera}\end{subfigure}
\end{minipage}"""),
    dict(
        n="2", key="timeline", stem="fig2_timeline",
        title="AI agents and engineers, April to November 2026",
        caption=(
            "AI agents modelled the first parts from text and drawings; from July the engineers "
            "redrew in conventional CAD the parts that were built and tested, and the agents moved "
            "on to running the tests and assembling the CAD. "
            "(a) Key designs on one date axis, each joined to its date. Above the axis are the "
            "designs modelled by AI agents, with the agent (purple) and model (grey) under each: "
            "the powder excavator (#2) and the first auger (#16), from the hackathon; the whole "
            "module from a single request (#35); the bracket the agent modelled from the team's "
            "dimensioned drawing (#46, #47; red arrow); the first tap collar and the collar after "
            "review (#51); the storage auger with its screw cap (#49); all 11 parts from one prompt "
            "through the Zoo Text-to-CAD API (#104, #110); and the team's parts assembled through "
            "the Onshape API (#170). Below the axis is the engineers' work: the hackathon sketch "
            "(#2), the first printed auger, the bracket drawing (#46), the Fusion 360 auger, cap "
            "and 44-tooth gear that turned in every test (#120), the first dose in a glove box "
            "(#117), the multi-doser carriage sketch and Onshape model (#128), and the doser as "
            "tested (#156). The hackathon (22–24 Apr) and the 13-powder test campaign "
            "(4 Aug–15 Sep) are shaded on the axis. "
            "(b) When each agent and model was in use, on the same date axis."),
        tex=r"""
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/timeline_a.pdf}\caption{Designs over time}\end{subfigure}\\[4pt]
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/timeline_b_band.pdf}\caption{Agents and models}\end{subfigure}"""),
    dict(
        n="3", key="redesign", stem="fig3_redesign",
        title="The original AI parts and what replaced them",
        caption=(
            "Every AI-modelled part was reviewed, printed and tested, but the tested doser ran on "
            "later versions: the agent revised the tap collar and the team then rebuilt it, and "
            "the team redrew the agent's auger in Fusion 360. AI parts have purple frames, the "
            "team's grey. "
            "(a) Tap collar: the first AI collar (15 May) and the collar after review (#51, by "
            "10 Jun), the collar on the rig during the tests (11 Sep, #156), and the team's new "
            "block (8 Oct, #128). "
            "(b) Auger: the AI storage auger with 16:48 gears (16 Jun, #49) and the team's "
            "Fusion 360 recreation with 20:44 gears (17 Jul, #120), which turned in every test. "
            "(c) Bracket, the other direction: the team's dimensioned drawing (#46) and the "
            "agent's model of it (#47), both 14 May."),
        tex=r"""
\begin{subfigure}[b]{\textwidth}\includegraphics{figures/redesign_a_tapcollar.pdf}\caption{Tap collar}\end{subfigure}\\[6pt]
\begin{subfigure}[b]{W(redesign_b_auger)}\includegraphics{figures/redesign_b_auger.pdf}\caption{Auger}\end{subfigure}\hfill
\begin{subfigure}[b]{W(redesign_c_bracket)}\includegraphics{figures/redesign_c_bracket.pdf}\caption{Bracket}\end{subfigure}"""),
    dict(
        n="4", key="dosing", stem="fig4_dosing", title="How a dose runs",
        caption=(
            "A person asks the AI agent for a dose in a GitHub comment; a three-phase controller "
            "on the doser's microcontroller then turns, tilts and taps the auger until the balance "
            "reads the target. "
            "(a) A request and the agent's reply (8 g of AlSi10Mg for an atomizer charge, #166, "
            "29 Sep 2026). "
            "(b) The control loop: the balance is read after every step, and the controller acts "
            "on the mass still to go. "
            "(c) One 1 g NaCl dose from the test campaign (12 Aug 2026), with its three phases "
            "shaded: bulk, fine and tap. Above the trace are the tube positions in each phase "
            "(CAD renders of the current design at 45°, 22.5° and 0°) and the fixed camera's "
            "stills before and after a 0.5 g salt dose (15 Sep 2026). The green band is the ±5% "
            "acceptance limit. One image rather than subfigures: the lines join the stills to "
            "the trace."),
        tex=r"""
\includegraphics{figures/dosing.pdf}"""),
    dict(
        n="5", key="use", stem="fig5_use", title="Using the doser",
        caption=(
            "Each powder has its own auger, filled once and stored loaded, so changing powder "
            "means swapping a tube. "
            "(a) Filling an auger with salt through its open end, then capping it (29 Jul 2026). "
            "(b) Fitting a filled auger to the doser, and (c) the doser ready over the cup, frames "
            "from the 30 Sep 2026 dose video: the powder falls through a paper funnel into an "
            "aluminium cup that stands in the glass beaker. "
            "(d) Eight of the labelled augers, with each label and the mass one auger revolution "
            "delivered (\\*at 22.5° tilt; Fig. 6a)."),
        tex=r"""
\begin{subfigure}[b]{W(use_a_fill)}\includegraphics{figures/use_a_fill.pdf}\caption{Fill}\end{subfigure}\hfill\raisebox{1.1in}{$\rightarrow$}\hfill
\begin{subfigure}[b]{W(use_b_fit)}\includegraphics{figures/use_b_fit.pdf}\caption{Fit}\end{subfigure}\hfill\raisebox{1.1in}{$\rightarrow$}\hfill
\begin{subfigure}[b]{W(use_c_ready)}\includegraphics{figures/use_c_ready.pdf}\caption{Over the cup}\end{subfigure}\hfill
\begin{subfigure}[b]{W(use_d_augers)}\includegraphics{figures/use_d_augers.pdf}\caption{One auger per powder}\end{subfigure}"""),
    dict(
        n="6", key="openloop", stem="fig6_open_loop",
        title="Open-loop delivery of 13 powders under one fixed set of settings",
        caption=(
            "Ten powders moved, from 10 to 231 mg per auger revolution, and three delivered "
            "nothing measurable; one solenoid tap released up to 20 mg, but for the fastest "
            "powders a single tap was unpredictable. "
            "(a) Mass per auger revolution at 22.5° (protocol C; mean ± standard error of six "
            "revolutions; log axis). "
            "(b) Mass released by one solenoid tap at 22.5° (protocol E): mean ± standard "
            "deviation of eight taps, the spread to expect from a single tap. Table S1 gives "
            "the standard errors. "
            "(c) Mass against time while the auger turned continuously at 15 rpm (protocol D)."),
        tex=r"""
\begin{subfigure}[b]{W(openloop_a_rev)}\includegraphics{figures/openloop_a_rev.pdf}\caption{Per revolution}\end{subfigure}\hfill
\begin{subfigure}[b]{W(openloop_b_tap)}\includegraphics{figures/openloop_b_tap.pdf}\caption{Per tap}\end{subfigure}\hfill
\begin{subfigure}[b]{W(openloop_c_time)}\includegraphics{figures/openloop_c_time.pdf}\caption{In time}\end{subfigure}""",
        label="fgr:v2openloop"),
    dict(
        n="7", key="closedloop", stem="fig7_closed_loop", title="Closed-loop doses",
        caption=(
            "Doses of 1 g landed within ±5% for every powder that delivered at least 26 mg per "
            "revolution; smaller doses missed more often, fast powders tending to overshoot and "
            "slow ones to fall short. "
            "Error of every valid closed-loop dose from both test rounds, one row per powder, "
            "ordered by mass per revolution (fastest at the top). The green band is the "
            "acceptance limit: ±10% below 100 mg, ±5% at and above. Times per dose are in "
            "Table 3 and SI Fig. S3. One image rather than subfigures: the three panels share "
            "the powder axis."),
        tex=r"""
\includegraphics{figures/closedloop.pdf}""",
        label="fgr:v2closedloop"),
]

SI_FIGURES = [
    dict(
        n="S1", key="cadcompare", stem="figS1_cad_comparison", title="Generative-CAD comparison",
        caption=(
            "Asked for the whole doser at once, every tool returned parts that did not make a "
            "working assembly; one part at a time, with review, worked better. "
            "(a–c) The same prompt (#104, 22 Jun 2026) given to the GitHub Copilot coding agent, "
            "CADSmith and the Zoo Text-to-CAD API, each rendered from the same viewpoint. "
            "(d–f) The tap collar from the coding agent (first version and after review) and from "
            "Zoo Design Studio (third Zookeeper iteration). (g, h) CADSmith's mounting plate and "
            "baseplate. (i–l) The coding agent's four mounting-plate iterations: out-of-date input "
            "files led to a hole, then platforms, then a gap, until the correct files were "
            "supplied. Not yet reviewed; still one image."),
        tex=r"""
\includegraphics{figures/figS_cad_comparison.pdf}"""),
    dict(
        n="S2", key="revvar", stem="figS2_rev_variation", title="Variation between revolutions",
        caption=(
            "Most powders varied by 2–18% from one revolution to the next; white rice flour, at "
            "37%, varied most. Revolution-to-revolution coefficient of variation against mass per "
            "revolution at 22.5° (old Fig. 3c, without the slow/fast shading). The same numbers "
            "are in Table S1, so this figure can also be dropped."),
        tex=r"""
\includegraphics{figures/figS_rev_variation.pdf}"""),
    dict(
        n="S3", key="dosetime", stem="figS3_dose_time", title="Time per dose",
        caption=(
            "Larger doses took longer: for doses within the limit, the median was 52 s at 50 mg, "
            "152 s at 200 mg and 185 s at 1 g. Time to finish each dose, by target mass; lines "
            "are the medians of the doses that finished within the acceptance limit "
            "(old Fig. 5d)."),
        tex=r"""
\includegraphics{figures/figS_dose_time.pdf}"""),
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
    return s


PREAMBLE = r"""\documentclass[9pt]{extarticle}
\usepackage[paperwidth=21cm,paperheight=29.7cm,textwidth=17.1cm,textheight=26cm,centering]{geometry}
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
\usepackage{array,booktabs}
\usepackage[hidelinks]{hyperref}
\newcommand{\siref}[1]{S\ref{#1}}
\setlength{\parindent}{0pt}
"""


def figure_env(f: dict, preview: bool, star=True) -> str:
    env = "figure*" if star else "figure"
    cap = f"\\caption{{\\textbf{{{tex_text(f['title'])}.}} {tex_text(f['caption'])}}}"
    lab = f.get("label", f"fgr:v2{f['key']}")
    body = layout(f["tex"]).strip("\n")
    end = "\\stepcounter{figure}" if preview else f"{cap}\n\\label{{{lab}}}"
    return f"\\begin{{{env}}}[p]\n\\centering\n{body}\n{end}\n\\end{{{env}}}\n"


def write_tex(preview: bool) -> Path:
    name = "figures-preview.tex" if preview else "figures.tex"
    parts = [f"% Generated by paper/v2/build_figures.py -- do not edit by hand.\n{PREAMBLE}"]
    if preview:
        parts.append("\\pagestyle{empty}\n")
    parts.append("\\begin{document}\n")
    for f in FIGURES:
        parts.append(figure_env(f, preview))
        if preview:
            parts.append("\\clearpage\n")
    if not preview:
        parts.append("\\clearpage\n")
        for t in TABLES_TEX:
            parts.append(f"\\input{{tables/{t}}}\n")
        parts.append("\\clearpage\n\\setcounter{figure}{0}\n\\renewcommand{\\thefigure}{S\\arabic{figure}}\n")
    else:
        parts.append("\\setcounter{figure}{0}\n")
    for f in SI_FIGURES:
        parts.append(figure_env(f, preview))
        if preview:
            parts.append("\\clearpage\n")
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
    PREVIEW.mkdir(exist_ok=True)
    tmp = HERE / ".preview_pages"
    tmp.mkdir(exist_ok=True)
    pdftoppm = shutil.which("pdftoppm") or str(Path.home() / "bin" / "pdftoppm")
    subprocess.run([pdftoppm, "-r", "200", "-png", str(pdf), str(tmp / "p")], check=True)
    pages = sorted(tmp.glob("p-*.png"))
    stems = [f["stem"] for f in FIGURES] + [f["stem"] for f in SI_FIGURES]
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


def figure_md(f: dict, img_url: str) -> str:
    return (f"### Fig. {f['n']} {f['title']}\n\n![Fig. {f['n']}]({img_url})\n\n"
            f"**Fig. {f['n']} {f['title']}.** {md_links(f['caption'])}\n")


def tables_md() -> str:
    out = []
    for head, fn, note in TABLES_MD:
        body = (TABLES / fn).read_text().strip()
        out.append(f"### {head}\n\n{md_links(note)}\n\n{body}\n")
    return "\n".join(out)


def write_markdown(sha: str | None) -> None:
    intro = (
        "# Figures and tables for review (v2)\n\n"
        "Every figure is shown with its full draft caption as text underneath (review of "
        "11 Nov, [`../review_2026-11-11/NOTES.md`](../review_2026-11-11/NOTES.md)). The images "
        "are rendered from [`figures.tex`](figures.tex), which assembles the panels as LaTeX "
        "subfigures; [`figures.pdf`](figures.pdf) is the compiled version with captions and "
        "tables. Title and abstract: [`TITLE-ABSTRACT.md`](TITLE-ABSTRACT.md). How each item maps "
        "to the whiteboard and the meetings: [`README.md`](README.md).\n\n## Main text\n\n")
    parts = [intro]
    for f in FIGURES:
        parts.append(figure_md(f, f"preview/{f['stem']}.png") + "\n")
    parts.append("## Tables\n\n" + tables_md() + "\n## Supporting information\n\n")
    for f in SI_FIGURES:
        parts.append(figure_md(f, f"preview/{f['stem']}.png") + "\n")
    parts.append("### SI Fig. S4 Assembly steps and adjusting the stand\n\n"
                 "Not remade. The exploded view and the 19 build steps from PR #170 already exist "
                 "(`paper/figures/figS_assembly_exploded.pdf`, `paper/figures/figS_assembly_steps.pdf`). "
                 "Nothing shows the new stand (fitted 2 Oct) being assembled or its height being "
                 "adjusted.\n")
    (HERE / "FIGURES-AND-TABLES.md").write_text("".join(parts))
    print("wrote FIGURES-AND-TABLES.md")
    if sha:
        raw = f"{REPO}/blob/{sha}/paper/v2/preview"
        body = [f"<!-- generated by paper/v2/build_figures.py --sha {sha} -->\n"]
        for f in FIGURES:
            body.append(figure_md(f, f"{raw}/{f['stem']}.png?raw=true").replace("### ", "#### ") + "\n")
        (HERE / "PR-FIGURES.md").write_text("".join(body))
        si = [figure_md(f, f"{raw}/{f['stem']}.png?raw=true").replace("### ", "#### ") + "\n"
              for f in SI_FIGURES]
        (HERE / "PR-SI.md").write_text("".join(si))
        (HERE / "PR-TABLES.md").write_text(tables_md().replace("### ", "#### "))
        print("wrote PR-FIGURES.md, PR-SI.md, PR-TABLES.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sha", help="7-character commit for absolute image URLs (PR description)")
    ap.add_argument("--no-latex", action="store_true")
    a = ap.parse_args()
    if not a.no_latex:
        compile_tex(write_tex(preview=False))
        render_previews(compile_tex(write_tex(preview=True)))
        (HERE / "figures-preview.pdf").unlink()
    else:
        write_tex(False), write_tex(True)
    write_markdown(a.sha)
