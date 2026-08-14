"""M30 phase-BERV pre-checks (LESSONS §1.8: ten minutes before any campaign compute).

Reuses the m15_inventory.py step-[3] geometry: per trial period P, the R^2 of BERV
regressed on [cos, sin](2*pi t / P) over the actual epoch sampling. R^2 -> 1 means a
BERV nuisance term absorbs any orbit at that period (CD-35's -0.71 entanglement
at 171 d, three milestones' cost).

Two checks, both from data/m30-verify.json (no new queries; epoch times are the
median frame timestamp embedded in each night's dp_ids):

[1] HIP 65426 — does adding the three public HiRISE nights (2025-01-31/02-01/02-02)
    to M22's five slit nights change the BERV degeneracy structure, in particular
    over the P <= 100 d range where the M20 exomoon-regime limit lives?
    (The HiRISE nights are M27-class fibre data; this is the forward check for the
    day they yield RVs on the same target.)

[2] CD-35 2722 — the ten embargoed 116.2AP9 nights (observed, dates fixed, release
    2026-12-19 -> 2027-05-02): is the 171.454 d satellite phase clean of BERV over
    that sampling, i.e. will the release be a genuine out-of-sample test?

Writes data/m30-precheck.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

P_SAT = 171.454  # M14 blind-search period on CD-35 2722 B

M22_SLIT_NIGHTS = ["2024-03-11", "2025-04-07", "2025-04-15",
                   "2025-05-04", "2025-05-07"]
HIRISE_NIGHTS = ["2025-01-31", "2025-02-01", "2025-02-02"]


def night_times(ver: dict, target: str, nights: list[str]):
    """Median frame timestamp per night, from the dp_id-embedded UTC."""
    from astropy.time import Time
    out = []
    for d in nights:
        n = ver["targets"][target]["nights"][d]
        stamps = sorted(dp.split(".", 1)[1].rsplit(".", 1)[0]
                        for dp in n["dp_ids"] if dp and dp.startswith("CRIRE."))
        t = stamps[len(stamps) // 2].replace("T", " ")
        out.append(f"{t}")
    return Time([s.replace(" ", "T") for s in out], scale="utc")


def berv_for(ra: float, dec: float, t):
    from astropy.coordinates import EarthLocation, SkyCoord
    import astropy.units as u
    loc = EarthLocation.of_site("paranal")
    sc = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
    t2 = t.copy()
    t2.location = loc
    return sc.radial_velocity_correction("barycentric",
                                         obstime=t2).to_value("m/s")


def degeneracy(tt: np.ndarray, berv: np.ndarray,
               p_lo=5.0, p_hi=460.0, n=2000):
    periods = np.exp(np.linspace(np.log(p_lo), np.log(p_hi), n))
    b = berv - berv.mean()
    r2 = np.empty_like(periods)
    for i, P in enumerate(periods):
        w = 2 * np.pi / P
        A = np.column_stack([np.cos(w * tt), np.sin(w * tt), np.ones_like(tt)])
        coef, *_ = np.linalg.lstsq(A, b, rcond=None)
        r2[i] = 1 - (b - A @ coef).var() / b.var()
    bad = r2 > 0.5
    windows, start = [], None
    for i, flag in enumerate(bad):
        if flag and start is None:
            start = periods[i]
        if not flag and start is not None:
            windows.append([float(round(start, 1)), float(round(periods[i - 1], 1))])
            start = None
    if start is not None:
        windows.append([float(round(start, 1)), float(round(periods[-1], 1))])
    # merge windows separated by < 2% in period (grid noise, not structure)
    merged: list[list[float]] = []
    for w in windows:
        if merged and w[0] <= merged[-1][1] * 1.02:
            merged[-1][1] = max(merged[-1][1], w[1])
        else:
            merged.append(list(w))
    return periods, r2, merged, float(bad.mean())


def r2_at(tt: np.ndarray, berv: np.ndarray, P: float) -> float:
    b = berv - berv.mean()
    w = 2 * np.pi / P
    A = np.column_stack([np.cos(w * tt), np.sin(w * tt), np.ones_like(tt)])
    coef, *_ = np.linalg.lstsq(A, b, rcond=None)
    return float(1 - (b - A @ coef).var() / b.var())


def main() -> None:
    ver = json.loads((ROOT / "data" / "m30-verify.json").read_text(encoding="utf-8"))
    out: dict = {}

    # ---------- [1] HIP 65426 ----------
    tgt = ver["targets"]["HIP 65426"]
    ra, dec = tgt["ra"], tgt["dec"]
    print("=== [1] HIP 65426: M22 slit sampling vs slit+HiRISE ===", flush=True)
    res1 = {}
    for label, nights in (("5 slit (M22)", M22_SLIT_NIGHTS),
                          ("8 = slit + HiRISE", M22_SLIT_NIGHTS + HIRISE_NIGHTS)):
        t = night_times(ver, "HIP 65426", sorted(nights))
        berv = berv_for(ra, dec, t)
        tt = t.mjd
        periods, r2, windows, frac = degeneracy(tt, berv)
        sub100 = r2[periods <= 100]
        p100 = periods[periods <= 100]
        w100 = [w for w in windows if w[0] <= 100]
        print(f"  {label}: n={len(nights)} baseline={tt.max()-tt.min():.0f} d "
              f"BERV span={berv.max()-berv.min():.0f} m/s")
        print(f"    degenerate fraction (R^2>0.5): {frac:.3f}  "
              f"windows: {windows}")
        print(f"    P<=100 d: max R^2={sub100.max():.2f} at "
              f"{p100[np.argmax(sub100)]:.1f} d; degenerate windows <=100 d: "
              f"{w100 or 'none'}", flush=True)
        res1[label] = {
            "nights": sorted(nights),
            "mjd": [round(float(x), 5) for x in tt],
            "berv_ms": {d: round(float(v), 1)
                        for d, v in zip(sorted(nights), berv)},
            "baseline_d": round(float(tt.max() - tt.min()), 1),
            "berv_span_ms": round(float(berv.max() - berv.min()), 1),
            "frac_degenerate_r2_gt_0.5": round(frac, 3),
            "degenerate_windows_d": windows,
            "max_r2_below_100d": round(float(sub100.max()), 3)}
    out["hip65426"] = res1

    # ---------- [2] CD-35 2722: the embargoed out-of-sample epochs ----------
    tgt = ver["targets"]["CD-35 2722"]
    ra, dec = tgt["ra"], tgt["dec"]
    emb = sorted(d for d, n in tgt["nights"].items()
                 if not n["public_now"] and "116.2AP9" in ",".join(n["progs"]))
    print("\n=== [2] CD-35 2722: embargoed 116.2AP9 epochs at P=171.454 d ===",
          flush=True)
    t = night_times(ver, "CD-35 2722", emb)
    berv = berv_for(ra, dec, t)
    tt = t.mjd
    phase = (tt / P_SAT) % 1.0
    r2sat = r2_at(tt, berv, P_SAT)
    periods, r2, windows, frac = degeneracy(tt, berv)
    # phase coverage: largest gap in sorted phase (cyclic)
    ph = np.sort(phase)
    gaps = np.diff(np.concatenate([ph, [ph[0] + 1.0]]))
    print(f"  n={len(emb)} nights {emb[0]} -> {emb[-1]} "
          f"(release {tgt['nights'][emb[0]]['release_max'][:10]} -> "
          f"{tgt['nights'][emb[-1]]['release_max'][:10]})")
    print(f"  BERV span {berv.max()-berv.min():.0f} m/s")
    print(f"  R^2(BERV | 171.454 d) = {r2sat:.2f}   "
          f"(CD-35's original entanglement: r=-0.71 -> R^2~0.5)")
    print(f"  171-d phase coverage: {len(emb)} epochs, largest gap "
          f"{gaps.max():.2f} cycles; phases: "
          f"{', '.join(f'{p:.2f}' for p in sorted(phase))}")
    print(f"  full-grid degenerate fraction: {frac:.3f}  windows: {windows}",
          flush=True)
    out["cd35_embargoed"] = {
        "nights": emb,
        "berv_ms": {d: round(float(v), 1) for d, v in zip(emb, berv)},
        "r2_berv_at_171.454d": round(r2sat, 3),
        "phase_at_171.454d": {d: round(float(p), 3)
                              for d, p in zip(emb, phase)},
        "largest_phase_gap_cycles": round(float(gaps.max()), 3),
        "frac_degenerate_r2_gt_0.5": round(frac, 3),
        "degenerate_windows_d": windows}

    # ---- [2b] combined: existing H-monitoring series + the embargoed epochs ----
    # Existing set approximated as the public H-band monitoring nights
    # 2023-10-13 -> 2025-01-21 minus the screened fatal epoch 2024-10-21
    # (M14's series is 18 of these; the geometry is insensitive at that level).
    old = sorted(d for d, n in tgt["nights"].items()
                 if n["public_now"] and "2023-10-13" <= d <= "2025-01-21"
                 and d != "2024-10-21"
                 and any(p.startswith(("112.25HG", "114.271E"))
                         for p in n["progs"]))
    both = old + emb
    tb = night_times(ver, "CD-35 2722", both)
    bb = berv_for(ra, dec, tb)
    r2_old = r2_at(night_times(ver, "CD-35 2722", old).mjd,
                   berv_for(ra, dec, night_times(ver, "CD-35 2722", old)), P_SAT)
    r2_both = r2_at(tb.mjd, bb, P_SAT)
    print(f"\n  [2b] combined-series geometry at 171.454 d:")
    print(f"    existing series ({len(old)} kept nights): R^2 = {r2_old:.2f}")
    print(f"    combined ({len(both)} nights):            R^2 = {r2_both:.2f}",
          flush=True)
    out["cd35_combined"] = {
        "existing_nights_used": old,
        "r2_existing_at_171.454d": round(r2_old, 3),
        "r2_combined_at_171.454d": round(r2_both, 3)}

    p = ROOT / "data" / "m30-precheck.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {p}", flush=True)


if __name__ == "__main__":
    main()
