#!/usr/bin/env python3
"""Capture the idle scale stream and store it -- tiers 2/3 of issue #126.

The dose-side capture (``dose_run_capture.py``) turns one dispense into
one document.  This is the other half the design doc calls out as
missing: the *idle* stream, i.e. what the balance is doing when nobody
is dosing.  That signal is what tells you about drift, bench vibration,
HVAC, and whether the rig was actually settled when a run started.

Input is the CSV emitted by ``hardware/test-module/firmware/scale_stream.py``
(``M,``/``S,``/``E,`` rows), read live from a pipe or from a saved log::

    ssh pi 'mpremote connect /dev/ttyACM0 run /tmp/scale_stream_run.py' \\
      | tee data/scale-idle/raw.log \\
      | python scripts/scale_stream_capture.py - --upload

Two tiers come out of one pass:

* **tier 3, raw** (``scale_raw``, time-series, TTL'd) -- one document per
  *change*, plus a heartbeat every ``--heartbeat`` seconds.  The dead
  band is exactly one scale count, so this is lossless: the HR-100A
  cannot report a change smaller than its own resolution, and the
  heartbeats bound the "nothing changed" stretches.
* **tier 2, aggregates** (``scale_1min``, permanent) -- min/max/mean/std/
  count/unstable/missed per wall-clock minute, computed from *every*
  sample rather than from the dead-banded subset.

The device has no clock and its ``t_ms`` restarts each run, so absolute
time comes from a host anchor taken at the first sample (recorded in the
metadata as ``anchor_utc``); sample times are ``anchor + t_ms``, which
keeps the device's own inter-sample spacing instead of inheriting host
scheduling jitter.

``--benchmark`` skips storage and instead measures the candidate layouts
against each other on a captured log (see ``--help``).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = 1

RAW_COLLECTION = "scale_raw"
MINUTE_COLLECTION = "scale_1min"

FLAG_STABLE = "S"
FLAG_UNSTABLE = "U"
FLAG_OVERLOAD = "O"
FLAG_MISSED = "X"


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

class Sample:
    """One poll of the balance."""

    __slots__ = ("t_ms", "grams", "flag")

    def __init__(self, t_ms: int, grams, flag: str):
        self.t_ms = t_ms
        self.grams = grams          # float, or None for O/X
        self.flag = flag

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"Sample({self.t_ms}, {self.grams}, {self.flag!r})"

    def __eq__(self, other):
        return (isinstance(other, Sample) and self.t_ms == other.t_ms
                and self.grams == other.grams and self.flag == other.flag)


def strip_repl(line: str) -> str:
    """Drop the control bytes ``mpremote``'s raw REPL wraps output in.

    A piped ``mpremote run`` can prefix the first payload line with
    ``OK`` and sprinkle ``\\x04`` around; without this, the first sample
    of every run is silently lost.
    """
    line = line.replace("\x04", "").replace("\r", "").strip()
    if line.startswith("OK"):
        line = line[2:].lstrip()
    return line


def parse_line(line: str):
    """Parse one protocol row.

    Returns ``("S", Sample)``, ``("M", (key, value))``, ``("E", (t_ms,
    text))``, or ``None`` for anything unrecognised (tracebacks, banner
    text, blank lines).
    """
    line = strip_repl(line)
    if not line or "," not in line:
        return None
    kind, _, rest = line.partition(",")
    if kind == "M":
        key, _, value = rest.partition(",")
        if not key:
            return None
        return ("M", (key.strip(), value.strip()))
    if kind == "E":
        t_txt, _, text = rest.partition(",")
        try:
            return ("E", (int(t_txt), text.strip()))
        except ValueError:
            return None
    if kind != "S":
        return None
    parts = rest.split(",")
    if len(parts) < 3:
        return None
    try:
        t_ms = int(parts[0])
    except ValueError:
        return None
    flag = parts[2].strip().upper()
    if flag not in (FLAG_STABLE, FLAG_UNSTABLE, FLAG_OVERLOAD, FLAG_MISSED):
        return None
    grams = None
    if flag in (FLAG_STABLE, FLAG_UNSTABLE):
        try:
            grams = float(parts[1])
        except ValueError:
            return None
        if math.isnan(grams):
            grams = None
    return ("S", Sample(t_ms, grams, flag))


def coerce_meta(value: str):
    """Metadata arrives as text; keep numbers numeric for querying."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


