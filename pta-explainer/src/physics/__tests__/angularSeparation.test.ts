/**
 * Tests for the spherical-law-of-cosines angular separation.
 *
 * The headline assertion is a *known pulsar pair*: the on-sky angle between
 * J1713+0747 and J1909−3744 (two of the most precisely timed NANOGrav millisecond
 * pulsars, and a natural pair for the live demo) is ≈ 52.96°. This value is
 * reproducible from their catalogue J2000 positions via the closed form, so it's a
 * self-checking landmark, not a magic number.
 */
import { describe, it, expect } from "vitest";
import {
  angularSeparationDeg,
  angularSeparationRad,
  angularSeparationBetween,
} from "../angularSeparation";

// Real J2000 positions (decimal degrees), as shipped in nanograv15_pulsars.json
// (ATNF-resolved positions for the NANOGrav 15-yr array).
const J1713 = { name: "J1713+0747", raDeg: 258.4564, decDeg: 7.7937 };
const J1909 = { name: "J1909-3744", raDeg: 287.4476, decDeg: -37.7374 };

describe("angularSeparation — known pulsar pair", () => {
  it("J1713+0747 ↔ J1909−3744 ≈ 52.96°", () => {
    const sep = angularSeparationBetween(J1713, J1909);
    expect(sep).toBeCloseTo(52.962, 2);
  });

  it("is symmetric (order of the pair does not matter)", () => {
    expect(angularSeparationBetween(J1713, J1909)).toBeCloseTo(
      angularSeparationBetween(J1909, J1713),
      12,
    );
  });
});

describe("angularSeparation — geometric sanity checks", () => {
  it("a point with itself is exactly 0° (no NaN from acos round-off)", () => {
    const sep = angularSeparationDeg(258.4585, 7.7877, 258.4585, 7.7877);
    expect(Number.isNaN(sep)).toBe(false);
    expect(sep).toBeCloseTo(0, 9);
  });

  it("the two celestial poles are exactly 180° apart", () => {
    expect(angularSeparationDeg(0, 90, 123.4, -90)).toBeCloseTo(180, 9);
  });

  it("two equatorial points 90° apart in RA are 90° apart on the sky", () => {
    expect(angularSeparationDeg(0, 0, 90, 0)).toBeCloseTo(90, 9);
  });

  it("along a meridian, separation equals the declination difference", () => {
    expect(angularSeparationDeg(0, 0, 0, 45)).toBeCloseTo(45, 9);
    expect(angularSeparationDeg(123.4, -10, 123.4, 30)).toBeCloseTo(40, 9);
  });

  it("clamps acos domain: identical positions never yield NaN", () => {
    // This input drives the dot product to exactly +1 (the clamp's reason for existing).
    const rad = angularSeparationRad(1.234, 0.5, 1.234, 0.5);
    expect(Number.isNaN(rad)).toBe(false);
    expect(rad).toBe(0);
  });
});
