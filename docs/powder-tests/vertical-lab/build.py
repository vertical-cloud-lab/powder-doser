"""Package the powder-test animations for the vertical lab's long-form on byu-vcl (PR #318, issue #303).

The long-form (byu-vcl vertical-lab/longform.py) already shows other projects' renders as "ext" parts: an MP4 under
out/mp4/ext/, framed above a caption band with a badge naming whose render it is, credited in a credits.json beside it.
It does this for this repo's v10 doser (PR #185). This script writes the same pieces for the eight clips of PR #190:

    manifest.json         every clip: its file at a pinned commit, sha256, frames, fps, steps, the caption for the
                          band, a suggested highlight shot, and where its test sits in the vertical lab
    credits.json          entries in out/mp4/ext/credits.json's format, for out/mp4/ext/powder_tests/credits.json
    narration.json        lines in vertical-lab/narration.json's format, one for the card and one per clip
    longform_chapter.py   the chapter to paste into longform.py's CHAPTERS, after "alloy4" (the powder, checked)
    longform_preview.png  (with --byu-vcl) the card and each clip as the long-form would frame them, drawn by
                          longform.py's own card_image() and ext_png(); its caption_fits() checks every caption

    python3 build.py                              # after the MP4s are committed: reads git for the pinned commit
    python3 build.py --byu-vcl /path/to/byu-vcl   # also checks the captions and draws the preview

fetch.py, beside this file, copies the clips into a byu-vcl checkout and checks each sha256.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                    # the repo
ANIM = HERE.parent / "animations"
REPO = "vertical-cloud-lab/powder-doser"
PR = 190
DEST = "vertical-lab/out/mp4/ext/powder_tests"    # in byu-vcl
PART_DIR = "ext/powder_tests"                     # longform.py's parts are relative to out/mp4
BADGE = "POWDER-DOSER'S OWN RENDER"
CAPTION_TOP = 642     # y of the clips' own step caption box at 720p (common.py: H - 78); highlight.py's band_top
CARD_S = 6.0          # longform.py's card length
WPS = 2.43            # words a second, the slowest tenth of the long-form's 81 narration cues (Kokoro, speed 0.96)

BYU = "https://github.com/vertical-cloud-lab/byu-vcl"
DAL = "https://github.com/vertical-cloud-lab/digital-alloy-lab"
PSD = f"{BYU}/blob/938115f/vertical-lab/twin/instruments/psd.py"          # twin round 6's head (PR #427)
PLAN = f"{BYU}/blob/cad4e6d/atomizer-runs/plan-adv-mater/measurements.md"  # the runs plan DAL #256 cites
FAC = f"{BYU}/blob/938115f/vertical-lab/twin/facility.py"                 # the twin's two facilities

# One entry per clip, in the order the chapter plays them. `vlab` says where the test sits in the vertical lab now:
# the long-form's lab model, the real lab's plan (DAL #256's schedule and the runs plan it cites), and the twin.
CLIPS = [
    dict(name="hall_flow", label="Hall and Carney flow",
         title="Hall flowmeter and Carney funnel: flow rate", standards=["ASTM B213-25", "ASTM B964"],
         caption="Hall and Carney flow (ASTM B213, B964), by hand: seconds for 50 g to run out. The twin's "
                 "psd.flow() predicts both; the lab doesn't measure them",
         narration=(6.6, "The Hall flowmeter times fifty grams through a two and a half millimetre orifice. A "
                         "cohesive powder stops in it and goes through the wider Carney funnel instead. The twin "
                         "predicts both times from the powder's size and shape."),
         shot=(6.6, 17.0, 14.5),
         vlab=dict(model="Not shown.",
                   plan="Not planned. The plan's flow numbers come from the doser: V_g and I_stop, as in "
                        "[`docs/flowability/`](https://github.com/vertical-cloud-lab/powder-doser/blob/0030e0d/docs/"
                        "flowability/README.md) on this repo's branch at `0030e0d`.",
                   twin=f"[`psd.flow()`]({PSD}#L408-L443) gives Hall and Carney times for 50 g, with no Hall "
                        f"flow below *ff*<sub>c</sub> 3.5 and no Carney flow below 2.2 (assumed there); round 6 calls it only "
                        f"from a test. The proposals' lab books powder QC at a station named \"Powder size and flow "
                        f"(sieve analysis, Hall funnel)\" ([`facility.py` L76]({FAC}#L76)); the vertical lab's `psd` station is the "
                        f"Mastersizer and XRF instead ([L133]({FAC}#L133)).")),
    dict(name="density", label="Apparent and tap density, Hausner ratio",
         title="Apparent and tap density to the Hausner ratio", standards=["ASTM B212-25", "ASTM B527-24"],
         caption="Apparent and tap density (ASTM B212, B527) give the Hausner ratio, which the lab's runs plan "
                 "takes in a graduated cylinder within a week of a run",
         narration=(3.2, "Apparent density fills a twenty-five cubic centimetre cup without packing it. Tapping a "
                         "weighed sample in a cylinder gives the tapped density, and their ratio is the Hausner "
                         "ratio, which the lab's plan measures within a week of each run."),
         shot=(17.8, 28.4, 27.0),
         vlab=dict(model="Not shown.",
                   plan=f"\"Doser flowability, Hausner ratio\", within a week of each run, 0.5–1 h "
                        f"([DAL #256]({DAL}/issues/256)); the Hausner ratio from a graduated cylinder "
                        f"([runs plan]({PLAN}#L97-L103)).",
                   twin=f"`psd.flow()` returns an apparent density ([L425]({PSD}#L425)); no tapped density.")),
    dict(name="angle_of_repose", label="Angle of repose",
         title="Angle of repose, fixed funnel", standards=["ISO 4324", "USP <1174>"],
         caption="Angle of repose (ISO 4324, USP <1174>), by hand: a cone on a fixed base, free-flowing then "
                 "cohesive. Neither the lab nor the twin has it yet",
         narration=(3.4, "Powder poured through a funnel onto a fixed base builds a cone, and its height gives the "
                         "angle of repose: thirty-two degrees for this free-flowing powder, forty-seven for a "
                         "cohesive one."),
         shot=(3.4, 14.2, 13.5),
         vlab=dict(model="Not shown (heaps in the lab model sit at an assumed angle).",
                   plan="Not planned.",
                   twin="None.")),
    dict(name="sieve", label="Sieve analysis",
         title="Sieve analysis", standards=["ASTM B214", "ASTM E11"],
         caption="Sieve analysis (ASTM B214): five 8 in. sieves, 150 to 45 µm, 15 min on a tapping shaker. "
                 "Chapter 3's cell splits the powder; this sizes it",
         narration=(4.2, "Sieve analysis shakes about a hundred grams through a stack of sieves for fifteen "
                         "minutes, then weighs what each one holds. The lab's sieving cell uses the same kind of "
                         "stack, but to split the powder into the cuts it prints."),
         shot=(13.0, 25.6, 25.0),
         vlab=dict(model=f"Chapter 3 (\"sieve and print\"): the sieving cell, a Retsch AS 200 in a downdraft "
                         f"enclosure that splits the powder into jars "
                         f"([`sieve_station.py`]({BYU}/blob/0425020/vertical-lab/sieve_station.py)).",
                   plan=f"No. 60, 230 and 325 and the pan, by hand, 10–20 g at a time ([runs plan]({PLAN}#L55-L65)), "
                        f"within 48 h of a run ([DAL #256]({DAL}/issues/256)).",
                   twin=f"The proposals' lab has a Retsch AS 200 and a `psd` station for \"sieve analysis, Hall "
                        f"funnel\" ([`facility.py` L75-L76]({FAC}#L75-L76)); the vertical lab has the sieve cell "
                        f"with its wash ([L132]({FAC}#L132)).")),
    dict(name="laser_diffraction", label="Laser diffraction",
         title="Laser diffraction", standards=["ASTM B822", "ISO 13320"],
         caption="Laser diffraction (ASTM B822, ISO 13320), drawn with a wet cell; tray E's Mastersizer disperses "
                 "dry. The twin's psd.py models the same optics",
         narration=(4.8, "Laser diffraction sizes particles by how they scatter light: large ones to small "
                         "angles, small ones to wide angles. This one disperses the powder in water; the lab's "
                         "Mastersizer on tray E disperses it in air."),
         shot=(12.8, 23.0, 22.5),
         vlab=dict(model=f"Chapter 4 (\"the powder, checked\"): the Malvern Mastersizer 3000 with the Aero S dry "
                         f"disperser on tray E ([`alloy_powder.py`]({BYU}/blob/0425020/vertical-lab/alloy_powder.py)).",
                   plan=f"A cross-check on one half \"if a laser-diffraction instrument can be used without an ME "
                        f"Order\" ([runs plan]({PLAN}#L66-L67)). Utah's PSSC lab charges $5.10–$9.10 a sample, "
                        f"dry (this PR's costs).",
                   twin=f"[`psd.py`]({PSD}) simulates the Mastersizer: optics, dispersion, sampling and the "
                        "inversion.")),
    dict(name="moisture_lod", label="Moisture, loss on drying",
         title="Moisture by loss on drying", standards=["USP <731>"],
         caption="Moisture by loss on drying (USP <731>): weigh, dry at 105 °C, cool, reweigh to constant mass. "
                 "Neither the lab nor the twin has it yet",
         narration=(3.6, "Loss on drying weighs about ten grams of powder, dries it at a hundred and five degrees, "
                         "cools it in a desiccator and weighs it again, until two weighings an hour apart agree."),
         shot=(15.6, 28.4, 27.5),
         vlab=dict(model="Not shown.",
                   plan="Not planned (the plan records how many days each sample was stored, for oxygen pick-up).",
                   twin="None.")),
    dict(name="ft4_shear", label="FT4 shear cell",
         title="FT4 shear cell: yield locus and flow function", standards=["ASTM D7891-24"],
         caption="FT4 shear cell (ASTM D7891): the yield locus and the flow function ffc. The twin estimates ffc "
                 "from a Bond number; this is how it's measured",
         narration=(4.6, "A shear cell measures the strength of a consolidated powder. The points where it fails "
                         "give the yield locus, and two Mohr circles give the flow function. The twin estimates this "
                         "number; this is how it's measured."),
         shot=(18.0, 30.9, 30.0),
         vlab=dict(model="Not shown.",
                   plan="Not planned; a send-out ($650 a sample at Micromeritics, this PR's costs).",
                   twin=f"`psd.flow()` sets *ff*<sub>c</sub> = 3.7 Bo<sup>−0.27</sup> from a Bond number "
                        f"(Capece et al., \"as recalled; check\" there; [L424]({PSD}#L424)), and gates Hall and "
                        f"Carney flow on it.")),
    dict(name="ring_shear", label="Ring shear tester",
         title="Schulze ring shear tester: yield locus and flow function", standards=["ASTM D6773-22"],
         caption="Schulze ring shear tester (ASTM D6773): the same ffc, for a cohesive powder. Sent out at about "
                 "$650 a sample; no station in the lab",
         narration=(4.0, "A ring shear tester does the same in an annular cell. This cohesive fine powder has a "
                         "flow function just under three."),
         shot=(11.0, 24.5, 24.0),
         vlab=dict(model="Not shown.", plan="Not planned; a send-out, as for the FT4.",
                   twin="As for the FT4.")),
]

CHAPTER = dict(
    key="powdertests", title="The powder tests by the standards: powder-doser's renders",
    card=["Eight standard tests of a powder's flow, density, size, moisture and strength, drawn by the powder-doser "
          "project at a bench, by hand. The lab model has no station for most of them. The lab's plan sieves by "
          "hand and takes the Hausner ratio in a cylinder; the twin models Hall flow, apparent density and ffc.",
          "Schematics, not vendor CAD. Every number on screen is illustrative, for 316L, AlSi10Mg or table salt, "
          "not the lab's own powders."],
    narration=(0.5, "Next, eight standard powder tests, each done by hand, in the powder doser project's renders."))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def probe(p: Path) -> dict:
    import imageio_ffmpeg
    rd = imageio_ffmpeg.read_frames(str(p))
    meta = next(rd)
    rd.close()
    n, secs = imageio_ffmpeg.count_frames_and_secs(str(p))
    return dict(frames=int(n), fps=float(meta["fps"]), size=list(meta["size"]), seconds=round(float(secs), 3))


def steps_of(name: str) -> list[dict]:
    """The scene's step list, read from its script without importing it (an import builds the VTK stage)."""
    import ast
    import math
    tree = ast.parse((HERE.parent / "render" / f"{name}.py").read_text())
    env = {"math": math}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            try:
                val = eval(compile(ast.Expression(node.value), "<c>", "eval"), {"__builtins__": {}}, env)
            except Exception:
                continue
            if isinstance(tgt, ast.Name):
                env[tgt.id] = val
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "TL":
            out = []
            for call in node.value.args[0].elts:
                a = [eval(compile(ast.Expression(x), "<s>", "eval"), {"__builtins__": {}}, env) for x in call.args]
                out.append(dict(t0=round(float(a[0]), 3), t1=round(float(a[1]), 3), text=a[2]))
            return out
    raise SystemExit(f"no timeline in {name}.py")


