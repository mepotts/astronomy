"""M33: resolve every cited reference's bibliographic details from CrossRef.

The contrast-wall note's pre-submission item 6 asks for journal, volume and bibcode on four
references that are currently cited from archived full texts. The obvious tool is ADS, and ADS
needs an API token this machine does not have -- its API returns "Missing Authorization" and
its web interface is a JavaScript application that a fetch cannot read.

CrossRef needs no token and holds the same fields for anything with a DOI: journal, volume,
page, year, and the DOI itself. That covers item 6 completely. What it does NOT hold is the ADS
bibcode, which is an ADS-specific identifier; where a bibcode is genuinely wanted it still needs
a human with an ADS session, and that is stated rather than papered over.

Every match is printed with its CrossRef relevance score AND the queried title, so a wrong
match is visible rather than silently adopted. Nothing here rewrites a reference automatically:
this project has already shipped fifteen wrong citations, and an automatic rewriter would be a
sixteenth waiting to happen.

Usage: python scripts/m33_resolve_refs.py
"""
import io
import json
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "matthew.e.potts@gmail.com"        # CrossRef's polite pool wants a contact
UA = {"User-Agent": f"exosat-rv/0.1 (mailto:{MAILTO})"}

# DOI-first. CrossRef's bibliographic search is unreliable for A&A -- it returned an
# encyclopedia entry for one query and a 1988 symbiotic-star paper for another -- so any
# reference whose DOI is already verified is looked up by DOI, which is exact. Title search
# is the fallback and its result is always printed for eyeballing.
#
# ⚠ A DOI lookup is exact only if the DOI is VERIFIED. Two entries here were first filled
# from memory: one happened to be right and the other silently resolved to a different 2014
# A&A paper by another author, reported as "[by DOI - exact]" because the lookup succeeded.
# It is the printed TITLE that catches that, not the DOI mechanism. Every DOI below now
# traces to an archived copy, a verified reference list, or a match whose title was read.
KNOWN_DOI = {
    "Neuhauser+2011":  "10.1111/j.1365-2966.2011.19139.x",
    "Bohn+2020":       "10.3847/2041-8213/aba27e",
    "Viswanath+2023":  "10.1051/0004-6361/202346154",
    "Langlois+2021":   "10.1051/0004-6361/202039753",
    "Lazzoni+2020":    "10.1051/0004-6361/201937290",
    "Lazzoni+2022":    "10.1093/mnras/stac2081",
    "Vanderburg+2021": "10.3847/2041-8213/ac33b4",
    "Vanderburg+2018": "10.3847/1538-3881/aae0fc",
    "Ruffio+2023":     "10.3847/1538-3881/acb34a",
    "Macias+2026":     "10.3847/1538-3881/ae421c",
    "Kohler+2025":     "10.1051/0004-6361/202553919",
    "Dorn+2023":       "10.1051/0004-6361/202245217",
    "Speagle+2020":    "10.1093/mnras/staa278",
}

# (short key, bibliographic query, what the repo currently claims)
REFS = [
    ("Neuhauser+2011", "Further deep imaging of HR 7329 A eta Tel A and its brown dwarf "
     "companion B", "MNRAS 416, 1430"),
    ("Bohn+2020", "Two directly imaged sub-stellar companions to the young star "
     "TYC 8998-760-1", "cited from archived text"),
    ("Bonnefoy+2014", "Physical and orbital properties of beta Pictoris b",
     "cited from archived text"),
    ("Viswanath+2023", "HIP 81208 a compact hierarchical quadruple system "
     "brown dwarf companion", "cited from archived text"),
    ("Langlois+2021", "SPHERE infrared survey for exoplanets SHINE III "
     "observations description data reduction", "cited from archived text"),
    ("Lazzoni+2020", "The search for disks or planetary objects around directly imaged "
     "companions a candidate around DH Tauri B", "A&A 641, A131"),
    ("Lazzoni+2022", "Detectability of satellites around directly imaged exoplanets "
     "and brown dwarfs", "MNRAS 516, 391"),
    ("Vanderburg+2021", "First Doppler Limits on Binary Planets and Exomoons in the "
     "HR 8799 System", "ApJL 922, L2"),
    ("Vanderburg+2018", "Exomoons transit timing variations Kepler", "AJ 156, 184"),
    ("Ruffio+2023", "Detecting exomoons from radial velocity measurements of "
     "self-luminous planets HR 7672 B", "AJ 165, 113"),
    ("Macias+2026", "First Astrometric Limits on Binary Planets and Exomoons Orbiting "
     "beta Pictoris b", "AJ 171, 197"),
    ("Kohler+2025", "viper Velocity and IP EstimatoR", "A&A 698, A44"),
    ("Wahhaj+2011", "The Gemini NICI Planet-Finding Campaign discovery of a substellar "
     "companion CD-35 2722", "ApJ"),
    ("Speagle+2020", "dynesty a dynamic nested sampling package for estimating Bayesian "
     "posteriors and evidences", "MNRAS 493, 3132"),
    ("Dorn+2023", "CRIRES+ on sky performance high resolution infrared spectrograph",
     "A&A 671, A24"),
]


