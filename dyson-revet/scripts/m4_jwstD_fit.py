"""M4: simultaneous 2-component fit (avoids the centroid-dragging trap) + deblended aperture phot."""
import sys, warnings, json; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import Cutout2D
from astropy.modeling import models, fitting
from photutils.aperture import CircularAperture, CircularAnnulus, aperture_photometry
from photutils.centroids import centroid_quadratic

ROOT="c:/Users/matth/projects/astronomy/dyson-revet/"
RA16,DEC16,PMRA,PMDEC,PLX = 351.96372836,5.10726195,-30.67371151,-21.61135431,4.69567256
c16=SkyCoord(ra=RA16*u.deg,dec=DEC16*u.deg,pm_ra_cosdec=PMRA*u.mas/u.yr,pm_dec=PMDEC*u.mas/u.yr,
             distance=(1000.0/PLX)*u.pc,obstime=Time("J2016.0"))
FILT=["f560w","f1000w","f1500w"]
PSFREF={"f560w":[(399.1,960.1),(986.3,667.5),(698.4,774.0),(746.8,216.3),(865.0,1012.6)],
        "f1000w":[(399.2,960.9),(986.9,667.9),(216.5,782.5),(698.6,774.5)],
        "f1500w":[(399.2,960.9),(986.9,668.2),(1005.7,325.4),(630.1,869.9)]}