# --------------------------------------------------------------------------
# tiering
# --------------------------------------------------------------------------

class DeadBand:
    """Emit on change, plus a heartbeat -- the tier-3 filter.

    ``keep(sample)`` is the whole policy: a reading passes if its value
    differs from the last kept value, if its flag changed (a stable ->
    unstable transition is information even at identical mass), or if
    ``heartbeat_s`` has elapsed.
    """

    def __init__(self, heartbeat_s: float = 60.0, epsilon: float = 0.0):
        self.heartbeat_s = heartbeat_s
        self.epsilon = epsilon
        self.last_value = None
        self.last_flag = None
        self.last_kept_ms = None

    def keep(self, sample: Sample) -> bool:
        if self.last_kept_ms is None:
            self._remember(sample)
            return True
        if sample.flag != self.last_flag:
            self._remember(sample)
            return True
        if sample.grams is None or self.last_value is None:
            changed = sample.grams is not self.last_value
        else:
            changed = abs(sample.grams - self.last_value) > self.epsilon
        if changed:
            self._remember(sample)
            return True
        if (sample.t_ms - self.last_kept_ms) >= self.heartbeat_s * 1000:
            self._remember(sample)
            return True
        return False

    def _remember(self, sample: Sample):
        self.last_value = sample.grams
        self.last_flag = sample.flag
        self.last_kept_ms = sample.t_ms


class MinuteAggregator:
    """Tumbling wall-clock-minute stats over *every* sample."""

    def __init__(self, anchor: datetime):
        self.anchor = anchor
        self._bucket_start = None
        self._values = []
        self._n = 0
        self._unstable = 0
        self._missed = 0
        self._first = None
        self._last = None

    def add(self, sample: Sample):
        """Add one sample; returns a finished bucket document or None."""
        ts = self.anchor + timedelta(milliseconds=sample.t_ms)
        minute = ts.replace(second=0, microsecond=0)
        done = None
        if self._bucket_start is None:
            self._bucket_start = minute
        elif minute != self._bucket_start:
            done = self.flush()
            self._bucket_start = minute
        self._n += 1
        if sample.flag == FLAG_UNSTABLE:
            self._unstable += 1
        if sample.flag in (FLAG_MISSED, FLAG_OVERLOAD):
            self._missed += 1
        if sample.grams is not None:
            self._values.append(sample.grams)
            if self._first is None:
                self._first = sample.grams
            self._last = sample.grams
        return done

    def flush(self):
        if self._bucket_start is None or self._n == 0:
            return None
        doc = {
            "t": self._bucket_start,
            "n": self._n,
            "n_unstable": self._unstable,
            "n_missed": self._missed,
        }
        if self._values:
            lo, hi = min(self._values), max(self._values)
            # Rounded because these are derived from a 0.1 mg-resolution
            # instrument; unrounded float noise (0.09999999999998899 mg)
            # is worse than useless in a stored record.
            doc.update({
                "min_g": lo,
                "max_g": hi,
                "ptp_mg": round((hi - lo) * 1000.0, 4),
                "mean_g": round(statistics.fmean(self._values), 7),
                "std_mg": round(statistics.pstdev(self._values) * 1000.0, 4)
                          if len(self._values) > 1 else 0.0,
                "first_g": self._first,
                "last_g": self._last,
            })
        self._values = []
        self._n = self._unstable = self._missed = 0
        self._first = self._last = None
        self._bucket_start = None
        return doc


def raw_doc(sample: Sample, anchor: datetime, meta: dict, seq: int) -> dict:
    """Tier-3 document: short field names, they are paid per sample."""
    return {
        "t": anchor + timedelta(milliseconds=sample.t_ms),
        "m": meta,
        "g": sample.grams,
        "f": sample.flag,
        "seq": seq,
    }


