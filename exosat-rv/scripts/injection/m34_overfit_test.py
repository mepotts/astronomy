"""M34: is the CD-35 detection an artefact of tuning the extraction on the published RVs?

The manuscript's Table 1 says it plainly: "the scoring metric for every choice was the rms
against the published RV series". The extraction configuration -- order set, template
iteration, clipping, oversampling -- was selected by minimising disagreement with Hoy et al.'s
answer. The period search that follows is blind, and its epoch screen is internal, but its
INPUT was chosen with the published numbers in hand. So the chain is not independent end to
end, and a referee is entitled to ask whether a ~171 d peak was tuned into existence.

THE TEST. A configuration sweep already exists on disk -- M13_A..M13_J and the M14 variants,
each a complete RV series from the same spectra under a different configuration. For every
one of them this script computes two numbers that were never combined before:

    rms against the published series   -- the metric that SELECTED the adopted configuration
    blind-search dBIC near 171 d       -- the result that configuration was used to obtain

and then asks the only question that matters:

    Does the detection appear ONLY in the configurations that best match the published RVs?

  If dBIC correlates strongly with rms_pub, the detection tracks the tuning metric and the
  concern is real: better agreement with their answer is buying the signal.

  If the signal appears at similar strength across configurations INCLUDING rms-poor ones,
  it is a property of the spectra rather than of the selection, and the tuning is not what
  put it there.

Nothing here re-reduces anything. It re-scores runs that already exist, which is why it can
be run at all -- and it is the cheapest available answer to the sharpest question anyone has
asked about this reproduction.

⚠ ROUND 1 OF THIS SCRIPT WAS WRONG, and the way it was wrong is worth keeping. The period
search was reimplemented here "to avoid a dependency" -- a bad reason, since `blind_search.py`
takes a filename and there was no dependency to avoid -- and the reimplementation differed
from the project's in two ways that both crush the evidence toward zero. It combined orders by
taking viper's own `RV` column instead of the MEDIAN ACROSS PER-ORDER RVs, and it fitted with
inverse-variance weights from the `e_RV` column, which carries 400-1000 m/s against a true
epoch precision of 70-90 m/s, where the project fits UNWEIGHTED and scores
BIC = n log(RSS/n) + k log(n) rather than chi-squared. The adopted configuration came out at
dBIC ~ 0 where M14 measured +24.8, and the script duly announced that the detection tracks the
tuning metric. It does not; the tool was broken. This version imports the project's own
machinery so the numbers are comparable to M14's by construction.

Usage (WSL): ~/viperenv/bin/python scripts/injection/m34_overfit_test.py
"""
import glob
import io
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_published import load                   # noqa: E402  the project's own reader


def _import_bic_landscape():
    """Lift bic_landscape out of blind_search.py without running it.

    blind_search.py is a script: it reads sys.argv[1] at module level, so it cannot be
    imported. Copying the function is what produced round 1's wrong answer, so instead
    the function's own source is extracted and executed. One definition, one behaviour,
    and it fails loudly if the source ever moves.
    """
    import ast as _ast
    src = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'blind_search.py'), encoding='utf-8').read()
    tree = _ast.parse(src)
    for node in tree.body:
        if isinstance(node, _ast.FunctionDef) and node.name == 'bic_landscape':
            ns = {'np': np}
            exec(compile(_ast.Module([node], []), 'blind_search.py', 'exec'), ns)
            return ns['bic_landscape']
    raise SystemExit('bic_landscape not found in blind_search.py')


bic_landscape = _import_bic_landscape()

VIPER = os.path.expanduser("~/viper-src")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PUB = os.path.join(ROOT, "data", "published", "hoy2026_nature_table2_rvs.csv")

P_TARGET = 171.45          # the published period, used only to READ OFF the grid
P_WINDOW = 12.0            # d, how near the published period a peak must fall to count
PGRID = np.arange(20.0, 400.0, 0.25)
SPREAD_SCREEN = 3.0        # the M14 internal screen: drop epochs > 3x median across-order


def load_rvo(path):
    """BJD, RV, e_RV, BERV and the per-order RVs from a viper .rvo.dat."""
    rows = []
    with io.open(path, encoding="utf-8", errors="replace") as f:
        head = f.readline().split()
        for line in f:
            p = line.split()
            if len(p) < 8:
                continue
            try:
                rows.append([float(x) for x in p[:-1]])
            except ValueError:
                continue
    if not rows:
        return None
    a = np.array(rows)
    order_cols = [i for i, c in enumerate(head[:-1]) if c.startswith("rv")]
    return dict(bjd=a[:, 0], rv=a[:, 1], erv=a[:, 2], berv=a[:, 3],
                orders=a[:, order_cols] if order_cols else None)


def internal_screen(d):
    """M14's screen: drop epochs whose across-order spread exceeds 3x the median.
    Computed from our data alone -- it never sees a published number."""
    if d["orders"] is None or d["orders"].shape[1] < 3:
        return np.ones(len(d["bjd"]), bool)
    spread = np.nanstd(d["orders"], axis=1)
    med = np.nanmedian(spread)
    if not np.isfinite(med) or med <= 0:
        return np.ones(len(d["bjd"]), bool)
    return spread <= SPREAD_SCREEN * med


