#!/usr/bin/env python3
"""Re-create the MongoDB snapshot that analysis/opt_stats.py reads.

Writes every document of ``powder_doser.opt_trials`` (without MongoDB's ``_id``), oldest
first, as one JSON object per line, to
``data/opt_trials/opt_trials_<first-date>-<last-date>.jsonl``.

Needs ``MONGODB_URI`` in the environment (never printed) and ``pip install pymongo``.
The committed snapshot holds 125 documents, 29 Sep to 20 Oct 2026; a later export also
picks up any newer trials, under a new file name.

Usage (from paper/optimization/):  python3 analysis/export_opt_trials.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pymongo
from bson import json_util

OUT = Path(__file__).resolve().parent.parent / "data" / "opt_trials"


def main() -> None:
    client = pymongo.MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=20000)
    docs = list(client["powder_doser"]["opt_trials"].find({}).sort("started_utc", 1))
    for d in docs:
        d.pop("_id", None)
    first, last = docs[0]["started_utc"][:10].replace("-", ""), docs[-1]["started_utc"][:10].replace("-", "")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"opt_trials_{first}-{last}.jsonl"
    with open(path, "w") as f:
        for d in docs:
            f.write(json_util.dumps(d) + "\n")
    print(f"wrote {len(docs)} documents to {path}")


if __name__ == "__main__":
    main()
