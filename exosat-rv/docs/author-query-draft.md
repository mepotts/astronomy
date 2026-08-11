# Draft query to the corresponding author — NOT SENT

The Nature version carries *"All correspondence and request for materials can be made to
Kevin Hoy (kevin.hoy@mail.udp.cl)"*. Kevin Hoy is also reachable at `Kevin.Hoy@eso.org`.

**Send it yourself.** Nothing in this repo should mail anyone. Edit freely — the questions
are ordered by how much they would save us, and question 4 is the one that matters most.

---

**Subject:** Reproducing the CD-35 2722 B RV extraction — a few method questions

Dear Dr Hoy,

Congratulations on the CD-35 2722 B result. I'm working through it as an independent
reproduction, with a view to applying the same method to other directly imaged companions
that have archival CRIRES+ H-band data.

The inference side largely reproduces: fitting your published RV table with an independent
Keplerian code recovers the ~171-day signal, and your 87.3-day choice for the second period
beats the 14/70/115-day aliases in both the preprint and published tables — so this isn't a
question about the detection.

Where I'm stuck is the extraction. I've built cr2res 1.6.10 and taken five of your nights
from the raw frames through `cal_dark`/`cal_flat`/`cal_wave`/`obs_nodding` — that part
validates, reproducing ESO's archived products to ~40 m/s in the final RV. Against your
published values my best viper series now scatters by ~150–220 m/s over the 17 archival
epochs (a robust order combine recovers K = 304 ± 69 m/s at your period, against your
306.0), where your quoted per-epoch errors are ~58 m/s. Closing that last factor of ~3 is
where I'd be grateful for any of the following:

1. **The viper command line or config section you used.** I've inferred `-nocell` (the data
   is cell-free), that a tight `kapsig` matters, and `-telluric add2` from the two telluric
   coefficients in your Fig. 11, but I'm still guessing at `oversampling` and the IP model.

2. **How the template was built.** You mention two iterations — were those `-createtpl` runs
   with `-tpl_wave tell`, co-added over all 40 frames, and with the cell modelling off?

3. **Whether I have the eleven orders right.** Mapping your order labels through viper's
   older CRIRES+ numbering (pre commit `6e1b19c`) gives, in current numbering,
   `oset 4,7,8,9,10,12,13,14,17,18,19` — and that set does score best empirically. Is that
   the set, and what was the quantitative criterion for "sufficient telluric lines"?

4. **The scientific question, and the one I'd most value your view on:** in my extraction the
   per-order RV zero points are stable within a night — two nodding frames ten minutes apart
   agree well — but drift between nights by several hundred m/s, and that drift is essentially
   my entire error budget. Did you see anything similar, and if so, is it handled by the
   template, by the order weighting, or by something else?

5. If it's not too much trouble, **the per-order RVs** (before combining) for even one or two
   nights would let me localise the difference immediately. Happy to work with whatever
   format is easiest.

I'd of course acknowledge any help, and I'm glad to share what I find either way — including
the reduction scripts, if they're useful to anyone repeating this.

One small thing that may be worth knowing: the RV table in arXiv:2607.05193v1 appears to have
BJDs offset by about −0.87 d relative to the observations (17 of the 18 epochs I can check
against the ESO product headers). The published Table 2 matches the archive to within a few
minutes, so this looks like it was caught in review — but the preprint is still the version
most people will download.

With thanks and best wishes,

[name]
[affiliation, if any]

---

## Notes on the draft

- **Lead with what reproduces.** The period-choice reproduction is real (M6, M13 §5) and
  saying so first makes clear this isn't a challenge to the result.
- **Deliberately not raised: the second-satellite evidence flip** (M13 §5 — our BIC/2 proxy
  gives −0.51 on the Nature table where the paper quotes +2.62). It's a proxy result, the
  kind of thing to raise only after nested sampling confirms it, and never in a first email
  asking for favours. Numbers in the draft are chosen so nothing said here contradicts it
  later: "recovers the ~171-day signal" and "the 87.3-day choice beats the aliases" are both
  true on either table.
- **Q4 is the ask.** Q1–3 are configuration archaeology that one reply settles; Q4 is the
  open problem and the only one where their answer might be scientifically interesting to
  them too.
- **Q5 is the highest-value if granted** — per-order RVs would localise the difference in an
  afternoon — but it's the biggest imposition, so it goes last and stays optional.
- **The BJD note is offered as useful, not as a correction.** It is independently verified
  from the ESO headers (M12 §1.1) and is already fixed in the published version.
- Not raised: the published Methods still quote "169.45 d" where Table 1 gives 171.454. It's
  an editorial leftover, and leading with two nitpicks would change the tone of the email.