# --------------------------------------------------------------------------
# stream processing
# --------------------------------------------------------------------------

class Capture:
    """Consume the protocol; hand tier-2/tier-3 documents to ``sink``."""

    def __init__(self, meta: dict, anchor: datetime, heartbeat_s=60.0,
                 epsilon=0.0):
        self.meta = meta
        self.anchor = anchor
        self.deadband = DeadBand(heartbeat_s, epsilon)
        self.minutes = MinuteAggregator(anchor)
        self.stream_meta = {}
        self.events = []
        self.n_samples = 0
        self.n_kept = 0
        self.n_minutes = 0
        self.seq = 0
        self.raw_docs = []
        self.minute_docs = []

    def feed_line(self, line: str):
        parsed = parse_line(line)
        if parsed is None:
            return
        kind, payload = parsed
        if kind == "M":
            key, value = payload
            self.stream_meta[key] = coerce_meta(value)
            return
        if kind == "E":
            t_ms, text = payload
            self.events.append({"t_ms": t_ms, "text": text})
            return
        self.feed_sample(payload)

    def feed_sample(self, sample: Sample):
        self.n_samples += 1
        self.seq += 1
        done = self.minutes.add(sample)
        if done is not None:
            self.n_minutes += 1
            self.minute_docs.append(self._decorate(done))
        if self.deadband.keep(sample):
            self.n_kept += 1
            self.raw_docs.append(raw_doc(sample, self.anchor, self.meta,
                                         self.seq))

    def finish(self):
        done = self.minutes.flush()
        if done is not None:
            self.n_minutes += 1
            self.minute_docs.append(self._decorate(done))

    def _decorate(self, doc: dict) -> dict:
        doc["m"] = self.meta
        return doc


def build_meta(args, stream_meta: dict) -> dict:
    meta = {
        "device": args.device_id,
        "scale": args.scale_model,
        "src": stream_meta.get("stream", "scale-idle-v1"),
        "schema_version": SCHEMA_VERSION,
    }
    if args.location:
        meta["location"] = args.location
    if args.note:
        meta["note"] = args.note
    return meta


# --------------------------------------------------------------------------
# storage
# --------------------------------------------------------------------------

def mongo_db(uri=None, dbname="powder_doser"):
    import pymongo

    uri = uri or os.environ.get("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is not set (and --uri not given)")
    return pymongo.MongoClient(uri, serverSelectionTimeoutMS=20000)[dbname]


def ensure_collections(db, ttl_days: int):
    """Create the tier-2/3 collections with the options they need.

    Idempotent: existing collections are left exactly as they are (this
    never silently rewrites a live collection's TTL).
    """
    existing = set(db.list_collection_names())
    created = []
    if RAW_COLLECTION not in existing:
        db.create_collection(
            RAW_COLLECTION,
            timeseries={"timeField": "t", "metaField": "m",
                        "granularity": "seconds"},
            expireAfterSeconds=int(ttl_days * 86400),
        )
        created.append(f"{RAW_COLLECTION} (time-series, TTL {ttl_days} d)")
    if MINUTE_COLLECTION not in existing:
        db.create_collection(
            MINUTE_COLLECTION,
            timeseries={"timeField": "t", "metaField": "m",
                        "granularity": "minutes"},
        )
        created.append(f"{MINUTE_COLLECTION} (time-series, permanent)")
    return created


