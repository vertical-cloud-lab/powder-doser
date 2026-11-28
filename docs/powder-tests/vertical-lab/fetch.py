"""Copy powder-doser PR #190's powder-test clips into a byu-vcl checkout for the vertical-lab long-form.

Standard library only. Each clip comes from raw.githubusercontent.com at the commit manifest.json pins it to (or from
a local powder-doser checkout with --src), and its sha256 is checked against the manifest before it is written. The
credits for out/mp4/ext/powder_tests/credits.json come from credits.json beside this file.

From the root of a byu-vcl checkout (PR #318's branch, or one stacked on it):

    REF=<a commit of powder-doser that has docs/powder-tests/vertical-lab/>
    B=https://raw.githubusercontent.com/vertical-cloud-lab/powder-doser/$REF/docs/powder-tests/vertical-lab
    mkdir -p /tmp/powder-tests
    for f in fetch.py manifest.json credits.json; do curl -fsSL "$B/$f" -o "/tmp/powder-tests/$f"; done
    python3 /tmp/powder-tests/fetch.py                # -> vertical-lab/out/mp4/ext/powder_tests/

Then paste longform_chapter.py's BADGE_POWDER_DOSER and CHAPTER into vertical-lab/longform.py (after "alloy4"), add
narration.json's lines to vertical-lab/narration.json, and run `python3 longform.py plan` to see them in order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest", nargs="?", type=Path, default=Path("vertical-lab/out/mp4/ext/powder_tests"),
                    help="where the clips go (default: vertical-lab/out/mp4/ext/powder_tests)")
    ap.add_argument("--src", type=Path, help="a powder-doser checkout to copy from instead of downloading")
    ap.add_argument("--only", nargs="*", help="clip names to fetch (default: all)")
    a = ap.parse_args()
    man = json.loads((HERE / "manifest.json").read_text())
    a.dest.mkdir(parents=True, exist_ok=True)
    bad = 0
    for c in man["clips"]:
        if a.only and c["name"] not in a.only:
            continue
        if a.src:
            data = (a.src / c["file"]).read_bytes()
        else:
            with urllib.request.urlopen(c["url"], timeout=120) as r:
                data = r.read()
        got = sha256(data)
        if got != c["sha256"]:
            print(f"{c['name']}: sha256 {got[:12]} isn't the manifest's {c['sha256'][:12]}; not written",
                  file=sys.stderr)
            bad += 1
            continue
        out = a.dest / f"{c['name']}.mp4"
        out.write_bytes(data)
        print(f"{out}  {len(data) / 1e6:.2f} MB  {c['frames']} frames at {c['fps']:g} fps  ({c['commit'][:7]})")
    shutil.copyfile(HERE / "credits.json", a.dest / "credits.json")
    print(f"{a.dest / 'credits.json'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
