# DATA-SOURCES — TAP endpoints, schema introspection, ADQL, parsers

Facts verified via web research, current to **June 2026**. All target endpoints below are
**public and anonymous — no account, token, or auth required** for the read/query operations
we need. Each entry notes the one practical limit that matters (sync row caps, result retention).

---

## 1. Target TAP endpoints (base URLs)

A TAP "base URL" is the root; clients append `/sync`, `/async`, `/tables`, etc. PyVO and
astroquery handle that for you — you pass the base URL to `TAPService(...)`.

| Archive | TAP base URL | Notes / quirks | Auth |
|---|---|---|---|
| **Gaia (ESA)** | `https://gea.esac.esa.int/tap-server/tap` | DR3 + DR4. Sync queries capped at **2000 rows** — use async for more. Anonymous async results retained **3 days**. Schema names like `gaiadr3.gaia_source`. | None |
| **VizieR (CDS)** | `https://tapvizier.cds.unistra.fr/TAPVizieR/tap` | Hosts ~tens of thousands of catalogs; table names are catalog-coded (e.g. `"I/355/gaiadr3"`, quoted, slash-delimited). UCD-rich. Older host alias `tapvizier.u-strasbg.fr` still redirects. | None |
| **MAST (STScI), CAOM** | `https://mast.stsci.edu/vo-tap/api/v0.1/caom` | CAOM = Common Archive Observation Model (HST/JWST/TESS footprints & observations). ObsCore-style columns (`s_ra`, `s_dec`, `s_region`, `t_min`...). Other MAST TAP services exist (`/tic`, `/missionmast`). | None |
| **DESI (via NOIRLab Astro Data Lab)** | `https://datalab.noirlab.edu/tap` | Single TAP service exposing many schemas; select schema **`desi_dr1`** (or `desi_edr`). DESI has **no first-party TAP** — NOIRLab Data Lab is the canonical public TAP route. | None (anonymous public access) |

> Rubin DP1 (mentioned in the dossier for later milestones) is served via the Rubin Science
> Platform TAP, which **does** require an RSP account — out of scope for the no-auth v0/M1.
> Start with the four anonymous endpoints above.

A neutral practice/sandbox endpoint also exists — GAVO's **`http://dc.g-vo.org/tap`** — handy
for offline-ish development and used as the example in the PyVO docs.

---

## 2. Introspecting the schema (TAP_SCHEMA)

TAP services are self-describing. Every compliant service exposes a `TAP_SCHEMA` schema whose
tables describe the service's own tables and columns. Two equivalent ways to read it with PyVO:

**(a) The `.tables` property** — convenient, returns a dict-like of table metadata:

```python
import pyvo as vo

svc = vo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")

# names of all queryable tables
table_names = list(svc.tables.keys())

# human-readable dump of tables + columns
svc.tables.describe()

# per-column metadata for one table
for col in svc.tables["gaiadr3.gaia_source"].columns:
    print(col.name, col.description, col.unit, col.datatype, col.ucd)
```

**(b) Query `TAP_SCHEMA.columns` directly with ADQL** — works everywhere, gives you exactly the
five fields the linter needs (name, description, unit, datatype, UCD):

```python
rows = svc.search("""
    SELECT table_name, column_name, description, unit, datatype, ucd
    FROM TAP_SCHEMA.columns
""").to_table()
```

The linter's **schema resolver** caches this (per endpoint) to a local JSON store so it does not
re-hit the service on every lint. Cache key = endpoint URL; refresh on demand.

Key `TAP_SCHEMA` tables: `TAP_SCHEMA.schemas`, `TAP_SCHEMA.tables`, `TAP_SCHEMA.columns`,
`TAP_SCHEMA.keys` + `TAP_SCHEMA.key_columns` (**the latter two declare foreign keys — that is how
we know the legitimate JOIN keys between tables**, central to the "missing JOIN key" diagnostic).

---

## 3. ADQL geometry essentials (ADQL 2.1)

ADQL = SQL + spherical-geometry extensions. The spatial functions are where generic Text-to-SQL
tools fail and where most user errors live. The ones the linter must understand:

- **`POINT('ICRS', ra, dec)`** — a position; first arg is the coordinate frame (often `'ICRS'`).
- **`CIRCLE('ICRS', ra_c, dec_c, radius_deg)`** — a cone (frame, centre RA, centre Dec, radius in degrees).
- **`BOX('ICRS', ra_c, dec_c, w_deg, h_deg)`** and **`POLYGON('ICRS', ra1, dec1, ...)`** — other regions.
- **`CONTAINS(geom_inner, geom_outer)`** — returns 1 if inner is inside outer, else 0.
- **`INTERSECTS(geom1, geom2)`** — returns 1 if the regions overlap.
- **`DISTANCE(POINT(...), POINT(...))`** — angular distance in degrees between two points.

Canonical cone-search predicate (this exact shape is what a correct positional query looks like):

```sql
WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 34.0, 45.0, 0.1)) = 1
```

**Linter rule that follows directly:** if the FROM table has spatial columns (RA/Dec, detectable
by UCDs `pos.eq.ra` / `pos.eq.dec`, or by name) and the query has **no `CONTAINS`/`INTERSECTS`/
`DISTANCE` constraint and no narrow positional WHERE**, warn "no spatial constraint — this is a
full-catalog scan." That single check is the highest-value, always-correct diagnostic we ship.

