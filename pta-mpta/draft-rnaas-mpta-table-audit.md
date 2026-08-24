# DRAFT — NOT SUBMITTED

*Research Note of the AAS, draft. Nothing here has been sent to any journal, any collaboration, or
any person. Author, affiliation and ORCID are placeholders and are Matthew's to fill or delete.*

*Venue limits verified live from the AAS site on 2026-08-23,
<https://journals.aas.org/research-notes/>: **1,500 words or fewer**, **a single figure or table
(but not both)**, abstract required (since 2020-05-01), moderated but **non-peer-reviewed**,
citable and indexed in ADS.*

*Every number is re-derived from committed artifacts by `scripts/m4_note_numbers.py`, which
re-parses the arXiv LaTeX source with code sharing nothing with the M3 parser and cross-checks the
two: 504 noise values, 0 mismatches. The 29-row audit table (claim → value → artifact → verdict) is
in [`M4-finish-the-array.md`](M4-finish-the-array.md) §5. Pre-registration for this note: same file,
§1.5 (N1–N6). Prior-art verdict and its sources: §5.3.*

**Word count of the note proper (Title → end of "What would fix it"), excluding Table 1 and the
reference list: 1,451** (RNAAS limit 1,500).

---

**Title:** Reading the MeerKAT Pulsar Timing Array Noise Table: Unstated Priors, Seven Unreachable
Rows, and 66 Prior-Bounded Amplitudes

**Authors:** [PLACEHOLDER — Independent Researcher], ORCID [PLACEHOLDER]

## Abstract

The MeerKAT Pulsar Timing Array (MPTA) 4.5-yr release publishes per-pulsar noise models for 83
millisecond pulsars — 588 tabulated values — together with everything needed to reproduce them. In
the course of an independent reproduction from that public data we measured four properties of the
tables that a user needs and the paper does not state. No prior range is given for any parameter.
Seven of the 26 tabulated solar-wind spectral indices are negative, so a reproducer who applies the
[0, 7] range routine for power-law indices cannot reach them; two lie below even the −2 floor that
`enterprise_extensions` used for this signal class at the time. Twenty-six of the 588 values (4.4%,
22 pulsars) have a maximum-a-posteriori (MAP) value outside their own printed 68% interval, all but
one of them amplitudes. And 66 of the 83 log₁₀A₁₃/₃ intervals extend below −16.5, the paper's own
"clearly disfavoured" point, so most of that column is bounded by the prior, not the data. None of
this is an error, and all of it is checkable only because the release is complete and open.

## The tables, and why they can be audited at all

Miles et al. (2025) present the MPTA 4.5-yr data release and the noise models of its 83 pulsars in
two longtables — 14 parameter columns × 83 pulsars, and a deterministic-model table of 8 columns ×
23 pulsars, 588 sampled values in all. The release is fully public and account-free (Data Central,
doi:10.57891/j0vh-5g31): 83 ephemerides, 83 arrival-time files (245,907 sub-banded ToAs), and the
epoch archives. That completeness is why the tables can be re-derived at all, and it is not the
norm; the audit below is a service the collaboration made possible.

Two of the paper's own inventory counts differ from its tables by one, which is worth knowing before
either is quoted: the text reports a stochastic solar-wind term favoured in 25 pulsars where 26 rows
print one, and 58 pulsars with a DM or scattering process where 59 rows carry one.

That prior choices matter for PTA gravitational-wave inference is established (Goncharov & Sardana
2025; van Haasteren 2024), and nothing here re-argues it. What follows is narrower: four
measurements of one published table, each requiring no sampling, each checkable by any reader in
minutes, and each with a fix that costs a caption.

## (a) No prior range is tabulated

