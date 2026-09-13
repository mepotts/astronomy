# RXJ M2: bounded raw summary HTML, unadjudicated

Prospective and unexecuted. Adopt [M1 next-step decision](XMM-RXJ-M1-NEXT-2026-09-13.md)
without changing M1's STOP or interpreting its wildcard as a download target.

Exactly one anonymous GET:

```text
https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0851180501&level=PPS&name=SUMMAR&extension=HTM
```

No HEAD, redirects, retries, Range, environment authentication/proxies, cookie
reuse, links, packages or products beyond this raw metadata HTML. Fresh session,
auth=None, trust_env=False, cleared cookies, identity encoding; socket timeouts
5/15 seconds, reviewed helper process-tree deadline30 seconds. HTTP parser limits
65,536 bytes/line and100 headers. Raw retention262,144 bytes plus one unretained
overflow byte. Complete EOF is an exclusive transport receipt, not a semantic
completeness assertion. Missing EOF receipt means not confirmed, including interruption.

Require HTTP200/exact final URL, text/html and absent/identity encoding before
body reads. Safe headers use six inherited names, each exactly one ASCII value
of at most1,024 characters; duplicates or controls stop before unsafe text is
persisted. Optional Content-Length: positive decimal, at most9 digits, within
raw cap and equal complete received bytes. No invented validator. Missing length
uses the local cap. Missing disposition is allowed. Disposition is at most one
ASCII value of2,048 characters, inline/attachment with optional single filename
(quoted or unquoted); extended/unknown parameters and duplicates stop. If named,
require PPS positions `P0851180501` + two instrument characters + one exposure
flag + three exposure digits + `SUMMAR` + four subset/source characters + `.HTM`.
Instrument/flag/subset characters are uppercase alphanumeric (flag a letter).
No particular unobserved instrument/exposure is selected. Package names fail.
Only classification, kind and accepted filename SHA256 are retained, never raw
Content-Disposition. This cannot replay the discarded raw-header parser; it
replays safe classification receipts. Wrong final URLs are recorded only as a
boolean mismatch, never arbitrary URL text.

HTML goes to locally ignored summary.html before execution, never browser-opened
or rendered. No content, contacts or coordinates appear in public receipts or
logs. No literal footer, table schema or observation-identity gate is imposed.
Even an HTML error page can reach SUMMARY_HTML_RETAINED_UNADJUDICATED; offline
adjudication remains required. The summary is a metadata fetch; the renamed
science_products_fetched counter remains zero. No modes, exposure, inventory,
accessibility, clean-control or discovery claim follows.

Use a fresh verified-buffer M0 module, exactly six body-filename substitutions,
one allowlist insertion for .gitignore and three counter-name substitutions.
Override only paths/config, binding, bounded save, HTTP/disposition collection,
safe receipt checks and transport-only interpretation. Inherited exclusive
attempt/worker markers, safe exception schemas, parent subprocess, return-code
validation, artifact closure and read-only replay remain active. No prior-stage
worker is launched: the inherited worker runs only with isolated M2 paths and
configuration. No old HTML semantic parser is called. Each JSON receipt≤65,536 bytes; aggregate≤1MiB with
64KiB reserved for outcome.json. Body budget is separate. All partials remain.
Parent output is length/hash only. Bind M0 source/tests/protocol/helper lineage,
M1 source/tests/outcome/body, adopted LF note, new source/tests/protocol/runtime,
and local privacy/attributes files. Root must preserve protocol and note LF.

Before exact-byte freeze: mocked anonymous one-GET success, EOF versus partial,
HTML MIME/packaging/disposition/length rejection, overflow, reserved terminal
receipt, safe logs, module isolation, dependency binding, no retry, immutable
offline replay and changed receipt rejection must pass. No actual requests,
scientific product opens or semantic HTML inspection are authorized by this
implementation. Subsequent offline adjudication must be separately identified.
