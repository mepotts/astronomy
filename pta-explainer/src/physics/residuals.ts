/**
 * Timing residuals induced by a SINGLE circular supermassive-black-hole binary (SMBHB).
 *
 * This is the load-bearing physics of M2 (the draggable-source sandbox). Like
 * `hellingsDowns.ts`, it must stay exact — see `residuals.test.ts` for the asserted
 * landmarks, and BUILD-PLAN.md §6 for the physics-validation philosophy.
 *
 * SCOPE / HONESTY (BUILD-PLAN §6, dossier "physics-correctness risk"):
 *   • ONE monochromatic, non-evolving, circular binary — NOT the stochastic GW background.
 *     We never present this as "the GWB"; it is an illustrative single source.
 *   • Leading-order (quadrupole) waveform only. No orbital evolution / chirp across the
 *     PTA band (the source is treated as fixed-frequency over the ~15-yr span — valid for
 *     the nanohertz sources this explains).
 *
 * The model, in three exact pieces:
 *
 *   1. STRAIN AMPLITUDE.  For a circular binary radiating by GW emission,
 *          h0 = 2 (G·ℳ)^(5/3) (π f_gw)^(2/3) / (c^4 · d_L)
 *      with chirp mass ℳ, GW frequency f_gw (= twice the orbital frequency), luminosity
 *      distance d_L. Numerically h0 = 2.76e-14 · (ℳ/1e9 M☉)^(5/3) · (10 Mpc/d_L) ·
 *      (f/1e-8 Hz)^(2/3) — the published normalization we validate against.
 *
 *   2. ANTENNA PATTERN.  A GW from sky direction ŝ (propagation Ω̂ = −ŝ) couples to a
 *      pulsar in direction p̂ through the geometric factors
 *          F+ = ½[(m̂·p̂)² − (n̂·p̂)²]/(1 + Ω̂·p̂),   F× = (m̂·p̂)(n̂·p̂)/(1 + Ω̂·p̂)
 *      where (m̂, n̂) is the GW polarization basis ⊥ Ω̂ (rotated by the polarization angle
 *      ψ). This is the standard PTA response (Ellis, Siemens & Creighton 2012). Its
 *      sky+polarization average over sources reproduces the Hellings–Downs curve — the
 *      cross-check that ties this module back to `hellingsDowns.ts` (see the test suite).
 *
 *   3. RESIDUAL = ∫ redshift dt.  The induced redshift is
 *          z(t) = F+ h+(t) + F× h×(t),
 *      with h+(t) = h0 (1+cos²ι)/2 cos Φ(t), h×(t) = h0 cos ι sin Φ(t), Φ(t) = 2π f t + φ0,
 *      inclination ι. The timing residual is its time integral, so each sinusoid picks up
 *      a 1/(2π f) factor (lower-frequency sources ⇒ larger residuals at fixed strain):
 *          R_Earth(t) = (h0 / 2π f) · [ F+ (1+cos²ι)/2 · sin Φ(t)  −  F× cos ι · cos Φ(t) ].
 *      The full residual subtracts the "pulsar term" — the same waveform evaluated at the
 *      retarded time, i.e. phase-shifted by 2π f (L/c)(1 − cos μ) for pulsar distance L and
 *      pulsar–source angle μ. The Earth term is COMMON to all pulsars (this is what
 *      correlates them, à la Hellings–Downs); the pulsar term carries a per-pulsar phase
 *      and decorrelates. We default to the Earth term; the pulsar term is opt-in and needs
 *      a distance the NANOGrav position table does not carry (so it is never faked here).
 *
 * Symbols & units: angles in radians unless a name says Deg; ℳ in solar masses; d_L in Mpc;
 * f in Hz; time in seconds (helpers convert years↔seconds); residuals in seconds (helpers
 * convert to nanoseconds for the UI). h0 is dimensionless strain.
 */

// ---------------------------------------------------------------------------
// Physical constants (SI), CODATA / IAU
// ---------------------------------------------------------------------------
const G = 6.6743e-11; // m^3 kg^-1 s^-2
const C_LIGHT = 2.99792458e8; // m s^-1
const M_SUN = 1.98892e30; // kg
const MPC = 3.0856775814913673e22; // m
const KPC = 3.0856775814913673e19; // m
/** Julian year in seconds (365.25 d). */
export const SECONDS_PER_YEAR = 365.25 * 86400;
const DEG2RAD = Math.PI / 180;

