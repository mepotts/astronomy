#!/usr/bin/env python3
"""M3: MPTA per-pulsar noise models for all 83 released pulsars.

Model configuration and published MAP/68% CI values come from
results/m3/published_table.json, machine-parsed by scripts/m3_parse_tables.py
from the arXiv:2412.01148 LaTeX source. That parser is validated against M2's
independent hand transcription of ten pulsars (0 mismatches, values AND model
inference) — see M3-noise-criticism.md section 2.

Conventions are M2's, unchanged (M2 doc section 1.2), including the enterprise
3.5.0 varying-basis phi-cache fix for free-beta chromatic GPs.

Three model VARIANTS (pre-registered, M3 doc section 1):
  "noise" — the favoured model exactly as tabulated; everything sampled.
            This is what the published noise table reports.
  "table" — the favoured model, white noise FIXED at our own `noise`-campaign
            medians. The seam-(b) CONTROL: same model as the table, cheap
            evals, so the only difference from "fl" is the added red process.
  "fl"    — the favoured model PLUS a free achromatic red process where the
            favoured model lacks one, white noise fixed as in "table".
            This is the collaboration's own common-signal configuration
            (paper sections 'Search for common processes' / 'Common signals':
            "achromatic red noise processes were included for pulsars, even if
            they did not have this term in their noise models").
"""
import json
from pathlib import Path

import numpy as np

NCOMP = 120  # paper: "We thus chose 120 components"

REPO = Path(__file__).resolve().parent.parent
TABLE_PATH = REPO / "results" / "m3" / "published_table.json"

_T = json.loads(TABLE_PATH.read_text())
PUBLISHED = {p: r["pub"] for p, r in _T.items()}
MODELS = {p: r["model"] for p, r in _T.items()}
NSAMPLED = {p: r["n_sampled"] for p, r in _T.items()}
CURN_SOURCED = {p: r["curn_sourced"] for p, r in _T.items()}
ALL83 = sorted(_T)

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

# pre-registered prior ranges (M2 doc 1.2; UNSOURCED — the paper tabulates none)
PRIORS = dict(
    efac=(0.1, 5.0), log10_tnequad=(-10, -5), log10_ecorr=(-10, -5),
    red_log10_A=(-18, -11), red_gamma=(0, 7),
    dm_log10_A=(-18, -11), dm_gamma=(0, 7),
    chrom_log10_A=(-18, -11), chrom_gamma=(0, 7), chrom_beta=(0, 14),
    sw_log10_A=(-10, 1), sw_gamma=(0, 7), n_earth=(0, 30),
    gw13_log10_A=(-18, -11),
    bump_log10_A=(-10, -4), bump_beta=(0, 14), bump_sigma=(10, 2000),
    ann_log10_A=(-18, -4), ann_beta=(0, 14), ann_phase=(0, 2 * np.pi),
)


def map_param(name, psrname):
    return SUFFIX_TO_KEY.get(name.replace(f"{psrname}_", ""))


def stability_tol(name, psrname, tspan_days):
    s = name.replace(f"{psrname}_", "")
    if s == "bump_t0":
        return 0.1 * tspan_days
    if s == "bump_sigma_g":
        return 0.1 * (2000.0 - 10.0)
    if s == "annual_phase":
        return 0.1 * 2.0 * np.pi
    if ("gamma" in s) or s.endswith("_idx") or s in ("n_earth", "bump_beta_g"):
        return 0.3
    return 0.1


