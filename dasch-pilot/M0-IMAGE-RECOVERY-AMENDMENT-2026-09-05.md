# Exploratory known-event image recovery amendment

This separate feasibility check is specified **after** the original six images
and the new control light curves were inspected, and **before** any images below
were retrieved. It does not change the failed frozen nearest-epoch image test.

The first V404 Cyg event plate was too shallow (field B limit 10.847). Two clean
light-curve detections occur in the published 1938 outburst. Use this information
only to test whether known-event image recovery is possible on a better plate.

Fixed selection: take the **earliest** clean detection in JD [2429190,2429250],
then select adjacent non-detection light-curve rows from the **same series** with
finite local limiting magnitude at least 0.5 mag fainter than that event's
measured magnitude. Pre-event: latest row before JD2429100 within 365 days;
post-event: earliest after JD2429400 within 365 days. Join exact plate, mosaic,
and solution identity to WCS-solved exposure metadata. Resolve ties by plate and
solution. If no exposure survives, report the missing control; do not loosen
depth, time, or series criteria. At most three additional cutout requests.

Acceptance requires visual source presence during the event, absence on both
adjacent images of adequate depth, no obvious WCS mismatch or confounding blend,
and a credible comparison of neighboring stars. This is an exploratory
known-control recovery, not validation of unknown-source precision. Any apparent
pass would advance only to a separate held-out control study. Preserve both the
original failure and this exploratory result.
