#!/usr/bin/env python3
"""Read-only probe of Quilter.ai's surface to answer one question for this repo:
**can Quilter's autonomous PCB layout be driven from our headless GitHub /
Copilot CI environment, or is it web-UI-only?**

This is the electrical-design analogue of ``flux_probe.py`` (which asked the same
of Flux.ai). It performs only safe, unauthenticated, read-only requests using the
Python standard library (no API key, no account, no uploads):

* DNS resolution of the documented hosts (``www.quilter.ai``, ``app.quilter.ai``,
  ``docs.quilter.ai``) and of plausible *programmatic* hosts (``api.quilter.ai``,
  ``api.app.quilter.ai``).
* An unauthenticated ``GET`` of a few candidate REST-ish paths under the web app
  and a check of the response ``Content-Type`` to tell a JSON API apart from the
  single-page-app HTML shell that a UI-only product serves for every route.

It writes nothing and changes nothing on Quilter's side. Run it with::

    python paper/background/quilter_probe.py

The findings are summarized in ``16-quilter-ai-pcb-layout.md``. The probe is
included so the "no public API → not CI-automatable" conclusion is reproducible
and not just asserted.
"""
from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

USER_AGENT = "powder-doser-quilter-probe/1.0 (+read-only; https://github.com/vertical-cloud-lab/powder-doser)"
TIMEOUT = 15

# Hosts Quilter documents for humans vs. hosts a programmatic API would plausibly
# live on. If the latter do not resolve, there is no public machine interface.
HOSTS = [
    "www.quilter.ai",
    "app.quilter.ai",
    "docs.quilter.ai",
    "api.quilter.ai",
    "api.app.quilter.ai",
]

# Candidate API-style paths. A real REST API answers JSON; a UI-only product
# returns its SPA HTML shell (200 text/html) for unknown routes.
URLS = [
    "https://api.quilter.ai/",
    "https://app.quilter.ai/api/",
    "https://app.quilter.ai/api/v1/jobs",
    "https://www.quilter.ai/api/",
    "https://docs.quilter.ai/api-reference",
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
        return DnsResult(host, True, ", ".join(addrs))
    except OSError as exc:  # DNS failure / no such host
        return DnsResult(host, False, f"{type(exc).__name__}: {exc}")


def _classify(status: int | None, content_type: str, body_head: str) -> str:
    ct = content_type.lower()
    if status is None:
        return "no-response"
    if "application/json" in ct:
        return "json-api"
    if "text/html" in ct:
        # SPA shells echo an app bootstrap rather than data.
        if "<html" in body_head.lower() or "<!doctype html" in body_head.lower():
            return "html-spa-shell"
        return "html"
    return ct or "unknown"


def probe_http(url: str) -> HttpResult:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body_head = resp.read(512).decode("utf-8", "replace")
            ct = resp.headers.get("Content-Type", "")
            status = resp.status
            return HttpResult(url, status, ct, _classify(status, ct, body_head), "ok")
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "") if exc.headers else ""
        try:
            body_head = exc.read(512).decode("utf-8", "replace")
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
        print(f"  [{flag}] {r['host']:<22} {r['detail']}")
    print("\n== HTTP (unauthenticated GET) ==")
    for r in http:
        print(f"  [{r['looks_like']:<14}] {r['url']}  ({r['detail']})")

    api_hosts = [r for r in dns if r["host"].startswith("api") and r["resolved"]]
    json_apis = [r for r in http if r["looks_like"] == "json-api"]
    print("\n== Verdict ==")
    if not api_hosts and not json_apis:
        print(
            "  No public programmatic API: api* hosts do not resolve and no probed "
            "path returns JSON. Quilter is web-UI-only (app.quilter.ai), so it "
            "cannot be driven from headless CI / the Copilot sandbox."
        )
    else:
        print("  A programmatic surface may exist; inspect results above.")

    print("\n" + json.dumps({"dns": dns, "http": http}, indent=2))


if __name__ == "__main__":
    main()
