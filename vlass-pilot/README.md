# VLASS: one known-source feasibility pilot

This independent radio front starts with **VT 1137-0337 only**, its public
multi-epoch quick-look cutouts, and a same-field comparison/null ensemble.
It asks whether the input identity, beam-aware source recovery and local
measurement consistency are adequate to justify further validation.

**Executed:** three-epoch source recovery passes, but only one reference comparison
survives (five required). Overall **STOP_MEASUREMENT**, not discovery-ready. See
[September 12 results](RESULTS-2026-09-12.md) for exact measurements and gates.

**Separate full-parent-plane follow-up:** the same unchanged cuts yield 12 common
comparison candidates. [Calibration feasibility passes](FULL-PLANE-RESULTS-2026-09-12.md),
but common-beam, morphology and empirical false-positive validation remain; this
is not a discovery or authorization for an unknown search. Earlier results remain
unchanged. New requests used a tested tree-aware timeout driver.
That cleanup test succeeds in the owner execution context used for acquisition;
restricted-token cleanup is not guaranteed. The [next validation proposal](NEXT-VALIDATION-PROPOSAL.md)
is unexecuted and uses only retained data.

Read [PROTOCOL.md](PROTOCOL.md). This is not a discovery search or a replication
of the published fading rate. Raw FITS inputs are ignored; the acquisition
manifest binds URLs, HTTP provenance, byte counts and SHA-256 hashes.

Fallback operating rules are in [AGENTS.md](AGENTS.md); the referenced global
agent-kit README was unavailable.

Current verification commands from the repository root (existing science runtime,
no installation; acquisition and first measurement are already complete):

```powershell
dyson-revet/.venv/Scripts/python.exe vlass-pilot/pilot.py replay --followup
dyson-revet/.venv/Scripts/python.exe vlass-pilot/full_plane.py replay
dyson-revet/.venv/Scripts/python.exe -m unittest discover -s vlass-pilot/tests -v
```

Initial/follow-up acquisitions are already retained and never overwritten. For
the completed follow-up use `pilot.py replay --followup`; do not rerun `fetch`.

Scientific dependencies: numpy, scipy and astropy. Network access is needed only
for `fetch`. No source catalogue is queried and no identifiers are submitted.
