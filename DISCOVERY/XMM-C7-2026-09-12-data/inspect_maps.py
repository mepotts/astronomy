"""Isolated C5 composition: one MOS2 map, ten unchanged static regions."""

import contextlib
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C7-2026-09-12.md"
BASE_PATH = HERE.parent / "XMM-C5-2026-09-12-data/inspect_maps.py"
BASE_HASH = "5e7af10b0d8ac5ea8272229efb8a618a392c92d802e6efc401e6b3a54cb5a05b"
BASE_TEST_HASH = "51fa37948ea7fcb9a5fd41d1d232a835f7cf04027a6b9d385752b35aac9c3007"
BASE_OUTCOME = "58d8526abdaeb0347cecb252b740fcbd8b5f6956bf89a661b08eb5210d892a36"
PRIOR_PATH = HERE.parent / "XMM-C6-2026-09-12-data/acquire.py"
PRIOR_HASH = "4ed7d10e229a38f4356f34386ee70e510915049c1468b006841908ecaf1cbfdb"
PRIOR_TEST_HASH = "f46468825846e68649ccb48d2592163b0151476de6a49609f315af2141c31ccf"
PRIOR_OUTCOME = "8cd766cd9ec4e2a54548248bd6b8aa0805c94678e1e066ba3c560713e03e0caa"
COMPATIBILITY = HERE.parent / "XMM-MOS2-MAP-COMPATIBILITY-2026-09-12.md"
COMPATIBILITY_HASH = "edfb5068c498826077c85580fa22b5c34e5249a749244e9202d4522848f87f43"
ITEM = {"map": 1, "camera": "EMOS2", "exposure": "S002", "filename": "P0884250101M2S002EXPMAP8000.fits",
        "offset": 25920, "file_bytes": 1707840,
        "sha256": "a92d6907db2e9e4def19b124c19da6056d20a06e3465da7103a23fb5dcd36983",
        "header_sha256": "6cc4bfa1b08d93a31f8f89ba49274511e9ef0052634d64cb1235fdde739e2285"}
LOGGER = logging.getLogger(__name__)


