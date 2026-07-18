/**
 * Integration check for the M2 "done when" wiring — the exact pipeline main.ts feeds into
 * the residual panel, exercised on the REAL shipped pulsar array (mirrors the philosophy of
 * liveDemo.integration.test.ts: assert the physics wiring, not the SVG view).
 *
 * The pipeline: source parameters → for each displayed pulsar, sampleResidualSeries → the
 * curves the panel draws. We assert the properties that make the panel pedagogically honest:
 *   • every displayed pulsar gets a finite series of the right length;
 *   • different pulsars get DIFFERENT amplitudes (the antenna-pattern story — otherwise the
 *     panel would be telling a lie about geometry mattering);
 *   • the Earth-term wiggle is coherent (periodic at the GW period) for each pulsar;
 *   • moving the source on the sky changes the pattern of amplitudes.
 */
import { describe, it, expect } from "vitest";
import {
  sampleResidualSeries,
  earthTermResidualSec,
  SECONDS_PER_YEAR,
  type SourceParams,
  type SkyDirection,
} from "../residuals";
import { pulsars } from "../../data/pulsars";

// Mirror main.ts's pickResidualPulsars: prefer recognizable names, else even spread.
function pickResidualPulsars(all: typeof pulsars, n = 6) {
  const preferred = [
    "J1909-3744",
    "J1713+0747",
    "J0437-4715",
    "J1744-1134",
    "J0030+0451",
    "J1640+2224",
  ];
  const byName = new Map(all.map((p) => [p.name, p]));
  const chosen: typeof pulsars = [];
  const seen = new Set<string>();
  for (const nm of preferred) {
    const p = byName.get(nm);
    if (p && !seen.has(p.name)) {
      chosen.push(p);
      seen.add(p.name);
    }
    if (chosen.length >= n) break;
  }
  const step = Math.max(1, Math.floor(all.length / n));
  for (let i = 0; i < all.length && chosen.length < n; i += step) {
    const p = all[i];
    if (!seen.has(p.name)) {
      chosen.push(p);
      seen.add(p.name);
    }
  }
  return chosen.slice(0, n);
}

const baseParams: SourceParams = {
  chirpMassSolar: 1e9,
  distanceMpc: 50,
  freqHz: 10e-9,
  source: { raDeg: 180, decDeg: 0 },
  inclinationRad: Math.PI / 4,
  psiRad: 0,
  phase0Rad: 0,
};

function peakNs(params: SourceParams, psr: SkyDirection): number {
  const s = sampleResidualSeries(params, psr, { spanYears: 15, samples: 240 });
  return Math.max(...s.map((p) => Math.abs(p.residualNs)));
}

describe("M2 residual-panel wiring on the real array", () => {
  it("selects a non-empty, de-duplicated set of real pulsars", () => {
    const chosen = pickResidualPulsars(pulsars);
    expect(chosen.length).toBeGreaterThanOrEqual(2);
    expect(new Set(chosen.map((p) => p.name)).size).toBe(chosen.length);
    for (const p of chosen) {
      expect(pulsars.some((q) => q.name === p.name)).toBe(true);
    }
  });

  it("produces a finite, full-length series for every displayed pulsar", () => {
    const chosen = pickResidualPulsars(pulsars);
    for (const p of chosen) {
      const s = sampleResidualSeries(baseParams, p, { spanYears: 15, samples: 240 });
      expect(s.length).toBe(240);
      expect(s.every((pt) => Number.isFinite(pt.residualNs))).toBe(true);
    }
  });

  it("gives DIFFERENT pulsars different amplitudes (geometry matters)", () => {
    const chosen = pickResidualPulsars(pulsars);
    const peaks = chosen.map((p) => peakNs(baseParams, p));
    const max = Math.max(...peaks);
    const min = Math.min(...peaks);
    // If antenna patterns were ignored, all peaks would be identical. Require a real spread.
    expect(max).toBeGreaterThan(0);
    expect((max - min) / max).toBeGreaterThan(0.05);
  });

  it("each displayed pulsar's Earth term is coherent (periodic at the GW period)", () => {
    const chosen = pickResidualPulsars(pulsars);
    const T = 1 / baseParams.freqHz;
    const t = 3.3 * SECONDS_PER_YEAR;
    for (const p of chosen) {
      expect(earthTermResidualSec(baseParams, p, t)).toBeCloseTo(
        earthTermResidualSec(baseParams, p, t + T),
        16,
      );
    }
  });

  it("moving the source on the sky changes the amplitude pattern across pulsars", () => {
    const chosen = pickResidualPulsars(pulsars);
    const atA = chosen.map((p) => peakNs(baseParams, p));
    const atB = chosen.map((p) =>
      peakNs({ ...baseParams, source: { raDeg: 30, decDeg: 60 } }, p),
    );
    // At least one pulsar's induced amplitude should change appreciably.
    const changed = atA.some((v, i) => Math.abs(v - atB[i]) / Math.max(v, atB[i], 1e-9) > 0.1);
    expect(changed).toBe(true);
  });
});
