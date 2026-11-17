"""Export Fusion 360 public-share links to STEP (or another format) without
a browser.

Uses the same three calls the share page's Download menu makes:
  GET /shares/metadata/<shareId>              (title, downloadEnabled)
  GET /shares/download/<shareId>/?toFormat=stp (queues a job -> jobId)
  GET /shares/exportstatus/<shareId>/?exportId=<jobId>  (-> output.downloadUrl)

Only works when the owner left "Allow download" on.  Run it from a machine
Autodesk doesn't block; we ran it on the rig's Pi (stdlib only, rate-capped):

    ssh pi 'python3 - --out ~/fusion_exports' < fetch_fusion_shares.py
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# a360.co short links from the lab Fusion account (PR #170 comment).
SHARES = {
    "baseplate": "https://a360.co/4AOA7sI",
    "brackets": "https://a360.co/46XtYN1",
    "mounting-plate": "https://a360.co/4xXUj8L",
    "servo-pinion": "https://a360.co/4dcGSdF",
    "stepper-pinion": "https://a360.co/4yqSHFz",
    "tap-collar": "https://a360.co/4AIIgyz",
    "auger": "https://a360.co/4y1oz2H",
    "auger-cap": "https://a360.co/4w9kRE5",
}


def _get(url: str, accept: str = "application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    return urllib.request.urlopen(req, timeout=60)


def _json(url: str) -> dict:
    with _get(url) as r:
        return json.loads(r.read().decode())


def resolve(short_url: str) -> tuple[str, str]:
    """a360.co link -> (https://<host>, shareId)."""
    with _get(short_url, accept="text/html") as r:
        final = r.geturl()
    m = re.match(r"(https://[^/]+)/g/shares/(SH[0-9A-Za-z]+)", final)
    if not m:
        raise RuntimeError(f"unexpected share URL {final}")
    return m.group(1), m.group(2)


def download(url: str, dest: Path, max_bps: int) -> int:
    n = 0
    t0 = time.time()
    with _get(url, accept="*/*") as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(32768)
            if not chunk:
                break
            f.write(chunk)
            n += len(chunk)
            ahead = n / max_bps - (time.time() - t0)
            if ahead > 0:
                time.sleep(ahead)
    return n


def export_share(name: str, short_url: str, out: Path, fmt: str, max_bps: int) -> dict:
    host, sid = resolve(short_url)
    meta = _json(f"{host}/shares/metadata/{sid}?version=0")["success"]["body"]["metadata"]
    rec = {"name": name, "url": short_url, "shareId": sid, "title": meta["shareTitle"],
           "version": meta.get("version"), "versionUrn": meta.get("versionUrn"),
           "downloadEnabled": meta.get("downloadEnabled")}
    if meta.get("downloadEnabled") != "true":
        rec["error"] = "download disabled on the share"
        return rec
    job = _json(f"{host}/shares/download/{sid}/?toFormat={fmt}")["response"]
    job_id = job["jobId"]
    for _ in range(120):
        st = _json(f"{host}/shares/exportstatus/{sid}/?exportId={job_id}")
        dl = (st.get("output") or {}).get("downloadUrl")
        if dl and st.get("progress") == "100%":
            ext = {"stp": "step"}.get(fmt, fmt)
            dest = out / f"{name}.{ext}"
            rec["bytes"] = download(dl, dest, max_bps)
            rec["file"] = dest.name
            return rec
        if str(st.get("status")).upper() in {"F", "FAILED", "E", "ERROR"}:
            rec["error"] = f"export failed: {st}"
            return rec
        time.sleep(5)
    rec["error"] = "export timed out"
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="fusion_exports")
    ap.add_argument("--format", default="stp", help="stp, stl, f3z, igs, ...")
    ap.add_argument("--max-kbps", type=int, default=250, help="download cap, kB/s")
    ap.add_argument("names", nargs="*", help="subset of SHARES (default: all)")
    a = ap.parse_args()
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    recs = []
    for name in a.names or SHARES:
        try:
            rec = export_share(name, SHARES[name], out, a.format, a.max_kbps * 1000)
        except Exception as e:  # keep going; report per share
            rec = {"name": name, "url": SHARES[name], "error": repr(e)}
        print(json.dumps(rec), flush=True)
        recs.append(rec)
    (out / f"shares_{a.format}.json").write_text(json.dumps(recs, indent=2) + "\n")


if __name__ == "__main__":
    main()
