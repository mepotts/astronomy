"""M4 Q4 figure: threshold separation vs contrast for archival WISE centroid vetting."""
import sys, warnings, json
sys.stdout.reconfigure(encoding="utf-8"); warnings.filterwarnings("ignore")
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "c:/Users/matth/projects/astronomy/dyson-revet/"
S = json.load(open(ROOT+"out/m4_jwstD_summary.json"))
SEP = S["sep_arcsec"]; rW3 = S["rho_W3"]; rW4 = S["rho_W4"]
RMAX = 3.25   # Suazo et al. 2024 / Hephaistos IV Sec 5.1 W3-PSF contamination radius

rho = np.logspace(-0.6, 3.2, 500)
fig, ax = plt.subplots(1, 2, figsize=(12.4, 5.2))

a = ax[0]
for F, c in [(1.0, "tab:blue"), (1.5, "tab:purple"), (2.0, "tab:red")]:
    a.plot(rho, F*(1+1/rho), color=c, lw=2, label=f'floor = {F:.1f}"')
    a.axhline(F, color=c, ls=":", lw=1)
a.fill_between(rho, 0, 2.0*(1+1/rho), color="tab:red", alpha=0.06)
a.scatter([rW3], [SEP], marker="*", s=320, color="k", zorder=6)
a.annotate(f'candidate D at W3\n$\\rho$={rW3:.0f}, sep={SEP:.2f}"', (rW3, SEP),
           xytext=(2.2, 3.4), fontsize=9, arrowprops=dict(arrowstyle="->", lw=1.2))
a.axhline(SEP, color="k", ls="--", lw=1.1)
a.text(0.30, SEP*1.04, "D's measured separation", fontsize=8)
a.set_xscale("log"); a.set_xlim(0.3, 1500); a.set_ylim(0.7, 7)
a.set_xlabel(r"contrast  $\rho = f_{\rm contaminant}/f_{\rm star}$  in the WISE band")
a.set_ylabel("separation needed to clear the floor (arcsec)")
a.set_title("Threshold separation vs contrast\n"
            r"offset $=$ sep$\cdot\rho/(1+\rho) > F$   $\Leftrightarrow$   sep $> F(1+1/\rho)$", fontsize=10)
a.legend(fontsize=9); a.grid(alpha=0.25)
a.text(0.35, 0.78, "shaded: invisible to a 2\" floor", fontsize=8, color="tab:red")

b = ax[1]
for F, c in [(1.0, "tab:blue"), (1.5, "tab:purple"), (2.0, "tab:red")]:
    b.plot(rho, np.minimum(F*(1+1/rho)/RMAX, 1)**2*100, color=c, lw=2, label=f'floor = {F:.1f}"')
    b.axhline(min(F/RMAX, 1)**2*100, color=c, ls=":", lw=1)
    b.text(400, min(F/RMAX, 1)**2*100*1.05, f"{min(F/RMAX,1)**2*100:.0f}% floor asymptote",
           fontsize=7.5, color=c)
b.axvline(rW3, color="k", ls="--", lw=1.1)
b.text(rW3*1.15, 78, f"D at W3\n$\\rho$={rW3:.0f}", fontsize=8.5)
b.set_xscale("log"); b.set_xlim(0.3, 1500); b.set_ylim(0, 100)
b.set_xlabel(r"contrast  $\rho = f_{\rm contaminant}/f_{\rm star}$")
b.set_ylabel(f'fraction of contaminants invisible to centroid vetting (%)')
b.set_title(f"Blind fraction of a uniform background population\n"
            f'inside the WISE W3 PSF radius ({RMAX}", Suazo+24)', fontsize=10)
b.legend(fontsize=9, loc="center right"); b.grid(alpha=0.25)

fig.suptitle("Q4 — what the JWST measurement of candidate D calibrates about the archival "
             "1-2\" centroid floor", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(ROOT+"out/m4_jwstD_centroid_threshold.png", dpi=145)
print("wrote out/m4_jwstD_centroid_threshold.png")