The word "prior" occurs six times in the uncommented LaTeX source of arXiv:2412.01148 — once as an
adverb, twice as "prior range" without a range — and the words "uniform" and "log-uniform" do not
occur at all. No numeric prior range is given anywhere for any of the 588 values. Nor is one
supplied elsewhere: the companion gravitational-wave paper defers to this one, and the Data Central
release contains 83 `.par` files, 83 `.tim` files, the archives, the portraits and a nine-video
anisotropy supplement — no chains, no posterior samples, no configuration or prior file (verified by
inspecting the downloaded tarballs). A reproducer working from the paper and the release must
guess all of them. They are undocumented rather than unknowable: a public repository belonging to
the paper's first author (`MattTMiles/MPTAGW`, no README, licence, tag or DOI, cited by no MPTA
publication) sets γ_SW ~ U(−4, 4), a range that brackets the whole column — but nothing in the
paper or the release points a reader there. For most columns the guess is harmless anyway, because
the published posterior sits far inside any reasonable range. For one column it is not.

## (b) Seven solar-wind spectral indices cannot be reached

The stochastic solar-wind model (Hazboun et al. 2022) is a power law in the plasma-density
fluctuation spectrum, and the paper says plainly that its index "is allowed to have a red or blue
spectrum" — so a negative γ_SW is intended, not an accident, and nothing here suggests the paper
implies a positive-only prior. What is missing is the range. Of the 26 pulsars whose favoured model
samples γ_SW, **seven have a negative tabulated value** (Table 1), and a further twelve have a 68%
interval crossing zero: **19 of 26 (73%)** cannot be fully represented by a γ ∈ [0, 7] prior — the
range routinely applied to power-law spectral indices in PTA analyses and, in our own first attempt,
inherited by the solar-wind block without thought.

Nor does the obvious library default rescue it. In `enterprise_extensions` the powerlaw branch of
`solar_wind_block` hard-coded γ_SW ~ U(−2, 1) in v2.4.3 (April 2024, current when the paper was
submitted) and still in v3.0.3 (June 2025, the version we ran); two published values (−2.21, −2.32)
and interval edges reaching −3.21 lie outside it. The package widened that range to U(−6, 5) in
September 2025, citing Susarla et al. (2024) — and that range does contain all seven. So the answer
to "which prior reproduces this column?" changed after publication and depends on a package version,
while the MPTA's own range remains unpublished. In our reproduction, chains run under γ ∈ [0, 7]
cannot visit the published solution for those rows at all, so a disagreement there is forced by our
prior and measures nothing.

## (c) Twenty-six MAPs fall outside their own intervals

The noise-table caption warns that "in some few cases, the MAP value has fallen outside of the …
confidence interval we report". The number is **26 of 588 (4.4%), affecting 22 of 83 pulsars**,
counting strictly (four further values print an offset of exactly 0.00 on one side and are excluded
as rounding). The distribution is the informative part: 13 are log₁₀A₁₃/₃, five E_Q, two each E_C,
log₁₀A_DM and the annual amplitude, one log₁₀A_Red — every affected value is an amplitude except a
single annual phase. No spectral index, chromatic index, n_⊕ or Gaussian-event parameter is
affected.

That pattern identifies the mechanism, and it is benign: these are one-sided, near-flat posteriors
whose mode lies against a prior rail while the equal-tailed 68% quantiles lie elsewhere. Both
numbers are right; they describe different features of the same distribution. The useful statement
for a reader is that a MAP outside its interval is a **flag that the row is prior-limited**, not a
typographical accident — and it occurs in one row in twenty-three.

## (d) Most of the log₁₀A₁₃/₃ column is not a measurement

Every MPTA noise model carries a free-amplitude achromatic red process at fixed γ = 13/3, described
in the paper as "allowed to vary across the entire amplitude prior range". Taking the paper's own
Savage–Dickey reference point — p(log₁₀A_CURN < −16.5), "a point where the prior range was clearly
disfavoured" — and applying it row by row: **66 of the 83 tabulated log₁₀A₁₃/₃ values have a 68%
interval reaching below −16.5** (median width 3.01 dex, up to 4.01). Seventeen are bounded on both
sides, and only **six** are constrained better than 0.7 dex: J2129−5721 (0.37), J1909−3744 (0.38),
J1751−2857 (0.44), J1547−5709 (0.45), J1643−1224 (0.55) and J1216−6410 (0.65).

