/**
 * Angular separation between two points on the celestial sphere.
 *
 * Uses the spherical law of cosines:
 *
 *   cos θ = sin δ1 · sin δ2 + cos δ1 · cos δ2 · cos(α1 − α2)
 *
 * where (α, δ) are right ascension and declination. This is exactly the quantity
 * that feeds the Hellings–Downs curve: θ is the on-sky angle between a pulsar pair.
 *
 * The law of cosines is numerically poor for *very* small separations (the haversine
 * formula is preferred there), but for a pulsar-pair sky-map demo — where the smallest
 * inter-pulsar angles are degrees, not arcseconds — it is more than accurate enough,
 * and it is the form named in DATA-SOURCES.md §2. We do guard the one real failure
 * mode: floating-point round-off can push the dot product just past ±1, which would
 * make Math.acos return NaN. We clamp to [-1, 1] before taking the arccosine.
 *
 * See angularSeparation.test.ts for the asserted checkpoints.
 */

const DEG2RAD = Math.PI / 180;
const RAD2DEG = 180 / Math.PI;

/** Clamp a value into the closed interval [lo, hi]. */
function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

/**
 * Angular separation in **radians** between two sky positions given in **radians**.
 * @param ra1 right ascension of point 1 (radians)
 * @param dec1 declination of point 1 (radians)
 * @param ra2 right ascension of point 2 (radians)
 * @param dec2 declination of point 2 (radians)
 */
export function angularSeparationRad(
  ra1: number,
  dec1: number,
  ra2: number,
  dec2: number,
): number {
  const cosTheta =
    Math.sin(dec1) * Math.sin(dec2) +
    Math.cos(dec1) * Math.cos(dec2) * Math.cos(ra1 - ra2);
  // Round-off can nudge cosTheta to e.g. 1.0000000002 → acos → NaN. Clamp first.
  return Math.acos(clamp(cosTheta, -1, 1));
}

/**
 * Angular separation in **degrees** between two sky positions given in **degrees**.
 * This is the form the UI uses: pulsar RA/Dec are stored in decimal degrees, and the
 * H–D curve x-axis is in degrees.
 * @param raDeg1 right ascension of point 1 (degrees)
 * @param decDeg1 declination of point 1 (degrees)
 * @param raDeg2 right ascension of point 2 (degrees)
 * @param decDeg2 declination of point 2 (degrees)
 */
export function angularSeparationDeg(
  raDeg1: number,
  decDeg1: number,
  raDeg2: number,
  decDeg2: number,
): number {
  return (
    angularSeparationRad(
      raDeg1 * DEG2RAD,
      decDeg1 * DEG2RAD,
      raDeg2 * DEG2RAD,
      decDeg2 * DEG2RAD,
    ) * RAD2DEG
  );
}

/** A minimal sky position, matching the shape of the pulsar JSON entries. */
export interface SkyPosition {
  raDeg: number;
  decDeg: number;
}

/** Convenience overload taking two {raDeg, decDeg} objects, returning degrees. */
export function angularSeparationBetween(a: SkyPosition, b: SkyPosition): number {
  return angularSeparationDeg(a.raDeg, a.decDeg, b.raDeg, b.decDeg);
}
