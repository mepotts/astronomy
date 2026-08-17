"""Assemble the draft manuscript: inline the twelve SVG figures into the template.

Reads docs/paper/draft.template.html, replaces {{FIGn}} with <figure> blocks whose
images are base64 SVG data URIs (isolated namespaces — no clip-path id collisions),
writes docs/paper/cd35-etatel-draft.html.

Figures 1-4 (m16_figures.py) carry a caption only. Figures 5-12 (m18_figures.py) each
answer one numbered figure in H26, so they also carry a pairing header naming the H26
figure and the verdict — see PAIRS.
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "data" / "export"
TPL = ROOT / "docs" / "paper" / "draft.template.html"
OUT = ROOT / "docs" / "paper" / "cd35-etatel-draft.html"

CAPTIONS = {
    "FIG1": ("fig1_cd35_series.svg",
             "<b>Figure 1.</b> CD-35 2722 B radial velocities: the published series "
             "(orange, 23 epochs with published errors) and this work's from-raw "
             "per-nodding extraction (blue, mean order combine, internal error bars = "
             "across-order scatter/√11), matched on 17 archival nights. Bottom: "
             "night-by-night difference after removing one constant offset; shaded band "
             "= ±1 rms (90 m s⁻¹). The 2026 epochs exist only in the published table — "
             "their raw frames are still under embargo."),
    "FIG2": ("fig2_phasefold.svg",
             "<b>Figure 2.</b> Both series folded at the published period "
             "(171.454 d), with the published circular orbit (K = 306 m s⁻¹) fitted "
             "for phase and offset only. Our amplitude runs high (§4) — visible here as "
             "blue points overshooting the curve at the quadratures."),
    "FIG3": ("fig3_landscapes.svg",
             "<b>Figure 3.</b> Blind period search (ΔBIC of a circular Keplerian vs a "
             "constant; internally screened series). Left: CD-35 2722 B — the published "
             "period family is the top peak at ΔBIC = +40, and remains the top peak at "
             "+27 with a BERV nuisance covariate (orange). Right: η Tel B under the "
             "identical machinery — no credible peak; the sub-20 d comb moves between "
             "extraction routes and combines and is treated as a sampling alias. "
             "Dotted vertical line: 171.45 d in both panels; dashed: ΔBIC = 10."),
    # ---- the H26 figure-match set (§7), from m18_figures.py --------------------
    "FIG5": ("fig5_periodograms.svg",
             "<b>Figure 4.</b> Generalised Lomb-Scargle periodograms, computed "
             "identically on both series: left, <span class='them'>H26</span>'s "
             "published 23-epoch table; right, this work's 17 from-raw nights. Top "
             "row, the RVs; middle and bottom, the residuals after removing one and "
             "two circular signals at the published periods. Dashed rules are the 10%, "
             "1% and 0.1% false-alarm levels (bottom to top); the dotted vertical is "
             "171.45 d; triangles mark each panel's top peak. The published series "
             "peaks at 171.0 d (power 0.85), ours at 170.3 d (power 0.93). In the "
             "one-satellite residuals their second signal appears at 87.2 d; ours does "
             "not — our residual peak is at 44.3 d, below the 1% level."),
    "FIG6": ("fig6_models.svg",
             "<b>Figure 5.</b> Both RV series with the orbit models drawn over them, "
             "in the layout of <span class='them'>H26</span>'s Fig. 2: one satellite "
             "above, two below. Curves are the posterior-median models from this "
             "work's nested sampling on the published table; points are the published "
             "RVs (orange) and this work's from-raw extraction (blue, error bars = "
             "across-order scatter/√11). The gaps are the seasonal visibility windows; "
             "the final orange points are the embargoed 2026 epochs, which exist only "
             "in the published table."),
    "FIG7": ("fig7_nodding.svg",
             "<b>Figure 6.</b> The measurement <span class='them'>H26</span>'s Fig. 4 "
             "makes — the gain from extracting the two nodding positions separately "
             "rather than combining the spectra first — made again here. The "
             "percentage is plotted because it is the only quantity the two papers "
             "share: they report a mean internal RV error, we report rms against their "
             "published series, and each row prints its own absolute pair. The "
             "direction is confirmed and, on a robust order combine, exceeded; on a "
             "plain mean combine over all 17 nights it reverses."),
    "FIG8": ("fig8_p2posteriors.svg",
             "<b>Figure 7.</b> Period posterior for the <em>second</em> signal on "
             "<span class='them'>H26</span>'s own table, in the structure of their "
             "Fig. 5. Top: a wide prior, P₂ ~ U(5, 150) d, with dashed rules at the "
             "four peaks they report — three of the four (70, 88, 115 d) reappear "
             "unprompted, 14 d does not. Bottom: the four windowed fits, each labelled "
             "with its evidence against a single eccentric satellite on the same data "
             "under the same priors. The 88 d window is the best of the four, as they "
             "conclude — and still loses to one satellite by ΔlnZ = −2.8."),
    "FIG9": ("fig9_windowmodels.svg",
             "<b>Figure 8.</b> The four high-evidence two-satellite models drawn "
             "through the published RVs, matching <span class='them'>H26</span>'s "
             "Fig. 6. Their argument against the 14 d solution reproduces directly: it "
             "is the same implausible high-frequency comb, unsupportable at this "
             "cadence. Every panel's ΔlnZ is negative — the ranking among the four "
             "reproduces, the case for any of them does not."),
    "FIG10": ("fig10_viper_gls.svg",
              "<b>Figure 9.</b> GLS periodograms of every viper output, "
              "<span class='them'>H26</span>'s Fig. 7, plus the panel it does not "
              "contain. Each panel prints its own top peak and its power at 171 d; the "
              "dotted vertical is 171.45 d. Their conclusion holds — no instrumental "
              "or atmospheric parameter repeats the RV periodicity, the largest being "
              "the linear wavelength coefficient at 0.42, most below 0.2. The "
              "barycentric correction is not a viper output and so is absent from "
              "their grid; here it carries power 0.66 at the signal period. RV panel: "
              "this work's final per-nodding series. Nuisance panels: per-epoch medians "
              "over orders from the archive-route run committed in <code>data/viper/</code>."),
    "FIG11": ("fig11_corner_sat1.svg",
              "<b>Figure 10.</b> Corner plot for the large satellite — "
              "<span class='them'>H26</span>'s Fig. 8 — from a one-satellite eccentric "
              "fit to their published table. Orange rules and crosses are their "
              "Table 1 values; blue dotted lines are our 16/50/84th percentiles. Their "
              "period and mass sit inside our posterior; only eccentricity is "
              "marginally high (0.38 ± 0.09 against their 0.269). m sin i is derived "
              "with a host mass calibrated so that their own (P, K, e) return their own "
              "m sin i — 38.1 M<sub>Jup</sub>, within Wahhaj et al. (2011)'s 31 ± 8 — "
              "so the mass axes are on one scale."),
    "FIG12": ("fig12_corner_sat2.svg",
              "<b>Figure 11.</b> Corner plot for the small satellite — "
              "<span class='them'>H26</span>'s Fig. 9 — from the two-satellite "
              "eccentric fit, P₂ confined to their own 75–100 d window. The period "
              "recovers (90.4<sup>+5.4</sup><sub>−8.0</sub> d against their 87.349), "
              "and the amplitude does not: K₂ peaks at zero and m sin i = "
              "0.07<sup>+0.08</sup><sub>−0.05</sub> M<sub>Jup</sub> leaves their 0.219 "
              "in the tail, with e₂ prior-dominated. Under the circular pairing of "
              "their Table 1 the amplitude is better behaved (K₂ = 105 ± 20 m s⁻¹); "
              "the eccentric fit shown here is the one that matches the parameter set "
              "of their figure."),
}

# Figures 5-12 answer a numbered H26 figure; the header strip states which, and the
# verdict class picks the colour (yes / part / no).
PAIRS = {
    "FIG5": ("H26 Fig. 1", "Figure 4", "reproduces", "yes"),
    "FIG6": ("H26 Fig. 2", "Figure 5", "reproduces", "yes"),
    "FIG7": ("H26 Fig. 4", "Figure 6", "direction confirmed", "part"),
    "FIG8": ("H26 Fig. 5", "Figure 7", "peaks yes · evidence no", "part"),
    "FIG9": ("H26 Fig. 6", "Figure 8", "ranking yes · case no", "part"),
    "FIG10": ("H26 Fig. 7", "Figure 9", "reproduces, and extends", "yes"),
    "FIG11": ("H26 Fig. 8", "Figure 10", "reproduces", "yes"),
    "FIG12": ("H26 Fig. 9", "Figure 11", "does not reproduce", "no"),
}

html = TPL.read_text(encoding="utf-8")
for key, (fname, caption) in CAPTIONS.items():
    svg = (EXP / fname).read_bytes()
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
    head, cls = "", ""
    if key in PAIRS:
        theirs, ours, verdict, vcls = PAIRS[key]
        cls = " class=\"pair\""
        head = (f'<div class="pairhead"><span class="chip them">{theirs}</span>'
                f'<span class="to">answered by</span>'
                f'<span class="chip us">{ours}</span>'
                f'<span class="verdict {vcls}">{verdict}</span></div>')
    block = (f'<figure{cls}>{head}<img src="{uri}" alt="{key}">'
             f"<figcaption>{caption}</figcaption></figure>")
    html = html.replace("{{" + key + "}}", block)

missing = [k for k in CAPTIONS if "{{" + k + "}}" in html]
assert not missing, f"placeholder left unfilled: {missing}"
assert "{{" not in html, "template still has an unreplaced placeholder"

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} kB)")
