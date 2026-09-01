#!/usr/bin/env python3
"""Fetch and archive the per-figure Edison ANALYSIS review tasks dispatched by
figure_review_batches.py.

Reads figure_review_task_ids.json, polls each task, and writes for every
completed task:
  results/<batch>__<figure>.answer.md          -- the analysis answer
  results/<batch>__<figure>.notebook.ipynb     -- the notebook state (if any)
and a roll-up results/INDEX.md with status for all 36 tasks.

Usage:
  export EDISON_API_KEY=...   # or EDISON_PLATFORM_API_KEY
  python fetch_figure_reviews.py [--minutes 20]
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from edison_client import EdisonClient

HERE = Path(__file__).resolve().parent
IDS = HERE / "figure_review_task_ids.json"
RESULTS = HERE / "results"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get(
        "EDISON_PLATFORM_API_KEY"
    )
    if not key:
        raise SystemExit("No EDISON_API_KEY / EDISON_PLATFORM_API_KEY set.")
    return key


def _dump(result) -> dict:
    return result.model_dump() if hasattr(result, "model_dump") else dict(result)


def _answer(data: dict) -> str:
    try:
        a = data["environment_frame"]["state"]["state"]["answer"]
        if a:
            return a
    except (KeyError, TypeError):
        pass
    return data.get("answer") or data.get("formatted_answer") or ""


def _notebook(data: dict):
    try:
        nb = data["environment_frame"]["state"]["state"]["nb_state"]
        if nb:
            return nb
    except (KeyError, TypeError):
        pass
    return data.get("notebook")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=20.0)
    ap.add_argument("--poll", type=float, default=30.0)
    args = ap.parse_args()
    deadline = time.time() + args.minutes * 60

    RESULTS.mkdir(exist_ok=True)
    record = json.loads(IDS.read_text())
    client = EdisonClient(api_key=_api_key())

    tasks = []  # (batch, fig, task_id)
    for batch, figs in record["batches"].items():
        for fig, tid in figs.items():
            tasks.append((batch, fig, tid))

    done: dict[str, str] = {}
    while True:
        pending = [t for t in tasks if f"{t[0]}__{t[1]}" not in done]
        if not pending:
            break
        for batch, fig, tid in pending:
            key = f"{batch}__{fig}"
            try:
                data = _dump(client.get_task(tid))
            except Exception as exc:  # noqa: BLE001
                print(f"  {key} get_task error: {exc}", flush=True)
                continue
            status = str(data.get("status", "")).lower()
            if status in {"success", "fail", "cancelled", "truncated"}:
                answer = _answer(data)
                (RESULTS / f"{key}.answer.md").write_text(answer)
                nb = _notebook(data)
                if nb is not None:
                    (RESULTS / f"{key}.notebook.ipynb").write_text(
                        json.dumps(nb, default=str, indent=2)
                    )
                done[key] = status
                print(f"  {key}: {status} ({len(answer)} chars)", flush=True)
        if len([t for t in tasks if f"{t[0]}__{t[1]}" in done]) == len(tasks):
            break
        if time.time() > deadline:
            print("Time budget reached; remaining tasks fetch next session.",
                  flush=True)
            break
        time.sleep(args.poll)

    # roll-up index
    lines = ["# Per-figure Edison ANALYSIS review — status index\n"]
    for batch, figs in record["batches"].items():
        lines.append(f"\n## Batch: {batch}\n")
        for fig, tid in figs.items():
            key = f"{batch}__{fig}"
            st = done.get(key, "pending")
            lines.append(f"- {fig}: `{tid}` — **{st}**")
    (RESULTS / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"Archived {len(done)}/{len(tasks)} results to {RESULTS}", flush=True)


if __name__ == "__main__":
    main()
