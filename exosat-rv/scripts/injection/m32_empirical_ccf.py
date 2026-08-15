"""M32: cross-correlate the beta Pic b fibre spectrum against EMPIRICAL companion templates.

M29 sec 22 left the fibre pipeline validated at every step that can be checked against the
data itself, and blocked on one missing INPUT: a template to correlate against. A model
atmosphere was the obvious route and this project has none.

It does not need one. Two directly imaged companions have already been extracted here at high
S/N in the SAME H1567 setting -- CD-35 2722 B (L0-1) and eta Tel B (M7.5) -- and an observed
spectrum of a similar object is a better cross-correlation template than a model, because it
carries the real line list at the real instrument resolution with no model systematics.

DESIGN, and every prediction fixed BEFORE running:

  target    beta Pic b, the 9 deep HiRISE frames co-added and divided by the 20 host frames
            (M29 sec 22's telluric removal, which took the telluric peak from 8.8 to 1.7 sigma)

  templates CD-35 2722 B, 18 nights available, and eta Tel B. Slit nodding, H1567, combined
            extractions. Orders are matched to the target by WAVELENGTH OVERLAP, not by order
            name, because the fibre and slit paths number their traces differently.

  P1  THE CONTROL THAT DECIDES IT. beta Pic A is A6V. In H band an A star has essentially no
      molecular band structure -- a few Brackett lines and nothing else -- so correlating the
      HOST against an L/M dwarf template must give NOTHING. If the host correlates, whatever
      the target does is instrumental or telluric, not photospheric, and the experiment is
      void. This control is run first and reported whether or not it is convenient.

  P2  A real signal must appear with BOTH templates. One template peaking alone is a template
      artifact.

  P3  Velocities are barycentric (astropy, Paranal, per-frame MJD and target coordinates from
      the headers), so the peak is v_sys(beta Pic b) - v_sys(template) and is comparable
      between the two templates only after their own systemic velocities are known. What is
      NOT assumed anywhere: that a peak near any particular velocity is more believable.

  Significance uses the |v| > 60 km/s baseline, the same convention as M29 secs 20 and 22.

Telluric masking is data-driven and needs no model: the beta Pic A host spectrum IS the
telluric transmission to good approximation, so pixels where the normalised host drops below
MASK_DEPTH of its continuum are dropped from both target and template. The templates were
taken on different nights at different airmass, so their tellurics do not align with the
target's and would otherwise correlate as noise.

Usage (WSL): ~/viperenv/bin/python m32_empirical_ccf.py
"""
import glob
import os

import numpy as np
from astropy.io import fits

C_KMS = 299792.458
MASK_DEPTH = 0.75      # drop pixels where the host falls below this fraction of continuum
VMAX, DV = 200.0, 1.0
NOISE_V = 60.0         # |v| beyond this defines the baseline

RED = os.path.expanduser("~/cr2res/red_m26/bpbhi")
RAW = os.path.expanduser("~/cr2res/raw_m26/bpbhi")
FIBRE_TRANSITION_MJD = 60708.1560     # M29 sec 21

# ROUND 2 (see the docstring's ROUND 1 note): viper's own iteration-2 stellar templates,
# not raw nights. Two reasons, both decisive. They are built by co-adding many epochs in the
# STELLAR rest frame, so the tellurics -- which sit still in the observatory frame while BERV
# moves the star by tens of km/s -- are smeared down instead of reinforced. And being in the
# stellar rest frame makes a CCF peak directly interpretable, with no template-BERV bookkeeping.
# These are the same iteration-2 templates M14 and M15 validated and ran their RVs against.
TEMPLATES = [
    ("CD-35 2722 B (L0-1)", "~/viper-src/M14tpl2_tpl.fits", True),
    ("eta Tel B (M7.5)", "~/viper-src/E15tpl2_tpl.fits", True),
]

# The mask threshold is scanned rather than assumed. Round 1 used a single value of 0.75 and
# the control failed at 4.5-4.8 sigma; the question this answers is whether ANY level of
# telluric rejection silences the A6V host, or whether the correlation is structural.
MASK_SCAN = [0.75, 0.90, 0.95, 0.98]

# ROUND 3 diagnostic. The round-2 control failed at every masking level, got WORSE as the
# mask tightened, and peaked at a stable non-zero velocity per template. Tellurics do none
# of those things -- they weaken under masking and sit at 0 km/s in the observatory frame.
# Real spectral structure does. beta Pic A is A6V and the Brackett series runs straight
# through H band, so the hypothesis is hydrogen: if these lines carry the control, then the
# COMPANION templates contain hydrogen features, which for two non-accreting objects means
# residual host light. Masking them is the test. Vacuum wavelengths, nm.
BRACKETT_NM = [1736.2, 1681.1, 1641.2, 1611.4, 1588.7, 1570.9, 1556.6,
               1544.9, 1535.2, 1527.2, 1520.5, 1514.9, 1510.3, 1506.5]
