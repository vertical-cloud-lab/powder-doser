"""Generate the test-protocol table for the SI (and a markdown mirror).

The uniform powder test battery runs one frozen sequence of seven test
protocols on every powder, so results are directly comparable across
powders.  The protocol specification below is transcribed from the
firmware constants in ``hardware/test-module/firmware/powder_battery.py``
(``BATTERY_VERSION = 2``, on the ``claude/issue-116-*`` branches); the
as-run coverage columns of the markdown table are computed from the tidy
CSVs in ``paper/figures/candidates/data/`` so they cannot drift from the
data.

The firmware and the raw CSV schema label the protocols ``A``--``G`` in a
field named ``block``.  That field name is part of the serial protocol and
is left alone; only the prose and the tables say "test protocol".

    python make_protocol_table.py      # -> test_protocols.tex, TEST-PROTOCOLS.md

Then rebuild the SI and refresh the preview crop that TEST-PROTOCOLS.md
embeds (page and crop box track the table's position in si.pdf)::

    cd .. && latexmk -pdf si.tex
    pdftoppm -png -r 150 -f 3 -l 3 -x 100 -y 430 -W 1180 -H 810 \\
        si.pdf protocols/test_protocols_preview && \\
        mv protocols/test_protocols_preview-3.png \\
           protocols/test_protocols_preview.png
"""

import collections
import csv
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "figures" / "candidates" / "data"

# ----------------------------------------------------------------------
# Protocol specification -- frozen firmware parameters (battery_version 2).
#
# tilt convention: 0 deg = auger tube horizontal, 90 deg = vertical.
# "trials" counts the machine-readable trial rows the protocol emits per
# run, which is what the analysis treats as its unit of replication.
# ----------------------------------------------------------------------
PROTOCOLS = [
    dict(
        key="A",
        name="Balance baseline",
        varies="Nothing",
        fixed="Tilt 45°; 8 reads",
        measures="Mass change with no actuator commanded, giving the "
                 "per-run noise floor every other protocol is read against",
        trials="8",
    ),
    dict(
        key="B",
        name="Static hold",
        varies="Tilt (0/45/90°)",
        fixed="15 s hold; no actuation",
        measures="Spontaneous discharge under gravity alone, separating "
                 "free-flowing powders from those needing actuation and "
                 "testing the horizontal-park shutoff claim",
        trials="3",
    ),
    dict(
        key="C",
        name="Rotation yield",
        varies="Tilt (0/45/90°)",
        fixed="6 × 360° steps; 30 rpm",
        measures="Mass delivered per auger revolution and its "
                 "revolution-to-revolution spread, i.e. the feed factor "
                 "and precision at each tilt",
        trials="18",
    ),
    dict(
        key="D",
        name="Speed sweep",
        varies="Auger speed (15/45/90 rpm)",
        fixed="Tilt 45°; 3 rev continuous; balance streamed every 250 ms",
        measures="Mass flow rate versus rotation speed, and the "
                 "within-revolution pulsation of the discharge from the "
                 "streamed mass trace",
        trials="3 (+ polls)",
    ),
    dict(
        key="E",
        name="Tap yield",
        varies="Tilt (0/45°)",
        fixed="8 trials × (360° re-feed + 1 solenoid tap, 60 ms on)",
        measures="Mass released per solenoid tap, with the metered re-feed "
                 "rotation logged separately so the tap delta is tap-only",
        trials="32",
    ),
    dict(
        key="F",
        name="Vibration yield",
        varies="Tilt (0/45°)",
        fixed="As protocol E, with 3 ERM bursts replacing the tap",
        measures="Mass released per vibration burst, the counterpart of "
                 "protocol E for the eccentric-rotating-mass actuator",
        trials="32",
    ),
    dict(
        key="G",
        name="Closed-loop dose",
        varies="Nothing",
        fixed="3 doses; 1.000 g target; three-phase controller",
        measures="Delivered mass, dose error, time to dose, and the "
                 "bulk/fine/tap cycle breakdown of the closed-loop "
                 "controller",
        trials="3 doses",
    ),
]

CAPTION = (
    r"Uniform powder test battery. Seven test protocols are run in a fixed "
    r"order with frozen parameters on every powder, so that the results are "
    r"directly comparable across powders; the battery is a characterization "
    r"sequence rather than an optimization workflow. Protocols A--F "
    r"characterize the actuation primitives one at a time, and protocol G "
    r"exercises the three-phase closed-loop controller built on them. Tilt is "
    r"measured from horizontal (0$^\circ$ = auger tube horizontal, "
    r"90$^\circ$ = vertical). \emph{Trials} is the number of machine-readable "
    r"trial records each protocol emits per run, which is the unit of "
    r"replication in the analysis. Parameter values are the frozen defaults of "
    r"the battery firmware "
    r"(\texttt{hardware/test-module/firmware/powder\_battery.py}), which "
    r"identifies the protocols by the same letters."
)


# Unicode source text -> LaTeX.  The table body is authored once, in plain
# text, so the markdown mirror and the SI table cannot disagree.
_TEX_SUBS = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("_", r"\_"),
    ("#", r"\#"),
    ("\u00b0", r"$^\circ$"),
    ("\u00d7", r"$\times$"),
    ("\u2013", "--"),
    ("\u2014", "---"),
    ("i.e. ", "i.e.\\ "),
]

# Numbers glued to their units with a non-breaking space.
_UNITS = ("s", "ms", "g", "mg", "rpm", "rev", "reads", "doses", "trials")


def _tex(text):
    """Render one plain-text table cell as LaTeX."""
    for src_ch, dst in _TEX_SUBS:
        text = text.replace(src_ch, dst)
    return re.sub(
        r"(\d)\s+({})\b".format("|".join(_UNITS)), r"\1~\2", text
    )


