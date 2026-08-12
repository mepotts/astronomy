"""Assemble the draft manuscript: inline the four SVG figures into the template.

Reads docs/paper/draft.template.html, replaces {{FIGn}} with <figure> blocks whose
images are base64 SVG data URIs (isolated namespaces — no clip-path id collisions),
writes docs/paper/cd35-etatel-draft.html.
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
    "FIG4": ("fig4_limit.svg",
             "<b>Figure 4.</b> η Tel B: injection-calibrated 90% companion exclusion "
             "(blue curve and shading; detection = ΔBIC ≥ 10 and rank 1 at the injected "
             "period, phase-marginalized). The CD-35 2722 B satellite, scaled to "
             "η Tel B's host mass (orange diamond), sits at the boundary — a twin would "
             "have been detected with ~70% probability. Dashed line: the pre-analysis "
             "survey forecast (3.3 M_Jup)."),
}

html = TPL.read_text(encoding="utf-8")
for key, (fname, caption) in CAPTIONS.items():
    svg = (EXP / fname).read_bytes()
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg).decode()
    block = (f'<figure><img src="{uri}" alt="{key}">'
             f"<figcaption>{caption}</figcaption></figure>")
    html = html.replace("{{" + key + "}}", block)

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size // 1024} kB)")
