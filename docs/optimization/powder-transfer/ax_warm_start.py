#!/usr/bin/env python3
"""Warm-start a related powder's BO from salt, with the fingerprint as GP
context: the Ax half of the powder_box.py example (PR #166).

What it does, all in the pinned ax-platform==0.4.3 template of
scripts/opt_campaign.py (same objectives and 180 s / 20 mg thresholds):

1. the new powder's reduced box from powder_box.reduced_box(): the R1
   afterflow rule is an Ax parameter constraint;
2. two context parameters, ctx_log10_feed and ctx_log10_tap, added to the
   search space: log10 of the bulk feed at 40 deg / 20 rpm and of the mass
   per tap cycle at 15 deg;
3. every usable salt dose of both campaigns (95) attached as data, each with
   its own session's fingerprint as context, so the GP sees one powder in
   two states (the 10-13/10-15 rig tapped about 3x less per cycle);
4. the model fitted on all of it (``fit_out_of_design``: salt doses the new
   box excludes still inform the model; Ax only stops proposing there);
5. asks for the new powder with the context held at ITS fingerprint
   (``FixedFeatures``), and the model's predictions for salt's validated
   points in each context.

Nothing is dosed: this shows the plumbing and what the model believes
before the new powder's first dose.  The asks are model output from salt
data only, not results.

    python docs/optimization/powder-transfer/ax_warm_start.py --powder AlSi10Mg
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import powder_box as pb  # noqa: E402
import opt_common as oc  # noqa: E402  (powder_box put scripts/ on the path)

VARIANT = oc.VARIANT_THREE_STAGE_MARGIN
# salt's two validated points (the 10-06 blocks), at the 35 mg margin they
# were validated with, plus bo-012 of the margin campaign at 0 mg
PROBES = {
    "bo-005": {"bulk_tap": "2hz", "trim_tap": "off", "bulk_tilt_deg": 40.0,
               "trickle_tilt_deg": 10.0, "tap_tilt_deg": 15.0,
               "bulk_rpm": 100.0, "trickle_start_remaining_g": 0.3,
               "tolerance_g": 0.003, "cutoff_margin_g": 0.035},
    "corner-09": {"bulk_tap": "2hz", "trim_tap": "off", "bulk_tilt_deg": 40.0,
                  "trickle_tilt_deg": 30.0, "tap_tilt_deg": 15.0,
                  "bulk_rpm": 20.0, "trickle_start_remaining_g": 0.05,
                  "tolerance_g": 0.003, "cutoff_margin_g": 0.035},
    "bo-012 (margin)": {"bulk_tap": "2hz", "trim_tap": "2hz",
                        "bulk_tilt_deg": 40.0, "trickle_tilt_deg": 10.0,
                        "tap_tilt_deg": 15.0, "bulk_rpm": 20.0,
                        "trickle_start_remaining_g": 0.3,
                        "tolerance_g": 0.003, "cutoff_margin_g": 0.0},
}


def make_client(box, ctx_params, model_name, seed, parallel):
    from ax.modelbridge.factory import Models
    from ax.modelbridge.generation_strategy import (GenerationStep,
                                                    GenerationStrategy)
    from ax.service.ax_client import AxClient, ObjectiveProperties
    model = Models.SAASBO if model_name == "saasbo" else Models.MOO
    gs = GenerationStrategy(steps=[
        # no SOBOL step: the attached salt doses are the initial data
        GenerationStep(model=model, num_trials=-1, max_parallelism=parallel,
                       model_kwargs={"fit_out_of_design": True}),
    ])
    ax = AxClient(generation_strategy=gs, verbose_logging=False,
                  random_seed=seed)
    # created on the FULL box: Ax 0.4.3 refuses to attach a trial outside
    # the search space, so the box is narrowed after the salt doses are in
    ax.create_experiment(
        name="powder-transfer-example",
        parameters=[dict(p) for p in oc.search_space_ax(VARIANT)] + ctx_params,
        immutable_search_space_and_opt_config=False,
        objectives={
            "t_total_s": ObjectiveProperties(
                minimize=True, threshold=oc.THRESHOLD_T_TOTAL_S),
            "abs_error_mg": ObjectiveProperties(
                minimize=True, threshold=oc.THRESHOLD_ABS_ERROR_MG),
        },
    )
    return ax


def attach_salt(ax, doses, boxes, reduced):
    """Every usable salt dose, with its session's context; returns how many
    sit outside the new powder's ``reduced`` search space."""
    outside = 0
    names = [n for n, _k, _t in oc.search_params(VARIANT)]
    for d in doses:
        session = next(n for n, dates in pb.SALT_SESSIONS.items()
                       if d["date"] in dates)
        params = {n: d["params"][n] for n in names}
        params.update(boxes[session]["context"])
        outside += not reduced.check_membership(params)
        _, idx = ax.attach_trial(params)
        # the margin campaign's scoring: jams AND overshoots penalized
        raw = oc.ax_raw_data(
            {"t_total_s": d["t_total_s"], "abs_error_mg": d["abs_error_mg"]},
            jam=d["jam"], overshoot=d["status"] == "overshoot")
        ax.complete_trial(trial_index=idx, raw_data=raw)
    return outside


