"""Fetch a paper into papers/ and extract its text.

The project read Hoy et al. once via an ad-hoc pypdf call and kept nothing. That is why
three attribution errors survived into SPEC/HANDOFF and why reference [11] -- a published
detectability framework for exactly this method -- went unread for six milestones.

Usage:
    python scripts/fetch_paper.py 2207.07569 lazzoni2022
    python scripts/fetch_paper.py --title "Detecting exomoons via doppler monitoring"

Always writes UTF-8 explicitly: see HANDOFF section 4 for what cp1252 did to README.md.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "papers" / "pdf"
TXT = ROOT / "papers" / "text"
UA = {"User-Agent": "exosat-rv/0.1 (mailto:matthew.e.potts@gmail.com)"}


def _get(url: str, tries: int = 3) -> bytes:
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=90
            ).read()
        except Exception as exc:
            if i == tries - 1:
                raise
            print(f"  retry {i+1}/{tries} after {type(exc).__name__}", file=sys.stderr)
            time.sleep(3 * (i + 1))
    raise AssertionError("unreachable")


def find_arxiv_id(title: str) -> tuple[str, str] | None:
    """Resolve a title to (arxiv_id, canonical_title) via the arXiv API."""
    q = urllib.parse.urlencode(
        {"search_query": f'ti:"{title}"', "max_results": 5, "start": 0}
    )
    xml = _get(f"http://export.arxiv.org/api/query?{q}").decode("utf-8", "replace")
    entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
    for e in entries:
        idm = re.search(r"<id>http://arxiv\.org/abs/([^<]+)</id>", e)
        tm = re.search(r"<title>(.*?)</title>", e, re.DOTALL)
        if idm and tm:
            return idm.group(1), re.sub(r"\s+", " ", tm.group(1)).strip()
    return None


def fetch(arxiv_id: str, slug: str) -> Path:
    bare = arxiv_id.split("v")[0]
    pdf_path = PDF / f"{slug}_{bare.replace('/', '_')}.pdf"
    txt_path = TXT / f"{slug}.txt"
    PDF.mkdir(parents=True, exist_ok=True)
    TXT.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        pdf_path.write_bytes(_get(f"https://arxiv.org/pdf/{arxiv_id}"))

    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    text = "\n\n".join(
        f"<<<PAGE {i+1}>>>\n" + (p.extract_text() or "")
        for i, p in enumerate(reader.pages)
    )
    txt_path.write_text(text, encoding="utf-8")  # never omit: cp1252 truncates on Windows
    print(f"{slug:24s} {arxiv_id:16s} {len(reader.pages):3d}p {len(text):7d}ch -> {txt_path.name}")
    return txt_path


if __name__ == "__main__":
    if sys.argv[1] == "--title":
        hit = find_arxiv_id(" ".join(sys.argv[2:]))
        print(hit if hit else "NOT FOUND")
    else:
        fetch(sys.argv[1], sys.argv[2])
