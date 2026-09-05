# CCOR2 reported-source pilot

**Completed, stopped before pixel measurement.** This is an access/calibration
result, not a recovered comet or a discovery. See [RESULTS.md](RESULTS.md).

The single [prospectively frozen specification](SPEC-2026-09-05.md) selected
four 2026-09-01 L1A frames and one previously reported *potential* comet.
All four downloads succeeded (36,581,760 bytes total). All lack the documented
ISVIABLE flag required by the frozen gate. A header-only follow-up audit also
finds WCS rotation outside the frozen flip-only tolerance; the reporter's
display-to-FITS mapping remains unresolved. The images were not decompressed,
scored, searched, or converted into cutouts. There was no threshold tuning.

## Reproduce the local result without downloading images

From the repository root, with Python and NumPy installed:

```powershell
python -m unittest discover -s ccor-pilot/tests -v
python ccor-pilot/scripts/pilot.py --evidence ccor-pilot/results/header-evidence.json
python -m ruff check ccor-pilot
```

The small tracked header fixture includes every source URL, timestamp, byte
size, SHA-256 and image-extension header. Replay does not need Astropy or a
network connection. `.gitattributes` pins specification/code text to LF and
disables normalization for byte-hashed JSON evidence, whose original CRLF bytes
must also survive checkout. The synthetic tests cover fixed-track recovery, eight
negative tracks, one injection, invalid pixels, metadata, and orientation
gates; synthetic success is not real-source recovery.

The original live-header run used Python 3.12.10, NumPy 2.5.2 and Astropy 8.0.1
from the existing `erosita-dr2/.venv`. Its commands were:

```powershell
& .\ccor-pilot\scripts\download.ps1
.\erosita-dr2\.venv\Scripts\python.exe -m unittest discover -s ccor-pilot/tests -v
.\erosita-dr2\.venv\Scripts\python.exe ccor-pilot/scripts/pilot.py
.\erosita-dr2\.venv\Scripts\python.exe ccor-pilot/scripts/audit_headers.py
.\erosita-dr2\.venv\Scripts\python.exe -m unittest discover -s ccor-pilot/tests -v
```

Do not rerun the acquisition in place: download/result scripts refuse to
overwrite the single attempt. Raw FITS and the official ReadMe are kept only in
ignored `data/raw/`; the operational rolling server may later remove or change
the files. Exact raw regeneration would require the same hash-matching bytes,
normal HTTPS trust, and `requirements.txt`. The tracked evidence is sufficient
to reproduce the stopped gate, but not pixel photometry. The current command
intentionally has no option to waive scientific gates; actual pixel recovery
would require a new approved specification and a verified orientation path.

No automation, unknown-source scan, source report, account, submission,
publication, or correspondence was created.

The 9,989-byte [executed-source.zip](results/executed-source.zip) preserves the
exact two Python scripts and specification associated with the recorded
execution hashes. Subsequent import sorting/formatting does not change the
frozen criteria or evidence; offline replay checks the maintained source too.
Its ZIP SHA-256 is
`d3ad38c911755565bba844d18a3a9889c7b35c0d0afe3bf709347f80c9321367`.
