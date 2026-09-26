#!/usr/bin/env python3
"""Amend an already-recorded uniform-battery run (issue #116).

Bench evidence sometimes arrives *after* a run is captured and uploaded --
an operator confirms from video that the outlet was not taped, or a hand
test rules out the drive coupler.  Such evidence can change the QC verdict
without changing a single measured number, so it must never be edited into
``run.json`` by hand: the original assessment and who overrode it are part
of the provenance the manuscript depends on.

This script appends a dated, attributed entry to the run document's
``amendments`` list, optionally revises ``qc.verdict`` /
``qc.valid_for_cross_powder_comparison``, and applies the same change to
the MongoDB document so the local artifact and the database stay
identical.  Measured data (``trials``/``polls``/``doses``) is never
touched.

Usage::

    python scripts/amend_battery_run.py data/battery/<run>/run_<powder>.json \\
        --author swcharles --evidence-file evidence.json \\
        --summary "video confirms the outlet tape was off" \\
        --set-verdict no-conveyance-auger-suspect --push

``--push`` requires ``MONGODB_URI`` and ``pymongo``; without it the script
only rewrites the local file (and prints the Mongo filter it would use).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys


DB = "powder_doser"
COLLECTION = "battery_runs"
URI_ENV = "MONGODB_URI"


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def build_amendment(args, evidence):
    entry = {
        "amended_utc": utc_now(),
        "author": args.author,
        "summary": args.summary,
    }
    if args.detail:
        entry["detail"] = args.detail
    if evidence:
        entry["evidence"] = evidence
    if args.set_verdict or args.set_valid is not None:
        entry["qc_change"] = {}
    return entry


def apply_qc(doc, entry, args):
    """Revise the qc block, recording what it was before."""
    qc = doc.setdefault("qc", {})
    change = entry.get("qc_change")
    if change is None:
        return
    if args.set_verdict:
        change["verdict"] = {"from": qc.get("verdict"), "to": args.set_verdict}
        qc["verdict"] = args.set_verdict
    if args.set_valid is not None:
        change["valid_for_cross_powder_comparison"] = {
            "from": qc.get("valid_for_cross_powder_comparison"),
            "to": args.set_valid,
        }
        qc["valid_for_cross_powder_comparison"] = args.set_valid
    if args.set_reason:
        change["reason"] = {"from": qc.get("reason"), "to": args.set_reason}
        qc["reason"] = args.set_reason
    qc["last_amended_utc"] = entry["amended_utc"]


def push(doc, args):
    uri = os.environ.get(URI_ENV)
    if not uri:
        print("[push] {} is not set -- local file updated only".format(URI_ENV))
        return False
    try:
        from pymongo import MongoClient
    except ImportError:
        print("[push] pymongo not installed -- local file updated only")
        return False
    flt = {"powder_id": doc["powder_id"], "started_utc": doc["started_utc"]}
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    result = client[args.db][args.collection].update_one(
        flt, {"$set": {"qc": doc["qc"], "amendments": doc["amendments"]}})
    print("[push] {} matched, {} modified in {}.{} for {}".format(
        result.matched_count, result.modified_count,
        args.db, args.collection, flt))
    return result.matched_count > 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_json", help="path to run_<powder>.json")
    parser.add_argument("--author", required=True,
                        help="who supplied the evidence (GitHub handle)")
    parser.add_argument("--summary", required=True,
                        help="one-line statement of what changed and why")
    parser.add_argument("--detail", default=None,
                        help="longer free-form explanation")
    parser.add_argument("--evidence-file", default=None,
                        help="JSON file of structured supporting evidence")
    parser.add_argument("--set-verdict", default=None,
                        help="new qc.verdict")
    parser.add_argument("--set-reason", default=None,
                        help="new qc.reason")
    parser.add_argument("--set-valid", dest="set_valid", default=None,
                        choices=["true", "false"],
                        help="new qc.valid_for_cross_powder_comparison")
    parser.add_argument("--push", action="store_true",
                        help="apply the same change to the MongoDB document")
    parser.add_argument("--db", default=DB)
    parser.add_argument("--collection", default=COLLECTION)
    args = parser.parse_args(argv)

    if args.set_valid is not None:
        args.set_valid = args.set_valid == "true"

    with open(args.run_json) as fh:
        doc = json.load(fh)

    evidence = None
    if args.evidence_file:
        with open(args.evidence_file) as fh:
            evidence = json.load(fh)

    entry = build_amendment(args, evidence)
    apply_qc(doc, entry, args)
    doc.setdefault("amendments", []).append(entry)

    with open(args.run_json, "w") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print("[amend] {} :: qc.verdict={!r} valid={!r} ({} amendment(s))".format(
        args.run_json, doc["qc"].get("verdict"),
        doc["qc"].get("valid_for_cross_powder_comparison"),
        len(doc["amendments"])))

    if args.push:
        push(doc, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
