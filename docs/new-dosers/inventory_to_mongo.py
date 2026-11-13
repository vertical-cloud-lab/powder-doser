"""Send an inventory-checklist CSV to MongoDB.

Each row of the CSV becomes one document in `powder_doser.parts_inventory`.
Each upload also gets one document in `powder_doser.parts_inventory_snapshots`,
holding the CSV text exactly as received, its sha256, and where it came from.

A new count is a new snapshot, and the newest `taken_at` is the current
inventory. If the newest snapshot is already this exact file (same sha256),
nothing is written, so re-sending the file adds no copies; --force rewrites
it. Row documents are keyed by snapshot and row number.

    pip install pymongo
    python inventory_to_mongo.py "inventory-checklist (updated).csv" \
        --source-url https://github.com/vertical-cloud-lab/powder-doser/pull/181#issuecomment-6614295586 \
        --author brandonmunk --taken-at 2026-11-03T20:09:27Z

The master copy is docs/new-dosers/inventory-checklist.csv in this repo, and
inventory-to-mongo.yml (a GitHub Action, once copied into .github/workflows/)
runs this script on each new version of it.

The connection string comes from $PI_MONGODB_URI (readWrite on powder_doser
only) or $MONGODB_URI; choose with --uri-env. It is never printed. --dry-run
parses the file and prints the first documents without connecting.

In Atlas: Cluster0 -> Browse Collections -> powder_doser -> parts_inventory,
filter {snapshot_id: "<id this script prints>"}. Your Atlas login has to be
invited to the lab's project with at least the "Project Data Access Read Only"
role; a new login only sees its own empty "Project 0" (README section 3).
"""

import argparse
import csv
import getpass
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

DB = "powder_doser"
ROWS = "parts_inventory"
SNAPSHOTS = "parts_inventory_snapshots"

# Column header -> field name. Headers not listed are kept under a snake_case name.
FIELDS = {
    "Category": "category",
    "Item": "item",
    "Part number / source": "part_number_source",
    "Per doser": "per_doser",
    "Need for 25": "need_for_25",
    "On hand": "on_hand",
    "Short": "short",
    "Notes": "notes",
}
NUMERIC = {"per_doser", "need_for_25", "on_hand", "short"}


def field_name(header):
    if header in FIELDS:
        return FIELDS[header]
    if header.startswith("Status in PR #115"):
        return "status_pr115"
    return re.sub(r"[^0-9a-z]+", "_", header.lower()).strip("_") or "column"


def hide_hosts(kind, err, tb):
    """Print an uncaught MongoDB error without the cluster's host names.

    Connection errors list every host of the cluster, and a GitHub Action's
    log is public in this repo; the rest of the message is kept.
    """
    from pymongo.errors import PyMongoError
    if not isinstance(err, PyMongoError):
        return sys.__excepthook__(kind, err, tb)
    text = re.sub(r"mongodb(\+srv)?://\S+", "<connection string>", str(err))
    text = re.sub(r"[\w.-]+\.mongodb\.net", "<atlas host>", text)
    print(f"MongoDB error, {kind.__name__}: {text}", file=sys.stderr)


