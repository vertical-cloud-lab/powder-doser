"""Run fsgen's own push code for one part against fsgen's fake Onshape: the exact requests and their count, 0 calls.

    python dry_run_push.py auger_cap                    # into the servos-above document (onshape_document.json)
    python dry_run_push.py auger_cap --document <URL>   # into another document, e.g. an empty one made in vcl-shared

Writes results/dry_run/<stem>.json: every request the push would send (method, endpoint, JSON body) and the
billable count. fsgen's fake (fsgen.costmodel.fake_onshape) intercepts every request in-process, so nothing
reaches Onshape and the real keys are never read. The fake answers every feature with OK, so this checks the
request sequence and the cost; whether Onshape regenerates each feature is only known after the real push.
State goes to a temporary folder, so the real .fsgen_native.json and call ledger are untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from fsgen.cloud import parse_document
from fsgen.costmodel import fake_onshape
from fsgen.native import build as nb
from fsgen.native.script import trace
from fsgen.onshape import Onshape, endpoint_key
from fsgen.usage import estimate_push

from assemble_paste import TITLES

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stem", choices=list(TITLES), help="part script in parts/")
    ap.add_argument("--document", help="target document URL (default: onshape_document.json)")
    a = ap.parse_args()
    url = a.document or json.loads((HERE / "onshape_document.json").read_text())["url"]
    tr = trace((HERE / "parts" / f"{a.stem}.fs").read_text())
    if not tr.ok:
        raise SystemExit(f"script error: {tr.error}")
    est = estimate_push(tr, None, metrics=True)
    ws = parse_document(url)
    sent = []
    with tempfile.TemporaryDirectory() as tmp, fake_onshape() as fake:
        cwd = Path.cwd()
        os.chdir(tmp)
        os.environ["ONSHAPE_ACCESS_KEY"] = os.environ["ONSHAPE_SECRET_KEY"] = "dry-run"
        answer = fake.request

        def record(method, req_url, json=None, **kw):
            sent.append({"call": endpoint_key(method, req_url), "body": json})
            return answer(method, req_url, json=json, **kw)

        fake.request = record
        try:
            o = Onshape(purpose=f"dry run {a.stem}")
            st = nb.get_studio(o, TITLES[a.stem], ws["did"], ws["wid"])
            r = nb.push_trace(o, st, tr, log=lambda s: None)
            nb.studio_metrics(o, st)
        finally:
            os.chdir(cwd)
    out = HERE / "results" / "dry_run" / f"{a.stem}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"part": a.stem, "studio": TITLES[a.stem], "document": url, "ok": r.ok,
                               "billable_calls": o.calls, "estimate": est.total, "requests": sent}, indent=1) + "\n")
    for s in sent:
        body = s["body"] if isinstance(s["body"], dict) else {}
        print(f"  {s['call']:58s} {(body.get('feature') or {}).get('name', '')}")
    print(f"{a.stem}: push {'OK' if r.ok else 'FAILED'} against the fake, {o.calls} billable calls "
          f"(fsgen's estimate {est.total}) -> {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
