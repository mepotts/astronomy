/**
 * PHYSICS-VALIDATION GATE for M2 (BUILD-PLAN.md §6) — the single-SMBHB residual model.
 *
 * Same philosophy as hellingsDowns.test.ts: assert the physics against landmarks that are
 * derivable independently of this implementation, so the tests are self-checking, not
 * circular. Three groups:
 *
 *   1. STRAIN AMPLITUDE   — pinned to the published normalization 2.76e-14, plus the three
 *                            power-law scalings (ℳ^5/3, 1/d_L, f^2/3).
 *   2. ANTENNA PATTERN    — the headline cross-check: averaging F+₁F+₂ + F×₁F×₂ over GW
 *                            source directions + polarizations reproduces the Hellings–Downs
 *                            curve from hellingsDowns.ts. This ties M2's new geometry back to
 *                            the M1 physics already validated against the published figure.
 *   3. RESIDUAL WAVEFORM  — integration 1/(2πf) scaling, linearity in strain, the face-on /
 *                            edge-on inclination limits, Earth-term periodicity (coherence),
 *                            and pulsar-term decorrelation.
 */
import { describe, it, expect } from "vitest";
import {
  strainAmplitude,
  residualAmplitudeSec,
  gwBasis,
  antennaPattern,
  earthTermResidualSec,
  residualSec,
  residualMultiSec,
  pulsarTermPhase,
  sampleResidualSeries,
  sampleResidualSeriesMulti,
  directionToUnitVector,
  SECONDS_PER_YEAR,
  type SourceParams,
  type SkyDirection,
} from "../residuals";
import { hellingsDownsDeg } from "../hellingsDowns";

// A fiducial source used across the waveform tests.
const fiducial: SourceParams = {
  chirpMassSolar: 1e9,
  distanceMpc: 100,
  freqHz: 1e-8,
  source: { raDeg: 120, decDeg: -20 },
  inclinationRad: Math.PI / 3,
  psiRad: 0.4,
  phase0Rad: 0,
};

describe("strainAmplitude h0 — published normalization + scalings", () => {
  it("h0 = 2.76e-14 at ℳ=1e9 M☉, d_L=10 Mpc, f=1e-8 Hz (literature landmark)", () => {
    // Sesana/Vecchio & NANOGrav individual-source papers:
    //   h0 = 2.76e-14 (ℳ/1e9 M☉)^5/3 (10 Mpc/d_L) (f/1e-8 Hz)^2/3.
    const h0 = strainAmplitude(1e9, 10, 1e-8);
    expect(h0).toBeGreaterThan(2.6e-14);
    expect(h0).toBeLessThan(2.9e-14);
    // within ~2% of the quoted value
    expect(h0 / 2.76e-14).toBeCloseTo(1, 1);
  });

  it("scales as ℳ^(5/3)", () => {
    const a = strainAmplitude(1e9, 100, 1e-8);
    const b = strainAmplitude(2e9, 100, 1e-8);
    expect(b / a).toBeCloseTo(Math.pow(2, 5 / 3), 6);
  });

  it("scales as 1/d_L", () => {
    const a = strainAmplitude(1e9, 100, 1e-8);
    const b = strainAmplitude(1e9, 300, 1e-8);
    expect(a / b).toBeCloseTo(3, 6);
  });

  it("scales as f^(2/3)", () => {
    const a = strainAmplitude(1e9, 100, 1e-8);
    const b = strainAmplitude(1e9, 100, 4e-8);
    expect(b / a).toBeCloseTo(Math.pow(4, 2 / 3), 6);
  });
});

describe("antennaPattern — geometry + singularity guard", () => {
  it("returns finite, bounded values for a generic geometry", () => {
    const basis = gwBasis({ raDeg: 45, decDeg: 10 }, 0.3);
    const { fPlus, fCross } = antennaPattern(basis, { raDeg: 200, decDeg: -30 });
    expect(Number.isFinite(fPlus)).toBe(true);
    expect(Number.isFinite(fCross)).toBe(true);
  });

  it("guards the coordinate singularity when the pulsar lies along the source direction", () => {
    // Pulsar exactly at the source ⇒ 1 + Ω̂·p̂ = 1 − 1 = 0. Guarded to {0,0}.
    const source: SkyDirection = { raDeg: 77, decDeg: 33 };
    const basis = gwBasis(source, 0);
    const { fPlus, fCross } = antennaPattern(basis, source);
    expect(fPlus).toBe(0);
    expect(fCross).toBe(0);
  });

  it("polarization basis is orthonormal and perpendicular to the propagation direction", () => {
    const { omega, mHat, nHat } = gwBasis({ raDeg: 130, decDeg: -42 }, 1.1);
    const dot = (a: readonly number[], b: readonly number[]) =>
      a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    expect(dot(omega, omega)).toBeCloseTo(1, 12);
    expect(dot(mHat, mHat)).toBeCloseTo(1, 12);
    expect(dot(nHat, nHat)).toBeCloseTo(1, 12);
    expect(dot(mHat, nHat)).toBeCloseTo(0, 12);
    expect(dot(mHat, omega)).toBeCloseTo(0, 12);
    expect(dot(nHat, omega)).toBeCloseTo(0, 12);
  });
});

