---
title: 'exosat-rv: A Python Pipeline for Radial-Velocity Exosatellite Searches Around Directly Imaged Companions'
tags:
  - Python
  - astronomy
  - exoplanets
  - exomoons
  - radial velocity
  - spectroscopy
  - direct imaging
  - brown dwarfs
authors:
  - name: Matthew Potts
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 13 August 2026
bibliography: paper.bib
---

## Summary

`exosat-rv` is a Python toolkit for **companion-side radial-velocity searches for
exosatellites**: rather than watching a star for the reflex wobble of a planet, the
method points a high-resolution spectrograph at a directly imaged brown dwarf or giant
planet and looks for the reflex wobble of *its own* satellite. The technique was
proposed by @vanderburg2018 and returned three published non-detections
[@ruffio2023; @vanderburgrodriguez2021; @horstman2024] before @hoy2026 reported the
first claimed detection — a roughly Jupiter-mass companion to the brown dwarf
CD-35 2722 B [@wahhaj2011] — from VLT/CRIRES+ spectra [@dorn2023]. `exosat-rv` grew out
of an independent attempt to reproduce that result from the public ESO archive, and now
provides the reusable parts of that attempt: archive inventory and provenance auditing,
conversion of ESO pipeline products into the layout the `viper` radial-velocity code
[@kohler2025] consumes, an injection-recovery gate that every extraction configuration
must clear before its output is trusted, a blind period search with
permutation-calibrated significance, nested-sampling model comparison [@speagle2020],
and a target-feasibility framework built on the detectability calculations of
@lazzoni2022 and extended to a public VLTI/GRAVITY astrometric alternative
[@kral2026].

## Statement of need

Radial-velocity exomoon searches on directly imaged companions are a young, small
field. The method was proposed by @vanderburg2018; three published searches returned
non-detections [@ruffio2023; @vanderburgrodriguez2021; @horstman2024]; and in 2026
@hoy2026 reported the first claimed detection. Each of these was a bespoke, largely
unshared analysis built around a general-purpose radial-velocity code, and no common,
reusable, verification-disciplined pipeline exists for the problem's specific failure
modes.

Those failure modes are concrete, not hypothetical. In an independent reproduction of
the CD-35 2722 B detection, three separate pipeline changes that *looked* like
improvements to the science target were later shown, by a positive control on the known
binary brown dwarf GJ 229 B, to work by deleting signal rather than recovering it: an
empirical per-order weighting scheme, a telluric order screen, and an under-iterated
self-templating recipe. Each would have been silently adopted, and each would have made
every subsequent non-detection look stronger than it actually was, had the control not
caught it. This is the failure mode `exosat-rv` is built to prevent: every change to an
extraction recipe is scored only against externally fixed values — a paper's published
radial velocities, or a synthetic injected signal — and nothing is adopted on the
strength of an internal metric alone. That discipline, more than any single
measurement, is the project's most transferable contribution, and it is the part a
target-specific search is most likely to skip under time pressure. `exosat-rv` packages
it as runnable, version-controlled code rather than as a methods-section paragraph: the
injection gate, the positive control, and the significance calibration are the same
machinery for every target, not something reimplemented per campaign.

The package also lowers the barrier to attempting this kind of search at all. Locating
the right archive holdings for a given companion is itself nontrivial: target names are
inconsistent across ESO's archive, programme names do not identify the science target,
and reduced-product band metadata (`filter_path`) is documented, in this project, to be
wrong in specific and recurring ways. `exosat-rv inventory` and `exosat-rv targets`
encode those corrections once so a new user does not have to rediscover them from raw
archive queries.

## Functionality

The installable package (`exosat-rv`, MIT-licensed, Python >=3.11,
`pip install -e ".[dev]"`) exposes a `typer`-based command-line interface —
`inventory`, `probe`, `targets`, `alias`, `orbits`, `survey`, `closein`, `orders`,
`gravity` — covering: archive inventory and public/embargoed/reduced-product
bookkeeping against the ESO TAP service and the NASA Exoplanet Archive; lossless
conversion of ESO `calib_level=2` CRIRES+ products into the per-order, per-detector
layout `viper` requires; alias-period discrimination via injection-recovery on the
observing cadence; a BIC-based approximation to nested-sampling model comparison,
run directly against a paper's published radial-velocity table; a companion-feasibility
survey across the directly imaged companion population, calibrated on achieved rather
than forecast instrumental precision; and a query layer for public VLTI/GRAVITY
astrometry as an independent, non-spectroscopic route to the same question. This layer
carries 123 offline unit and integration tests (`pytest`, `ruff`-linted) that pass in a
clean virtual environment, plus network-marked tests against the live archives.

The from-raw extraction pipeline itself — driving `cr2res` and `viper`, the
injection-recovery gate, the permutation-calibrated blind search, and the
`dynesty`-based nested-sampling comparison — is implemented as an accompanying suite of
analysis and reduction scripts (`scripts/`) rather than inside the installed package,
and is documented as a runbook (`docs/viper-runbook.md`) aimed at reproducing the
author's own pipeline rather than as general-purpose end-user API documentation. Every
scientific conclusion the project has published, together with the traps that produced
a wrong one along the way, is indexed in `LESSONS.md` and the per-milestone
`M*-RESULTS.md` series that accompanies the code.

## Acknowledgements

Development of this project — including its literature search, pipeline
implementation, statistical analysis, and this manuscript — was carried out by AI
agents (Claude, Anthropic, via Claude Code) directed and reviewed by the author, who
set the research questions, verified the agents' claims, and takes sole responsibility
for all content. This follows the disclosure practice already established for the
project's scientific manuscript: see the AI contribution and responsibility statement
in `docs/paper/draft.template.html` and the stage-by-stage checklist at the repository
root, `AI-CHECKLIST.md`.

## References
