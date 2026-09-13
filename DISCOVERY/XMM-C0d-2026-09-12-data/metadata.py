"""Five fixed anonymous metadata requests; never read a HEAD product body."""

import hashlib
import http.client as http_client
import importlib.util
import json
import logging
import math
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C0d-2026-09-12.md"
HELPER = HERE.parents[1] / "dyson-revet/scripts/check_e_release.py"
HELPER_HASH = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"
INVENTORY = HERE.parent / "XMM-C0c2-2026-09-12-data/inventory.json"
INVENTORY_HASH = "6ddb4a357439922dbefaa51e365b53802e6d031d079348706274555f4e063c23"
INDEX = INVENTORY.with_name("index.html")
INDEX_HASH = "97f9372b999b354ebcbff51a4b42af885433de598795a6a58656ef1e09bac258"
BASE = "https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0884250101/PPS/"
NAMES = ("P0884250101PNS003PIEVLI0000.FTZ", "P0884250101M1S001MIEVLI0000.FTZ",
         "P0884250101M2S002MIEVLI0000.FTZ", "P0884250101EPX000OBSMLI0000.FTZ",
         "P0884250101OBX000SUMMAR0000.HTM")
CAP = 262144
SECONDS = 60
SAFE_HEADERS = ("Content-Type", "Content-Length", "Content-Encoding", "Date", "ETag", "Last-Modified")
PASS = "SIZE_AND_SUMMARY_METADATA_RETAINED"
LOGGER = logging.getLogger(__name__)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_bytes())


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def failure(error):
    message = str(error)
    code = message if isinstance(error, ValueError) and re.fullmatch(r"STOP_[A-Z0-9_]+", message) else None
    return {"error_type": type(error).__name__, "error_code": code}


def plan():
    if sha(INVENTORY) != INVENTORY_HASH or sha(INDEX) != INDEX_HASH:
        raise ValueError("STOP_INPUT_HASH")
    entries = json.loads(INVENTORY.read_bytes())["entries"]
    result = []
    for i, name in enumerate(NAMES, 1):
        rows = [r for r in entries if r["name"] == name]
        if len(rows) != 1 or rows[0]["url"] != BASE + name:
            raise ValueError("STOP_INVENTORY_SELECTION")
        result.append({"slot": i, "method": "HEAD" if i < 5 else "GET", "url": rows[0]["url"]})
    return result


def binding(protocol):
    if sha(HELPER) != HELPER_HASH:
        raise ValueError("STOP_HELPER_HASH")
    return {"slots": plan(), "cap": CAP, "worker_seconds": SECONDS,
            "source_sha256": sha(SOURCE), "tests_sha256": sha(HERE / "test_metadata.py"),
            "protocol_sha256": sha(protocol), "helper_sha256": HELPER_HASH,
            "inventory_sha256": INVENTORY_HASH, "index_sha256": INDEX_HASH}


def verify_binding():
    if read("run-start.json") != binding(HERE / "protocol.snapshot.md"):
        raise ValueError("STOP_BINDING")


def length(values, required):
    if not values:
        if required:
            raise ValueError("STOP_SIZE_METADATA")
        return None
    tokens = [token.strip() for value in values for token in value.split(",")]
    if (not tokens or any(not re.fullmatch(r"[0-9]{1,20}", token) for token in tokens)
            or len({int(token) for token in tokens}) != 1 or int(tokens[0]) <= 0):
        raise ValueError("STOP_SIZE_METADATA")
    return int(tokens[0])


def single(headers, key, default=""):
    values = headers.get(key, [])
    if not values:
        return default
    if len(set(values)) != 1:
        raise ValueError("STOP_HEADER_AMBIGUITY")
    return values[0]


def check_http(slot, http):
    if (set(http) != {"method", "url", "status", "headers"} or http["method"] != slot["method"]
            or http["url"] != slot["url"] or http["status"] != 200):
        raise ValueError("STOP_HTTP_IDENTITY_OR_STATUS")
    headers = http["headers"]
    if (not set(headers) <= set(SAFE_HEADERS)
            or any(not isinstance(v, list) or not v or any(not isinstance(x, str) for x in v)
                   for v in headers.values())):
        raise ValueError("STOP_HEADER_SCHEMA")
    if single(headers, "Content-Encoding", "identity").lower() not in ("identity", ""):
        raise ValueError("STOP_CONTENT_ENCODING")
    if slot["method"] == "GET" and "html" not in single(headers, "Content-Type").lower():
        raise ValueError("STOP_NOT_HTML")
    return length(headers.get("Content-Length", []), slot["method"] == "HEAD")


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def body_record():
    p = HERE / "summary.html"
    return {"bytes": p.stat().st_size, "sha256": sha(p)} if p.exists() else None


