# M2 pre-execution review audit

No real M2 measurements were made while these issues were corrected. The original
200 grid positions, five flux strata and 103/97 spatial split are unchanged;
the regression suite compares all positions against m2-plan-v1.json exactly.

Independent review led to these pre-output corrections/clarifications:

- Common-beam photometry uses the same local celestial Jacobian as convolution
  and its noise annulus, not the original full-plane scale approximation.
- Numerical proof checks both an independently generated exact-sky template and
  the actual fixed-position measurement function. All 240 combinations pass.
- Insertion tests apply the original 21x21 local maximum and all target/edge/
  separation criteria at the selected peak coordinate, not only the true centre.
- Conditioned photometry measures at the selected QL3.1 coordinates while keeping
  the injected model at its original true position. Original-selection and final
  common-morphology conditioning are reported separately.
- An injected-stage failure cannot become a blank-screen exclusion. Missing
  measurements remain in denominators, required flux-bias results become undefined
  and fail rather than dropping missing values, and empty selected strata have
  unmeasured bias rather than zero bias.
- The parent resolved the prospective bright-injection criterion conservatively
  as >=95% JOINT three-epoch recovery, retaining per-epoch rates too.

The earlier preflight source/protocol/plan snapshot is preserved in
m2-preflight-revision1.zip; the prior plan is m2-plan-v1.json. The initial narrower
synthetic receipt is m2-numerical-v1.json. That provisional receipt did not bind
a script hash, so no claim is made that the later source snapshot reproduces its
exact code version. The final real execution reruns the strengthened numerical
proof and binds the complete executing source and input/protocol hashes.

Seventeen M2 regression tests and Ruff pass before first real execution. They
include the selected-coordinate regression, selected-morphology conditioning,
failure denominators, joint recovery, kernel handedness, unit/NaN/beam rejection,
and proof that all 200 positions stayed unchanged.

Source frozen for first execution:
`f76854d02568d1ebf78f6bbe367d7093a149e681bbe4b4b83bbe150ff3ee9ffa`.
Protocol:
`07f0df26052f78fa0e40725c646df659d804d44fbd893fb7bce7145eebaea356`.
Plan:
`ae410ffa184db03894822f1cee2179445ab48977997aa6dd43c163d1ea57e7e3`.

All earlier pilot/full-plane scripts, protocols and measurement results remain
unchanged. No additional acquisition is part of M2. Reference-screened nulls are
conditional on QL3.1 screening, with no additional cross-epoch masking; they are
not a random unconditioned sample of the sky.