class Sink:
    """Where finished documents go: JSONL, MongoDB, or a disk spool.

    A bench Pi on residential Wi-Fi will lose Atlas now and then, and
    dropping the idle stream on the floor for that window is exactly the
    kind of silent gap that makes a drift record untrustworthy.  Failed
    batches are appended to ``spool_path`` as ``{collection, doc}`` lines
    and replayed on the next successful flush.
    """

    def __init__(self, db, jsonl=None, spool_path=None):
        self.db = db
        self.jsonl = jsonl
        self.spool_path = spool_path
        self.spooled = 0
        self.inserted = 0

    def flush(self, cap: "Capture"):
        batches = ((RAW_COLLECTION, cap.raw_docs),
                   (MINUTE_COLLECTION, cap.minute_docs))
        for name, docs in batches:
            if not docs:
                continue
            if self.jsonl is not None:
                for doc in docs:
                    self.jsonl.write(json.dumps(
                        {"_c": name, **doc}, default=str) + "\n")
                self.jsonl.flush()
            if self.db is not None:
                self._insert(name, docs)
        cap.raw_docs = []
        cap.minute_docs = []
        if self.db is not None and self.spooled:
            self._replay_spool()

    def _insert(self, name, docs):
        try:
            self.db[name].insert_many(docs)
            self.inserted += len(docs)
        except Exception as exc:
            print(f"insert into {name} failed ({exc}); spooling "
                  f"{len(docs)} documents", file=sys.stderr)
            self._spool(name, docs)

    def _spool(self, name, docs):
        if not self.spool_path:
            return
        with open(self.spool_path, "a") as handle:
            for doc in docs:
                handle.write(json.dumps({"_c": name, "doc": doc},
                                        default=str) + "\n")
        self.spooled += len(docs)

    def _replay_spool(self):
        """Best-effort: only clears the spool if everything went in."""
        if not self.spool_path or not os.path.exists(self.spool_path):
            return
        pending = []
        with open(self.spool_path) as handle:
            for line in handle:
                try:
                    pending.append(json.loads(line))
                except ValueError:
                    continue
        try:
            for entry in pending:
                doc = entry["doc"]
                doc["t"] = datetime.fromisoformat(doc["t"])
                self.db[entry["_c"]].insert_one(doc)
        except Exception as exc:
            print(f"spool replay stopped ({exc}); spool kept",
                  file=sys.stderr)
            return
        os.remove(self.spool_path)
        self.spooled = 0


def collection_size(db, name: str) -> dict:
    """Size numbers for either collection type.

    ``size`` is the metric that matters: it is the BSON actually stored
    server-side, which for a time-series collection means the *bucket*
    documents (column-compressed), not the measurements you handed in.
    That is also what ``dbstats.dataSize`` sums, i.e. what the Atlas
    free-tier 512 MB quota is metered against.

    ``storageSize`` is the on-disk WiredTiger figure and is useless at
    bench scale -- it reports the 4 KB minimum allocation until a
    checkpoint happens, so it is reported but never extrapolated from.
    """
    try:
        stats = db.command("collStats", name)
    except Exception as exc:  # pragma: no cover - server-dependent
        return {"error": str(exc)}
    out = {
        "size": stats.get("size", 0),
        "storageSize": stats.get("storageSize", 0),
        "totalIndexSize": stats.get("totalIndexSize", 0),
        "count": stats.get("count", 0),
    }
    if "timeseries" in stats:
        ts = stats["timeseries"]
        out["buckets"] = ts.get("bucketCount", 0)
        out["avgBucketSize"] = ts.get("avgBucketSize", 0)
        out["measurements"] = ts.get("numMeasurementsCommitted", 0)
    return out


# --------------------------------------------------------------------------
# benchmark
# --------------------------------------------------------------------------

def bson_bytes(docs) -> int:
    """Uncompressed BSON size -- the metric Atlas free-tier quota uses."""
    import bson

    return sum(len(bson.encode(d)) for d in docs)


def build_layouts(samples, anchor, meta, heartbeat_s, epsilon):
    """The candidate storage layouts, all from the same real samples."""
    verbose = []
    compact = []
    for i, s in enumerate(samples, start=1):
        ts = anchor + timedelta(milliseconds=s.t_ms)
        verbose.append({
            "timestamp": ts,
            "device_id": meta["device"],
            "scale_model": meta["scale"],
            "source": meta["src"],
            "schema_version": SCHEMA_VERSION,
            "mass_grams": s.grams,
            "status_flag": s.flag,
            "stable": s.flag == FLAG_STABLE,
            "sequence_number": i,
        })
        compact.append(raw_doc(s, anchor, meta, i))

    band = DeadBand(heartbeat_s, epsilon)
    deadbanded = [d for d, s in zip(compact, samples) if band.keep(s)]

    agg = MinuteAggregator(anchor)
    minute_docs = []
    for s in samples:
        done = agg.add(s)
        if done is not None:
            done["m"] = meta
            minute_docs.append(done)
    done = agg.flush()
    if done is not None:
        done["m"] = meta
        minute_docs.append(done)

    return [
        ("A: plain collection, every sample, verbose fields", verbose, False),
        ("B: time-series, every sample, short fields", compact, True),
        ("C: time-series, dead-band + heartbeat", deadbanded, True),
        ("D: 1-minute aggregates only", minute_docs, True),
    ]


