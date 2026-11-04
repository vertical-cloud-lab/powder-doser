#!/usr/bin/env python3
"""Snapshot the Onshape documents listed in #193 without the API keys.

    python scripts/onshape_public_snapshot.py OUT_DIR

For public and link-shared documents, Onshape answers anonymous requests with the document
metadata, the element list, each Part Studio's feature list and shaded-view renders. It refuses
every geometry export anonymously (STL, STEP, Parasolid, glTF, tessellation, blob download:
401 or 403). Anonymous requests don't count against the company's yearly API cap, which has
answered the keys with HTTP 402 since 2026-10-29.

Writes, per Part Studio (and the main assembly):
  OUT_DIR/<doc>/<element>/{top,front,right}.png  orthographic renders, cropped, PX mm per pixel
  OUT_DIR/<doc>/<element>/iso.png                isometric render, zoomed to fit
  OUT_DIR/<doc>/<element>/features.json.gz       the feature list exactly as Onshape returned it
  OUT_DIR/manifest.json                           ids, sourceMicroversion, extents, features
The top/front/right renders are the reference views docs/prints/2026-11-03-baseplate-h2d/check_stl.py
compares an STL against.
"""
import base64
import gzip
import io
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image

API = "https://cad.onshape.com/api/v6"
JSON = {"Accept": "application/json;charset=UTF-8; qs=0.09"}
PX = 0.2  # mm per pixel for the orthographic renders
MAX_PX = 3000  # widest render requested; coarser than PX beyond this

# The links in https://github.com/vertical-cloud-lab/powder-doser/issues/193#issuecomment (2026-10-29),
# "the most current editions of each part of the doser". Two have no workspace/element.
LINKS = {
    "Baseplate": "68b18e694d8672d95f496279/w/ca6615cd1f43e41c93dbf2f5/e/9f7a9b5e682bc05529f15125",
    "Mounting plate": "53e9cce7f09a50f89c120028/w/d45f5e9d7335aff0b1f1e88d/e/224d71f16476d8c27dc6e3e0",
    "Auger": "51aa3e7d16cc046d79714a7a/w/e4a7f050613025f7f2cb4fb6/e/3c166b7f26f467535e63234e",
    "Tap collar": "b0b9aed3e11591e566530a68/w/7dc93c75a03ccff73030ba25/e/cf844b34a00ef7d2d52191c1",
    "Servo pinion": "35ecacf511109e3b823b3ed0",
    "Stepper pinion": "0401d55bca2deb006cc69926",
    "Stand bracket (back)": "6cb5182c1e0e0193cfea81bb/w/97676bb10a178925d14f31d1/e/ea82a43a82cf5f861b73a9e3",
    "Stand bracket (sides)": "3493a07ffbb9b140e0fcdf21/w/50e6d3a1a5f5feadde61da47/e/cbbebd3d1064640d9bce4c7f",
    "Wood leg": "659ee3322c5c9c9ce8146b43/w/f5c8346fbf02967b4d0261a6/e/bbd4667923221cda37cd63e1",
    "Assembly": "f866631c78fbefd61e6856e4/w/043fe020d0194e41cea13bc2/e/3156bac055c13d8160e229b4",
}
calls = []


def get(path, **params):
    for attempt in range(4):
        r = requests.get(f"{API}/{path}", params=params, headers=JSON, timeout=180)
        calls.append({"path": re.sub(r"[0-9a-f]{24}", "{id}", path), "status": r.status_code})
        if r.status_code != 429:
            break
        time.sleep(10 * (attempt + 1))
    r.raise_for_status()
    time.sleep(0.3)
    return r.json()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def render(kind, did, wid, eid, view, px_mm, size):
    j = get(f"{kind}/d/{did}/w/{wid}/e/{eid}/shadedviews", viewMatrix=view, outputWidth=size,
            outputHeight=size, pixelSize=px_mm / 1000)
    return Image.open(io.BytesIO(base64.b64decode(j["images"][0]))).convert("RGBA")


def alpha_box(img):
    a = np.asarray(img)[..., 3] > 0
    ys, xs = np.nonzero(a)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None


