# Quarantine variant, before any held-out curves

The original strict run stopped after the Feige34 exposure request: seven of
2,339 clean detections have inconsistent exposure numbers despite matching the
four-part imaging key (six 0 versus 1; one 2 versus 0). The cause is unresolved;
these are not uniformly offset numbering conventions. No corrected values are
invented. Original strict behavior, specification and response bundle remain.

Freeze a separately named `--quarantine-conflicts` variant: exclude and count
every exposure-number conflict, never use its photometry, and stop expansion if
conflicts exceed 2% of clean detections in any star. This is a quality exclusion
chosen from metadata, before held-out curves or matched-window outcomes. All
other gates and thresholds remain unchanged. Reuse the exact first response,
bound to its existing manifest hash; at most 23 further requests. Store new
results separately with both spec and amendment hashes. Strict mode still raises.

Official [daschlab documentation](https://daschlab.readthedocs.io/en/latest/_modules/daschlab/photometry.html)
acknowledges some detections cannot reliably be linked to exposures; this does
not identify the cause of these specific seven conflicts. Missing joins and
conflicts are reported separately. This amendment is not evidence that the
unmodified experiment passed.