def build(byu: Path | None) -> None:
    rows, credits, lines = [], {}, []
    for c in CLIPS:
        rel = f"docs/powder-tests/animations/{c['name']}.mp4"
        p = ROOT / rel
        commit = git("log", "-1", "--format=%H", "--", rel)
        if not commit:
            raise SystemExit(f"{rel} isn't committed yet: commit the renders first")
        if git("status", "--porcelain", "--", rel):
            raise SystemExit(f"{rel} differs from its last commit: commit it first")
        info = probe(p)
        t0, t1, still = c["shot"]
        rows.append(dict(name=c["name"], title=c["title"], standards=c["standards"], label=c["label"],
                         file=rel, commit=commit, url=f"https://raw.githubusercontent.com/{REPO}/{commit}/{rel}",
                         sha256=sha256(p), bytes=p.stat().st_size, **info,
                         byu_vcl=dict(dest=f"{DEST}/{c['name']}.mp4", part=f"{PART_DIR}/{c['name']}.mp4",
                                      badge=BADGE, caption=c["caption"]),
                         highlight_shot=dict(t0=t0, t1=t1, still=still, band_top=CAPTION_TOP - 2),
                         steps=steps_of(c["name"]), vertical_lab=c["vlab"]))
        credits[f"{c['name']}.mp4"] = dict(
            source=f"{REPO} PR #{PR} @ {commit[:7]}, {rel}",
            what=f"{c['title']} ({', '.join(c['standards'])}): powder-doser's schematic walkthrough of the test, by "
                 f"hand at a bench. Every number on screen is illustrative, not a measurement.",
            url=f"https://github.com/{REPO}/blob/{commit[:7]}/docs/powder-tests/README.md")
        off, text = c["narration"]
        lines.append(dict(chapter=CHAPTER["key"], part=f"{PART_DIR}/{c['name']}.mp4", offset=off, text=text,
                          source=f"{PART_DIR}/credits.json (powder-doser PR #{PR} at {commit[:7]}); "
                                 f"docs/powder-tests/vertical-lab/README.md there"))
    for r, ln in zip(rows, lines):          # each line has to end inside its clip (longform.py pushes it otherwise)
        end = ln["offset"] + len(ln["text"].split()) / WPS
        if end > r["seconds"] - 0.5:
            raise SystemExit(f"{r['name']}: its line would run to {end:.1f} s of a {r['seconds']:.1f} s clip")
    off, text = CHAPTER["narration"]
    if off + len(text.split()) / WPS > CARD_S + 1.0:          # may run 1 s into the first clip, whose line waits
        raise SystemExit("the card's line runs well past the card")
    lines.insert(0, dict(chapter=CHAPTER["key"], part="card", offset=off, text=text,
                         source=f"powder-doser PR #{PR}, docs/powder-tests/vertical-lab/"))
    commits = sorted({r["commit"] for r in rows})
    credits["note"] = (f"Fetched from powder-doser PR #{PR} (docs/powder-tests/vertical-lab/fetch.py, which checks "
                       f"each sha256 against its manifest.json). Schematics, not vendor CAD; the procedures are "
                       f"paraphrased from public summaries of the standards.")
    manifest = dict(
        what=f"powder-doser PR #{PR}'s powder-test animations, packaged for byu-vcl's vertical-lab long-form "
             f"(PR #318) as 'ext' parts",
        made=dt.date.today().isoformat(), repo=REPO, pr=PR, commits=commits,
        format="H.264 MP4, 1280 x 720, 30 fps, no audio (the long-form's own format, so its join repeats no frames)",
        chapter=dict(key=CHAPTER["key"], title=CHAPTER["title"], after="alloy4"),
        clips=rows)
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    (HERE / "credits.json").write_text(json.dumps(credits, indent=1, ensure_ascii=False) + "\n")
    (HERE / "narration.json").write_text(json.dumps(lines, indent=1, ensure_ascii=False) + "\n")
    parts = ",\n".join(f"        ({'ext'!r}, {r['byu_vcl']['part']!r}, BADGE_POWDER_DOSER,\n"
                       f"         {r['byu_vcl']['caption']!r},\n         {r['label']!r})"
                       for r in rows)
    card = ",\n".join(f"        {ln!r}" for ln in CHAPTER["card"])
    (HERE / "longform_chapter.py").write_text(
        f'"""The chapter for byu-vcl vertical-lab/longform.py\'s CHAPTERS, after "alloy4" (the powder, checked).\n\n'
        f"Written by build.py from powder-doser PR #{PR} (the clips at {', '.join(c[:7] for c in commits)}).\n"
        f"Copy the clips in first (fetch.py), then paste BADGE_POWDER_DOSER and CHAPTER into longform.py,\n"
        f"and narration.json's lines into vertical-lab/narration.json.\n"
        f'"""\n'
        f"BADGE_POWDER_DOSER = {BADGE!r}\n\n"
        f"CHAPTER = dict(\n"
        f"    key={CHAPTER['key']!r}, title={CHAPTER['title']!r},\n"
        f"    card=[\n{card}],\n"
        f"    parts=[\n{parts}])\n")
    print(f"wrote manifest.json, credits.json, narration.json, longform_chapter.py ({len(rows)} clips, "
          f"commit {', '.join(c[:7] for c in commits)})")
    if byu:
        preview(byu, rows)