def latex_table():
    lines = [
        "% Generated by paper/protocols/make_protocol_table.py -- do not edit by hand.",
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        r"\setlength{\tabcolsep}{4pt}",
        r"\caption{" + CAPTION + "}",
        r"\label{tbl:protocols}",
        r"\begin{tabular}{@{}l"
        r" >{\raggedright\arraybackslash}p{2.5cm}"
        r" >{\raggedright\arraybackslash}p{4.0cm}"
        r" >{\raggedright\arraybackslash}p{5.3cm} l@{}}",
        r"\toprule",
        r"\textbf{Protocol} & \textbf{Varied factor} & "
        r"\textbf{Fixed parameters} & \textbf{Quantity measured} & "
        r"\textbf{Trials} \\",
        r"\midrule",
    ]
    for p in PROTOCOLS:
        lines.append(
            "{} {} & {} & {} & {} & {} \\\\".format(
                p["key"],
                _tex(p["name"]),
                _tex(p["varies"]),
                _tex(p["fixed"]),
                _tex(p["measures"]),
                _tex(p["trials"]),
            )
        )
        lines.append(r"\addlinespace[2pt]")
    lines = lines[:-1]  # drop the trailing \addlinespace
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def _coverage():
    """As-run coverage of each protocol in the round-1 campaign."""
    runs = list(csv.DictReader(open(DATA / "runs.csv")))
    trials = list(csv.DictReader(open(DATA / "trials.csv")))
    doses = list(csv.DictReader(open(DATA / "doses.csv")))

    requested = collections.Counter()
    for run in runs:
        for key in run["blocks"]:
            requested[key] += 1

    produced_rows = collections.Counter(t["block"] for t in trials)
    produced_runs = collections.defaultdict(set)
    for t in trials:
        produced_runs[t["block"]].add(t["run_id"])
    produced_rows["G"] = len(doses)
    produced_runs["G"] = {d["run_id"] for d in doses}

    return {
        p["key"]: (
            requested[p["key"]],
            produced_rows[p["key"]],
            len(produced_runs[p["key"]]),
        )
        for p in PROTOCOLS
    }, len(runs)


def markdown_table():
    cov, n_runs = _coverage()
    out = [
        "# Test protocols",
        "",
        "The uniform powder test battery runs one frozen sequence of seven",
        "**test protocols** on every powder, so results are directly comparable",
        "across powders. It is a characterization sequence, not an optimization",
        "workflow: the parameters are fixed and the point is to see how each",
        "powder behaves under identical conditions.",
        "",
        "Protocols A–F characterize the actuation primitives one at a time;",
        "protocol G exercises the three-phase closed-loop controller built on",
        "them. Tilt is measured from horizontal (0° = auger tube horizontal,",
        "90° = vertical).",
        "",
        "The firmware and the raw CSVs identify these by the same letters, in a",
        "field named `block`; that field name is part of the serial protocol and",
        "is unchanged. Only the prose and tables say *test protocol*.",
        "",
        "## Specification",
        "",
        "As typeset in the SI (Table S2):",
        "",
        "![Test-protocol table as typeset in the SI](test_protocols_preview.png)",
        "",
        "Parameters are the frozen defaults of",
        "`hardware/test-module/firmware/powder_battery.py` (`BATTERY_VERSION = 2`).",
        "*Trials* is the number of machine-readable trial records each protocol",
        "emits per run — the unit of replication in the analysis.",
        "",
        "| Protocol | Varied factor | Fixed parameters | Quantity measured | Trials |",
        "|---|---|---|---|---|",
    ]
    for p in PROTOCOLS:
        out.append(
            "| **{}** {} | {} | {} | {} | {} |".format(
                p["key"],
                p["name"],
                p["varies"],
                p["fixed"],
                p["measures"],
                p["trials"],
            )
        )

    out += [
        "",
        "## As-run coverage, round-1 campaign",
        "",
        "Computed from the tidy CSVs in `../figures/candidates/data/` by",
        "`make_protocol_table.py`, over the {} runs of the round-1 campaign".format(n_runs),
        "(2026-08-04 to 2026-08-21, 13 powders). *Requested* counts runs whose",
        "`blocks` string asked for the protocol; *records* counts the trial (or",
        "dose) rows it actually produced.",
        "",
        "| Protocol | Runs requesting | Runs producing records | Records |",
        "|---|---|---|---|",
    ]
    for p in PROTOCOLS:
        req, rows, runs_ok = cov[p["key"]]
        out.append(
            "| **{}** {} | {} | {} | {} |".format(
                p["key"], p["name"], req, runs_ok, rows
            )
        )

    req_f, rows_f, _ = cov["F"]
    out += [
        "",
        "**Protocol F produced no records in any run.** {} runs asked for it and".format(req_f),
        "each got a skip record: the DRV2605L haptic driver reports `EIO`, so the",
        "vibration actuator is uncharacterized across the whole campaign. The",
        "Experimental section already states that the ERM motor is not used in the",
        "baseline dosing procedure, but the abstract and platform overview still",
        "advertise vibration assistance, and the planned actuation ablation has no",
        "vibration arm to report.",
        "",
        "Protocol E emits 32 records in a complete run (two tilts × 8 trials × two",
        "records per trial: the metered re-feed rotation and the tap itself); one",
        "truncated run contributed 16.",
        "",
    ]
    return "\n".join(out)


def main():
    (HERE / "test_protocols.tex").write_text(latex_table())
    (HERE / "TEST-PROTOCOLS.md").write_text(markdown_table())
    print("wrote test_protocols.tex and TEST-PROTOCOLS.md")


if __name__ == "__main__":
    main()
