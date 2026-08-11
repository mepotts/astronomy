"""Resolve one ADP product to every raw frame + master needed to redo it.

Two traps, both hit:
  * the cr2res prefix contains a deliberately SSL-less libcurl; if cr2env.sh has been
    sourced it sits on LD_LIBRARY_PATH and every curl in the shell returns HTTP 000.
    Network stages must run in a clean environment -- /usr/bin/curl is used explicitly.
  * archive.eso.org intermittently returns a VOTable that parses fine but is missing the
    calSelector rows, so validity has to be checked on CONTENT, inside the retry loop.
"""
import io, os, subprocess, sys, time
from astropy.io import fits
from astropy.table import Table

ADP_DIR = "/mnt/c/Users/matth/projects/astronomy/exosat-rv/data/spectra"
ENV = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}

def fetch(url, need, tries=12):
    """GET url until the response actually contains `need`."""
    for k in range(tries):
        p = subprocess.run(["/usr/bin/curl", "-sL", "--max-time", "240", url],
                           capture_output=True, env=ENV)
        if p.returncode == 0 and p.stdout.lstrip().startswith(b"<?xml") and need in p.stdout:
            return p.stdout
        time.sleep(min(10 * (k + 1), 60))
    raise RuntimeError(f"no usable response for {url[:90]} (wanted {need!r})")

adp, out = sys.argv[1], sys.argv[2]
h = fits.getheader(os.path.join(ADP_DIR, adp))
prov = [h[f"PROV{n}"].replace(".fits", "") for n in (1, 2, 3, 4) if f"PROV{n}" in h]
urls, seen = [], set()
for dp in prov:
    t = Table.read(io.BytesIO(fetch(
        f"https://archive.eso.org/datalink/links?ID=ivo://eso.org/ID?{dp}",
        b"calSelector_raw2master")), format="votable")
    mu = [str(r["access_url"]) for r in t
          if "raw2mast" in str(r["semantics"]) and str(r["access_url"]).strip()][0]
    m = Table.read(io.BytesIO(fetch(mu, b"dataPortal")), format="votable")
    for r in m:
        u = str(r["access_url"])
        if str(r["eso_category"]) == "ASSOCIATION_TREE" or not u.startswith("https://dataportal"):
            continue
        if u not in seen:
            seen.add(u); urls.append(u)
if len(urls) < 10:
    raise RuntimeError(f"only {len(urls)} files resolved for {adp}; refusing to proceed")
with open(out, "w") as f:
    f.write("\n".join(urls) + "\n")
print(f"{adp} {h['DATE-OBS'][:10]} -> {len(urls)} files")
