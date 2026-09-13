# C9 resource preflight: synthetic only, runtime fit still pending

Root independently exercised the three frozen pure components using invented
coordinates and repeated synthetic packed rows, not retained science products.
Camera lengths, strides and fixed selection/time configuration match C9's
prospective declared workload; fixture photons are synthetic and deliberately
accepted. This is a kernel throughput check, not a numerical experiment.

Across334chunks/3,323,958synthetic rows:142,652,840buffer bytes supplied to the
decoder and93,070,824selected bytes decoded. Each chunk passes decoder, true
TAN/spherical geometry and fixed counter; accepted/source-aperture counts agree
exactly with the generated fixture size. No full-table array is allocated.
Elapsed1.218seconds; process peak74,665,984bytes (Windows peak sampler).
Actual science-product bytes read:0. Frozen component hashes are those in
their [geometry](XMM-EVENT-GEOMETRY-REVIEW.md) and
[counter](XMM-RECORDED-COUNTS-REVIEW.md) reviews and the C9 manifest proposal.

This does **not** include full-product hashing, structural replay, disk row
reads,334durable chunk receipt pairs, JSON artifact closure or parent replay.
Those costs need the author's full-wrapper synthetic fixture before final
120second/512MiB/4MiBJSON feasibility acceptance. A kernel timing is not a
guarantee of real-data runtime or a reason to waive a timeout.
