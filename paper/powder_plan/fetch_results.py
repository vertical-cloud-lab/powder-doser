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


def _dump(result) -> dict:
    return result.model_dump() if hasattr(result, "model_dump") else dict(result)


def archive(client: EdisonClient, name: str, tid: str) -> str:
    task = client.get_task(task_id=tid, verbose=True)
    status = str(task.status)
    if status != "success":
        return status
    data = _dump(task)
    answer = ""
    # ANALYSIS tasks: environment_frame.state.state.answer
    try:
        answer = data["environment_frame"]["state"]["state"]["answer"] or ""
    except (KeyError, TypeError):
        pass
    # LITERATURE tasks: environment_frame.state.state.response.answer.formatted_answer
    if not answer:
        try:
            pqa = data["environment_frame"]["state"]["state"]["response"]["answer"]
            answer = pqa.get("formatted_answer") or pqa.get("answer") or ""
        except (KeyError, TypeError, AttributeError):
            pass
    if not answer:
        answer = data.get("answer") or data.get("formatted_answer") or ""
    if answer:
        (HERE / f"{name}.answer.md").write_text(str(answer))
        print(f"  wrote {name}.answer.md ({len(str(answer))} chars)", flush=True)
    nb = None
    try:
        nb = data["environment_frame"]["state"]["state"]["nb_state"]
    except (KeyError, TypeError):
        pass
    if nb:
        (HERE / f"{name}.notebook.ipynb").write_text(
            json.dumps(nb, indent=2, default=str)
        )
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