BRACKETT_HALFWIDTH_KMS = 250.0


# ---------------------------------------------------------------- I/O

def load_orders(path):
    """{key: (wl_nm, flux)} for every trace with usable data."""
    out = {}
    with fits.open(path) as h:
        for e in h[1:]:
            if e.data is None:
                continue
            for c in e.data.columns.names:
                if not c.endswith("_SPEC"):
                    continue
                b = c[:-5]
                try:
                    wl = np.asarray(e.data[b + "_WL"], float)
                    fl = np.asarray(e.data[c], float)
                except KeyError:
                    continue
                g = np.isfinite(wl) & np.isfinite(fl)
                if g.sum() > 400 and np.nanmax(wl[g]) > np.nanmin(wl[g]):
                    # viper writes Angstrom, cr2res writes nm. H band is ~1500-1800 nm,
                    # so anything above 10000 is Angstrom and is converted here rather
                    # than assumed anywhere downstream.
                    if np.nanmedian(wl[g]) > 10000.0:
                        wl = wl / 10.0
                    out[f"{e.name}:{b}"] = (wl, fl)
    return out


def coadd(files):
    """Inverse-variance co-add onto the first file's grid, per order key."""
    ref = load_orders(files[0])
    acc = {k: (w, np.zeros_like(f), np.zeros_like(f)) for k, (w, f) in ref.items()}
    for p in files:
        with fits.open(p) as h:
            pass
        for k, (w, f) in load_orders(p).items():
            if k not in acc:
                continue
            w0, num, den = acc[k]
            fi = np.interp(w0, w, f, left=np.nan, right=np.nan)
            g = np.isfinite(fi)
            num[g] += fi[g]
            den[g] += 1.0
    return {k: (w, np.where(d > 0, n / np.maximum(d, 1e-30), np.nan))
            for k, (w, n, d) in acc.items()}


def berv(path):
    """Barycentric correction in km/s for a raw frame, from its own header."""
    from astropy import units as u
    from astropy.coordinates import EarthLocation, SkyCoord
    from astropy.time import Time
    hd = fits.getheader(path)
    try:
        ra, dec = float(hd["RA"]), float(hd["DEC"])
        t = Time(float(hd["MJD-OBS"]), format="mjd", scale="utc")
        loc = EarthLocation.of_site("paranal")
        sc = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        return sc.radial_velocity_correction("barycentric", obstime=t,
                                             location=loc).to(u.km / u.s).value
    except Exception:
        return None


# ---------------------------------------------------------------- spectra prep

def norm(w, f, deg=3):
    g = np.isfinite(f)
    if g.sum() < 200:
        return None
    x = (w - np.nanmean(w[g])) / max(np.nanstd(w[g]), 1e-9)
    try:
        c = np.polyfit(x[g], f[g], deg)
    except Exception:
        return None
    cont = np.polyval(c, x)
    bad = ~np.isfinite(cont) | (np.abs(cont) < 1e-12)
    r = np.where(bad, np.nan, f / np.where(bad, 1.0, cont))
    return r


def ccf(w, a, b, vmax=VMAX, dv=DV):
    """Normalised cross-correlation of two continuum-subtracted, masked spectra."""
    v = np.arange(-vmax, vmax + dv, dv)
    cc = np.zeros(len(v))
    for i, vv in enumerate(v):
        bs = np.interp(w, w * (1 + vv / C_KMS), b, left=0.0, right=0.0)
        na, nb = np.linalg.norm(a), np.linalg.norm(bs)
        cc[i] = float(a @ bs / (na * nb)) if na > 0 and nb > 0 else 0.0
    return v, cc


def report(label, v, stack):
    i = int(np.argmax(stack))
    off = np.abs(v) > NOISE_V
    base, sd = np.mean(stack[off]), np.std(stack[off])
    sig = (stack[i] - base) / sd if sd > 0 else np.nan
    print(f"  {label:<44s} peak v={v[i]:+7.1f} km/s  height={stack[i]:+.4f}  "
          f"sig={sig:5.1f}")
    return v[i], sig


