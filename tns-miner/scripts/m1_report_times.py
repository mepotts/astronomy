"""Scrape the true TNS report time ("Time received (UT)") per object.

The search CSV gives only the *discovery epoch* -- the timestamp of the exposure.
The deadline we actually had to beat is when the winning discovery report was
FILED, which TNS shows only on the object page, in the "AT Reports" table.

For AT 2026stb the gap is 22.5 h (discovery 2026-07-08 06:35:20 UT, DCAP's report
received 2026-07-09 05:04:43 UT).  Using the discovery epoch as the rewind cutoff
is therefore far stricter than the mission's "before the report was filed", and it
is what an honest lead-time measurement has to use.

Rate-limited to 8 req / 60 s (TNS publishes 10).  Read-only.
Writes data/tns/report_times.csv (gitignored).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tnscommon import DATA, session, tns_get  # noqa: E402

# NB: the reporter_name cell carries a title="..." attribute, so the class name
# must not be followed by a literal '>' in the pattern.
ROW_RE = re.compile(
    r'cell-time_received">([^<]+)</td>\s*'
    r'<td class="cell-user_name"[^>]*>([^<]*)</td>\s*'
    r'<td class="cell-reporter_name"[^>]*>(.*?)</td>\s*'
    r'<td class="cell-reporting_group_name"[^>]*>([^<]*)</td>',
    re.S)


def scrape(names: list[str], out_csv: Path) -> pd.DataFrame:
    done = {}
    if out_csv.exists():
        prev = pd.read_csv(out_csv, dtype=str)
        done = dict(zip(prev["tns_name"], prev.to_dict("records")))
    s = session()
    rows = list(done.values())
    todo = [n for n in names if n not in done]
    print(f"report times: {len(done)} cached, {len(todo)} to fetch", flush=True)
    for i, name in enumerate(todo, 1):
        slug = name.split()[-1]  # "AT 2026stb" -> "2026stb"
        r = tns_get(s, f"https://www.wis-tns.org/object/{slug}")
        rec = {"tns_name": name, "http": r.status_code,
               "first_report_ut": None, "first_report_sender": None,
               "first_report_group": None, "n_reports": 0}
        if r.status_code == 200:
            m = ROW_RE.findall(r.text)
            if m:
                m_sorted = sorted(m, key=lambda t: t[0])
                rec.update({
                    "first_report_ut": m_sorted[0][0].strip(),
                    "first_report_sender": m_sorted[0][1].strip(),
                    "first_report_group": m_sorted[0][3].strip(),
                    "n_reports": len(m),
                })
        rows.append(rec)
        if i % 10 == 0:
            print(f"  {i}/{len(todo)} ({name})", flush=True)
            pd.DataFrame(rows).to_csv(out_csv, index=False)
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    return df


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "dcap"
    src, out = {
        "dcap": (DATA / "tns" / "dcap_group195.csv", DATA / "tns" / "report_times.csv"),
        "auto": (DATA / "tns" / "auto_reporter_sample.csv",
                 DATA / "tns" / "report_times_auto.csv"),
    }[which]
    names = pd.read_csv(src, dtype=str)["Name"].dropna().tolist()
    df = scrape(names, out)
    got = df["first_report_ut"].notna().sum()
    print(f"got report times for {got}/{len(df)}")


if __name__ == "__main__":
    main()