def preview(byu: Path, rows: list[dict]) -> None:
    """The card and each clip's highlight still as longform.py frames them, using its own drawing code."""
    import imageio_ffmpeg
    import numpy as np
    from PIL import Image, ImageDraw
    sys.path.insert(0, str(byu / "vertical-lab"))
    import longform as L                                    # noqa: E402  (byu-vcl's own code)
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    bad = [r["name"] for r in rows if not L.caption_fits(dict(kind="ext", badge=BADGE, caption=r["byu_vcl"]["caption"]))]
    if bad:
        raise SystemExit(f"captions too long for the band: {bad}")
    W, H = L.SIZE
    band = int(L.BAND * L.K)
    after = [c["key"] for c in L.CHAPTERS].index("alloy4")          # 0-based; the new chapter is the next part
    tiles = [L.card_image(f"Part {after + 2} of {len(L.CHAPTERS) + 1}", CHAPTER["title"], CHAPTER["card"])]
    for r in rows:
        rd = imageio_ffmpeg.read_frames(str(ROOT / r["file"]), input_params=["-ss", str(r["highlight_shot"]["still"])])
        meta = next(rd)
        fr = Image.frombytes("RGB", tuple(meta["size"]), next(rd))
        rd.close()
        s = min(W / fr.width, (H - band) / fr.height)
        fit = fr.resize((round(fr.width * s), round(fr.height * s)), Image.LANCZOS)
        base = Image.new("RGBA", (W, H), (246, 247, 249, 255))
        base.paste(fit, ((W - fit.width) // 2, (H - band - fit.height) // 2))
        ov = Path("/tmp") / f"ext_{r['name']}.png"
        L.ext_png(BADGE, r["byu_vcl"]["caption"], ov)
        tiles.append(Image.alpha_composite(base, Image.open(ov).convert("RGBA")).convert("RGB"))
    k, gap = 3, 12
    tw, th = W // 3, H // 3
    sheet = Image.new("RGB", (k * tw + (k + 1) * gap, 3 * th + 4 * gap), (255, 255, 255))
    for i, t in enumerate(tiles):
        sheet.paste(t.resize((tw, th), Image.LANCZOS), (gap + (i % k) * (tw + gap), gap + (i // k) * (th + gap)))
    sheet.save(HERE / "longform_preview.png", optimize=True)
    print("wrote longform_preview.png; every caption fits its band")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--byu-vcl", type=Path, help="a byu-vcl checkout with vertical-lab/longform.py (PR #318's branch)")
    a = ap.parse_args()
    build(a.byu_vcl)
