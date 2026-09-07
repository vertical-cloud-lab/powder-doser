"""Probe Onshape REST API with HMAC-SHA256 auth.

Reads ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY from the environment (e.g. as
encrypted GitHub Actions secrets). Never prints the secrets. Tests two
endpoints that both require valid API-key auth:

  - GET /api/v6/users/sessioninfo  (lightweight; returns 200 + user info
    on a normal account, or 204 with empty body if the account exists
    but the API key isn't authorised yet)
  - GET /api/v6/documents          (auth-required listing of own docs)

Sig spec: https://onshape-public.github.io/docs/auth/apikeys/

  sigStr  = (method + "\n" + nonce + "\n" + date + "\n" + ctype + "\n" +
             path + "\n" + query + "\n").lower().encode("utf-8")
  sig     = base64(HMAC-SHA256(secretKey, sigStr))
  header  = "On {accessKey}:HmacSHA256:{sig}"
"""
import base64
import datetime
import hashlib
import hmac
import json
import os
import secrets
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("ONSHAPE_BASE_URL", "https://cad.onshape.com")


def signed_get(access_key: str, secret_key: bytes, path: str, query: str = ""):
    method = "GET"
    nonce = secrets.token_hex(13)[:25]
    date = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    ctype = "application/json"
    sig_str = "\n".join([method, nonce, date, ctype, path, query, ""]).lower()
    sig = base64.b64encode(
        hmac.new(secret_key, sig_str.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    url = BASE + path + (("?" + query) if query else "")
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": ctype,
            "Date": date,
            "On-Nonce": nonce,
            "Authorization": f"On {access_key}:HmacSHA256:{sig}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    access = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret = os.environ.get("ONSHAPE_SECRET_KEY")
    if not access or not secret:
        print(
            "ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY not set in env; "
            "skipping authenticated probe."
        )
        return 0

    print(f"BASE = {BASE}")
    print(f"access key: len={len(access)}")
    print(f"secret key: len={len(secret)}")

    sk = secret.encode("utf-8")

    print("\n== GET /api/v6/users/sessioninfo ==")
    code, body = signed_get(access, sk, "/api/v6/users/sessioninfo")
    print(f"HTTP {code}")
    try:
        j = json.loads(body) if body else {}
        safe = {
            k: j.get(k)
            for k in ("id", "name", "email", "role", "state", "company")
            if k in j
        }
        print(json.dumps(safe, indent=2, default=str) or "(empty body)")
    except Exception:
        print(body[:400].decode(errors="replace"))

    print("\n== GET /api/v6/documents (own, first page) ==")
    code, body = signed_get(
        access,
        sk,
        "/api/v6/documents",
        "filter=0&limit=10&sortColumn=modifiedAt&sortOrder=desc",
    )
    print(f"HTTP {code}")
    try:
        j = json.loads(body)
        items = j.get("items", []) if isinstance(j, dict) else []
        if code != 200:
            print(body[:300].decode(errors="replace"))
        print(f"items returned: {len(items)}")
        for d in items[:10]:
            owner = (d.get("owner") or {}).get("name")
            print(
                f"  - id={d.get('id')}  name={d.get('name')!r}  "
                f"owner={owner!r}  modified={d.get('modifiedAt')}"
            )
    except Exception:
        print(body[:400].decode(errors="replace"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
