# RXJ M6 independent review

Current disposition: **GO for parent exact-byte freeze and the separately
authorized, bounded M6 attempt.** The historical HOLD checkpoints below are
preserved; the final acceptance resolves them without changing scientific gates.

## Initial design checkpoint — 2026-09-13

**HOLD for author-ready adapter, final protocol and synthetic tests.** The
complete adopted M5-NEXT decision was read. No material objection was found to
the separately named fresh attempt with unchanged identity/scientific/byte gates.
This review has not read the old partial, private products or headers, run any
historical stage, or issued a request.

The retained M5 record does not supply a strong representation validator, verified
EOF or a complete product. A fresh exclusive transfer is therefore a distinct
proposal; no Range append, splice, old-file reuse or retrospective repair is
authorized. The crude prior retained-byte/time ratio is only an engineering
budget rationale, not a throughput forecast or proof of eventual completion.

The new adapter must explicitly rebind all runtime and helper state/path globals
to M6 and invoke its own CLI. Loading hash-pinned M5 mechanics is not permission
to invoke the historical worker, binding replay or original output directory.
Current source/tests/protocol and prior public evidence remain hash-bound;
historical private artifacts are unnecessary for this adapter's binding.

The final review will check exactly the adopted changes: one 7,200-second hard
batch deadline, 7,140-second cooperative worker budget, separate 300-second
parent/replay passes, and 64-KiB maximum network reads while local copying and
decompression retain their 1-MiB chunks. Cap-plus-one and unknown interrupted
work must remain honest. Missing completion following return code 124 needs an
explicit hard-deadline STOP, without relabelling M5. No retry loop or new endpoint
follows from another STOP.

All existing raw/expanded totals, free-space, memory acceptance, JSON/reserve,
identity and privacy gates remain. Success is still retained authenticated
headers only, not photon recovery, calibration sufficiency, aperture coverage,
clean controls or discovery. Final assessment is pending the implemented adapter
and finite synthetic isolation/deadline/partial-accounting tests.

## Adapter review checkpoint

The complete adapter, protocol and focused/inherited-test harness were read.
The adapter loads the frozen M5 source from verified bytes into a fresh module,
whose C1 primitive module is also fresh. M6 paths, source/protocol and helper
state are rebound before execution. No source-string rewriting or original M5
CLI dispatch is used. The inherited fixed request plan is interpreted only in
M6 state. Temporary network chunk and assessment-time overrides are restored
in `finally`; binding records stable separate settings during those overrides.

Independent execution passed **21 synthetic tests** (16 inherited cases and five
focused cases) and Ruff 0.16.5. **Eight additional independent cases** passed:
six network cap/overflow probes around zero and the 64-KiB boundary, one local
copy-size/EOF check, and mutation of one fresh module's plan/helper state without
affecting another. The network cases returned exactly cap+1 bytes, retained only
cap bytes and restored the 1-MiB local chunk setting. They used generated memory
buffers only. The guarded actual binding fixture opened no prior private input.

The parent's read-order finding is fixed: the wrapper calls resource validation
before reading its outcome JSON. A focused guard confirms no outcome read when
that budget check fails. One legitimate combined failure remains under final
correction: a hard timeout with no worker-result can subsequently be downgraded
to `STOP_PEAK_MEMORY` by inherited terminal serialization. The wrapper must
accept an actually evidenced parent-peak STOP while retaining raw 124 and absent
completion, instead of rejecting that legitimate failure artifact. Parent and
reviewer identified the same case; it is not a request for a broader framework.

Final GO is pending only this narrow combined-stop correction, its synthetic
regression and final hashes. No real request, private partial/header read or
historical replay has been performed in this review.

## Final scoped acceptance — 2026-09-13

The final combined-stop implementation, regression and protocol clarification
were read. A missing-worker hard timeout may retain `STOP_PEAK_MEMORY` as its
primary error only with a typed integer parent peak strictly above the cap,
`STOP` status and explicitly false assessment completion. Raw integer 124 and
missing completion remain required evidence; the inherited failure-artifact
validation still runs. The focused regression exercises the actual inherited
terminal save's late peak override, then artifact-only replay under a no-header
tripwire, checks immutable artifacts, and rejects an at-cap peak mutation.
This resolves the concrete replay defect; it does not turn a failed transfer
into successful header validation.

The independent final run passed **22 tests** (16 inherited M5 cases and six
focused M6 cases) and Ruff 0.16.5. The eight additional generated-buffer/isolation
probes recorded above also passed. No further benchmark or combinatorial test
campaign was needed. The protocol now accurately describes both the explicit
hard-deadline STOP and the evidenced late-memory precedence. All final hashes
below were independently calculated from the current files.

| Artifact | SHA256 |
| --- | --- |
| M6 `acquire.py` | `b7370adf14a0e8935e00d0c8d312b4dd913790d621e85475bf0f39325c926e77` |
| M6 `test_acquire.py` | `b33cd3176a207f6832c9bd348f15c5e74e793d1ee1afa7d76cbb5a772bb7af82` |
| M6 protocol | `f14ac193511e0a6a876809adc1dfd04b588beac5a1efc4b3988f1ee566de5847` |
| M6 `.gitattributes` | `805ac80d2520f7a8f224ec68cb639663af574872866680a623d86c5f06aa21e8` |
| M6 `.gitignore` | `6567d61f6c56523a1af8103f3af2db07f6859b799ada7db68895139e211f28c3` |

Acceptance is limited to the reviewed isolated adapter, three unchanged fixed
requests, finite budgets and header-only acceptance. It predicts neither
transfer completion nor astronomical recovery. M5's partial and STOP remain
untouched. This review issued no request, opened no actual private partial or
header, and invoked no historical worker or replay. Parent freeze and explicit
execution authority remain separate from this preflight review.
