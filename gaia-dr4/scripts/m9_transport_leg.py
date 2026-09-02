#!/usr/bin/env python
"""M9: the chain's TRANSPORT leg -- M7's phase B, re-run as a chain stage.

M7's day-one dry run proved DataLink transport at 981-row scale and left the
fetched products in `data/epoch_cache/Gaia_DR3/`.  Re-running it there is a
981-row cache-hit test, which measures nothing.  This wrapper runs the SAME
production harness over the SAME payload-stratified 981 ids against a
CACHE ROOT OF ITS OWN, so the network is genuinely exercised and the chain's
wall clock contains a real transport leg.

Nothing else changes: same `epoch_vet_harness.run(...)`, same batching,
same retry/backoff/Retry-After policy, same atomic per-source cache, same
append-only transport ledger, same resume.  DR3 EPOCH_PHOTOMETRY is a
stand-in for DR4 epoch astrometry in KIND (M7 sec.1b); the cost model
`t = 2.42 s + 0.215 s/source x n + 0.1424 s/KiB x KiB` converts between
them and is the only thing that may be quoted for December.

  .venv\\Scripts\\python.exe scripts\\m9_transport_leg.py --queue ... --ledger ...
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epoch_vet_harness as H                                    # noqa: E402
import m7_day1_dryrun as D7                                      # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--queue", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--cache-root", default=None,
                    help="a cache root of this leg's own, so the fetch is "
                         "real rather than a cache-hit replay")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--gap", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--progress-every", type=int, default=5)
    a = ap.parse_args(argv)

    if a.cache_root:
        root = os.path.join(BASE, a.cache_root) \
            if not os.path.isabs(a.cache_root) else a.cache_root
        os.makedirs(root, exist_ok=True)
        H.CACHE_ROOT = root
        print("transport leg: cache root -> %s" % root)

    src = D7.PhotometryDataLinkSource()
    led, stats = H.run(source="datalink", queue=a.queue, limit=a.limit,
                       batch=a.batch, gap=a.gap,
                       ledger=(a.ledger if os.path.isabs(a.ledger)
                               else os.path.join(BASE, a.ledger)),
                       timings=os.path.join(BASE, "out", "m9_chain",
                                            "transport_timings.csv"),
                       run_id="m9_chain_transport",
                       epoch_source=src, transport_only=True,
                       progress_every=a.progress_every)
    print("transport leg stats: %s" % stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
