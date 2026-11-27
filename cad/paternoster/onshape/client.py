"""Minimal Onshape REST client with a call budget and a ledger.

Same auth as the lab's earlier Onshape scripts (PR #170 ``onshape_build.py``,
PR #176 ``onshape_client.py``): the company API key pair over basic auth.
The company plan (EDU Educator) allows 2,500 calls a year for the whole
company, so every request is counted, appended to ``api_calls.jsonl``
(run, method, path, status, UTC time) and a run stops at ``budget`` calls.
Onshape does not count failed (4xx) requests, but they are logged anyway.

Needs ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY in the environment.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

API = "https://cad.onshape.com/api/v10"
HERE = Path(__file__).resolve().parent
LEDGER = HERE / "api_calls.jsonl"


class Onshape:
    def __init__(self, budget: int = 40, run: str = ""):
        self.auth = HTTPBasicAuth(os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
        self.s = requests.Session()
        self.budget, self.calls, self.run = budget, 0, run

    def req(self, method: str, path: str, raw: bool = False, **kw):
        kw.setdefault("timeout", 300)
        headers = kw.pop("headers", {})
        headers.setdefault("Accept", "application/json;charset=UTF-8; qs=0.09")
        url = path if path.startswith("http") else API + path
        for attempt in range(3):
            if self.calls >= self.budget:
                raise RuntimeError(f"API budget of {self.budget} calls used up before {method} {path}")
            self.calls += 1
            r = self.s.request(method, url, auth=self.auth, headers=headers, **kw)
            with LEDGER.open("a") as f:
                f.write(json.dumps({"run": self.run, "n": self.calls, "method": method,
                                    "path": url.replace(API, "").split("?")[0], "status": r.status_code,
                                    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
            if r.status_code in (429, 502, 503, 504):
                time.sleep(float(r.headers.get("Retry-After", 5 * (attempt + 1))))
                continue
            break
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:800]}")
        if raw:
            return r
        return r.json() if r.content and "json" in r.headers.get("Content-Type", "") else r

    def get(self, path, **kw):
        return self.req("GET", path, **kw)

    def post(self, path, **kw):
        return self.req("POST", path, **kw)
