"""Probe what we can do against Onshape's REST API without API keys.
Hypothesis: documents listed PUBLIC on cad.onshape.com may be readable,
but creating/modifying anything will require keys."""
import urllib.request, json, ssl

# A well-known *public* Onshape document is the Onshape "Featurescript samples"
# document. Try listing its parts via the public element/parts endpoint.
# The DID below is the public Onshape "Public docs" - we'll try a known one.
# Try anonymous against the docs endpoint
url = "https://cad.onshape.com/api/v6/documents/public?limit=5"
req = urllib.request.Request(url, headers={"Accept": "application/json"})
try:
    r = urllib.request.urlopen(req, timeout=10)
    body = r.read().decode()
    print(f"GET {url} -> {r.status}")
    print(body[:400])
except urllib.error.HTTPError as e:
    print(f"HTTPError {e.code} {e.reason}: {e.read().decode()[:300]}")
except Exception as e:
    print(f"Err: {e}")
