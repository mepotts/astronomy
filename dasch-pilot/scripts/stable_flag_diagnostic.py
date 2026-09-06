"""Post-hoc confound check, retaining the primary Feige 66 excursion flag."""
import hashlib
import json
import statistics
import zipfile
from pathlib import Path

from m0_extension import clean, decimal_year, table

ROOT = Path(__file__).resolve().parents[1]


def run():
    folder = ROOT / "data/stable-normalized-20260906"
    manifest = json.loads((folder / "provenance.json").read_bytes())
    with zipfile.ZipFile(folder / "responses.zip") as archive:
        raw = archive.read("13-lightcurve.raw")
    if hashlib.sha256(raw).hexdigest() != manifest["artifacts"]["13-lightcurve"]["sha256"]:
        raise ValueError("changed light curve")
    rows = [r for r in clean(table(raw)) if int(decimal_year(float(r["date_jd"]))) == 1974]
    kept = [{k: r[k] for k in ("date_jd", "series", "plate_number", "magcal_magdep", "aflags")} for r in rows]
    red = [float(r["magcal_magdep"]) for r in rows if r["series"] == "dnr"]
    blue = [float(r["magcal_magdep"]) for r in rows if r["series"] == "dnb"]
    simultaneous = [{"jd": a["date_jd"], "red_minus_blue_mag": float(a["magcal_magdep"])-float(b["magcal_magdep"])}
                    for a in rows for b in rows if a["series"] == "dnr" and b["series"] == "dnb" and a["date_jd"] == b["date_jd"]]
    return {"interpretation": "POST_HOC_EMULSION_CONFOUND_NOT_A_DISCOVERY_OR_NEW_PRIMARY_CUT",
            "primary_flag_preserved": True, "star": "Feige66", "year": 1974,
            "measurements": kept, "red_n": len(red), "blue_n": len(blue),
            "red_median": statistics.median(red), "blue_median": statistics.median(blue),
            "same_timestamp_pairs": simultaneous,
            "blue_only_year_eligible_under_five_point_rule": len(blue) >= 5,
            "true_long_term_variability_ruled_out": False,
            "reference": "https://dasch.cfa.harvard.edu/dr7/colorterms/"}


if __name__ == "__main__":
    result = run()
    with (ROOT / "data/stable-normalized-20260906/flag-diagnostic.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