// ---------------------------------------------------------------------------
// Minimal 3-vector helpers (equatorial Cartesian)
// ---------------------------------------------------------------------------
export type Vec3 = readonly [number, number, number];

const dot = (a: Vec3, b: Vec3): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const scale = (a: Vec3, s: number): Vec3 => [a[0] * s, a[1] * s, a[2] * s];
const add = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

/**
 * Unit vector for a sky position (RA, Dec in degrees) in equatorial Cartesian coords:
 * x̂ toward (α=0, δ=0), ẑ toward the north celestial pole.
 */
export function directionToUnitVector(raDeg: number, decDeg: number): Vec3 {
  const a = raDeg * DEG2RAD;
  const d = decDeg * DEG2RAD;
  const cd = Math.cos(d);
  return [cd * Math.cos(a), cd * Math.sin(a), Math.sin(d)];
}

/** A sky direction, matching the {raDeg, decDeg} shape used across the app. */
export interface SkyDirection {
  raDeg: number;
  decDeg: number;
}

// ---------------------------------------------------------------------------
// 1. Strain amplitude
// ---------------------------------------------------------------------------

/**
 * Dimensionless GW strain amplitude h0 of a circular binary:
 *   h0 = 2 (G ℳ)^(5/3) (π f)^(2/3) / (c^4 d_L).
 * Validated against the published normalization 2.76e-14 at ℳ=1e9 M☉, d_L=10 Mpc,
 * f=1e-8 Hz (see residuals.test.ts).
 *
 * @param chirpMassSolar chirp mass ℳ in solar masses
 * @param distanceMpc    luminosity distance d_L in megaparsecs
 * @param freqHz         GW frequency f_gw in hertz
 */
export function strainAmplitude(
  chirpMassSolar: number,
  distanceMpc: number,
  freqHz: number,
): number {
  const m = chirpMassSolar * M_SUN;
  const dL = distanceMpc * MPC;
  return (
    (2 * Math.pow(G * m, 5 / 3) * Math.pow(Math.PI * freqHz, 2 / 3)) /
    (Math.pow(C_LIGHT, 4) * dL)
  );
}

// ---------------------------------------------------------------------------
// 2. Antenna pattern
// ---------------------------------------------------------------------------

/** GW geometry at the Solar System: propagation direction + polarization basis. */
export interface GWBasis {
  /** Propagation direction Ω̂ = −ŝ (from source toward the observer). */
  omega: Vec3;
  /** Polarization basis vector m̂ (⊥ Ω̂), rotated by the polarization angle ψ. */
  mHat: Vec3;
  /** Polarization basis vector n̂ (⊥ Ω̂, ⊥ m̂), rotated by ψ. */
  nHat: Vec3;
}

/**
 * Build the GW propagation + polarization basis for a source at sky position `source`,
 * with polarization angle ψ. Uses the standard convention (Ellis et al. 2012): with
 * colatitude θ = 90°−Dec and azimuth φ = RA,
 *   Ω̂ = −ŝ,  m̂0 = (sinφ, −cosφ, 0),  n̂0 = (−cosθ cosφ, −cosθ sinφ, sinθ),
 * then (m̂, n̂) are (m̂0, n̂0) rotated by ψ within the plane ⊥ Ω̂.
 */
export function gwBasis(source: SkyDirection, psiRad = 0): GWBasis {
  const a = source.raDeg * DEG2RAD; // φ
  const d = source.decDeg * DEG2RAD;
  const sinTheta = Math.cos(d); // sin(90°−Dec) = cos Dec
  const cosTheta = Math.sin(d); // cos(90°−Dec) = sin Dec
  const cosPhi = Math.cos(a);
  const sinPhi = Math.sin(a);

  const sHat: Vec3 = [sinTheta * cosPhi, sinTheta * sinPhi, cosTheta];
  const omega: Vec3 = scale(sHat, -1);
  const m0: Vec3 = [sinPhi, -cosPhi, 0];
  const n0: Vec3 = [-cosTheta * cosPhi, -cosTheta * sinPhi, sinTheta];

  // Rotate the polarization basis by ψ in the (m0, n0) plane.
  const cp = Math.cos(psiRad);
  const sp = Math.sin(psiRad);
  const mHat = add(scale(m0, cp), scale(n0, sp));
  const nHat = add(scale(m0, -sp), scale(n0, cp));
  return { omega, mHat, nHat };
}

