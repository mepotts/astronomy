/**
 * PHYSICS-VALIDATION for the illustrative multipole overlap-reduction functions (ORFs)
 * shown as reference overlays on the §3 plot (see `overlapReduction.ts`).
 *
 * These are deliberately simple closed forms, so their landmarks are self-checking:
 *   • monopole (clock errors)      → constant 1  (flat, angle-independent)
 *   • dipole   (ephemeris errors)  → cos θ        (+1 at 0°, 0 at 90°, −1 at 180°)
 *   • quadrupole (GWs)             → Hellings–Downs (tested in hellingsDowns.test.ts)
 *
 * We pin the PURE (autocorrelation-normalized, =1 at θ=0) landmark values, and separately
 * pin the PLOT-scaled sampling helpers, which anchor all three curves to the HD distinct-pair
 * value of 1/2 at θ=0 so they overlay comparably.
 */
import { describe, it, expect } from "vitest";
import {
  monopoleORF,
  dipoleORF,
  dipoleORFDeg,
  sampleMonopoleCurve,
  sampleDipoleCurve,
  ORF_PLOT_ANCHOR,
} from "../overlapReduction";
import { hellingsDownsDeg } from "../hellingsDowns";

const deg2rad = (d: number) => (d * Math.PI) / 180;

describe("Monopole ORF — clock/timing errors (flat)", () => {
  it("is the constant 1, independent of angle (the defining property of a monopole)", () => {
    // It takes no angle by construction — a monopole correlation is the same for every pair.
    expect(monopoleORF()).toBe(1);
    // and the plotted sample is genuinely flat (asserted from the sampler below too).
    const pts = sampleMonopoleCurve(9);
    expect(new Set(pts.map((p) => p.corr)).size).toBe(1);
  });
});

describe("Dipole ORF — solar-system ephemeris errors (∝ cos θ)", () => {
  it("hits its landmark values ±1 at 0°/180° and 0 at 90° (before display normalization)", () => {
    expect(dipoleORF(0)).toBeCloseTo(1, 12); // +1 in the same direction
    expect(dipoleORF(deg2rad(90))).toBeCloseTo(0, 12); // 0 at right angles
    expect(dipoleORF(deg2rad(180))).toBeCloseTo(-1, 12); // −1 on opposite sides
  });

  it("passes through the intermediate cos-θ values (60° → ½, 120° → −½)", () => {
    expect(dipoleORF(deg2rad(60))).toBeCloseTo(0.5, 12);
    expect(dipoleORF(deg2rad(120))).toBeCloseTo(-0.5, 12);
  });

  it("is antisymmetric about 90°: dip(θ) = −dip(180°−θ)", () => {
    for (const d of [10, 33.3, 70, 88]) {
      expect(dipoleORFDeg(d)).toBeCloseTo(-dipoleORFDeg(180 - d), 12);
    }
  });

  it("the degree wrapper matches the radian function", () => {
    for (const d of [0, 25, 49.3, 90, 137, 180]) {
      expect(dipoleORFDeg(d)).toBeCloseTo(dipoleORF(deg2rad(d)), 12);
    }
  });
});

describe("Plot-scaled sampling helpers — anchored to the HD distinct-pair value ½", () => {
  it("monopole samples span [0°,180°] and are flat at the display anchor (½)", () => {
    const pts = sampleMonopoleCurve(181);
    expect(pts.length).toBe(181);
    expect(pts[0].thetaDeg).toBe(0);
    expect(pts[pts.length - 1].thetaDeg).toBe(180);
    // every point sits exactly on the flat anchor line, independent of θ
    expect(pts.every((p) => p.corr === ORF_PLOT_ANCHOR)).toBe(true);
    // and that anchor is precisely where the rendered HD curve starts at θ=0
    expect(ORF_PLOT_ANCHOR).toBeCloseTo(hellingsDownsDeg(0), 12);
  });

  it("dipole samples run ½·cos θ: ½ at 0°, 0 at 90°, −½ at 180° (stays within [−0.5,1])", () => {
    const pts = sampleDipoleCurve(181);
    expect(pts.length).toBe(181);
    const at = (deg: number) => pts.find((p) => Math.abs(p.thetaDeg - deg) < 1e-9)!.corr;
    expect(at(0)).toBeCloseTo(0.5, 12);
    expect(at(90)).toBeCloseTo(0, 12);
    expect(at(180)).toBeCloseTo(-0.5, 12);
    // never leaves the plot's y-domain [-0.5, 1.0]
    expect(pts.every((p) => p.corr >= -0.5 - 1e-12 && p.corr <= 1.0 + 1e-12)).toBe(true);
    // starts at the same θ=0 anchor as the HD curve (so all three overlays are comparable)
    expect(at(0)).toBeCloseTo(hellingsDownsDeg(0), 12);
  });

  it("sampling helpers equal anchor × the pure ORF at matching angles", () => {
    const mono = sampleMonopoleCurve(37);
    const dip = sampleDipoleCurve(37);
    for (let i = 0; i < mono.length; i++) {
      expect(mono[i].corr).toBeCloseTo(ORF_PLOT_ANCHOR * monopoleORF(), 12);
      expect(dip[i].corr).toBeCloseTo(ORF_PLOT_ANCHOR * dipoleORFDeg(dip[i].thetaDeg), 12);
    }
  });
});
