"""M4 photometry: deblended star/contaminant measurement on JWST GO-7199 MIRI L3 mosaics.

Method:
  * star position = Gaia DR3 2660349163149053824 propagated to MJD 60884.2 (JWST epoch)
  * contaminant position = quadratic centroid on its peak
  * empirical radial PSF from isolated field point sources -> cross-contamination model
  * circular aperture photometry at CRDS EE30/EE50/EE70 radii (from the L3 cat apcorr meta),
    local sky from a 3.0-4.5" annulus, cross-contamination subtracted, CRDS apcorr applied
"""
import sys, warnings, json; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import Cutout2D
from astropy.modeling import models, fitting
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureStats, aperture_photometry
from photutils.centroids import centroid_quadratic

ROOT="c:/Users/matth/projects/astronomy/dyson-revet/"
RA16,DEC16,PMRA,PMDEC,PLX = 351.96372836,5.10726195,-30.67371151,-21.61135431,4.69567256
c16=SkyCoord(ra=RA16*u.deg,dec=DEC16*u.deg,pm_ra_cosdec=PMRA*u.mas/u.yr,pm_dec=PMDEC*u.mas/u.yr,
             distance=(1000.0/PLX)*u.pc,obstime=Time("J2016.0"))
FILT=["f560w","f1000w","f1500w"]
PSFREF={"f560w":[(399.1,960.1),(986.3,667.5),(698.4,774.0),(746.8,216.3),(865.0,1012.6)],
        "f1000w":[(399.2,960.9),(986.9,667.9),(216.5,782.5),(698.6,774.5)],
        "f1500w":[(399.2,960.9),(986.9,668.2),(1005.7,325.4),(630.1,869.9)]}
# JDox MIRI imaging PSF FWHM (arcsec), for reference only
JDOX_FWHM={"f560w":0.207,"f1000w":0.328,"f1500w":0.488}

def radial_profile(img,cx,cy,rmax,nbin=60):
    yy,xx=np.mgrid[:img.shape[0],:img.shape[1]]
    r=np.hypot(xx-cx,yy-cy)
    b=np.linspace(0,rmax,nbin+1); rc=0.5*(b[1:]+b[:-1]); prof=np.full(nbin,np.nan)
    for i in range(nbin):
        m=(r>=b[i])&(r<b[i+1])&np.isfinite(img)
        if m.sum()>=3: prof[i]=np.median(img[m])
    return rc,prof

rows=[]; store={}
for f in FILT:
    fn=ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits"
    with fits.open(fn) as h:
        hdr0=h[0].header; sci=h[1].data.astype(float); err=h[2].data.astype(float)
        w=WCS(h[1].header); scale=abs(h[1].header["CDELT1"])*3600.0
        pixar_sr=h[1].header["PIXAR_SR"]; t=Time(hdr0["EXPSTART"],format="mjd")
    cat=ascii.read(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv")
    ap=cat.meta["aperture_params"]
    radii=np.asarray(ap["aperture_radii"]); apcorr=np.asarray(ap["aperture_corrections"])
    cobs=c16.apply_space_motion(new_obstime=t)
    xs,ys=[float(v) for v in w.world_to_pixel(cobs)]

    # ---- empirical normalised PSF radial profile from isolated field sources ----
    profs=[]
    for (px,py) in PSFREF[f]:
        cu=Cutout2D(sci,(px,py),(81,81),mode="strict"); d=cu.data.copy()
        ccx,ccy=cu.to_cutout_position((px,py))
        cq=centroid_quadratic(d,xpeak=ccx,ypeak=ccy,fit_boxsize=5)
        yy,xx=np.mgrid[:d.shape[0],:d.shape[1]]; rr=np.hypot(xx-cq[0],yy-cq[1])
        sky=np.median(d[(rr*scale>3.0)&(rr*scale<4.0)])
        d-=sky
        norm=np.nansum(d[rr<radii[2]])           # normalise on the EE70 aperture
        if norm<=0: continue
        rc,pr=radial_profile(d/norm,cq[0],cq[1],35)
        profs.append(pr)
    P=np.nanmedian(np.vstack(profs),axis=0)      # normalised surface brightness / (EE70 flux)
    rc_pix=rc

    # ---- centroids of the two components in the science cutout ----
    HALF=45
    cut=Cutout2D(sci,(xs,ys),(2*HALF+1,2*HALF+1),wcs=w,mode="strict")
    ecut=Cutout2D(err,(xs,ys),(2*HALF+1,2*HALF+1),mode="strict")
    d=cut.data.copy(); e=ecut.data.copy()
    cxs,cys=cut.to_cutout_position((xs,ys))
    yy,xx=np.mgrid[:d.shape[0],:d.shape[1]]
    rs_arc=np.hypot(xx-cxs,yy-cys)*scale
    sky=np.median(d[(rs_arc>3.0)&(rs_arc<4.5)]); skyrms=np.std(d[(rs_arc>3.0)&(rs_arc<4.5)])
    dz=d-sky
    # contaminant: brightest peak between 0.5 and 2.2 arcsec from the star
    ring=(rs_arc>0.5)&(rs_arc<2.2)
    iy,ix=np.unravel_index(np.argmax(np.where(ring,dz,-1e9)),dz.shape)
    cg=centroid_quadratic(dz,xpeak=ix,ypeak=iy,fit_boxsize=5)
    # star: measured centroid where detectable (F560W/F1000W), else Gaia-propagated
    star_meas=centroid_quadratic(dz,xpeak=int(round(cxs)),ypeak=int(round(cys)),fit_boxsize=5)
    store[f]=dict(d=d,sky=sky,skyrms=skyrms,cut=cut,scale=scale,cxs=cxs,cys=cys,
                  cg=cg,star_meas=star_meas,radii=radii,apcorr=apcorr,rc=rc_pix,P=P,
                  pixar_sr=pixar_sr,cobs=cobs,e=e)

    sc_g=cut.wcs.pixel_to_world(cg[0],cg[1]); sc_s=cut.wcs.pixel_to_world(*star_meas)
    print(f"\n{'='*72}\n{f}: sky={sky:.4f} rms={skyrms:.4f} MJy/sr | EE radii(pix)={radii.round(3)} = {(radii*scale).round(4)}\"")
    print(f"  star  Gaia-propagated pix=({cxs:.3f},{cys:.3f})   measured pix=({star_meas[0]:.3f},{star_meas[1]:.3f})  "
          f"delta={np.hypot(star_meas[0]-cxs,star_meas[1]-cys)*scale:.4f}\"")
    print(f"  contaminant pix=({cg[0]:.3f},{cg[1]:.3f})")
    print(f"  sep(Gaia star -> contam)     = {cobs.separation(sc_g).arcsec:.4f}\"  PA={cobs.position_angle(sc_g).deg:.2f} deg")
    print(f"  sep(measured star -> contam) = {sc_s.separation(sc_g).arcsec:.4f}\"  PA={sc_s.position_angle(sc_g).deg:.2f} deg")
np.save(ROOT+"data/jwst/m4_psfprof.npy",np.vstack([store[f]["P"] for f in FILT]))
import pickle; pickle.dump({f:{k:v for k,v in store[f].items() if k not in("cut","cobs")} for f in FILT},
                           open(ROOT+"data/jwst/m4_store.pkl","wb"))