def measurement(slot, http):
    size = check_http(slot, http)
    if slot["method"] == "HEAD":
        return {"advertised_compressed_bytes": size, "body": None, "body_bytes_read": 0}
    body = body_record()
    if body is None or not 0 < body["bytes"] <= CAP or (size is not None and size != body["bytes"]):
        raise ValueError("STOP_SUMMARY_LENGTH")
    text = (HERE / "summary.html").read_bytes().decode("utf-8", errors="replace")
    if not re.search(r"</html\s*>\s*$", text, re.IGNORECASE):
        raise ValueError("STOP_SUMMARY_FOOTER")
    parser = VisibleText()
    parser.feed(text)
    if not re.search(r"(?<![0-9])0884250101(?![0-9])", " ".join(parser.parts)):
        raise ValueError("STOP_SUMMARY_CONTROL_ID")
    return {"advertised_compressed_bytes": None, "body": body, "body_bytes_read": body["bytes"],
            "visible_control_id_present": True, "eligibility": "METADATA_INCOMPLETE_FOR_CONTROL_CONTRACT"}


def collect(slot):
    import requests

    if http_client._MAXLINE > 65536 or http_client._MAXHEADERS > 100:
        raise ValueError("STOP_UNBOUNDED_HEADER_PARSER")
    with requests.Session() as session:
        session.trust_env = False
        session.auth = None
        session.cookies.clear()
        with session.request(slot["method"], slot["url"], timeout=(5, 15), stream=True,
                             allow_redirects=False, headers={"Accept-Encoding": "identity"}) as response:
            headers = {k: response.raw.headers.getlist(k) for k in SAFE_HEADERS
                       if response.raw.headers.getlist(k)}
            if sum(len(x) for values in headers.values() for x in values) > 65536:
                raise ValueError("STOP_SAFE_HEADER_CAP")
            http = {"method": response.request.method, "url": response.url,
                    "status": response.status_code, "headers": headers}
            save(f"slot-{slot['slot']}-http.json", http)
            if slot["method"] == "GET":
                # Never consume a non-HTML or encoded body, including an error response.
                if single(headers, "Content-Encoding", "identity").lower() not in ("identity", ""):
                    raise ValueError("STOP_CONTENT_ENCODING")
                if "html" not in single(headers, "Content-Type").lower():
                    raise ValueError("STOP_NOT_HTML")
                count = 0
                with (HERE / "summary.html").open("xb") as handle:
                    while True:
                        chunk = response.raw.read(min(8192, CAP - count + 1), decode_content=False)
                        if not chunk:
                            break
                        keep = chunk[:CAP - count]
                        handle.write(keep)
                        count += len(keep)
                        if len(chunk) > len(keep):
                            raise ValueError("STOP_BYTE_CAP")
            return measurement(slot, http)


def artifact_hashes():
    names = [p for p in HERE.iterdir() if p.is_file() and
             (p.name.startswith("slot-") or p.name in ("summary.html", "worker-start.json"))]
    return {p.name: sha(p) for p in names}


def ledger():
    result = []
    stopped = False
    last_elapsed = -1
    for slot in plan():
        n = slot["slot"]
        marker = HERE / f"slot-{n}-start.json"
        receipt = HERE / f"slot-{n}-result.json"
        row = {**slot, "status": "NOT_ATTEMPTED"}
        if marker.exists():
            mark = read(marker.name)
            elapsed = mark.get("elapsed_seconds")
            if (stopped or set(mark) != {"slot", "method", "url", "elapsed_seconds"}
                    or {k: mark[k] for k in slot} != slot or type(elapsed) not in (float, int)
                    or not math.isfinite(elapsed) or not last_elapsed <= elapsed < SECONDS):
                raise ValueError("STOP_REQUEST_ORDER_OR_MARKER")
            last_elapsed = elapsed
            row["status"] = "INTERRUPTED_OR_NO_RECEIPT"
            if receipt.exists():
                recorded = read(receipt.name)
                if recorded.get("slot") != slot or recorded.get("status") not in ("OK", "FAILED"):
                    raise ValueError("STOP_SLOT_RECEIPT")
                if recorded["status"] == "OK":
                    expected = {"slot": slot, "status": "OK", **measurement(slot, read(f"slot-{n}-http.json"))}
                    if recorded != expected:
                        raise ValueError("STOP_SLOT_REPLAY")
                elif set(recorded) != {"slot", "status", "error_type", "error_code", "body"}:
                    raise ValueError("STOP_FAILED_RECEIPT")
                row.update({k: v for k, v in recorded.items() if k != "slot"})
            stopped = row["status"] != "OK"
        else:
            if receipt.exists() or (HERE / f"slot-{n}-http.json").exists():
                raise ValueError("STOP_ORPHAN_RECEIPT")
            stopped = True
        result.append(row)
    if len(list(HERE.glob("slot-*-start.json"))) != sum(r["status"] != "NOT_ATTEMPTED" for r in result):
        raise ValueError("STOP_EXTRA_REQUEST")
    return result


