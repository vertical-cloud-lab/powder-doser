#!/usr/bin/env python3
"""Authenticated, **read-only** liveness ping of the DeepPCB public API.

Where ``deeppcb_probe.py`` is an *unauthenticated* probe that only establishes
that ``api.deeppcb.ai`` is a real backend (no key, no account), this script goes
one step further: it uses a provisioned API key to confirm the documented
DeepPCB Public API (https://client.scalar.com/@local/default/document/deeppcb-public-api)
actually authenticates and is callable from this headless GitHub / Copilot
sandbox -- the prerequisite for ever wiring an "export KiCad -> route on DeepPCB
-> download routed board" step into CI.

It is deliberately limited to the **free, no-credit, GET-only** endpoints so that
running it never starts a routing/placement job and never spends credits:

* ``GET /api/v1/apiuser/credit-flow``      -- account balance / usage summary.
* ``GET /api/v1/boards/board-schema``      -- the board JSON schema.
* ``GET /api/v1/boards/constraints-schema``-- the constraints JSON schema.

The board lifecycle that *would* consume credits (``POST /boards`` ->
``PATCH /confirm`` with ``jobType: Routing|Placement``) is intentionally NOT
exercised here.

The key is read from the ``DEEPPCB_API_KEY`` environment variable (in this repo's
Copilot agent it is provisioned as an agent secret). The key itself is never
printed. Run with::

    export DEEPPCB_API_KEY=...
    python paper/background/deeppcb_api_ping.py

Findings are summarized in ``17-deeppcb-ai-pcb-routing.md``.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

BASE = "https://api.deeppcb.ai/api/v1"
TIMEOUT = 30
USER_AGENT = "powder-doser-deeppcb-ping/1.0 (+read-only; https://github.com/vertical-cloud-lab/powder-doser)"

# Free, read-only GET endpoints only. (Routing/placement POST+confirm would burn
# credits and is intentionally excluded.)
ENDPOINTS = [
    ("credit-flow", f"{BASE}/apiuser/credit-flow"),
    ("board-schema", f"{BASE}/boards/board-schema"),
    ("constraints-schema", f"{BASE}/boards/constraints-schema"),
]


@dataclass
class PingResult:
    name: str
    status: int | None
    content_type: str
    bytes: int
    summary: str


def _summarize(name: str, body: bytes) -> str:
    if name == "credit-flow":
        try:
            d = json.loads(body)
            return (
                f"balance={d.get('balance')} credits "
                f"({d.get('balanceInMinutes')} min), "
                f"usedCredits={d.get('usedCredits')}, "
                f"createdBoards={d.get('createdBoards')}"
            )
        except (ValueError, AttributeError):
            return "(could not parse JSON)"
    # Schemas: just confirm we got a JSON document with a title/top-level keys.
    try:
        d = json.loads(body)
        title = d.get("title") or d.get("$id") or "schema"
        return f"valid JSON schema ({title}; {len(body)} bytes)"
    except ValueError:
        return f"non-JSON body ({len(body)} bytes)"


def ping(name: str, url: str, api_key: str) -> PingResult:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "accept": "application/json",
            "x-deeppcb-api-key": api_key,
        },
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body = resp.read()
            ct = resp.headers.get("Content-Type", "")
            return PingResult(name, resp.status, ct, len(body), _summarize(name, body))
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "") if exc.headers else ""
        detail = "401 Unauthorized (key rejected)" if exc.code == 401 else f"HTTP {exc.code}"
        return PingResult(name, exc.code, ct, 0, detail)
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        return PingResult(name, None, "", 0, f"{type(exc).__name__}: {exc}")


def main() -> None:
    api_key = os.environ.get("DEEPPCB_API_KEY")
    if not api_key:
        raise SystemExit(
            "DEEPPCB_API_KEY is not set. Export it (or provision it as an agent "
            "secret) before running this read-only ping."
        )

    results = [ping(name, url, api_key) for name, url in ENDPOINTS]

    print("== DeepPCB public API (authenticated, read-only GET) ==")
    for r in results:
        flag = "ok " if r.status == 200 else "FAIL"
        print(f"  [{flag}] {r.name:<20} HTTP {r.status}  {r.summary}")

    authed = all(r.status == 200 for r in results)
    print("\n== Verdict ==")
    if authed:
        print(
            "  DEEPPCB_API_KEY authenticates and the DeepPCB public API is callable "
            "from this headless sandbox (all read-only GET endpoints returned 200 "
            "JSON, no credits spent). A CI step that uploads a KiCad board, confirms "
            "a Routing/Placement job, and downloads the routed .kicad_pcb is "
            "therefore technically feasible -- gated only by credit balance (the "
            "free trial is one board / ~30 min) and a webhook/poll for results."
        )
    else:
        print("  One or more endpoints failed; inspect the rows above.")

    print("\n" + json.dumps([asdict(r) for r in results], indent=2))


if __name__ == "__main__":
    main()
