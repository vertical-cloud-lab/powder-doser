#!/usr/bin/env python3
"""Checks for the settling gate (issue #157).

The gate's promise is narrow but load-bearing: given short read-only
samples, decide *now or later* per measurement profile, and predict the
later honestly from the measured exponential decay.  The tests pin the
threshold algebra, the tau fit, and -- because we have them -- the
verdicts against the real drift capture from the night of 2026-09-07,
where the right answers are known: short bracketed work was safe the
whole time, block G was not, and the decay constant was about 21 min.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import balance_readiness as br  # noqa: E402

DRIFT = ROOT / "docs" / "issue-157-drift"

# Segment start offsets in seconds, from the wall clocks in
# docs/issue-157-drift/README.md (22:37:57, 22:41:47, 22:47:15,
# 22:52:44, 22:58:12, 23:03:41 MDT).
SEG_OFFSETS = {
    "seg0_smoke.csv": 0,
    "seg1.csv": 230,
    "seg2.csv": 558,
    "seg3.csv": 887,
    "seg4.csv": 1215,
    "seg5.csv": 1544,
}


def replay_args():
    return ["{}@{}".format(DRIFT / name, off)
            for name, off in SEG_OFFSETS.items()]


def test_limits_follow_the_error_budget():
    # 5 mg over 3 min is block G's whole band; 5 mg over 10 s is loose.
    assert math.isclose(br.limit_for(180.0, 5.0), 5.0 / 3.0)
    assert math.isclose(br.limit_for(10.0, 5.0), 30.0)


def test_eta_is_exponential_not_linear():
    # 3.3 mg/min decaying with tau=21 min crosses 5/3 mg/min in
    # 21*ln(3.3/1.667) ~= 14.3 min.  A linear extrapolation would say
    # never (the rate is the derivative), so the number itself matters.
    eta = br.eta_min(3.3, 5.0 / 3.0, 21.0)
    assert 13.0 < eta < 16.0
    assert br.eta_min(1.0, 5.0 / 3.0, 21.0) == 0.0
    assert br.eta_min(-1.0, 5.0 / 3.0, 21.0) == 0.0     # sign-blind


def test_tau_fit_recovers_synthetic_decay():
    tau_s = 21 * 60.0
    hist = [(t, 12.0 * math.exp(-t / tau_s)) for t in (0, 240, 480, 720, 960)]
    fit = br.fit_tau_min(hist)
    assert fit is not None and abs(fit - 21.0) < 1.0


def test_tau_fit_refuses_bad_evidence():
    assert br.fit_tau_min([(0, 5.0)]) is None                     # one point
    assert br.fit_tau_min([(0, 3.0), (300, 6.0)]) is None         # growing
    assert br.fit_tau_min([(0, 0.2), (300, 0.1)]) is None         # noise floor


def test_shock_disqualifies_and_reports_it():
    t = [0.3 * i for i in range(200)]
    mg = [0.0 if x < 30 else 100.0 for x in t]
    s = br.analyze(t, mg, ["ST"] * len(t))
    assert len(s["steps"]) == 1
    ready, why = br.verdict(s, 10.0, 5.0)
    assert not ready and "shock" in why


def test_real_seg1_blocks_g_but_not_short_work():
    # 22:41 on drift night: +10.4 mg/min, quiet otherwise.
    t, mg, status = br.read_csv(str(DRIFT / "seg1.csv"))
    s = br.analyze(t, mg, status)
    assert 9.0 < s["rate_mg_min"] < 12.0
    assert s["jitter_mg"] < 0.15
    assert not s["steps"]
    assert br.verdict(s, 180.0, 5.0)[0] is False
    assert br.verdict(s, 10.0, 5.0)[0] is True


def test_replay_of_drift_night_short_profile_is_go_immediately():
    assert br.main(["--profile", "short",
                    "--from-csv", replay_args()[0]]) == 0


def test_confirm_requires_consecutive_clean_samples():
    # Live on 2026-09-08 a lone quiet 90 s window opened the gate while
    # someone was demonstrably still in the lab (rate swung -5.9 -> +0.0
    # mg/min).  --confirm 2 is the defense: one green sample is not two.
    seg5 = str(DRIFT / "seg5.csv")            # +3.3 mg/min: dose-60 ready
    seg4 = str(DRIFT / "seg4.csv")            # +5.5 mg/min: dose-60 not
    base = ["--profile", "dose-60", "--confirm", "2", "--from-csv"]
    assert br.main(base + [seg5 + "@0", seg5 + "@300"]) == 0
    assert br.main(base + [seg4 + "@0", seg5 + "@300"]) == 1   # streak 0 -> 1


def test_replay_of_drift_night_block_g_stays_closed_with_sane_eta(tmp_path):
    out = tmp_path / "state.json"
    rc = br.main(["--profile", "block-g", "--json", str(out),
                  "--from-csv"] + replay_args())
    assert rc == 1          # 30 min was genuinely not enough for block G
    state = json.loads(out.read_text())
    assert state["ready"] is False
    assert state["tau_source"] == "fitted live"
    assert 12.0 < state["tau_min"] < 35.0       # night's fit was ~21
    assert 5.0 < state["eta_min"] < 25.0        # ~14 min at 23:07
    assert len(state["history"]) == len(SEG_OFFSETS)
