#!/usr/bin/env python3
"""Pull the method-relevant sentences out of each full text in files/ (for the notes in README.md).

For every paper it prints the sentences that name a code, a contact or constitutive model, a calibration test,
a particle count, a speed-up or a run time. Output goes to stdout only; nothing from the texts is committed.

Usage: python extract_methods.py [key ...]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"

PATTERNS = {
    "code": r"\b(LIGGGHTS|LAMMPS|EDEM|Rocky|MercuryDPM|Mercury|YADE|Yade|Chrono|PFC|MFiX|OpenFOAM|CFDEM|Gerris|Basilisk|"
            r"BACI|Taichi|PySPH|GrainLearning|GNS|PyTorch|Abaqus|ANSYS|STAR-CCM)\b",
    "contact": r"\b(JKR|SJKR|DMT|EEPA|Hertz|Mindlin|rolling (?:friction|resistance)|surface energy|cohesion energy|"
               r"van der Waals|Hamaker|liquid bridge|capillary|Willett|Rabinovich|condenser model|work function|"
               r"Coulomb|image charge|Drucker|Mohr|mu\(I\)|μ\(I\)|inertial number|Beverloo|Janssen|Jenike)\b",
    "test": r"\b(shear cell|ring shear|FT4|angle of repose|Hall|Carney|tapped density|bulk density|Hausner|"
            r"rotating drum|GranuDrum|uniaxial|draw.?down|funnel|spreadab|packing fraction|silo|hopper|screw|auger|"
            r"feeder|dosing)\b",
    "scale": r"\b(\d[\d,.]*\s*(?:million|M|k|thousand)?\s*particles|coarse.?grain\w*|scal(?:ed|ing) (?:factor|up)|"
             r"CPU|GPU|core[- ]hours|hours|wall.?clock|time step)\b",
}
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    return [s.strip() for s in SENT.split(text) if 40 < len(s.strip()) < 600]


def main(keys: list[str]) -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    for key, ent in manifest.items():
        if keys and key not in keys:
            continue
        p = FILES / f"{key}.txt"
        if not ent.get("ok") or not p.exists():
            continue
        sents = sentences(p.read_text(errors="ignore"))
        print(f"\n===== {key}: {ent['citation'][:140]}")
        abstract = next((s for s in sents if "abstract" in s.lower()[:40]), sents[0] if sents else "")
        print("ABSTRACT:", abstract[:900])
        shown = 0
        for s in sents:
            hits = [k for k, pat in PATTERNS.items() if re.search(pat, s)]
            if len(hits) >= 2 or "code" in hits:
                print(f"- [{','.join(hits)}] {s[:420]}")
                shown += 1
                if shown >= 22:
                    break


if __name__ == "__main__":
    main(sys.argv[1:])