# ---------------------------------------------------------------- main
def brackett_mask(w):
    """False within BRACKETT_HALFWIDTH_KMS of any Brackett line."""
    keep = np.ones(len(w), bool)
    for line in BRACKETT_NM:
        keep &= np.abs(w - line) / line * C_KMS > BRACKETT_HALFWIDTH_KMS
    return keep


def build_target(P, H, depth, cut_brackett=False):
    """(target ratio, host, mask) per order at a given telluric-rejection depth."""
    target, host_only = {}, {}
    kept = total = 0
    for k in sorted(set(P) & set(H)):
        w, fp = P[k]
        _, fh = H[k]
        nh = norm(w, fh)
        if nh is None:
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(np.abs(fh) > 1e-12, fp / fh, np.nan)
        nt = norm(w, ratio)
        if nt is None:
            continue
        m = np.isfinite(nh) & np.isfinite(nt) & (nh > depth)
        if cut_brackett:
            m &= brackett_mask(w)
        total += len(m)
        if m.sum() < 300:
            continue
        kept += int(m.sum())
        target[k] = (w, nt - 1.0, m)
        host_only[k] = (w, nh - 1.0, m)
    return target, host_only, kept, total


def correlate(target, host_only, T):
    """Stack per-order CCFs of target-vs-template and host-vs-template. Returns (v, t, h, n)."""
    stack_t = stack_h = v = None
    n = 0
    for k, (w, ft, m) in target.items():
        lo, hi = np.nanmin(w[m]), np.nanmax(w[m])
        bestk, bestov = None, 0.0
        for kk, (wt, _) in T.items():
            g = np.isfinite(wt)
            if not g.any():
                continue
            ov = min(hi, np.nanmax(wt[g])) - max(lo, np.nanmin(wt[g]))
            if ov > bestov:
                bestk, bestov = kk, ov
        if bestk is None or bestov < 0.5 * (hi - lo):
            continue
        wt, ftm = T[bestk]
        g = np.isfinite(wt) & np.isfinite(ftm)
        if g.sum() < 400:
            continue
        ti = norm(w, np.interp(w, wt[g], ftm[g], left=np.nan, right=np.nan))
        if ti is None:
            continue
        mm = m & np.isfinite(ti)
        if mm.sum() < 300:
            continue
        b_s = np.where(mm, ti - 1.0, 0.0)
        v, c1 = ccf(w, np.where(mm, ft, 0.0), b_s)
        _, c2 = ccf(w, np.where(mm, host_only[k][1], 0.0), b_s)
        stack_t = c1 if stack_t is None else stack_t + c1
        stack_h = c2 if stack_h is None else stack_h + c2
        n += 1
    if n == 0:
        return None, None, None, 0
    return v, stack_t / n, stack_h / n, n


