/**
 * The Hellings & Downs (1983) analytic correlation curve.
 * This is the load-bearing physics of the whole project — keep it exact.
 *
 * For an isotropic, unpolarized, general-relativistic stochastic GW background, the
 * expected cross-correlation of timing residuals for two pulsars separated by angle θ:
 *
 *   Γ(θ) = (1/2)·δ_ab + 1/2 − x/4 + (3/2)·x·ln(x),   x = (1 − cos θ)/2
 *
 * where δ_ab = 1 for the self-pair (a == b), else 0.
 *
 * Normalized convention as used in the NANOGrav 2023 figure: for DISTINCT pulsars the
 * curve starts at 0.5 (NOT 1.0), crosses zero near 49.3°, dips to ≈ −0.173 near 82.5°,
 * and returns to 0.25 at 180°. See DATA-SOURCES.md §1 for references and validation
 * landmarks; see hellingsDowns.test.ts (M1) for the asserted checkpoints.
 */

/** x = (1 − cos θ)/2, with θ in radians. */
export function hdX(thetaRad: number): number {
  return (1 - Math.cos(thetaRad)) / 2;
}

/**
 * Hellings–Downs expected correlation.
 * @param thetaRad angular separation in radians (0 .. π)
 * @param samePulsar set true only for the self-pair (adds the +1/2 δ term)
 */
export function hellingsDowns(thetaRad: number, samePulsar = false): number {
  const x = hdX(thetaRad);
  // x·ln(x) → 0 as x → 0, but JS gives 0 * -Infinity = NaN. Guard it.
  const xLogX = x === 0 ? 0 : x * Math.log(x);
  const self = samePulsar ? 0.5 : 0;
  return self + 0.5 - x / 4 + 1.5 * xLogX;
}

/** Convenience: same curve but taking degrees, for the (degree-based) UI/axes. */
export function hellingsDownsDeg(thetaDeg: number, samePulsar = false): number {
  return hellingsDowns((thetaDeg * Math.PI) / 180, samePulsar);
}

/**
 * Sample the distinct-pulsar curve across [0°, 180°] for plotting.
 * @param steps number of sample points (inclusive of both ends)
 */
export function sampleHDCurve(steps = 181): Array<{ thetaDeg: number; corr: number }> {
  const out: Array<{ thetaDeg: number; corr: number }> = [];
  for (let i = 0; i < steps; i++) {
    const thetaDeg = (180 * i) / (steps - 1);
    out.push({ thetaDeg, corr: hellingsDownsDeg(thetaDeg, false) });
  }
  return out;
}
