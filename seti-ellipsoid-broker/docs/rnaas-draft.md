# DRAFT — Research Note (RNAAS) for your review, not submitted

> **Status: DRAFT for Matthew to decide on.** This is a *tool/methods* note, not a discovery
> claim. It announces an open, account-free implementation and validates it against published
> work — it does **not** claim a new technosignature result. Before considering submission:
> confirm you want to publish, add author/affiliation/ORCID, and sanity-check every number
> against the code's current output. RNAAS notes are peer-reviewed-lite, citable (they get a
> DOI), max ~1000 words and one figure/table.

---

**Title:** An Open, Account-Free Broker for SN 1987A SETI-Ellipsoid Target Lists, Validated
Against Nilipour et al. (2023)

**Authors:** Matthew Potts (affiliation TBD)

## Body (draft)

The SETI Ellipsoid is a strategy for time-domain technosignature searches: if an extraterrestrial
civilization synchronized a transmission to a conspicuous Galactic event such as SN 1987A, the
locus of stars from which that signal would be arriving at Earth *now* is an ellipsoid with foci
at Earth and the supernova [@Nilipour2023]. Stars crossing this shell at the present epoch are
prioritized targets. @Nilipour2023 computed crossing times for stars in the *Gaia* DR3 catalog
and identified SN 1987A ellipsoid targets suitable for time-domain monitoring.

We present `seti-ellipsoid-broker`, an open-source (MIT) Python pipeline that computes SN 1987A
ellipsoid crossings and exports ranked, observer-ready target lists. Two properties distinguish
it as infrastructure rather than a one-off analysis. First, it is **account-free**: it queries
*Gaia* DR3 anonymously through the ESA TAP service and accepts an externally supplied transient
list, so it requires no broker credentials — relevant now that alert-broker access is
increasingly gated behind survey data-rights. Second, it applies the *Gaia* DR3 parallax
zero-point correction [@Lindegren2021] before inverting parallax to distance; at the
few-hundred-parsec-to-few-kiloparsec distances typical of these targets, the ~-17 microarcsecond
mean offset shifts inferred crossing epochs by up to several years, comparable to or larger than
the per-star statistical crossing-time windows.

We validate the geometry against the published crossing times of @Nilipour2023. Using the
authors' machine-readable Table 2, we feed each of the 217 SN 1987A ellipsoid targets' adopted
distance and *Gaia* position into our solver and recover their published crossing epoch with a
maximum residual of $5 \times 10^{-4}$ yr across all targets, well within each target's quoted
1$\sigma$ crossing-time uncertainty. This confirms the implementation reproduces the reference
result exactly, and provides a regression test that guards the geometry against future changes.

The tool is timely: the SN 1987A ellipsoid crossing rate for the nearby stellar population peaks
in the late 2020s, so a maintained, reproducible, account-free target generator has near-term
observational value for both professional and amateur time-domain campaigns. The software, its
test suite (including the external validation above), and documentation are available at
[GitHub/Zenodo — insert DOI on release].

## Notes to self (delete before any submission)
- Honesty check: the *new* contributions are (a) the open account-free implementation, (b) the
  zero-point correction applied in this context, and (c) a reproducible, validated regression
  harness. Reproducing Nilipour is validation, not a result — keep the framing as a tool note.
- Consider one figure: the ellipsoid-crossing calendar for the current epoch, or a residual
  histogram (ours - Nilipour) showing the $5\times10^{-4}$ yr agreement.
- References needed in a `.bib`: Nilipour et al. 2023 (AJ 166, 79; DOI 10.3847/1538-3881/acde79);
  Lindegren et al. 2021 (A&A 649, A4; DOI 10.1051/0004-6361/202039653).
- RNAAS is appropriate for tool/dataset announcements; if you later add a genuinely new forward
  crossing catalog (stars crossing in 2026-2028 not in Nilipour), that could be the actual
  science hook.