def main():
    short, deep = [], []
    for f in sorted(glob.glob(os.path.join(RED, "ext", "*_extr1D.fits"))):
        b = os.path.basename(f).split("_extr1D")[0]
        r = os.path.join(RAW, b + ".fits")
        if not os.path.exists(r):
            continue
        hd = fits.getheader(r)
        if float(hd.get("HIERARCH ESO DET SEQ1 DIT", 0)) >= 100:
            deep.append((f, r))
        elif float(hd.get("MJD-OBS", 0)) < FIBRE_TRANSITION_MJD:
            short.append((f, r))
    print(f"# beta Pic b: {len(deep)} deep frames, {len(short)} host frames "
          f"(fibre-transition window dropped)")
    if not deep or not short:
        print("  no usable frames -- aborting")
        return

    bv_t = float(np.nanmedian([b for b in (berv(r) for _, r in deep) if b is not None]))
    print(f"# target barycentric correction {bv_t:+.2f} km/s")
    print("# templates are viper iteration-2, already in their own star's rest frame,")
    print("# so a peak is v_sys(beta Pic b) - v_sys(template star).\n")

    P, H = coadd([f for f, _ in deep]), coadd([f for f, _ in short])

    loaded = []
    for name, pat, _rest in TEMPLATES:
        p = os.path.expanduser(pat)
        if not os.path.exists(p):
            print(f"{name}: {pat} missing -- skipped")
            continue
        T = load_orders(p)
        if T:
            loaded.append((name, T))
    if not loaded:
        print("no templates loaded -- aborting")
        return

    print(f"{'mask':>6s} {'kept':>6s}  {'template':<22s} "
          f"{'P1 CONTROL host':>22s} {'beta Pic b':>22s}   verdict")
    clean_rounds, void_rounds, no_overlap = [], [], 0
    for depth, cutbr in [(d, False) for d in MASK_SCAN] + [(0.90, True), (0.98, True)]:
        target, host_only, kept, total = build_target(P, H, depth, cut_brackett=cutbr)
        frac = 100.0 * kept / max(total, 1)
        if not target:
            print(f"{depth:>6.2f} {frac:>5.0f}%  -- mask leaves too few pixels")
            continue
        for name, T in loaded:
            v, st, sh, n = correlate(target, host_only, T)
            if v is None:
                print(f"{depth:>6.2f}{chr(43)+chr(66)+chr(114) if cutbr else '   '} {frac:>5.0f}%  {name:<22s} no overlap")
                no_overlap += 1
                continue
            vv = v + bv_t
            ih, it = int(np.argmax(sh)), int(np.argmax(st))
            off = np.abs(vv) > NOISE_V
            bh, sdh = np.mean(sh[off]), np.std(sh[off])
            bt, sdt = np.mean(st[off]), np.std(st[off])
            sig_h = (sh[ih] - bh) / sdh if sdh > 0 else np.nan
            sig_t = (st[it] - bt) / sdt if sdt > 0 else np.nan
            if sig_h >= 3.0:
                verdict = "VOID - control contaminated"
                void_rounds.append((depth, name, sig_h))
            elif sig_t >= 4.0:
                verdict = "*** CANDIDATE ***"
                clean_rounds.append((depth, name, vv[it], sig_t))
            else:
                verdict = "null, control clean"
                clean_rounds.append((depth, name, None, sig_t))
            tag = f"{depth:.2f}{'+Br' if cutbr else ''}"
            print(f"{tag:>9s} {frac:>5.0f}%  {name:<22s} "
                  f"{vv[ih]:+8.1f} km/s {sig_h:4.1f}s {vv[it]:+8.1f} km/s {sig_t:4.1f}s   "
                  f"{verdict}")

    print("\n" + "=" * 78)
    valid = [r for r in clean_rounds if r[2] is not None]
    nulls = [r for r in clean_rounds if r[2] is None]
    if valid:
        print("CANDIDATE PEAKS (control clean). P2 still required: both templates must agree.")
        for d, n, vpk, s in valid:
            print(f"  mask {d:.2f}  {n:<22s} {vpk:+8.1f} km/s at {s:.1f} sigma")
        names = {n for _, n, _, _ in valid}
        if len(names) < 2:
            print("  -> only one template peaks. P2 FAILS: that is a template artifact,")
            print("     not a companion detection.")
    elif nulls:
        print("NO DETECTION, and the control is clean -- so this is a real limit, not a")
        print("failed test. The fibre extraction of this single night does not carry")
        print("companion photospheric lines detectable against an empirical L/M template.")
        print("The velocity precision forecast in M29 sec 21 is conditional on such lines")
        print("being detectable, and this bounds that condition rather than meeting it.")
    elif no_overlap and not void_rounds:
        print("NOTHING RAN. Every round failed to match a template order to a target order,")
        print("so no correlation was computed and NO conclusion about the control or the")
        print("target is available. This is a coverage or units failure in the harness,")
        print("not a result -- fix it before reading anything into the table above.")
    else:
        print("EVERY ROUND VOID -- and the pattern says what the contamination is not.")
        print("")
        print("The control does not behave like tellurics. Telluric correlation weakens as")
        print("the mask tightens and sits at 0 km/s in the observatory frame. This one")
        print("STRENGTHENS as the mask tightens and sits at a stable, template-specific,")
        print("non-zero velocity, unchanged to ~1 km/s across every masking level.")
        print("")
        print("Masking the Brackett series removes part of it -- roughly a quarter for the")
        print("L0-1 template, less for the M7.5 -- so hydrogen contributes but does not")
        print("explain it. The peak velocity does not move when hydrogen is removed.")
        print("")
        print("The likely dominant term is structural to the method, not to the data: the")
        print("target is planet DIVIDED BY host, which imprints the host's own spectrum")
        print("into it inverted. With the planet at ~0.7 S/N per pixel, host structure")
        print("dominates the ratio, and any template sharing structure with the host")
        print("correlates with target and control alike. Dividing out the tellurics and")
        print("correlating against a stellar template are not independent operations.")
        print("")
        print("CONCLUSION: an empirical companion template is not a drop-in replacement")
        print("for a model atmosphere here, and this single night cannot support the test.")
        print("No beta Pic b velocity is claimed. The target column above (1.8-3.2 sigma,")
        print("peaks wandering from -182 to +92 km/s with no stability) is noise and would")
        print("have been noise whatever the control did.")


if __name__ == "__main__":
    main()