def ortho(kind, did, wid, eid, view):
    """Render one named view centred on the origin at PX mm/px, sized from a coarse pass."""
    coarse = 1.0
    img = render(kind, did, wid, eid, view, coarse, 1200)
    box = alpha_box(img)
    if box is None:
        return None, None
    c = 600
    half = max(c - box[0], box[2] - c, c - box[1], box[3] - c) * coarse + 10  # mm, with margin
    px = PX
    while 2 * half / px > MAX_PX:
        px *= 2.5
    img = render(kind, did, wid, eid, view, px, int(np.ceil(2 * half / px)))
    x0, y0, x1, y1 = alpha_box(img)
    m = 4
    img = img.crop((max(0, x0 - m), max(0, y0 - m), x1 + m + 1, y1 + m + 1))
    return img, {"mm_per_px": px, "w_mm": round((x1 - x0 + 1) * px, 1), "h_mm": round((y1 - y0 + 1) * px, 1)}


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "https://github.com/vertical-cloud-lab/powder-doser/issues/193",
                "method": "anonymous Onshape REST requests (no API key, no API calls counted)",
                "mm_per_px": PX, "documents": []}
    for name, link in LINKS.items():
        parts = link.split("/")
        did = parts[0]
        doc = get(f"documents/{did}")
        wid = parts[2] if len(parts) > 2 else doc["defaultWorkspace"]["id"]
        linked = parts[4] if len(parts) > 4 else None
        els = get(f"documents/d/{did}/w/{wid}/elements")
        rec = {"name": name, "document": doc["name"], "url": f"https://cad.onshape.com/documents/{link}",
               "did": did, "wid": wid, "linked_element": linked, "public": doc.get("public"),
               "owner": doc.get("owner", {}).get("name"), "modifiedAt": doc.get("modifiedAt"),
               "elements": []}
        print(f"{name}: '{doc['name']}' modified {doc.get('modifiedAt')}", flush=True)
        used = set()
        for e in els:
            erec = {"id": e["id"], "name": e["name"], "type": e.get("elementType"), "linked": e["id"] == linked}
            rec["elements"].append(erec)
            is_main_asm = name == "Assembly" and e.get("elementType") == "ASSEMBLY" and e["id"] == linked
            if e.get("elementType") != "PARTSTUDIO" and not is_main_asm:
                continue
            kind = "assemblies" if is_main_asm else "partstudios"
            # Two elements can slug alike ("Stepper Pinion", "stepper_pinion"): keep them apart.
            es = slug(e["name"])
            if es in used:
                es = f"{es}-{e['id'][:6]}"
            used.add(es)
            d = out / slug(name) / es
            d.mkdir(parents=True, exist_ok=True)
            if kind == "partstudios":
                feats = get(f"partstudios/d/{did}/w/{wid}/e/{e['id']}/features")
                with gzip.open(d / "features.json.gz", "wt") as f:
                    json.dump(feats, f, separators=(",", ":"), sort_keys=True)
                erec["sourceMicroversion"] = feats.get("sourceMicroversion")
                erec["features"] = [
                    f"{x.get('name')} ({x.get('featureType')}{', suppressed' if x.get('suppressed') else ''})"
                    for x in feats.get("features", [])]
            views = {}
            for view in ("top", "front", "right"):
                img, info = ortho(kind, did, wid, e["id"], view)
                if img is None:
                    views[view] = None
                    continue
                img.save(d / f"{view}.png", optimize=True)
                views[view] = info
            iso = render(kind, did, wid, e["id"], "isometric", 0, 700)
            box = alpha_box(iso)
            if box:
                iso = iso.crop((max(0, box[0] - 8), max(0, box[1] - 8), box[2] + 9, box[3] + 9))
                iso.save(d / "iso.png", optimize=True)
            erec["views"] = views
            if views.get("top") and views.get("front"):
                erec["extent_mm"] = [views["top"]["w_mm"], views["top"]["h_mm"], views["front"]["h_mm"]]
            erec["dir"] = str(d.relative_to(out))
            print(f"   {e['name']}: extent {erec.get('extent_mm')} mm, microversion {erec.get('sourceMicroversion')}",
                  flush=True)
        manifest["documents"].append(rec)
    manifest["requests"] = {"total": len(calls), "by_status": {str(s): sum(c["status"] == s for c in calls)
                                                               for s in sorted({c["status"] for c in calls})}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print("requests:", manifest["requests"])


def overview(out):
    """One sheet of every snapshotted element's isometric render, with its extent."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out)
    m = json.loads((out / "manifest.json").read_text())
    tiles = [(d, e) for d in m["documents"] for e in d["elements"] if e.get("dir") and (out / e["dir"] / "iso.png").exists()]
    cols = 5
    rows = -(-len(tiles) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.5 * rows))
    for ax in axes.flat:
        ax.axis("off")
    for ax, (d, e) in zip(axes.flat, tiles):
        ax.imshow(Image.open(out / e["dir"] / "iso.png"))
        ext = " × ".join(f"{v:.1f}" for v in e.get("extent_mm", [])) + " mm" if e.get("extent_mm") else ""
        tag = "linked in #193" if e.get("linked") else ("imported STEP" if any("importForeign" in f for f in e.get("features", [])) else "")
        title = d["name"] if e["name"] in (d["name"], "Part Studio 1", "Base", "Assembly 1") else f"{d['name']}: {e['name']}"
        ax.set_title(f"{title}\n{ext}" + (f"\n({tag})" if tag else ""), fontsize=9)
    fig.suptitle(f"Onshape documents listed in #193, rendered by Onshape at {m['fetched_utc']} "
                 "(extents x × y × z in the part's own frame)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "overview.png", dpi=90)
    print("wrote", out / "overview.png")


if __name__ == "__main__":
    if "--overview-only" not in sys.argv:
        main(sys.argv[1])
    overview(sys.argv[1])