def predict(ax, parameterizations):
    """{metric: (mean, standard error)} per parameterization, for the two
    (penalized) objectives the model is fitted to."""
    preds = ax.get_model_predictions_for_parameterizations(
        parameterizations=parameterizations)
    return [{m: (round(float(p[m][0]), 1), round(float(p[m][1]), 1))
             for m in ("t_total_s", "abs_error_mg")} for p in preds]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--powder", default="AlSi10Mg",
                    help="a fingerprint name from powder_box.py")
    ap.add_argument("--asks", type=int, default=3)
    ap.add_argument("--model", choices=("moo", "saasbo"), default="moo",
                    help="moo (qNEHVI, fast) or saasbo (the campaign default)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", default=os.path.join(HERE, "ax_warm_start.json"))
    args = ap.parse_args(argv)

    res, doses = pb.build()
    box = res["boxes"][args.powder]
    if box["space"] is None:
        raise SystemExit("{}: {}".format(args.powder, box["rules"][-1][1]))
    ctx_new = box["context"]
    contexts = {n: res["boxes"][n]["context"] for n in pb.SALT_SESSIONS}
    contexts[args.powder] = ctx_new
    ctx_params = []
    for key in ("ctx_log10_feed", "ctx_log10_tap"):
        vals = [c[key] for c in contexts.values()]
        ctx_params.append({"name": key, "type": "range",
                           "bounds": [round(min(vals) - 0.1, 3),
                                      round(max(vals) + 0.1, 3)]})

    ax = make_client(box, ctx_params, args.model, args.seed, args.asks)
    reduced = ax.make_search_space(
        parameters=[dict(p) for p in box["space"]] + ctx_params,
        parameter_constraints=box["constraints"])
    outside = attach_salt(ax, doses, res["boxes"], reduced)
    # now search only the new powder's box; the model still trains on all
    # 95 doses (fit_out_of_design)
    ax.experiment.search_space = reduced
    print("attached {} salt doses ({} outside the {} box), context ranges {}"
          .format(len(doses), outside, args.powder,
                  {p["name"]: p["bounds"] for p in ctx_params}))

    from ax.service.utils.instantiation import FixedFeatures
    t0 = time.time()
    trials, _ = ax.get_next_trials(
        max_trials=args.asks, fixed_features=FixedFeatures(parameters=ctx_new))
    gen_s = time.time() - t0
    asks = []
    for idx, params in sorted(trials.items()):
        knobs = {k: (round(v, 4) if isinstance(v, float) else v)
                 for k, v in params.items() if not k.startswith("ctx_")}
        asks.append({"trial_index": idx, "params": knobs,
                     "in_box": pb.inside(knobs, box)})
    print("{} asks for {} in {:.0f} s ({}):".format(
        len(asks), args.powder, gen_s, args.model))
    pred_asks = predict(ax, [dict(a["params"], **ctx_new) for a in asks])
    for a, pr in zip(asks, pred_asks):
        a["predicted"] = pr
        print("  ", a["params"], "in box:", a["in_box"], "predicted:", pr)

    probes = {}
    for label, p in PROBES.items():
        probes[label] = dict(zip(contexts, predict(
            ax, [dict(p, **c) for c in contexts.values()])))
        print("  {:<16}".format(label), probes[label])

    out = {"powder": args.powder, "model": args.model, "seed": args.seed,
           "box": box, "context_params": ctx_params, "contexts": contexts,
           "attached": len(doses), "attached_outside_box": outside,
           "gen_seconds": round(gen_s, 1), "asks": asks,
           "probe_predictions": probes,
           "note": "model output from salt data only; nothing was dosed"}
    with open(args.json, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", args.json)


if __name__ == "__main__":
    main()