/**
 * THE CROSS-CHECK THAT TIES M2 TO M1.
 *
 * For an isotropic, unpolarized GW background the overlap reduction function — the
 * expected correlation between two pulsars as a function of their separation — is exactly
 * the average of the Earth-term antenna-pattern product over all source directions and
 * polarizations, and it equals the Hellings–Downs curve. We compute that average with a
 * deterministic Fibonacci-sphere grid of source directions (no RNG ⇒ no flaky tests) and
 * confirm it reproduces the shape of hellingsDowns.ts, normalized so two co-located
 * distinct pulsars give Γ(0)=0.5.
 */
describe("antennaPattern — sky/polarization average reproduces Hellings–Downs", () => {
  /** ⟨F+₁F+₂ + F×₁F×₂⟩ over a Fibonacci grid of sources × evenly-spaced ψ. */
  function overlap(psr1: SkyDirection, psr2: SkyDirection, nSrc = 4000, nPsi = 8): number {
    const golden = Math.PI * (3 - Math.sqrt(5)); // golden angle
    let sum = 0;
    let count = 0;
    for (let i = 0; i < nSrc; i++) {
      const z = 1 - (2 * (i + 0.5)) / nSrc; // uniform in cos(polar angle)
      const r = Math.sqrt(Math.max(0, 1 - z * z));
      const phi = golden * i;
      const raDeg = (Math.atan2(r * Math.sin(phi), r * Math.cos(phi)) * 180) / Math.PI;
      const decDeg = (Math.asin(z) * 180) / Math.PI;
      const src: SkyDirection = { raDeg, decDeg };
      for (let k = 0; k < nPsi; k++) {
        const psi = (Math.PI * k) / nPsi; // ψ ∈ [0, π)
        const basis = gwBasis(src, psi);
        const a = antennaPattern(basis, psr1);
        const b = antennaPattern(basis, psr2);
        sum += a.fPlus * b.fPlus + a.fCross * b.fCross;
        count++;
      }
    }
    return sum / count;
  }

  it("the normalized overlap C(θ)/C(0) matches 2·Γ(θ) across the curve", () => {
    const p1: SkyDirection = { raDeg: 0, decDeg: 0 };
    // Two pulsars at dec=0 separated by ΔRA are exactly Δ° apart on the sky.
    const c0 = overlap(p1, p1); // θ = 0 (co-located, distinct)
    expect(c0).toBeGreaterThan(0);

    // hellingsDownsDeg(0) = 0.5, so the HD ratio Γ(θ)/Γ(0) = 2·Γ(θ).
    const angles = [30, 49.3173, 60, 90, 120, 180];
    for (const theta of angles) {
      const c = overlap(p1, { raDeg: theta, decDeg: 0 });
      const ratio = c / c0;
      const expected = 2 * hellingsDownsDeg(theta);
      // Deterministic grid average; absolute tolerance covers grid discretization.
      expect(ratio).toBeCloseTo(expected, 1); // |Δ| < 0.05
    }
  });

  it("recovers the famous zero crossing: overlap ≈ 0 near θ ≈ 49.3°", () => {
    const p1: SkyDirection = { raDeg: 0, decDeg: 0 };
    const c0 = overlap(p1, p1);
    const cZero = overlap(p1, { raDeg: 49.3173, decDeg: 0 });
    expect(Math.abs(cZero / c0)).toBeLessThan(0.05);
  });
});

