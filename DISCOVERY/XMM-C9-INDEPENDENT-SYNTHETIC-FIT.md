# C9 independent full-size synthetic fit

**PASS for the tested draft's synthetic streaming/resource/receipt path, not
actual-input validation or scientific recovery.** No retained product/header
files, actual source coordinates, scientific arrays or network were accessed.
The harness forbids retained `products/` and `headers/` opens and socket
connection/resolution through a Python audit hook.

## Exact tested implementation

- C9 draft `inspect_counts.py` SHA256
  `562786dae3cc4c835d8d9b3c43a4b4428adcb98d75dc2528ad75b0beb05ec11b`.
- Independent harness [c9_independent_synthetic_fit.py](c9_independent_synthetic_fit.py)
  SHA256 `b95f3739abbe51b0db39d8053c5c484d7c3e92842dbe09f29f1fe543a96b2697`.
- Pinned real pure decoder, geometry and counter are loaded by that draft;
  none was mocked. Existing structural reader, JSON resource functions,
  Windows peak-memory checks and process-tree runner are also real.
- Command: `dyson-revet/.venv/Scripts/python.exe -B DISCOVERY/c9_independent_synthetic_fit.py`.
  Pinned Ruff check of the harness passed.

The author is adding prefreeze receipt-schema checks after this benchmark.
This source-bound result must not be relabelled as execution of a later hash;
the parent can judge whether final changes warrant another synthetic fit.

## Real synthetic I/O, explicit substitutions

The fixture writes three independent, standards-readable FITS files in an
exclusive temporary directory, with the exact declared camera row counts,
strides, EVENTS offsets and **whole-file byte sizes**. Each generation chunk
is at most 10,000 rows; no whole event table is allocated. Extra opaque IMAGE
tails make the whole-file hashing cost match the three retained products'
sizes without copying or interpreting their other HDUs. Synthetic selected
values cycle across fixed times, several regions, CCDs and rejection cuts;
they are not an all-null/no-projection shortcut.

`verify_product` really hashes each full file and independently reparses its
headers against the generated report. `measure` uses the real packed decoder,
TAN projection and counter; it emits all chunk receipts. The actual audited
deadline helper launches a separate Python worker. Unchanged parent `assess`
and numerical `replay` re-read and compare the synthetic results.

Only three substitutions are made: generated-input manifest/binding in place
of C1/C8/C5 provenance; an artificial fixed five-centre geometry; and the
harness child entrypoint that configures the draft before calling `worker`.
This does **not** test actual `manifest()`/`binding()` or real C5 AST equivalence.
The synthetic FITS have three HDUs each, not the real complete HDU families;
header parsing and synthetic binding are therefore not exact full production
metadata costs. The byte totals and actual per-row numerical work are exact.
No science gate or bad state is overridden to force a successful result.

## Clean run results

Local temporary evidence directory:
`C:/Users/matth/AppData/Local/Temp/xmm-c9-independent-d5nby_h_`.
All raw fixtures/receipts remain there locally, not in the acquisition stage
or committed product tree. The harness generates fresh directories on a new
invocation; it does not overwrite either retained run.

| Quantity | Result |
| --- | ---: |
| Total rows per numerical pass | 3,323,958 |
| Physical EVENTS row bytes per pass | 142,652,840 |
| Selected decoded bytes per pass | 93,070,824 |
| Full opaque product bytes hashed per pass | 246,890,880 |
| Completed chunks, pn / MOS1 / MOS2 | 270 / 28 / 36 |
| Durable chunk start/result pairs | 334 |
| Stage JSON files / actual bytes | 678 / 709,463 |
| Worker peak memory | 73,211,904 bytes |
| Parent process peak memory | 75,014,144 bytes |
| Fixture generation | 0.515 s |
| Worker launch + run + independent parent assessment | 8.828 s |
| Additional numerical replay | 2.937 s |

The worker and parent are below 536,870,912 bytes; JSON is below 4,194,304 bytes
with room for the 262,144-byte terminal reserve. Worker execution is included
within the reported 8.828 seconds, comfortably below its 120-second cap.
The explicit replay also completes below its independent 120-second cap.
These timings are local observations, not guaranteed bounds on other machines
or different scientific field occupancy. No process-timeout kill was triggered
or newly tested by this successful run.

Worker, parent and one explicit replay all succeed, producing three complete
passes: **427,958,520 physical row bytes** and **279,212,472 selected bytes**.
Each camera's final progress has `current=null` and exact complete counters.
Outcome SHA256:
`a034e7defb1dfd666bafb5f92082bf0e0abd031a79ee2b2655ac767afa73fa4f`.

An additional **aggregate/receipt-only** independent check verified 1,355
recorded artifact hashes (678 outcome references and 677 worker references),
all 334 pairs, row/rejection/accepted closure, per-CCD accepted closure, every
254-by-5 histogram shape and per-CCD region sum, exact five labels, and all
three false inference flags. This check added **zero numerical passes**.
Parent/replay agreement is reproducibility, not an independent scientific
oracle for every simulated count; the pure counter's separate scalar-oracle
review supplies that complementary evidence.

## Preserved first fixture attempt

An earlier synthetic run at
`C:/Users/matth/AppData/Local/Temp/xmm-c9-independent-qfckm7v4` also completed
all three passes, but the fixture generator used lowercase exponent text in
two FITS cards. Astropy warned and normalized these cards while constructing
the synthetic file. That was a **fixture-generation warning**, not a bypass
of the runtime's warning gate. The harness was corrected to uppercase FITS
exponents and configured to treat all generation warnings as errors before
the separate clean invocation above. No wrapper, thresholds or real inputs
changed. First outcome hash:
`059414ab91a4923b66a9382fd3758dc785b9a686324f6261c8965503812b7363`;
first harness hash:
`cefee29a73a25cfd1ca5cfe02ef454f0110e896689eb019966f9fec1ede99cb4`.
First run/parent 9.453 s, replay 2.844 s, same 709,463 JSON bytes.
Both directories are retained; no failed/warning evidence was overwritten.

## Remaining boundary

This closes an independent full-size synthetic resource/streaming feasibility
check for the stated draft. Final source/tests/protocol review and exact freeze
remain the parent's responsibility. Real C9 provenance/header validation,
actual counted outputs and their independent replay remain unexecuted by this
reviewer. Neither this fixture nor descriptive histograms establish usable
exposure, clean background, two usable negative apertures, detector-artifact
rejection, calibrated recovery, or an unknown-source discovery.
