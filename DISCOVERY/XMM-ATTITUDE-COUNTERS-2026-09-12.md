# XMM attitude counter semantics: bounded primary-source check

Date label: 2026-09-12; completed 2026-09-13 UTC. Independent documentation review only. No catalog/product requests, software installation, attitude-array decoding, reprocessing, or changes to executed C4 artifacts.

## Conclusion

The five official sources below do **not establish** that this product's OM columns are synthetic copies of AHF, nor do they supply the exact producer rule for `NGAHFOM`. The counter/finite-value discrepancy remains unresolved. It is not evidence of a new astronomical effect, and equal summary statistics are not proof of row-by-row identity or independent sensor agreement.

The documented OAL fallback concerns **AHF versus RAF**, both star-tracker attitude sources. It must not be relabelled as an AHF-to-OM fallback. A historical statement that OM attitude construction was unimplemented is relevant context, not proof of the behavior of the much later producer used here.

## Local evidence being interpreted

The already-retained C4 result reports 51,975 finite AHF triplets and 51,975 finite OM triplets; their reported relative-motion aggregates agree, and every stored `DAHFOM` value is zero. The retained header counters are `NATT=NGAHF=NGOM=51975`, but `NGAHFOM=0`. These are C4's results, not new measurements in this review. In particular, no pairwise raw-triplet equality test was performed here.

The C4 result document read for this review had SHA-256 `dbba9bdd283ce8a7b93a6b0266ba549e2153f2a4432ac03db0ec35415510b33f`. This identifies the reviewed interpretive document, not a claim that subsequent editorial corrections must retain that hash.

## Five primary sources and what they establish

1. [SAS atthkgen description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node3.html). The task obtains AHF and OM tracking-history attitude through OAL at sampled times. An input-time separation exceeding 20 seconds is described as bad quality, represented by NULL output triplets. The description defines `DAHFPNT` against median AHF pointing, `DOMPNT` against the OM counterpart, and `DAHFOM` between the two sources. It does not document an AHF-copy-to-OM fallback or the counter update expressions.

2. [SAS atthkgen output description](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/node7.html). This specifies the ATTHK table's real64 columns, seconds for TIME and degrees for attitude/offset values, and lists `NATT`, `NGAHF`, `NGOM`, and `NGAHFOM`. Listing those counters does not establish that `NGAHFOM` must equal a count of jointly finite triplets, particularly in an undocumented fallback or initialization branch.

3. [OAL SAS_ATTITUDE environment setting](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/oal/node13.html). AHF and RAF are star-tracker sources; allowed preferences include AHF-only, RAF-only, and fallback orders, with AHF:RAF the documented default. The selected source is intended to be recorded in `ATT_SRC`. This says nothing about synthesizing OM columns. This review has not established the observation's actual environment setting or an applicable `ATT_SRC` value.

4. [atthkgen ChangeLog](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/atthkgen/ChangeLog). Version 1.16, dated 2000-11-28, records replacing the nominal pointing reference with median spacecraft pointing for the instantaneous offsets (SSC-SPR-2077). Version 1.22.1 describes a preqgti/uncorrected-median change; 1.22.2 describes SUM.ASC variability-alert updates. No entry examined documents copied OM fallback or an `NGAHFOM` update rule. The retained product's reported producer is atthkgen 1.22.1/SAS 21, whereas the current task documentation identifies 1.22.2/SAS 22; the changelog is useful version context, not a substitute for inspecting producer code.

5. [OAL ChangeLog](https://xmm-tools.cosmos.esa.int/external/sas/current/doc/oal/ChangeLog). Version 2.0 (1998-08-30) introduces the `attitudeFromAhf` selector between AHF and OM tracking history, while noting that constructing an OM AttitudeLocator was not yet implemented. Later entries document AHF/RAF work, including the SAS_ATTITUDE setting in 3.104. The historical unimplemented branch does not specify copied output values, counter arithmetic, or the behavior of the retained product's later OAL build. No current copied-OM guarantee was established by this history.

## Interpretation correction and next proof

The C4 interpretive table's phrase “Recorded offset from nominal pointing” should read “Recorded offset from median AHF/OM pointing,” with the matching source identified for each column. The numbers and executed receipts do not change. This is supported by sources 1 and 4 above; the parent has been notified. This reviewer did not edit C4.

The narrow missing proof is the version-matched atthkgen implementation of the OM output assignment, `DAHFOM` computation, and initialization/increment/write rules for all four N-counters, together with the invoked OAL attitude-selection and failure paths. Establish whether those paths actually distinguish independent OM tracking, unavailable OM, a shared locator, or another behavior; do not choose a branch because its prediction matches the aggregate result. A directly available official source excerpt or a maintainer's explicit version-qualified explanation could resolve this without another data download or numerical fit. No such source-code proof was obtained in this bounded check.

Until then, keep the finite sampled AHF motion diagnostics as the limited C4 measurements they are. Do not call OM an independent confirmation, convert zero `NGAHFOM` into a missing-row count, infer continuous attitude stability between samples, or relax downstream scientific gates. The unresolved provenance question is separate from the already-verified byte integrity and descriptive numerical extraction.