def worker():
    began = time.monotonic()
    result = {"status": "STOP"}
    try:
        verify_binding()
        save("worker-start.json", {"binding_sha256": sha(HERE / "run-start.json")})
        for slot in plan():
            elapsed = time.monotonic() - began
            if not 0 <= elapsed < SECONDS:
                raise ValueError("STOP_TOTAL_DEADLINE")
            save(f"slot-{slot['slot']}-start.json", {**slot, "elapsed_seconds": elapsed})
            try:
                value = collect(slot)
            except Exception as error:
                LOGGER.exception("Metadata slot failed")
                save(f"slot-{slot['slot']}-result.json", {"slot": slot, "status": "FAILED",
                     **failure(error), "body": body_record() if slot["method"] == "GET" else None})
                raise
            save(f"slot-{slot['slot']}-result.json", {"slot": slot, "status": "OK", **value})
        result["status"] = PASS
    except Exception as error:
        LOGGER.exception("Metadata worker stopped")
        result.update(failure(error))
    finally:
        result.update(artifacts=artifact_hashes(), ledger=ledger())
        save("worker-result.json", result)
    return 0 if result["status"] == PASS else 1


def assess(code):
    verify_binding()
    rows = ledger()
    worker_path = HERE / "worker-result.json"
    worker_result = read(worker_path.name) if worker_path.exists() else None
    if worker_result and (worker_result["artifacts"] != artifact_hashes() or worker_result["ledger"] != rows):
        raise ValueError("STOP_WORKER_CLOSURE")
    success = code == 0 and worker_result is not None and worker_result["status"] == PASS
    if success and (any(r["status"] != "OK" for r in rows)
                    or read("worker-start.json") != {"binding_sha256": sha(HERE / "run-start.json")}):
        raise ValueError("STOP_WORKER_SUCCESS")
    sizes = [r["advertised_compressed_bytes"] for r in rows[:4] if r["status"] == "OK"]
    return {"status": PASS if success else "STOP", "ledger": rows,
            "request_markers": sum(r["status"] != "NOT_ATTEMPTED" for r in rows),
            "successful_responses": sum(r["status"] == "OK" for r in rows),
            "compressed_lengths": sizes, "compressed_total": sum(sizes) if len(sizes) == 4 else None,
            "worker_error_code": worker_result.get("error_code") if worker_result else None,
            "photon_body_bytes_read": 0, "eligibility": "METADATA_INCOMPLETE_FOR_CONTROL_CONTRACT"}


def run():
    if (HERE / "run-start.json").exists() or (HERE / "outcome.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    result = {"status": "STOP", "worker_returncode": None, "worker_dispatch_started": False}
    try:
        save("run-start.json", binding(PROTOCOL))
        with (HERE / "protocol.snapshot.md").open("xb") as handle:
            handle.write(PROTOCOL.read_bytes())
        spec = importlib.util.spec_from_file_location("xmm_c0d_deadline", HELPER)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        result["worker_dispatch_started"] = True
        code, _output = helper.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE), "_worker"], SECONDS)
        result["worker_returncode"] = code
        result.update(assess(code))
    except Exception as error:
        LOGGER.exception("Metadata parent stopped")
        result.update(failure(error))
        result.setdefault("ledger", [{"slot": i, "method": "HEAD" if i < 5 else "GET", "url": BASE + name,
              "status": "UNVERIFIED_ATTEMPT" if (HERE / f"slot-{i}-start.json").exists() else "NOT_ATTEMPTED"}
              for i, name in enumerate(NAMES, 1)])
    finally:
        result["artifacts"] = {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}
        save("outcome.json", result)
    print(json.dumps(result))
    return 0 if result["status"] == PASS else 1


def replay():
    outcome = read("outcome.json")
    for name, expected in outcome["artifacts"].items():
        if sha(HERE / name) != expected:
            raise ValueError("STOP_ARTIFACT_HASH")
    computed = assess(outcome["worker_returncode"])
    if any(outcome.get(k) != v for k, v in computed.items()):
        raise ValueError("STOP_OUTCOME_REPLAY")
    print("PASS_OFFLINE_REPLAY", computed["status"])


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        raise SystemExit(run())
    if sys.argv[1:] == ["_worker"]:
        raise SystemExit(worker())
    if sys.argv[1:] == ["replay"]:
        replay()
    else:
        raise SystemExit("Expected run, internal _worker, or replay")
