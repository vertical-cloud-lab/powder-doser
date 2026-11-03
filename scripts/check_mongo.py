#!/usr/bin/env python3
"""Preflight: can this machine reach the powder_doser MongoDB, and via
which credential source?  Never prints the connection string.

Resolution order (opt_common.resolve_mongo_uri): ``$MONGODB_URI`` ->
``$PI_MONGODB_URI`` -> ``~/.config/powder-doser/env`` (the PR #131
on-device file).  Run it anywhere a campaign script will run --
laptop, Pi Zero (including over non-interactive SSH), or CI:

    python3 scripts/check_mongo.py
    ssh <zero> 'cd ~/powder-doser && \
        ~/powder-doser-venv/bin/python scripts/check_mongo.py'

Exit codes: 0 reachable, 2 no URI found, 3 pymongo missing,
4 connect/auth failed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402


def main(argv=None):
    uri, source = oc.resolve_mongo_uri()
    if not uri:
        print("no MongoDB URI found (checked ${}, ${}, {})".format(
            oc.MONGODB_URI_ENV, oc.MONGODB_URI_ENV_FALLBACKS[0],
            oc.MONGODB_ENV_FILE))
        return 2
    print("URI source: {}".format(source))
    try:
        import pymongo
    except ImportError:
        print("pymongo is not installed for {} -- on the Zero use "
              "~/powder-doser-venv/bin/python".format(sys.executable))
        return 3
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=15000)
        client.admin.command("ping")
        db = client[oc.DB_NAME]
        names = sorted(n for n in db.list_collection_names()
                       if not n.startswith("system."))
        print("ping OK -- database {!r}, collections: {}".format(
            oc.DB_NAME, ", ".join(names) or "(none yet)"))
        campaign = (oc.COLL_CAMPAIGNS, oc.COLL_TRIALS, oc.COLL_PROFILES,
                    oc.COLL_POWDER_MODELS)
        missing = [n for n in campaign if n not in names]
        if missing:
            print("campaign collections not created yet (first write "
                  "creates them): {}".format(", ".join(missing)))
        client.close()
    except Exception as exc:
        # Exception text can embed the cluster host from the secret
        # URI, so print only the type; common causes: wrong password,
        # Atlas Network Access blocking this IP, no DNS/egress.
        print("connection FAILED ({})".format(type(exc).__name__))
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