def build_pta(psrname, tdbdir, partim, variant="noise", whites=None,
              sw_gamma_prior=None):
    """Build one pulsar's PTA for the given variant (see module docstring).

    sw_gamma_prior: (lo, hi) override for the solar-wind GP spectral index.
    Default None = the pre-registered M2 prior U(0, 7). Used ONLY by the
    declared post-hoc supplementary check of M3 section 6: 7 of the 26
    tabulated gamma_SW values are NEGATIVE and therefore unreachable under
    U(0, 7), while enterprise_extensions' own solar_wind_block default is
    U(-2, 1) -- so the blanket gamma prior M1 declared is the wrong one for
    this signal and cannot reproduce those rows by construction."""
    import pint.logging
    pint.logging.setup(level="ERROR")
    from enterprise.pulsar import Pulsar
    from enterprise.signals import (deterministic_signals, gp_signals,
                                    parameter, signal_base, utils,
                                    white_signals)
    from enterprise.signals import gp_bases
    from enterprise_extensions.chromatic import solar_wind as sw_mod
    from enterprise_extensions.chromatic import chromatic as chrom_mod

    assert variant in ("noise", "table", "fl")
    cfg = MODELS[psrname]
    fixed_whites = variant in ("table", "fl")
    add_red = (variant == "fl") and not cfg["red"]

    par = Path(tdbdir) / f"{psrname}.tdb.par"
    tim = Path(partim) / f"{psrname}.tim"
    psr = Pulsar(str(par), str(tim), ephem="DE440", timing_package="pint")
    Tspan = psr.toas.max() - psr.toas.min()
    tspan_days = Tspan / 86400.0
    tmin_mjd = psr.toas.min() / 86400.0
    tmax_mjd = psr.toas.max() / 86400.0

    def W(key, lo, hi):
        if fixed_whites:
            return parameter.Constant(whites[key])
        return parameter.Uniform(lo, hi)

    model = white_signals.MeasurementNoise(efac=W("efac", 0.1, 5.0))
    if cfg["equad"]:
        model += white_signals.TNEquadNoise(
            log10_tnequad=W("log10_tnequad", -10, -5))
    if cfg["ecorr"]:
        model += white_signals.EcorrKernelNoise(
            log10_ecorr=W("log10_ecorr", -10, -5))

    if cfg["red"] or add_red:
        red_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                   gamma=parameter.Uniform(0, 7))
        model += gp_signals.FourierBasisGP(red_prior, components=NCOMP,
                                           Tspan=Tspan, name="red_gp")

    if cfg["dm"]:
        dm_basis = utils.createfourierdesignmatrix_dm(nmodes=NCOMP,
                                                      Tspan=Tspan)
        dm_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                  gamma=parameter.Uniform(0, 7))
        model += gp_signals.BasisGP(dm_prior, dm_basis, name="dm_gp")

    if cfg["chrom"]:
        idx = 4.0 if cfg["chrom"] == "fixed4" else parameter.Uniform(0, 14)
        ch_basis = gp_bases.createfourierdesignmatrix_chromatic(
            nmodes=NCOMP, Tspan=Tspan, idx=idx)
        ch_prior = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                                  gamma=parameter.Uniform(0, 7))
        ch_cls = gp_signals.BasisGP(ch_prior, ch_basis, name="chrom_gp",
                                    combine=(cfg["chrom"] == "fixed4"))
        if cfg["chrom"] == "free":
            # enterprise 3.5.0 defect (M2 doc 2.1 item 7): _construct_basis
            # zeroes self._phi whenever a BASIS parameter (beta) changes, but
            # _construct_prior is cached on prior params only and never
            # refills it -> phi block 0 -> phiinv inf -> cho_factor crash on
            # every single-parameter beta jump. limit=1 because
            # _construct_prior has side effects.
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
            swg = sw_gamma_prior or PRIORS["sw_gamma"]
            sw_prior = utils.powerlaw(log10_A=parameter.Uniform(-10, 1),
                                      gamma=parameter.Uniform(*swg))
            model += gp_signals.BasisGP(sw_prior, sw_basis, name="sw_gp")

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

    if cfg["annual"]:
        ann_wf = chrom_mod.chrom_yearly_sinusoid(
            log10_Amp=parameter.Uniform(-18, -4),
            phase=parameter.Uniform(0, 2 * np.pi),
            idx=parameter.Uniform(0, 14))
        model += deterministic_signals.Deterministic(ann_wf, name="annual")

    gw13 = utils.powerlaw(log10_A=parameter.Uniform(-18, -11),
                          gamma=parameter.Constant(13.0 / 3.0))
    model += gp_signals.FourierBasisGP(gw13, components=NCOMP, Tspan=Tspan,
                                       name="gw13")

    model += gp_signals.TimingModel(use_svd=True)
    pta = signal_base.PTA([model(psr)])
    meta = dict(psr=psrname, ntoa=len(psr.toas), tspan_days=tspan_days,
                tmin_mjd=tmin_mjd, tmax_mjd=tmax_mjd, variant=variant,
                add_red=bool(add_red), fixed_whites=bool(fixed_whites),
                sw_gamma_prior=list(sw_gamma_prior or PRIORS["sw_gamma"]))
    return pta, meta


def published_vector(pta, psrname):
    """Published MAP values ordered like pta.param_names."""
    pub = PUBLISHED[psrname]
    x = []
    for name in pta.param_names:
        key = map_param(name, psrname)
        v = pub.get(key) if key else None
        if v is None:
            return None, name
        x.append(v[0] if isinstance(v, (list, tuple)) else float(v))
    return np.array(x), None


def a2_compare(pta, psrname, post):
    """Pre-registered A2 rule per parameter (M1 section 3, unchanged)."""
    pub = PUBLISHED[psrname]
    rows, n_agree, n_comp = [], 0, 0
    for i, name in enumerate(pta.param_names):
        key = map_param(name, psrname)
        med = float(np.median(post[:, i]))
        lo, hi = (float(np.percentile(post[:, i], q)) for q in (16, 84))
        row = dict(param=name, key=key, median=med, ci68=[lo, hi])
        v = pub.get(key) if key else None
        if isinstance(v, (list, tuple)):
            pmap, plo, phi = v
            agree = (lo <= pmap <= hi) or (pmap + plo <= med <= pmap + phi)
            row.update(published_map=pmap,
                       published_ci=[pmap + plo, pmap + phi],
                       agree=bool(agree))
            n_comp += 1
            n_agree += int(agree)
        rows.append(row)
    return rows, n_agree, n_comp