def by_doi(doi):
    req = urllib.request.Request("https://api.crossref.org/works/" + doi, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))["message"]


def crossref(query, rows=1):
    url = ("https://api.crossref.org/works?" +
           urllib.parse.urlencode({"query.bibliographic": query, "rows": rows,
                                   "mailto": MAILTO, "select":
                                   "title,container-title,volume,page,issued,DOI,score,author"}))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))["message"]["items"]


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print = lambda *a: out.write(" ".join(str(x) for x in a) + "\n")   # noqa: A001

    print("# M33: bibliographic details from CrossRef (no token needed).")
    print("# ADS itself is unavailable here -- its API requires an Authorization header and")
    print("# no key is configured -- so ADS BIBCODES still need a human. Everything else")
    print("# item 6 asks for is below, with the match score so a bad match is visible.\n")
    print(f"{'key':<17s} {'score':>6s}  resolved")
    print("-" * 96)
    results = []
    for key, query, claimed in REFS:
        try:
            if key in KNOWN_DOI:
                items = [dict(by_doi(KNOWN_DOI[key]), score=999.0)]
            else:
                items = crossref(query)
        except Exception as e:
            print(f"{key:<17s} {'--':>6s}  QUERY FAILED: {type(e).__name__}")
            time.sleep(1.0)
            continue
        if not items:
            print(f"{key:<17s} {'--':>6s}  NO MATCH -- resolve by hand")
            time.sleep(1.0)
            continue
        d = items[0]
        title = (d.get("title") or ["?"])[0]
        title = " ".join(title.split())
        jrnl = (d.get("container-title") or ["?"])[0]
        yr = d.get("issued", {}).get("date-parts", [[None]])[0][0]
        a1 = (d.get("author") or [{}])[0].get("family", "?")
        line = (f"{a1} {yr}, {jrnl}, vol {d.get('volume','?')}, "
                f"p {d.get('page','?')}, doi:{d.get('DOI','?')}")
        sc = d.get("score", 0)
        flag = ("   [by DOI - exact]" if sc >= 999 else
                "" if sc > 55 else "   [LOW SCORE - CHECK THE TITLE]")
        print(f"{key:<17s} {('DOI' if sc >= 999 else f'{sc:.1f}'):>6s}  {line}{flag}")
        print(f"{'':<17s} {'':>6s}  title: {title[:78]}")
        print(f"{'':<17s} {'':>6s}  repo currently says: {claimed}")
        results.append((key, line, title, d.get("score", 0)))
        time.sleep(1.0)

    print("\n" + "=" * 96)
    print("Nothing above has been written into any draft. Verify the title on each line")
    print("matches the work actually intended, then transcribe. An automatic rewriter here")
    print("would be the sixteenth wrong citation this project has shipped.")
    low = [r for r in results if r[3] <= 55]
    if low:
        print(f"\n{len(low)} match(es) scored low and need a human eye: "
              + ", ".join(r[0] for r in low))


if __name__ == "__main__":
    main()
