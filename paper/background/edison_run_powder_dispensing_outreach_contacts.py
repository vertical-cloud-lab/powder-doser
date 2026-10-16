#!/usr/bin/env python3
"""Edison Scientific ``LITERATURE_HIGH`` query that identifies named
individuals and organizations the BYU Vertical Cloud Lab could reach out to
for help with **accurate, automated powder dispensing** for the powder-doser
project (issue #36 — "Determine individuals and organizations we could reach
out to for help with powder dispensing").

This is the powder-dispensing counterpart to the generative-CAD outreach
query in ``edison_run_outreach_contacts.py`` (PR #43, issues #6 / #27 / #29);
the prompt structure, output layout, and "do not invent emails" guardrail
are deliberately mirrored so the two synthesized notes are directly
comparable. Sources explicitly requested in the prompt include the
accelerated-discovery.org thread on accurate powder dispensing for
chemistry/materials-science (post URL embedded below) and the prior work
referenced in PR #29's ``paper/background/01-*.md`` and ``02-*.md``.

Output is written to ``paper/background/edison_artifacts/`` with the same
``<key>.task.json`` / ``<key>.answer.md`` / ``<key>.references.md`` layout
used by ``edison_run.py``, ``edison_run_followup_spatial.py``, and
``edison_run_outreach_contacts.py``. Re-run with::

    pip install edison_client
    export EDISON_API_KEY=...   # never commit this value
    python paper/background/edison_run_powder_dispensing_outreach_contacts.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "powder_dispensing_outreach_contacts": (
        "Identify named individuals and organizations a small university "
        "research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant "
        "scale, focused on self-driving labs for additive-manufacturing "
        "alloy discovery) could realistically reach out to for collaboration, "
        "advice, or technical support on **accurate, automated powder "
        "dispensing** for chemistry / materials-science / metal-AM "
        "applications in 2025-2026. The lab's specific need is a sub-$10k, "
        "multi-powder (~30 reservoirs), 250 mL/blend, +/- 1 mg accuracy "
        "dispenser able to handle metal-AM feedstock powders (Ti, Ni, HEAs, "
        "refractory) as well as ceramic / oxide / pharma-style powders, "
        "with future integration into an L-PBF / DED workflow. Cover the "
        "categories below and for EACH named contact give: full name, "
        "current affiliation / role, the specific reason they are relevant "
        "(1-3 sentences with concrete evidence — paper, repo, product, "
        "talk, forum post), AT LEAST ONE direct, *publicly listed* contact "
        "channel (institutional or company email, personal / lab website "
        "contact page, GitHub handle, Twitter/X handle, LinkedIn, "
        "Mastodon, lab Slack/Discord invite, conference Q&A channel, "
        "company sales/support address), and the FULL public URL where "
        "that contact info is listed so the claim can be verified. If "
        "only a lab/org-level contact is public (no individual email), "
        "say so explicitly and give the lab/org channel. Do NOT invent "
        "emails — if you cannot find a public address, say 'no public "
        "direct email found; reachable via <lab page URL> / <social handle>'.\n\n"
        "Seed sources you SHOULD mine for named individuals and verify "
        "their contact channels against:\n"
        "  - The accelerated-discovery.org forum thread 'Accurate powder "
        "dispensing for chemistry and materials science applications' at "
        "https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177 "
        "(participants include Sterling Baird (@sgbaird), Andrew Lee "
        "(@shijing), @loppe35, @muon, @kthchow, Matthew Reish (@mreish), "
        "Benji Maruyama (@benjimaruyama), and others — pull every named or "
        "handled participant and find their public lab/GitHub/X page).\n"
        "  - Cooper group PowderBot (https://arxiv.org/abs/2309.00544) and "
        "Ceder group A-Lab (https://www.nature.com/articles/s41586-023-06734-w).\n"
        "  - Vecchio group HT-READ (UCSD, ~50 alloys / 24 h, custom "
        "ChemSpeed + 16-hopper ADF + DED; manual powder handling was "
        "explicitly the bottleneck) and Charpagne et al. on graded-alloy "
        "discovery.\n"
        "  - OpenTrickler (https://github.com/eamars/OpenTrickler) and "
        "Autotrickler v4 (https://autotrickler.com/pages/autotrickler-v4).\n"
        "  - Pharma self-driving-lab community CMAC "
        "(https://www.cmac.ac.uk/) and Filippos Tourlomousis's "
        "$100 automated powder dispenser for biopolymers.\n"
        "  - INSSTEK clogged-vibration-mechanism doser "
        "(https://www.insstek.com/technology/cvm_powder).\n"
        "  - Commercial vendors with public engineering / sales contact "
        "pages: Mettler-Toledo Quantos / CHRONECT, Chemspeed Technologies "
        "(SWING / FLEX / overhead gravimetric dispenser), Unchained Labs, "
        "Hamilton, Thermo Fisher Scientific, Trajan, MTI Corporation "
        "(call this out explicitly — they sell feeders / micro-augers / "
        "powder-handling components used by university AM labs), "
        "Coperion K-Tron, Schenck Process, Gericke, Brabender Technologie, "
        "Movacolor, Sartorius, Freeman Technology (FT4 powder rheometer), "
        "A&D Company (FX-120i / HR-100A scales), CE Products, Emerald "
        "Cloud Lab.\n\n"
        "Categories to cover (aim for ~3-7 named contacts per category, "
        "~30-45 total):\n"
        "  1. **Forum / community participants** from the "
        "accelerated-discovery thread above and adjacent open-science "
        "powder-handling threads.\n"
        "  2. **Academic PIs and engineers working on automated powder "
        "dosing for chemistry / materials-science** (PowderBot, A-Lab, "
        "HT-READ, Bahr 2018/2020 work on Quantos dosing of sub-10 mg "
        "powders, Neirinck et al. on multi-material AM, CMAC powder "
        "flowability, Acceleration Consortium SDL work).\n"
        "  3. **Academic AM / DED / L-PBF groups** with hands-on powder "
        "handling experience (Vecchio @ UCSD, Tim Simpson @ Penn State "
        "CIMP-3D, Allison Beese @ Penn State, Iver Anderson @ Ames Lab — "
        "powder atomization, Tresa Pollock @ UCSB, Markl group @ FAU "
        "Erlangen, Wegener / Schuh @ ETH/RWTH, Wayne King ex-LLNL / "
        "Open Additive). Lab page + listed contact email + group GitHub.\n"
        "  4. **Commercial powder-dosing / feeding vendors** — give the "
        "publicly listed engineering / sales / dev-rel contact for each "
        "(Mettler-Toledo Quantos product line, Chemspeed Technologies, "
        "Unchained Labs, Hamilton Company, Thermo Fisher, Trajan, MTI "
        "Corporation, Coperion K-Tron, Schenck Process, Gericke, "
        "Brabender, Movacolor, Sartorius, Freeman Technology, A&D, "
        "Emerald Cloud Lab). Prioritize named application engineers / "
        "product managers / scientific support leads when their email "
        "or LinkedIn is publicly listed on the company site.\n"
        "  5. **Open-source / DIY powder-dosing maintainers and "
        "communities** (OpenTrickler maintainers, Autotrickler founders, "
        "the firearms-reloading community projects, Hackaday.io powder "
        "projects, the Acceleration Consortium SDL Slack/Discord, the "
        "Self-Driving Lab community channels, /r/reloading, "
        "/r/3Dprinting metal-AM threads).\n"
        "  6. **Adjacent self-driving-lab / agentic-hardware groups** that "
        "have published on powder handling end-to-end (Aspuru-Guzik / "
        "Acceleration Consortium, Andy Cooper @ Liverpool, Lee Cronin / "
        "Chemify, Milad Abolhasani @ NC State, Joshua Schrier @ Fordham, "
        "Keith Brown @ BU, Jason Hein, Ben Blaiszik / Ian Foster @ "
        "Argonne).\n"
        "  7. **Conferences, workshops, and funding / program officers** "
        "where a powder-dispensing collaboration ask is on-topic (MRS "
        "Spring/Fall powder-handling and AM symposia, TMS Annual, "
        "Acceleration Consortium meetings, NSF DMREF, NSF Future "
        "Manufacturing, ARPA-E DIFFERENTIATE, America Makes, NASA Space "
        "Grant program officers). Public program-officer page URL.\n\n"
        "Format the final answer as Markdown with one H2 per category "
        "and one H3 subsection per named contact (so each contact has its "
        "own anchor — e.g., '### Sterling Baird'). Each subsection must "
        "end with a parenthetical '(source: <full URL>)' tag pointing at "
        "the public page where the listed contact channel is shown, so a "
        "human can verify. If a person is highly relevant but you "
        "genuinely cannot find a public contact channel, still list them "
        "and say 'no public contact channel located' rather than "
        "fabricating one. Prioritize *direct, individual* channels over "
        "generic 'info@' inboxes when both are available. Aim for 30-45 "
        "named contacts total."
    ),
}

TAG = "powder-doser-grant"


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY (or EDISON_PLATFORM_API_KEY) is not set. "
            "Export it before running this script."
        )

    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)
    tasks = [
        {
            "name": JobNames.LITERATURE_HIGH,
            "query": q,
            "tags": [TAG, key, "outreach-contacts", "powder-dispensing"],
        }
        for key, q in QUERIES.items()
    ]
    print(f"Dispatching {len(tasks)} LITERATURE_HIGH tasks...", flush=True)
    results = client.run_tasks_until_done(
        tasks, verbose=True, progress_bar=False, timeout=3000
    )

    for key, result in zip(QUERIES.keys(), results):
        data = (
            result.model_dump() if hasattr(result, "model_dump") else dict(result)
        )
        (out_dir / f"{key}.task.json").write_text(
            json.dumps(data, default=str, indent=2)
        )
        try:
            answer = data["environment_frame"]["state"]["state"]["response"]["answer"]
            formatted = answer.get("formatted_answer") or answer.get("answer") or ""
            references = answer.get("references") or ""
        except (KeyError, TypeError):
            formatted, references = "", ""
        (out_dir / f"{key}.answer.md").write_text(formatted)
        (out_dir / f"{key}.references.md").write_text(references)
        print(
            f"  {key}: status={data.get('status')} "
            f"answer_chars={len(formatted)} refs_chars={len(references)}",
            flush=True,
        )

    print(f"Wrote artifacts to {out_dir}", flush=True)


if __name__ == "__main__":
    main()
