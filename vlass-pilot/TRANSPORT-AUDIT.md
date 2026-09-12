# Timeout process-tree audit

Parent review correctly identified that `subprocess.run(timeout=75)` does not
prove every Windows venv descendant was killed when the original QL4.1 RMS request
timed out. The original statement that the entire worker was terminated was too
strong. The original timeout and receipt remain preserved; this is a correction
to the process-lifecycle interpretation, not a changed scientific criterion.

Read-only owner-context checks at **2026-09-12T20:14:31.9660150Z**:

- `Win32_Process` inventory filtered to python/pythonw executables whose command
  lines contain both `vlass-pilot` and `_request`: **zero matching processes**.
- Exact original path `data/followup/VLASS4.1-rms.fits`: **does not exist**.
- No processes were killed during this audit. No broad/guessed PID operation.

These observations show no outstanding matching request worker and no late
original RMS file at the audit time. They do not establish when a possible
descendant exited or prove cleanup occurred exactly at the original deadline.

**Before any further acquisition**, replace this transport wrapper with a tested
tree-aware bounded worker, using absolute paths and preserving current source and
measurement receipts. The repository's `dyson-revet/scripts/check_e_release.py`
contains `bounded_run`: Windows cleanup targets the newly created process tree;
POSIX uses its new process group. Read and reuse/test that implementation, record
the helper's exact hash, and verify child-process cleanup. Merely increasing the
timeout or hiding the exception is not an acceptable fix.

No additional network requests were made after the authorized successful retry.
The current `pilot.py` is preserved so its recorded measurement source hash and
exact offline replay remain valid. Transport hardening is an explicit remaining
gate, in addition to the failed local comparison-ensemble gate.