def load_base():
    raw = BASE_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASE_HASH:
        raise ValueError("STOP_BASE_SOURCE_HASH")

    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("STOP_MODULE_IDENTITY")
            return compile(raw, str(BASE_PATH), "exec")

    spec = importlib.util.spec_from_file_location("c7_isolated_base", BASE_PATH, loader=VerifiedLoader("c7_isolated_base", str(BASE_PATH)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_base()
C = B.C
B.HERE = C.HERE = HERE
B.SOURCE, B.PROTOCOL = SOURCE, PROTOCOL
B.PRIOR_PATH, B.PRIOR_HASH, B.PRIOR_OUTCOME = PRIOR_PATH, PRIOR_HASH, PRIOR_OUTCOME
B.MAPS = (ITEM,)
B.TOTAL = B.PAYLOAD
BASE_BINDING, BASE_LEDGER, BASE_ASSESS = B.binding, B.ledger, B.assess
BASE_VALIDATE = B.validate_validation


def manifest():
    """C6 header JSON only; unchanged C5 geometry validation uses no pixels."""
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    outcome = json.loads(PRIOR_PATH.with_name("outcome.json").read_bytes())
    if outcome["status"] != "MOS2_MAP_RETAINED_HEADERS_ONLY" or outcome["worker_returncode"] != 0:
        raise ValueError("STOP_PRIOR_STATUS")
    if (outcome["artifacts"]["products/" + ITEM["filename"]] != ITEM["sha256"]
            or outcome["artifacts"]["headers/slot-1-headers.json"] != ITEM["header_sha256"]):
        raise ValueError("STOP_PRIOR_MAP_BINDING")
    core = C.load_pinned("c7_core_schema", B.CORE_PATH, B.CORE_HASH)
    wcs = B.read_header(ITEM)
    dummy = B.np.empty((B.SIDE, B.SIDE), dtype=B.np.float32)
    for centre in B.centres():
        for kind in B.KINDS:
            core.validate(dummy, wcs, centre, kind)
    return {"maps": [ITEM], "labels": list(B.LABELS), "kinds": list(B.KINDS), "planned_regions": 10,
            "definition_sha256": B.DEFINITION_HASH, "centre_convention": "published_ICRS_offsets_then_FK5_J2000",
            "wcs_contract": "primary_CDELT_only_RA_DEC_TAN_deg_FK5_J2000_explicit_no_fix",
            "value_contract": "absent_BUNIT_no_scaling_sign_only_no_physical_units",
            "MOS2": "ONLY_MAP_IN_THIS_STAGE", "C5": "UNCHANGED_NOT_REPLAYED"}


def binding(protocol):
    paths = {BASE_PATH: BASE_HASH, BASE_PATH.with_name("test_inspect_maps.py"): BASE_TEST_HASH,
             PRIOR_PATH.with_name("test_acquire.py"): PRIOR_TEST_HASH,
             BASE_PATH.with_name("outcome.json"): BASE_OUTCOME, COMPATIBILITY: COMPATIBILITY_HASH}
    if any(C.sha(p) != digest for p, digest in paths.items()):
        raise ValueError("STOP_COMPOSITION_DEPENDENCY")
    result = BASE_BINDING(protocol)
    result["dependencies"].update({str(p): digest for p, digest in paths.items()})
    result["composition"] = "C5_frozen_numerical_and_receipt_functions_isolated_single_map_adapter"
    result["prior_c5_outcome_sha256"] = BASE_OUTCOME
    return result


def verify_prior():
    if C.sha(PRIOR_PATH.with_name("outcome.json")) != PRIOR_OUTCOME or C.sha(BASE_PATH.with_name("outcome.json")) != BASE_OUTCOME:
        raise ValueError("STOP_PRIOR_OUTCOME_HASH")
    prior = C.load_pinned("c7_c6_header_replay", PRIOR_PATH, PRIOR_HASH)
    with contextlib.redirect_stdout(io.StringIO()):
        prior.replay()  # Header/hash only. Never run C5's original map replay.
    C.checkpoint()


def fallback():
    return [{"map": 1, "status": "UNVERIFIED_ATTEMPT" if any(HERE.glob("map-1-*.json")) else "NOT_ATTEMPTED",
             "accounting": None}]


def validation_state():
    return {"status": "NOT_ATTEMPTED", "accounting": B.zero(),
            "maps": [{"map": 1, "status": "NOT_ATTEMPTED", "accounting": B.zero()}]}


def validate_validation(record):
    if not isinstance(record, dict) or not isinstance(record.get("maps"), list) or len(record["maps"]) != 1:
        raise ValueError("STOP_VALIDATION_ACCOUNTING")
    # Reuse every frozen consistency rule with a virtual unattempted second
    # slot. It is never persisted, measured or exposed in C7's one-map ledger.
    expanded = {**record, "maps": [*record["maps"], {"map": 2, "status": "NOT_ATTEMPTED", "accounting": B.zero()}]}
    BASE_VALIDATE(expanded)


def ledger(recompute=False, validation=None):
    if any(p.name not in {"map-1-start.json", "map-1-result.json"} for p in HERE.glob("map-*.json")):
        raise ValueError("STOP_EXTRA_MAP_ARTIFACT")
    return BASE_LEDGER(recompute=recompute, validation=validation)


def assess(code, validation=None):
    result = BASE_ASSESS(code, validation)
    result.update(planned_regions=10, MOS2="ONLY_MAP_IN_THIS_STAGE", prior_c5_outcome_sha256=BASE_OUTCOME)
    return result


# All callbacks are rebound only in this new module instance. The inherited
# entry points dispatch through these globals, including in the child process.
B.manifest, B.binding, B.verify_prior = manifest, binding, verify_prior
B.fallback, B.validation_state, B.validate_validation = fallback, validation_state, validate_validation
B.ledger, B.assess = ledger, assess


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["run"]:
            raise SystemExit(B.run())
        if sys.argv[1:] == ["_worker"]:
            raise SystemExit(B.worker())
        if sys.argv[1:] == ["replay"]:
            B.replay()
        else:
            raise ValueError("STOP_COMMAND")
    except Exception as error:
        LOGGER.exception("MOS2 map command stopped", exc_info=(RuntimeError, RuntimeError("Safe code only"), None))
        print(B.O.failure(error).get("error_code") or "STOP_INTERNAL")
        raise SystemExit(1) from None