def run_benchmark(db, samples, anchor, meta, args):
    """Insert each layout into a scratch collection and measure it.

    Scratch collections are dropped afterwards -- ``scale_raw`` /
    ``scale_1min`` are never touched by this path.
    """
    span_s = (samples[-1].t_ms - samples[0].t_ms) / 1000.0 if samples else 0.0
    rate_hz = (len(samples) - 1) / span_s if span_s > 0 else 0.0
    results = []
    for label, docs, timeseries in build_layouts(
            samples, anchor, meta, args.heartbeat, args.epsilon):
        row = {
            "layout": label,
            "docs": len(docs),
            "bson_bytes": bson_bytes(docs),
        }
        if db is not None and docs:
            name = "bench_" + label.split(":")[0].strip().lower()
            db.drop_collection(name)
            if timeseries:
                db.create_collection(
                    name,
                    timeseries={"timeField": "t", "metaField": "m",
                                "granularity": "seconds" if len(docs) > 100
                                else "minutes"})
            db[name].insert_many(docs)
            row["server"] = collection_size(db, name)
            if not args.keep_scratch:
                db.drop_collection(name)
        # Extrapolate to a full day of the same behaviour, from the
        # server-side stored size when we have it (bucketing changes the
        # answer by ~70x, so client-side BSON is not a stand-in).
        stored = row.get("server", {}).get("size") or row["bson_bytes"]
        row["stored_bytes"] = stored
        if span_s > 0:
            row["bytes_per_day"] = stored * 86400.0 / span_s
            row["days_to_512mb"] = (512 * 1024 * 1024) / row["bytes_per_day"]
        results.append(row)
    return {"n_samples": len(samples), "span_s": span_s, "rate_hz": rate_hz,
            "layouts": results}


