"""Single approved XMM schema GET; no scientific products or second query."""

import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C0b1-SCHEMA-2026-09-12.md"
HELPER = HERE.parents[1] / "dyson-revet/scripts/check_e_release.py"
HELPER_HASH = "11ad0bef9fd2efae234e204358c6b6730e723ed3dc24c6fe0c345f2ddcfb53dd"
URL = "https://nxsa.esac.esa.int/tap-server/tap/sync"
QUERY = ("SELECT table_name,column_name,datatype,unit,description\n"
         "FROM TAP_SCHEMA.columns\n"
         "WHERE table_name IN ('xsa.v_exposure','xsa.v_instrument_mode','xsa.data_product')\n"
         "ORDER BY table_name,column_name")
PARAMS = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "json", "QUERY": QUERY}
CAP = 131072


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def validate(body):
    obj = json.loads(body)
    names = [x["name"] for x in obj["metadata"]]
    if names != ["table_name", "column_name", "datatype", "unit", "description"]:
        raise ValueError("STOP_COLUMN_SCHEMA")
    rows = obj["data"]
    tables = {"xsa.v_exposure", "xsa.v_instrument_mode", "xsa.data_product"}
    if not rows or any(len(row) != 5 for row in rows):
        raise ValueError("STOP_ROW_STRUCTURE")
    if {row[0] for row in rows} != tables:
        raise ValueError("STOP_TABLE_COVERAGE")
    keys = [(r[0], r[1]) for r in rows]
    if len(set(keys)) != len(keys) or keys != sorted(keys):
        raise ValueError("STOP_DUPLICATE_OR_ORDER")
    if any(not isinstance(r[1], str) or not r[1] or not isinstance(r[2], str) for r in rows):
        raise ValueError("STOP_INVALID_COLUMN")
    return {table: sum(r[0] == table for r in rows) for table in sorted(tables)}


def worker():
    import requests

    start = json.loads((HERE / "run-start.json").read_bytes())
    if start["source_sha256"] != sha(SOURCE) or start["helper_sha256"] != sha(HELPER):
        raise ValueError("STOP_PROVENANCE")
    if start["protocol_sha256"] != sha(HERE / "schema-protocol.snapshot.md"):
        raise ValueError("STOP_PROTOCOL_HASH")
    save("worker-start.json", {"params": PARAMS, "source_sha256": sha(SOURCE)})
    result = {"outcome": "STOP_REQUEST", "request_count": 1}
    try:
        with requests.get(URL, params=PARAMS, timeout=(5, 15), stream=True,
                          allow_redirects=False, headers={"Accept-Encoding": "identity"}) as response:
            headers = {"status": response.status_code, "url": response.url,
                       "headers": dict(response.headers)}
            save("http.json", headers)
            if response.headers.get("Content-Encoding", "identity").lower() not in ("identity", ""):
                raise ValueError("STOP_CONTENT_ENCODING")
            count = 0
            with (HERE / "schema-response.body").open("xb") as handle:
                for chunk in response.iter_content(8192):
                    if count + len(chunk) > CAP:
                        raise ValueError("STOP_BYTE_CAP")
                    handle.write(chunk)
                    count += len(chunk)
            if response.status_code != 200:
                raise ValueError(f"STOP_HTTP_{response.status_code}")
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) != count:
                raise ValueError("STOP_CONTENT_LENGTH")
            result = {"outcome": "PASS_SCHEMA", "request_count": 1,
                      "tables": validate((HERE / "schema-response.body").read_bytes())}
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        path = HERE / "schema-response.body"
        result["body"] = ({"bytes": path.stat().st_size, "sha256": sha(path)}
                          if path.exists() else None)
        save("worker-result.json", result)
    return 0 if result["outcome"] == "PASS_SCHEMA" else 1


def run():
    if (HERE / "run-start.json").exists():
        raise ValueError("STOP_ALREADY_ATTEMPTED")
    if sha(HELPER) != HELPER_HASH:
        raise ValueError("STOP_HELPER_HASH")
    with (HERE / "schema-protocol.snapshot.md").open("xb") as handle:
        handle.write(PROTOCOL.read_bytes())
    save("run-start.json", {"utc": datetime.now(timezone.utc).isoformat(), "url": URL,
                           "params": PARAMS, "byte_cap": CAP, "worker_seconds": 30,
                           "source_sha256": sha(SOURCE), "helper_sha256": sha(HELPER),
                           "protocol_sha256": sha(PROTOCOL)})
    start = time.monotonic()
    result = {"outcome": "STOP_PARENT", "second_request_executed": False}
    try:
        spec = importlib.util.spec_from_file_location("xmm_audited_bounded", HELPER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        code, output = module.bounded_run([str(Path(sys.executable).resolve()), "-B", str(SOURCE),
                                           "_worker"], 30)
        result.update(worker_returncode=code, worker_output=output)
        if code:
            raise ValueError(f"STOP_WORKER_{code}")
        receipt = json.loads((HERE / "worker-result.json").read_bytes())
        body = HERE / "schema-response.body"
        if (receipt["outcome"] != "PASS_SCHEMA" or receipt["request_count"] != 1
                or receipt["body"] != {"bytes": body.stat().st_size, "sha256": sha(body)}
                or not 0 < body.stat().st_size <= CAP):
            raise ValueError("STOP_RECEIPT")
        if validate(body.read_bytes()) != receipt["tables"]:
            raise ValueError("STOP_VALIDATION_REPLAY")
        result.update(outcome="PASS_SCHEMA", tables=receipt["tables"])
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        result["artifacts"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)}
                               for p in HERE.iterdir() if p.is_file()}
        save("outcome.json", result)
    print(json.dumps(result, indent=2))
    return 0 if result["outcome"] == "PASS_SCHEMA" else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        raise SystemExit(run())
    if sys.argv[1:] == ["_worker"]:
        raise SystemExit(worker())
    raise SystemExit("Only run or internal _worker is accepted")