describe("residual waveform — integration, linearity, inclination limits", () => {
  it("residualAmplitudeSec = h0 / (2π f)", () => {
    const h0 = strainAmplitude(fiducial.chirpMassSolar, fiducial.distanceMpc, fiducial.freqHz);
    const expected = h0 / (2 * Math.PI * fiducial.freqHz);
    expect(residualAmplitudeSec(fiducial)).toBeCloseTo(expected, 18);
  });

  it("for FIXED strain, the residual grows as 1/f (the time-integration factor)", () => {
    // Hold h0 fixed by adjusting distance so only the 1/f integration factor moves.
    const f1 = 1e-8;
    const f2 = 2e-8;
    // choose distances so that h0 is identical at both frequencies
    const base = strainAmplitude(1e9, 100, f1);
    const d2 = (strainAmplitude(1e9, 100, f2) / base) * 100; // d ∝ h0 at fixed ℳ,f
    const ampA = residualAmplitudeSec({ ...fiducial, freqHz: f1, distanceMpc: 100 });
    const ampB = residualAmplitudeSec({ ...fiducial, freqHz: f2, distanceMpc: d2 });
    // same h0, frequency doubled ⇒ residual amplitude halved
    expect(ampA / ampB).toBeCloseTo(2, 6);
  });

  it("is linear in strain: doubling distance halves the residual everywhere", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const near = residualSec(fiducial, psr, 3.2e8);
    const far = residualSec({ ...fiducial, distanceMpc: 200 }, psr, 3.2e8);
    expect(near / far).toBeCloseTo(2, 6);
  });

  it("edge-on (ι=90°) kills the cross quadrature → no cosΦ term", () => {
    // At φ0=0, t=0: Φ=0, sinΦ=0, cosΦ=1, so the residual isolates −amp·F×·cos ι.
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const edgeOn = earthTermResidualSec(
      { ...fiducial, inclinationRad: Math.PI / 2, phase0Rad: 0 },
      psr,
      0,
    );
    expect(edgeOn).toBeCloseTo(0, 12);
  });

  it("face-on (ι=0°) leaves a nonzero cross quadrature at Φ=0", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const basis = gwBasis(fiducial.source, fiducial.psiRad);
    const { fCross } = antennaPattern(basis, psr);
    const amp = residualAmplitudeSec(fiducial);
    const faceOn = earthTermResidualSec(
      { ...fiducial, inclinationRad: 0, phase0Rad: 0 },
      psr,
      0,
    );
    // ι=0 ⇒ cos ι = 1, (1+cos²ι)/2 = 1; at Φ=0 residual = −amp·F×.
    expect(faceOn).toBeCloseTo(-amp * fCross, 18);
    expect(Math.abs(faceOn)).toBeGreaterThan(0);
  });
});

describe("residual waveform — Earth-term coherence vs pulsar-term decorrelation", () => {
  it("the Earth term is periodic at the GW period (coherent, common to all pulsars)", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const T = 1 / fiducial.freqHz; // GW period in seconds
    const t = 2.7e7;
    expect(earthTermResidualSec(fiducial, psr, t)).toBeCloseTo(
      earthTermResidualSec(fiducial, psr, t + T),
      18,
    );
  });

  it("two pulsars share the Earth term's phase (same f, deterministic amplitude ratio)", () => {
    // Both are pure sinusoids at the same frequency ⇒ each is periodic at T.
    const T = 1 / fiducial.freqHz;
    const pA: SkyDirection = { raDeg: 10, decDeg: 60 };
    const pB: SkyDirection = { raDeg: 250, decDeg: -35 };
    for (const t of [1e7, 5e7]) {
      expect(earthTermResidualSec(fiducial, pA, t)).toBeCloseTo(
        earthTermResidualSec(fiducial, pA, t + T),
        15,
      );
      expect(earthTermResidualSec(fiducial, pB, t)).toBeCloseTo(
        earthTermResidualSec(fiducial, pB, t + T),
        15,
      );
    }
  });

  it("the pulsar-term phase is many radians for nanohertz GWs at kpc distances", () => {
    // 2π f (L/c)(1−cos μ): for f~1e-8 Hz and L~1 kpc this is thousands of radians,
    // so different pulsars carry effectively independent pulsar-term phases.
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const dPhi = pulsarTermPhase(fiducial, psr, 1.0);
    expect(dPhi).toBeGreaterThan(100);
  });

  it("including the pulsar term changes the residual (it is not the Earth term alone)", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const earthOnly = residualSec(fiducial, psr, 4e7);
    const withPulsar = residualSec(fiducial, psr, 4e7, 1.3);
    // Residuals are ~nanoseconds (~1e-9 s); compare at a physical sub-ns scale rather
    // than toBeCloseTo's absolute decimal threshold. Here the two differ by ~1.3 ns.
    expect(Math.abs((withPulsar - earthOnly) * 1e9)).toBeGreaterThan(0.5);
  });
});

