"""Non-coordinate derivative of a retained headers-only report; no FITS arrays."""

import json
import re
import sys
from pathlib import Path

from astropy.io.fits import Header

METADATA = (
    "TELESCOP", "INSTRUME", "OBS_ID", "EXP_ID", "EXPIDSTR", "DATAMODE",
    "SUBMODE", "FILTER", "OBS_MODE", "DATE-OBS", "DATE-END", "TSTART", "TSTOP",
    "TIMESYS", "TIMEUNIT", "TIMEZERO", "MJDREF", "MJDREFI", "MJDREFF",
    "TIMEREF", "TASSIGN", "CLOCKAPP", "ONTIME", "LIVETIME", "EXPOSURE",
    "DEADC", "SAS_VER", "SAS_CCF", "CREATOR", "CCDNR", "CCDID", "MODE",
    "WINDOWX0", "WINDOWY0", "WINDOWDX", "WINDOWDY", "TIMEDEL",
)


def summarize(report):
    if report["status"] != "HEADER_LAYOUT_ONLY":
        raise ValueError("Expected structural-only report")
    output = {key: report[key] for key in (
        "status", "file_bytes", "hdu_count", "header_bytes_read",
        "declared_data_region_bytes_read",
    )}
    output["hdus"] = []
    for item in report["hdus"]:
        header = Header.fromstring("".join(item["cards"]), sep="")
        # Preserve repeated allowed keys explicitly rather than silently taking
        # the first. Never serialize arbitrary cards, comments or WCS values.
        metadata = {key: [card.value for card in header.cards if card.keyword == key]
                    for key in METADATA if key in header}
        columns = [{key: header.get(f"{prefix}{i}") for key, prefix in (
            ("name", "TTYPE"), ("format", "TFORM"), ("unit", "TUNIT"))}
            for i in range(1, header.get("TFIELDS", 0) + 1)]
        output["hdus"].append({
            "hdu": item["hdu"], "extname": item["extname"],
            "data_bytes": item["data_bytes"], "rows": header.get("NAXIS2"),
            "metadata": metadata, "columns": columns,
            "data_subspace_keys_present": sorted({key for key in header
                if re.match(r"^\d*(?:DSTYP|DSUNI|DSVAL|DSREF)", key)}),
            "wcs_keys_present": sorted({key for key in header
                if key.startswith(("TCTYP", "TCRPX", "TCRVL", "TCDLT", "TCUNI"))}),
        })
    return output


if __name__ == "__main__":
    print(json.dumps(summarize(json.loads(Path(sys.argv[1]).read_bytes())),
                     indent=2, allow_nan=False))
