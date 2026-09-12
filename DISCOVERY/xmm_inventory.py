"""Offline inventory of one complete, retained HEASARC control directory."""

import argparse
import hashlib
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

URL = "https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/"
TITLE = "Index of /FTP/xmm/data/rev0/0884250101/PPS"
PRODUCT = re.compile(
    r"P0884250101(?P<instrument>[A-Z0-9]{2})(?P<exposure>[SUX][0-9]{3})"
    r"(?P<product>[A-Z0-9_]{6})(?P<subset>[A-Z0-9])(?P<source>[A-Z0-9]{3})"
    r"\.(?P<extension>[A-Z0-9]{3})"
)
LINK = re.compile(r'<a href="([^"]+)">([^<]+)</a>([^\r\n<]*)')
ROW = re.compile(r"\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(\S+)\s*")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            values = [value for key, value in attrs if key == "href"]
            if len(values) != 1:
                raise ValueError("Ambiguous anchor")
            self.hrefs.append(values[0])


def parse(body):
    text = body.decode("iso-8859-1")
    if (f"<title>{TITLE}</title>" not in text or f"<h1>{TITLE}</h1>" not in text
            or not text.rstrip().lower().endswith("</html>") or "</pre>" not in text):
        raise ValueError("Incomplete or wrong directory")
    anchors = Links()
    anchors.feed(text)
    matches = list(LINK.finditer(text))
    if [unescape(m[1]) for m in matches] != anchors.hrefs:
        raise ValueError("Unparsed or ambiguous link")
    ignored = {"?C=N;O=D", "?C=M;O=A", "?C=S;O=A", "?C=D;O=A",
               "/FTP/xmm/data/rev0/0884250101/"}
    entries = []
    seen = set()
    for match in matches:
        name, label, rest = (unescape(value) for value in match.groups())
        if name in ignored:
            continue
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or ".." in name
                or name != label or name in seen):
            raise ValueError("Unsafe, mismatched or duplicate file link")
        row = ROW.fullmatch(rest)
        if row is None:
            raise ValueError("Unparsed file row")
        seen.add(name)
        size = row[2]
        fields = PRODUCT.fullmatch(name)
        entries.append({"name": name, "url": URL + name, "modified_display": row[1],
                        "size_display": size, "exact_bytes": None,
                        "display_integer": int(size) if size.isdecimal() else None,
                        "size_kind": "integer" if size.isdecimal() else "rounded_or_unknown",
                        "pps_fields": fields.groupdict() if fields else None})
    if not entries:
        raise ValueError("Empty inventory")
    return entries


def inventory(directory):
    body = (directory / "index.html").read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    outcome = json.loads((directory / "outcome.json").read_bytes())
    for name, expected in outcome["artifacts"].items():
        if (not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or ".." in name
                or hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected):
            raise ValueError("Artifact provenance mismatch")
    if not {"index.html", "http.json", "worker-result.json"} <= set(outcome["artifacts"]):
        raise ValueError("Required receipt absent from outcome")
    worker = json.loads((directory / "worker-result.json").read_bytes())
    http = json.loads((directory / "http.json").read_bytes())
    if (outcome["status"] != "HTTP_INDEX_RETAINED" or outcome["worker_returncode"] != 0
            or outcome["artifacts"]["index.html"] != digest
            or worker["body"] != {"bytes": len(body), "sha256": digest}
            or worker["status"] != "HTTP_INDEX_RETAINED"
            or http["status"] != 200 or http["url"] != URL):
        raise ValueError("Incomplete or inconsistent transport receipt")
    entries = parse(body)
    return {"status": "OFFLINE_DIRECTORY_INVENTORY", "url": URL,
            "body_sha256": digest, "body_bytes": len(body), "entries_count": len(entries),
            "limits": "Index only; rounded sizes are not exact bytes. Modes and science contents unverified.",
            "entries": entries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inventory(args.directory)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "entries"}))