/** Geometric coupling of each GW polarization to a pulsar. */
export interface AntennaPattern {
  fPlus: number;
  fCross: number;
}

/**
 * Antenna-pattern functions F+, F× for a pulsar in direction `pulsar`, given the GW
 * `basis`. Returns {0,0} at the coordinate singularity where the pulsar lies exactly
 * along the GW propagation direction (pulsar behind the source), 1 + Ω̂·p̂ → 0.
 */
export function antennaPattern(basis: GWBasis, pulsar: SkyDirection): AntennaPattern {
  const p = directionToUnitVector(pulsar.raDeg, pulsar.decDeg);
  const denom = 1 + dot(basis.omega, p);
  if (Math.abs(denom) < 1e-12) return { fPlus: 0, fCross: 0 };
  const mp = dot(basis.mHat, p);
  const np = dot(basis.nHat, p);
  return {
    fPlus: (0.5 * (mp * mp - np * np)) / denom,
    fCross: (mp * np) / denom,
  };
}

// ---------------------------------------------------------------------------
// 3. Residual waveform
// ---------------------------------------------------------------------------

/** Parameters of the single SMBHB source. */
export interface SourceParams {
  /** Chirp mass ℳ in solar masses. */
  chirpMassSolar: number;
  /** Luminosity distance d_L in megaparsecs. */
  distanceMpc: number;
  /** GW frequency f_gw in hertz (= twice the orbital frequency). */
  freqHz: number;
  /** Source sky position. */
  source: SkyDirection;
  /** Inclination ι in radians (0 = face-on, π/2 = edge-on). */
  inclinationRad: number;
  /** Polarization angle ψ in radians. */
  psiRad: number;
  /** Initial GW phase φ0 in radians. */
  phase0Rad: number;
}

/**
 * Residual amplitude scale h0/(2π f) in seconds — the size of the induced timing
 * residual before the (order-unity) antenna-pattern × inclination projection. This is
 * the quantity that grows as 1/f: the same strain makes a bigger *timing* residual at a
 * lower frequency.
 */
export function residualAmplitudeSec(params: SourceParams): number {
  const h0 = strainAmplitude(params.chirpMassSolar, params.distanceMpc, params.freqHz);
  return h0 / (2 * Math.PI * params.freqHz);
}

/**
 * Earth-term timing residual (seconds) for one pulsar at time t (seconds):
 *   R_Earth(t) = (h0/2πf) [ F+ (1+cos²ι)/2 sin Φ − F× cos ι cos Φ ],  Φ = 2π f t + φ0.
 * This term is identical (same phase) for every pulsar up to its antenna pattern — the
 * origin of the inter-pulsar correlation.
 */
export function earthTermResidualSec(
  params: SourceParams,
  pulsar: SkyDirection,
  tSec: number,
): number {
  const basis = gwBasis(params.source, params.psiRad);
  const { fPlus, fCross } = antennaPattern(basis, pulsar);
  const amp = residualAmplitudeSec(params);
  const phi = 2 * Math.PI * params.freqHz * tSec + params.phase0Rad;
  const ci = Math.cos(params.inclinationRad);
  const aPlus = (1 + ci * ci) / 2;
  return amp * (fPlus * aPlus * Math.sin(phi) - fCross * ci * Math.cos(phi));
}

/**
 * Extra phase of the pulsar term relative to the Earth term, 2π f (L/c)(1 − cos μ),
 * where μ is the pulsar–source angle and L the pulsar distance. For nanohertz sources
 * and kiloparsec distances this is many radians, so different pulsars carry effectively
 * independent pulsar-term phases — which is why the pulsar terms do not correlate.
 */
