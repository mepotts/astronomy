"""Resolve one NIGHT of raw CRIRES science frames + master calibrations, without
any reduced product to walk (the nights beta Pic b needs have no ADPs, so
urls_for_night.py's PROV-chain route cannot start).

Science-frame URLs come straight from dbo.raw dp_ids; the master-calibration set
comes from calSelector datalink on ONE science frame of the night (same trap rules
as urls_for_night.py: clean env, /usr/bin/curl, content-validated retries).

Usage: m19_urls_from_raw.py NIGHT OBJLIST OUT.txt
  NIGHT    e.g. 2022-04-05
  OBJLIST  comma-separated ESO OBJECT names, e.g. "BET PIC B,BETA PIC B"
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.parse

from astropy.table import Table

ENV = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
TAP = "https://archive.eso.org/tap_obs/sync"


def curl(url, tries=12, need=None, expect_json=False):
    for k in range(tries):
        p = subprocess.run(["/usr/bin/curl", "-sL", "--max-time", "240", url],
                           capture_output=True, env=ENV)
        body = p.stdout
        if p.returncode == 0 and body:
            if expect_json:
                try:
                    return json.loads(body)
                except ValueError:
                    pass
            elif body.lstrip().startswith(b"<?xml") and (need is None or need in body):
                return body
        time.sleep(min(10 * (k + 1), 60))
    raise RuntimeError(f"no usable response for {url[:90]}")


def fetch(url, need, tries=12):
    return curl(url, tries=tries, need=need)


def tap(query):
    qs = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL",
                                 "FORMAT": "json", "QUERY": query})
    j = curl(f"{TAP}?{qs}", expect_json=True)
    cols = [c["name"] for c in j["metadata"]]
    return [dict(zip(cols, row)) for row in j["data"]]


night, objlist, out = sys.argv[1], sys.argv[2], sys.argv[3]
names = " OR ".join(f"object = '{n.strip()}'" for n in objlist.split(","))
rows = tap(f"""
    SELECT dp_id FROM dbo.raw
    WHERE instrument = 'CRIRES' AND dp_cat = 'SCIENCE' AND ({names})
      AND date_obs BETWEEN '{night}' AND '{night}T23:59:59'
    """)
sci = sorted(r["dp_id"] for r in rows)
if not sci:
    raise SystemExit(f"no science frames on {night}")
print(f"{night}: {len(sci)} science frames")

urls = [f"https://dataportal.eso.org/dataPortal/file/{d}" for d in sci]
seen = set(urls)

# calibrations from calSelector on the first science frame
t = Table.read(io.BytesIO(fetch(
    f"https://archive.eso.org/datalink/links?ID=ivo://eso.org/ID?{sci[0]}",
    b"calSelector_raw2master")), format="votable")
mu = [str(r["access_url"]) for r in t
      if "raw2mast" in str(r["semantics"]) and str(r["access_url"]).strip()][0]
m = Table.read(io.BytesIO(fetch(mu, b"dataPortal")), format="votable")
n_cal = 0
for r in m:
    u = str(r["access_url"])
    if str(r["eso_category"]) == "ASSOCIATION_TREE" or not u.startswith("https://dataportal"):
        continue
    if u not in seen:
        seen.add(u)
        urls.append(u)
        n_cal += 1
print(f"{night}: +{n_cal} calibration files -> {len(urls)} total")
if n_cal < 3:
    raise SystemExit(f"only {n_cal} calibs resolved; refusing")
with open(out, "w") as f:
    f.write("\n".join(urls) + "\n")
