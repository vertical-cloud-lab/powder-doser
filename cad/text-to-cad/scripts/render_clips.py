"""Render the assembly and motion GIFs with text-to-cad's own animation.

1. Load an assembly model's tree (calling the model from plain Python
   returns its geometry, built or cached).
2. Write its animation module (lib.doser.animation: clips ``motion`` and
   ``assembly``) and annotate a copy of the saved STEP with it and the
   kinematics: ``cadgen step build IN OUT --kinematics --animation``.
3. ``cadgen step snapshot OUT --animation <clip> --video`` renders the GIF;
   the assembly GIF then gets a caption bar and step counter (PIL).

    PYTHONPATH=src:src/parts:src/purchased:src/electronics \\
        python3 scripts/render_clips.py --variant above [--clips assembly motion]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "parts"), str(ROOT / "src" / "purchased"),
                str(ROOT / "src" / "electronics")]

from lib import assembly_steps as AS  # noqa: E402
from lib import doser  # noqa: E402

MODELS = {"above": ("assembly_servos_above", "STEP/assembly_servos_above.step"),
          "below": ("assembly_current", "STEP/assembly_current.step")}
CAMERA = {"assembly": "35:22", "motion": "35:18"}


def tree_of(variant: str):
    """The assembly's labelled tree, as its model builds it (the clips only
    need the labels; the saved STEP is what gets rendered)."""
    from lib.electronics_place import electronics
    return doser.build_doser(variant, electronics=electronics(variant))


# the GIF holds each finished step itself (caption_gif), so the clip only
# needs a short pause between moves; that keeps the frame count down
GIF_MOVE, GIF_HOLD, GIF_PAUSE_MS = 1.5, 0.25, 1700


def annotate(variant: str, tree, out_dir: Path) -> tuple[Path, list[dict]]:
    _, step_path = MODELS[variant]
    steps = AS.steps_servos_above()
    clip_steps, captions = AS.timed_steps(tree, steps, GIF_MOVE, GIF_HOLD)
    js = doser.animation(variant, tree, clip_steps)
    out_dir.mkdir(parents=True, exist_ok=True)
    js_path = out_dir / f"{variant}_clips.js"
    js_path.write_text(js)
    # the kinematics exactly as the model's build resolved them (its sidecar),
    # turned back into the declaration vocabulary `cadgen step build` takes
    side = json.loads((ROOT / (step_path + ".json")).read_text())
    kin = side.get("kinematics")
    if kin:
        kin = {**kin, "mates": [
            {"name": m["name"], "kind": m["kind"], "parent": m["parent"], "child": m["child"],
             "origin": m["axis"]["origin"], "direction": m["axis"]["dir"],
             "limits": m["limits"]["value"]} for m in kin["mates"]]}
    kin_path = out_dir / f"{variant}_kinematics.json"
    kin_path.write_text(json.dumps(kin))
    out = out_dir / f"{Path(step_path).stem}_animated.step"
    cmd = ["cadgen", "step", "build", str(ROOT / step_path), str(out),
           "--animation", str(js_path)] + (["--kinematics", str(kin_path)] if kin else [])
    subprocess.run(cmd, check=True, cwd=ROOT)
    (out_dir / f"{variant}_captions.json").write_text(json.dumps(captions, indent=1))
    return out, captions


def video(step: Path, clip: str, out: Path, fps: int, width: int, height: int,
          extra: dict | None = None) -> None:
    req = {"fps": fps, "quality": "review", **(extra or {})}
    cmd = ["cadgen", "step", "snapshot", str(step), str(out), "--animation", clip,
           "--video", json.dumps(req), "--camera", CAMERA.get(clip, "iso"),
           "--width", str(width), "--height", str(height)]
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def caption_gif(src: Path, dst: Path, captions: list[dict], fps: int, title: str,
                move: float = GIF_MOVE) -> None:
    from PIL import Image, ImageDraw, ImageFont, ImageSequence

    im = Image.open(src)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 19)
        bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 21)
    except OSError:
        font = bold = ImageFont.load_default()
    frames, durations, n = [], [], len(captions)
    for i, fr in enumerate(ImageSequence.Iterator(im)):
        t = i / fps
        cap = next((c for c in captions if c["t0"] <= t < c["t1"]), captions[-1])
        # a step's frames while its parts move, then its last frame, held so
        # the caption can be read (the clip's own hold frames are dropped)
        last = t + 1.0 / fps >= cap["t1"] - 1e-6
        if t >= cap["t0"] + move and not last:
            continue
        durations.append(GIF_PAUSE_MS if last else int(1000 / fps))
        fr = fr.convert("RGB")
        w, h = fr.size
        bar = 78
        canvas = Image.new("RGB", (w, h + bar), (250, 250, 250))
        canvas.paste(fr, (0, 0))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, h, w, h + bar], fill=(32, 36, 44))
        d.text((16, h + 8), f"Step {cap['step']}/{n}", font=bold, fill=(255, 206, 84))
        d.text((16 + 150, h + 9), title, font=font, fill=(200, 205, 214))
        # wrap the caption to the bar
        words, line, lines = cap["caption"].split(), "", []
        for wd in words:
            trial = (line + " " + wd).strip()
            if d.textlength(trial, font=font) > w - 32:
                lines.append(line)
                line = wd
            else:
                line = trial
        lines.append(line)
        for k, ln in enumerate(lines[:2]):
            d.text((16, h + 34 + 21 * k), ln, font=font, fill=(240, 240, 240))
        frames.append(canvas.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="above", choices=list(MODELS))
    ap.add_argument("--clips", nargs="+", default=["assembly", "motion"])
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--height", type=int, default=640)
    a = ap.parse_args()
    sys.argv[1:] = []        # the model's own decorator CLI must not see these flags
    tree = tree_of(a.variant)
    tmp = ROOT / "tmp" / "clips"
    step, captions = annotate(a.variant, tree, tmp)
    name = MODELS[a.variant][0]
    for clip in a.clips:
        raw = tmp / f"{name}_{clip}_raw.gif"
        video(step, clip, raw, a.fps, a.width, a.height)
        out = ROOT / "renders" / "assembly" / f"{name}_{clip}.gif"
        out.parent.mkdir(parents=True, exist_ok=True)
        if clip == "assembly":
            caption_gif(raw, out, captions, a.fps,
                        "Powder doser, servos above (text-to-cad)" if a.variant == "above"
                        else "Powder doser (text-to-cad)")
        else:
            out.write_bytes(raw.read_bytes())
        print("wrote", out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
