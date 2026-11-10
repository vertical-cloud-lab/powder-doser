#!/usr/bin/env python3
"""Fetch and archive the round-2 verification ANALYSIS tasks dispatched by
figure_review_round3.py.

Reads figure_review_round3_task_ids.json (flat {"tasks": {fig: id}}), polls each
task, and writes results/verify3__<figure>.answer.md (+ .notebook.ipynb) and a
results/INDEX_round3.md status roll-up.

Usage:
  export EDISON_API_KEY=...   # or EDISON_PLATFORM_API_KEY
  python fetch_figure_reviews_round3.py [--minutes 20]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from edison_client import EdisonClient

from fetch_figure_reviews import _api_key, _answer, _dump, _notebook

HERE = Path(__file__).resolve().parent
IDS = HERE / "figure_review_round3_task_ids.json"
RESULTS = HERE / "results"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=20.0)
    ap.add_argument("--poll", type=float, default=30.0)
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60

    RESULTS.mkdir(exist_ok=True)
    record = json.loads(IDS.read_text())
    client = EdisonClient(api_key=_api_key())

    tasks = list(record["tasks"].items())  # (fig, task_id)
    done: dict[str, str] = {}
    while True:
        pending = [t for t in tasks if t[0] not in done]
        if not pending:
            break
        for fig, tid in pending:
            try:
                data = _dump(client.get_task(tid))
            except Exception as exc:  # noqa: BLE001
                print(f"  verify3__{fig} get_task error: {exc}", flush=True)
                continue
            status = str(data.get("status", "")).lower()
            if status in {"success", "fail", "cancelled", "truncated"}:
                answer = _answer(data)
                (RESULTS / f"verify3__{fig}.answer.md").write_text(answer)
                nb = _notebook(data)
                if nb is not None:
                    (RESULTS / f"verify3__{fig}.notebook.ipynb").write_text(
                        json.dumps(nb, default=str, indent=2)
                    )
                done[fig] = status
                print(f"  verify3__{fig}: {status} ({len(answer)} chars)", flush=True)
        if len(done) == len(tasks):
            break
        if time.time() > deadline:
            print("Time budget reached; remaining tasks fetch next session.",
                  flush=True)
            break
        time.sleep(args.poll)

    lines = ["# Round-3 figure verification — status index\n"]
    for fig, tid in tasks:
        lines.append(f"- {fig}: `{tid}` — **{done.get(fig, 'pending')}**")
    (RESULTS / "INDEX_round3.md").write_text("\n".join(lines) + "\n")
    print(f"Archived {len(done)}/{len(tasks)} round-2 results to {RESULTS}",
          flush=True)


if __name__ == "__main__":
    main()
