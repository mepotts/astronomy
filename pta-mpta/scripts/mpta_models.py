#!/usr/bin/env python3
"""MPTA per-pulsar noise models for the M2 top-10 campaign.

Favoured models and published MAP/68% CI values transcribed from
arXiv:2412.01148 (Miles et al. 2025), Tables "MPTA noise models" and
"MPTA determinstic models" [sic] (LaTeX source retrieved 2026-08-16).
Model conventions and priors: pta-mpta/M2-converge-scale.md section 1.2
(pre-registered). M1-validated conventions carried unchanged from
scripts/w2_noise_run.py.

Solar-wind classes per the paper: "full" = deterministic n_earth + SW GP,
"det" = n_earth only, "fixed" = n_earth held at 4 cm^-3 (tempo2 default).
"""
import numpy as np

NCOMP = 120  # paper: "We thus chose 120 components"

# --- published values: key -> (MAP, lo_offset, hi_offset) as printed ---
PUBLISHED = {
    "J1713+0747": {
        "efac": (1.07, -0.02, +0.02),
        "log10_ecorr": (-6.86, -0.09, +0.05),
        "chrom_log10_A": (-14.69, -3.36, +0.18),
        "chrom_gamma": (0.60, -0.26, +3.66),
        "gw13_log10_A": (-16.59, -0.57, +2.55),
    },
    "J2241-5236": {
        "efac": (1.05, -0.01, +0.01),
        "sw_log10_A": (-6.16, -0.10, +0.06),
        "sw_gamma": (1.81, -0.30, +0.18),
        "gw13_log10_A": (-14.82, -1.57, +0.28),
        "n_earth": (5.86, -2.32, +1.59),
    },
    "J0437-4715": {
        "efac": (1.20, -0.01, +0.02),
        "log10_ecorr": (-6.68, -0.04, +0.02),
        "dm_log10_A": (-13.51, -0.06, +0.07),
        "dm_gamma": (1.11, -0.12, +0.19),
        "chrom_log10_A": (-15.55, -0.28, +0.24),
        "chrom_gamma": (0.41, -0.27, +0.19),
        "chrom_beta": (7.95, -0.67, +1.41),
        "gw13_log10_A": (-15.86, -1.62, +0.70),
    },
    "J1909-3744": {
        "efac": (1.04, -0.02, +0.00),
        "log10_tnequad": (-7.17, -0.03, -0.00),
        "log10_ecorr": (-7.17, -0.06, +0.02),
        "dm_log10_A": (-13.60, -0.07, +0.07),
        "dm_gamma": (2.04, -0.18, +0.28),
        "sw_log10_A": (-6.43, -0.19, +0.10),
        "sw_gamma": (1.39, -0.42, +0.21),
        "gw13_log10_A": (-14.28, -0.21, +0.17),
        "n_earth": (4.96, -1.24, +0.86),
    },
    "J1744-1134": {
        "efac": (1.03, -0.01, +0.02),
        "log10_tnequad": (-7.04, -0.04, +0.05),
        "log10_ecorr": (-6.59, -0.06, +0.03),
        "sw_log10_A": (-6.43, -0.37, +0.15),
        "sw_gamma": (0.91, -0.81, +0.66),
        "gw13_log10_A": (-16.18, -1.24, +1.18),
        "n_earth": (3.73, -1.10, +1.09),
    },
    "J0125-2327": {
        "efac": (1.04, -0.02, +0.01),
        "log10_tnequad": (-6.99, -1.84, +0.03),
        "log10_ecorr": (-6.77, -0.10, +0.05),
        "dm_log10_A": (-13.42, -0.30, +0.06),
        "dm_gamma": (2.72, -0.42, +1.45),
        "gw13_log10_A": (-14.96, -2.39, +0.36),
    },
    "J1946-5403": {
        "efac": (0.97, -0.02, +0.02),
        "gw13_log10_A": (-14.46, -2.76, +0.05),
    },
    "J1600-3053": {
        "efac": (1.01, -0.01, +0.03),
        "log10_tnequad": (-6.81, -0.30, +0.06),
        "dm_log10_A": (-13.10, -0.06, +0.10),
        "dm_gamma": (1.81, -0.21, +0.27),
        "chrom_log10_A": (-13.51, -0.19, +0.08),
        "chrom_gamma": (1.57, -0.44, +0.30),
        "gw13_log10_A": (-13.51, -2.53, +0.20),
        "n_earth": (2.72, -0.99, +1.42),
        "bump_log10_A": (-6.13, -1.01, +0.55),
        "bump_beta": (4.17, -1.02, +2.54),
        "bump_t0": (58738.82, -116.58, +222.06),
        "bump_sigma": (937.13, -258.68, +382.94),
    },
    "J1017-7156": {
        "efac": (1.10, -0.01, +0.03),
        "log10_tnequad": (-6.86, -0.11, +0.05),
        "log10_ecorr": (-6.68, -1.42, +0.04),
        "red_log10_A": (-13.28, -4.57, +0.03),
        "red_gamma": (1.31, -0.08, +4.56),
        "chrom_log10_A": (-13.42, -0.20, +0.26),
        "chrom_gamma": (1.57, -0.30, +0.20),
        "chrom_beta": (3.85, -0.99, +0.43),
        "sw_log10_A": (-5.27, -2.59, +0.04),
        "sw_gamma": (2.20, -0.88, +0.58),
        "gw13_log10_A": (-15.77, -1.37, +1.30),
        "n_earth": (8.70, -5.95, +6.27),
        "bump_log10_A": (-7.68, -0.63, +0.88),
        "bump_beta": (8.95, -3.32, +1.85),
        "bump_t0": (59381.10, -302.77, +385.29),
        "bump_sigma": (1244.40, -407.19, +224.27),
    },
    "J2129-5721": {
        "efac": (1.03, -0.01, +0.02),
        "chrom_log10_A": (-14.01, -0.31, +0.06),
        "chrom_gamma": (1.01, -0.45, +0.62),
        "gw13_log10_A": (-13.83, -0.21, +0.16),
        "n_earth": (1.28, -0.47, +4.87),
        "ann_log10_A": (-6.68, -9.40, +0.13),
        "ann_beta": (2.35, -1.13, +7.53),
        "ann_phase": (4.56, -2.71, +0.53),
    },
}

