"""M4: empirical-PSF simultaneous photometry of star + contaminant (photutils PSFPhotometry)."""
import sys, warnings, pickle; sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np
from astropy.io import fits, ascii
from astropy.wcs import WCS
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
from astropy.nddata import NDData, Cutout2D
from astropy.stats import sigma_clipped_stats
from photutils.psf import extract_stars, EPSFBuilder, PSFPhotometry, SourceGrouper, ImagePSF, EPSFStars

ROOT="c:/Users/matth/projects/astronomy/dyson-revet/"
RA16,DEC16,PMRA,PMDEC,PLX=351.96372836,5.10726195,-30.67371151,-21.61135431,4.69567256
c16=SkyCoord(ra=RA16*u.deg,dec=DEC16*u.deg,pm_ra_cosdec=PMRA*u.mas/u.yr,pm_dec=PMDEC*u.mas/u.yr,
             distance=(1000.0/PLX)*u.pc,obstime=Time("J2016.0"))
FILT=["f560w","f1000w","f1500w"]
out={}
for f in FILT:
    with fits.open(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_i2d.fits") as h:
        sci=h[1].data.astype(float); err=h[2].data.astype(float); w=WCS(h[1].header)
        scale=abs(h[1].header["CDELT1"])*3600.; t=Time(h[0].header["EXPSTART"],format="mjd")
    cat=ascii.read(ROOT+f"data/jwst/jw07199-o005_t007_miri_{f}_cat.ecsv")
    nn=np.asarray(cat["nn_dist"]); ft=np.asarray(cat["aper_total_flux"])
    ext=np.asarray(cat["is_extended"]); X=np.asarray(cat["xcentroid"]); Y=np.asarray(cat["ycentroid"])
    cobs=c16.apply_space_motion(new_obstime=t); xs,ys=[float(v) for v in w.world_to_pixel(cobs)]
    far=np.hypot(X-xs,Y-ys)>20
    ok=(~ext)&(nn>45)&(ft>0)&(X>60)&(X<1145)&(Y>60)&(Y<1095)&far&np.isfinite(ft)
    o=np.argsort(-np.where(ok,ft,-1))[:12]
    stars_tbl=Table({"x":X[o],"y":Y[o]})
    mean,med,std=sigma_clipped_stats(sci,sigma=3.)
    nd=NDData(data=sci-med)
    stars=extract_stars(nd,stars_tbl,size=41)
    keep=EPSFStars([s for s in stars if np.isfinite(s.data).all() and np.nanmax(s.data)>0])
    epsf,fitted=EPSFBuilder(oversampling=2,maxiters=12,progress_bar=False,smoothing_kernel="quadratic")(keep)
    ed=np.array(epsf.data); ed=ed/ed.sum()
    print(f"\n{'='*72}\n{f}: ePSF from {len(keep)} isolated field point sources (41 pix stamps, oversample 2)")
    # ePSF FWHM: azimuthal profile half-max radius on the oversampled grid
    oy,ox=np.unravel_index(np.argmax(ed),ed.shape)
    gy,gx=np.mgrid[:ed.shape[0],:ed.shape[1]]; rr=np.hypot(gx-ox,gy-oy)/2.0*scale
    order=np.argsort(rr.ravel()); rs=rr.ravel()[order]; vs=ed.ravel()[order]
    from numpy import interp
    nb=80; bb=np.linspace(0,2.0,nb+1); rc=.5*(bb[1:]+bb[:-1]); pr=np.array([np.median(vs[(rs>=bb[i])&(rs<bb[i+1])]) if ((rs>=bb[i])&(rs<bb[i+1])).sum()>2 else np.nan for i in range(nb)])
    pk=np.nanmax(pr); half=pk/2
    idx=np.where(pr<half)[0]; fwhm_epsf=2*np.interp(half,[pr[idx[0]],pr[idx[0]-1]],[rc[idx[0]],rc[idx[0]-1]]) if len(idx) else np.nan
    print(f"   ePSF FWHM (empirical, azimuthal) = {fwhm_epsf:.3f}\"   [JDox MIRI: f560w .207 f1000w .328 f1500w .488]")

    psfmod=ImagePSF(ed,flux=1.0,x_0=0,y_0=0,oversampling=2)
    # initial guesses: star at Gaia-propagated position, contaminant at its peak
    H=45; cu=Cutout2D(sci,(xs,ys),(91,91),wcs=w,mode="strict")
    dz=cu.data-med; cxs,cys=cu.to_cutout_position((xs,ys))
    yy,xx=np.mgrid[:91,:91]; rs2=np.hypot(xx-cxs,yy-cys)*scale
    ring=(rs2>.5)&(rs2<2.2); iy,ix=np.unravel_index(np.argmax(np.where(ring,dz,-1e9)),dz.shape)
    gx0,gy0=cu.to_original_position((ix,iy))
    init=Table({"x_init":[xs,gx0],"y_init":[ys,gy0],
                "flux_init":[float(np.nansum(sci[int(ys)-2:int(ys)+3,int(xs)-2:int(xs)+3]-med)),
                             float(np.nansum(sci[int(gy0)-2:int(gy0)+3,int(gx0)-2:int(gx0)+3]-med))]})
    ph=PSFPhotometry(psfmod,fit_shape=(11,11),grouper=SourceGrouper(min_separation=30),aperture_radius=4)
    r=ph(sci-med,error=err,init_params=init)
    r["_lab"]=["star","contam"]
    print(r["_lab","x_fit","y_fit","flux_fit","flux_err","qfit","cfit","flags"])
    sx,sy,gxf,gyf=r["x_fit"][0],r["y_fit"][0],r["x_fit"][1],r["y_fit"][1]
    scs=w.pixel_to_world(sx,sy); scg=w.pixel_to_world(gxf,gyf)
    print(f"   star fit pix ({sx:.3f},{sy:.3f}) vs Gaia ({xs:.3f},{ys:.3f}) -> d={np.hypot(sx-xs,sy-ys)*scale:.4f}\"")
    print(f"   sep(PSFfit)={scs.separation(scg).arcsec:.4f}\" PA={scs.position_angle(scg).deg:.2f}   "
          f"sep(Gaia-anchored)={cobs.separation(scg).arcsec:.4f}\" PA={cobs.position_angle(scg).deg:.2f}")
    fr=r["flux_fit"][1]/r["flux_fit"][0]
    print(f"   PSF flux ratio contam/star = {fr:.4f} -> dmag = {-2.5*np.log10(fr):+.3f}")
    out[f]=dict(epsf=ed,fwhm_epsf=fwhm_epsf,res={k:list(map(float,r[k])) for k in ("x_fit","y_fit","flux_fit","flux_err","qfit","cfit")},
                xs=xs,ys=ys,scale=scale,sep_fit=float(scs.separation(scg).arcsec),pa_fit=float(scs.position_angle(scg).deg),
                sep_gaia=float(cobs.separation(scg).arcsec),pa_gaia=float(cobs.position_angle(scg).deg),
                ratio=float(fr),med=float(med),nstars=int(keep.n_stars),
                star_sky=(scs.ra.deg,scs.dec.deg),gal_sky=(scg.ra.deg,scg.dec.deg),gaia_sky=(cobs.ra.deg,cobs.dec.deg),
                epoch=float(t.decimalyear))
pickle.dump(out,open(ROOT+"data/jwst/m4_epsf.pkl","wb"))