export function pulsarTermPhase(
  params: SourceParams,
  pulsar: SkyDirection,
  pulsarDistanceKpc: number,
): number {
  const sHat = directionToUnitVector(params.source.raDeg, params.source.decDeg);
  const p = directionToUnitVector(pulsar.raDeg, pulsar.decDeg);
  const cosMu = dot(sHat, p);
  const L = pulsarDistanceKpc * KPC;
  return 2 * Math.PI * params.freqHz * (L / C_LIGHT) * (1 - cosMu);
}

/**
 * Full residual (seconds) = Earth term − pulsar term. The pulsar term is the same
 * waveform retarded by the light-travel phase (`pulsarTermPhase`); for a non-evolving
 * source that is just a constant phase offset at the same frequency.
 *
 * @param pulsarDistanceKpc when omitted (or non-finite), only the Earth term is returned.
 */
export function residualSec(
  params: SourceParams,
  pulsar: SkyDirection,
  tSec: number,
  pulsarDistanceKpc?: number,
): number {
  const earth = earthTermResidualSec(params, pulsar, tSec);
  if (pulsarDistanceKpc == null || !Number.isFinite(pulsarDistanceKpc)) return earth;
  const dPhi = pulsarTermPhase(params, pulsar, pulsarDistanceKpc);
  // Pulsar term: identical waveform with φ0 → φ0 − dPhi.
  const shifted: SourceParams = { ...params, phase0Rad: params.phase0Rad - dPhi };
  const pulsarTerm = earthTermResidualSec(shifted, pulsar, tSec);
  return earth - pulsarTerm;
}

// ---------------------------------------------------------------------------
// Series sampling (for plotting)
// ---------------------------------------------------------------------------

/** One sample of a residual time series, in display units. */
export interface ResidualSample {
  /** Time since the start of the span, in years. */
  tYears: number;
  /** Induced timing residual, in nanoseconds. */
  residualNs: number;
}

export interface ResidualSeriesOptions {
  /** Length of the observing span in years (default 15, the NANOGrav 15-yr span). */
  spanYears?: number;
  /** Number of samples across the span (default 240). */
  samples?: number;
  /** Include the pulsar term using this distance (kpc). Omit for Earth-term only. */
  pulsarDistanceKpc?: number;
}

/**
 * Sample a pulsar's induced residual across an observing span, in (years, nanoseconds) —
 * ready for plotting. Earth-term only unless `pulsarDistanceKpc` is given.
 */
export function sampleResidualSeries(
  params: SourceParams,
  pulsar: SkyDirection,
  options: ResidualSeriesOptions = {},
): ResidualSample[] {
  return sampleResidualSeriesMulti([params], pulsar, options);
}

// ---------------------------------------------------------------------------
// Superposition — several independent binaries
// ---------------------------------------------------------------------------
// General relativity is linear in the weak field, so the residual from several
// independent sources is simply the SUM of their individual residuals. This is the
// honest conceptual bridge from "one source" toward "the real background is many sources"
// — without ever running a stochastic Monte-Carlo (which the dossier warns against for a
// lay audience).

/** Total residual (seconds) at one time from a SET of sources (their residuals summed). */
export function residualMultiSec(
  sources: SourceParams[],
  pulsar: SkyDirection,
  tSec: number,
  pulsarDistanceKpc?: number,
): number {
  let sum = 0;
  for (const s of sources) sum += residualSec(s, pulsar, tSec, pulsarDistanceKpc);
  return sum;
}

/**
 * Sample the SUMMED residual of several sources across the span, in (years, nanoseconds).
 * With a single source this is identical to `sampleResidualSeries`.
 */
export function sampleResidualSeriesMulti(
  sources: SourceParams[],
  pulsar: SkyDirection,
  options: ResidualSeriesOptions = {},
): ResidualSample[] {
  const spanYears = options.spanYears ?? 15;
  const samples = Math.max(2, options.samples ?? 240);
  const out: ResidualSample[] = [];
  for (let i = 0; i < samples; i++) {
    const tYears = (spanYears * i) / (samples - 1);
    const tSec = tYears * SECONDS_PER_YEAR;
    const r = residualMultiSec(sources, pulsar, tSec, options.pulsarDistanceKpc);
    out.push({ tYears, residualNs: r * 1e9 });
  }
  return out;
}
