# XMM C0c: one public control-directory listing

Prospective metadata-only operation, 2026-09-12. The previous C0b-1 schema STOP
remains unchanged. Official HEASARC archive documentation and the independently
read parent directory expose this exact PPS link for published observation
0884250101:

`https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/`

Authorize exactly one anonymous GET of that directory index, not any linked
photon, light-curve, image, archive or other product. At most 262144 retained
response bytes, with one extra read byte permitted to detect overflow, no
redirects or retries, socket timeouts 5/15 seconds and the existing audited
process-tree helper's 30-second worker deadline. Cleanup has its own allowance.
No install, credentials, cookies, private coordinates or remote processing.
A fresh HTTP session disables environment/netrc authentication and proxies,
starts without authentication/cookies and does not follow redirects.

Freeze the worker/protocol/tests before the first request; preserve exclusive
parent and worker attempt markers, source/protocol/helper hashes, complete or
partial response body, HTTP status, a safe allowlist of response headers and
explicit worker/parent outcomes. Never retain Set-Cookie or authentication
headers. One local protocol snapshot permits later narrative additions without
changing executed rules. Failure does not authorize a second request.

The transport can report only HTTP_INDEX_RETAINED or STOP, not product or science
acceptance. Offline inspection must verify the directory identity, product names,
public same-directory links and size syntax. Preserve missing, ambiguous and
rounded sizes; a human-readable K/M directory size is not an exact byte count.
No Python lexicographic-equivalence requirement is imposed on archive row order.
Do not infer usable camera modes, good-time overlap, event contents or discovery
readiness from a directory listing. Further metadata or photon requests require
their own explicit selection and resource contract.

Source: XMM-C0c-2026-09-12-data/listing.py. Raw metadata and receipts stay in that
directory. The parent accepts the independently reviewed transport for this one
request after its tests pass. This is a local prospective record, not public
preregistration. The broader goal is a size-verified published-control bundle,
not making this diagnostic return a favorable status.
