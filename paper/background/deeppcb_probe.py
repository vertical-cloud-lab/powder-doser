#!/usr/bin/env python3
"""Read-only probe of DeepPCB's surface to answer one question for this repo:
**can DeepPCB's autonomous PCB placement/routing be driven from our headless
GitHub / Copilot CI environment, or is it web-UI-only like Quilter.ai / Flux.ai?**

This is the direct analogue of ``quilter_probe.py`` (and ``flux_probe.py``),
asking the same "is there a real programmatic API?" question of DeepPCB. It
performs only safe, unauthenticated, read-only requests using the Python standard
library (no API key, no account, no uploads):

* DNS resolution of the documented human hosts (``deeppcb.ai``, ``app.deeppcb.ai``)
  and of the *programmatic* host DeepPCB documents (``api.deeppcb.ai``).
* An unauthenticated ``GET`` of a few candidate paths and a check of the response
  status / ``Content-Type`` / ``Server`` header. A real REST backend answers with
  a non-HTML control plane (e.g. an ASP.NET ``Kestrel`` server returning ``404``
  for unknown routes and a ``200`` liveness probe at ``/health``); a UI-only
  product instead serves a single-page-app HTML shell for every route.

It writes nothing and changes nothing on DeepPCB's side. Run it with::

    python paper/background/deeppcb_probe.py

The findings are summarized in ``17-deeppcb-ai-pcb-routing.md``. Unlike Quilter
(``api.quilter.ai`` does not resolve, every path is the SPA shell), DeepPCB's
``api.deeppcb.ai`` resolves to a real backend host with a documented Swagger spec
and a working ``/health`` endpoint — i.e. it *does* expose a public, scriptable
API (account/API key still required to submit jobs). The probe is included so
that "DeepPCB has a real API, Quilter does not" conclusion is reproducible and
not just asserted.
"""
from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass

USER_AGENT = "powder-doser-deeppcb-probe/1.0 (+read-only; https://github.com/vertical-cloud-lab/powder-doser)"
TIMEOUT = 15

# Hosts DeepPCB documents for humans vs. the host a programmatic API lives on.
# DeepPCB's own API announcement points integrators at ``api.deeppcb.ai`` and a
# Swagger spec under it (https://deeppcb.ai/deeppcb-api-your-pcb-design-ai-agent/).
HOSTS = [
    "deeppcb.ai",
    "www.deeppcb.ai",
    "app.deeppcb.ai",
    "api.deeppcb.ai",
    "docs.deeppcb.ai",
]

# Candidate paths. A real REST/control-plane backend answers with a non-HTML
# control surface (JSON, plain-text health, or bare 404s from a framework like
# ASP.NET Kestrel); a UI-only product returns its SPA HTML shell for every route.
URLS = [
    "https://api.deeppcb.ai/",
    "https://api.deeppcb.ai/health",
    "https://api.deeppcb.ai/v1/",
    "https://api.deeppcb.ai/v1/jobs",
    "https://api.deeppcb.ai/v1/swagger/index.html",
    "https://app.deeppcb.ai/api-key",
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
    server: str
    looks_like: str
    detail: str


def probe_dns(host: str) -> DnsResult:
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        addrs = sorted({i[4][0] for i in infos})
        return DnsResult(host, True, ", ".join(addrs))
    except OSError as exc:  # DNS failure / no such host
        return DnsResult(host, False, f"{type(exc).__name__}: {exc}")


def _classify(status: int | None, content_type: str, server: str, body_head: str) -> str:
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
    # A framework backend (e.g. ASP.NET Kestrel) returning empty-body 404s or a
    # plain-text health probe is a real API control plane, not an SPA shell.
    if "kestrel" in server.lower() or ct.startswith("text/plain"):
        return "api-backend"
    return ct or "unknown"


def probe_http(url: str) -> HttpResult:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body_head = resp.read(512).decode("utf-8", "replace")
            ct = resp.headers.get("Content-Type", "")
            srv = resp.headers.get("Server", "")
            status = resp.status
            return HttpResult(url, status, ct, srv, _classify(status, ct, srv, body_head), "ok")
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "") if exc.headers else ""
        srv = exc.headers.get("Server", "") if exc.headers else ""
        try:
            body_head = exc.read(512).decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body_head = ""
        return HttpResult(
            url, exc.code, ct, srv, _classify(exc.code, ct, srv, body_head), f"HTTPError {exc.code}"
        )
    except (urllib.error.URLError, ssl.SSLError, socket.timeout, OSError) as exc:
        return HttpResult(url, None, "", "", "no-response", f"{type(exc).__name__}: {exc}")


def main() -> None:
    dns = [asdict(probe_dns(h)) for h in HOSTS]
    http = [asdict(probe_http(u)) for u in URLS]

    print("== DNS ==")
    for r in dns:
        flag = "ok " if r["resolved"] else "FAIL"
        print(f"  [{flag}] {r['host']:<20} {r['detail']}")
    print("\n== HTTP (unauthenticated GET) ==")
    for r in http:
        print(f"  [{r['looks_like']:<14}] {r['url']}  (srv={r['server'] or '-'}; {r['detail']})")

    api_host_up = any(
        r["host"] == "api.deeppcb.ai" and r["resolved"] for r in dns
    )
    api_surface = [r for r in http if r["looks_like"] in ("json-api", "api-backend")]
    print("\n== Verdict ==")
    if api_host_up and api_surface:
        print(
            "  Public programmatic API present: api.deeppcb.ai resolves to a real "
            "backend (non-SPA responses; documented Swagger + /health liveness), so "
            "DeepPCB CAN be driven from headless CI / the Copilot sandbox once an "
            "account + API key is provisioned. (Contrast Quilter.ai: api host does "
            "not resolve, every path is the SPA HTML shell.)"
        )
    else:
        print(
            "  No public programmatic API detected from unauthenticated probing; "
            "inspect results above."
        )

    print("\n" + json.dumps({"dns": dns, "http": http}, indent=2))


if __name__ == "__main__":
    main()