This is a property of a 4.5-yr array, not a defect: a factorised-likelihood search works precisely
by multiplying many individually uninformative constraints, and the collaboration's own result rests
on that. But the column should not be read pulsar-by-pulsar as a set of measured intrinsic
amplitudes, and a reader cannot tell which 17 rows are measurements without recomputing it.

## One ephemeris value worth replacing

The released ephemeris for PSR J1825−0319 carries `BINARY DDH` with orthometric Shapiro parameters
H₃ = −2.979(96) × 10⁻⁷ s and ς = 0.513(335) — an H₃ that is 3.1σ *negative*, implying a companion
mass of −0.45 M⊙. A negative central value for a weakly detected H₃ is expected behaviour of that
parameterisation, whose whole purpose is that the fit converges whether or not the Shapiro delay is
detected (Freire & Wex 2010), and other PTAs tabulate non-significant h₃ values as a matter of
course. The narrow point is that this one sits in the ephemeris shipped for timing rather than in a
results table: `PINT` refuses to build the model, so the file cannot be loaded as released. The
delay involved is ≤ 0.3 µs against a 4.6 µs weighted residual RMS and is absorbed by the
timing-model marginalisation, so no published result appears to depend on it.

## What would fix it

Three caption-sized changes make the tables self-contained: print the prior range beside each
parameter column; mark the rows whose 68% interval reaches the prior floor; and state that a MAP
outside its interval indicates a prior-limited posterior rather than an error. The first is the one
that matters — without it, seven published rows cannot be reproduced by anyone who has to guess.

---

### Table 1

**Rows of the MPTA noise table that a reproducer cannot reach, and the shape of the two
prior-limited columns.** Values as printed in arXiv:2412.01148. γ ∈ [0,7] is the range routinely
applied to power-law spectral indices; U(−2,1) is what `enterprise_extensions` v2.4.3–v3.0.3
hard-coded for γ_SW; U(−6,5) is its range since September 2025.

| Pulsar | γ_SW | 68% interval | log₁₀A_SW | reachable under γ∈[0,7] | under U(−2,1) | under U(−6,5) |
|---|---|---|---|---|---|---|
| J0900−3144 | −0.20 | [−2.17, +2.26] | −6.16 | no | yes | yes |
| J1652−4838 | −0.68 | [−2.60, +2.21] | −8.92 | no | yes | yes |
| J1327−0755 | −0.76 | [−3.05, −0.07] | −7.19 | no | yes | yes |
| J1730−2304 | −1.61 | [−2.67, +2.32] | −7.92 | no | yes | yes |
| J1643−1224 | −1.96 | [−2.05, +2.84] | −8.31 | no | yes | yes |
| J1811−2405 | −2.21 | [−3.21, −0.36] | −8.37 | no | **no** | yes |
| J1751−2857 | −2.32 | [−3.01, +1.59] | −8.04 | no | **no** | yes |
| *12 further SW_Full pulsars* | +0.19 … +2.36 | crosses 0 | — | partly | — | yes |
| **MAP outside its own 68% interval** | 26 / 588 values (4.4%), 22 pulsars | 13 A₁₃/₃, 5 E_Q, 2 E_C, 2 A_DM, 2 A_s, 1 A_Red, 1 φ | | | | |
| **log₁₀A₁₃/₃ interval reaching below −16.5** | 66 / 83 rows | median width 3.01 dex | | | | |
| **log₁₀A₁₃/₃ constrained better than 0.7 dex** | 6 / 83 rows | 0.37 – 0.65 dex | | | | |

### References

