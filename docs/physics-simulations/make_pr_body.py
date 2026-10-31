#!/usr/bin/env python3
"""Draft the per-run sections of the PR description from runs/*/README.md and result.json.

Usage: python make_pr_body.py <short-sha> > /tmp/pr_runs.md
Images are linked through the commit so the PR keeps showing what was committed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
REPO = "https://github.com/vertical-cloud-lab/powder-doser"
sys.path.insert(0, str(HERE))
from collect_results import ORDER  # noqa: E402


def section(md: str, name: str) -> str:
    m = re.search(rf"^#+\s*{re.escape(name)}[^\n]*\n(.*?)(?=^#+\s|\Z)", md, flags=re.S | re.M | re.I)
    return m.group(1).strip() if m else ""


def first_para(text: str, n: int = 700) -> str:
    paras = [p.strip() for p in text.strip().split("\n\n") if p.strip() and not p.strip().startswith("![")]
    para = " ".join(paras[0].split()) if paras else ""
    return para if len(para) <= n else para[:n].rsplit(" ", 1)[0] + " …"


def main(sha: str) -> None:
    ids = [p.name for p in sorted(RUNS.iterdir()) if p.is_dir()]
    ids = [i for i in ORDER if i in ids] + [i for i in ids if i not in ORDER]
    out = []
    for rid in ids:
        d = RUNS / rid
        md = (d / "README.md").read_text() if (d / "README.md").exists() else ""
        r = json.loads((d / "result.json").read_text()) if (d / "result.json").exists() else {}
        title = md.splitlines()[0].lstrip("# ").strip() if md else rid
        base = f"{REPO}/blob/{sha}/docs/physics-simulations/runs/{rid}"
        gifs = sorted(d.glob("*.gif"))
        pngs = sorted(d.glob("*.png"))
        mp4s = sorted(d.glob("*.mp4"))
        out.append(f"#### `{rid}`: {title}\n")
        out.append(f"**Status: {r.get('status', 'no result.json')}** · {r.get('code', '')} {r.get('version', '')} · "
                   f"[README]({base}/README.md) · [folder]({REPO}/tree/{sha}/docs/physics-simulations/runs/{rid})"
                   + "".join(f" · [{m.name}]({base}/{m.name})" for m in mp4s) + "\n")
        what = first_para(section(md, "What it models"))
        if what:
            out.append(f"- **What:** {what}")
        res = first_para(section(md, "Result"), 900)
        if res:
            out.append(f"- **Result:** {res}")
        st = first_para(section(md, "Status"), 500)
        if st:
            out.append(f"- **Status detail:** {st}")
        lim = first_para(section(md, "Limitations"), 400)
        if lim:
            out.append(f"- **Limitations:** {lim}")
        out.append("")
        for g in gifs[:1]:
            out.append(f"![{rid}]({base}/{g.name}?raw=true)\n")
        for p in pngs[:2 if not gifs else 1]:
            out.append(f"![{rid}]({base}/{p.name}?raw=true)\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1])
