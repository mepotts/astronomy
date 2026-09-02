"""M7 side-stat: how much slow-moving, far-northern material does the ITF hold?

Scoping number for the queued TNO niche (run-3 prospectus avenue #3: "everyone tunes
for main-belt rates; MPC hand-processes TNO linkages; Dec > +30 is where Rubin barely
covers"). No gating build here -- one count, defined precisely:

    tracklets (desig x obscode x local night, n_obs >= 2, span > 0) whose endpoint
    apparent rate is < 10 arcsec/hr and whose mean Dec > +30 deg.

A TNO at opposition moves ~1-3 arcsec/hr; < 10 covers the whole distant population
while excluding main-belt rates (~30+). Rate noise from two 0.3" endpoints over a
median 0.64 h span is ~1 arcsec/hr -- small against the 10 arcsec/hr cut, but real for
the shortest tracklets, so the count is also split by span.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl

from itf_linker import config
from itf_linker.ingest.fetch import fetch_obscodes

OUT = ROOT / "data" / "raw" / "rubin" / "m7-tno-stat.json"


def main() -> None:
    lon = fetch_obscodes()
    lon_df = pl.DataFrame(
        {"obscode": list(lon.keys()),
         "lon_deg": [v - 360.0 if v > 180.0 else v for v in lon.values()]}
    )
    trk = (
        pl.scan_parquet(config.ITF_PARQUET)
        .filter(pl.col("desig") != "")
        .filter(pl.col("mjd") > 15020)  # drop the four pre-1900 sentinel epochs (M0)
        .join(lon_df.lazy(), on="obscode", how="left")
        .with_columns(
            (pl.col("mjd") + pl.col("lon_deg").fill_null(0.0) / 360.0 + 0.5)
            .floor().cast(pl.Int32).alias("night")
        )
        .group_by("desig", "obscode", "night")
        .agg(
            pl.len().alias("n_obs"),
            pl.col("mjd").min().alias("mjd_first"),
            pl.col("mjd").max().alias("mjd_last"),
            pl.col("ra_deg").sort_by("mjd").first().alias("ra_first"),
            pl.col("ra_deg").sort_by("mjd").last().alias("ra_last"),
            pl.col("dec_deg").sort_by("mjd").first().alias("dec_first"),
            pl.col("dec_deg").sort_by("mjd").last().alias("dec_last"),
            pl.col("dec_deg").mean().alias("dec_mean"),
        )
        .filter((pl.col("n_obs") >= 2) & (pl.col("mjd_last") > pl.col("mjd_first")))
        .with_columns(
            ((pl.col("mjd_last") - pl.col("mjd_first")) * 24.0).alias("span_hours"),
            (((pl.col("ra_last") - pl.col("ra_first") + 180.0) % 360.0) - 180.0)
            .alias("dra_deg"),
        )
        .with_columns(
            (
                (
                    (pl.col("dra_deg") * pl.col("dec_mean").radians().cos()).pow(2)
                    + (pl.col("dec_last") - pl.col("dec_first")).pow(2)
                ).sqrt()
                * 3600.0
                / pl.col("span_hours")
            ).alias("rate_arcsec_hr")
        )
        .collect()
    )

    total = trk.height
    north = trk.filter(pl.col("dec_mean") > 30.0)
    slow_north = north.filter(pl.col("rate_arcsec_hr") < 10.0)
    robust = slow_north.filter(pl.col("span_hours") >= 0.5)

    by_code = (
        slow_north.group_by("obscode").agg(pl.len().alias("n"))
        .sort("n", descending=True).head(10)
    )
    by_year = (
        slow_north.with_columns(
            ((pl.col("mjd_first") - 51544.0) / 365.25 + 2000.0)
            .floor().cast(pl.Int32).alias("year")
        )
        .group_by("year").agg(pl.len().alias("n")).sort("year")
    )

    report = {
        "itf_provenance": json.loads(config.ITF_PROVENANCE.read_text(encoding="utf-8")),
        "definition": (
            "tracklets (desig x obscode x local night), n_obs >= 2, span > 0, "
            "endpoint great-circle rate < 10 arcsec/hr, mean Dec > +30 deg"
        ),
        "rate_measurable_tracklets": total,
        "dec_gt_30": north.height,
        "dec_gt_30_rate_lt_10": slow_north.height,
        "dec_gt_30_rate_lt_10_span_ge_30min": robust.height,
        "slow_north_by_obscode_top10": {
            str(r["obscode"]): int(r["n"]) for r in by_code.to_dicts()
        },
        "slow_north_by_year": {str(r["year"]): int(r["n"]) for r in by_year.to_dicts()},
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
