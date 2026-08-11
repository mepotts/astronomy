"""cr2res extracts 8 orders (02-09); ESO's IDP keeps 7 (02-08), and so does our template.

viper derives the DRS order from `columns.names[-1]` separately for the observation and the
template, so a different highest order puts them permanently one order apart -- every pixel
is trimmed and you get the empty-index IndexError of M2 s3. Drop order 09 to realign.
"""
import sys, glob, os
from astropy.io import fits

for src in sys.argv[1:]:
    h = fits.open(src)
    out = [fits.PrimaryHDU(header=h[0].header)]
    for det in (1, 2, 3):
        keep = [c for c in h[det].columns if not c.name.startswith("09_")]
        out.append(fits.BinTableHDU.from_columns(keep, name=h[det].name,
                                                 header=h[det].header))
    dest = src.replace(".fits", "_o8.fits")
    fits.HDUList(out).writeto(dest, overwrite=True)
    n = len([c for c in fits.open(dest)[1].columns])
    print(f"{os.path.basename(dest)}: {n} cols/detector "
          f"(was {len(h[1].columns)}), orders "
          f"{sorted({c.name.split('_')[0] for c in fits.open(dest)[1].columns})}")