- Freire, P. C. C. & Wex, N. 2010, MNRAS 409, 199 — arXiv:1007.0933
- Goncharov, B. & Sardana, S. 2025, MNRAS 537, 3470 — arXiv:2409.03661
- Hazboun, J. S., Simon, J., Madison, D. R., et al. 2022, ApJ 929, 39 — arXiv:2111.09361
- Miles, M. T., Shannon, R. M., Reardon, D. J., et al. 2025, MNRAS 536, 1467 — arXiv:2412.01148,
  doi:10.1093/mnras/stae2572
- Susarla, S. C., Chalumeau, A., Tiburzi, C., et al. 2024, A&A 692, A18
- Taylor, S. R., Baker, P. T., Hazboun, J. S., Simon, J. & Vigeland, S. J. 2021,
  enterprise_extensions v2.4.3, https://github.com/nanograv/enterprise_extensions
- van Haasteren, R. 2024, ApJS 273, 23 — arXiv:2406.05081

---

## Notes for Matthew — NOT part of the note

### Prior-art verdict

*Re-swept 2026-08-24 and still NOT SCOOPED on all four claims. The re-sweep added INSPIRE
(76 citing works against OpenAlex's 44) and found nothing auditing or reproducing this table, no
erratum (Crossref reports no `update-to` relation on doi:10.1093/mnras/stae2572), no second MPTA
release, and no prior ranges published anywhere. It did change one thing, folded into claim (a)
above: the γ_SW range is readable in public code. It also found the `enterprise_extensions`
default unchanged since the September 2025 widening, and that at the commit contemporaneous with
the paper the default was U(−2, 1) — which two published values fall below and most of the rest
above, so the collaboration demonstrably did not use the library default of the day. NASA ADS
refused automated access again.*

**NOT SCOOPED on any of the four claims, nor on J1825−0319.** The check covered: the arXiv listing
(v1 only, no replacement, no comments, no ancillary files); the OUP record (no erratum or
corrigendum; "corrected and typeset 17 Dec 2024" only); the companion GW paper arXiv:2412.01153
(no prior table, defers to this one); the Data Central release contents; the absence of any MPTA
code/prior repository; and all 44 works citing the paper (OpenAlex `W4405033984`), of which none
re-analyses or audits the noise table. The nearest MPTA-specific follow-up, Mishra et al. 2026
(arXiv:2607.09004, IPS-informed heliospheric modelling of this exact data set), re-models the solar
wind and does not touch the tabulated γ_SW values or the priors. Di Marco et al. 2026
(arXiv:2603.23817) *reproduces* one MPTA pulsar's model and reports agreement without commenting on
documentation. Coverage caveat, recorded: ADS's citation endpoint refused automated access and
Google Scholar hit a captcha, so the citation sweep rests on OpenAlex (44) plus a Scholar count
(43); a small residual risk of a missed citing item remains.

Two flagged risks, both closed locally afterwards rather than taken on trust:
(i) that a prior or config file ships inside one of the release tarballs — **checked directly, it
does not**: `data/partim.tar.gz` holds exactly 83 `.par` + 83 `.tim` and nothing else, and the
anisotropy supplement is nine MP4s;
(ii) that the `enterprise_extensions` default had moved since the value M3 quoted — **it had**, and
the note now version-stamps it (verified against the installed v3.0.3 source, line 234, and against
current master).

Two things prior art *does* constrain, both handled in the text:
1. "Priors matter for PTA GW results" is already published (Goncharov & Sardana 2025; van Haasteren
   2024) and is explicitly disclaimed as not new.
2. A negative H₃ from a weak Shapiro fit is expected behaviour of the h₃ parameterisation (Freire &
   Wex 2010), and other PTAs tabulate non-significant h₃ routinely; the J1825−0319 paragraph was
   rewritten down to the only claim that survives — that this value is in a timing ephemeris that
   consequently will not load.

### The single-graphic choice

RNAAS permits one figure **or** one table. The note spends its allowance on Table 1, because claim
(b) needs the pulsar names to be actionable. The alternative graphic —
`figures/m4_table_audit_a13.png`, all 83 published log₁₀A₁₃/₃ rows sorted by interval width with the
−16.5 line marked — is in the repo and would be the better choice if the note were re-scoped around
claim (d) alone.

### DRAFTED — NOT SENT: a paragraph Matthew could send the MPTA about the γ_SW prior

*Draft only. It has not been sent, it has no addressee, and nothing in this repository sends it. It
exists so that the option costs a copy-paste rather than a writing session. Sending it is Matthew's
call alone.*

> Dear MPTA colleagues,
>
> While reproducing the noise models of the 4.5-yr release from your public data, I ran into
> something I think is worth two lines of a future caption. Seven of the 26 tabulated solar-wind
> spectral indices are negative — J0900−3144, J1652−4838, J1327−0755, J1730−2304, J1643−1224,
> J1811−2405 and J1751−2857 — and twelve more have a 68% interval crossing zero. The paper says in
> the text that γ_SW is "allowed to have a red or blue spectrum", so the sign is clearly intended;
> what is missing is the range. Anyone who applies the usual γ ∈ [0, 7] to every power-law index (as
> I did at first) simply cannot land on those rows, and the `enterprise_extensions`
> `solar_wind_block` value of the time, U(−2, 1), does not contain two of them either — the package
> only widened to U(−6, 5) in September 2025. Widening my own prior to U(−4, 4) reproduced the
> published values, which is what convinced me the problem was my prior and not your data.
>
> I should add that I later found U(−4, 4) in your `MPTAGW` repository, so I may well have
> arrived at the range you actually used. That is the point rather than a caveat: the number
> exists and is even public, but nothing in the paper or the Data Central release points to it,
> so a reader who does not go looking through personal repositories cannot get there.
>
> More generally, the paper does not give a prior range for any of the 588 tabulated values. For
> most columns that is harmless; for γ_SW it is the difference between a table that can be
> independently checked and one that cannot. Given that you have already released everything else
> needed to check it, printing the ranges beside the column headings seems a cheap way to finish the
> job.
>
> With thanks for a genuinely open data release,
> [name]

### Reviewed against M5, and unchanged (2026-08-24)

M5 re-derived every number in this note (`scripts/m4_note_numbers.py`: 29 audited, 28 PASS, the one
CORRECTED row unchanged) and re-ran the note-vs-artifact checker
(`scripts/m4_note_check.py`: 22 checks, 0 failures). **M5's two new measurements — the registered
ESS floor and the solar-wind prior-propping census — change no number in this note**, because every
claim here is a property of the published table that needs no sampling, which is exactly the scope
N-criteria fixed for it. The note is therefore left as drafted.

Two M5 results bear on it without belonging in it, and are recorded here rather than added to the
text (adding them would break the note's zero-compute scope and its 1,500-word budget):

- **Claim (b)'s "19 of 26" is a lower bound, and M5 now measures by how much.** Across all 26
  solar-wind rows, run under both priors, **only five are measurements of γ_SW**; five more have an
  apparent constraint that is the prior edge, and fifteen are unconstrained under either prior — 20
  of 26 in total (16–20 across M5's registered sensitivity grid). Two of them — J1614−2230 and
  J1744−1134 — print *narrow* intervals and have *positive* published values, so a reader cannot
  flag them from the table alone. That is the companion paper's result, not this note's.
- **A companion full paper now exists in draft**
  ([`draft-paper-mpta-noise-reproduction.md`](draft-paper-mpta-noise-reproduction.md), DRAFT — NOT
  SUBMITTED). If this note goes out first, the paper cites it; if the paper goes first, this note
  stays publishable on its own, because its four claims are table-only and none of them depends on
  the reproduction.

### State

**DRAFT — NOT SUBMITTED. Collaboration paragraph DRAFTED — NOT SENT.** Both are Matthew's calls.
Submission would additionally need: author, affiliation and ORCID; an AAS account; and — if the note
is to point at the audit products — a citable archive DOI (the same open item as itf-linker C5 and
the eROSITA note).