def series_and_dbic(path):
    """Build the series exactly as the project does and score it with the project's own
    landscape function: orders combined by MEDIAN, fitted UNWEIGHTED, scored as
    BIC = n log(RSS/n) + k log(n), with BERV carried as a nuisance covariate.

    Returns (t, y_median, berv, landscape) or None. The landscape columns are
    (period, dBIC, amplitude), on blind_search's own 5-460 d log grid.
    """
    try:
        c, orders = load(path)
    except Exception:
        return None
    if not orders:
        return None
    RV = np.array([np.where(np.isfinite(c[f'e_rv{o}']) & (c[f'e_rv{o}'] > 0),
                            c[f'rv{o}'], np.nan) for o in orders])
    y = np.nanmedian(RV, axis=0)
    t = np.asarray(c['BJD'], float)
    berv = np.asarray(c['BERV'], float)
    spread = np.nanstd(RV, axis=0)
    med = np.nanmedian(spread)
    keep = (spread <= SPREAD_SCREEN * med) if np.isfinite(med) and med > 0 \
        else np.ones(len(t), bool)
    keep &= np.isfinite(y)
    if keep.sum() < 8:
        return None
    land, n = bic_landscape(t[keep], y[keep], berv[keep])
    return t[keep], y[keep], berv[keep], land, int(n)


def published():
    t, v = [], []
    with io.open(PUB, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = [x.strip() for x in line.replace(",", " ").split()]
            try:
                a, b = float(p[0]), float(p[1])
            except (ValueError, IndexError):
                continue
            t.append(a)
            v.append(b)
    return np.array(t), np.array(v)


def rms_vs_published(d, keep, pt, pv):
    """rms of our series against the published one on matched epochs, best constant offset
    removed -- the metric the manuscript says selected the configuration."""
    ours_t, ours_v = d["bjd"][keep], d["rv"][keep]
    m_o, m_p = [], []
    for i, tt in enumerate(ours_t):
        j = int(np.argmin(np.abs(pt - tt)))
        if abs(pt[j] - tt) < 0.5:
            m_o.append(ours_v[i])
            m_p.append(pv[j])
    if len(m_o) < 5:
        return None, 0
    m_o, m_p = np.array(m_o), np.array(m_p)
    diff = m_o - m_p
    return float(np.std(diff - np.mean(diff))), len(m_o)


def main():
    pt, pv = published()
    print("# M34: does the detection track the metric that selected the configuration?")
    print(f"# published series: {len(pt)} epochs. Search machinery imported from")
    print("# blind_search.py, so dBIC is comparable to M14 by construction.")
    print("")

    series = sorted(glob.glob(os.path.join(VIPER, 'M13_?.rvo.dat')) +
                    glob.glob(os.path.join(VIPER, 'M14_*.rvo.dat')))
    print(f"{'config':<12s} {'n':>3s} {'rms_pub':>8s} {'best P':>8s} {'dBIC':>7s} {'P@171':>7s} {'dBIC':>7s} {'rank':>6s}")
    rows = []
    for path in series:
        name = os.path.basename(path).replace('.rvo.dat', '')
        got = series_and_dbic(path)
        if got is None:
            continue
        t, y, berv, land, n = got
        d = dict(bjd=t, rv=y)
        m_o, m_p = [], []
        for i, tt in enumerate(t):
            j = int(np.argmin(np.abs(pt - tt)))
            if abs(pt[j] - tt) < 0.5:
                m_o.append(y[i]); m_p.append(pv[j])
        if len(m_o) < 5:
            continue
        diff = np.array(m_o) - np.array(m_p)
        rms = float(np.std(diff - np.mean(diff)))
        i_best = int(np.nanargmax(land[:, 1]))
        near = np.abs(np.log(land[:, 0] / P_TARGET)) < 0.06
        if not near.any():
            continue
        sub = land[near]
        j = int(np.nanargmax(sub[:, 1]))
        d171, p171 = float(sub[j, 1]), float(sub[j, 0])
        rank = int(np.sum(land[:, 1] > d171)) + 1
        rows.append((name, rms, land[i_best, 0], land[i_best, 1], d171, p171, rank, n))
        print(f"{name:<12s} {n:>3d} {rms:>8.0f} {land[i_best,0]:>8.1f} {land[i_best,1]:>7.1f} {p171:>7.1f} {d171:>+7.1f} {rank:>6d}")

    if len(rows) < 4:
        print("\n# too few configurations recovered to test.")
        return
    rms = np.array([r[1] for r in rows])
    dnear = np.array([r[4] for r in rows])
    r = float(np.corrcoef(rms, dnear)[0, 1])
    print("\n" + "=" * 78)
    print(f"Configurations tested: {len(rows)}")
    print(f"rms vs published: {rms.min():.0f}-{rms.max():.0f} m/s (factor {rms.max()/max(rms.min(),1):.1f})")
    print(f"dBIC near {P_TARGET:.0f} d: {dnear.min():+.1f} to {dnear.max():+.1f}")
    print(f"\ncorrelation(rms_pub, dBIC@171) = {r:+.2f}")
    print("  strongly negative = better agreement with their answer buys the signal,")
    print("  which is the failure mode this test exists to catch.")
    med_rms = float(np.median(rms))
    poor = [x for x in rows if x[1] > med_rms]
    poor_det = [x for x in poor if x[4] > 10]
    print(f"\nAmong the {len(poor)} configurations that match the published series WORSE")
    print(f"than median, {len(poor_det)} still show dBIC > 10 near {P_TARGET:.0f} d.")
    print("")
    if len(poor_det) >= max(1, len(poor) // 3) and r > -0.6:
        print("READING: the signal is not confined to the best-matching configurations.")
        print("It survives where agreement with the published series is poor, so it is a")
        print("property of the spectra rather than of the selection metric. The tuning")
        print("remains a real limitation of the reproduction and should be stated, but it")
        print("is not what put the period there.")
    else:
        print("READING: the detection tracks the tuning metric, which would mean the")
        print("reproduction cannot be called independent. Re-derive the configuration from")
        print("injection recovery alone before publishing the blind-search framing.")


if __name__ == "__main__":
    main()
