"""M1 kill checks: is the route reachable TODAY, with no credentials?

(a) TNS API shape + rate limit   (b) a tokenless broker for the full public ZTF
stream   (c) is ZTF still flowing, and how much.

Read-only. No account is created, no credential is read, no write path is touched.
Writes out/m1_killchecks.json.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import OUT, session, write_text  # noqa: E402

R: dict = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def check_tns(s: requests.Session) -> dict:
    out: dict = {"source": "https://www.wis-tns.org"}

    # (1) the documented read API, unauthenticated
    r = s.get("https://www.wis-tns.org/api/get/object", timeout=60)
    out["api_get_object_status"] = r.status_code
    out["api_get_object_body"] = r.text[:200]
    out["rate_limit_headers_api"] = {
        k: v for k, v in r.headers.items() if k.lower().startswith("x-rate-limit")
    }
    time.sleep(8)

    # (2) the tokenless read route actually available: web search CSV export
    url = ("https://www.wis-tns.org/search?&discovered_period_value=1"
           "&discovered_period_units=days&num_page=50&format=csv")
    r2 = s.get(url, timeout=120)
    out["search_csv_status"] = r2.status_code
    out["search_csv_is_csv"] = r2.text.lstrip().startswith('"ID"')
    out["search_csv_content_disposition"] = r2.headers.get("Content-disposition")
    out["rate_limit_headers_search"] = {
        k: v for k, v in r2.headers.items() if k.lower().startswith("x-rate-limit")
    }
    time.sleep(8)

    # (3) the bulk public-object mirror TNS asks you to use for cross-matching
    r3 = s.head("https://www.wis-tns.org/system/files/tns_public_objects/"
                "tns_public_objects.csv.zip", timeout=60)
    out["public_objects_zip_status"] = r3.status_code
    out["public_objects_zip_note"] = (
        "403 unauthenticated: the bulk mirror sits behind the same api_key/tns_marker "
        "POST as /api/get/. Not usable without an account."
    )

    # (4) re-measure the rate limit politely: 4 slow reads, watch the counter
    seen = []
    for _ in range(4):
        rr = s.get("https://www.wis-tns.org/api/get/object", timeout=60)
        seen.append({
            "limit": rr.headers.get("x-rate-limit-limit"),
            "remaining": rr.headers.get("x-rate-limit-remaining"),
            "reset": rr.headers.get("x-rate-limit-reset"),
            "status": rr.status_code,
        })
        time.sleep(1.5)
    out["rate_limit_probe"] = seen
    return out


def check_brokers(s: requests.Session) -> dict:
    out: dict = {}

    # --- ALeRCE ---------------------------------------------------------------
    t0 = time.time()
    r = s.get("https://api.alerce.online/ztf/v1/objects/",
              params={"page_size": 1, "order_by": "lastmjd", "order_mode": "DESC"},
              timeout=60)
    j = r.json()
    newest = j["items"][0]["lastmjd"] if j.get("items") else None
    out["alerce"] = {
        "base": "https://api.alerce.online/ztf/v1/",
        "status": r.status_code,
        "auth_required": False,
        "auth_evidence": "200 with no Authorization header, no cookie, no key",
        "newest_lastmjd": newest,
        "latency_s": round(time.time() - t0, 3),
    }
    r2 = s.get("https://api.alerce.online/ztf/v1/objects/",
               params={"firstmjd": [61271, 61277], "ndet": 2, "page_size": 1,
                       "count": "true"}, timeout=90)
    out["alerce"]["new_objects_mjd61271_61277"] = r2.json().get("total")

    # --- Fink -----------------------------------------------------------------
    t0 = time.time()
    r = s.get("https://api.ztf.fink-portal.org/api/v1/latests",
              params={"class": "Unknown", "n": 1,
                      "columns": "i:objectId,i:jd,i:magpsf"}, timeout=90)
    j = r.json()
    out["fink"] = {
        "base": "https://api.ztf.fink-portal.org/api/v1/",
        "status": r.status_code,
        "auth_required": False,
        "auth_evidence": "200 with no token. Kafka streaming needs free registration; REST does not.",
        "newest_jd": j[0]["i:jd"] if j else None,
        "newest_mjd": round(j[0]["i:jd"] - 2400000.5, 4) if j else None,
        "latency_s": round(time.time() - t0, 3),
    }

    # --- ANTARES --------------------------------------------------------------
    t0 = time.time()
    r = s.get("https://api.antares.noirlab.edu/v1/loci",
              params={"sort": "-properties.newest_alert_observation_time",
                      "page[limit]": 1}, timeout=90)
    j = r.json()
    try:
        newest = j["data"][0]["attributes"]["properties"]["newest_alert_observation_time"]
    except Exception:
        newest = None
    out["antares"] = {
        "base": "https://api.antares.noirlab.edu/v1/",
        "status": r.status_code,
        "auth_required": False,
        "auth_evidence": "200 JSON:API with no token",
        "newest_alert_mjd": newest,
        "latency_s": round(time.time() - t0, 3),
    }
    return out


def check_ztf(s: requests.Session) -> dict:
    r = s.get("https://ztf.uw.edu/alerts/public/", timeout=120)
    rows = re.findall(
        r'(ztf_public_(\d{8})\.tar\.gz)</a></td><td class="indexcollastmod">([^<]*)'
        r'</td><td class="indexcolsize">\s*([^<]*?)\s*</td>', r.text)

    def to_gb(sz: str) -> float:
        sz = sz.strip()
        if sz.endswith("G"):
            return float(sz[:-1])
        if sz.endswith("M"):
            return float(sz[:-1]) / 1024
        if sz.endswith("K"):
            return float(sz[:-1]) / 1024 / 1024
        try:
            return float(sz) / 1e9
        except ValueError:
            return 0.0

    rows_sorted = sorted(rows, key=lambda t: t[1], reverse=True)
    recent = [{"night": t[1], "posted": t[2].strip(), "size": t[3]} for t in rows_sorted[:30]]
    gb = [to_gb(t[3]) for t in rows_sorted[:30]]
    gb_real = [g for g in gb if g > 0.01]  # 74-byte files are weathered-out nights

    # Fink nightly counters: the authoritative alert-count series
    rs = s.post("https://api.ztf.fink-portal.org/api/v1/statistics",
                json={"date": "2026", "output-format": "json"}, timeout=120)
    stats = rs.json()
    sci = [int(x["basic:sci"]) for x in stats]
    sci_recent = [int(x["basic:sci"]) for x in stats[-30:]]

    return {
        "archive": "https://ztf.uw.edu/alerts/public/",
        "n_nightly_tarballs": len(set(t[1] for t in rows)),
        "newest_night": rows_sorted[0][1] if rows_sorted else None,
        "newest_posted": rows_sorted[0][2].strip() if rows_sorted else None,
        "recent_30": recent,
        "median_gb_per_night_last30_observing": round(statistics.median(gb_real), 1),
        "range_gb_last30_observing": [round(min(gb_real), 1), round(max(gb_real), 1)],
        "n_weathered_out_last30": len(gb) - len(gb_real),
        "fink_nights_2026": len(stats),
        "fink_median_sci_alerts_per_night_2026": statistics.median(sci),
        "fink_median_sci_alerts_per_night_last30": statistics.median(sci_recent),
        "fink_max_sci_alerts_per_night_2026": max(sci),
    }


def main() -> None:
    s = session()
    print("kill check (a) TNS ...", flush=True)
    R["tns"] = check_tns(s)
    print("kill check (b) brokers ...", flush=True)
    R["brokers"] = check_brokers(s)
    print("kill check (c) ZTF stream ...", flush=True)
    R["ztf"] = check_ztf(s)

    tokenless = [k for k, v in R["brokers"].items()
                 if v.get("status") == 200 and not v.get("auth_required")]
    R["verdict"] = {
        "tns_read_api_open_unauthenticated": R["tns"]["api_get_object_status"] == 200,
        "tns_tokenless_read_route": "web search CSV export (/search?...&format=csv)",
        "tokenless_brokers": tokenless,
        "ztf_newest_public_night": R["ztf"]["newest_night"],
        "pass": bool(tokenless) and R["tns"]["search_csv_is_csv"],
    }
    write_text(OUT / "m1_killchecks.json", json.dumps(R, indent=2))
    print(json.dumps(R["verdict"], indent=2))


if __name__ == "__main__":
    main()
