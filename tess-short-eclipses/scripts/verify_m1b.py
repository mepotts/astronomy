"""Read-only exact replay of M1b pixels and catalog interpretation; no network."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def comparator(destination, clean, recorded, outputs):
    def compare_only(path, value):
        if path != destination or clean(value) != recorded:
            raise ValueError(f"exact M1b replay differs: {destination.name}")
        outputs.append(path)
    return compare_only


def main():
    for tic in (450781262, 53206761, 2041210548):
        spec = importlib.util.spec_from_file_location("isolated_m1b_replay", ROOT / "scripts/m1b.py")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        destination = ROOT / "out" / f"m1b-{tic}.json"
        recorded = json.loads(destination.read_bytes())
        for key, path in (
            ("metadata_adapter_sha256", ROOT / "scripts/m1b.py"),
            ("metadata_amendment_sha256", adapter.PROTOCOL),
            ("script_sha256", ROOT / "scripts/m1.py"),
            ("protocol_sha256", adapter.m1.PROTOCOL),
            ("runner_sha256", adapter.m1.RUNNER),
            ("m0b_result_sha256", ROOT / "out" / f"m0b-{tic}.json"),
        ):
            if adapter.m1.sha(path) != recorded[key]:
                raise ValueError(f"provenance mismatch: {key}")
        outputs = []

        # The adapter captures this as its final persistence function. Replaying
        # analysis cannot overwrite a receipt/result or retry a catalog request.
        adapter.m1.save = comparator(destination, adapter.m1.clean, recorded, outputs)
        adapter.worker("analyze", tic)
        if outputs != [destination]:
            raise ValueError("expected exactly one verified output")
        print(json.dumps({"tic": tic, "exact_replay": "PASS", "flags": recorded["flags"],
                          "unknown_search_authorized": False}))
    print("M1b exact raw-data replay: 3/3 PASS; source confusion remains unresolved")


if __name__ == "__main__":
    main()