# --- favoured model configuration per pulsar (same tables) ---
# chrom: None | "fixed4" | "free"; sw: "full" | "det" | "fixed";
# bump: None | +1 | -1 (sign column); annual: bool; red: free achromatic red.
MODELS = {
    "J1713+0747": dict(equad=False, ecorr=True, dm=False, red=False,
                       chrom="fixed4", sw="fixed", bump=None, annual=False),
    "J2241-5236": dict(equad=False, ecorr=False, dm=False, red=False,
                       chrom=None, sw="full", bump=None, annual=False),
    "J0437-4715": dict(equad=False, ecorr=True, dm=True, red=False,
                       chrom="free", sw="fixed", bump=None, annual=False),
    "J1909-3744": dict(equad=True, ecorr=True, dm=True, red=False,
                       chrom=None, sw="full", bump=None, annual=False),
    "J1744-1134": dict(equad=True, ecorr=True, dm=False, red=False,
                       chrom=None, sw="full", bump=None, annual=False),
    "J0125-2327": dict(equad=True, ecorr=True, dm=True, red=False,
                       chrom=None, sw="fixed", bump=None, annual=False),
    "J1946-5403": dict(equad=False, ecorr=False, dm=False, red=False,
                       chrom=None, sw="fixed", bump=None, annual=False),
    "J1600-3053": dict(equad=True, ecorr=False, dm=True, red=False,
                       chrom="fixed4", sw="det", bump=+1, annual=False),
    "J1017-7156": dict(equad=True, ecorr=True, dm=False, red=True,
                       chrom="free", sw="full", bump=+1, annual=False),
    "J2129-5721": dict(equad=False, ecorr=False, dm=False, red=False,
                       chrom="fixed4", sw="det", bump=None, annual=True),
}

TOP10 = ["J1713+0747", "J2241-5236", "J0437-4715", "J1909-3744",
         "J1744-1134", "J0125-2327", "J1946-5403", "J1600-3053",
         "J1017-7156", "J2129-5721"]

# enterprise param-name suffix -> published-table key
SUFFIX_TO_KEY = {
    "efac": "efac",
    "log10_tnequad": "log10_tnequad",
    "log10_ecorr": "log10_ecorr",
    "red_gp_log10_A": "red_log10_A",
    "red_gp_gamma": "red_gamma",
    "dm_gp_log10_A": "dm_log10_A",
    "dm_gp_gamma": "dm_gamma",
    "chrom_gp_log10_A": "chrom_log10_A",
    "chrom_gp_gamma": "chrom_gamma",
    "chrom_gp_idx": "chrom_beta",
    "sw_gp_log10_A": "sw_log10_A",
    "sw_gp_gamma": "sw_gamma",
    "gw13_log10_A": "gw13_log10_A",
    "n_earth": "n_earth",
    "bump_log10_Amp": "bump_log10_A",
    "bump_beta_g": "bump_beta",
    "bump_t0": "bump_t0",
    "bump_sigma_g": "bump_sigma",
    "annual_log10_Amp": "ann_log10_A",
    "annual_idx": "ann_beta",
    "annual_phase": "ann_phase",
}


def map_param(name, psrname):
    """Full enterprise parameter name -> published-table key (or None)."""
    suffix = name.replace(f"{psrname}_", "")
    return SUFFIX_TO_KEY.get(suffix)


