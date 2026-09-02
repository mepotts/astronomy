"""M4 core: locate star + contaminant in MIRI L3 mosaics, measure sep/PA/contrast/FWHM."""
import sys, warnings, json; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import Cutout2D
from astropy.modeling import models, fitting
from photutils.centroids import centroid_com, centroid_quadratic
from photutils.detection import find_peaks

ROOT="c:/Users/matth/projects/astronomy/dyson-revet/"
RA16, DEC16 = 351.96372836, 5.10726195
PMRA, PMDEC, PLX = -30.67371151, -21.61135431, 4.69567256
c16 = SkyCoord(ra=RA16*u.deg, dec=DEC16*u.deg, pm_ra_cosdec=PMRA*u.mas/u.yr,
               pm_dec=PMDEC*u.mas/u.yr, distance=(1000.0/PLX)*u.pc, obstime=Time("J2016.0"))
FILT=["f560w","f1000w","f1500w"]
HALF=45  # pixels -> ~10 arcsec box

out={}
for f in FILT:
    fn=ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits"
    with fits.open(fn) as h:
        hdr0=h[0].header; sci=h[1].data.astype(float); err=h[2].data.astype(float)
        w=WCS(h[1].header); scale=abs(h[1].header["CDELT1"])*3600.0
        t=Time(hdr0["EXPSTART"],format="mjd")
    cobs=c16.apply_space_motion(new_obstime=t)
    xs,ys=[float(v) for v in w.world_to_pixel(cobs)]
    cut=Cutout2D(sci,(xs,ys),(2*HALF+1,2*HALF+1),wcs=w,mode="strict")
    ecut=Cutout2D(err,(xs,ys),(2*HALF+1,2*HALF+1),wcs=w,mode="strict")
    d=cut.data
    print("\n"+"="*70); print(f"{f}  scale={scale:.5f}\"/pix  star pix ({xs:.2f},{ys:.2f})  cutout OK, no NaN: {np.isfinite(d).all()}")
    # local background from an annulus 3-4.5"
    yy,xx=np.mgrid[:d.shape[0],:d.shape[1]]
    cx,cy=cut.to_cutout_position((xs,ys))
    r=np.hypot(xx-cx,yy-cy)*scale
    ann=(r>3.0)&(r<4.5)
    bkg=np.median(d[ann]); rms=np.std(d[ann])
    print(f"  local bkg (3-4.5\" ann) = {bkg:.4f} MJy/sr, rms = {rms:.4f}")
    # peaks within 2.5"
    core=(r<2.5)
    pk=find_peaks(np.where(core,d-bkg,-1e9), threshold=5*rms, box_size=3, npeaks=8)
    print("  peaks within 2.5\" (>5sigma):")
    if pk is not None:
        pk.sort("peak_value"); pk.reverse()
        for row in pk:
            px,py=row["x_peak"],row["y_peak"]
            sc=cut.wcs.pixel_to_world(px,py)
            print(f"    pix({px},{py}) val={row['peak_value']:.2f}  sep_from_star={cobs.separation(sc).arcsec:.3f}\" PA={cobs.position_angle(sc).deg:.1f}")
    out[f]=dict(cut=cut,ecut=ecut,d=d,bkg=bkg,rms=rms,cx=cx,cy=cy,scale=scale,cobs=cobs,t=t)
    np.save(ROOT+f"data/jwst/m4_cut_{f}.npy", d)
    # ASCII render for eyeball, 21x21 centred on star, log scale
    print("  --- 21x21 around Gaia star position (log10 of bkg-sub, '.'=<=0) ; +x=right(-RA), +y=up(+Dec) ---")
    i0,j0=int(round(cy)),int(round(cx))
    for i in range(i0+10,i0-11,-1):
        srow=""
        for j in range(j0-10,j0+11):
            v=d[i,j]-bkg
            srow += "." if v<=0 else "0123456789ABCD"[min(13,int(np.log10(v)*3+6))] if v>0 else "."
        print("   ",srow, " <-- star row" if i==i0 else "")
import pickle
pickle.dump({k:{kk:vv for kk,vv in v.items() if kk in ("bkg","rms","cx","cy","scale")} for k,v in out.items()}, open(ROOT+"data/jwst/m4_meta.pkl","wb"))