ADQL also has the usual `TOP n`, `WHERE`, `JOIN ... ON`, `ORDER BY`, plus math/string functions.
Reference: IVOA ADQL 2.1 — https://www.ivoa.net/documents/ADQL/ (spec repo: https://github.com/ivoa-std/ADQL).

---

## 4. Reusable ADQL parser options

| Option | What it is | Fit for us | Verdict |
|---|---|---|---|
| **`queryparser-python3`** (aipescience) | ANTLR4-based ADQL→PostgreSQL **translator**; class `queryparser.adql.ADQLQueryTranslator`, `.to_postgresql()`. Apache-2.0. PyPI wheel ships pre-generated parser; **runtime dep is only `antlr4-python3-runtime` (pure Python — no Java at runtime)**. Java/ANTLR needed only to regenerate the grammar from source. Understands geometry funcs (e.g. `POINT('ICRS', ra, de)`). | It already has a real ADQL grammar and, as a side effect of translating, surfaces the **table/column references** and rejects syntactically invalid ADQL — which is exactly the parse + extract-identifiers step the linter needs. We ignore its PostgreSQL output. | **Primary.** Reuse for parse + identifier extraction; do NOT depend on its pg_sphere translation. |
| **`lark` / hand-rolled grammar** | Write a small ADQL subset grammar in `lark` (pure-Python PEG/LALR). | Full control, no ANTLR baggage, easy to emit our own AST. More work; must keep grammar current with ADQL 2.1. | **Fallback / escape hatch** if `queryparser` proves brittle on real Gaia/VizieR queries or its AST is awkward to walk. |
| **`sqlparse`** | Generic non-validating SQL tokenizer. | Tokenizes but does **not** understand ADQL geometry or validate structure. | Reject as core parser; possibly useful for cheap pretty-printing only. |
| TOPCAT/STILTS ADQL parser (Java) | Mature, embedded in TOPCAT. | JVM dependency; wrong language for a Python tool. | Reject (reference only). |

**Decision:** primary = `queryparser-python3` for grammar + identifier extraction; `lark` kept as a
documented fallback. Either way, **schema resolution and all lint rules are our own deterministic
code** layered on top of the parse tree — the parser only tells us "is this valid ADQL and what
names does it reference"; the live `TAP_SCHEMA` tells us "do those names exist."

---

## 5. Minimal access example (pyvo + astroquery)

```python
# pip install pyvo astroquery
import pyvo as vo

# --- generic, works for Gaia / VizieR / MAST / DESI by swapping the URL ---
svc = vo.dal.TAPService("https://gea.esac.esa.int/tap-server/tap")

# 1) introspect schema (cache this locally)
cols = svc.search(
    "SELECT table_name, column_name, datatype, unit, ucd "
    "FROM TAP_SCHEMA.columns"
).to_table()

# 2) run a real (small) query — note TOP to respect the 2000-row sync cap
res = svc.search("""
    SELECT TOP 10 source_id, ra, dec, parallax, ruwe
    FROM gaiadr3.gaia_source
    WHERE parallax_over_error > 10 AND ruwe < 1.4
      AND CONTAINS(POINT('ICRS', ra, dec),
                   CIRCLE('ICRS', 45.0, 0.0, 0.5)) = 1
""")
tbl = res.to_table()   # astropy Table -> .to_pandas() if desired

# astroquery alternative for Gaia specifically (handles async + login if ever needed):
#   from astroquery.gaia import Gaia
#   job = Gaia.launch_job_async("SELECT TOP 10 ... FROM gaiadr3.gaia_source ...")
#   tbl = job.get_results()
```

For >2000 rows on Gaia (or any large pull), use **async**: `svc.submit_job(adql)` → `job.run()` →
poll `job.phase` → `job.fetch_result()`. v0/M1 only need sync + small `TOP n` previews.

---

## Sources

- PyVO DAL docs (TAPService, `.tables`, `TAP_SCHEMA`, `.search()`): https://pyvo.readthedocs.io/en/stable/dal/index.html
- Gaia TAP endpoint + sync 2000-row cap + 3-day anonymous retention: https://gea.esac.esa.int/tap-server/tap and https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access
- Gaia ADQL geometry how-to: https://www.cosmos.esa.int/web/gaia-users/archive/writing-queries
- VizieR TAP: https://tapvizier.cds.unistra.fr/adql/about.html
- MAST TAP services index (CAOM): https://mast.stsci.edu/vo-tap/
- DESI via NOIRLab Astro Data Lab TAP (`desi_dr1`): https://datalab.noirlab.edu/data/desi and https://datalab.noirlab.edu/docs/manual/UsingAstroDataLab/DataAccessInterfaces/CatalogDataAccessTAPSCS/CatalogDataAccessTAPSCS.html
- ADQL 2.1 spec + geometry functions: https://www.ivoa.net/documents/ADQL/ and https://github.com/ivoa-std/ADQL
- queryparser (ADQL→PostgreSQL, ANTLR, Apache-2.0): https://github.com/aipescience/queryparser and https://pypi.org/project/queryparser-python3/
- antlr4-python3-runtime (pure-Python runtime, no Java): https://pypi.org/project/antlr4-python3-runtime/
