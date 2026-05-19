#!/usr/bin/env python3
"""Edison Scientific ``LITERATURE_HIGH`` query that identifies named
individuals and organizations the BYU Vertical Cloud Lab could reach out to
for help with **generative CAD** for the powder-doser project (issues #6, #7,
#27, #29).

The ask, set by the parent issue, is for *direct, public* contact info for
each person/organization (email, lab site, Twitter/X, GitHub, LinkedIn, etc.)
with a citable public URL for that contact info — no scraping of private data.

Output is written to ``paper/background/edison_artifacts/`` with the same
``<key>.task.json`` / ``<key>.answer.md`` / ``<key>.references.md`` layout as
the four queries dispatched by ``edison_run.py`` and the follow-up dispatched
by ``edison_run_followup_spatial.py`` (see PR #29). Re-run with::

    pip install edison_client
    export EDISON_API_KEY=...
    python paper/background/edison_run_outreach_contacts.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames

QUERIES: dict[str, str] = {
    "gencad_outreach_contacts": (
        "Identify named individuals and organizations a small university "
        "research lab (BYU Vertical Cloud Lab, ~3 people, NASA Space Grant "
        "scale, focused on self-driving labs for additive-manufacturing "
        "alloy discovery) could realistically reach out to for collaboration, "
        "advice, or technical support on **generative CAD for engineering "
        "hardware** in 2025-2026. The lab's specific need is agentic, "
        "code-based, manufacturability-aware generative CAD of small "
        "mechanical assemblies (a 30-reservoir powder doser, 250 mL/blend, "
        "+/-1 mg accuracy, FDM/SLA-printed on a Bambu H2D, with a future "
        "L-PBF integration path) where an LLM/agent loop writes CadQuery / "
        "build123d / OpenSCAD code, slices it, and ideally drives the "
        "printer end-to-end. Cover the following categories and for EACH "
        "named contact give: full name, current affiliation/role, the "
        "specific reason they are relevant (1-3 sentences with concrete "
        "evidence — paper, repo, product, talk), AT LEAST ONE direct, "
        "*publicly listed* contact channel (institutional or company email, "
        "personal/lab website contact page, GitHub handle, Twitter/X handle, "
        "LinkedIn, Mastodon, lab Slack/Discord invite, conference Q&A "
        "channel), and the FULL public URL where that contact info is listed "
        "so the claim can be verified. If only a lab/org-level contact is "
        "public (no individual email), say so explicitly and give the lab/org "
        "channel. Do NOT invent emails — if you cannot find a public address, "
        "say 'no public direct email found; reachable via <lab page URL> / "
        "<social handle>'.\n\n"
        "Categories to cover (aim for ~3-6 named contacts per category, "
        "~25-40 total):\n"
        "  1. **Academic CAD-LLM / generative-CAD researchers** — authors of "
        "DeepCAD (Rundi Wu / Changxi Zheng @ Columbia), Text2CAD / "
        "Text-to-CADQuery (Xie et al.), CAD-Recode (Rukhovich et al.), "
        "CADCrafter, CADSmith, GenCAD / GenCAD-Self-Repairing, ArtiCAD, "
        "CADReview, SkexGen, SketchGraphs (Princeton/Adobe), Fusion 360 "
        "Gallery (Autodesk Research), ABC dataset, BlenderBench, Sadik 2025. "
        "For each first author or PI: institution page, lab page, email "
        "(if listed), GitHub, X/Twitter.\n"
        "  2. **Code-CAD / programmatic-CAD open-source maintainers** — "
        "CadQuery (Adam Urbanczyk / Jeremy Wright / CadQuery org), "
        "build123d (Roger Maitland / gumyr), OpenSCAD (Marius Kintel + "
        "core team), SolidPython / SolidPython2, JSCAD, FreeCAD "
        "(Brad Collette / Yorik van Havre / FPA), OCP / OCCT Python bindings "
        "(CadQuery org / Open Cascade), KiCad mech-equivalent libs. "
        "Provide GitHub handle + project Discord/forum + maintainer email "
        "if posted in the project README/AUTHORS.\n"
        "  3. **Commercial generative-design / CAD-API contacts** — "
        "Autodesk Research (Karl Willis, Hooman Shayani, Yewen Pu — Fusion "
        "360 Gallery / generative design / CAD-as-program), nTopology "
        "(Bradley Rothenberg, developer relations), PTC Creo Generative "
        "Topology Optimization, Siemens NX / Solid Edge generative, "
        "Onshape / PTC FeatureScript developer relations, Rhino+Grasshopper "
        "(McNeel — Steve Baer, Brian James, dev outreach), Shapr3D, "
        "Zoo.dev / KittyCAD (Jess Frazelle and team — text-to-CAD API), "
        "CADL / Adam (Spline / similar AI-CAD startups), Plasticity "
        "(Nick Kallen). Provide the developer-relations / research-contact "
        "address listed on the company site (e.g., 'research@autodesk.com', "
        "'devrel@kittycad.io'), plus founder/PM social handles where public.\n"
        "  4. **Self-driving-lab / agentic-hardware groups already mixing "
        "LLMs with physical hardware** — Alan Aspuru-Guzik (U. Toronto / "
        "Acceleration Consortium), Andy Cooper (Liverpool — mobile robot "
        "chemist), Lee Cronin (Glasgow — Chemify), Ben Blaiszik / Ian "
        "Foster (Argonne / Globus), Milad Abolhasani (NC State), Joshua "
        "Schrier (Fordham), Keith Brown (BU — Bayesian self-driving "
        "mechanics lab), Alexander Norman / Mat Tantum / Jason Hein. For "
        "each: lab page + listed contact email + group GitHub.\n"
        "  5. **Additive-manufacturing + design-for-AM experts who routinely "
        "co-author with software/AI groups** — Tim Simpson (Penn State CIMP-"
        "3D), Wayne King (ex-LLNL, now Open Additive), Allison Beese (Penn "
        "State), Iver Anderson (Ames Lab — atomization), Tresa Pollock "
        "(UCSB), Vecchio group (UCSD — HT-READ), Markl group (FAU "
        "Erlangen), Wegener / Schuh (ETH/RWTH). Lab page + dept email.\n"
        "  6. **Communities, Slacks, Discords, mailing lists, and "
        "conferences** that are realistic 'cold-post' venues — CadQuery "
        "Discord, build123d Discord, FreeCAD forum, OpenSCAD subreddit, "
        "Hackaday.io, /r/cad and /r/3Dprinting, the AI-Plus-Hardware Slack, "
        "Acceleration Consortium Slack, the SDL community Discord, the "
        "Generative Design subreddit, AAAI workshops on geometric / "
        "engineering ML, NeurIPS ML4CAD / ML4Eng workshops, ASME IDETC-CIE "
        "(JCISE), CAD'25 conference, SCF (Symposium on Computational "
        "Fabrication). Give the public invite URL or the conference/chair "
        "contact email.\n"
        "  7. **Funding / program officers and incubators** likely to "
        "advise an academic team standing up agentic CAD work — NSF "
        "Designing Materials to Revolutionize and Engineer our Future "
        "(DMREF), NSF Future Manufacturing, ARPA-E DIFFERENTIATE, DARPA "
        "ML/CAD-adjacent program managers, America Makes, Manufacturing "
        "USA institutes, Schmidt Futures Polymathic AI, Acceleration "
        "Consortium funding leads. Public program-officer page URL.\n\n"
        "Format the final answer as Markdown with one H2 per category and "
        "one bullet per contact. Each bullet must end with a parenthetical "
        "'(source: <full URL>)' tag pointing at the public page where the "
        "listed contact channel is shown, so a human can verify. If a "
        "person is highly relevant but you genuinely cannot find a public "
        "contact channel, still list them and say 'no public contact "
        "channel located' rather than fabricating one. Prioritize *direct, "
        "individual* channels over generic 'info@' inboxes when both are "
        "available. Aim for 25-40 named contacts total."
    ),
}

TAG = "powder-doser-grant"


def main() -> None:
    api_key = os.environ.get("EDISON_API_KEY")
    if not api_key:
        raise SystemExit(
            "EDISON_API_KEY is not set. Export it before running this script."
        )

    out_dir = Path(__file__).parent / "edison_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = EdisonClient(api_key=api_key)
    tasks = [
        {
            "name": JobNames.LITERATURE_HIGH,
            "query": q,
            "tags": [TAG, key, "outreach-contacts"],
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
