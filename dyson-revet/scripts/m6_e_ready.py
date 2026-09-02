"""M6 PR-4: candidate E readiness re-check.  Nothing about E is pre-empted.

Three checks and no analysis:

  1. The outcome map.  M5 Sec 5.3 wrote a four-case outcome map BEFORE E's data
     open, which is only worth something if it has not been edited since.  This
     hashes Sec 5.3 of the working-tree M5 document and compares it with the
     same section of the LAST COMMITTED M5, byte for byte.
  2. The procedure.  M5 Sec 5.2's parameterised chain is re-run against
     candidate D and graded against M4 Sec 5's seven hard-coded numbers.
  3. The data.  E's MAST status is re-checked anonymously, and the release date
     is compared with today.  If E is still embargoed, that is the expected
     answer and the script stops.  If E has become public EARLY, the script
     still stops: M5 PR-4 fixed that the analysis happens on or after the
     release date, and moving it forward is exactly the after-the-fact choice
     the outcome map exists to prevent.

    python scripts/m6_e_ready.py
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
M5 = "M5-nebular-stage-highlat-catalog.md"
SEC = "### 5.3 The outcome map"
RELEASE = "2026-09-09"


def section(text: str) -> str:
    i = text.index(SEC)
    j = text.index("\n## ", i)
    return text[i:j]


def main() -> None:
    res = {"release_date": RELEASE}

    # ---------------------------------------------------- 1. outcome map ---
    disk = (ROOT / M5).read_text(encoding="utf-8")
    rel = "dyson-revet/" + M5
    committed = subprocess.run(["git", "show", "HEAD:" + rel],
                               cwd=ROOT.parent, capture_output=True,
                               text=True, encoding="utf-8")
    ok_git = committed.returncode == 0
    s_disk = section(disk)
    h_disk = hashlib.sha256(s_disk.encode("utf-8")).hexdigest()
    h_commit = (hashlib.sha256(section(committed.stdout).encode("utf-8")).hexdigest()
                if ok_git else None)
    res["outcome_map"] = {
        "section": SEC, "chars": len(s_disk), "sha256_working_tree": h_disk,
        "sha256_last_commit": h_commit, "git_available": ok_git,
        "unedited": bool(ok_git and h_disk == h_commit),
        "cases_present": sorted(re.findall(r"\*\*Outcome (\d)", s_disk))}
    print("1. OUTCOME MAP (M5 Sec 5.3)")
    print("   %d chars, sha256 %s" % (len(s_disk), h_disk[:16]))
    print("   identical to the last committed M5: %s"
          % res["outcome_map"]["unedited"])
    print("   four cases present: %s" % res["outcome_map"]["cases_present"])

    # ------------------------------------------------------ 2. procedure ---
    print("\n2. PROCEDURE (M5 Sec 5.2 chain, re-graded on candidate D)")
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "m5_jwst_target.py"),
                        "measure", "--label", "D", "--obsprefix", "jw07199-o005",
                        "--validate"], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    txt = (p.stdout or "") + (p.stderr or "")
    (OUT / "m6_e_ready_validate.log").write_text(txt, encoding="utf-8")
    npass = len(re.findall(r"\bPASS\b", txt))
    nfail = len(re.findall(r"\bFAIL\b", txt))
    res["procedure"] = {"returncode": p.returncode, "n_pass": npass,
                        "n_fail": nfail, "ready": bool(nfail == 0 and npass >= 7)}
    for line in txt.splitlines():
        if "PASS" in line or "FAIL" in line or "READY" in line:
            print("   " + line.strip())
    print("   -> %d PASS, %d FAIL, ready: %s"
          % (npass, nfail, res["procedure"]["ready"]))

    # ----------------------------------------------------------- 3. data ---
    print("\n3. DATA (anonymous MAST, GO 7199, Object_E)")
    q = subprocess.run([sys.executable, str(ROOT / "scripts" / "m5_jwst_target.py"),
                        "status", "--label", "E"], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    stxt = (q.stdout or "") + (q.stderr or "")
    (OUT / "m6_e_ready_status.log").write_text(stxt, encoding="utf-8")
    npub = re.search(r"PUBLIC observations:\s*(\d+)\s*of\s*(\d+)", stxt)
    rels = sorted(set(re.findall(r"\d+\.\d+\s+(\d{4}-\d{2}-\d{2})", stxt)))
    res["data"] = {"n_public": int(npub.group(1)) if npub else None,
                   "n_total": int(npub.group(2)) if npub else None,
                   "release_dates": rels,
                   "matches_M5_release": bool(rels and all(r == RELEASE for r in rels))}
    print("   PUBLIC %s of %s; release dates %s"
          % (res["data"]["n_public"], res["data"]["n_total"], rels))
    if res["data"]["n_public"]:
        print("   E's products are PUBLIC.  M5 PR-4 fixes the analysis to on or "
              "after %s; this script does not run it." % RELEASE)
    else:
        print("   still embargoed until %s -- expected, and nothing is "
              "pre-empted." % RELEASE)

    res["ready"] = bool(res["outcome_map"]["unedited"] and res["procedure"]["ready"])
    (OUT / "m6_e_readiness.json").write_text(json.dumps(res, indent=2))
    print("\nREADY: %s   -> out/m6_e_readiness.json" % res["ready"])


if __name__ == "__main__":
    main()
