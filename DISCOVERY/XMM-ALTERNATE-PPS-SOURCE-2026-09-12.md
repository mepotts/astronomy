# Official alternate PPS route: XSA AIO, metadata check first

September 12, 2026. Research only. No product HEAD/GET, coordinate query,
scientific array access, installation or account action was performed.
C3 and C3b STOP outcomes remain unchanged.

## Decision

**A documented alternate service exists: ESA XSA AIO.** Its ESA/ESAC-authored
client explicitly uses HTTP HEAD before downloading. The smallest useful next
action is a separately frozen, single anonymous **ATTTSR-filtered AIO HEAD**.
Do not yet repeat the HEASARC requests or acquire an observation bundle.

This resolves the method/endpoint question, not current product availability.
The source demonstrates intended HEAD use; no live response from the product
service was obtained here. It also does not establish that the mirror's 404s
were caused by missing files, method handling, or a transient service problem.

## What is documented

The stable XMM client API gives the canonical HTTPS service:

```text
https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?
```

It documents observation ID and PPS selectors including instrument, exposure
flag/number, product type, subset, source number and extension. **Specify
`level=PPS`**: the default is broader. Its `filename` argument is a local output
name, not an exact remote-file selector; `name` means the six-character product
type such as ATTTSR or EXPMAP.
[Stable XMM API](https://astroquery.readthedocs.io/en/stable/api/astroquery.esa.xmm_newton.XMMNewtonClass.html).

The inspected implementation identifies ESA/ESAC authorship. `_create_link`
builds the AIO query; `_request_link` sends HEAD and examines Content-Type and
Content-Disposition before `download_data` calls the downloader. Thus HEAD is
not an invented service probe. This is client implementation evidence, not a
guarantee of successful HEAD responses or Content-Length today. The inspected
source is astroquery `0.4.12.dev710+g038841faa`; the stable API page is 0.4.11.
[ESA XMM client source](https://astroquery.readthedocs.io/en/latest/_modules/astroquery/esa/xmm_newton/core.html).

The official-client usage example shows filtered PPS retrieval returning a
TAR file. Therefore a selector intended to isolate one PPS product must not be
assumed to return the raw FTZ directly. The observed archive format, member
identity and sizes need validation before extraction.
[XMM archive client examples](https://astroquery.readthedocs.io/en/latest/esa/xmm_newton/xmm_newton.html).

## Concrete selectors, derived from already observed filenames

These are proposals, not executed URLs. Shared fields are `obsno=0884250101`,
`level=PPS`, `sourceno=000`, `extension=FTZ`.

| Expected retained product | Additional documented selectors |
| --- | --- |
| `P0884250101OBX000ATTTSR0000.FTZ` | `name=ATTTSR`, `expflag=X`, `expno=000`, `datasubsetno=0` |
| `P0884250101M2S002EXPMAP8000.FTZ` | `instname=M2`, `name=EXPMAP`, `expflag=S`, `expno=002`, `datasubsetno=8` |

The stable API's listed instrument values do not include OB. Do **not** invent
`instname=OB` support merely because OB appears in the filename. The proposed
ATT query omits that parameter and narrows the other documented fields instead.
Consequently it is a tightly filtered product request, not a verified exact
filename lookup. The desired filename must still be the sole admitted science
member if a later bounded acquisition is authorized.

Proposed first request, exactly:

```text
HEAD https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0884250101&level=PPS&name=ATTTSR&expflag=X&expno=000&datasubsetno=0&sourceno=000&extension=FTZ
```

The MOS2 selector is documented as a possible later alternative, **not** part of
this proposed first request. The adopted pn/MOS1 path already needs attitude
information; restoring MOS2 is not necessary to lower or waive any control gate.

## Smallest next request contract for parent adoption

1. Freeze a new one-request metadata attempt; use the exact ATT URL above and
   the existing tree-aware 30-second bound, 5/15-second socket timeouts, fresh
   anonymous session, disabled environment credentials/proxies, no redirects,
   retry, cookies, Range or response-body reads. Do not run the convenience
   downloader: its additional calls/cache behavior are not this one-request
   contract.
2. Require HTTP 200 and exact final URL. Parse bounded safe headers and an
   unambiguous positive Content-Length no larger than 2 MiB. Absent length,
   text/error response, redirect, authentication demand, or an oversized entity
   gives a named STOP/incomplete result. An absent length is not evidence of an
   absent product. No fallback GET is implied.
3. Add narrowly parsed **Content-Disposition filename metadata** to the previous
   safe-header scheme, since the documented client relies on it. Bound the
   field; accept only a safe basename and never log cookies, arbitrary response
   headers or unchecked header text. Record whether the advertised entity is
   the expected FTZ or a package; do not describe a package's Content-Length as
   the size of its embedded compressed FITS file.
4. A successful HEAD establishes only a bounded advertised response. If it is
   an archive, freeze an explicit subsequent package contract before GET:
   bounded streaming, exact allowed member name, no path traversal/links/devices,
   no automatic extraction, and separate package/member/decompression limits.
   Extra science members, unknown packaging or unresolved identity stop that
   stage. Do not use a fully trusted TAR extraction policy. Header-only
   validation of the admitted product still precedes any attitude/map arrays.

The 2-MiB metadata eligibility ceiling above is prospective, not inferred from
HEASARC's rounded 148K listing or a measured XSA entity. A new ESA copy may use
different packaging or processing from the mirror; establish its identity and
compatibility independently rather than expect identical compressed hashes.
No wider PPS/ODF bundle is needed to test this route.

## Research/access limits

Two targeted search batches were used. The client source and stable API pages
were successfully opened; the example page's relevant text was returned by
search. Direct attempts to read the NXSA AIO help page, the Cosmos archive page
and the historical 2014 AIO PDF failed respectively with a tool safe-open error,
HTTP 451, and a fetch timeout. None was retried, and no restriction was bypassed.
Their failure was not treated as evidence that the product endpoint fails.

No undocumented direct `data-action` product arguments, remote `filename`
parameter, HEAD-to-GET workaround, or alternative mirror path is recommended.
If the proposed AIO HEAD cannot establish a bounded entity, the precise next
missing evidence is its documented packaging/length behavior or exact-file
selection contract—not a need for a broad literature search.
