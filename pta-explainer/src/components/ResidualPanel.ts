/**
 * The timing-residual panel (M2: the single-source sandbox).
 *
 * Renders, for a handful of representative pulsars, the timing residual that ONE
 * illustrative supermassive-black-hole binary stamps onto each of them over a ~15-year
 * span. As the caller drags the source parameters (chirp mass, GW frequency, sky
 * position, inclination), `update(params)` recomputes every pulsar's curve live.
 *
 * The pedagogical point this makes visible: the Earth-term residual is the SAME sinusoid
 * (same period) in every pulsar, but its amplitude and sign are set by each pulsar's
 * antenna pattern relative to the source — which is exactly the geometry that makes pairs
 * of pulsars correlate (the Hellings–Downs story, in the time domain). See residuals.ts.
 *
 * Like the other components this one is "dumb": it owns no source state. The caller
 * (main.ts) owns the parameters and pushes them in via `update`.
 */
import { scaleLinear } from "d3-scale";
import { axisBottom, axisLeft } from "d3-axis";
import { line } from "d3-shape";
import { select } from "d3-selection";
import {
  sampleResidualSeriesMulti,
  type SourceParams,
  type ResidualSample,
} from "../physics/residuals";
import type { Pulsar } from "../data/pulsars";

export interface ResidualPanelController {
  /**
   * Recompute and redraw every pulsar's residual for the given set of sources (summed),
   * with a shaded ±`rmsNs` timing-noise band (0 hides it).
   */
  update(sources: SourceParams[], rmsNs?: number): void;
}

export interface ResidualPanelOptions {
  /** The pulsars to display (a small representative subset). */
  pulsars: Pulsar[];
  /** Observing span in years (default 15 — the NANOGrav 15-yr span). */
  spanYears?: number;
  /** Samples per curve (default 240). */
  samples?: number;
  /** Initial set of sources to render (their residuals are summed). */
  initialSources: SourceParams[];
  /** Initial timing-noise RMS in ns for the shaded band (default 0 = no band). */
  initialRmsNs?: number;
  /** Called after each render with the peak residual and how many pulsars clear the band. */
  onRender?: (info: { peakNs: number; nAboveNoise: number; total: number }) => void;
}

// A colour-blind-friendly categorical palette (Okabe–Ito), enough for ~8 pulsars.
const PALETTE = [
  "#0072b2",
  "#e69f00",
  "#009e73",
  "#cc79a7",
  "#d55e00",
  "#56b4e9",
  "#f0e442",
  "#000000",
];

export function renderResidualPanel(
  container: HTMLElement,
  options: ResidualPanelOptions,
): ResidualPanelController {
  const pulsars = options.pulsars;
  const spanYears = options.spanYears ?? 15;
  const samples = options.samples ?? 240;

  const width = 720;
  const height = 380;
  const margin = { top: 16, right: 150, bottom: 48, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const x = scaleLinear().domain([0, spanYears]).range([0, innerW]);
  const y = scaleLinear().domain([-100, 100]).range([innerH, 0]); // rescaled per update

  const svg = select(container)
    .append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", "100%")
    .attr("role", "img")
    .attr("aria-label", "Induced timing residuals for several pulsars from a single source");

  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // timing-noise band (M2 detection overlay): a shaded ±RMS region, drawn first so it sits
  // behind the zero line, axes, and curves.
  const noiseBand = g
    .append("rect")
    .attr("x", 0)
    .attr("width", innerW)
    .attr("fill", "#94a3b8")
    .attr("opacity", 0.16);
  const noiseLabel = g
    .append("text")
    .attr("x", 6)
    .attr("font-size", 10)
    .attr("fill", "#475569");

  // zero line
  const zeroLine = g
    .append("line")
    .attr("x1", 0)
    .attr("x2", innerW)
    .attr("stroke", "#bbb")
    .attr("stroke-dasharray", "3 3");

  // x-axis (static) + label
  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(axisBottom(x).ticks(8));
  g.append("text")
    .attr("x", innerW / 2)
    .attr("y", innerH + 40)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Time (years of observing)");

  // y-axis (redrawn per update because the scale changes) + label
  const yAxisG = g.append("g");
  g.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerH / 2)
    .attr("y", -46)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Timing residual (nanoseconds)");

  // one group holds all the pulsar curves
  const linesG = g.append("g").attr("fill", "none").attr("stroke-width", 1.6);

  // legend (static: pulsar names + colours)
  const legend = g
    .append("g")
    .attr("transform", `translate(${innerW + 16},0)`)
    .attr("font-size", 11);
  pulsars.forEach((p, i) => {
    const row = legend.append("g").attr("transform", `translate(0,${i * 18 + 4})`);
    row
      .append("line")
      .attr("x1", 0)
      .attr("x2", 16)
      .attr("y1", 0)
      .attr("y2", 0)
      .attr("stroke", PALETTE[i % PALETTE.length])
      .attr("stroke-width", 2.5);
    row
      .append("text")
      .attr("x", 22)
      .attr("y", 3)
      .attr("fill", "#1a1a1a")
      .attr("class", "psr-label")
      .text(p.name);
  });

  const lineGen = line<ResidualSample>()
    .x((d) => x(d.tYears))
    .y((d) => y(d.residualNs));

  function update(sources: SourceParams[], rmsNs = 0): void {
    // Compute each pulsar's (summed-over-sources) series, its peak, and the overall peak.
    const series = pulsars.map((p) =>
      sampleResidualSeriesMulti(sources, p, { spanYears, samples }),
    );
    const perPulsarPeak = series.map((s) =>
      s.reduce((m, pt) => Math.max(m, Math.abs(pt.residualNs)), 0),
    );
    const peak = perPulsarPeak.reduce((m, v) => Math.max(m, v), 0);
    const rms = Math.max(0, rmsNs);
    const nAboveNoise = perPulsarPeak.filter((v) => v > rms).length;

    // y-range covers both the signal and the noise band (so a signal swamped by noise
    // still shows the band dwarfing it). Floor so a near-zero source still has sane axes.
    const yMax = Math.max(peak * 1.1, rms * 1.1, 1);
    y.domain([-yMax, yMax]);
    zeroLine.attr("y1", y(0)).attr("y2", y(0));
    yAxisG.call(axisLeft(y).ticks(6));

    if (rms > 0) {
      noiseBand
        .style("display", null)
        .attr("y", y(rms))
        .attr("height", y(-rms) - y(rms));
      noiseLabel
        .style("display", null)
        .attr("y", Math.max(y(rms) + 12, 12))
        .text(`timing noise ±${Math.round(rms)} ns`);
    } else {
      noiseBand.style("display", "none");
      noiseLabel.style("display", "none");
    }

    linesG
      .selectAll<SVGPathElement, ResidualSample[]>("path")
      .data(series)
      .join("path")
      .attr("stroke", (_d, i) => PALETTE[i % PALETTE.length])
      .attr("d", (d) => lineGen(d));

    options.onRender?.({ peakNs: peak, nAboveNoise, total: pulsars.length });
  }

  update(options.initialSources, options.initialRmsNs ?? 0);
  return { update };
}
