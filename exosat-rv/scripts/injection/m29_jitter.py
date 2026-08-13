"""M29 / A1: the radial-velocity jitter floor of directly imaged companions.

Every proposal in this genre guesses the astrophysical RV noise floor of a young
self-luminous giant. This project can measure it, because it holds multi-epoch RVs for
~11 companions spanning M7 -> L -> T, all reduced through one pipeline whose velocity
transmission is injection-verified per target.

The decomposition uses no formal errors at all -- viper's are not trustworthy (M12) --
only the data's own two timescales:

  within-night   frames of the same night are minutes apart. A companion satellite on
                 an orbit of days-to-years moves < 1 m/s in that time (M12 sec 8), so
                 frame-to-frame scatter inside a night is pure measurement noise plus
                 any genuinely fast astrophysical variability.
  night-to-night scatter of the nightly means carries measurement noise AND slow
                 astrophysical variability (rotation, weather, accretion, companions).

The nightly mean of n frames carries measurement noise sigma_w / sqrt(n), so

    jitter^2 = var(nightly means) - mean(sigma_w^2 / n)

and a negative result means the series is consistent with pure measurement noise -- an
upper limit, reported as such rather than clipped silently.

IMPORTANT framing. Within-night scatter is a LOWER BOUND on measurement noise, not an
estimate of it: airmass, telluric column, wavelength solution and template registration
all drift between nights and not within one. The excess computed here therefore contains
astrophysical variability AND night-to-night instrumental systematics, and is an UPPER
BOUND on jitter. That is still the number a proposal needs -- what limits an exomoon
search is the total night-to-night floor, not its split -- but it must not be quoted as
purely astrophysical.

Two built-in controls: CD-35 2722 B carries a real satellite signal (published
K = 306 m/s; fitted here at 426-472 m/s by direct fit at the published period) and
must show a large resolved excess; eta Tel B carries the project's tightest null and should
be consistent with zero.

Usage (WSL): python m29_jitter.py label=path [label=path ...]
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vs_published import load  # noqa: E402

NIGHT_TOL = 0.2

# Spectral type / mass / age, with the source milestone. Masses in M_Jup, ages in Myr.
# "-" where this project never needed the number.
CONTEXT = {
    "yses1":     ("YSES 1 b",      "L0",   "~6",    "~16",   "M26"),
    "hd19467":   ("HD 19467 B",    "T5.5", "~65",   "~9000", "M26"),
    "m0103a":    ("2M0103AB b",    "L",    "~13",   "~30",   "M26"),
    "cd35":      ("CD-35 2722 B",  "L0",   "31-37", "~120",  "M14 (has a real signal)"),
    "hip81208":  ("HIP 81208 B",   "M",    "~67",   "~17",   "M26 (H staring)"),
    "h81208k":   ("HIP 81208 B",   "M",    "~67",   "~17",   "M26 (K nodding)"),
    "etatel":    ("eta Tel B",     "M7.5", "~47",   "~24",   "M15"),
    "pds70":     ("PDS 70 (star)", "K7",   "star",  "~5",    "M20 (accreting host)"),
    "hip65426":  ("HIP 65426 b",   "L",    "~8",    "~14",   "M20"),
    "abpicb":    ("AB Pic b",      "L0",   "~14",   "~45",   "M17"),
    "ctchab":    ("CT Cha B",      "M8",   "~17",   "~2",    "M17 (accreting)"),
    "betapicb":  ("beta Pic b",    "L",    "~13",   "~16",   "M17/M20 (contaminated)"),
    "bpb2":      ("beta Pic b",    "L",    "~13",   "~16",   "M20 v2 (contaminated)"),
    "bpb3":      ("beta Pic b",    "L",    "~13",   "~16",   "M20 v3 (contaminated)"),
    "hd1160":    ("HD 1160 B",     "M",    "~80",   "~100",  "M23 (quality-limited)"),
    "hd206893h": ("HD 206893 B",   "L",    "~30",   "~250",  "M26 (H)"),
    "hd206893k": ("HD 206893 B",   "L",    "~30",   "~250",  "M26 (K)"),
    "aflep":     ("AF Lep b",      "L",    "~3",    "~24",   "M23 (dilution-limited)"),
}


def frames(path):
    """Per-frame median-combined RV, its across-order noise estimate, and BJD.

    The second noise channel is the across-order dispersion divided by sqrt(N_orders):
    the error on the frame's combined RV implied by how much its own orders disagree.
    It has N_orders - 1 degrees of freedom per frame rather than n_frames - 1 per night,
    which is why it has the statistical power the within-night channel lacks -- and,
    crucially, it is invariant to a common-mode velocity by construction (M12), so it
    measures noise without ever seeing the signal.
    """
    c, orders = load(path)
    RV = np.array([np.where(np.isfinite(c[f"e_rv{o}"]) & (c[f"e_rv{o}"] > 0),
                            c[f"rv{o}"], np.nan) for o in orders])
    with np.errstate(all="ignore"):
        # Per-order centering. Each order carries a large STATIC zero-point offset
        # (M12/M14: raw across-order dispersion is ~1300 m/s on CD-35 while the
        # epoch-to-epoch scatter is 330), which cancels epoch to epoch and must be
        # removed before the dispersion can estimate a random error. Subtracting a
        # per-order constant cannot remove a common-mode signal, so this is
        # signal-preserving -- M14 adopted the same centering for its best combines.
        RV = RV - np.nanmedian(RV, axis=1)[:, None]
        v = np.nanmedian(RV, axis=0)
        nok = np.sum(np.isfinite(RV), axis=0)
        disp = np.nanstd(RV - v[None, :], axis=0, ddof=1)
        e_ord = 1.2533 * disp / np.sqrt(np.maximum(nok, 1))   # median -> mean efficiency
    t = np.asarray(c["BJD"], float)
    g = np.isfinite(t) & np.isfinite(v)
    return t[g], v[g], e_ord[g], nok[g], len(orders)


def group_nights(t, tol=NIGHT_TOL):
    i = np.argsort(t)
    t = t[i]
    out, cur = [], [i[0]]
    ts = t
    for j in range(1, len(ts)):
        if ts[j] - ts[j - 1] < tol:
            cur.append(i[j])
        else:
            out.append(cur)
            cur = [i[j]]
    out.append(cur)
    return out


def analyse(label, path):
    if not os.path.exists(path):
        return None
    t, v, e_ord, nok, nord = frames(path)
    if len(t) < 2:
        return None
    groups = group_nights(t)
    means, ns, within, e_nights, dof_ord = [], [], [], [], 0
    for g in groups:
        vv = v[g]
        means.append(vv.mean())
        ns.append(len(vv))
        if len(vv) > 1:
            within.append(np.sum((vv - vv.mean()) ** 2))
        ee = e_ord[g]
        ee = ee[np.isfinite(ee)]
        if len(ee):
            # error on the nightly mean from the across-order channel
            e_nights.append(np.sqrt(np.sum(ee ** 2)) / len(ee))
            dof_ord += int(np.sum(np.maximum(nok[g] - 1, 0)))
    means = np.array(means, float)
    ns = np.array(ns, int)
    n_nights = len(means)
    # pooled within-night variance across all multi-frame nights
    dof = int(np.sum(ns[ns > 1] - 1))
    sig_w = np.sqrt(np.sum(within) / dof) if dof > 0 else np.nan
    if n_nights < 2:
        return dict(label=label, name=CONTEXT.get(label, (label,))[0], nights=n_nights,
                    frames=len(t), orders=nord, sig_w=sig_w, night_rms=np.nan,
                    noise_on_mean=np.nan, jitter=np.nan, limit=True)
    night_rms = np.std(means, ddof=1)
    f_night = 1.0 / np.sqrt(2 * (n_nights - 1))
    var_n = night_rms ** 2

    def excess_vs(noise, dof_noise):
        """Excess variance of the nightly means over a noise model, with its error."""
        if not np.isfinite(noise) or noise <= 0:
            return dict(noise=np.nan, jitter=np.nan, sig=np.nan, lim=np.nan,
                        resolved=False)
        var_e = noise ** 2
        f_e = 1.0 / np.sqrt(2 * dof_noise) if dof_noise > 0 else np.inf
        ex = var_n - var_e
        e_ex = np.hypot(2 * var_n * f_night, 2 * var_e * f_e)
        s = ex / e_ex if np.isfinite(e_ex) and e_ex > 0 else np.nan
        return dict(noise=noise, jitter=np.sqrt(ex) if ex > 0 else np.nan, sig=s,
                    lim=np.sqrt(max(ex, 0.0) + 2 * e_ex) if np.isfinite(e_ex) else np.nan,
                    resolved=bool(np.isfinite(s) and s >= 2.0 and ex > 0))

    w = excess_vs(np.sqrt(np.mean(sig_w ** 2 / ns)) if np.isfinite(sig_w) else np.nan, dof)
    o = excess_vs(np.sqrt(np.mean(np.array(e_nights, float) ** 2)) if e_nights else np.nan,
                  dof_ord)
    return dict(label=label, name=CONTEXT.get(label, (label,))[0], nights=n_nights,
                frames=len(t), orders=nord, sig_w=sig_w, night_rms=night_rms,
                span=t.max() - t.min(), dof_w=dof, dof_o=dof_ord,
                noise_on_mean=w["noise"], jitter=w["jitter"], sig=w["sig"],
                jit_lim=w["lim"], resolved=w["resolved"], limit=not w["resolved"],
                o_noise=o["noise"], o_jitter=o["jitter"], o_sig=o["sig"],
                o_lim=o["lim"], o_resolved=o["resolved"])


# Series that cannot measure a companion's jitter, with the reason. Reported apart
# from the science table so the headline is not polluted by known-bad data.
EXCLUDE = {
    "betapicb": "starlight-contaminated (M20)",
    "bpb2": "starlight-contaminated (M20)",
    "bpb3": "starlight-contaminated (M20)",
    "hip81208": "HiRISE fibre data mis-reduced through the slit recipe (M27)",
    "aflep": "HiRISE fibre data mis-reduced through the slit recipe (M27)",
    "hd1160": "quality-limited, 41 d baseline (M23)",
    "pds70": "the host star, not the companion (M20)",
}


def show(rows, title):
    if not rows:
        return
    print(f"\n{title}")
    print(f"# {'object':<16s} {'SpT':<6s} {'nt':>3s} {'fr':>4s} {'span':>6s} "
          f"{'night':>7s} | {'noise_o':>8s} {'dof':>5s} {'FLOOR_o':>9s} {'sig':>5s} | "
          f"{'noise_w':>8s} {'floor_w':>9s} {'sig':>5s}")
    for r in sorted(rows, key=lambda x: (x["night_rms"] if np.isfinite(x["night_rms"])
                                         else 9e9)):
        c = CONTEXT.get(r["label"], (r["label"], "-", "-", "-", "-"))

        def cell(res, jit, lim):
            return (f"{jit:>9.0f}" if res
                    else f"{'<' + format(lim, '.0f') if np.isfinite(lim) else '-':>9s}")
        so = f"{r['o_sig']:>5.1f}" if np.isfinite(r.get("o_sig", np.nan)) else f"{'-':>5s}"
        sw = f"{r['sig']:>5.1f}" if np.isfinite(r.get("sig", np.nan)) else f"{'-':>5s}"
        print(f"  {c[0]:<16s} {c[1]:<6s} {r['nights']:>3d} {r['frames']:>4d} "
              f"{r.get('span', 0):>6.0f} {r['night_rms']:>7.0f} | "
              f"{r['o_noise']:>8.0f} {r['dof_o']:>5d} "
              f"{cell(r['o_resolved'], r['o_jitter'], r['o_lim'])} {so} | "
              f"{r['noise_on_mean']:>8.0f} "
              f"{cell(r['resolved'], r['jitter'], r['jit_lim'])} {sw}")


def main():
    rows = []
    for spec in [a for a in sys.argv[1:] if "=" in a]:
        label, path = spec.split("=", 1)
        r = analyse(label, path)
        if r:
            rows.append(r)
    print("# M29: the night-to-night RV floor of directly imaged companions.")
    print("# Excess of nightly-mean scatter over within-night frame scatter. Contains")
    print("# astrophysical variability AND night-to-night instrumental systematics, so")
    print("# it is an UPPER BOUND on jitter. No formal errors are used anywhere.")
    print("# 'floor' resolved only at >= 2 sigma; otherwise a 95% bound.")

    good = [r for r in rows if r["label"] not in EXCLUDE and np.isfinite(r["night_rms"])]
    bad = [r for r in rows if r["label"] in EXCLUDE and np.isfinite(r["night_rms"])]
    show(good, "## Companions with usable series")
    show(bad, "## Excluded from the science table (reason below)")
    for r in sorted(bad, key=lambda x: x["label"]):
        print(f"#   {CONTEXT.get(r['label'], (r['label'],))[0]:<16s} "
              f"{EXCLUDE[r['label']]}")

    res = [r for r in good if r.get("o_resolved")]
    lim = [r for r in good if not r.get("o_resolved") and np.isfinite(r.get("o_lim", np.nan))]
    print(f"\n# {len(res)} of {len(good)} usable series resolve an excess at >= 2 sigma.")
    if res:
        j = np.array([r["o_jitter"] for r in res])
        print(f"#   resolved: {', '.join(CONTEXT.get(r['label'], (r['label'],))[0] for r in res)}"
              f"  ({j.min():.0f}-{j.max():.0f} m/s)")
    if lim:
        b = np.array([r["o_lim"] for r in lim])
        print(f"#   unresolved, best 95% bound: {b.min():.0f} m/s "
              f"({CONTEXT.get(lim[int(np.argmin(b))]['label'], ('?',))[0]})")


if __name__ == "__main__":
    main()
