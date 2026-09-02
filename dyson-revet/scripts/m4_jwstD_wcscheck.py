"""M4: verify the L3 mosaic astrometric registration against Gaia DR3 field stars (anonymous TAP)."""
import sys, warnings; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pyvo
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
ROOT="c:/Users/matth/projects/astronomy/dyson-revet/"
svc=pyvo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")
q=("SELECT source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag FROM gaiadr3.gaia_source "
   "WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',351.96953,5.11140,0.030))=1")
g=svc.search(q).to_table().to_pandas()
print(f"Gaia DR3 sources within 108\" of the MIRI pointing: {len(g)}")
gg=g.dropna(subset=["pmra","pmdec"])
gc=SkyCoord(ra=np.asarray(gg.ra)*u.deg,dec=np.asarray(gg.dec)*u.deg,
            pm_ra_cosdec=np.asarray(gg.pmra)*u.mas/u.yr,pm_dec=np.asarray(gg.pmdec)*u.mas/u.yr,
            obstime=Time("J2016.0"))
for f in ["f560w","f1000w","f1500w"]:
    hd=fits.getheader(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits",0)
    t=Time(hd["EXPSTART"],format="mjd")
    gobs=gc.apply_space_motion(new_obstime=t)
    cat=ascii.read(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv")
    cc=SkyCoord(cat["sky_centroid"])
    idx,d2d,_=gobs.match_to_catalog_sky(cc)
    m=d2d.arcsec<0.7
    if m.sum()<2: print(f"  {f}: only {m.sum()} Gaia matches <0.7\" -- no useful WCS check"); continue
    # signed offsets (catalog - gaia)
    dra=(cc[idx][m].ra-gobs[m].ra).to(u.arcsec).value*np.cos(np.radians(gobs[m].dec.value))
    ddec=(cc[idx][m].dec-gobs[m].dec).to(u.arcsec).value
    print(f"  {f}: {m.sum()} Gaia<->L3cat matches <0.7\"  |  median dRA*={np.median(dra):+.4f}\" dDec={np.median(ddec):+.4f}\""
          f"  scatter {np.std(dra):.4f}/{np.std(ddec):.4f}\"  median sep={np.median(d2d.arcsec[m]):.4f}\"")
    print("     G mags of matches:", np.round(np.sort(np.asarray(gg.phot_g_mean_mag)[m]),1)[:12])
