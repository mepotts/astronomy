# Draft query to the corresponding author. NOT SENT.

The Nature version carries *"All correspondence and request for materials can be made to
Kevin Hoy (kevin.hoy@mail.udp.cl)"*. Kevin Hoy is also reachable at `Kevin.Hoy@eso.org`.

**Send it yourself.** Nothing in this repo should mail anyone. Rewritten after M14: the
extraction questions from the old draft are mostly answered by our own work now, so the
email leads with the good news (the satellite reproduces from raw frames) and asks for
the two things we genuinely cannot get elsewhere: their EMPEROR setup, and order level
RVs.

---

**Subject:** Your CD-35 2722 B satellite reproduces from the raw frames. Two asks.

Dear Dr Hoy,

Congratulations on the CD-35 2722 B paper, and thanks for publishing the full RV table.
I have been reproducing it independently, starting from the raw CRIRES+ frames in the
ESO archive, with the aim of pointing the same method at other companions that already
have archival H band data.

First the good news. The main detection holds up from scratch. I rebuilt the reduction
with cr2res 1.6.10, extracted per nodding RVs with viper, and ran a blind period search
with no published values anywhere in the chain. The ~171 day signal comes out as the top
peak, and it survives adding BERV as a nuisance term, which given how entangled orbital
phase and BERV are in the archive sampling was the part I most doubted. My per epoch
scatter against your Table 2 lands at 70 to 90 m/s, so a bit above your 57.7, and my
semi amplitude runs some 20 to 40 percent high, which I currently blame on that same
phase BERV entanglement rather than on anything real.

Now the two asks.

1. The EMPEROR configuration for the model comparison, ideally the priors on each
parameter (periods, amplitudes, eccentricity terms, jitter, offset), the period windows
behind the windowed evidences, and the sampler settings. The reason I ask: running
nested sampling myself on your published Table 2, one satellite eccentric versus two
satellites as in your Table 1, I get log evidence differences that favor the one
satellite model under every prior choice I have tried, where the paper quotes +2.622
for two. I would much rather run your exact setup and find my priors were the problem
than speculate. If you have the per window logZ values for the 70, 88 and 115 day
models from the Nature run, those would help too.

2. The order level RVs, before combining, for even one or two nights. My remaining
precision gap is small but stubborn, and comparing per order values would localize it
in an afternoon. Any format is fine.

Two smaller things while I have you. I reverse engineered your setup as the eleven
orders that map to oset 4,7,8,9,10,12,13,14,17,18,19 in current viper numbering, a
telluric free template built in two iterations, kappa sigma clipping at 3, and template
oversampling of 2. If any of that is wrong I would love to know. And the night at BJD
2460604.82 is in the archive but not in Table 2; my pipeline throws it out on its own
(the across order scatter is seven times the typical night), and I am guessing yours
did something similar, but it would be good to confirm.

Happy to share everything, the reduction scripts, the injection tests, the nested
sampling code, whichever is useful. And if the second satellite question resolves in
your favor with the real priors, I will be glad to have been wrong in public.

Best,

Matthew Potts

---

## Notes on the draft

- **Lead with the reproduction.** It is true, it is the strongest opener, and it makes
  clear the email is collegial rather than adversarial. The blind search result is
  M14 §6 and §8; the numbers quoted (70 to 90 m/s, 20 to 40 percent high K) are the
  per nodding and archive route figures.
- **The second satellite is now raised directly.** The old draft held it back because
  it was a BIC proxy result. That threshold was passed in M14 §1 and §7: ten dynesty
  integrals, all negative, three pairings, three prior styles. The email still frames
  it as "my priors might be the problem," which is honest (evidence is prior
  sensitive) and gives them a graceful path.
- **The asks are ordered by value.** The EMPEROR priors are the one thing we cannot
  reconstruct from any archive; order level RVs close the last precision gap. The
  config confirmation and the 60604 night are one liners they can answer from memory.
- **Not raised:** the amplitude overshoot as a claim (confound limited, M14 §9), the
  Eq. 1 metrology finding, and the v1 BJD offset (already fixed in the published
  version; leading with old nitpicks would sour the tone). The embargoed epochs
  release on their own schedule (Dec 2026 to May 2027); asking for early access in a
  first email felt like one favor too many.