def cell(field, text):
    """Blank -> None; whole numbers in the count columns -> int; anything else kept as text."""
    text = text.strip()
    if not text:
        return None
    if field in NUMERIC and re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def parse(raw):
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    headers = next(reader)
    fields = [field_name(h) for h in headers]
    if len(set(fields)) != len(fields):
        sys.exit(f"two columns map to the same field: {fields}")
    rows = []
    for values in reader:
        if not any(v.strip() for v in values):
            continue
        if len(values) != len(headers):
            sys.exit(f"row {len(rows) + 1} has {len(values)} cells, the header has {len(headers)}")
        rows.append({f: cell(f, v) for f, v in zip(fields, values)})
    return headers, fields, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--source-url", required=True, help="where the file was posted, e.g. the GitHub comment")
    ap.add_argument("--file-url", help="direct link to the file, if different")
    ap.add_argument("--file-name", help="file name as posted (default: the local name)")
    ap.add_argument("--author", required=True, help="who did the count (GitHub login)")
    ap.add_argument("--taken-at", required=True, help="when the count was posted, ISO 8601 UTC")
    ap.add_argument("--comment-file", help="text posted with the file, stored with the snapshot")
    ap.add_argument("--snapshot-id", help="default: <taken-at date>-<first 8 of sha256>")
    ap.add_argument("--uploaded-by", help="default: $GITHUB_ACTOR or the local user name")
    ap.add_argument("--uri-env", default=None, help="env var holding the URI (default: PI_MONGODB_URI, then MONGODB_URI)")
    ap.add_argument("--force", action="store_true", help="write even if the newest snapshot is this same file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = open(args.csv_path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    headers, fields, rows = parse(raw)
    taken_at = datetime.fromisoformat(args.taken_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    sid = args.snapshot_id or f"{taken_at:%Y-%m-%d}-{sha[:8]}"
    uploaded_at = datetime.now(timezone.utc).replace(microsecond=0)
    run_url = None
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = "{}/{}/actions/runs/{}".format(
            os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
            os.environ.get("GITHUB_REPOSITORY", ""), os.environ["GITHUB_RUN_ID"])

    docs = [
        {"_id": f"{sid}:{i:02d}", "snapshot_id": sid, "row": i, **r,
         "taken_at": taken_at, "author": args.author, "source_url": args.source_url}
        for i, r in enumerate(rows, 1)
    ]
    comment = open(args.comment_file, encoding="utf-8").read().replace("\r\n", "\n").strip() if args.comment_file else None
    snapshot = {
        "_id": sid,
        "taken_at": taken_at,
        "author": args.author,
        "source_url": args.source_url,
        "file_url": args.file_url,
        "file_name": args.file_name or os.path.basename(args.csv_path),
        "comment": comment,
        "sha256": sha,
        "csv_text": raw.decode("utf-8"),  # exact text, so sha256(csv_text.encode()) == sha256
        "columns": [{"header": h, "field": f} for h, f in zip(headers, fields)],
        "row_count": len(docs),
        "rows_collection": ROWS,
        "uploaded_at": uploaded_at,
        "uploaded_by": args.uploaded_by or os.environ.get("GITHUB_ACTOR") or getpass.getuser(),
        "uploaded_from": run_url,
    }

    print(f"snapshot {sid}: {len(docs)} rows, sha256 {sha}")
    if args.dry_run:
        print(json.dumps(docs[:2], indent=1, default=str))
        return

    from pymongo import MongoClient, ReplaceOne

    names = [args.uri_env] if args.uri_env else ["PI_MONGODB_URI", "MONGODB_URI"]
    uri_var = next((n for n in names if os.environ.get(n)), None)
    if not uri_var:
        sys.exit(f"none of {names} is set")
    client = MongoClient(os.environ[uri_var], serverSelectionTimeoutMS=20000, appname="inventory_to_mongo")
    db = client[DB]

    newest = db[SNAPSHOTS].find_one({}, {"sha256": 1, "taken_at": 1}, sort=[("taken_at", -1)])
    if newest and newest["sha256"] == sha and not args.force:
        print(f"unchanged: the newest snapshot, {newest['_id']} ({newest['taken_at']:%Y-%m-%d %H:%M} UTC), "
              "is this same file, so nothing was written (--force to rewrite it)")
        client.close()
        return

    db[SNAPSHOTS].replace_one({"_id": sid}, snapshot, upsert=True)
    res = db[ROWS].bulk_write([ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in docs])
    stale = db[ROWS].delete_many({"snapshot_id": sid, "_id": {"$nin": [d["_id"] for d in docs]}})
    db[ROWS].create_index([("snapshot_id", 1), ("row", 1)])
    print(f"wrote via ${uri_var}: {res.upserted_count} new, {res.modified_count} replaced, "
          f"{stale.deleted_count} stale removed")

    # Read everything back and compare with what was sent.
    back = list(db[ROWS].find({"snapshot_id": sid}).sort("row", 1))
    snap = db[SNAPSHOTS].find_one({"_id": sid})
    strip = lambda d: {k: v for k, v in d.items() if k != "taken_at"}
    problems = []
    if len(back) != len(docs):
        problems.append(f"{len(back)} rows read back, {len(docs)} sent")
    problems += [f"row {d['row']} differs" for d, b in zip(docs, back) if strip(d) != strip(b)]
    if any(b["taken_at"].replace(tzinfo=timezone.utc) != taken_at for b in back):
        problems.append("taken_at differs")
    if not snap or hashlib.sha256(snap["csv_text"].encode("utf-8")).hexdigest() != sha:
        problems.append("snapshot CSV text does not hash back to the file")
    client.close()
    if problems:
        sys.exit("read-back FAILED: " + "; ".join(problems))
    print(f"read back {len(back)} rows and the snapshot from {DB}.{ROWS} / {DB}.{SNAPSHOTS}: all match")


if __name__ == "__main__":
    sys.excepthook = hide_hosts
    main()
