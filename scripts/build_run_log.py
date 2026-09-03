#!/usr/bin/env python3
"""Build the running log of every powder-doser battery run (issue #116).

Why this exists
---------------
Runs accumulate one directory at a time under ``data/battery/``, and the story
of each one lives in a different place: timings in the run document, numbers in
the summary CSV, interpretation in a run-notes markdown file, and the video in
an 8 h YouTube broadcast that has to be identified by wall clock.  Answering
"what was running at 15:30 last Tuesday, and where is the footage?" meant
opening several of those by hand.

This script joins them and writes a single log:

* ``docs/battery-runs/RUN-LOG.md``   -- the table to read
* ``docs/battery-runs/run-log.csv``  -- the same rows, to sort or plot

It is generated, not hand-maintained: re-run it after every battery and the new
run appears with its timings, blocks, speeds, dispensed mass, QC verdict, data
links and video link already filled in.

Usage::

    python scripts/build_run_log.py                  # regenerate both files
    python scripts/build_run_log.py --check          # fail if out of date (CI)

Video links come from ``stream-broadcasts.json`` (which broadcast covers this
wall clock) refined by ``stream-registry.json`` (frame-accurate anchors, where
someone has calibrated one).  A link built from the broadcast title alone is
accurate to about a minute and is marked so in the log; a link built from a
calibrated anchor is frame-accurate.  See ``refresh_stream_broadcasts.py``.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BATTERY_DIR = REPO / "data" / "battery"
NOTES_DIR = REPO / "docs" / "battery-runs"
BROADCASTS = NOTES_DIR / "stream-broadcasts.json"
REGISTRY = NOTES_DIR / "stream-registry.json"
OUT_MD = NOTES_DIR / "RUN-LOG.md"
OUT_CSV = NOTES_DIR / "run-log.csv"

BLOB = "https://github.com/vertical-cloud-lab/powder-doser/blob/main"
TREE = "https://github.com/vertical-cloud-lab/powder-doser/tree/main"

# Seconds of lead-in so a link lands just before the action starts.
LINK_LEAD_S = 15
# A broadcast covers at most this long; used when it is the newest one.
MAX_BROADCAST_S = 8 * 3600 + 1800


# --------------------------------------------------------------------------
# loading


def _parse_utc(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_runs() -> list[dict]:
    """Every battery run and every aborted pre-flight, oldest first."""
    runs = []
    for run_json in sorted(BATTERY_DIR.glob("*/run_*.json")):
        doc = json.loads(run_json.read_text())
        doc["_dir"] = run_json.parent
        doc["_json"] = run_json
        doc["_kind"] = "battery"
        runs.append(doc)
    for pre in sorted(BATTERY_DIR.glob("*_preflight/preflight.json")):
        doc = json.loads(pre.read_text())
        d = pre.parent
        stamp, _, powder = d.name.partition("_")
        runs.append({
            "_dir": d,
            "_json": pre,
            "_kind": "preflight-only",
            "powder_id": powder.removesuffix("_preflight"),
            "started_utc": _stamp_to_iso(stamp),
            "status": "aborted",
            "preflight": doc,
            "qc": {"valid_for_cross_powder_comparison": False,
                   "verdict": doc.get("verdict", "aborted")},
        })
    runs.sort(key=lambda r: r.get("started_utc") or "")
    return runs


def _stamp_to_iso(stamp: str) -> str | None:
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$", stamp)
    if not m:
        return None
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}+00:00"


def load_broadcasts() -> list[dict]:
    if not BROADCASTS.exists():
        return []
    doc = json.loads(BROADCASTS.read_text())
    out = []
    for b in doc.get("broadcasts", []):
        t0 = _parse_utc(b.get("nominal_start_utc"))
        if t0:
            out.append({**b, "_start": t0})
    out.sort(key=lambda b: b["_start"])
    return out


def load_anchors() -> dict[str, dt.datetime]:
    """video_id -> calibrated wall-clock UTC of video offset zero."""
    if not REGISTRY.exists():
        return {}
    doc = json.loads(REGISTRY.read_text())
    anchors = {}
    for s in doc.get("streams", []):
        t0 = _parse_utc(s.get("content_t0_utc"))
        if t0 and s.get("video_id"):
            anchors[s["video_id"]] = t0
    return anchors


# --------------------------------------------------------------------------
# video


def find_video(when: dt.datetime | None, broadcasts: list[dict],
               anchors: dict[str, dt.datetime]) -> dict | None:
    """The broadcast covering ``when``, with a ?t= offset into it."""
    if not when or not broadcasts:
        return None
    covering = None
    for i, b in enumerate(broadcasts):
        end = (broadcasts[i + 1]["_start"] if i + 1 < len(broadcasts)
               else b["_start"] + dt.timedelta(seconds=MAX_BROADCAST_S))
        if b["_start"] <= when < end:
            covering = b
            break
    if covering is None:
        return None
    anchor = anchors.get(covering["video_id"])
    t0 = anchor or covering["_start"]
    offset = int((when - t0).total_seconds()) - LINK_LEAD_S
    if offset < 0:
        offset = 0
    return {
        "video_id": covering["video_id"],
        "title": covering["title"],
        "offset_s": offset,
        "exact": anchor is not None,
        "url": f"https://youtu.be/{covering['video_id']}?t={offset}",
    }


# --------------------------------------------------------------------------
# per-run derived numbers


def dispensed_g(run: dict) -> float | None:
    """Powder actually delivered: measured trial gains plus closed-loop doses.

    Losses are dropped rather than netted -- a negative trial delta is a
    balance artifact or a re-tare, never powder climbing back out of the cup.
    """
    trials = run.get("trials")
    if trials is None:
        return None
    total = sum(max(0.0, t.get("delta_g") or 0.0) for t in trials)
    total += sum(max(0.0, d.get("dispensed_g") or 0.0)
                 for d in run.get("doses") or [])
    return total


def blocks_run(run: dict) -> str:
    """Blocks that actually produced trials, not the blocks that were asked for."""
    seen = {t.get("block") for t in run.get("trials") or []}
    seen |= {d.get("block") for d in run.get("device_summary") or []}
    # Dose blocks emit DOSE rows rather than trials, so they have to be
    # read off the doses themselves.  Rows predating Block H carry no
    # block and are Block G by definition.
    seen |= {d.get("block") or "G" for d in run.get("doses") or []}
    return "".join(b for b in "ABCDEFGH" if b in seen)


def speeds(run: dict) -> str:
    p = run.get("parameters") or {}
    rot = p.get("rotation_rpm")
    sweep = p.get("speed_rpms")
    parts = []
    if rot:
        parts.append(f"C/E {float(rot):g}")
    if sweep:
        parts.append("D " + "/".join(f"{float(x):g}" for x in sweep.split(";")))
    return " · ".join(parts) + (" RPM" if parts else "")


def feed_factor(run: dict, tilt: float) -> float | None:
    """Block C mean mass per 360 deg revolution, in mg.

    ``tilt_deg`` is compared against None explicitly: horizontal is 0.0,
    which is falsy, so an ``or``-style default silently made every run's
    tilt-0 feed factor unreportable.
    """
    for row in run.get("host_summary") or []:
        row_tilt = row.get("tilt_deg")
        if (row.get("block") == "C" and row.get("phase") == "rotation"
                and row_tilt is not None and abs(row_tilt - tilt) < 0.01):
            mean = row.get("mean_g")
            if mean is not None:
                return mean * 1000.0
    return None


def dose_cell(run: dict) -> str:
    """Closed-loop dose accuracy, per target.

    Once Block H runs, a run holds doses at 50 mg, 200 mg and 1 g, and a
    single mean over all of them is not a number anybody wants: it
    averages a 4 mg error on a 50 mg dose against the same 4 mg on a 1 g
    dose, which are 8 % and 0.4 % of target.  Single-target runs -- every
    run committed so far -- render exactly as before.
    """
    by_target = run.get("dose_summary_by_target") or []
    if len(by_target) > 1:
        parts = []
        for row in sorted(by_target, key=lambda r: -(r["target_g"] or 0.0)):
            err = row.get("mean_error_g")
            mg = f"{row['target_g'] * 1000:.0f} mg"
            parts.append(f"{mg} {row['n']}x {err * 1000:+.1f} mg"
                         if err is not None else f"{mg} {row['n']}x")
        return "; ".join(parts)
    ds = run.get("dose_summary") or {}
    if not ds.get("n"):
        return "--"
    err = ds.get("mean_error_g")
    return f"{ds['n']}x, {ds.get('ok', 0)} ok, mean {err * 1000:+.1f} mg" \
        if err is not None else f"{ds['n']}x"


def env_cell(run: dict) -> str:
    env = run.get("environment")
    if not env:
        return "not recorded"
    sig = env.get("median_sigma_g")
    parts = []
    if sig is not None:
        parts.append(f"sigma {sig * 1000:.1f} mg")
    if env.get("shock_events"):
        parts.append(f"{env['shock_events']} shocks")
    if env.get("retried_trials"):
        parts.append(f"{env['retried_trials']} retries")
    # Suppressing the zeros made the quietest runs the least informative
    # cell in the table: "sigma 0.0 mg" alone is indistinguishable from a
    # run where the counters were simply never populated.  A clean bench
    # is the thing a reader most wants to spot, so say it.
    clean = env.get("clean_trial_fraction")
    if (not env.get("shock_events") and not env.get("retried_trials")
            and clean is not None and clean >= 1.0):
        parts.append("no shocks or retries")
    return ", ".join(parts) or "recorded"


# Several runs of the same powder on the same day cannot be told apart by
# date and powder id alone, so those are pinned by run directory.  Anything
# unambiguous is matched automatically and needs no entry here.
NOTES_OVERRIDES = {
    "20260804T204316Z_brown-rice-flour": "2026-08-04-brown-rice-flour.md",
    "20260804T224937Z_brown-rice-flour": "2026-08-04-brown-rice-flour-rerun.md",
    "20260805T185305Z_brown-rice-flour": "2026-08-05-brown-rice-flour-auger2.md",
    "20260805T211216Z_carboxymethyl-cellulose_preflight":
        "2026-08-05-carboxymethyl-cellulose-aborted.md",
    "20260805T215252Z_carboxymethyl-cellulose":
        "2026-08-05-carboxymethyl-cellulose.md",
}


def find_notes(run: dict) -> Path | None:
    """Run-notes markdown for this run, matched on date and powder id."""
    pinned = NOTES_OVERRIDES.get(run["_dir"].name)
    if pinned:
        p = NOTES_DIR / pinned
        return p if p.exists() else None
    started = _parse_utc(run.get("started_utc"))
    if not started or not NOTES_DIR.exists():
        return None
    day = started.date().isoformat()
    pid = (run.get("powder_id") or "").lower()
    if not pid:
        return None
    cands = [md for md in sorted(NOTES_DIR.glob("*.md"))
             if md.name.lower().startswith(day) and pid in md.name.lower()]
    if not cands:
        return None
    # Shortest name is the plain run notes; longer ones are follow-ups
    # (amendment, re-run, aborted) that belong to a specific other run.
    return min(cands, key=lambda p: len(p.name))


def rel(p: Path) -> str:
    return p.resolve().relative_to(REPO).as_posix()


# --------------------------------------------------------------------------
# rendering


def row_for(run: dict, broadcasts, anchors) -> dict:
    started = _parse_utc(run.get("started_utc"))
    ended = _parse_utc(run.get("ended_utc"))
    vid = find_video(started, broadcasts, anchors)
    disp = dispensed_g(run)
    qc = run.get("qc") or {}
    return {
        "started_utc": run.get("started_utc") or "",
        "ended_utc": run.get("ended_utc") or "",
        "started_local": run.get("started_local") or "",
        "ended_local": run.get("ended_local") or "",
        "elapsed_s": run.get("elapsed_s") or (
            (ended - started).total_seconds() if started and ended else ""),
        "powder_id": run.get("powder_id") or "",
        "powder": run.get("powder") or "",
        "batch": run.get("batch") or "",
        "operator": run.get("operator") or "",
        "kind": run["_kind"],
        "status": run.get("status") or "",
        "blocks": blocks_run(run),
        "speeds_rpm": speeds(run),
        "trials": len(run.get("trials") or []),
        "dispensed_g": f"{disp:.4f}" if disp is not None else "",
        "feed_mg_per_rev_0": _fmt(feed_factor(run, 0.0)),
        "feed_mg_per_rev_45": _fmt(feed_factor(run, 45.0)),
        "feed_mg_per_rev_90": _fmt(feed_factor(run, 90.0)),
        "doses": dose_cell(run),
        "environment": env_cell(run),
        "qc_valid": qc.get("valid_for_cross_powder_comparison", ""),
        "qc_verdict": qc.get("verdict", ""),
        "preflight_verdict": (run.get("preflight") or {}).get("verdict", ""),
        "data_dir": rel(run["_dir"]),
        "run_json": rel(run["_json"]),
        "notes": rel(find_notes(run)) if find_notes(run) else "",
        "video_id": vid["video_id"] if vid else "",
        "video_url": vid["url"] if vid else "",
        "video_exact": vid["exact"] if vid else "",
    }


def _fmt(v):
    return f"{v:.2f}" if isinstance(v, float) else ""


def _short_utc(iso: str) -> str:
    d = _parse_utc(iso)
    return d.strftime("%Y-%m-%d %H:%M") if d else "--"


def _hms(seconds) -> str:
    try:
        s = int(float(seconds))
    except (TypeError, ValueError):
        return "--"
    return f"{s // 60}:{s % 60:02d}"


def render_md(rows: list[dict]) -> str:
    valid = sum(1 for r in rows if r["qc_valid"] is True)
    out = io.StringIO()
    w = out.write
    w("# Powder-doser run log\n\n")
    w("Every battery run on the bench rig, newest first: when it ran, what it "
      "ran, how much powder went through, and where the data and the video "
      "are. Issue "
      "[#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116).\n\n")
    w("**Generated file -- do not edit by hand.** Rebuild with "
      "`python scripts/build_run_log.py` after each run "
      "(and `python scripts/refresh_stream_broadcasts.py` first if the run is "
      "on a broadcast newer than the listing). The same rows are in "
      "[`run-log.csv`](run-log.csv).\n\n")
    w(f"{len(rows)} entries, {valid} valid for cross-powder comparison. ")
    w("All times UTC; the lab is on MDT (UTC-6), given alongside per run "
      "below.\n\n")

    w("## Runs\n\n")
    w("| Start (UTC) | End | Dur | Powder | Blocks | Speeds (RPM) | "
      "Dispensed | Feed @90 deg | Doses | Environment | QC | Data | Video |\n")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in reversed(rows):
        qc = ("valid" if r["qc_valid"] is True else "excluded")
        verdict = r["qc_verdict"]
        qc_cell = f"{qc}<br>`{verdict}`" if verdict else qc
        disp = f"{float(r['dispensed_g']):.2f} g" if r["dispensed_g"] else "--"
        feed = f"{r['feed_mg_per_rev_90']} mg/rev" if r["feed_mg_per_rev_90"] else "--"
        data = f"[dir]({TREE}/{r['data_dir']})"
        if r["notes"]:
            data += f" · [notes]({BLOB}/{r['notes']})"
        video = (f"[{'exact' if r['video_exact'] else '~1 min'}]({r['video_url']})"
                 if r["video_url"] else "--")
        w(f"| {_short_utc(r['started_utc'])} | {_short_utc(r['ended_utc'])} "
          f"| {_hms(r['elapsed_s'])} | `{r['powder_id']}` | {r['blocks'] or '--'} "
          f"| {r['speeds_rpm'] or '--'} | {disp} | {feed} | {r['doses']} "
          f"| {r['environment']} | {qc_cell} | {data} | {video} |\n")

    w("\n## Per-run detail\n\n")
    for r in reversed(rows):
        title = f"{_short_utc(r['started_utc'])} UTC -- {r['powder_id']}"
        w(f"### {title}\n\n")
        w(f"- **Window** {r['started_utc']} -> {r['ended_utc'] or '(none)'}"
          f"  ({_hms(r['elapsed_s'])})\n")
        if r["started_local"]:
            w(f"- **Lab clock** {r['started_local']} -> {r['ended_local']}\n")
        if r["powder"]:
            w(f"- **Powder** {r['powder']}")
            if r["batch"]:
                w(f"  ·  batch `{r['batch']}`")
            if r["operator"]:
                w(f"  ·  operator {r['operator']}")
            w("\n")
        w(f"- **Tests** blocks {r['blocks'] or '(none)'}"
          f"  ·  {r['trials']} measured trials"
          f"  ·  {r['speeds_rpm'] or 'n/a'}\n")
        if r["dispensed_g"]:
            w(f"- **Dispensed** {float(r['dispensed_g']):.4f} g\n")
        feeds = [(t, r[f"feed_mg_per_rev_{t}"]) for t in ("0", "45", "90")]
        if any(v for _, v in feeds):
            w("- **Feed factor (block C)** "
              + "  ·  ".join(f"{t} deg {v or '--'} mg/rev" for t, v in feeds)
              + "\n")
        if r["doses"] != "--":
            w(f"- **Closed-loop doses** {r['doses']}\n")
        if r["preflight_verdict"]:
            w(f"- **Pre-flight** {r['preflight_verdict']}\n")
        w(f"- **Environment** {r['environment']}\n")
        w(f"- **QC** {'valid' if r['qc_valid'] is True else 'excluded'}"
          f"{' -- `' + r['qc_verdict'] + '`' if r['qc_verdict'] else ''}\n")
        w(f"- **Data** [{r['data_dir']}]({TREE}/{r['data_dir']})\n")
        if r["notes"]:
            w(f"- **Notes** [{r['notes']}]({BLOB}/{r['notes']})\n")
        if r["video_url"]:
            kind = ("frame-accurate" if r["video_exact"]
                    else "accurate to about a minute")
            w(f"- **Video** [{r['video_url']}]({r['video_url']}) -- {kind}\n")
        else:
            w("- **Video** no covering broadcast in the listing "
              "(run `scripts/refresh_stream_broadcasts.py`)\n")
        w("\n")

    w("## How the video links work\n\n")
    w("The bench camera streams continuously in rolling 8 h broadcasts, so "
      "every run is already on video. A run's `started_utc` picks the "
      "covering broadcast out of "
      "[`stream-broadcasts.json`](stream-broadcasts.json) and becomes a "
      "`?t=` offset into it.\n\n")
    w("- **`~1 min`** -- the offset is measured from the broadcast title's "
      "start time, which is when YouTube accepted the broadcast rather than "
      "the video's `t=0`. Close enough to find the run; not close enough to "
      "land on one auger revolution.\n")
    w("- **`exact`** -- the broadcast has a calibrated anchor in "
      "[`stream-registry.json`](stream-registry.json), measured against the "
      "burned-in overlay clock. Add one with "
      "`python scripts/battery_stream_links.py --calibrate`, and per-block "
      "links become available from that script too.\n\n")
    w("Links carry a 15 s lead-in so the action starts just after the seek.\n")
    return out.getvalue()


def render_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=list(rows[0].keys()),
                        lineterminator="\n")
    wr.writeheader()
    for r in rows:
        wr.writerow(r)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the committed log is stale")
    args = ap.parse_args()

    runs = load_runs()
    broadcasts = load_broadcasts()
    anchors = load_anchors()
    rows = [row_for(r, broadcasts, anchors) for r in runs]
    md, csv_text = render_md(rows), render_csv(rows)

    if args.check:
        stale = [p for p, want in ((OUT_MD, md), (OUT_CSV, csv_text))
                 if not p.exists() or p.read_text() != want]
        if stale:
            print("[run-log] stale: " + ", ".join(rel(p) for p in stale))
            print("[run-log] run: python scripts/build_run_log.py")
            return 1
        print("[run-log] up to date")
        return 0

    OUT_MD.write_text(md)
    OUT_CSV.write_text(csv_text)
    missing = [r for r in rows if not r["video_url"]]
    print(f"[run-log] {len(rows)} entries -> {rel(OUT_MD)}, {rel(OUT_CSV)}")
    if missing:
        print(f"[run-log] {len(missing)} without a covering broadcast; "
              "refresh the listing if these are recent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
