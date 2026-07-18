/**
 * Integration check for the M1 "done when" criterion (BUILD-PLAN.md §M1):
 *
 *   "user picks J1909−3744 + J1713+0747 (or any pair / arbitrary θ), the marker sits on
 *    the correct point of the published curve."
 *
 * This exercises the exact pipeline main.ts uses to place the marker:
 *   pick two pulsars → angularSeparationBetween → θ → hellingsDownsDeg(θ) = marker height.
 * It does not render the SVG (that's a thin D3 view); it asserts the *physics wiring* that
 * determines where the marker lands is correct end-to-end, using the real shipped data.
 */
import { describe, it, expect } from "vitest";
import { angularSeparationBetween } from "../angularSeparation";
import { hellingsDownsDeg } from "../hellingsDowns";
import { pulsars } from "../../data/pulsars";

function byName(name: string) {
  const p = pulsars.find((x) => x.name === name);
  if (!p) throw new Error(`pulsar ${name} not in dataset`);
  return p;
}

describe("Live-demo pipeline: pick a pair → θ → Γ marker", () => {
  it("J1909−3744 + J1713+0747 land on the correct curve point", () => {
    // These two pulsars are in both the placeholder and the real array.
    const a = byName("J1909-3744");
    const b = byName("J1713+0747");

    const theta = angularSeparationBetween(a, b);
    expect(theta).toBeCloseTo(52.962, 2); // their on-sky separation (real 15-yr positions)

    // The marker's y is exactly Γ(θ) for the SAME θ derived from the pair.
    const corr = hellingsDownsDeg(theta);
    // At ~53° the curve is just past the zero crossing, so the correlation is small and
    // slightly negative.
    expect(corr).toBeLessThan(0);
    expect(corr).toBeGreaterThan(-0.05);
    // Pin the actual value (≈ −0.0315) so a normalization regression would be caught.
    expect(corr).toBeCloseTo(-0.0315, 3);
  });

  it("every distinct pulsar pair yields a finite θ in [0,180] and a finite Γ", () => {
    for (let i = 0; i < pulsars.length; i++) {
      for (let j = i + 1; j < pulsars.length; j++) {
        const theta = angularSeparationBetween(pulsars[i], pulsars[j]);
        expect(Number.isFinite(theta)).toBe(true);
        expect(theta).toBeGreaterThanOrEqual(0);
        expect(theta).toBeLessThanOrEqual(180);
        expect(Number.isFinite(hellingsDownsDeg(theta))).toBe(true);
      }
    }
  });

  it("dataset is well-formed (unique names, valid RA/Dec ranges)", () => {
    expect(pulsars.length).toBeGreaterThanOrEqual(2);
    const names = new Set(pulsars.map((p) => p.name));
    expect(names.size).toBe(pulsars.length); // no duplicates
    for (const p of pulsars) {
      expect(p.raDeg).toBeGreaterThanOrEqual(0);
      expect(p.raDeg).toBeLessThan(360);
      expect(p.decDeg).toBeGreaterThanOrEqual(-90);
      expect(p.decDeg).toBeLessThanOrEqual(90);
    }
  });
});
