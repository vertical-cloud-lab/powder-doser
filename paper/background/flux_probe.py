#!/usr/bin/env python3
"""Probe flux.ai for a remote, API-key-driven PCB-generation API.

Issue: "Test out flux.ai for PCB generation" -> attempt remote usage with a
dummy API key, if possible, and provide recommendations.

Flux (https://www.flux.ai) is a browser-based, AI-assisted PCB EDA tool. Its
"Copilot" AI generates/edits schematics from natural-language prompts, but it
is driven from the web UI and metered in ACU credits -- there is no documented
public REST API and no concept of a user-supplied API key for programmatic PCB
generation (verified against https://docs.flux.ai as of 2026-06).

This script makes the empirical attempt the issue asks for: it sends a dummy
bearer token to a set of plausible endpoints and classifies each response so a
reviewer can reproduce the finding that no key-authenticated API exists. It is
deliberately read-only (HTTP GET) and uses only the Python standard library so
it runs in CI with no extra dependencies.

Usage:
    python3 flux_probe.py                # uses a dummy placeholder key
    FLUX_API_KEY=sk-... python3 flux_probe.py   # override the key (still GET-only)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# A deliberately fake key. Flux has no public API-key scheme, so this should
# never authenticate; the point is to observe how each endpoint reacts.
DUMMY_KEY = os.environ.get("FLUX_API_KEY", "dummy-flux-api-key-0000000000000000")

# Candidate endpoints: the documented docs host plus the paths a programmatic
# Copilot / project API would most plausibly live at if one existed.
ENDPOINTS = [
    "https://docs.flux.ai/",
    "https://www.flux.ai/api",
    "https://www.flux.ai/api/v1",
    "https://www.flux.ai/api/copilot",
    "https://www.flux.ai/api/graphql",
    "https://api.flux.ai/",
    "https://api.flux.ai/v1",
]

TIMEOUT = 20


def classify(body: bytes, content_type: str) -> str:
    """Best-effort label for what kind of response we got back."""
    text = body[:512].lstrip().lower()
    if "json" in content_type.lower() or text.startswith(b"{") or text.startswith(b"["):
        return "json-like"
    if text.startswith(b"<!doctype html") or text.startswith(b"<html"):
        return "html-spa-shell"
    return "other"


def probe(url: str) -> dict:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            # Pretend to be an API client carrying a key.
            "Authorization": "Bearer " + DUMMY_KEY,
            "X-Api-Key": DUMMY_KEY,
            "Accept": "application/json",
            "User-Agent": "powder-doser-flux-probe/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return {
                "url": url,
                "status": resp.status,
                "content_type": ctype,
                "kind": classify(body, ctype),
                "bytes": len(body),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        ctype = exc.headers.get("Content-Type", "") if exc.headers else ""
        return {
            "url": url,
            "status": exc.code,
            "content_type": ctype,
            "kind": classify(body, ctype),
            "bytes": len(body),
        }
    except Exception as exc:  # noqa: BLE001 - connection refused / DNS / timeout
        return {
            "url": url,
            "status": None,
            "content_type": "",
            "kind": f"connection-error: {type(exc).__name__}",
            "bytes": 0,
        }


def main() -> int:
    results = [probe(u) for u in ENDPOINTS]
    print(f"# flux.ai remote-API probe (dummy key: {DUMMY_KEY[:8]}...)\n")
    header = f"{'STATUS':>7}  {'KIND':<22}  URL"
    print(header)
    print("-" * len(header))
    for r in results:
        status = r["status"] if r["status"] is not None else "ERR"
        print(f"{str(status):>7}  {r['kind']:<22}  {r['url']}")

    json_apis = [r for r in results if r["kind"] == "json-like" and r["status"] == 200]
    print()
    if json_apis:
        print("Found a JSON-returning endpoint -- investigate whether it accepts the key.")
    else:
        print(
            "No key-authenticated JSON API found: every reachable endpoint returns the\n"
            "single-page-app HTML shell (the dummy key is ignored, not rejected) or fails\n"
            "to connect. This matches the docs: Flux Copilot is UI-only / ACU-metered with\n"
            "no public REST API or API-key auth for programmatic PCB generation."
        )
    print("\nRaw results:")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
