# XMM C0c2 result: complete control-directory inventory

The single amended metadata GET succeeded on September 12 at 23:11:35 UTC:
HTTP 200, 319808 retained bytes, worker exit 0, parent elapsed 0.75 s. The
offline parser accepts 2193 unique file entries. **No photon product was fetched
and no scientific recovery or discovery has been demonstrated.** The earlier
[C0c cap failure](XMM-C0c-RESULT-2026-09-12.md) remains unchanged.

The [cap-only protocol](XMM-C0c2-2026-09-12.md), wrapper and tests were committed
in `ed02303` before execution; final independent review was committed in
`89a8f4f`. The executed protocol snapshot is the immutable authority. The
[pre-execution review](XMM-C0c2-REVIEW.md) covers seven amendment and six parser
tests. Parent also reran the twelve original transport tests: 25 total passed,
with Ruff and root repository checks passing. These are software checks, not
scientific validation.

## Observed products, not inferred availability

The complete retained [public directory](https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/)
contains these specific files. Sizes below are the archive's rounded displays,
**not independently verified entity lengths or expanded FITS sizes**.

| File | Displayed size | Role |
| --- | --- | --- |
| `P0884250101PNS003PIEVLI0000.FTZ` | 104M | pn imaging event list |
| `P0884250101M1S001MIEVLI0000.FTZ` | 7.3M | MOS1 imaging event list |
| `P0884250101M2S002MIEVLI0000.FTZ` | 9.5M | MOS2 imaging event list |
| `P0884250101EPX000OBSMLI0000.FTZ` | 118K | EPIC source list |
| `P0884250101OBX000SUMMAR0000.HTM` | 49K | Observation summary metadata |
| `P0884250101OBX000PINDEX0000.FTZ` | 114K | Product index metadata |

Product-type interpretation follows the [ESA PPS filename specification](https://xmm-tools.cosmos.esa.int/external/xmm_user_support/documentation/dfhb/pps.html).
An imaging filename does not establish a supported submode, valid times/GTIs,
camera overlap, usable control counts or sufficient calibration products.
This is a complete parsed representation of the returned index, not a claim
that the server inventories every possible product of the observation.

## Provenance and boundary

- Response SHA-256: `97f9372b999b354ebcbff51a4b42af885433de598795a6a58656ef1e09bac258`.
- [Generated inventory](XMM-C0c2-2026-09-12-data/inventory.json) SHA-256:
  `6ddb4a357439922dbefaa51e365b53802e6d031d079348706274555f4e063c23`.
- [Outcome and artifact hashes](XMM-C0c2-2026-09-12-data/outcome.json) bind the
  transport source, protocol snapshot, HTTP receipt, markers and response.
  Inventory parsing verifies every listed artifact before consuming the index.
- Every inventory `exact_bytes` remains null, including unsuffixed integer
  displays. No guessed product size has entered an acquisition budget.
- Raw index whitespace is retained byte-for-byte. Root Git attributes classify
  these exact raw HTTP bodies as non-source diffs; no normalization was applied.
  An initial multi-command PowerShell commit continued after the raw-whitespace
  check failed. Subsequent commands explicitly stop on nonzero status, and the
  complete branch whitespace check passed after the raw/source classification.

Next: a separately specified metadata batch can HEAD the four listed scientific
inputs and GET the small observation summary. It must not fetch event bodies.
This will establish advertised compressed lengths and potentially camera modes;
missing facts remain explicit. The [counts-recovery draft](XMM-CONTROL-RECOVERY-DRAFT-2026-09-12.md)
is not yet an adopted or executable science protocol. Expanded-size, timing,
exposure, screening and background requirements remain unresolved before a
bounded photon acquisition and known-control measurement.

ITF notification settings are unchanged. Its daily archive and existing-queue
watch are not fresh daily discovery searches; no dedicated SMS/email delivery
has been configured or tested. Overall discovery work remains active.
