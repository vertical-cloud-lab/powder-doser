"""Still renders of the assemblies with text-to-cad's ``cadgen step snapshot``.

* ``iso``: each assembly's iso view (renders/assembly/assembly_<name>_iso.png).
* ``collar``: the servos-above doser's tap collar, before and after the
  front bracket / tap collar swap, side by side and labelled
  (renders/assembly/collar_order_closeup.png).  "Before" is the assembly
  STEP at ``--before-ref``, from git.  The +X servo, its pinion, the board,
  the board screws and the electronics are hidden so the collar shows; the
  camera fits the rest, so the close-up is a crop of a 2400 x 1800 render.

    python3 scripts/render_stills.py [iso collar] [--before-ref ab2e27b]
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "renders" / "assembly"
TMP = ROOT / "tmp" / "stills"
ISO = {"servos_above": "STEP/assembly_servos_above.step", "current": "STEP/assembly_current.step"}

COLLAR_CAMERA = '{"position": [150, 30, 170], "target": [0, 100, 38], "up": [0, 0, 1]}'
COLLAR_HIDE = ("#servo_pos", "#servo_pinion_pos_group", "#electronics", "#board", "#baseplate_hw")
CROP = (300, 250, 1600, 1225)
# (text, arrow tip (x, y) in the crop, text at (x, y))
LABELS = {
    "before": [("tap collar: nothing in front of it", (430, 520), (60, 330)),
               ("front bracket, hidden behind the collar", (690, 640), (720, 900)),
               ("44T gear", (790, 560), (900, 430)),
               ("outlet", (110, 700), (60, 880))],
    "after": [("front bracket", (480, 600), (60, 330)),
              ("tap collar (on its base)", (650, 620), (720, 900)),
              ("44T gear", (810, 600), (900, 430)),
              ("outlet", (110, 700), (60, 880))],
}


def snapshot(step: Path, out: Path, *extra: str) -> None:
    subprocess.run(["cadgen", "step", "snapshot", str(step), str(out), *extra],
                   check=True, cwd=ROOT)


def iso() -> None:
    for name, step in ISO.items():
        snapshot(ROOT / step, OUT / f"assembly_{name}_iso.png", "--camera", "iso",
                 "--width", "1400", "--height", "1000")


def collar(before_ref: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    TMP.mkdir(parents=True, exist_ok=True)
    rel = "cad/text-to-cad/STEP/assembly_servos_above.step"
    old = TMP / "assembly_servos_above_before.step"
    for suffix in ("", ".json"):
        data = subprocess.run(["git", "show", f"{before_ref}:{rel}{suffix}"], check=True,
                              capture_output=True, cwd=ROOT).stdout
        Path(str(old) + suffix).write_bytes(data)
    hide = [a for h in COLLAR_HIDE for a in ("--hide", h)]
    crops = {}
    for name, step in (("before", old), ("after", ROOT / ISO["servos_above"])):
        png = TMP / f"collar_{name}.png"
        snapshot(step, png, "--camera", COLLAR_CAMERA, *hide, "--width", "2400", "--height", "1800")
        crops[name] = Image.open(png).convert("RGB").crop(CROP)

    titles = {"before": "before (PR #170's order): tap collar, front bracket, 44T gear",
              "after": "after: front bracket, tap collar, 44T gear"}
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.4))
    for ax, (name, im) in zip(axes, crops.items()):
        ax.imshow(im)
        for text, tip, at in LABELS[name]:
            ax.annotate(text, tip, at, fontsize=11, color="#111",
                        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#888", alpha=0.9),
                        arrowprops=dict(arrowstyle="->", lw=1.2, color="#222"))
        ax.set_title(titles[name], fontsize=12)
        ax.axis("off")
    fig.suptitle("Servos-above doser at rest, from the +X side (the +X servo hidden). The collar "
                 "rides loose on the tube; now the front bracket and the gear keep it on its base",
                 fontsize=11.5)
    fig.tight_layout()
    out = OUT / "collar_order_closeup.png"
    fig.savefig(out, dpi=100)
    print("wrote", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="*", default=["iso", "collar"], choices=["iso", "collar"])
    ap.add_argument("--before-ref", default="ab2e27b", help="commit with the old assembly STEP")
    a = ap.parse_args()
    if "iso" in a.what:
        iso()
    if "collar" in a.what:
        collar(a.before_ref)


if __name__ == "__main__":
    main()
