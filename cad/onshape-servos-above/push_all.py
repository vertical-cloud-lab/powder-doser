"""Push every part script into the servos-above document as a native feature tree (once API calls are available).

    python push_all.py --plan                # 0 calls: fsgen's offline estimate for each part, and the total
    python push_all.py --go                  # adopt the auger, push every part, rename and share the document
    python push_all.py --go --only bracket   # just these parts (script stems)
    python push_all.py --go --only auger_cap --document <URL>   # into another document you can edit

``--document`` pushes into any document whose URL you give (e.g. an empty one created in the browser in
``vcl-shared``, so it takes that folder's sharing), with the keys in your environment. It leaves the
servos-above document alone: no adopting, renaming or sharing, and every part is pushed as new.

The 2026-10-27 and 2026-10-29 runs could not push: every document request returned HTTP 402 "API limit exceeded"
(the yearly allowance the repo's key draws on). This script is the push they would have made. Order:

1. ``onshape_doc.py adopt --studio Auger`` (2 calls). The 2026-10-20 run pushed the auger but its fsgen state
   was lost with the runner; without it fsgen would build a second auger instead of updating the first. The
   auger's push then re-sends what fsgen_patches.diff changed (about 5 calls), and its tab gets renamed (1).
2. ``fsgen studio push parts/<stem>.fs --name <title> --document <url> --metrics``, one Part Studio per part,
   each with a hard budget of its estimate + 3. It stops at the first part that fails or overspends.
3. ``onshape_doc.py rename-doc`` (1 call) and ``share`` (2: the company's id, then the share).

Run from this folder with ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY set and fsgen 0.2.0 plus fsgen_patches.diff.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from assemble_paste import TITLES  # noqa: E402  (script stem -> Part Studio name)

FSGEN = os.environ.get("FSGEN", "fsgen")
EST = re.compile(r"estimated Onshape API calls: (\d+)")


def doc_url(document: str | None = None) -> str:
    return document or json.loads((HERE / "onshape_document.json").read_text())["url"]


def adopted(stem: str) -> bool:
    rec = json.loads((HERE / "onshape_document.json").read_text())
    state = HERE / ".fsgen_native.json"
    return state.exists() and f"{TITLES[stem]}@{rec['workspaceId']}" in json.loads(state.read_text())


def estimate(stem: str, document: str | None = None) -> tuple[int, str]:
    """fsgen's own estimate for pushing this part into the document (0 calls: the keys are removed)."""
    if stem == "auger" and document is None and not adopted(stem):
        # already in Onshape; fsgen can't see that until adopt has rebuilt its state. Counted offline with
        # onshape_doc._num_020: the push then re-sends 2 sketches whose expressions gain digits, the variables,
        # and checks the reused features' status and the volume
        return 5, "push to \"Auger\" (update, after adopt): 2 sketches + variables 1 + status check 1 + volume check 1"
    env = {k: v for k, v in os.environ.items() if k not in ("ONSHAPE_ACCESS_KEY", "ONSHAPE_SECRET_KEY")}
    out = subprocess.run([FSGEN, "studio", "check", str(HERE / "parts" / f"{stem}.fs"), "--name", TITLES[stem],
                          "--document", doc_url(document), "--metrics"], cwd=HERE, env=env, capture_output=True,
                         text=True, timeout=1800).stdout
    m = EST.search(out)
    if not m:
        raise SystemExit(f"{stem}: no estimate in fsgen's output:\n{out[-2000:]}")
    line = next(ln for ln in out.splitlines() if "estimated Onshape API calls" in ln)
    return int(m.group(1)), line.strip()


def run(cmd: list[str], log: Path) -> None:
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=3600)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(r.stdout + r.stderr)
    print("\n".join((r.stdout + r.stderr).splitlines()[-12:]))
    if r.returncode != 0:
        raise SystemExit(f"stopped: {' '.join(cmd[:4])} failed (log: {log.relative_to(HERE)})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--document", help="push into this document (URL) instead of the servos-above document")
    a = ap.parse_args()
    stems = [s for s in TITLES if not a.only or s in a.only]
    own = a.document is None     # the servos-above document: adopt the auger, rename and share
    plan = {}
    for stem in stems:
        n, line = estimate(stem, a.document)
        plan[stem] = n
        print(f"{stem:30s} {line}")
    if own:
        extra = (3 if "auger" in stems else 0) + 3   # adopt (2), rename the auger's tab (1); rename doc (1), share (2)
        total = sum(plan.values()) + extra
        what = ("adopt the auger and rename its tab, " if "auger" in stems else "") + "rename the document, share"
        print(f"total: {sum(plan.values())} for the parts + {extra} ({what}) = {total} calls")
        (HERE / "results").mkdir(exist_ok=True)
        (HERE / "results" / "push_plan.json").write_text(json.dumps({"calls_per_part": plan, "total": total},
                                                                    indent=1) + "\n")
    else:
        print(f"total: {sum(plan.values())} calls into {a.document}")
    if not a.go:
        return
    py = sys.executable
    if own and "auger" in stems:
        run([py, "onshape_doc.py", "adopt", "--studio", TITLES["auger"], "--script", "parts/auger.fs",
             "--budget", "2"], HERE / "results" / "push_logs" / "adopt_auger.log")
    for stem in stems:
        run([FSGEN, "studio", "push", f"parts/{stem}.fs", "--name", TITLES[stem], "--document", doc_url(a.document),
             "--metrics", "--budget", str(plan[stem] + 3)], HERE / "results" / "push_logs" / f"{stem}.log")
        if own and stem == "auger":     # the 2026-10-20 push built in the default tab, "Part Studio 1"
            run([py, "onshape_doc.py", "rename", "--studio", TITLES[stem], "--budget", "1"],
                HERE / "results" / "push_logs" / "rename_auger.log")
    if own:
        run([py, "onshape_doc.py", "rename-doc", "--budget", "1"], HERE / "results" / "push_logs" / "rename_doc.log")
        run([py, "onshape_doc.py", "share", "--budget", "2"], HERE / "results" / "push_logs" / "share.log")


if __name__ == "__main__":
    main()
