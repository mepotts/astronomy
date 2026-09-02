# SPHEREx pilot

This directory contains an aggregate-only M0 kill check for the only SPHEREx use case that
survived the existing `dyson-revet` results: a narrowly selected 3–5 micron warm-component test.

## Outcome — BLOCKED at the outbound-query gate; scientifically NARROW/PIVOT

The broad project is killed. The 223 fitted excess temperatures span only 100–283 K, while
SPHEREx stops at 5 microns. At 4.8 microns the catalogue's median model excess is 0.0158 microJy
and its 90th percentile is 0.703 microJy. The existing warm-window extractions give a conservative
5-sigma floor of 139.17 microJy. **Only one of 223 rows clears it** (161.20 microJy); the second is
13.46 microJy. A catalogue-wide extraction would therefore spend almost all its effort measuring
photospheres, not the fitted excesses.

The coordinate-free live check passed:

- the current [IRSA mission page](https://irsa.ipac.caltech.edu/Missions/spherex.html) exposes QR2;
- the official [Spectrophotometry Tool](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html)
  already supplies research-ready Tractor forced photometry, so forced photometry itself is not
  novelty;
- the anonymous IRSA TAP schema and the
  [AWS QR2 Level-2 bucket](https://registry.opendata.aws/spherex-qr/) were live.

Exact downloaded bytes are gitignored; their URL, byte count, and SHA-256 are in
[`out/m0_result.json`](out/m0_result.json). **Zero coordinate-bearing requests were sent.** The
target ranking is reproducible from the pre-existing tracked `dyson-revet` catalog and this
tracked ranking code; this pilot does not claim that those target identities are secret.

The formal verdict remains **BLOCKED** because the frozen positional-coverage gate would send a
six-row target/control payload to IRSA. The exact unblock action is explicit approval for
those six anonymous TAP coverage queries. If they pass, the next experiment is only the leading
warm-tail row, one nearby photospheric control, and the second-ranked subthreshold falsifier in
official-tool D5+D6 runs. No broader SPHEREx scan is recommended.

The frozen protocol is in [`M0-PROTOCOL.md`](M0-PROTOCOL.md). The exact outbound manifest, the
three matched-control identities, service payloads, and any future spectra are gitignored. The
leading target ranks remain reconstructible from the already tracked upstream catalog. The
tracked result adds aggregate feasibility evidence only.

Run locally from the repository root:

```powershell
python spherex-pilot/scripts/m0_pilot.py manifest
python spherex-pilot/scripts/m0_pilot.py public-probe
python -m unittest discover -s spherex-pilot/tests -v
```

The default `public-probe` performs coordinate-free anonymous reads of the official IRSA
schema/documentation and an AWS S3 listing. It sends no private position anywhere. The separate
`probe` command adds six coordinate-bearing IRSA coverage queries and must not run without explicit
approval for that outward payload. It also fails closed unless
`--authorize-private-manifest-sha256` exactly matches the locally prepared six-row manifest, so an
approval cannot silently carry over to a changed payload. Neither command launches a
Spectrophotometry Tool job.
