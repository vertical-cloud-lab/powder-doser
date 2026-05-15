"""Walk ``zoo-output/multi-part/*/*.kcl`` and produce sibling ``.step``
files via ``zoo kcl export`` (the Zoo modeling-app CLI).

The current ML-ephant text-to-CAD endpoint returns KCL only — the
``outputs`` field with the rendered STEP/GLTF blobs that the May 2026
calls saw is now consistently null on completed jobs (verified against
``get_text_to_cad_part_for_user`` via both the official ``kittycad``
Python lib and the raw ``GET /user/text-to-cad/{id}`` endpoint). The
documented work-around is the ``zoo`` CLI's ``kcl export`` subcommand,
which uploads the KCL source to the Zoo design API and writes back a
real BREP. See https://github.com/KittyCAD/cli for the binary.

Usage::

    python kcl_to_step.py                      # walk all parts
    python kcl_to_step.py auger_solid          # one part only
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE / "zoo-output" / "multi-part"
ZOO_BIN = os.environ.get("ZOO_CLI", "/tmp/zoo")


def export_one(kcl: pathlib.Path, dst_dir: pathlib.Path) -> bool:
    dst_dir.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        # Both env names are accepted by `zoo kcl export`.
        "KITTYCAD_TOKEN": os.environ.get("ZOO_API_TOKEN", ""),
        "ZOO_TOKEN": os.environ.get("ZOO_API_TOKEN", ""),
    }
    cmd = [ZOO_BIN, "kcl", "export", "--output-format=step", str(kcl), str(dst_dir)]
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"    failed: {r.stderr.strip()[:300]}")
        return False
    # `zoo kcl export` writes ``output.step``; rename to <part>.step.
    src = dst_dir / "output.step"
    if not src.exists():
        # Some older CLI versions write <basename>.step
        candidates = list(dst_dir.glob("*.step"))
        if not candidates:
            print(f"    no STEP produced (output: {r.stdout.strip()[:200]})")
            return False
        src = candidates[0]
    final = dst_dir / f"{kcl.stem}.step"
    if src != final:
        shutil.move(str(src), str(final))
    print(f"    wrote {final.relative_to(HERE.parent.parent)}  ({final.stat().st_size} bytes)")
    return True


def main(argv: list[str]) -> int:
    if not pathlib.Path(ZOO_BIN).exists():
        print(f"zoo CLI not found at {ZOO_BIN}; download from "
              "https://github.com/KittyCAD/cli/releases", file=sys.stderr)
        return 1
    if not os.environ.get("ZOO_API_TOKEN"):
        print("ZOO_API_TOKEN not set", file=sys.stderr)
        return 1
    only = set(argv[1:]) if len(argv) > 1 else None
    parts = sorted(p for p in ROOT.iterdir() if p.is_dir())
    n_ok = n_fail = 0
    for part_dir in parts:
        if only and part_dir.name not in only:
            continue
        kcl = part_dir / f"{part_dir.name}.kcl"
        if not kcl.exists():
            print(f"[{part_dir.name}] no KCL — skipping")
            continue
        print(f"[{part_dir.name}]")
        if export_one(kcl, part_dir):
            n_ok += 1
        else:
            n_fail += 1
    print(f"\n== {n_ok} exported, {n_fail} failed ==")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
