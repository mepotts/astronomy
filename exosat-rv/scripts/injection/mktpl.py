"""Make one wavelength-shifted copy of a template per epoch.

Shifting the TEMPLATE by -v injects a stellar RV of +v, because viper measures the
observation against the template. Shifting the OBSERVATION instead moves the tellurics
too, and viper's telluric-anchored wavelength solution absorbs ~92% of it (measured).
"""
import json, shutil, sys, os
from astropy.io import fits
C = 299792458.0
plan = json.load(open(sys.argv[1]))
src, outdir = sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for i, d in enumerate(plan):
    dest = os.path.join(outdir, f"inj{i:02d}_tpl.fits")
    shutil.copy(src, dest)
    with fits.open(dest, mode="update") as h:
        for det in (1, 2, 3):
            for c in h[det].columns:
                if c.name.endswith("_WL"):
                    h[det].data[c.name] = h[det].data[c.name] * (1 - d["v"] / C)
        h.flush()
print(f"wrote {len(plan)} shifted templates from {os.path.basename(src)} to {outdir}")
