#!/usr/bin/env python3
"""Generate flattened Bambu Studio profile JSONs for headless CLI slicing.

The BambuStudio CLI (`--load-settings` / `--load-filaments`) does NOT
resolve the `inherits` chains inside the presets it ships with, and it
refuses outright the diff-only *user* presets Bambu Studio saves under
AppData\\Roaming\\BambuStudio\\user\\... ("unknown config type ... The
input preset file is invalid and can not be parsed", return_code -5 -
field-seen on Thumbelina, PR #23). What the CLI needs is one fully
merged ("flattened") JSON per role, which this script produces from the
system presets bundled with an installed Bambu Studio:

    # Windows (default install):
    python flatten_bambu_profiles.py --studio-dir "C:\\Program Files\\Bambu Studio"

    # Linux AppImage (extract once, no FUSE needed):
    ./bambu.AppImage --appimage-extract
    python flatten_bambu_profiles.py --studio-dir squashfs-root

    # macOS:
    python flatten_bambu_profiles.py --studio-dir /Applications/BambuStudio.app

Defaults produce the A1-mini trio used by a1_mini_slice_and_send.py
(a1mini_machine_flat.json / a1mini_process_flat.json /
a1mini_filament_flat.json in the current directory). Other printers
work too, e.g. for the H2D:

    python flatten_bambu_profiles.py --studio-dir ... --prefix h2d \
        --printer "Bambu Lab H2D 0.4 nozzle" \
        --process "0.20mm Standard @BBL H2D" \
        --filament "Bambu PLA Basic @BBL H2D"

It walks each preset's `inherits` chain upward through the bundled
`resources/profiles/BBL/` tree, merges child-over-parent, and applies
the identity patches the CLI's compatibility check requires
(`from = "system"`, `inherits = ""`, and on the machine config
`printer_settings_id = <preset name>`) - the recipe empirically
verified in PR #23 for P2S, H2D, and A1 mini.
"""

import argparse
import glob
import json
import os
import re
import sys

DEFAULTS = {
    "printer": "Bambu Lab A1 mini 0.4 nozzle",
    "process": "0.20mm Standard @BBL A1M",
    "filament": "Bambu PLA Basic @BBL A1M",
    "prefix": "a1mini",
}


def find_profiles_dir(studio_dir):
    """Locate the bundled resources/profiles dir under an install root,
    an extracted AppImage, a .app bundle, or the profiles dir itself."""
    candidates = [
        studio_dir,
        os.path.join(studio_dir, "resources", "profiles"),
        os.path.join(studio_dir, "usr", "resources", "profiles"),
        os.path.join(studio_dir, "Contents", "Resources", "profiles"),
        os.path.join(studio_dir, "Contents", "resources", "profiles"),
    ]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "BBL")):
            return c
    # Last resort: a bounded recursive search for a BBL vendor dir.
    hits = glob.glob(os.path.join(glob.escape(studio_dir), "**", "profiles", "BBL"),
                     recursive=True)
    if hits:
        return os.path.dirname(hits[0])
    sys.exit(f"ERROR: could not find a profiles/BBL directory under "
             f"{studio_dir}. Point --studio-dir at the Bambu Studio "
             "install root (the folder containing resources/profiles), "
             "an extracted AppImage (squashfs-root), or the profiles "
             "directory itself.")


def index_presets(profiles_dir):
    """Map preset name -> parsed JSON for every BBL preset file."""
    by_name = {}
    for path in glob.glob(os.path.join(glob.escape(profiles_dir), "BBL", "**", "*.json"),
                          recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        name = data.get("name")
        if isinstance(name, str) and name not in by_name:
            by_name[name] = data
    if not by_name:
        sys.exit(f"ERROR: no presets found under {profiles_dir}/BBL.")
    return by_name


def flatten(name, by_name, _seen=None):
    """Resolve `inherits` recursively; child keys override parent keys."""
    _seen = _seen or set()
    if name in _seen:
        sys.exit(f"ERROR: inheritance loop at {name!r}.")
    _seen.add(name)
    preset = by_name.get(name)
    if preset is None:
        sys.exit(f"ERROR: preset {name!r} not found in the bundled "
                 "profiles. Check the exact name (it must match the "
                 '"name" field, e.g. "Bambu Lab A1 mini 0.4 nozzle").')
    merged = {}
    parent = preset.get("inherits")
    if parent:
        merged.update(flatten(parent, by_name, _seen))
    merged.update(preset)
    return merged


def write_flat(role, name, by_name, out_path):
    flat = flatten(name, by_name)
    # Identity patches so the CLI's compatibility check treats the file
    # as a system preset (verified recipe, PR #23).
    flat["from"] = "system"
    flat["inherits"] = ""
    flat["name"] = name
    if role == "machine":
        flat["printer_settings_id"] = name
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2)
    print(f"wrote {out_path}  ({role}: {name!r}, {len(flat)} keys)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--studio-dir", required=True,
                        help="Bambu Studio install root / extracted "
                        "AppImage / .app bundle (or the resources/profiles "
                        "dir directly)")
    parser.add_argument("--printer", default=DEFAULTS["printer"],
                        help=f'machine preset name (default: '
                        f'"{DEFAULTS["printer"]}")')
    parser.add_argument("--process", default=DEFAULTS["process"],
                        help=f'process preset name (default: '
                        f'"{DEFAULTS["process"]}")')
    parser.add_argument("--filament", default=DEFAULTS["filament"],
                        help=f'filament preset name (default: '
                        f'"{DEFAULTS["filament"]}")')
    parser.add_argument("--prefix", default=DEFAULTS["prefix"],
                        help='output filename prefix (default: '
                        f'"{DEFAULTS["prefix"]}")')
    parser.add_argument("--outdir", default=".",
                        help="where to write the flattened JSONs "
                        "(default: current directory)")
    args = parser.parse_args()

    profiles_dir = find_profiles_dir(args.studio_dir)
    print(f"using profiles from: {profiles_dir}")
    by_name = index_presets(profiles_dir)

    os.makedirs(args.outdir, exist_ok=True)
    prefix = re.sub(r"[^A-Za-z0-9._-]+", "_", args.prefix)
    outputs = {}
    for role, name in [("machine", args.printer),
                       ("process", args.process),
                       ("filament", args.filament)]:
        out_path = os.path.join(args.outdir, f"{prefix}_{role}_flat.json")
        outputs[role] = write_flat(role, name, by_name, out_path)

    print("\nReady to slice, e.g.:")
    print(f'  bambu-studio --orient 1 --arrange 1 '
          f'--load-settings "{outputs["machine"]};{outputs["process"]}" '
          f'--load-filaments "{outputs["filament"]}" '
          f'--slice 0 --export-3mf part.gcode.3mf --outputdir out part.stl')
    print("or fill MACHINE_JSON/PROCESS_JSON/FILAMENT_JSON in "
          "a1_mini_slice_and_send.py with the paths above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
