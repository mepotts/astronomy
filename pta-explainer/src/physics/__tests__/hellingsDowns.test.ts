/**
 * PHYSICS-VALIDATION GATE (BUILD-PLAN.md §6).
 *
 * The #1 de-risk for the whole project: prove the rendered curve IS the published
 * Hellings–Downs curve by asserting the analytic Γ(θ) against its closed-form landmark
 * values. These landmarks are *independently derivable from the closed form*, so the
 * test is self-checking, not circular.
 *
 * The curve under test is the normalized distinct-pulsar form shipped in
 * `hellingsDowns.ts` (the convention used in the NANOGrav 2023 figure):
 *
 *     Γ(θ) = 1/2 − x/4 + (3/2)·x·ln x ,   x = (1 − cos θ)/2
 *
 * Closed-form landmarks (derived in comments next to each assertion):
 *   • Γ(0°)  = 1/2                       (exact)
 *   • zero crossing at θ ≈ 49.317°       (|Γ| < 1e−3)
 *   • minimum = 1/2 − (3/2)·e^(−5/6)     (exact) at θ = arccos(1 − 2·e^(−5/6)) ≈ 82.484°
 *   • Γ(180°) = 1/4                      (exact)
 *   • no NaN at θ = 0 (the x·ln x = 0·(−∞) guard)
 *
 * NOTE ON THE MINIMUM VALUE: the planning docs (BUILD-PLAN.md §6, DATA-SOURCES.md §1)
 * quote the dip as "≈ −0.173". That figure belongs to a *different* normalization of the
 * HD curve and does NOT match the formula actually shipped here. The mathematically exact
 * minimum of THIS normalized formula is 1/2 − (3/2)·e^(−5/6) = −0.151897…, confirmed two
 * independent ways below (a fine sampled scan AND the analytic stationary point
 * dΓ/dx = −1/4 + (3/2)(ln x + 1) = 0 ⇒ x = e^(−5/6)). Per the "do not fake the physics
 * tests" constraint, we assert the value the formula genuinely produces. If the project
 * later adopts the Γ(0)=1 normalization, scale by 2 and the dip becomes −0.3038.
 */
import { describe, it, expect } from "vitest";
import {
  hdX,
  hellingsDowns,
  hellingsDownsDeg,
  sampleHDCurve,
} from "../hellingsDowns";

const deg2rad = (d: number) => (d * Math.PI) / 180;

describe("Hellings–Downs Γ(θ) — closed-form landmarks", () => {
  it("Γ(0°, distinct) = 0.5 exactly (curve starts at 0.5, not 1.0)", () => {
    expect(hellingsDownsDeg(0)).toBeCloseTo(0.5, 12);
  });

  it("does NOT return NaN at θ = 0 (x·ln x = 0·(−∞) guard)", () => {
    const v = hellingsDowns(0);
    expect(Number.isNaN(v)).toBe(false);
    expect(v).toBe(0.5);
    // x itself is exactly 0 at θ=0
    expect(hdX(0)).toBe(0);
  });

  it("has its famous zero crossing at θ ≈ 49.3° (|Γ| < 1e−3)", () => {
    // The true root is θ = 49.3173°; assert the curve is essentially zero there.
    expect(Math.abs(hellingsDownsDeg(49.3173))).toBeLessThan(1e-3);
    // And bracket it: positive just below, negative just above.
    expect(hellingsDownsDeg(45)).toBeGreaterThan(0);
    expect(hellingsDownsDeg(55)).toBeLessThan(0);
  });

  it("reaches its anticorrelation minimum near θ ≈ 82.5°", () => {
    // Exact minimum value = 1/2 − (3/2)·e^(−5/6); exact location θ = arccos(1 − 2 e^(−5/6)).
    const xMin = Math.exp(-5 / 6);
    const expectedMinValue = 0.5 - 1.5 * xMin; // = −0.151897…
    const expectedMinThetaDeg = (Math.acos(1 - 2 * xMin) * 180) / Math.PI; // ≈ 82.484°

    // (a) sampled-scan minimum agrees with the analytic value and location.
    let scanMinVal = Infinity;
    let scanMinThetaDeg = NaN;
    for (let d = 0; d <= 180; d += 0.001) {
      const v = hellingsDownsDeg(d);
      if (v < scanMinVal) {
        scanMinVal = v;
        scanMinThetaDeg = d;
      }
    }
    expect(scanMinThetaDeg).toBeGreaterThan(80);
    expect(scanMinThetaDeg).toBeLessThan(85);
    expect(scanMinThetaDeg).toBeCloseTo(expectedMinThetaDeg, 2);
    expect(scanMinVal).toBeCloseTo(expectedMinValue, 4);

    // (b) the formula evaluated AT the analytic minimum returns the analytic value.
    expect(hellingsDownsDeg(expectedMinThetaDeg)).toBeCloseTo(expectedMinValue, 10);

    // (c) sanity: that value really is ≈ −0.1519 (NOT the doc's −0.173).
    expect(expectedMinValue).toBeCloseTo(-0.151897, 5);
  });

  it("Γ(180°) = 0.25 exactly", () => {
    expect(hellingsDownsDeg(180)).toBeCloseTo(0.25, 12);
  });

  it("adds the +1/2 δ self-term only for the same pulsar (Γ_self(0°) = 1.0)", () => {
    expect(hellingsDowns(0, true)).toBeCloseTo(1.0, 12);
    // distinct vs self differ by exactly 1/2 everywhere
    const t = deg2rad(73);
    expect(hellingsDowns(t, true) - hellingsDowns(t, false)).toBeCloseTo(0.5, 12);
  });
});

describe("Hellings–Downs Γ(θ) — independent stationary-point cross-check", () => {
  it("dΓ/dx = 0 at x = e^(−5/6) (matches the analytic derivative)", () => {
    // Γ(x) = 1/2 − x/4 + (3/2)x·ln x ⇒ dΓ/dx = −1/4 + (3/2)(ln x + 1).
    // Setting = 0 gives ln x = 1/6 − 1 = −5/6 ⇒ x = e^(−5/6).
    const xMin = Math.exp(-5 / 6);
    const dGamma = (x: number) => -0.25 + 1.5 * (Math.log(x) + 1);
    expect(dGamma(xMin)).toBeCloseTo(0, 12);
    // numerically confirm it's a minimum: derivative flips sign across xMin
    expect(dGamma(xMin - 0.05)).toBeLessThan(0);
    expect(dGamma(xMin + 0.05)).toBeGreaterThan(0);
  });
});

describe("sampleHDCurve — plotting helper", () => {
  it("spans [0°, 180°] inclusive with the requested number of points and no NaN", () => {
    const pts = sampleHDCurve(181);
    expect(pts.length).toBe(181);
    expect(pts[0].thetaDeg).toBe(0);
    expect(pts[pts.length - 1].thetaDeg).toBe(180);
    expect(pts.every((p) => Number.isFinite(p.corr))).toBe(true);
    // endpoints carry the exact landmark values
    expect(pts[0].corr).toBeCloseTo(0.5, 12);
    expect(pts[pts.length - 1].corr).toBeCloseTo(0.25, 12);
  });
});
