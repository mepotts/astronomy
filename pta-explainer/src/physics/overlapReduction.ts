/**
 * Illustrative multipole overlap-reduction functions (ORFs): the MONOPOLE and DIPOLE
 * reference shapes drawn alongside the Hellings–Downs QUADRUPOLE on the §3 plot.
 *
 * WHY THESE EXIST (the pedagogy this file carries):
 * The headline of the 2023 PTA result is not merely that pulsar pairs correlate, but that
 * they correlate with a specific ANGULAR shape — the quadrupolar Hellings–Downs curve. That
 * shape is the smoking gun for a gravitational-wave background, because the rival systematics
 * imprint DIFFERENT angular shapes:
 *   • CLOCK / timing-standard errors  →  a MONOPOLE: a common offset added to every pulsar
 *     pair by the same amount, independent of their separation on the sky → a FLAT line.
 *   • SOLAR-SYSTEM EPHEMERIS errors (a mis-placed Solar-System barycentre) → a DIPOLE: the
 *     induced correlation ∝ cos θ (a single sign change, +1 at 0° → −1 at 180°).
 *   • An isotropic, GR gravitational-wave background → the QUADRUPOLE (Hellings & Downs,
 *     `hellingsDowns.ts`).
 * PTA collaborations therefore fit for all three multipoles simultaneously and report the
 * quadrupole as the dominant, GW-consistent term. These functions let the plot SHOW that
 * contrast instead of merely asserting it.
 *
 * NORMALIZATION (documented honestly — these are ILLUSTRATIVE reference shapes):
 * The pure functions below are normalized to 1 at θ = 0, i.e. to the AUTOCORRELATION
 * (self-pair) limit — the same limit at which this app's Hellings–Downs self-pair value is 1
 * (`hellingsDowns(0, true) === 1`). So in their pure form:
 *       monopoleORF()  ≡ 1              (flat)
 *       dipoleORF(θ)   = cos θ          (+1 at 0°, 0 at 90°, −1 at 180°)
 *
 * The PLOT, however, draws the DISTINCT-pair Hellings–Downs curve, which starts at 1/2 at
 * θ = 0 (not 1 — the famous "one-half at zero separation"; see `hellingsDowns.ts`). To put all
 * three curves on the SAME axes, comparably anchored, the sampling helpers multiply the pure
 * ORFs by `ORF_PLOT_ANCHOR = 1/2`, so every curve shares the θ = 0 anchor of 1/2 that the
 * rendered HD curve already uses — and a full-amplitude dipole (which would reach −1 at 180°)
 * lands at −1/2, staying inside the plot's existing [−0.5, 1.0] y-range instead of clipping.
 * The vertical scale of these two reference shapes is illustrative; the load-bearing,
 * pedagogical content is their SHAPE (flat vs. cos θ vs. the HD dip-and-recover).
 */

/**
 * Monopole overlap-reduction function: a constant, independent of angular separation.
 * Physically, a MONOPOLE correlation is what a drifting reference clock (a timing-standard
 * error) would produce — the same spurious correlation for every pulsar pair, whatever their
 * angle on the sky. Normalized to 1 at θ = 0 (the autocorrelation limit).
 */
export function monopoleORF(): number {
  return 1;
}

/**
 * Dipole overlap-reduction function ∝ cos θ, with θ in radians.
 * Physically, a DIPOLE correlation is the signature of a Solar-System EPHEMERIS error (a
 * mis-located Solar-System barycentre): +1 for pulsars in the same direction (θ = 0°), 0 at
 * θ = 90°, −1 for pulsars on opposite sides of the sky (θ = 180°). Normalized to 1 at θ = 0.
 */
export function dipoleORF(thetaRad: number): number {
  return Math.cos(thetaRad);
}

/** Convenience: the dipole ORF taking degrees, for the (degree-based) UI/axes. */
export function dipoleORFDeg(thetaDeg: number): number {
  return dipoleORF((thetaDeg * Math.PI) / 180);
}

/**
 * Display anchor for overlaying the (autocorrelation-normalized) monopole/dipole reference
 * shapes on the SAME axes as the rendered DISTINCT-pair Hellings–Downs curve, which starts at
 * 1/2 at θ = 0. Multiplying the pure ORFs by this factor makes all three curves share that
 * θ = 0 anchor and keeps the dipole inside the plot's [−0.5, 1.0] y-range. See the file
 * header for the full rationale.
 */
export const ORF_PLOT_ANCHOR = 0.5;

/**
 * Sample the monopole reference shape across [0°, 180°] for plotting, scaled to the HD
 * display anchor (default 1/2) so it overlays the distinct-pair HD curve comparably.
 * @param steps number of sample points (inclusive of both ends)
 * @param anchor θ=0 anchor to scale the (=1) pure ORF to; defaults to `ORF_PLOT_ANCHOR`
 */
export function sampleMonopoleCurve(
  steps = 181,
  anchor = ORF_PLOT_ANCHOR,
): Array<{ thetaDeg: number; corr: number }> {
  const out: Array<{ thetaDeg: number; corr: number }> = [];
  for (let i = 0; i < steps; i++) {
    const thetaDeg = (180 * i) / (steps - 1);
    out.push({ thetaDeg, corr: anchor * monopoleORF() });
  }
  return out;
}

/**
 * Sample the dipole (∝ cos θ) reference shape across [0°, 180°] for plotting, scaled to the
 * HD display anchor (default 1/2) so it overlays the distinct-pair HD curve comparably.
 * @param steps number of sample points (inclusive of both ends)
 * @param anchor θ=0 anchor to scale the (=1 at θ=0) pure ORF to; defaults to `ORF_PLOT_ANCHOR`
 */
export function sampleDipoleCurve(
  steps = 181,
  anchor = ORF_PLOT_ANCHOR,
): Array<{ thetaDeg: number; corr: number }> {
  const out: Array<{ thetaDeg: number; corr: number }> = [];
  for (let i = 0; i < steps; i++) {
    const thetaDeg = (180 * i) / (steps - 1);
    out.push({ thetaDeg, corr: anchor * dipoleORFDeg(thetaDeg) });
  }
  return out;
}
