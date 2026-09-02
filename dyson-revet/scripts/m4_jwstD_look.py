import sys, warnings; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time

RA16, DEC16 = 351.96372836, 5.10726195
PMRA, PMDEC, PLX = -30.67371151, -21.61135431, 4.69567256
c16 = SkyCoord(ra=RA16*u.deg, dec=DEC16*u.deg, pm_ra_cosdec=PMRA*u.mas/u.yr,
               pm_dec=PMDEC*u.mas/u.yr, distance=(1000.0/PLX)*u.pc, obstime=Time("J2016.0"))

for f in ["f560w","f1000w","f1500w"]:
    fn=f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits"
    with fits.open(fn) as h:
        t = Time(h[0].header["EXPSTART"], format="mjd"); w = WCS(h[1].header); sci=h[1].data
    cobs = c16.apply_space_motion(new_obstime=t)
    x,y = [float(v) for v in w.world_to_pixel(cobs)]
    print(f"\n{'='*24} {f}  epoch {t.decimalyear:.4f}  star pix ({x:.2f},{y:.2f})  PM shift {c16.separation(cobs).arcsec:.4f}\"")
    xi,yi=int(round(x)),int(round(y))
    st = sci[yi-30:yi+31, xi-30:xi+31]
    print(f"  stamp finite {np.isfinite(st).sum()}/{st.size}  max {np.nanmax(st):.2f}  med {np.nanmedian(st):.3f} MJy/sr; edge margins x:{min(xi,sci.shape[1]-xi)} y:{min(yi,sci.shape[0]-yi)} pix")
    cat = ascii.read(f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv")
    cc = SkyCoord(cat["sky_centroid"])
    sep = cobs.separation(cc).arcsec
    m = sep < 4.0
    print(f"  L3 catalog: {len(cat)} sources total; {m.sum()} within 4\" of star")
    sub = cat[m]; ss = sep[m]; o=np.argsort(ss)
    for k in o:
        r=sub[k]
        pa = cobs.position_angle(cc[m][k]).deg
        print(f"   sep={ss[k]:.4f}\" PA={pa:6.1f}  ABmag_tot={r['aper_total_abmag']:.3f}+-{r['aper_total_abmag_err']:.3f}"
              f"  f70={r['aper70_flux']:.4e}Jy ftot={r['aper_total_flux']:.4e}Jy"
              f"  CI7030={r['CI_70_30']:.3f} ext={r['is_extended']} sharp={r['sharpness']:.3f} round={r['roundness']:.3f}")
