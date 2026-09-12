"""C0c2 resource-only wrapper around the byte-identical C0c transport."""

import hashlib
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
PROTOCOL = HERE.parent / "XMM-C0c2-2026-09-12.md"
CORE = HERE.parent / "XMM-C0c-2026-09-12-data/listing.py"
CORE_HASH = "6dfc1715fa477a69687fd54a01a6cd61abd26be99519f18fd4e9297cd3091e31"
CAP = 1048576


def load_core():
    raw = CORE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CORE_HASH:
        raise ValueError("STOP_FROZEN_CORE_HASH")
    class VerifiedLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            if fullname != self.name:
                raise ImportError("Unexpected frozen module name")
            return compile(raw, str(CORE), "exec")

    name = "xmm_c0c2_frozen_transport"
    spec = importlib.util.spec_from_file_location(name, CORE, loader=VerifiedLoader(name, str(CORE)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = HERE
    module.SOURCE = SOURCE
    module.PROTOCOL = PROTOCOL
    module.CAP = CAP
    return module


def dispatch(stage):
    if stage not in ("run", "_worker"):
        raise ValueError("Only run or internal _worker is accepted")
    core = load_core()
    return core.run() if stage == "run" else core.worker()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Only run or internal _worker is accepted")
    raise SystemExit(dispatch(sys.argv[1]))
