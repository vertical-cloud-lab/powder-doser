#!/usr/bin/env python3
"""Jargon and readability audit for the powder-doser manuscript.

Reads paper/main.tex and paper/si.tex, strips LaTeX, and reports:

  1. Sentence-length distribution per section (long sentences are the single
     strongest predictor of "this reads like jargon").
  2. Acronyms, split into defined-before-first-use / defined-late / never
     defined anywhere in the document.
  3. Hits against a curated lexicon of domain terms, tagged by the audience
     that would stumble on them, with a suggested plain-language gloss.
  4. Structural flags: stacked hyphenated modifiers, multi-em-dash sentences,
     abstract-noun (nominalization) density.
  5. Insider references a reader outside the GitHub repo cannot resolve
     (bare issue/discussion numbers, file paths, "the repository").

Nothing here edits the manuscript. It produces audit_report.md and
audit_report.json next to this script so the numbers in JARGON-AUDIT.md can be
regenerated after every revision.

Usage:
    python paper/readability/jargon_audit.py
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent

# Sentences longer than this are flagged. 35 words is roughly the point at
# which a reader has to re-read; RSC house style tends to sit near 25.
LONG_SENTENCE = 35
VERY_LONG_SENTENCE = 50

# --------------------------------------------------------------------------
# Curated lexicon.  category -> {term regex: (plain gloss, severity 1-3)}
# severity 3 = a Digital Discovery reader outside this subfield will simply not
#              know the word, or will know it to mean something else;
#         2 = guessable from context but should be glossed at first use;
#         1 = fine for the Experimental/SI sections, noise in Results.
# --------------------------------------------------------------------------
LEXICON: dict[str, dict[str, tuple[str, int]]] = {
    "ai/ml jargon": {
        r"\bablation(s)?\b": ("leave-one-out comparison; to a materials reader "
                              "'ablation' means laser removal of material", 3),
        r"\bsilent regression(s)?\b": ("an unrelated feature quietly changing; "
                                       "'regression' reads as curve fitting", 3),
        r"\bpolicy-parameter space\b": ("the set of tunable dosing settings", 3),
        r"\bconstraint-aware\b": ("respecting limits such as no-overshoot", 3),
        r"\bcontextual\b": ("per-powder", 2),
        r"\bcompositional spatial reasoning\b": ("reasoning about how parts fit "
                                                 "together", 2),
        r"\bhallucinat(ed|ion|ions)\b": ("invented, non-existent", 2),
        r"\bdescriptor(s)?\b": ("measured property", 2),
        r"\bdefect taxonomy\b": ("a classification of the faults found", 2),
        r"\bcomparator(s)?\b": ("tool we compared against", 2),
        r"\bbenchmark geometry\b": ("test shapes rather than real parts", 2),
        r"\bagent-mediated\b": ("done through an AI agent", 2),
        r"\btext-to-CAD\b": ("type a description, get a 3D model", 1),
        r"\bprogrammatic[- ]CAD\b": ("CAD written as code", 1),
    },
    "cad/software jargon": {
        r"\bREPL\b": ("interactive command prompt on the microcontroller", 3),
        r"\bwatertight(ness)?\b": ("no holes in the 3D surface", 3),
        r"\bsingle-body assertion(s)?\b": ("a check that the part is one solid "
                                           "piece", 3),
        r"\binterference(s)\b": ("two parts occupying the same space", 3),
        r"\bprimitives?\b": ("basic command", 3),
        r"\bKCL\b": ("KittyCAD Language, Zoo's CAD scripting language", 3),
        r"\bSTL(s)?\b": ("the standard 3D-printable mesh file format", 2),
        r"\bCI\b": ("continuous integration, the automated build service", 2),
        r"\bGUI\b": ("point-and-click", 2),
        r"\btolerancing\b": ("assigning allowed dimensional error", 2),
        r"\bkernel\b": ("the geometry engine", 2),
        r"\bstale input files?\b": ("out-of-date source files", 2),
        r"\bupstream part files?\b": ("the files this part must mate with", 2),
        r"\bthree-view\b": ("front/side/top", 2),
        r"\borthographic\b": ("straight-on", 1),
        r"\bisometric\b": ("angled 3D", 1),
        r"\bparametric\b": ("dimension-driven", 1),
        r"\bpull request(s)?\b": ("a proposed, reviewable change", 1),
    },
    "powder-handling jargon": {
        r"\bglidant\b": ("flow aid", 3),
        r"\btrickler\b": ("a commercial fine-powder dispenser", 3),
        r"\bfeed[- ]factor\b": ("mass delivered per auger turn", 3),
        r"\bloss-in-weight\b": ("feeders metered by watching the hopper lose "
                                "weight", 3),
        r"\bmaster-alloy\b": ("a concentrated pre-blended alloy", 3),
        r"\b\d+\s*[–-]{1,2}\s*\d+\s*mesh\b": ("sieve size; inconsistent with the um grade "
                               "quoted for the other silicon", 3),
        r"\bunit operation\b": ("process step", 3),
        r"\brheologic(al|ally)\b": ("flow-behaviour", 2),
        r"\bgas-atomi(z|s)ed\b": ("made by spraying molten metal into droplets", 2),
        r"\bflowability\b": ("how freely a powder flows", 2),
        r"\bbridging\b": ("powder arching over the opening and stopping", 2),
        r"\bdribble\b": ("powder trickling out after the dose ends", 2),
        r"\bgravimetric\b": ("weight-based", 2),
        r"\bfines\b": ("the finest particles", 2),
        r"\bsurrogate(s)?\b": ("stand-in powder", 2),
        r"\btapped density\b": ("density after settling by tapping", 2),
        r"\bcohesive\b": ("sticky, clumping", 1),
    },
    "metrology / stats jargon": {
        r"\bparity\b": ("a plot of asked-for versus actually-delivered", 3),
        r"\boperating envelope\b": ("the range of doses it can handle", 3),
        r"\bpre-?declared\b": ("fixed in advance", 2),
        r"\bpre-registered\b": ("committed to in advance", 2),
        r"\bterminal tolerance\b": ("how close to target counts as done", 2),
        r"\bsystematic error\b": ("consistent offset from target", 1),
        r"\brandom error\b": ("scatter between repeats", 1),
        r"\bISO 8655(-\d)?\b": ("the pipette-accuracy standard", 1),
        r"\bcoefficient of variation\b": ("relative scatter", 1),
    },
    "electronics jargon": {
        r"\bback-?EMF\b": ("voltage kicked back by the motor", 2),
        r"\bH-bridge\b": ("a driver that can reverse the motor", 2),
        r"\bbuck regulator\b": ("step-down power supply", 2),
        r"\bshunt regulator\b": ("clamp that dumps excess voltage", 2),
        r"\btransceiver\b": ("signal-level converter", 2),
        r"\bERM\b": ("the off-balance motor used in phone vibrate", 2),
        r"\bPCB(s)?\b": ("printed circuit board", 2),
        r"\bbreakout\b": ("a small pre-wired module", 1),
        r"\bUART\b|\bI\$\^2\$C\b|\bI2C\b|\bRS-232\b": ("serial link", 1),
        r"\bNEMA-\d+\b": ("a standard motor frame size", 1),
    },
    "business / vague": {
        r"\bwetted parts\b": ("the parts the powder touches", 3),
        r"\bform factor\b": ("size and shape", 2),
        r"\bgating\b": ("rate-limiting", 2),
        r"\bamalgamation\b": ("mash-up", 2),
        r"\bplateau at\b": ("stop improving at", 1),
        r"\bdivision of labour\b": ("who did what", 1),
    },
}

# Acronyms that need no definition for any plausible reader of this journal.
ACRONYM_ALLOW = {
    "AI", "CAD", "USA", "USD", "UT", "DOI", "PDF", "URL", "OD", "ID", "PLA",
    "CSV", "JSON", "HTML", "RSC", "DD", "SI", "TODO", "MIT", "PR", "OK", "US",
    "ISO", "NASA", "UART",
}

# Brand / product names that read as acronyms but are not abbreviations the
# authors owe the reader an expansion for.
BRAND_ALLOW = {
    "TOLEDO", "XPR", "MTI", "DESIGN", "LOG", "ZZ", "KICAD", "PICO",
}

NOMINALIZATION = re.compile(
    r"\b\w{4,}(tion|tions|ment|ments|ity|ities|ance|ance|ence|ences|ism|isms|"
    r"ness|nesses)\b", re.I)

# 3+ hyphen-joined words used as one modifier, e.g. "agent-mediated
# programmatic-CAD", "cross-contamination-free".
STACKED_MODIFIER = re.compile(r"\b\w+-\w+-\w+(-\w+)*\b")

# Vendor SKUs (Adafruit #412, Pololu #3135) look like issue numbers but are
# perfectly resolvable; don't flag them.
VENDOR_SKU = re.compile(
    r"(adafruit|pololu|digi-?key|mcmaster|sparkfun|amazon|thorlabs)", re.I)

INSIDER = {
    "bare issue/discussion number": re.compile(r"(?<![\w/])#\s?\d{1,4}\b"),
    "repo file path": re.compile(r"\b[\w./-]+\.(md|scad|py|tex|stl|json|csv)\b"),
    "unanchored 'the repository'": re.compile(r"\bthe repository\b", re.I),
    "unanchored 'design log'": re.compile(r"\bdesign log\b", re.I),
}

ABBREV_GUARD = [
    ("e.g.", "e_g_"), ("i.e.", "i_e_"), ("cf.", "cf_"), ("vs.", "vs_"),
    ("et al.", "et al_"), ("approx.", "approx_"), ("ca.", "ca_"),
    ("Fig.", "Fig_"), ("Figs.", "Figs_"), ("Eq.", "Eq_"), ("Ref.", "Ref_"),
    ("Sec.", "Sec_"), ("No.", "No_"), ("Dr.", "Dr_"), ("wt.", "wt_"),
    ("Inc.", "Inc_"), ("Ltd.", "Ltd_"), ("St.", "St_"),
]


# --------------------------------------------------------------------------
# LaTeX handling
# --------------------------------------------------------------------------
MATH_MAP = {r"\pm": "\u00b1", r"\sim": "\u2248", r"\ge": "\u2265",
            r"\le": "\u2264", r"\mu": "\u00b5", r"\times": "\u00d7",
            r"\circ": "\u00b0", r"\rightarrow": "\u2192",
            r"\approx": "\u2248", r"\cdot": "\u00b7"}


def _math(m: re.Match) -> str:
    """Render inline math as readable text rather than deleting it."""
    t = m.group(1)
    for k, v in MATH_MAP.items():
        t = t.replace(k, v)
    t = re.sub(r"\\[a-zA-Z]+", "", t)
    for ch in "^_{}~":
        t = t.replace(ch, "")
    return t.strip()


def strip_latex(s: str) -> str:
    """Reduce a LaTeX source line to readable prose."""
    s = re.sub(r"(?<!\\)%.*$", "", s)                       # comments
    s = re.sub(r"\\(cite|citep|citet|label|ref|eqref)\{[^}]*\}", " ", s)
    s = re.sub(r"\\url\{[^}]*\}", "URL", s)
    s = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\includegraphics(\[[^]]*\])?\{[^}]*\}", " ", s)
    # escaped specials -> sentinels so the generic \cmd sweep does not eat them
    for tex, sent in ((r"\%", "\x01"), (r"\$", "\x02"), (r"\&", "\x03"),
                      (r"\#", "\x04"), (r"\_", "\x05")):
        s = s.replace(tex, sent)
    s = re.sub(r"\$([^$]*)\$", _math, s)                    # inline math
    # unwrap single-argument formatting commands, repeatedly (they nest)
    fmt = (r"\\(emph|textit|textbf|texttt|textrm|normalsize|large|Large|LARGE|"
           r"small|footnotesize|underline|mbox)\{")
    for _ in range(6):
        new = re.sub(fmt + r"([^{}]*)\}", r"\2", s)
        if new == s:
            break
        s = new
    s = re.sub(r"\\[ ,;:!]", " ", s)                        # \ , \, \; spacing
    s = s.replace("~", " ").replace("\\\\", " ")
    s = s.replace("---", " \u2014 ").replace("--", "\u2013")
    s = re.sub(r"\\[a-zA-Z@]+\*?(\[[^]]*\])?", " ", s)      # residual commands
    s = s.replace("{", " ").replace("}", " ")
    for sent, ch in (("\x01", "%"), ("\x02", "$"), ("\x03", "&"),
                     ("\x04", "#"), ("\x05", "_")):
        s = s.replace(sent, ch)
    return re.sub(r"\s+", " ", s).strip()


SKIP_PREFIX = (
    r"\begin", r"\end", r"\label", r"\centering", r"\includegraphics",
    r"\hline", r"\toprule", r"\midrule", r"\bottomrule", r"\balance",
    r"\bibliography", r"\renewcommand", r"\multicolumn", r"\vspace", r"\item",
)


def load(path: Path, start_marker: str | None) -> list[dict]:
    """Return [{line, kind, section, text}] of prose-bearing source lines."""
    out: list[dict] = []
    section = "front matter"
    started = start_marker is None
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        # The abstract lives inside the RSC title block, before \section.
        if "head_foot/dates" in stripped:
            txt = strip_latex(re.sub(r".*?&", "", stripped, count=1))
            if txt:
                out.append({"file": path.name, "line": lineno,
                            "kind": "abstract", "section": "Abstract",
                            "text": txt})
            continue
        if start_marker and not started:
            if stripped.startswith(start_marker):
                started = True
            else:
                continue
        m = re.match(r"\\(sub)*section\*?\{([^}]*)\}", stripped)
        if m:
            section = strip_latex(m.group(2))
            continue
        if not stripped or stripped.startswith("%"):
            continue
        if any(stripped.startswith(p) for p in SKIP_PREFIX):
            continue
        if stripped.startswith(r"\caption"):
            kind = "caption"
        elif "&" in stripped and stripped.endswith(r"\\"):
            kind = "table"
        else:
            kind = "body"
        txt = strip_latex(stripped)
        if len(txt.split()) < 3:
            continue
        out.append({"file": path.name, "line": lineno, "kind": kind,
                    "section": section, "text": txt})
    return out


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------
def sentences(text: str) -> list[str]:
    guarded = text
    for a, b in ABBREV_GUARD:
        guarded = guarded.replace(a, b)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\u201c(\"'])", guarded)
    out = []
    for p in parts:
        for a, b in ABBREV_GUARD:
            p = p.replace(b, a)
        p = p.strip()
        if p:
            out.append(p)
    return out


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", text)


def syllables(word: str) -> int:
    w = word.lower()
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ye")):
        n -= 1
    return max(n, 1)


def fog(text: str) -> float:
    sents = sentences(text)
    ws = words(text)
    if not sents or not ws:
        return 0.0
    complex_w = sum(1 for w in ws if syllables(w) >= 3 and not w[0].isupper())
    return 0.4 * (len(ws) / len(sents) + 100.0 * complex_w / len(ws))


def audit(units: list[dict], full_text: str) -> dict:
    per_section: dict[str, dict] = defaultdict(
        lambda: {"words": 0, "sentences": 0, "long": [], "jargon": 0,
                 "nominalizations": 0, "fog": []})
    long_sentences, stacked, dashes = [], [], []
    jargon_hits: dict[str, list] = defaultdict(list)

    for u in units:
        sec, text = u["section"], u["text"]
        ws = words(text)
        st = per_section[sec]
        st["words"] += len(ws)
        st["nominalizations"] += len(NOMINALIZATION.findall(text))
        st["fog"].append((fog(text), len(ws)))
        for s in sentences(text):
            n = len(words(s))
            st["sentences"] += 1
            if n >= LONG_SENTENCE:
                rec = {"file": u["file"], "line": u["line"],
                       "section": sec, "kind": u["kind"],
                       "words": n, "em_dashes": s.count("\u2014"),
                       "text": s}
                st["long"].append(n)
                long_sentences.append(rec)
            if s.count("\u2014") >= 2:
                dashes.append({"file": u["file"], "line": u["line"],
                               "section": sec,
                               "em_dashes": s.count("\u2014"), "text": s})
        for m in STACKED_MODIFIER.finditer(text):
            tok = m.group(0)
            if any(c.isdigit() for c in tok) or tok.count("-") < 2:
                continue
            stacked.append({"file": u["file"], "line": u["line"],
                            "section": sec, "term": tok})
        for cat, terms in LEXICON.items():
            for pat, (gloss, sev) in terms.items():
                for m in re.finditer(pat, text, flags=re.I):
                    st["jargon"] += 1
                    jargon_hits[pat].append(
                        {"file": u["file"], "line": u["line"],
                         "section": sec, "kind": u["kind"],
                         "category": cat, "gloss": gloss, "severity": sev,
                         "match": m.group(0)})

    # Acronyms: is the expansion "(ACR)" present, and where?
    defined_at: dict[str, int] = {}
    for m in re.finditer(r"\(([A-Z][A-Z0-9]{1,5})s?\)", full_text):
        defined_at.setdefault(m.group(1), m.start())
    acronyms: dict[str, dict] = {}
    for m in re.finditer(
            r"(?<![\\A-Za-z0-9])([A-Z]{2,6})(?:s)?"
            r"(?![A-Za-z0-9]|-[A-Z0-9]|\.[a-z])",
            full_text):
        acr = m.group(1)
        if acr in ACRONYM_ALLOW or acr in BRAND_ALLOW or acr.isdigit():
            continue
        rec = acronyms.setdefault(acr, {"count": 0, "first": m.start()})
        rec["count"] += 1
    for acr, rec in acronyms.items():
        d = defined_at.get(acr)
        rec["defined"] = d is not None
        rec["status"] = ("never defined" if d is None else
                         "defined at first use" if d <= rec["first"] + 2 else
                         "defined AFTER first use")

    insider = defaultdict(list)
    for u in units:
        for name, pat in INSIDER.items():
            for m in pat.finditer(u["text"]):
                if (name == "bare issue/discussion number"
                        and VENDOR_SKU.search(u["text"])):
                    continue
                insider[name].append(
                    {"file": u["file"], "line": u["line"],
                     "section": u["section"], "kind": u["kind"],
                     "match": m.group(0)})

    for sec, st in per_section.items():
        tot = sum(w for _, w in st["fog"]) or 1
        st["fog_score"] = round(sum(f * w for f, w in st["fog"]) / tot, 1)
        st["mean_sentence"] = round(st["words"] / max(st["sentences"], 1), 1)
        st["max_sentence"] = max(st["long"], default=0)
        st["long_count"] = len(st["long"])
        st["jargon_per_100w"] = round(100 * st["jargon"] / max(st["words"], 1), 1)
        st["nom_per_100w"] = round(
            100 * st["nominalizations"] / max(st["words"], 1), 1)
        del st["fog"], st["long"]

    return {"sections": dict(per_section), "long_sentences": long_sentences,
            "stacked_modifiers": stacked, "multi_dash": dashes,
            "jargon": {k: v for k, v in jargon_hits.items()},
            "acronyms": acronyms, "insider": dict(insider)}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def report(res: dict, counts: dict) -> str:
    L = ["# Generated jargon / readability audit",
         "",
         "Regenerate with `python paper/readability/jargon_audit.py`. "
         "The narrative interpretation of these numbers, with suggested "
         "rewrites, is in [`JARGON-AUDIT.md`](JARGON-AUDIT.md).",
         "",
         f"Corpus: {counts['units']} prose units, {counts['words']} words, "
         f"{counts['sentences']} sentences across `main.tex` and `si.tex`.",
         "",
         "## 1. Section scoreboard",
         "",
         "`Fog` is a Gunning-Fog style grade estimate (higher = denser); it is "
         "inflated by chemical names and part numbers, so compare sections "
         "against each other rather than against an absolute target.",
         "",
         "| Section | Words | Mean sent. | Longest | Sent. >35w | Jargon/100w "
         "| Abstract nouns/100w | Fog |",
         "|---|--:|--:|--:|--:|--:|--:|--:|"]
    order = sorted(res["sections"].items(),
                   key=lambda kv: -kv[1]["jargon_per_100w"])
    for sec, st in order:
        L.append(f"| {sec} | {st['words']} | {st['mean_sentence']} | "
                 f"{st['max_sentence']} | {st['long_count']} | "
                 f"{st['jargon_per_100w']} | {st['nom_per_100w']} | "
                 f"{st['fog_score']} |")

    L += ["", "## 2. Longest sentences", "",
          f"{len(res['long_sentences'])} sentences are >= {LONG_SENTENCE} "
          f"words; "
          f"{sum(1 for s in res['long_sentences'] if s['words'] >= VERY_LONG_SENTENCE)}"
          f" are >= {VERY_LONG_SENTENCE}.", ""]
    for s in sorted(res["long_sentences"], key=lambda r: -r["words"])[:15]:
        L.append(f"- **{s['words']} words**, {s['em_dashes']} em-dashes "
                 f"&mdash; `paper/{s['file']}:{s['line']}` ({s['section']}, "
                 f"{s['kind']}): {s['text'][:180]}...")

    L += ["", "## 3. Acronyms", "",
          "| Acronym | Uses | Status |", "|---|--:|---|"]
    for acr, rec in sorted(res["acronyms"].items(),
                           key=lambda kv: (kv[1]["status"] == "defined at first use",
                                           -kv[1]["count"])):
        L.append(f"| {acr} | {rec['count']} | {rec['status']} |")

    L += ["", "## 4. Lexicon hits", "",
          "Severity 3 = a reader outside the subfield will not know it, or "
          "knows it to mean something else. 2 = guessable, gloss at first use. "
          "1 = fine in Experimental/SI.", "",
          "| Term | Hits | Sev | Category | Lines | Plain gloss |",
          "|---|--:|--:|---|---|---|"]
    rows = []
    for pat, hits in res["jargon"].items():
        first = min(hits, key=lambda h: h["line"])
        rows.append((hits[0]["severity"], len(hits), first["match"], hits,
                     first))
    for sev, n, term, hits, first in sorted(rows, key=lambda r: (-r[0], -r[1])):
        locs = sorted({(h["file"], h["line"]) for h in hits})
        shown = ", ".join(f"{f.split('.')[0]}:{ln}" for f, ln in locs[:6])
        if len(locs) > 6:
            shown += ", ..."
        L.append(f"| {term} | {n} | {sev} | {hits[0]['category']} | "
                 f"{shown} | {hits[0]['gloss']} |")

    L += ["", "## 5. Stacked hyphenated modifiers", ""]
    for term, n in Counter(s["term"] for s in res["stacked_modifiers"]).most_common():
        locs = sorted({(s["file"], s["line"]) for s in res["stacked_modifiers"]
                       if s["term"] == term})
        shown = ", ".join(f"{f.split('.')[0]}:{ln}" for f, ln in locs)
        L.append(f"- `{term}` ({n}x &mdash; {shown})")

    L += ["", "## 6. Sentences with 2+ em-dash asides", "",
          f"{len(res['multi_dash'])} sentences carry two or more em-dash "
          f"asides; the 12 with the most are shown.", ""]
    for d in sorted(res["multi_dash"], key=lambda r: -r["em_dashes"])[:12]:
        L.append(f"- {d['em_dashes']} dashes, `paper/{d['file']}:{d['line']}` "
                 f"({d['section']}): {d['text'][:150]}...")

    L += ["", "## 7. References a reader outside the repo cannot resolve", ""]
    for name, hits in res["insider"].items():
        locs = sorted({(h["file"], h["line"]) for h in hits})
        shown = ", ".join(f"{f.split('.')[0]}:{ln}" for f, ln in locs)
        L.append(f"- **{name}**: {len(hits)} hits &mdash; {shown}")
    return "\n".join(L) + "\n"


def main() -> None:
    units = (load(PAPER / "main.tex", r"\section{Introduction}")
             + load(PAPER / "si.tex", r"\begin{document}"))
    full_text = " ".join(u["text"] for u in units)
    res = audit(units, full_text)
    counts = {"units": len(units), "words": len(words(full_text)),
              "sentences": sum(st["sentences"]
                               for st in res["sections"].values())}
    (HERE / "audit_report.md").write_text(report(res, counts))
    (HERE / "audit_report.json").write_text(
        json.dumps({"counts": counts, **res}, indent=2))
    print(f"{counts['words']} words, {counts['sentences']} sentences, "
          f"{len(res['long_sentences'])} long sentences, "
          f"{sum(len(v) for v in res['jargon'].values())} lexicon hits")
    print(f"wrote {HERE/'audit_report.md'}")


if __name__ == "__main__":
    main()