def format_benchmark(report) -> str:
    lines = [
        f"samples={report['n_samples']}  span={report['span_s']:.1f}s  "
        f"rate={report['rate_hz']:.2f} Hz",
        "",
        f"{'layout':<50}{'docs':>7}{'BSON in':>13}{'stored':>12}"
        f"{'MB/day':>9}{'days->512MB':>13}",
    ]
    for row in report["layouts"]:
        mb_day = row.get("bytes_per_day", 0) / 1e6
        days = row.get("days_to_512mb", 0)
        lines.append(f"{row['layout']:<50}{row['docs']:>7}"
                     f"{row['bson_bytes']:>12,}B{row['stored_bytes']:>11,}B"
                     f"{mb_day:>9.2f}{days:>13,.0f}")
    for row in report["layouts"]:
        if "server" in row:
            s = row["server"]
            lines.append(
                f"  {row['layout'][:1]}  index={s.get('totalIndexSize', 0):,}B"
                + (f" buckets={s['buckets']} avg={s['avgBucketSize']:,}B"
                   if "buckets" in s else ""))
    lines.append("")
    lines.append("'stored' is server-side collStats.size (bucket documents "
                 "for time-series), which is what dbstats.dataSize -- and "
                 "the 512 MB free-tier quota -- counts.")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def read_lines(path):
    if path == "-":
        for line in sys.stdin:
            yield line
    else:
        with open(path, "r", errors="replace") as handle:
            for line in handle:
                yield line


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="log file, or '-' for stdin (live pipe)")
    p.add_argument("--device-id", default="rpi-zero2w-powder-doser")
    p.add_argument("--scale-model", default="AND HR-100A")
    p.add_argument("--location", default=None)
    p.add_argument("--note", default=None)
    p.add_argument("--heartbeat", type=float, default=60.0,
                   help="seconds between forced tier-3 samples (default 60)")
    p.add_argument("--epsilon", type=float, default=0.0,
                   help="dead band in grams; 0 means 'any change at all', "
                        "which is lossless at the scale's own resolution")
    p.add_argument("--anchor-utc", default=None,
                   help="ISO-8601 UTC time of the first sample "
                        "(default: now, taken when the first sample arrives)")
    p.add_argument("--jsonl", default=None,
                   help="also write tier-3 + tier-2 documents here as JSONL")
    p.add_argument("--upload", action="store_true",
                   help="insert into scale_raw / scale_1min")
    p.add_argument("--flush-every", type=float, default=30.0,
                   help="seconds of stream time between inserts (default 30)")
    p.add_argument("--spool", default=None,
                   help="file to hold documents that failed to insert; "
                        "replayed on the next successful flush")
    p.add_argument("--ensure-collections", action="store_true",
                   help="create the time-series collections if missing")
    p.add_argument("--ttl-days", type=float, default=90.0,
                   help="tier-3 retention when creating scale_raw")
    p.add_argument("--benchmark", action="store_true",
                   help="measure candidate layouts instead of storing")
    p.add_argument("--keep-scratch", action="store_true",
                   help="do not drop benchmark scratch collections")
    p.add_argument("--uri", default=None)
    p.add_argument("--db", default="powder_doser")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    anchor = (datetime.fromisoformat(args.anchor_utc).replace(tzinfo=None)
              if args.anchor_utc else datetime.now(timezone.utc).replace(
                  tzinfo=None, microsecond=0))

    db = None
    if args.upload or args.ensure_collections or args.benchmark:
        try:
            db = mongo_db(args.uri, args.db)
        except SystemExit:
            if args.benchmark:
                db = None          # benchmark still works offline
            else:
                raise

    if args.ensure_collections and db is not None:
        for created in ensure_collections(db, args.ttl_days):
            print(f"created {created}", file=sys.stderr)

    meta = build_meta(args, {})
    cap = Capture(meta, anchor, args.heartbeat, args.epsilon)
    jsonl = open(args.jsonl, "w") if (args.jsonl and not args.benchmark) else None
    sink = Sink(db if args.upload else None, jsonl, args.spool)
    samples = []
    last_flush_ms = 0
    for line in read_lines(args.source):
        parsed = parse_line(line)
        if parsed is None:
            continue
        kind, payload = parsed
        if kind == "M":
            cap.stream_meta[payload[0]] = coerce_meta(payload[1])
            continue
        if kind == "E":
            cap.events.append({"t_ms": payload[0], "text": payload[1]})
            continue
        if args.benchmark:
            samples.append(payload)
            continue
        cap.feed_sample(payload)
        # Flush on stream time, not host time: a replayed log then
        # batches exactly the way the live pipe did.
        if payload.t_ms - last_flush_ms >= args.flush_every * 1000:
            last_flush_ms = payload.t_ms
            sink.flush(cap)
    cap.finish()
    cap.meta["src"] = cap.stream_meta.get("stream", cap.meta["src"])

    if args.benchmark:
        if not samples:
            raise SystemExit("no samples parsed from " + args.source)
        report = run_benchmark(db, samples, anchor, cap.meta, args)
        print(format_benchmark(report))
        if args.jsonl:
            with open(args.jsonl, "w") as handle:
                json.dump(report, handle, indent=2, default=str)
        return 0

    sink.flush(cap)
    if jsonl is not None:
        jsonl.close()
    if sink.spooled:
        print(f"WARNING: {sink.spooled} documents could not be inserted and "
              f"were spooled to {args.spool}", file=sys.stderr)

    if not args.quiet:
        kept = cap.n_kept
        total = cap.n_samples or 1
        print(f"samples={cap.n_samples} tier3_kept={kept} "
              f"({100.0 * kept / total:.1f}%) tier2_minutes={cap.n_minutes} "
              f"inserted={sink.inserted} spooled={sink.spooled}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
