"""The salt campaign's doses, as the slides use them.

Everything comes from ``data/opt/salt-20260929T014732Z/``: the campaign
records (one per dose), the Zero's trial documents (per-poll telemetry) and
the Ax snapshot (the model's prediction for every SAASBO dose before it was
dosed, mean and variance).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CAMPAIGN = REPO / "data/opt/salt-20260929T014732Z"

HAND_TUNED = ("baseline-00", "baseline-01", "rebaseline-00", "rebaseline-01")
RECOMMENDED = "bo-005"


def group(label: str) -> str:
    if label in HAND_TUNED:
        return "hand"
    if label.startswith(("corner", "center")):
        return "screen"
    if label.startswith("recenter"):
        return "anchor"
    return "bo"


def doses() -> list[dict]:
    out = []
    preds = predictions()
    for line in open(CAMPAIGN / "campaign_records.jsonl"):
        r = json.loads(line)
        s = r["summary"]
        out.append(dict(
            i=r["trial_index"], label=r["label"], group=group(r["label"]), uuid=r["trial_uuid"],
            status=s["status"], t=s["t_total_s"], err=s["error_mg"], abs=s["abs_error_mg"],
            params=r["params"], ax=r.get("ax_trial_index"), pred=preds.get(r.get("ax_trial_index")),
        ))
    return out


def predictions() -> dict:
    """{ax trial index: (t mean, t sd, |err| mean, |err| sd)} for the SAASBO doses."""
    d = json.load(open(CAMPAIGN / "ax_snapshot.json"))
    out = {}
    for k, t in d["experiment"]["trials"].items():
        mp = (t.get("generator_run") or {}).get("model_predictions")
        if not mp:
            continue
        m, c = mp
        out[int(k)] = (m["t_total_s"][0], math.sqrt(c["t_total_s"]["t_total_s"][0]),
                       m["abs_error_mg"][0], math.sqrt(c["abs_error_mg"]["abs_error_mg"][0]))
    return out


def trial(uuid: str) -> dict:
    return json.load(open(CAMPAIGN / f"zero/trial_{uuid}.json"))


def trace(uuid: str) -> dict:
    """Balance readings of one dose: t (s since the dose started), mass (g),
    phase per reading, and the stage boundaries."""
    d = trial(uuid)
    cols = d["telemetry"]["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in d["telemetry"]["rows"]]
    t = [float(r["t_s"]) for r in rows]
    m = [float(r["z_g"]) for r in rows]
    ph = [r["phase"] for r in rows]
    o = d["outcomes"]
    t0 = next(tt for tt, p in zip(t, ph) if p == "bulk") - 0.4     # auger start, about one poll earlier
    tr0 = next((tt for tt, p in zip(t, ph) if p == "trickle"), None)
    tr1 = next((tt for tt, p in zip(t, ph) if p == "trickle_end"), None)
    taps = [(tt, mm) for tt, mm, p in zip(t, m, ph) if p == "tap"]
    return dict(t=[0.0, t0] + t + [o["t_total_s"]], m=[0.0, 0.0] + m + [o["settled_final_g"]],
                bulk_start=t0, trickle_start=tr0, trickle_end=tr1,
                m_trickle_end=m[ph.index("trickle_end")] if "trickle_end" in ph else None,
                taps=taps, total=o["t_total_s"], final=o["settled_final_g"], outcomes=o,
                params=d["parameters"])


def pareto_front(points):
    """Non-dominated (t, |err|) pairs, both minimised, sorted by t."""
    pts = sorted(points)
    front, best = [], math.inf
    for t, e, *rest in pts:
        if e < best:
            front.append((t, e, *rest))
            best = e
    return front