def stability_tol(name, psrname, tspan_days):
    """Pre-registered last-half vs full-chain median stability tolerance."""
    s = name.replace(f"{psrname}_", "")
    if s in ("bump_t0",):
        return 0.1 * tspan_days          # 0.1 x prior width (t0 ~ ToA span)
    if s in ("bump_sigma_g",):
        return 0.1 * (2000.0 - 10.0)
    if s in ("annual_phase",):
        return 0.1 * 2.0 * np.pi
    if ("gamma" in s) or s.endswith("_idx") or s in ("n_earth", "bump_beta_g"):
        return 0.3
    return 0.1                            # log10 amplitudes, EFAC


def build_pta(psrname, tdbdir, partim, fl=False, whites=None):
    """Build the favoured-model PTA for one pulsar.

    fl=False: the noise-campaign model (everything sampled).
    fl=True : the factorised-likelihood CURN model — whites FIXED at the
              values in `whites` (dict key->value from our own campaign),
              a free achromatic red process ADDED where the favoured model
              lacks one (paper section 'Search for common processes'), and
              the fixed-gamma=13/3 term acting as the CURN amplitude.
    """
    import pint.logging
    pint.logging.setup(level="WARNING")
    from enterprise.pulsar import Pulsar
    from enterprise.signals import (deterministic_signals, gp_signals,
                                    parameter, signal_base, utils,
                                    white_signals)
    from enterprise.signals import gp_bases
    from enterprise_extensions.chromatic import solar_wind as sw_mod
    from enterprise_extensions.chromatic import chromatic as chrom_mod

    cfg = MODELS[psrname]
    par = f"{tdbdir}/{psrname}.tdb.par"
    tim = f"{partim}/{psrname}.tim"
    psr = Pulsar(par, tim, ephem="DE440", timing_package="pint")
    Tspan = psr.toas.max() - psr.toas.min()
    tspan_days = Tspan / 86400.0
    tmin_mjd = psr.toas.min() / 86400.0
    tmax_mjd = psr.toas.max() / 86400.0

    def W(key, lo, hi):
        """White-noise parameter: sampled, or fixed for FL runs."""
        if fl:
            return parameter.Constant(whites[key])
        return parameter.Uniform(lo, hi)

    # --- white noise ---
    model = white_signals.MeasurementNoise(efac=W("efac", 0.1, 5.0))
    if cfg["equad"]:
        model += white_signals.TNEquadNoise(
            log10_tnequad=W("log10_tnequad", -10, -5))
    if cfg["ecorr"]:
        model += white_signals.EcorrKernelNoise(
            log10_ecorr=W("log10_ecorr", -10, -5))

    # --- achromatic red (favoured-model, or added for FL per the paper) ---
    if cfg["red"] or fl:
        red_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                   gamma=parameter.Uniform(0, 7))
        model += gp_signals.FourierBasisGP(red_prior, components=NCOMP,
                                           Tspan=Tspan, name="red_gp")

    # --- DM GP (120 components, 1400 MHz DM basis) ---
    if cfg["dm"]:
        dm_basis = utils.createfourierdesignmatrix_dm(nmodes=NCOMP,
                                                      Tspan=Tspan)
        dm_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                  gamma=parameter.Uniform(0, 7))
        model += gp_signals.BasisGP(dm_prior, dm_basis, name="dm_gp")

    # --- chromatic (scattering) GP: delay basis (1400/nu)^beta ---
    if cfg["chrom"]:
        idx = 4.0 if cfg["chrom"] == "fixed4" else parameter.Uniform(0, 14)
        ch_basis = gp_bases.createfourierdesignmatrix_chromatic(
            nmodes=NCOMP, Tspan=Tspan, idx=idx)
        ch_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                  gamma=parameter.Uniform(0, 7))
        ch_cls = gp_signals.BasisGP(ch_prior, ch_basis, name="chrom_gp",
                                    combine=(cfg["chrom"] == "fixed4"))
        if cfg["chrom"] == "free":
            # enterprise 3.5.0 bug (measured, M2 doc 2.1): when only a BASIS
            # parameter (beta) changes, _construct_basis re-runs and zeroes
            # self._phi, but _construct_prior is cached on prior_params only
            # and never refills it -> phi block = 0 -> phiinv = inf ->
            # cho_factor crash on every single-parameter beta jump. Fix: key
            # the prior fill on basis params too (body verbatim otherwise).
            # combine=False also prevents a mid-run basis merge with the DM
            # block when beta samples through exactly 2.0.
            # limit=1 is load-bearing: _construct_prior has SIDE EFFECTS
            # (it refills self._phi), and with the default depth-2 cache a
            # rejected-jump revisit pattern (idx A -> B -> A at unchanged
            # amplitude/gamma) hits the stale cache entry after
            # _construct_basis zeroed phi, skipping the refill -> inf again
            # (measured: this exact pattern crashed the first relaunch).
            class ChromBasisGP(ch_cls):
                @signal_base.cache_call(["prior_params", "basis_params"],
                                        limit=1)
                def _construct_prior(self, params):
                    for key, slc in self._slices.items():
                        phislc = self._prior[key](self._labels[key],
                                                  params=params)
                        self._phi = self._phi.set(phislc, slc)

            ch_cls = ChromBasisGP
        model += ch_cls

    # --- solar wind (Hazboun-style; M1-validated conventions) ---
    if cfg["sw"] == "fixed":
        model += deterministic_signals.Deterministic(
            sw_mod.solar_wind(n_earth=4.0), name="sw_det")
    else:
        n_earth = parameter.Uniform(0, 30)("n_earth")
        model += deterministic_signals.Deterministic(
            sw_mod.solar_wind(n_earth=n_earth), name="sw_det")
        if cfg["sw"] == "full":
            sw_basis = sw_mod.createfourierdesignmatrix_solar_dm(
                nmodes=NCOMP, Tspan=Tspan, logf=False)
            sw_prior = utils.powerlaw(log10_A=parameter.Uniform(-10, 1),
                                      gamma=parameter.Uniform(0, 7))
            model += gp_signals.BasisGP(sw_prior, sw_basis, name="sw_gp")

    # --- chromatic Gaussian event (paper Eq.; e_e 3.0.3 ships none) ---
    if cfg["bump"] is not None:
        @signal_base.function
        def chrom_gaussian_bump(toas, freqs, log10_Amp=-7.0, t0=59000.0,
                                sigma_g=500.0, beta_g=4.0, sign=1.0):
            t0_s = t0 * 86400.0
            sg_s = sigma_g * 86400.0
            wf = 10 ** log10_Amp * np.exp(-((toas - t0_s) ** 2)
                                          / (2.0 * sg_s ** 2))
            return np.sign(sign) * wf * (1400.0 / freqs) ** beta_g

        bump_wf = chrom_gaussian_bump(
            log10_Amp=parameter.Uniform(-10, -4),
            t0=parameter.Uniform(tmin_mjd, tmax_mjd),
            sigma_g=parameter.Uniform(10, 2000),
            beta_g=parameter.Uniform(0, 14),
            sign=float(cfg["bump"]))
        model += deterministic_signals.Deterministic(bump_wf, name="bump")

    # --- annual chromatic variation (e_e waveform) ---
    if cfg["annual"]:
        ann_wf = chrom_mod.chrom_yearly_sinusoid(
            log10_Amp=parameter.Uniform(-18, -4),
            phase=parameter.Uniform(0, 2 * np.pi),
            idx=parameter.Uniform(0, 14))
        model += deterministic_signals.Deterministic(ann_wf, name="annual")

    # --- fixed-index gamma=13/3 achromatic term (A_13/3; CURN slice in FL) ---
    gw13 = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                          gamma=parameter.Constant(13.0 / 3.0))
    model += gp_signals.FourierBasisGP(gw13, components=NCOMP, Tspan=Tspan,
                                       name="gw13")

    model += gp_signals.TimingModel(use_svd=True)
    pta = signal_base.PTA([model(psr)])
    meta = dict(psr=psrname, ntoa=len(psr.toas), tspan_days=tspan_days,
                tmin_mjd=tmin_mjd, tmax_mjd=tmax_mjd, fl=bool(fl))
    return pta, meta


def published_vector(pta, psrname):
    """Published MAP values ordered like pta.param_names (None if any
    sampled parameter has no published value)."""
    pub = PUBLISHED[psrname]
    x = []
    for name in pta.param_names:
        key = map_param(name, psrname)
        if key is None or key not in pub:
            return None, name
        x.append(pub[key][0])
    return np.array(x), None


def a2_compare(pta, psrname, post):
    """Pre-registered A2 rule per parameter; returns rows + counts."""
    pub = PUBLISHED[psrname]
    rows, n_agree, n_comp = [], 0, 0
    for i, name in enumerate(pta.param_names):
        key = map_param(name, psrname)
        med = float(np.median(post[:, i]))
        lo, hi = (float(np.percentile(post[:, i], q)) for q in (16, 84))
        row = dict(param=name, key=key, median=med, ci68=[lo, hi])
        if key and key in pub:
            pmap, plo, phi = pub[key]
            agree = (lo <= pmap <= hi) or (pmap + plo <= med <= pmap + phi)
            row.update(published_map=pmap,
                       published_ci=[pmap + plo, pmap + phi],
                       agree=bool(agree))
            n_comp += 1
            n_agree += int(agree)
        rows.append(row)
    return rows, n_agree, n_comp
