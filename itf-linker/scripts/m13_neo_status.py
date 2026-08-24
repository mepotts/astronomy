"""M13: freeze each queue object's NEO status into a small committed sidecar.

The MPC's identification criteria exempt NEOs from the rule that kills most of this
queue -- *"attempting to extend a non-NEO orbit across apparitions using a single tracklet
with arc length under 0.75 days"*, with the explicit note that **this criteria does not
apply to NEOs**. So whether a row is submittable at all can depend on one boolean per
object, and the payload builder needs it.

It cannot look that up at submission time. MPCORB is 181 MB and lives on
``minorplanetcenter.net``, which is unreachable from a GitHub runner -- the whole reason
the archive cron moved to a local machine. So the lookup happens **here**, on a connection
that can reach the MPC, and the answer is committed as a few kilobytes of JSON that the
runner reads instead.

NEO is taken as **q < 1.3 au**, the IAU/MPC definition, computed as ``a(1-e)`` from the
orbit MPCORB publishes; ``Orbit_type`` is carried alongside for a human reading the file.
An object absent from this sidecar is treated by the builder as **non-NEO**, which is the
restrictive branch -- an unknown object gets the stricter rule, never the exemption.

Regenerate whenever the review queue changes.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from itf_linker.attrib.bulk import iter_mpcorb_objects

NEO_PERIHELION_AU = 1.3


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--mpcorb", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rows = list(csv.DictReader(args.queue.open(encoding="utf-8-sig")))
    want = {r["object"] for r in rows}
    print(f"{len(want)} distinct objects to look up", flush=True)

    found: dict[str, dict] = {}
    for obj in iter_mpcorb_objects(args.mpcorb):
        desig = str(obj.get("Principal_desig") or "")
        if desig not in want or desig in found:
            continue
        a, e = obj.get("a"), obj.get("e")
        q = float(a) * (1.0 - float(e)) if a is not None and e is not None else None
        found[desig] = {
            "q_au": round(q, 4) if q is not None else None,
            "orbit_type": obj.get("Orbit_type"),
            "is_neo": bool(q is not None and q < NEO_PERIHELION_AU),
        }
        if len(found) == len(want):
            break

    missing = sorted(want - set(found))
    n_neo = sum(1 for v in found.values() if v["is_neo"])
    doc = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queue": args.queue.name,
        "mpcorb": args.mpcorb.name,
        "neo_definition": f"perihelion q = a(1-e) < {NEO_PERIHELION_AU} au",
        "note": "An object absent from `objects` is treated as NON-NEO by the payload "
                "builder -- the restrictive branch. Never infer the exemption from "
                "absence.",
        "n_objects": len(found),
        "n_neo": n_neo,
        "missing_from_mpcorb": missing,
        "objects": dict(sorted(found.items())),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"resolved {len(found)}/{len(want)}; NEOs {n_neo}; missing {len(missing)}",
          flush=True)
    print(f"wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
