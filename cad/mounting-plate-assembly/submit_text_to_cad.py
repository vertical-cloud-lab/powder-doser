#!/usr/bin/env python3
"""Submit the cup placeholder prompt to zoo.dev Text-to-CAD.

This script exists to satisfy the issue's requirement to exercise zoo.dev's
prompt-based CAD generation.  In the current sandbox the account is
payment-blocked (HTTP 402 missing_payment_method), so the request raises and
we record the response in step/cup_text_to_cad.json for review.  When the
account is funded, re-running this script will produce step/cup_text_to_cad.step.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

from kittycad import KittyCAD
from kittycad.exceptions import KittyCADClientError
from kittycad.models.file_export_format import FileExportFormat
from kittycad.models.text_to_cad_create_body import TextToCadCreateBody

PROMPT = (
    "A simple cylindrical catch cup, 38 mm outer diameter, 32 mm inner "
    "diameter, 45 mm tall, with a flat closed bottom 2.5 mm thick.  No lid, "
    "no handles.  The cup will sit on a kitchen scale and catch powder "
    "falling from above."
)

HERE = Path(__file__).resolve().parent


def main() -> int:
    token = os.environ.get("ZOO_API_TOKEN") or os.environ.get("KITTYCAD_API_TOKEN")
    if not token:
        print("ZOO_API_TOKEN not set in environment", file=sys.stderr)
        return 2

    client = KittyCAD(token=token)
    print(f"Ping: {client.meta.ping().message}")

    print(f"Submitting Text-to-CAD prompt:\n  {PROMPT!r}")
    try:
        job = client.ml.create_text_to_cad(
            output_format=FileExportFormat.STEP,
            body=TextToCadCreateBody(prompt=PROMPT),
        )
    except KittyCADClientError as exc:
        outfile = HERE / "step" / "cup_text_to_cad.json"
        outfile.parent.mkdir(parents=True, exist_ok=True)
        outfile.write_text(json.dumps({"error": str(exc)}, indent=2))
        print(f"Zoo.dev rejected the request: {exc}", file=sys.stderr)
        print(f"Wrote error report to {outfile}", file=sys.stderr)
        return 1

    print(f"Submitted: id={job.id} status={job.status}")
    # Poll until completed.
    for _ in range(120):
        time.sleep(2)
        job = client.api_calls.get_async_operation(id=str(job.id))
        print(f"  status={job.status}")
        status = str(job.status).lower()
        if "completed" in status or "failed" in status:
            break

    out_json = HERE / "step" / "cup_text_to_cad.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(job.model_dump_json(indent=2))

    outputs = getattr(job, "outputs", None) or {}
    if outputs:
        # Zoo returns base64-encoded files.
        for fname, b64 in outputs.items():
            data = base64.b64decode(b64)
            out_path = HERE / "step" / f"cup_text_to_cad_{Path(fname).name}"
            out_path.write_bytes(data)
            print(f"Wrote {out_path} ({len(data)} bytes)")
    else:
        print("No outputs returned (job did not complete successfully).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
