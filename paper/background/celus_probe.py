#!/usr/bin/env python3
"""Read-only probe of CELUS's surface to answer one question for this repo:
**can the CELUS Design Platform (concept/topology -> schematic + footprints +
floorplan, native-KiCad export) be driven from our headless GitHub / Copilot CI
environment, or is it web-UI / login-only?**

CELUS is the most promising candidate for the *intermediate* step @lbwinters
identified (topology + component list -> a router-ready KiCad starter board that
Quilter/DeepPCB can ingest), so the automation question is the same one asked of
Quilter (``quilter_probe.py``) and DeepPCB (``deeppcb_probe.py``): is there a
public, scriptable API, or only a browser app?

This performs only safe, unauthenticated, read-only requests using the Python
standard library (no API key, no account, no uploads):

* DNS resolution of the documented human hosts (``www.celus.io``,
  ``app.celus.io``) and of hosts a public API / developer portal would plausibly
  live on (``api.celus.io``, ``developer.celus.io``, ``docs.celus.io``).
* An unauthenticated ``GET`` of candidate API / developer-portal paths, checking
  status / ``Content-Type`` / body to tell a documented public API apart from a
  private SPA backend (Next.js app shell) or a bare "404 page not found".

It writes nothing on CELUS's side. Run it with::

    python paper/background/celus_probe.py

Findings are summarized in ``18-celus-ai-schematic-floorplan.md``. The observed
result is the "capable product, but not CI-automatable" pattern: the hosts
resolve, but ``api.celus.io`` serves a bare framework 404 (no public root/v1),
``app.celus.io`` is a login-gated Next.js SPA, and there is no
``developer.``/``docs.`` portal -- i.e. no documented public API/CLI/SDK, so CELUS
is a manual, browser-based, login-gated step, not a headless CI one.
"""
from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

USER_AGENT = "powder-doser-celus-probe/1.0 (+read-only; https://github.com/vertical-cloud-lab/powder-doser)"
TIMEOUT = 20

HOSTS = [
    "www.celus.io",
    "app.celus.io",
    "api.celus.io",
    "developer.celus.io",
    "docs.celus.io",
]

# Candidate API-style / developer-portal paths. A real public API answers JSON
# (often with a versioned root or an OpenAPI doc); a private SPA backend returns
# a bare framework 404 or the app HTML shell.
URLS = [
    "https://api.celus.io/",
    "https://api.celus.io/v1/",
    "https://app.celus.io/api/",
    "https://developer.celus.io/",
    "https://docs.celus.io/",
    "https://www.celus.io/developers",
]


@dataclass
class DnsResult:
    host: str
    resolved: bool
    detail: str


@dataclass
class HttpResult:
    url: str
    status: int | None
    content_type: str
    looks_like: str
    detail: str


def probe_dns(host: str) -> DnsResult:
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        addrs = sorted({i[4][0] for i in infos})
        return DnsResult(host, True, ", ".join(addrs[:3]))
    except OSError as exc:
        return DnsResult(host, False, f"{type(exc).__name__}: {exc}")


def _classify(status: int | None, content_type: str, body_head: str) -> str:
    ct = content_type.lower()
    if status is None:
        return "no-response"
    if "application/json" in ct:
        return "json-api"
    bh = body_head.lower()
    if "text/plain" in ct and "404 page not found" in bh:
        return "framework-404"  # backend host exists, no public route here
    if "text/html" in ct:
        if "data-next-head" in bh or "__next" in bh or "next" in bh:
            return "spa-shell"  # Next.js app shell (the login-gated web app)
        if "<html" in bh or "<!doctype html" in bh:
            return "html"
    return ct or "unknown"


def probe_http(url: str) -> HttpResult:
    req = urllib.request.Request(
        url, method="GET", headers={"User-Agent": USER_AGENT, "accept": "application/json"}
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body_head = resp.read(400).decode("utf-8", "replace")
            ct = resp.headers.get("Content-Type", "")
            return HttpResult(url, resp.status, ct, _classify(resp.status, ct, body_head), "ok")
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "") if exc.headers else ""
        try:
            body_head = exc.read(400).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body_head = ""
        return HttpResult(
            url, exc.code, ct, _classify(exc.code, ct, body_head), f"HTTPError {exc.code}"
        )
    except (urllib.error.URLError, ssl.SSLError, socket.timeout, OSError) as exc:
        return HttpResult(url, None, "", "no-response", f"{type(exc).__name__}: {exc}")


def main() -> None:
    dns = [asdict(probe_dns(h)) for h in HOSTS]
    http = [asdict(probe_http(u)) for u in URLS]

    print("== DNS ==")
    for r in dns:
        flag = "ok " if r["resolved"] else "FAIL"
        print(f"  [{flag}] {r['host']:<20} {r['detail']}")
    print("\n== HTTP (unauthenticated GET) ==")
    for r in http:
        print(f"  [{r['looks_like']:<14}] {r['url']}  ({r['detail']})")

    json_apis = [r for r in http if r["looks_like"] == "json-api"]
    print("\n== Verdict ==")
    if not json_apis:
        print(
            "  No documented public API: api.celus.io serves a bare framework 404 "
            "(no public root/v1), app.celus.io is a login-gated Next.js SPA, and "
            "there is no developer./docs. portal returning JSON. CELUS is a "
            "web-UI / login-gated product, so its topology->starter-board step "
            "cannot be driven from headless CI / the Copilot sandbox; it is a "
            "manual, browser-based step (same blocker class as Quilter / Flux.ai)."
        )
    else:
        print("  A programmatic surface may exist; inspect results above.")

    print("\n" + json.dumps({"dns": dns, "http": http}, indent=2))


if __name__ == "__main__":
    main()
