# RXJ M5 continuation decision: fresh bounded transfer, no splice

2026-09-13. Proposal for parent adoption, not authorization to issue a request.
No private partial bytes were opened or interpreted for this note. No acquisition
or replay was run, and no frozen M5 file was changed.

## What actually stopped

The [retained outcome](XMM-RXJ-M5-2026-09-13-data/outcome.json), SHA256
`9eb6912a34cabdfad6c5da42d751e7be25c249ed72ec2910f194bdbca59119bb`,
records worker return code 124, parent STOP_INTERNAL, assessment_completed=false,
PN UNVERIFIED_ATTEMPT and both MOS slots NOT_ATTEMPTED. All three additional
header-pass started/completed pairs are false. No worker completion, expanded
product or private header report exists in the outcome artifact inventory.

The frozen worker source is SHA256
`e8597327a7cbe4f6ca975d88d2e4b2584fef1afa21a4bf16c388daa046be2b12`;
its audited tree deadline helper returns 124 after its 300-second deadline. This
supports a hard worker deadline, not a diagnosed archive error, rate limit,
network outage, socket inactivity timeout or scientific failure. Parent
STOP_INTERNAL is the preserved terminal assessment label, not a causal diagnosis.

The PN file's filesystem length is 28,311,552 bytes (27 MiB). Its hash, copied from
the outcome rather than recomputed here, is
`8e5e6b07f836967030e05594d519527829c7ea4429c442a21317d0f8a81f233d`.
That is known retained length, not an exact count of bytes received on the wire or
an EOF declaration. Additional in-flight/buffered work at termination is unknown.
The [HTTP receipt](XMM-RXJ-M5-2026-09-13-data/slot-1-http.json), SHA256
`9defa91737820d025299806875c86b81d9aa8c989eed4786851f065bdc29af33`,
records 200, image/fits, exact URL and filename, but no Content-Length, ETag or
Last-Modified. The Date field is not a representation identity validator.

## Do not append a Range response to this partial

HTTP permits range requests but does not guarantee server support. Safe combining
of partial responses requires the same strong validator; If-Range cannot use a
weak entity tag, and a date requires the standard's strong-validator conditions.
No such validator was retained for this PN representation. A future 206 with an
offset, the same filename or a new ETag would not establish the identity of the
already retained prefix. Its local hash is not a server validator. Therefore do
not request a suffix, append to the partial, infer total size, or claim resume
safety. Preserve the original partial and STOP as evidence. This is a conclusion
about this record, not a claim that ESA never supports Range.
[RFC9110 §13.1.5](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.5),
[§15.3.7.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.7.3).

## Smallest useful next stage

Adopt a separately named M6 directory and exact-byte frozen contract. Reuse the
reviewed M5 mechanics as an explicitly isolated adapter where straightforward;
never launch M5 again, alter its files, or invoke its historical worker/plan as a
new request. Bind M5 outcome/HTTP/source/tests/protocol and original M4 decision.
The partial remains in M5; M6 starts fresh exclusive files and does not read it.

1. Make at most the same three complete anonymous GETs in PN/M1/M2 order with
   exactly the M5 URLs and names. Stop on first failure; retain all three slot
   states. No HEAD, Range, If-Range, redirects, retry, new selector or bundle.
2. Allow one 7,200-second tree-bounded worker for the whole batch. Use a separate
   7,140-second cooperative worker deadline to leave a 60-second reporting margin;
   margin is not another transfer allowance. Keep separate 300-second cooperative
   parent and explicit replay header/hash passes, with their existing partial
   verification accounting. Socket connect/read timeouts remain 5/15 seconds.
3. Retain all existing byte, expansion, memory, disk, JSON/reserve, identity,
   privacy and header-only gates: 256 MiB raw/file, 512 MiB raw/batch, 1 GiB expanded/file,
   2 GiB expanded/batch, 500,000,000-byte monitored peak, 4 GiB fresh free space,
   10 MiB aggregate JSON and 256 KiB terminal reserve. Missing Content-Length remains
   allowed only with locally bounded complete EOF; no guessed validators.
4. Use 64 KiB maximum network read requests rather than 1 MiB to make returned-byte
   checkpoints more granular; retain cap+1 and honest partial/unknown counters.
   Local copy/decompression chunks can remain 1 MiB. This is not a claim of faster
   transport. No new telemetry framework or per-chunk durable ledger is needed.
5. Preserve raw timeout 124 separately and explicitly classify a missing worker
   completion after 124 as a hard-deadline STOP in M6. Do not back-edit M5's label.
   Run finite synthetic tests for separate deadlines, 64 KiB reads/cap+1, timeout
   partial retention, no reuse of M5 paths, and inherited safe receipts/replay.
   Freeze exact bytes before one dispatch. A further failure is a new STOP, not
   permission for another automatic retry or larger cap.

The time allowance is an engineering decision, not outcome-threshold tuning.
27 MiB retained over the full 300-second worker budget gives a crude 0.09 MiB/s
end-to-end progress ratio, including overhead and unknown buffering. At that
ratio the 512 MiB raw batch cap would take about 5,689 seconds (94.8 minutes); a 2-hour
bound offers finite margin. Actual total sizes and future throughput are unknown,
so this neither forecasts completion nor proves that the maximum-sized batch
will fit. Increasing only the socket read timeout would not address the observed
tree deadline.

Requests documents its read timeout as an interval waiting for incoming data,
not a whole-download wall-clock limit. Streaming exposes the undecoded raw body;
urllib3's sized reads can collect data before returning a block. Thus a longer
transfer can legitimately outlast 15 seconds while still hitting an independent
300-second worker limit. These API semantics are compatible with the observation,
not evidence of its exact underlying cause. The owner runtime reports
requests 2.34.2 and urllib3 2.7.0.
[Requests timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts),
[urllib3 response read/stream](https://urllib3.readthedocs.io/en/stable/reference/urllib3.response.html#urllib3.response.HTTPResponse.read).

The strongest subsequent success remains retained, authenticated event-product
headers only. No photon values, calibration rows, exposure maps, counts,
pn-plus-MOS eligibility, clean negative controls or discovery are established by
this acquisition. All scientific gates and previous STOPs remain unchanged.

## Parent disposition

Root read this complete proposal, the retained public receipts and the cited
primary HTTP/streaming documentation. Adopt a separate fresh M6 attempt with
the proposed larger finite time budget, unchanged science/identity/byte gates
and smaller network chunks. Do not reuse or overwrite the M5 partial; no range
identity has been established. A tested isolated adapter may reuse pinned M5
mechanics only after rebinding all state and paths to M6, never dispatching the
original M5 CLI or its original directory. Final source/protocol review and
exact-byte freeze remain prerequisites to that new dispatch. This decision
does not retrospectively change M5 or authorize an automatic retry loop.