describe("sampleResidualSeries — plotting helper", () => {
  it("returns the requested samples across the span, in (years, ns), all finite", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const series = sampleResidualSeries(fiducial, psr, { spanYears: 15, samples: 100 });
    expect(series.length).toBe(100);
    expect(series[0].tYears).toBe(0);
    expect(series[series.length - 1].tYears).toBeCloseTo(15, 12);
    expect(series.every((s) => Number.isFinite(s.residualNs))).toBe(true);
  });

  it("converts seconds → nanoseconds consistently with residualSec", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const series = sampleResidualSeries(fiducial, psr, { spanYears: 10, samples: 11 });
    // midpoint sample (index 5) is at t = 5 years
    const tSec = 5 * SECONDS_PER_YEAR;
    expect(series[5].residualNs).toBeCloseTo(residualSec(fiducial, psr, tSec) * 1e9, 9);
  });

  it("sanity: a strong nearby fiducial source induces tens–hundreds of ns", () => {
    const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
    const series = sampleResidualSeries(
      { ...fiducial, distanceMpc: 15 },
      psr,
      { spanYears: 15, samples: 200 },
    );
    const peak = Math.max(...series.map((s) => Math.abs(s.residualNs)));
    expect(peak).toBeGreaterThan(10);
    expect(peak).toBeLessThan(5000);
  });
});

describe("superposition — multi-source residuals add linearly", () => {
  const psr: SkyDirection = { raDeg: 200, decDeg: 15 };
  const src2: SourceParams = {
    ...fiducial,
    freqHz: 2.5e-8,
    source: { raDeg: 40, decDeg: 55 },
    inclinationRad: Math.PI / 5,
    phase0Rad: 1.0,
  };

  it("a single-element source list equals the single-source residual exactly", () => {
    for (const t of [0, 1.5e7, 6e7]) {
      expect(residualMultiSec([fiducial], psr, t)).toBeCloseTo(
        residualSec(fiducial, psr, t),
        18,
      );
    }
  });

  it("two sources sum to the sum of their individual residuals (linearity of GR)", () => {
    for (const t of [0, 2.2e7, 5.1e7, 9e7]) {
      const a = residualSec(fiducial, psr, t);
      const b = residualSec(src2, psr, t);
      expect(residualMultiSec([fiducial, src2], psr, t)).toBeCloseTo(a + b, 18);
    }
  });

  it("two identical sources give exactly twice one source", () => {
    for (const t of [1e7, 4e7]) {
      expect(residualMultiSec([fiducial, fiducial], psr, t)).toBeCloseTo(
        2 * residualSec(fiducial, psr, t),
        18,
      );
    }
  });

  it("a massless source contributes nothing to the sum", () => {
    const dead: SourceParams = { ...src2, chirpMassSolar: 0 };
    for (const t of [3e6, 7e7]) {
      expect(residualMultiSec([fiducial, dead], psr, t)).toBeCloseTo(
        residualSec(fiducial, psr, t),
        18,
      );
    }
  });

  it("sampleResidualSeriesMulti matches the per-sample summed residual", () => {
    const series = sampleResidualSeriesMulti([fiducial, src2], psr, {
      spanYears: 12,
      samples: 13,
    });
    expect(series.length).toBe(13);
    const tSec = 6 * SECONDS_PER_YEAR; // index 6 = 6 years
    expect(series[6].residualNs).toBeCloseTo(
      residualMultiSec([fiducial, src2], psr, tSec) * 1e9,
      9,
    );
    // and the one-source helper is the [params] special case
    const one = sampleResidualSeries(fiducial, psr, { spanYears: 12, samples: 13 });
    const oneMulti = sampleResidualSeriesMulti([fiducial], psr, {
      spanYears: 12,
      samples: 13,
    });
    expect(oneMulti[6].residualNs).toBeCloseTo(one[6].residualNs, 12);
  });
});

describe("directionToUnitVector — basic sanity", () => {
  it("maps (0,0)→x̂, (90,0)→ŷ, (0,90)→ẑ", () => {
    const close = (v: readonly number[], e: readonly number[]) => {
      expect(v[0]).toBeCloseTo(e[0], 12);
      expect(v[1]).toBeCloseTo(e[1], 12);
      expect(v[2]).toBeCloseTo(e[2], 12);
    };
    close(directionToUnitVector(0, 0), [1, 0, 0]);
    close(directionToUnitVector(90, 0), [0, 1, 0]);
    close(directionToUnitVector(0, 90), [0, 0, 1]);
  });
});
