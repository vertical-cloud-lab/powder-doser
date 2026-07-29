#!/usr/bin/env python3
"""Poll and archive the powder-plan Edison tasks (LITERATURE_HIGH calibration
query + ANALYSIS manuscript review). Blocks until both terminal, then writes
<name>.answer.md (and the ANALYSIS notebook, git-ignored) next to this script.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from edison_client import EdisonClient

HERE = Path(__file__).resolve().parent
TERMINAL = {"success", "fail", "failed", "cancelled", "error"}


def task_ids() -> dict[str, str]:
    ids = {}
    for fname, key in [
        ("lit_query_task_ids.json", "calibration_lit"),
        ("analysis_task_ids.json", "powder_plan_analysis"),
    ]:
        p = HERE / fname
        if p.exists():
            ids[key] = json.loads(p.read_text())[key]
    return ids


def archive(client: EdisonClient, name: str, tid: str) -> str:
    task = client.get_task(task_id=tid, verbose=True)
    status = str(task.status)
    if status != "success":
        return status
    env = task.environment_frame or {}
    state = env.get("state", {}) if isinstance(env, dict) else {}
    answer = getattr(task, "answer", None) or state.get("answer")
    if isinstance(answer, dict):
        answer = answer.get("answer") or json.dumps(answer, indent=2)
    if answer:
        (HERE / f"{name}.answer.md").write_text(str(answer))
        print(f"  wrote {name}.answer.md ({len(str(answer))} chars)", flush=True)
    nb = state.get("notebook") if isinstance(state, dict) else None
    if nb:
        (HERE / f"{name}.notebook.ipynb").write_text(json.dumps(nb, indent=2))
        print(f"  wrote {name}.notebook.ipynb", flush=True)
    return status


def main() -> None:
    api_key = os.environ.get("EDISON_PLATFORM_API_KEY") or os.environ.get(
        "EDISON_API_KEY"
    )
    client = EdisonClient(api_key=api_key)
    ids = task_ids()
    pending = dict(ids)
    statuses: dict[str, str] = {}
    while pending:
        for name, tid in list(pending.items()):
            task = client.get_task(task_id=tid, verbose=False)
            status = str(task.status)
            print(f"{name}: {status}", flush=True)
            if status in TERMINAL:
                statuses[name] = archive(client, name, tid)
                del pending[name]
        if pending:
            time.sleep(240)
    (HERE / "fetch_status.json").write_text(json.dumps(statuses, indent=2))
    print("all terminal:", statuses, flush=True)


if __name__ == "__main__":
    main()