JDOX={"f560w":0.207,"f1000w":0.328,"f1500w":0.488}   # JDox MIRI imaging PSF FWHM, arcsec
res={}; rows=[]
for f in FILT:
    with fits.open(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits") as h:
        sci=h[1].data.astype(float); err=h[2].data.astype(float); w=WCS(h[1].header)
        scale=abs(h[1].header["CDELT1"])*3600.0; t=Time(h[0].header["EXPSTART"],format="mjd")
    cat=ascii.read(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv"); ap=cat.meta["aperture_params"]
    radii=np.asarray(ap["aperture_radii"]); apcorr=np.asarray(ap["aperture_corrections"])
    cobs=c16.apply_space_motion(new_obstime=t)
    xs,ys=[float(v) for v in w.world_to_pixel(cobs)]
    H=45; cut=Cutout2D(sci,(xs,ys),(2*H+1,2*H+1),wcs=w,mode="strict")
    ecut=Cutout2D(err,(xs,ys),(2*H+1,2*H+1),mode="strict")
    d=cut.data.copy(); e=ecut.data.copy(); cxs,cys=cut.to_cutout_position((xs,ys))
    yy,xx=np.mgrid[:d.shape[0],:d.shape[1]]
    rs=np.hypot(xx-cxs,yy-cys)*scale
    sky=np.median(d[(rs>3.0)&(rs<4.5)]); skyrms=np.std(d[(rs>3.0)&(rs<4.5)]); dz=d-sky

    # --- reference PSF FWHM from isolated field point sources (Moffat, same mosaic) ---
    fw=[]
    for (px,py) in PSFREF[f]:
        cu=Cutout2D(sci,(px,py),(31,31),mode="strict"); dd=cu.data.copy()
        ccx,ccy=cu.to_cutout_position((px,py))
        yy2,xx2=np.mgrid[:31,:31]; r2=np.hypot(xx2-ccx,yy2-ccy)*scale
        dd=dd-np.median(dd[(r2>1.2)&(r2<1.6)])
        m0=models.Moffat2D(amplitude=np.nanmax(dd),x_0=ccx,y_0=ccy,gamma=2.0,alpha=2.5)+models.Const2D(0.0)
        fit=fitting.LevMarLSQFitter()(m0,xx2,yy2,dd,maxiter=3000)
        fw.append(2*fit.gamma_0.value*np.sqrt(2**(1/fit.alpha_0.value)-1)*scale)
    fw=np.array(fw); psf_fwhm=np.median(fw)

    # --- contaminant peak (0.5-2.2" ring) as a starting guess ---
    ring=(rs>0.5)&(rs<2.2)
    iy,ix=np.unravel_index(np.argmax(np.where(ring,dz,-1e9)),dz.shape)
    g0=centroid_quadratic(dz,xpeak=ix,ypeak=iy,fit_boxsize=5)

    # --- simultaneous two-Moffat + constant fit on a 4" box about the pair midpoint ---
    mx,my=0.5*(cxs+g0[0]),0.5*(cys+g0[1])
    B=int(round(2.6/scale))
    sl=(slice(int(my)-B,int(my)+B+1),slice(int(mx)-B,int(mx)+B+1))
    sub=dz[sl]; esub=e[sl]; Y,X=np.mgrid[sl[0].start:sl[0].stop,sl[1].start:sl[1].stop]
    m=(models.Moffat2D(amplitude=max(dz[int(cys),int(cxs)],1e-3),x_0=cxs,y_0=cys,gamma=psf_fwhm/scale/2,alpha=2.5)
      +models.Moffat2D(amplitude=dz[int(g0[1]),int(g0[0])],x_0=g0[0],y_0=g0[1],gamma=psf_fwhm/scale/2,alpha=2.5)
      +models.Const2D(0.0))
    for p in ("x_0_0","y_0_0","x_0_1","y_0_1"): getattr(m,p).bounds=(getattr(m,p).value-4,getattr(m,p).value+4)
    if f=="f1500w":   # star undetectable -> hold it at the Gaia-propagated position
        m.x_0_0.fixed=True; m.y_0_0.fixed=True
    fit=fitting.LevMarLSQFitter()(m,X,Y,sub,weights=1.0/np.where(esub>0,esub,np.nan),maxiter=5000)
    def fwhm(g,a): return 2*g*np.sqrt(2**(1/a)-1)*scale
    def mflux(A,g,a): return A*np.pi*g**2/(a-1)          # Moffat analytic total flux (pix^2 units)
    sxy=(fit.x_0_0.value,fit.y_0_0.value); gxy=(fit.x_0_1.value,fit.y_0_1.value)
    fw_s=fwhm(abs(fit.gamma_0.value),fit.alpha_0.value); fw_g=fwhm(abs(fit.gamma_1.value),fit.alpha_1.value)
    Fs=mflux(fit.amplitude_0.value,abs(fit.gamma_0.value),fit.alpha_0.value)
    Fg=mflux(fit.amplitude_1.value,abs(fit.gamma_1.value),fit.alpha_1.value)
    sc_s=cut.wcs.pixel_to_world(*sxy); sc_g=cut.wcs.pixel_to_world(*gxy)
    sep=sc_s.separation(sc_g).arcsec; pa=sc_s.position_angle(sc_g).deg
    sep_gaia=cobs.separation(sc_g).arcsec; pa_gaia=cobs.position_angle(sc_g).deg
    print(f"\n{'='*74}\n{f}  scale={scale:.5f}\"/pix  refPSF FWHM={psf_fwhm:.3f}\" (N={len(fw)}, scatter {fw.std():.3f}\") | JDox {JDOX[f]}\"")
    print(f"  star  fit pix=({sxy[0]:.3f},{sxy[1]:.3f}) [Gaia ({cxs:.3f},{cys:.3f}), d={np.hypot(sxy[0]-cxs,sxy[1]-cys)*scale:.4f}\"]"
          f"  FWHM={fw_s:.3f}\"  amp={fit.amplitude_0.value:.3f}")
    print(f"  contam fit pix=({gxy[0]:.3f},{gxy[1]:.3f})  FWHM={fw_g:.3f}\"  amp={fit.amplitude_1.value:.3f}")
    print(f"  sep(fit star->contam)  = {sep:.4f}\"  PA={pa:.2f} deg")
    print(f"  sep(Gaia star->contam) = {sep_gaia:.4f}\"  PA={pa_gaia:.2f} deg")
    print(f"  Moffat flux ratio contam/star = {Fg/Fs:.4f}  -> dmag = {-2.5*np.log10(Fg/Fs):+.3f}")
    resid=sub-fit(X,Y); print(f"  fit resid: rms={np.std(resid):.3f} (sky rms {skyrms:.3f}), max|resid|/peak={np.max(np.abs(resid))/np.max(sub):.3f}")
    res[f]=dict(scale=scale,psf_fwhm=psf_fwhm,psf_fwhm_scatter=float(fw.std()),sxy=sxy,gxy=gxy,
                cxs=cxs,cys=cys,sep=sep,pa=pa,sep_gaia=sep_gaia,pa_gaia=pa_gaia,fw_s=fw_s,fw_g=fw_g,
                Fs=Fs,Fg=Fg,sky=sky,skyrms=skyrms,radii=radii.tolist(),apcorr=apcorr.tolist(),
                d=d,dz=dz,e=e,cut=cut,pixar_sr=fits.getheader(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits",1)["PIXAR_SR"],
                epoch=t.decimalyear, star_sky=(sc_s.ra.deg,sc_s.dec.deg), gal_sky=(sc_g.ra.deg,sc_g.dec.deg),
                gaia_sky=(cobs.ra.deg,cobs.dec.deg))
import pickle; pickle.dump({f:{k:v for k,v in res[f].items() if k!="cut"} for f in FILT},open(ROOT+"data/jwst/m4_fit.pkl","wb"))
print("\n--- separation / PA summary (Gaia-anchored, the robust anchor) ---")
for f in FILT: print(f"  {f}: sep={res[f]['sep_gaia']:.4f}\" PA={res[f]['pa_gaia']:.2f}")
s=np.array([res[f]['sep_gaia'] for f in FILT]); p=np.array([res[f]['pa_gaia'] for f in FILT])
print(f"  mean {s.mean():.4f}\" +- {s.std(ddof=1):.4f} (filter-to-filter);  PA {p.mean():.2f} +- {p.std(ddof=1):.2f} deg")
